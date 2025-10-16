import json
import time
from typing import Any, Dict


def rfc3339_ms(ts: float | None = None) -> str:
    if ts is None:
        ts = time.time()
    t = time.gmtime(ts)
    ms = int((ts - int(ts)) * 1000)
    return (
        f"{t.tm_year:04d}-{t.tm_mon:02d}-{t.tm_mday:02d}T"
        f"{t.tm_hour:02d}:{t.tm_min:02d}:{t.tm_sec:02d}.{ms:03d}Z"
    )


def ensure_envelope(req: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(req)
    if not isinstance(out.get("type"), str):
        out["type"] = "request"
    if not isinstance(out.get("ver"), str):
        out["ver"] = "1.0"
    if "msg_id" not in out or not isinstance(out["msg_id"], str) or not out["msg_id"]:
        out["msg_id"] = f"{int(time.time()*1000)}-{int(time.perf_counter_ns() & 0xffffffff):08x}"
    if not isinstance(out.get("ts"), str):
        out["ts"] = rfc3339_ms()
    if "op" not in out or not out["op"]:
        raise ValueError("Missing 'op' in request")
    if "payload" not in out or out["payload"] is None:
        out["payload"] = {}
    return out


def dumps_compact(obj: Dict[str, Any]) -> str:
    return json.dumps(obj, separators=(",", ":"))


def try_loads(line: str) -> Dict[str, Any] | None:
    try:
        o = json.loads(line)
        return o if isinstance(o, dict) else None
    except Exception:
        return None

