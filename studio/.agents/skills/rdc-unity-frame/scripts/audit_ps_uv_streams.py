"""Compare Unity KMF UV streams with RenderDoc's pixel-shader v0.xyzw.

The Kiana FBX's third UV block is not necessarily the vertex-shader output
v0.zw. For PS 31475, v0.zw controls albedo and normal/mask sampling on
backfaces; using FBX UV2 for it changes the material pattern.
"""

import argparse
import json
import struct
from pathlib import Path


def audit(kmf_path: Path, vsout_path: Path, stride: int):
    kmf = kmf_path.read_bytes()
    if kmf[:4] != b"KMF1":
        raise ValueError(f"Not KMF1: {kmf_path}")
    count, _ = struct.unpack_from("<II", kmf, 4)
    vsout = vsout_path.read_bytes()
    if len(vsout) != count * stride:
        raise ValueError(f"VSOut count/stride mismatch: {vsout_path}")
    uv0_offset = 12 + count * 14 * 4
    uv2_offset = 12 + count * 18 * 4
    max_uv0_error = 0.0
    max_uv2_error = 0.0
    changed = 0
    for i in range(count):
        uv0 = struct.unpack_from("<2f", kmf, uv0_offset + i * 8)
        uv2 = struct.unpack_from("<2f", kmf, uv2_offset + i * 8)
        ps_uv = struct.unpack_from("<4f", vsout, i * stride + 16)
        max_uv0_error = max(max_uv0_error, *(abs(uv0[j] - ps_uv[j]) for j in range(2)))
        err = max(abs(uv2[j] - ps_uv[j + 2]) for j in range(2))
        max_uv2_error = max(max_uv2_error, err)
        changed += err > 1e-5
    return {"eventId": int(kmf_path.stem[3:]), "vertexCount": count,
            "maxUv0Error": max_uv0_error, "maxUv2VersusPsZwError": max_uv2_error,
            "verticesNeedingPsZw": changed}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mesh_dir", type=Path)
    parser.add_argument("vsout_dir", type=Path)
    parser.add_argument("--stride", type=int, default=156)
    parser.add_argument("--write-uv-dir", type=Path,
                        help="Write PS v0.zw streams for Unity's existing mesh assets")
    args = parser.parse_args()
    results = []
    for kmf in sorted(args.mesh_dir.glob("EID*.bytes")):
        vsout = args.vsout_dir / f"{kmf.stem}.vsout.bin"
        if vsout.exists() and len(vsout.read_bytes()) % args.stride == 0:
            try:
                result = audit(kmf, vsout, args.stride)
                results.append(result)
                if args.write_uv_dir and result["verticesNeedingPsZw"]:
                    if result["maxUv0Error"] > 1e-5:
                        raise ValueError(f"UV0 ordering mismatch: {kmf}")
                    args.write_uv_dir.mkdir(parents=True, exist_ok=True)
                    data = vsout.read_bytes()
                    with (args.write_uv_dir / f"{kmf.stem}.bytes").open("wb") as out:
                        for i in range(result["vertexCount"]):
                            out.write(data[i * args.stride + 24:i * args.stride + 32])
            except ValueError:
                continue
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
