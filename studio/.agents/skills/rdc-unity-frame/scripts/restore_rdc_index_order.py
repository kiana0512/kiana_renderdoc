"""Verify and copy RDC index streams to Unity without changing mesh vertices.

The KMF/FBX export preserves triangle membership but can reorder triangles.
That changes which coplanar layer wins a depth tie and therefore its UV.
Only copy a stream when the complete unordered triangle multiset matches.
"""

import argparse
from collections import Counter
import json
from pathlib import Path
import struct


def indices(data, count):
    if len(data) == count * 4:
        return struct.unpack("<%dI" % count, data)
    if len(data) == count * 2:
        return struct.unpack("<%dH" % count, data)
    raise ValueError("unexpected RDC index stream length")


def triangles(values):
    return Counter(tuple(sorted(values[i:i + 3])) for i in range(0, len(values), 3))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("kmf_dir", type=Path)
    parser.add_argument("rdc_indices_dir", type=Path)
    parser.add_argument("unity_output_dir", type=Path)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    report = []
    args.unity_output_dir.mkdir(parents=True, exist_ok=True)
    for kmf_path in sorted(args.kmf_dir.glob("EID*.bytes")):
        source_path = args.rdc_indices_dir / (kmf_path.stem + ".indices.bin")
        if not source_path.exists():
            continue
        raw = kmf_path.read_bytes()
        if raw[:4] != b"KMF1":
            raise ValueError("bad KMF magic: " + str(kmf_path))
        vertex_count, index_count = struct.unpack_from("<II", raw, 4)
        kmf_indices = struct.unpack_from("<%dI" % index_count, raw,
                                         12 + vertex_count * 20 * 4)
        rdc_bytes = source_path.read_bytes()
        rdc_indices = indices(rdc_bytes, index_count)
        if triangles(kmf_indices) != triangles(rdc_indices):
            raise ValueError("triangle membership differs: " + kmf_path.stem)
        if max(rdc_indices) >= vertex_count:
            raise ValueError("index exceeds vertex count: " + kmf_path.stem)
        destination = args.unity_output_dir / (kmf_path.stem + ".bytes")
        destination.write_bytes(struct.pack("<%dI" % index_count, *rdc_indices))
        report.append({"eid": int(kmf_path.stem[3:]),
                       "vertices": vertex_count, "indices": index_count,
                       "triangles": index_count // 3,
                       "sameIndexPosition": sum(a == b for a, b in zip(kmf_indices, rdc_indices)),
                       "sameTrianglePosition": sum(
                           tuple(sorted(kmf_indices[i:i + 3])) ==
                           tuple(sorted(rdc_indices[i:i + 3]))
                           for i in range(0, index_count, 3)),
                       "sourceIndexWidth": len(rdc_bytes) // index_count})
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"meshes": len(report), "reordered": sum(
        item["sameIndexPosition"] != item["indices"] for item in report)},
        ensure_ascii=False))


if __name__ == "__main__":
    main()
