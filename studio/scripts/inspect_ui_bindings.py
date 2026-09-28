import json
import sys
from pathlib import Path

sys.path.insert(0, r"E:\renderdoc\kiana\mcp")
from src.ipc_client import IPCClient

client = IPCClient(timeout=120)
events = [2223, 2410, 2487, 2604, 2770, 2892, 3031, 3148, 3199, 3216, 3260, 3299]
rows = []
for eid in events:
    textures = client.call("get_bound_textures", {"event_id": eid, "stage": "fragment"}, timeout=120)
    rows.append({"eventId": eid, "textures": textures})
print(json.dumps(rows, ensure_ascii=False, indent=2))
