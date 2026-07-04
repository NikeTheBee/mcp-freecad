"""Phase 1 validation probe: talk directly to the headless FreeCAD MCP socket
on localhost:23456 using the project's own framing protocol, create a box, and
read back its geometry. Proves the FreeCAD-side server works end-to-end.

One request per connection; async tools return a job_id that we poll."""
import json
import socket
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".freecad-mcp"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "server" / "bridge_patches"))
from mcp_bridge_framing import send_message, receive_message
import mcp_auth  # NF5: the socket requires the shared token


def _one_shot(tool, args):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("localhost", 23456))
    try:
        send_message(s, json.dumps(mcp_auth.attach({"tool": tool, "args": args})))
        resp = receive_message(s, timeout=30.0)
        return json.loads(resp) if resp else None
    finally:
        s.close()


def call(tool, args):
    """Call a tool, transparently polling if it returns an async job_id."""
    r = _one_shot(tool, args)
    if isinstance(r, dict) and r.get("status") == "submitted" and r.get("job_id"):
        jid = r["job_id"]
        for _ in range(60):
            time.sleep(0.25)
            p = _one_shot("poll_job", {"job_id": jid})
            if isinstance(p, dict) and p.get("status") in ("done", "error"):
                return p
        return {"status": "timeout", "job_id": jid}
    return r


def main():
    print("-> view_control create_document")
    print(json.dumps(call("view_control",
          {"operation": "create_document", "name": "Phase1"}), indent=2)[:800])

    print("-> create_box 10x20x30")
    print(json.dumps(call("create_box",
          {"length": 10, "width": 20, "height": 30}), indent=2)[:800])

    print("-> measurement_operations get_volume (Box)")
    print(json.dumps(call("measurement_operations",
          {"operation": "get_volume", "object_name": "Box"}), indent=2)[:800])

    print("-> measurement_operations get_bounding_box (Box)")
    print(json.dumps(call("measurement_operations",
          {"operation": "get_bounding_box", "object_name": "Box"}), indent=2)[:800])


if __name__ == "__main__":
    main()
