"""Convert RenderDoc pass-state probe to a compact Unity material manifest."""

import argparse
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("probe", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    report = json.loads(args.probe.read_text(encoding="utf-8"))
    if not report["ok"] or len(report["events"]) != 26:
        raise ValueError("Expected all 26 G-buffer draw states")
    events = []
    for item in report["events"]:
        raster = item["rasterizer"]["state"]
        output = item["outputMerger"]
        depth = output["depthStencilState"]
        if depth["depthFunction"] != 5:
            raise ValueError("Unexpected depth function at EID %s" % item["eventId"])
        # Unity imported FBX triangle winding is opposite D3D's captured frontCCW.
        # Confirmed by isolated face draw: Unity Cull Back removes its front face.
        captured_cull = raster["cullMode"]
        unity_cull = {0: 0, 1: 2, 2: 1}[captured_cull]
        events.append({"eventId": item["eventId"],
                       "d3dCullMode": captured_cull,
                       "d3dFrontCCW": raster["frontCCW"],
                       "unityCullMode": unity_cull,
                       "depthFunction": depth["depthFunction"],
                       "depthWrites": depth["depthWrites"],
                       "stencilEnabled": depth["stencilEnable"],
                       "blendState": output["blendState"]["resourceId"]})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"frame": 38112, "pass": 5, "events": events},
                                      ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(args.output))


if __name__ == "__main__":
    main()
