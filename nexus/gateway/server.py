import asyncio
import json
import os
import sys
from pathlib import Path
from dataclasses import asdict

def _add_root(marker="toolkit"):
    here = Path(__file__).resolve()
    for parent in [here.parent] + list(here.parents):
        if (parent/marker).exists() and str(parent) not in sys.path:
            sys.path.append(str(parent)); return
_add_root()

import websockets  # type: ignore
from toolkit.events import new_event, from_json, Event
from toolkit.style import stylize
try:
    from mesh.nodes.ops.mini.mini import handle_interface_chat
except Exception:
    handle_interface_chat = None

clients=set(); sessions={}
EXPECTED_TOKEN=os.getenv("NEXUS_TOKEN")
DOWNSTREAM=os.getenv("INTERFACE_TARGET","mini")

def _register(ws,sid): 
    if not sid: return
    sessions.setdefault(sid,set()).add(ws)

async def _send_to_session(sid,payload):
    raw=json.dumps(payload)
    for ws in list(sessions.get(sid,set())):
        if ws.open: await ws.send(raw)

def _sim_hass(ev: Event):
    if ev.topic!="home.command": return None
    meta=dict(ev.meta or {}); sid=meta.get("session_id")
    cmd=ev.payload or {}; topic=cmd.get("topic")
    if topic=="hass.scene.set":
        txt=f"Sim HUD: scene -> '{cmd.get('scene','unknown')}'."
    elif topic=="hass.light.toggle":
        txt=f"Sim HUD: lights @ '{cmd.get('room','room')}' {cmd.get('state','on')}."
    else:
        txt=f"Sim HUD: home command: {cmd}"
    out=new_event("interface.output","nexus:sim.hass","notification",{"text": stylize(txt,channel='ui',session_id=sid,corr_id=meta.get('corr_id'))},meta={"session_id":sid,"corr_id":meta.get("corr_id")})
    return asdict(out)

async def handler(ws):
    # websockets v12 passes only the connection; path available as ws.path
    path = getattr(ws, "path", "")
    if EXPECTED_TOKEN:
        try:
            q=path.split("?",1)[1]; params=dict(p.split("=",1) for p in q.split("&") if "=" in p)
        except Exception:
            params={}
        if params.get("token")!=EXPECTED_TOKEN:
            await ws.close(code=1008, reason="Unauthorized"); return
    clients.add(ws)
    try:
        async for raw in ws:
            try: msg=json.loads(raw)
            except Exception: continue
            t=msg.get("type"); topic=msg.get("topic"); meta=msg.get("meta") or {}; payload=msg.get("payload") or {}
            sid=meta.get("session_id")
            if sid: _register(ws,sid)

            if t=="interface.input" and topic and topic.startswith("control."):
                out=new_event("interface.output","nexus:control","notification",{"text": stylize(f"Control ack: {topic}",channel='ui',session_id=sid,corr_id=meta.get('corr_id'))},meta={"session_id":sid,"corr_id":meta.get("corr_id")})
                await _send_to_session(sid, asdict(out)); continue

            if t=="grid.tick":
                n=payload.get("n")
                for s in list(sessions.keys()):
                    out=new_event("interface.output","nexus:grid","notification",{"text": stylize(f"Tick {n}",channel='grid',session_id=s,corr_id=meta.get('corr_id'))},meta={"session_id":s,"corr_id":meta.get("corr_id")})
                    await _send_to_session(s, asdict(out))
                continue

            if t=="interface.input" and topic=="chat.input":
                if DOWNSTREAM=="mini" and handle_interface_chat:
                    outs=handle_interface_chat(str(payload.get("text") or ""), sid, meta.get("corr_id"))
                    for ev in outs:
                        if ev.topic=="chat.output":
                            out=new_event("interface.output","nexus:mini","chat.output", ev.payload, meta={"session_id":sid,"corr_id":ev.meta.get("corr_id")})
                            await _send_to_session(sid, asdict(out))
                        elif ev.topic=="home.command":
                            sim=_sim_hass(ev)
                            if sim: await _send_to_session(sid, sim)
                    continue
                else:
                    out=new_event("interface.output","nexus:echo","chat.output",{"text": stylize(f"Echo return: {payload.get('text','')}",channel='ui',session_id=sid,corr_id=meta.get('corr_id'))},meta={"session_id":sid,"corr_id":meta.get("corr_id")})
                    await _send_to_session(sid, asdict(out)); continue

            for c in list(clients):
                if c.open: await c.send(raw)
    finally:
        clients.discard(ws)
        for s in list(sessions.values()): s.discard(ws)

async def main():
    host=os.getenv("NEXUS_HOST","127.0.0.1"); port=int(os.getenv("NEXUS_PORT","7000"))
    async with websockets.serve(handler, host, port):
        print(f"Nexus WS gateway on ws://{host}:{port} (target={DOWNSTREAM})")
        await asyncio.Future()

if __name__=="__main__":
    asyncio.run(main())
