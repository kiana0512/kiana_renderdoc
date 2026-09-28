"""Convert four captured UI post-VS triangle strips into editable Unity draw data.

Usage: python build_ui_postvs_manifest.py VSOUT_DIR OUTPUT_JSON
The fixed EID/resource mapping below is specific to frame 38112; change it after
inspecting another capture's UI draw bindings.
"""

import json
import struct
import sys
from pathlib import Path


DRAW_TEXTURES = {
    2237: "RID30499-GeneralPageBG2",
    2246: "RID30499-GeneralPageBG2",
    2280: "RID30512-GeneralBgLight",
    2307: "RID30497-GeneralPageBG1",
}


def build(source: Path) -> dict:
    draws = []
    for eid, texture in DRAW_TEXTURES.items():
        data = (source / f"EID{eid}.vsout.bin").read_bytes()
        indices = (source / f"EID{eid}.indices.bin").read_bytes()
        if len(data) != 4 * 72 or len(indices) != 6 * 2:
            raise ValueError(f"EID {eid}: expected four VSOut vertices and six indices")
        triangles = list(struct.unpack("<6H", indices))
        vertices = []
        for index in range(4):
            floats = struct.unpack_from("<18f", data, index * 72)
            vertices.append({"clip": list(floats[:4]),
                             "color": list(floats[4:8]),
                             "uv": list(floats[8:10])})
        draws.append({"eid": eid, "texture": texture,
                      "vertices": vertices, "indices": triangles})
    return {"sourceWidth": 3840, "sourceHeight": 2160, "draws": draws}


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    output = Path(sys.argv[2])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(build(Path(sys.argv[1])), indent=2), encoding="utf-8")
    print(output)
