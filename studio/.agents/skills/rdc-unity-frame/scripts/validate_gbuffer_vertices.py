"""Compare every imported IA vertex with the captured post-VS clip position."""

import argparse
import json
import struct
from pathlib import Path

import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("unity_assets", type=Path)
    ap.add_argument("postvs_report", type=Path)
    ap.add_argument("postvs_dir", type=Path)
    args = ap.parse_args()
    manifest = json.loads((args.unity_assets / "Manifest/gbuffer5-transforms.json").read_text(encoding="utf-8"))
    report = json.loads(args.postvs_report.read_text(encoding="utf-8"))
    by_eid = {item["eventId"]: item for item in report["events"]}
    camera = np.asarray(manifest["viewProjection"], dtype=np.float64).reshape(4, 4)
    rows = []
    for item in manifest["events"]:
        eid = item["eventId"]
        data = (args.unity_assets / "MeshData" / f"EID{eid}.bytes").read_bytes()
        count = struct.unpack_from("<I", data, 4)[0]
        local = np.frombuffer(data, dtype="<f4", count=count * 3, offset=12).reshape(-1, 3)
        transform = np.asarray(item["localToWorld"], dtype=np.float64).reshape(4, 4)
        mesh = by_eid[eid]["mesh"]
        stride = mesh["vertexByteStride"]
        raw = (args.postvs_dir / f"EID{eid}.vsout.bin").read_bytes()
        captured = np.ndarray((count, 4), dtype="<f4", buffer=raw,
                              strides=(stride, 4)).copy()
        homogeneous = np.c_[local, np.ones(count)]
        predicted = (homogeneous @ transform.T) @ camera.T
        error = np.max(np.abs(predicted - captured), axis=1)
        rows.append({"eventId": eid, "vertices": count,
                     "medianClipError": float(np.median(error)),
                     "p95ClipError": float(np.quantile(error, .95)),
                     "maxClipError": float(np.max(error))})
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
