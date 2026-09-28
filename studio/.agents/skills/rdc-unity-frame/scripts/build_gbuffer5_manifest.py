"""Build the exact pass-5 draw and texture audit from the RDC asset graph."""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("unity_project", type=Path)
    parser.add_argument("postvs_report", type=Path)
    args = parser.parse_args()
    root = args.unity_project / "Assets/Kiana"
    graph = json.loads((root / "Manifest/asset-graph.json").read_text(encoding="utf-8"))
    postvs = json.loads(args.postvs_report.read_text(encoding="utf-8"))
    actions = [action for action in graph["actions"]
               if 821 <= action["event_id"] <= 1332 and action["kind"] == "draw"]
    if len(actions) != 26 or sum(a["indices"] for a in actions) != 663852:
        raise ValueError("Pass-5 draw count or index sum differs from the RDC evidence")
    postvs_ids = {event["eventId"] for event in postvs["events"] if "error" not in event}
    if postvs_ids != {action["event_id"] for action in actions}:
        raise ValueError("Post-VS export does not cover exactly the pass-5 draw IDs")
    result = {"frame": 38112, "pass": 5, "eventRange": [821, 1332],
              "size": [2880, 1368], "colorTargets": [53242, 53246, 53250, 53254],
              "depthTarget": 53238, "totalIndices": 663852, "events": []}
    all_resources = {}
    for action in actions:
        textures = []
        for item in action["textures"]:
            rid = int(item["resourceId"])
            tex = {"slot": int(item["slot"]), "resourceId": rid,
                   "name": item.get("texName", ""), "format": item.get("format", ""),
                   "role": item.get("role", "unknown"),
                   "stage": item.get("stage", "")}
            textures.append(tex)
            all_resources[rid] = tex
        albedo = next((tex["resourceId"] for tex in textures
                       if tex["stage"] == "fragment" and tex["role"] == "albedo"), 0)
        result["events"].append({"eventId": action["event_id"],
                                 "indices": action["indices"], "vertexShader": action["shaders"]["vertex"],
                                 "fragmentShader": action["shaders"]["fragment"],
                                 "albedoResourceId": albedo, "textures": textures,
                                 "renderTargets": action["render_targets"],
                                 "depthTarget": action["depth_target"]})
    missing = [rid for rid in sorted(all_resources)
               if not (root / "Textures" / ("RID%d.png" % rid)).exists()]
    result["textureCoverage"] = {"uniqueBoundResources": len(all_resources),
                                 "missingExportIds": missing,
                                 "note": "Exported/bound is not equivalent to implemented shader sampling."}
    if missing:
        raise ValueError("Bound texture exports missing: %s" % missing)
    dest = root / "Manifest/gbuffer5-bindings.json"
    dest.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"draws": len(actions), "indices": result["totalIndices"],
                      "boundTextures": len(all_resources), "missingTextures": missing,
                      "manifest": str(dest)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
