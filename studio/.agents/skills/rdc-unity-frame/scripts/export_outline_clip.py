"""Export source outline VSOut clip positions for frame-specific Unity validation.

Usage: python export_outline_clip.py UNITY_MESHDATA_DIR VSOUT_DIR UNITY_DEST_DIR
The pass-5 outline VSOut stride is 104 bytes; SV_POSITION occupies bytes 0-15.
The Unity mesh stays a 3D Mesh. Its captured camera can read this UV5 stream
to compare source raster/depth/stencil independently from VS reconstruction.
"""

import json
import struct
import sys
from pathlib import Path

import numpy as np


def main(mesh_dir: Path, vsout_dir: Path, dest_dir: Path):
    dest_dir.mkdir(parents=True, exist_ok=True)
    draws = []
    for eid in (1057, 1078, 1091, 1107, 1118, 1130, 1143, 1161, 1183, 1331):
        mesh = (mesh_dir / "EID{}.bytes".format(eid)).read_bytes()
        if mesh[:4] != b"KMF1":
            raise ValueError("EID{} is not a KMF1 mesh".format(eid))
        vertex_count = struct.unpack_from("<I", mesh, 4)[0]
        source = (vsout_dir / "EID{}.vsout.bin".format(eid)).read_bytes()
        if len(source) != vertex_count * 104:
            raise ValueError("EID{} VSOut stride/count mismatch".format(eid))
        clip = np.ndarray((vertex_count, 4), dtype="<f4", buffer=source,
                          offset=0, strides=(104, 4)).copy()
        if not np.isfinite(clip).all() or not (clip[:, 3] > 0).all():
            raise ValueError("EID{} invalid captured clip values".format(eid))
        output = dest_dir / "EID{}.bytes".format(eid)
        output.write_bytes(clip.astype("<f4").tobytes())
        ndc = clip[:, :2] / clip[:, 3:4]
        draws.append({"eid": eid, "vertexCount": vertex_count,
                      "vsoutStride": 104, "clipMin": clip.min(0).tolist(),
                      "clipMax": clip.max(0).tolist(),
                      "ndcMin": ndc.min(0).tolist(),
                      "ndcMax": ndc.max(0).tolist(),
                      "unityUV5": str(output)})
    print(json.dumps({"frame": 38112, "draws": draws}, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    main(*(Path(x) for x in sys.argv[1:]))
