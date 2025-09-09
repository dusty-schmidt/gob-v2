import asyncio
import os
import sys
from pathlib import Path


def _add_root(marker="toolkit"):
    here=Path(__file__).resolve()
    for parent in [here.parent] + list(here.parents):
        if (parent/marker).exists() and str(parent) not in sys.path:
            sys.path.append(str(parent)); return
_add_root()

from toolkit.interface_sdk.client import InterfaceClient
from toolkit.style import stylize

HELP="/help to list commands: /quit, /mode <name>, /end"

def _println(s: str):
    print(s, flush=True)

async def run():
    client = InterfaceClient(interface_id=os.getenv("INTERFACE_ID","nano"), nexus_url=os.getenv("NEXUS_URL","ws://127.0.0.1:7000"), token=os.getenv("NEXUS_TOKEN"))
    await client.connect()
    _println(stylize(f"Neon link established. {HELP}", channel="ui", session_id=client.session_id))

    async def reader():
        loop = asyncio.get_running_loop()
        try:
            while True:
                text = await loop.run_in_executor(None, input, "> ")
                t = text.strip()
                if t in ("/q","/quit","/exit"):
                    await client.send_control("session.end", {"reason":"user"})
                    break
                if t.startswith("/mode "):
                    mode = t.split(" ",1)[1].strip() or "default"
                    await client.send_control("mode.set", {"mode": mode})
                    _println(stylize(f"Mode shift -> {mode}", channel="ui", session_id=client.session_id))
                    continue
                if t == "/help":
                    _println(HELP)
                    continue
                await client.publish_input(t)
        finally:
            await client.close()

    async def printer():
        async for ev in client.recv_outputs():
            payload = ev.payload or {}
            text = payload.get("text", "")
            if text:
                _println(text)

    await asyncio.gather(reader(), printer())

if __name__ == "__main__":
    asyncio.run(run())
