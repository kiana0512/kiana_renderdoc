"""Audit shader texture-slot coverage for every pass-5 draw.

Usage: python build_material_coverage.py BINDINGS.json SHADER_SLOTS.json OUT.json
"""

import json
import sys
from pathlib import Path


def main(bindings_file: Path, shader_slots_file: Path, output: Path):
    bindings = json.loads(bindings_file.read_text(encoding="utf-8"))
    shaders = json.loads(shader_slots_file.read_text(encoding="utf-8"))
    by_id = {item["eventId"]: item for item in shaders["events"]}
    table_file = output.parent / "frame38112-material-tables.json"
    table_draws = ({d["eid"] for d in json.loads(table_file.read_text(encoding="utf-8"))["draws"]}
                   if table_file.exists() else set())
    outline_file = output.parent / "frame38112-outline-material-tables.json"
    outline_draws = ({d["eid"] for d in json.loads(outline_file.read_text(encoding="utf-8"))["draws"]}
                     if outline_file.exists() else set())
    face_file = output.parent / "frame38112-face-material-tables.json"
    face_draws = ({d["eid"] for d in json.loads(face_file.read_text(encoding="utf-8"))["draws"]}
                  if face_file.exists() else set())
    result = []
    for item in bindings["events"]:
        eid = item["eventId"]
        shader = by_id[eid]
        fragment = {t["slot"]: t for t in item["textures"] if t["stage"] == "fragment"}
        albedo_slots = [slot for slot, tex in fragment.items()
                        if tex["resourceId"] == item["albedoResourceId"]]
        color_reads = albedo_slots[:]
        if eid in (858, 875, 895, 912, 928, 945):
            color_reads.append(4)  # t4 normal influences the current lighting approximation
        if eid == 1273:
            color_reads.append(4)  # face lightmap in the enabled eye family path
        source_reads = shader["referencedFragmentSlots"]
        # These nine PS families still issue a t2 sample, but cb3[106].x=0
        # selects the non-overlay color before lighting for this frame.
        overlay_result_unused = eid in (858, 875, 895, 912, 928, 945, 968, 1035, 1313)
        result.append({"eid": eid, "pixelShader": shader["pixelShader"],
                       "albedoResourceId": item["albedoResourceId"],
                       "unitySourcePSIdentityAssigned": True,
                       "unityBandTableBound": eid in table_draws,
                       "unityOutlineTableBound": eid in outline_draws,
                       "unityFaceTableBound": eid in face_draws,
                       "unityFamilyCandidateEnabled": shader["pixelShader"] in (31475, 42681, 33678, 31489),
                       "unityVertexLookupSlot1Audited": eid == 1273,
                       "sourceReferencedTextureSlots": source_reads,
                       "sourceSampledButColorDiscardedSlots": [2] if overlay_result_unused else [],
                       "sourceStructuredBufferSlots": shader["structuredBufferSlots"],
                       "unityCurrentColorTextureSlots": sorted(set(color_reads)),
                       "unityPendingTextureSlots": sorted(set(source_reads) - set(color_reads)),
                       "status": "partial"})
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"frame": 38112, "pass": 5,
                                  "draws": result,
                                  "psIdentityAssignedDraws": len(result),
                                  "bandTableBoundDraws": len(table_draws),
                                  "outlineTableBoundDraws": len(outline_draws),
                                  "faceTableBoundDraws": len(face_draws),
                                  "eyeVertexLookupAuditedDraws": 1,
                                  "completeDraws": 0}, indent=2), encoding="utf-8")
    print(f"Audited {len(result)} draws; none has full source shader coverage -> {output}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    main(*map(Path, sys.argv[1:]))
