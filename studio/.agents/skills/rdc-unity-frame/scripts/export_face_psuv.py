"""Audit/export face and eye PS v0.zw into Unity Mesh.uv3 without touching UV0.

Usage: python export_face_psuv.py KMF_DIR VSOUT_DIR UNITY_PSUV_DIR
The face VSOut stride is 144 bytes (eye: 132), with position at bytes 0-15 and
pixel input v0.xyzw at bytes 16-31. PS31476/31480 samples face lightmap
using v0.zw or v0.zy; the KMF third UV block is not that stream.
"""

import json
import struct
import sys
from pathlib import Path

import numpy as np


EIDS = {992: 144, 1008: 144, 1236: 144, 1252: 144, 1273: 132}


def main(mesh_dir: Path, vsout_dir: Path, dest_dir: Path):
    dest_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for eid, stride in EIDS.items():
        mesh = (mesh_dir / f"EID{eid}.bytes").read_bytes()
        if mesh[:4] != b"KMF1":
            raise ValueError(f"EID{eid} KMF1 expected")
        count = struct.unpack_from("<I", mesh, 4)[0]
        raw = (vsout_dir / f"EID{eid}.vsout.bin").read_bytes()
        if len(raw) != count * stride:
            raise ValueError(f"EID{eid} VSOut stride expected {stride}")
        ps_uv = np.ndarray((count, 4), dtype="<f4", buffer=raw,
                           offset=16, strides=(stride, 4))
        uv0 = np.frombuffer(mesh, dtype="<f4", count=count * 2,
                            offset=12 + count * 14 * 4).reshape(count, 2)
        uv2 = np.frombuffer(mesh, dtype="<f4", count=count * 2,
                            offset=12 + count * 18 * 4).reshape(count, 2)
        uv0_error = float(np.abs(ps_uv[:, :2] - uv0).max())
        if uv0_error > 1e-5:
            raise ValueError(f"EID{eid} UV0 vertex order mismatch {uv0_error}")
        out_path = dest_dir / f"EID{eid}.bytes"
        out_path.write_bytes(ps_uv[:, 2:4].astype("<f4").tobytes())
        results.append({"eid": eid, "vertexCount": count,
                        "maxUv0Error": uv0_error,
                        "maxKmfUv2VsPsZwError": float(np.abs(ps_uv[:, 2:4] - uv2).max()),
                        "psZwMin": ps_uv[:, 2:4].min(axis=0).tolist(),
                        "psZwMax": ps_uv[:, 2:4].max(axis=0).tolist(),
                        "unityOverride": str(out_path)})
    print(json.dumps({"draws": results}, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    main(*(Path(p) for p in sys.argv[1:]))
