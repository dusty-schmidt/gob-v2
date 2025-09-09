#!/usr/bin/env python3
import os, textwrap
from pathlib import Path

root = Path(".")
files = {
    "toolkit/events.py": """
from dataclasses import dataclass, asdict
import time, uuid, json

@dataclass
class Event:
    id: str
    ts: float
    type: str
    source: str
    targets: list
    topic: str
    payload: object
    meta: dict

def new_event(type, source, topic, payload, targets=None, meta=None, corr_id=None, session_id=None):
    m = dict(meta or {})
    if session_id:
        m["session_id"] = session_id
    if "corr_id" not in m:
        m["corr_id"] = corr_id or str(uuid.uuid4())
    return Event(str(uuid.uuid4()), time.time(), type, source, targets or [], topic, payload, m)

def to_json(e):
    return json.dumps(asdict(e), ensure_ascii=False)

def from_json(s):
    o = json.loads(s)
    return Event(
        o.get("id", str(uuid.uuid4())),
        float(o.get("ts", time.time())),
        o.get("type", ""),
        o.get("source", ""),
        list(o.get("targets", [])),
        o.get("topic", ""),
        o.get("payload"),
        dict(o.get("meta", {}))
    )
""",
    "toolkit/style.py": """
def stylize(text, channel="ui", session_id=None, corr_id=None):
    sid = session_id or "-"
    cid = corr_id or "-"
    return f"[NEON][{channel}][sid:{sid}][cid:{cid}] {text}"
""",
    # ... include the rest of the files exactly as in your original `files` dict ...
}

def write_all():
    for path, content in files.items():
        p = root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(textwrap.dedent(content).lstrip("\n"), encoding='utf-8')

    gi = root / ".gitignore"
    gi_txt = gi.read_text(encoding='utf-8') if gi.exists() else ""
    add = []
    if ".venv/" not in gi_txt:
        add.append("# Python venv\n.venv/")
    if "logs/" not in gi_txt:
        add.append("# Logs\nlogs/")
    if add:
        gi.write_text((gi_txt.rstrip() + "\n\n" + "\n".join(add) + "\n"), encoding='utf-8')

if __name__ == "__main__":
    write_all()
    print("[NEON] Bootstrap wrote code and scripts.")
    print("Next: bash scripts/run-nano.sh (inside your gobv2 conda env)")
