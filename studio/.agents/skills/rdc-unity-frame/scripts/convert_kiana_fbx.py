"""Convert a Kiana current-pose ASCII FBX to a compact Unity mesh stream.

The capture exporter writes per-vertex arrays but its FBX lacks mesh data that
Unity's FBX importer recognizes. This converter preserves the captured vertex
positions, normals, colors, tangents, UV0-2, and triangle indices.
"""

import argparse
import array
import json
import re
import struct
import sys
from pathlib import Path


def blocks(source: str, name: str):
    pattern = re.compile(r"\b" + re.escape(name) + r":\s*\*(\d+)\s*\{\s*a:\s*([^}]*)\}", re.S)
    for match in pattern.finditer(source):
        declared = int(match.group(1))
        values = match.group(2).strip().rstrip(",").split(",")
        if len(values) != declared:
            raise ValueError(f"{name}: declared {declared} values, found {len(values)}")
        yield values


def first(source: str, name: str, cast=float):
    value = next(blocks(source, name), None)
    if value is None:
        raise ValueError(f"Missing FBX array: {name}")
    return [cast(x) for x in value]


def optional(source: str, name: str, count: int, components: int, default):
    values = next(blocks(source, name), None)
    if values is None:
        return list(default) * count
    result = [float(x) for x in values]
    if len(result) != count * components:
        raise ValueError(f"{name}: expected {count * components} values, found {len(result)}")
    return result


def convert(source_path: Path, output_path: Path):
    source = source_path.read_text(encoding="utf-8")
    positions = first(source, "Vertices")
    if len(positions) % 3:
        raise ValueError("Vertex position array is not XYZ triples")
    vertex_count = len(positions) // 3
    raw_indices = first(source, "PolygonVertexIndex", int)
    if len(raw_indices) % 3:
        raise ValueError("Only triangulated FBX geometry is supported")
    if any(raw_indices[i] >= 0 for i in range(2, len(raw_indices), 3)):
        raise ValueError("FBX triangle end markers are missing")
    indices = [(-x - 1 if x < 0 else x) for x in raw_indices]
    if any(x < 0 or x >= vertex_count for x in indices):
        raise ValueError("A triangle index is outside the vertex array")

    normals = optional(source, "Normals", vertex_count, 3, (0.0, 0.0, 1.0))
    tangent_xyz = optional(source, "Tangents", vertex_count, 3, (1.0, 0.0, 0.0))
    tangents = [v for i in range(vertex_count) for v in (*tangent_xyz[i * 3:i * 3 + 3], 1.0)]
    colors = optional(source, "Colors", vertex_count, 4, (1.0, 1.0, 1.0, 1.0))
    uv_blocks = list(blocks(source, "UV"))
    uvs = []
    for i in range(3):
        if i < len(uv_blocks):
            uv = [float(x) for x in uv_blocks[i]]
            if len(uv) != vertex_count * 2:
                raise ValueError(f"UV{i}: expected {vertex_count * 2} values, found {len(uv)}")
            uvs.append(uv)
        else:
            uvs.append([0.0, 0.0] * vertex_count)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as output:
        output.write(b"KMF1")
        output.write(struct.pack("<II", vertex_count, len(indices)))
        for values in (positions, normals, tangents, colors, *uvs):
            array.array("f", values).tofile(output)
        array.array("I", indices).tofile(output)
    return {"source": str(source_path), "output": str(output_path), "vertices": vertex_count, "triangles": len(indices) // 3}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(json.dumps(convert(args.source, args.output), ensure_ascii=False))


if __name__ == "__main__":
    main()
