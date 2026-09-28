"""Validate IA → world → VSOut position and save per-draw 3D transforms."""

import argparse
import json
import struct
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("cbuffer_report", type=Path)
    parser.add_argument("unity_project", type=Path)
    args = parser.parse_args()
    source = json.loads(args.cbuffer_report.read_text(encoding="utf-8"))
    root = args.unity_project / "Assets/Kiana"
    result = {"frame": 38112, "pass": 5, "events": []}
    view_projection = None
    eye = None
    for event in source["events"]:
        eid = event["eventId"]
        mesh = (root / "MeshData" / ("EID%d.bytes" % eid)).read_bytes()
        if mesh[:4] != b"KMF1":
            raise ValueError("Missing IA mesh EID %d" % eid)
        ia = struct.unpack_from("<3f", mesh, 12)
        cb = event["vsConstantBuffers"]
        local_to_world = cb[1]["firstFloat4s"][:4]
        common = cb[0]["firstFloat4s"]
        uses_common_camera = any(any(abs(value) > 1e-7 for value in row)
                                 for row in common[127:131])
        vp_columns = common[127:131] if uses_common_camera else view_projection
        clip_bias = common[21][:2] if uses_common_camera else result["clipBias"]
        world = [sum(ia[j] * local_to_world[j][i] for j in range(3)) + local_to_world[3][i]
                 for i in range(3)]
        clip = [sum(world[j] * vp_columns[j][i] for j in range(3)) + vp_columns[3][i]
                for i in range(4)]
        clip[0] += clip_bias[0] * clip[3]
        clip[1] += clip_bias[1] * clip[3]
        captured = event["vertexSample"]["firstFloat4"]
        error = max(abs(a - b) for a, b in zip(clip, captured))
        local_flat = [local_to_world[col][row] for row in range(4) for col in range(4)]
        result["events"].append({"eventId": eid, "localToWorldColumns": local_to_world,
                                 "localToWorld": local_flat,
                                 "firstVertexClipMaxError": round(error, 6),
                                 "usesCommonCameraConstants": uses_common_camera})
        if view_projection is None:
            view_projection = vp_columns
            eye = common[55][:3]
            result["clipBias"] = clip_bias
        elif uses_common_camera and (view_projection != vp_columns or eye != common[55][:3]):
            raise ValueError("Camera constants differ between G-buffer draws")
    result["viewProjectionColumns"] = view_projection
    result["viewProjection"] = [view_projection[col][row] +
                                 (result["clipBias"][row] * view_projection[col][3] if row < 2 else 0.0)
                                 for row in range(4) for col in range(4)]
    result["cameraPosition"] = eye
    result["maxFirstVertexClipError"] = max(e["firstVertexClipMaxError"] for e in result["events"])
    target = root / "Manifest/gbuffer5-transforms.json"
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"events": len(result["events"]),
                      "maxClipError": result["maxFirstVertexClipError"],
                      "target": str(target)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
