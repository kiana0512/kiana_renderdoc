"""Convert RenderDoc pass-5 stencil enums into Unity ShaderLab values.

The captured-camera projection can reverse front/back winding in Unity, so
this manifest retains both source faces. Validate orientation per draw before
activating its Unity stencil state.
"""

import json
from pathlib import Path


SOURCE = Path("docs/frame38112-gbuffer-state-all.json")
OUTPUT = Path("docs/frame38112-gbuffer5-stencil.json")

# RenderDoc 1.36 CompareFunction from inspect_renderdoc_enums.py.
# UnityEngine.Rendering.CompareFunction values are ShaderLab's values.
COMPARE = {0: 1, 1: 8, 2: 2, 3: 4, 4: 5, 5: 7, 6: 3, 7: 6}


def main():
    events = json.loads(SOURCE.read_text(encoding="utf-8"))["events"]
    draws = []
    for event in events:
        state = event["outputMerger"]["depthStencilState"]
        front, back = state["frontFace"], state["backFace"]
        draws.append({
            "eid": event["eventId"],
            "sourceCull": event["rasterizer"]["state"]["cullMode"],
            "sourceFrontCCW": event["rasterizer"]["state"]["frontCCW"],
            "enabled": state["stencilEnable"],
            "reference": front["reference"],
            "readMask": front["compareMask"],
            "writeMask": front["writeMask"],
            "frontCompare": COMPARE[front["function"]],
            "backCompare": COMPARE[back["function"]],
            "frontPass": front["passOperation"],
            "backPass": back["passOperation"],
            "sourceFrontCompare": front["function"],
            "sourceBackCompare": back["function"],
        })
    OUTPUT.write_text(json.dumps({"frame": 38112, "pass": 5,
                                  "draws": draws}, indent=2) + "\n", encoding="utf-8")
    print("Wrote {} draw stencil states to {}".format(len(draws), OUTPUT))


if __name__ == "__main__":
    main()
