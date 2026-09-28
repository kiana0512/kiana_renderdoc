"""Inspect post-VS mesh buffers in Kiana's embedded RenderDoc Python.

Run with kiana_qrenderdoc.exe --python=SCRIPT and KIANA_POSTVS_CONFIG pointing
to JSON containing capture, output, and event_ids. This uses a separate replay
process and does not change the GUI's current event.
"""

import base64
import json
import os
import struct
import sys
import traceback
from pathlib import Path

_candidates = [
    Path(os.environ.get("LOCALAPPDATA", "")) / "Kiana RenderDoc" / "pymodules",
    Path(__file__).resolve().parents[4] / "release-next/win-unpacked/resources/kiana-runtime/pymodules",
]
_pymodules = next((path for path in _candidates if path.exists()), _candidates[0])
sys.path.insert(0, str(_pymodules))
import renderdoc as rd


def describe(mesh):
    fields = ("numIndices", "topology", "indexResourceId", "indexByteOffset",
              "indexByteStride", "vertexResourceId", "vertexByteOffset",
              "vertexByteStride", "baseVertex", "vertexOffset", "nearPlane",
              "farPlane", "instanced", "numInstances", "unproject")
    result = {}
    for field in fields:
        try:
            value = getattr(mesh, field)
            result[field] = int(value) if field.endswith("ResourceId") else (
                value if isinstance(value, (int, float, bool, str)) else str(value))
        except (AttributeError, TypeError, ValueError):
            pass
    return result


def sample_buffer(controller, resource_id, offset, stride):
    if not resource_id or stride <= 0:
        return None
    data = controller.GetBufferData(resource_id, max(0, int(offset)),
                                    min(256, int(stride) * 4))
    sample = {"byteCount": len(data), "firstBytesBase64": base64.b64encode(data).decode("ascii")}
    if len(data) >= 16:
        sample["firstFloat4"] = list(struct.unpack_from("<4f", data, 0))
    return sample


config_path = sys.argv[1] if len(sys.argv) > 1 else os.environ["KIANA_POSTVS_CONFIG"]
config = json.load(open(config_path, encoding="utf-8"))
report = {"capture": config["capture"], "events": [], "ok": False}
capture = controller = None
try:
    capture = rd.OpenCaptureFile()
    status = capture.OpenFile(config["capture"], "rdc", None)
    if not status.OK():
        raise RuntimeError(status.Message())
    status, controller = capture.OpenCapture(rd.ReplayOptions(), None)
    if not status.OK():
        raise RuntimeError(status.Message())
    for event_id in config["event_ids"]:
        event = {"eventId": int(event_id)}
        try:
            controller.SetFrameEvent(int(event_id), True)
            mesh = controller.GetPostVSData(0, 0, rd.MeshDataStage.VSOut)
            event["mesh"] = describe(mesh)
            event["vertexSample"] = sample_buffer(
                controller, mesh.vertexResourceId, mesh.vertexByteOffset,
                mesh.vertexByteStride)
            event["indexSample"] = sample_buffer(
                controller, mesh.indexResourceId, mesh.indexByteOffset,
                mesh.indexByteStride)
            pipeline = controller.GetPipelineState()
            if config.get("inspect_d3d11"):
                d3d = controller.GetD3D11PipelineState()
                event["d3d11Fields"] = [x for x in dir(d3d) if not x.startswith("_")]
                event["pipelineFields"] = [x for x in dir(pipeline) if not x.startswith("_")]
                event["constantBlockDoc"] = str(pipeline.GetConstantBlocks.__doc__)
                event["constantBlockOneDoc"] = str(pipeline.GetConstantBlock.__doc__)
                event["cbufferUsedCount"] = len(pipeline.GetConstantBlocks(rd.ShaderStage.Vertex, True))
                event["descriptorCount"] = int(d3d.descriptorCount)
                event["descriptorStore"] = int(d3d.descriptorStore)
                accesses = controller.GetDescriptorAccess()
                event["descriptorAccessCount"] = len(accesses)
                event["descriptorAccessFirst"] = [{name: str(getattr(a, name))
                                                    for name in dir(a) if not name.startswith("_")
                                                    and name not in ("acquire", "append", "disown", "next", "own", "this", "thisown")}
                                                   for a in accesses[:20]]
                for field in ("vertexShader", "vs", "VS"):
                    if hasattr(d3d, field):
                        stage_state = getattr(d3d, field)
                        event["d3d11VertexField"] = field
                        event["d3d11VertexFields"] = [x for x in dir(stage_state) if not x.startswith("_")]
                        event["d3d11VertexStage"] = str(stage_state.stage)
                        for cb_field in ("constantBuffers", "constantBuffers", "cbuffers"):
                            if hasattr(stage_state, cb_field):
                                buffers = getattr(stage_state, cb_field)
                                event["d3d11VertexCbuffers"] = [str(x) for x in buffers[:5]]
                                event["d3d11VertexCbufferFields"] = ([x for x in dir(buffers[0]) if not x.startswith("_")]
                                                                     if buffers else [])
                        break
            try:
                cbuffer_bindings = pipeline.GetConstantBlocks(rd.ShaderStage.Vertex, False)
                event["vsConstantBuffers"] = []
                for slot, binding in enumerate(cbuffer_bindings):
                    descriptor = binding.descriptor
                    rid = descriptor.resource
                    info = {"slot": slot, "resourceId": int(rid),
                            "byteOffset": int(descriptor.byteOffset),
                            "byteSize": int(descriptor.byteSize)}
                    if int(rid):
                        try:
                            raw = controller.GetBufferData(rid, info["byteOffset"],
                                                           min(4096, info["byteSize"]))
                            info["readBytes"] = len(raw)
                            info["firstFloat4s"] = [list(struct.unpack_from("<4f", raw, j))
                                                    for j in range(0, len(raw) - 15, 16)]
                        except Exception as exc:
                            info["readError"] = str(exc)
                    event["vsConstantBuffers"].append(info)
            except Exception as exc:
                event["vsConstantBufferError"] = str(exc)
            if config.get("inspect_ps_constants"):
                try:
                    event["psConstantBuffers"] = []
                    for slot, binding in enumerate(pipeline.GetConstantBlocks(rd.ShaderStage.Pixel, False)):
                        descriptor = binding.descriptor
                        rid = descriptor.resource
                        info = {"slot": slot, "resourceId": int(rid),
                                "byteOffset": int(descriptor.byteOffset),
                                "byteSize": int(descriptor.byteSize)}
                        if int(rid):
                            raw = controller.GetBufferData(rid, info["byteOffset"],
                                                           min(4096, info["byteSize"]))
                            info["float4s"] = [list(struct.unpack_from("<4f", raw, j))
                                               for j in range(0, len(raw) - 15, 16)]
                        event["psConstantBuffers"].append(info)
                except Exception as exc:
                    event["psConstantBufferError"] = str(exc)
            shader_id = pipeline.GetShader(rd.ShaderStage.Vertex)
            if int(shader_id):
                entries = controller.GetShaderEntryPoints(shader_id)
                if entries:
                    reflection = controller.GetShader(rd.ResourceId(), shader_id, entries[0])
                    if reflection:
                        event["vsOutputs"] = [{"semantic": str(s.semanticName),
                                               "semanticIndex": int(s.semanticIndex),
                                               "regIndex": int(s.regIndex),
                                               "varType": str(s.varType),
                                               "compCount": int(s.compCount)}
                                              for s in reflection.outputSignature]
            if config.get("export_dir") and mesh.numIndices > 0:
                directory = Path(config["export_dir"])
                directory.mkdir(parents=True, exist_ok=True)
                vb = controller.GetBufferData(mesh.vertexResourceId, 0, 0)
                ib = controller.GetBufferData(mesh.indexResourceId, 0, 0)
                vb_path = directory / ("EID%d.vsout.bin" % event_id)
                ib_path = directory / ("EID%d.indices.bin" % event_id)
                vb_path.write_bytes(vb)
                ib_path.write_bytes(ib)
                event["vertexFile"] = str(vb_path)
                event["indexFile"] = str(ib_path)
                event["vertexBytes"] = len(vb)
                event["indexBytes"] = len(ib)
        except Exception:
            event["error"] = traceback.format_exc()
        report["events"].append(event)
    report["ok"] = all("error" not in e for e in report["events"])
except Exception:
    report["error"] = traceback.format_exc()
finally:
    if controller:
        controller.Shutdown()
    if capture:
        capture.Shutdown()
    with open(config["output"], "w", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
sys.exit(0 if report["ok"] else 1)
