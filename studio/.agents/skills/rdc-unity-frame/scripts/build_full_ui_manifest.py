"""Build all frame 38112 UI draw meshes from exported post-VS buffers.

The EID2475 full-frame composite quad is deliberately excluded. It is
reconstructed by the Unity character pipeline, not sampled as a texture.
"""

import json
import struct
import sys
from pathlib import Path

chain_path, postvs_path, textures_dir, output_path = map(Path, sys.argv[1:5])
chain = json.loads(chain_path.read_text(encoding="utf-8"))
postvs = json.loads(postvs_path.read_text(encoding="utf-8"))
postvs_by_eid = {event["eventId"]: event for event in postvs["events"]}
asset_root = textures_dir.parent


def texture_path(rid):
    if rid in (0, 59, 65, 87):
        return ""
    matches = [p for p in textures_dir.rglob("RID%d*.png" % rid)
               if "alpha" not in p.stem.lower() and "mip" not in p.stem.lower()]
    if not matches:
        raise FileNotFoundError("RID%d texture is missing" % rid)
    path = sorted(matches, key=lambda p: len(p.name))[0]
    return "Assets/Kiana/" + path.relative_to(asset_root).as_posix()


draws = []
for event in chain["events"]:
    eid = event["eventId"]
    if eid < 2223 or eid == 2475 or event["indices"] == 0:
        continue
    vs = postvs_by_eid[eid]
    stride = vs["mesh"]["vertexByteStride"]
    if stride not in (40, 48, 72):
        raise ValueError("EID%d: unsupported VSOut stride %d" % (eid, stride))
    vertex_bytes = Path(vs["vertexFile"]).read_bytes()
    index_bytes = Path(vs["indexFile"]).read_bytes()
    if len(vertex_bytes) % stride or len(index_bytes) != event["indices"] * 2:
        raise ValueError("EID%d: VSOut buffer lengths do not match draw" % eid)
    vertices = []
    for offset in range(0, len(vertex_bytes), stride):
        fields = struct.unpack_from("<10f", vertex_bytes, offset)
        vertices.append({"clip": list(fields[:4]), "color": list(fields[4:8]),
                         "uv": list(fields[8:10])})
    indices = list(struct.unpack("<%dH" % event["indices"], index_bytes))
    if max(indices) >= len(vertices):
        raise ValueError("EID%d: index exceeds VSOut vertex count" % eid)
    bindings = {resource["slot"]: resource["id"]
                for resource in event["readOnly"].get("ps", [])}
    draws.append({"eid": eid, "fragmentShaderId": event["shaders"].get("ps", {}).get("id", 0),
                  "afterCharacter": eid > 2475, "texture": texture_path(bindings.get(0, 0)),
                  "maskTexture": texture_path(bindings.get(1, 0)),
                  "vertices": vertices, "indices": indices})

manifest = {"sourceWidth": 3840, "sourceHeight": 2160, "draws": draws}
output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
print("Wrote %d UI draws (%d before, %d after character) to %s" %
      (len(draws), sum(not d["afterCharacter"] for d in draws),
       sum(d["afterCharacter"] for d in draws), output_path))
