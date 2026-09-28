"""Build the EID2475 screen quad from the captured post-VS stream."""
import json
import struct
import sys
from pathlib import Path


def main(vsout: Path, indices: Path, output: Path) -> None:
    vertex_bytes = vsout.read_bytes()
    index_bytes = indices.read_bytes()
    if len(vertex_bytes) != 4 * 72 or len(index_bytes) != 6 * 2:
        raise ValueError("EID2475 must have four 72-byte vertices and six uint16 indices")
    vertices = []
    for i in range(4):
        f = struct.unpack_from("<18f", vertex_bytes, i * 72)
        vertices.append({"clip": list(f[:4]), "color": list(f[4:8]), "uv": list(f[8:10])})
    data = {
        "sourceWidth": 3840,
        "sourceHeight": 2160,
        "eventId": 2475,
        "inputResourceId": 52987,
        "backgroundStageEventId": 2456,
        "backgroundResourceId": 1181,
        "vertices": vertices,
        "indices": list(struct.unpack("<6H", index_bytes)),
        "blend": "One, OneMinusSrcAlpha",
        "pixelShader": 31769,
        "pixelAdd": [0, 0, 0, 0],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("build_final_stage_manifest.py VSOUT INDICES OUTPUT")
    main(*map(Path, sys.argv[1:]))
