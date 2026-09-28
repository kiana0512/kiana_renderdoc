"""Convert RenderDoc VSOut buffers to screen-space Unity KMF1 meshes.

This freezes the captured frame's actual vertex pose and projection. It does
not recover a reusable skeleton or the game's material shader.
"""

import argparse
import array
import json
import math
import struct
from pathlib import Path


def convert_event(event, target, aspect):
    mesh = event["mesh"]
    stride = int(mesh["vertexByteStride"])
    raw_vertices = Path(event["vertexFile"]).read_bytes()
    raw_indices = Path(event["indexFile"]).read_bytes()
    if stride < 16 or len(raw_vertices) % stride:
        raise ValueError("Invalid VSOut vertex buffer for EID %s" % event["eventId"])
    vertex_count = len(raw_vertices) // stride
    index_count = int(mesh["numIndices"])
    index_stride = int(mesh["indexByteStride"])
    if index_count % 3 or index_stride not in (2, 4):
        raise ValueError("Invalid VSOut triangle/index format for EID %s" % event["eventId"])
    if len(raw_indices) < index_count * index_stride:
        raise ValueError("Truncated VSOut index buffer for EID %s" % event["eventId"])
    indices = array.array("I", (struct.unpack_from("<I" if index_stride == 4 else "<H",
                                                   raw_indices, i * index_stride)[0]
                                  for i in range(index_count)))
    if indices and max(indices) >= vertex_count:
        raise ValueError("VSOut index exceeds vertex count for EID %s" % event["eventId"])

    positions = array.array("f")
    normals = array.array("f")
    tangents = array.array("f")
    colors = array.array("f")
    uv_numerator = array.array("f")
    reciprocal_w = array.array("f")
    uv2 = array.array("f")
    bounds = [float("inf"), float("inf"), -float("inf"), -float("inf")]
    invalid = 0
    for i in range(vertex_count):
        offset = i * stride
        x, y, z, w = struct.unpack_from("<4f", raw_vertices, offset)
        if not all(map(math.isfinite, (x, y, z, w))) or abs(w) < 1e-10:
            x = y = z = 0.0
            w = 1.0
            invalid += 1
        inv_w = 1.0 / w
        nx, ny, nz = x * inv_w * aspect, y * inv_w, z * inv_w
        positions.extend((nx, ny, nz))
        bounds[0] = min(bounds[0], nx)
        bounds[1] = min(bounds[1], ny)
        bounds[2] = max(bounds[2], nx)
        bounds[3] = max(bounds[3], ny)
        u, v = struct.unpack_from("<2f", raw_vertices, offset + 16) if stride >= 24 else (0.5, 0.5)
        uv_numerator.extend((u * inv_w, v * inv_w))
        reciprocal_w.extend((inv_w, 0.0))
        uv2.extend((u, v))
        normals.extend((0.0, 0.0, -1.0))
        tangents.extend((1.0, 0.0, 0.0, 1.0))
        colors.extend((1.0, 1.0, 1.0, 1.0))
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("wb") as output:
        output.write(b"KMF1")
        output.write(struct.pack("<II", vertex_count, index_count))
        for values in (positions, normals, tangents, colors,
                       uv_numerator, reciprocal_w, uv2, indices):
            values.tofile(output)
    return {"eventId": event["eventId"], "mesh": str(target),
            "vertexCount": vertex_count, "indexCount": index_count,
            "invalidClipVertices": invalid,
            "unityBoundsXY": [round(v, 6) for v in bounds],
            "vsoutStride": stride,
            "uvInterpretation": "TEXCOORD0.xy / clipW; uv1.x = 1 / clipW"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    parser.add_argument("unity_project", type=Path)
    parser.add_argument("--width", type=int, default=2880)
    parser.add_argument("--height", type=int, default=1368)
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    if not report.get("ok") or len(report["events"]) != 26:
        raise ValueError("Expected the successful 26-draw G-buffer VSOut report")
    root = args.unity_project / "Assets/Kiana/MeshData/PostVS"
    converted = [convert_event(event, root / ("EID%d.bytes" % event["eventId"]),
                               args.width / args.height) for event in report["events"]]
    summary = {"source": str(args.report), "resolution": [args.width, args.height],
               "coordinateSpace": "D3D clip / W mapped to Unity orthographic screen plane",
               "events": converted}
    summary_path = args.unity_project / "Assets/Kiana/Manifest/gbuffer5-postvs.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"converted": len(converted), "vertices": sum(x["vertexCount"] for x in converted),
                      "indices": sum(x["indexCount"] for x in converted),
                      "invalidClipVertices": sum(x["invalidClipVertices"] for x in converted),
                      "summary": str(summary_path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
