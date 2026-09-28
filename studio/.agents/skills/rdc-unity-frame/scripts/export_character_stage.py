"""Export all character draw meshes and their texture bindings for one RDC frame."""

import json
import shutil
import sys
from pathlib import Path

from export_kiana_ipc_textures import connect_frame


EVENT_IDS = [858, 875, 895, 912, 928, 945, 968, 992, 1008, 1035,
             1057, 1078, 1091, 1107, 1118, 1130, 1143, 1161, 1183,
             1236, 1252, 1273, 1313, 1331, 1610, 1868]


def main():
    if len(sys.argv) != 4:
        raise SystemExit("Usage: export_character_stage.py ANALYSIS_DIR UNITY_PROJECT FRAME_NUMBER")
    analysis = Path(sys.argv[1])
    project = Path(sys.argv[2])
    client = connect_frame(int(sys.argv[3]))
    export_root = analysis / "character-current-pose"
    geometry = project / "Assets/Kiana/Geometry"
    textures = project / "Assets/Kiana/Textures"
    manifest_path = project / "Assets/Kiana/Manifest/character-bindings.json"
    geometry.mkdir(parents=True, exist_ok=True)
    textures.mkdir(parents=True, exist_ok=True)
    manifest = {"frame": int(sys.argv[3]), "events": [], "textures": {}}
    for eid in EVENT_IDS:
        record = {"event_id": eid, "mesh": None, "fragment_textures": []}
        try:
            export = client.call("export_fbx", {"event_id": eid,
                "output_dir": str(export_root / f"eid-{eid}"),
                "export_textures": False, "position_attribute": "", "attribute_map": {}}, timeout=300)
            source = Path(export["fbx"])
            if source.exists():
                target = geometry / f"EID{eid}.fbx"
                shutil.copy2(source, target)
                record["mesh"] = target.name
                record["vertices"] = export.get("vertices", 0)
                record["triangles"] = export.get("triangles", 0)
        except Exception as exc:
            record["mesh_error"] = str(exc)
        try:
            bindings = client.call("get_bound_textures", {"event_id": eid, "stage": "fragment"}, timeout=30)
            record["fragment_textures"] = bindings
            for item in bindings:
                rid = item.get("resourceId")
                if not rid or rid in manifest["textures"]:
                    continue
                target = textures / f"RID{rid}.png"
                if not target.exists():
                    try:
                        client.call("save_texture", {"resource_id": rid,
                            "output_path": str(target), "mip": 0, "slice": -1}, timeout=60)
                    except Exception as exc:
                        item["export_error"] = str(exc)
                manifest["textures"][rid] = {"file": target.name if target.exists() else None,
                    "name": item.get("texName"), "format": item.get("format")}
        except Exception as exc:
            record["texture_error"] = str(exc)
        manifest["events"].append(record)
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"EID {eid}: {record.get('vertices', 0)} vertices, "
              f"{len(record['fragment_textures'])} texture bindings, "
              f"{record.get('mesh_error', record.get('texture_error', 'ok'))}", flush=True)
    print(f"Exported {len(manifest['events'])} draw records and {len(manifest['textures'])} unique textures", flush=True)


if __name__ == "__main__":
    main()
