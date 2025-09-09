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
