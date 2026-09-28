"""Audit the packed COLOR.b -> VSOut v5.w outline control for pass 5.

Usage: python audit_outline_vertex_control.py KMF_DIR VSOUT_DIR
PS31478 uses 0.9 - 0.2 * (int(COLOR.b*255) & 3).
PS31479 uses (int(COLOR.b*255) >> 5) & 1.
"""

import json
import struct
import sys
from pathlib import Path

import numpy as np


OUTLINE_A = (1057, 1161)
OUTLINE_B = (1078, 1091, 1107, 1118, 1130, 1143, 1183, 1331)


def audit(eid: int, mesh_dir: Path, vsout_dir: Path):
    mesh = (mesh_dir / f"EID{eid}.bytes").read_bytes()
    if mesh[:4] != b"KMF1":
        raise ValueError(f"EID{eid} is not KMF")
    count = struct.unpack_from("<I", mesh, 4)[0]
    color = np.frombuffer(mesh, dtype="<f4", count=count * 4,
                          offset=12 + count * 10 * 4).reshape(count, 4)
    raw = (vsout_dir / f"EID{eid}.vsout.bin").read_bytes()
    if len(raw) != count * 104:
        raise ValueError(f"EID{eid} expected 104-byte VSOut stride")
    source = np.ndarray((count,), dtype="<f4", buffer=raw,
                        offset=88, strides=(104,))
    source_uv = np.ndarray((count, 2), dtype="<f4", buffer=raw,
                           offset=16, strides=(104, 4))
    kmf_uv = np.frombuffer(mesh, dtype="<f4", count=count * 2,
                            offset=12 + count * 14 * 4).reshape(count, 2)
    # KMF float32 serialization can put a normalized byte infinitesimally
    # below its integer boundary. Recover the original UNORM8 byte first.
    packed = np.floor(color[:, 2] * 255 + 0.5).astype(np.int32)
    if eid in OUTLINE_A:
        predicted = 0.9 - 0.2 * (packed & 3)
    else:
        predicted = (packed >> 5) & 1
    error = np.abs(source - predicted)
    mismatch = np.flatnonzero(error >= 1e-4)
    return {"eid": eid, "vertexCount": count,
            "maxV1Uv0Error": float(np.abs(source_uv - kmf_uv).max()),
            "v5wValues": np.unique(source).tolist(),
            "matchingVertices1e4": int((error < 1e-4).sum()),
            "maxAbsError": float(error.max()),
            "firstMismatch": ({"vertex": int(mismatch[0]),
                               "colorB": float(color[mismatch[0], 2]),
                               "packedTruncated": int(packed[mismatch[0]]),
                               "captured": float(source[mismatch[0]]),
                               "predicted": float(predicted[mismatch[0]])}
                              if mismatch.size else None)}


def main(mesh_dir: Path, vsout_dir: Path):
    result = [audit(eid, mesh_dir, vsout_dir) for eid in OUTLINE_A + OUTLINE_B]
    print(json.dumps({"draws": result,
                      "totalVertices": sum(x["vertexCount"] for x in result),
                      "matchingVertices1e4": sum(x["matchingVertices1e4"] for x in result)},
                     indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(Path(sys.argv[1]), Path(sys.argv[2]))
