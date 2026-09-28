"""Generate one Unity ShaderLab asset per decompiled frame-38112 deferred EID."""
import argparse
import json
import re
from pathlib import Path


PASS_STATE = {
    1403: {"stencil": None, "blend": None},
    # RenderDoc CompareFunction value 6 is Equal (replay_enums.h), not D3D's
    # numeric D3D12_COMPARISON_FUNC value 6. Keep the API domains separate.
    1419: {"stencil": (144, 160, "Equal"), "blend": None},
    1429: {"stencil": (16, 255, "Equal"), "blend": None},
    1447: {"stencil": (32, 49, "Equal"), "blend": None},
    1466: {"stencil": (2, 162, "Equal"), "blend": None},
    1484: {"stencil": (32, 48, "Equal"), "blend": "One One"},
    1511: {"stencil": None, "blend": None},
}

SAMPLER_MAP = {
    1419: {"s0": "sampler_T5", "s1": "sampler_T1"},
    1447: {"s0": "sampler_T2", "s1": "sampler_T1"},
    1466: {"s0": "sampler_T2", "s1": "sampler_T1"},
    1484: {"s0": "sampler_T1"},
    1511: {"s0": "sampler_T0"},
}


def main_body(source):
    start = source.index("void main(")
    brace = source.index("{", start)
    depth = 0
    end = None
    for index in range(brace, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                end = index
                break
    if end is None:
        raise ValueError("unbalanced main function")
    return source[brace + 1:end], source[start:brace]


def transform_body(event_id, source):
    body, signature = main_body(source)
    outputs = 2 if re.search(r"\bo1\s*:", signature) else 1
    body = body.replace("precise ", "")
    body = re.sub(r"\bcb0\b", "_CB0", body)
    for slot in range(8):
        body = re.sub(r"\bt%d\b" % slot, "_T%d" % slot, body)
    for original, replacement in SAMPLER_MAP.get(event_id, {}).items():
        body = re.sub(r"\b%s\b" % original, replacement, body)
    body = re.sub(r"\bo0\b", "output.rt0", body)
    body = re.sub(r"\bo1\b", "output.rt1", body)
    body = re.sub(r"\breturn\s*;", "return output;", body)
    prefix = "    float4 v0 = input.positionCS;\n    float4 v1 = input.texcoord;\n"
    return prefix + body.strip() + "\n", outputs


def make_shader(event_id, source):
    body, outputs = transform_body(event_id, source)
    state = PASS_STATE[event_id]
    stencil = ""
    if state["stencil"]:
        reference, mask, comp = state["stencil"]
        stencil = f"""
        Stencil
        {{
            Ref {reference}
            ReadMask {mask}
            WriteMask 0
            Comp {comp}
            Pass Keep
        }}"""
    blend = f'\n        Blend {state["blend"]}' if state["blend"] else ""
    second = "\n        float4 rt1 : SV_Target1;" if outputs == 2 else ""
    return f'''// Generated from frame 38112 EID {event_id} DXBC. Do not hand-fit this pass.
Shader "Hidden/Kiana/Frame38112/EID{event_id}"
{{
    Properties
    {{
        [HideInInspector] _T0 ("t0", 2D) = "black" {{}}
        [HideInInspector] _T1 ("t1", 2D) = "black" {{}}
        [HideInInspector] _T2 ("t2", 2D) = "black" {{}}
        [HideInInspector] _T3 ("t3", 2D) = "black" {{}}
        [HideInInspector] _T4 ("t4", 2D) = "black" {{}}
        [HideInInspector] _T5 ("t5", 2D) = "black" {{}}
        [HideInInspector] _T6 ("t6", 2D) = "black" {{}}
        [HideInInspector] _T7 ("t7", 2D) = "black" {{}}
    }}
    SubShader
    {{
        Pass
        {{
            Name "EID{event_id}"
            Cull Off
            ZWrite Off
            ZTest Always{blend}{stencil}
            HLSLPROGRAM
            #pragma target 5.0
            #pragma only_renderers d3d11
            #pragma vertex vert
            #pragma fragment frag

            float4 _CB0[188];
            Texture2D<float4> _T0; SamplerState sampler_T0;
            Texture2D<float4> _T1; SamplerState sampler_T1;
            Texture2D<float4> _T2; SamplerState sampler_T2;
            Texture2D<float4> _T3; SamplerState sampler_T3;
            Texture2D<float4> _T4; SamplerState sampler_T4;
            Texture2D<float4> _T5; SamplerState sampler_T5;
            Texture2D<float4> _T6; SamplerState sampler_T6;
            Texture2D<float4> _T7; SamplerState sampler_T7;

            struct Varyings
            {{
                float4 positionCS : SV_POSITION;
                float4 texcoord : TEXCOORD0;
            }};
            struct FragmentOutput
            {{
                float4 rt0 : SV_Target0;{second}
            }};

            Varyings vert(uint vertexID : SV_VertexID)
            {{
                Varyings output;
                uint2 packed = uint2((vertexID << 1u) & 2u, vertexID & 2u);
                float2 corner = float2(packed);
                output.positionCS = float4(corner * 2.0 - 1.0, 1.0, 1.0);
                output.texcoord = float4(corner.x, 1.0 - corner.y, 0.0, 0.0);
                return output;
            }}

            FragmentOutput frag(Varyings input)
            {{
                FragmentOutput output;
{indent(body, 16)}            }}
            ENDHLSL
        }}
    }}
}}
'''


def indent(text, spaces):
    pad = " " * spaces
    return "".join(pad + line if line.strip() else line for line in text.splitlines(True))


def load_constants(*files):
    events = {}
    for filename in files:
        payload = json.loads(Path(filename).read_text(encoding="utf-8-sig"))
        for event in payload["events"]:
            buffers = event.get("pixelConstantBuffers", [])
            if buffers:
                events[int(event["eventId"])] = buffers[0]["float4s"]
    return events


def cs_float(value):
    if value != value:
        return "float.NaN"
    if value == float("inf"):
        return "float.PositiveInfinity"
    if value == float("-inf"):
        return "float.NegativeInfinity"
    return format(float(value), ".9g") + "f"


def write_constants(path, constants):
    lines = [
        "// Generated from captured frame 38112 constant buffers.\n",
        "using UnityEngine;\n\n",
        "namespace Kiana.Frame38112\n{\n",
        "    public static class Frame38112DeferredConstants\n    {\n",
        "        public static Vector4[] ForEvent(int eventId)\n        {\n",
        "            switch (eventId)\n            {\n",
    ]
    for event_id in sorted(constants):
        lines.append(f"                case {event_id}: return EID{event_id};\n")
    lines.extend([
        "                default: return null;\n",
        "            }\n        }\n\n",
    ])
    for event_id, vectors in sorted(constants.items()):
        lines.append(f"        static readonly Vector4[] EID{event_id} =\n        {{\n")
        for values in vectors:
            lines.append("            new Vector4(%s),\n" % ", ".join(cs_float(v) for v in values))
        lines.append("        };\n\n")
    lines.append("    }\n}\n")
    Path(path).write_text("".join(lines), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--hlsl-dir", required=True)
    parser.add_argument("--unity-dir", required=True)
    parser.add_argument("--constants-json", required=True)
    parser.add_argument("--copy-constants-json", required=True)
    args = parser.parse_args()
    hlsl_dir = Path(args.hlsl_dir)
    unity_dir = Path(args.unity_dir)
    shader_dir = unity_dir / "Shaders/Deferred"
    shader_dir.mkdir(parents=True, exist_ok=True)
    for event_id in PASS_STATE:
        source = (hlsl_dir / f"EID{event_id}-PS.hlsl").read_text(encoding="utf-8")
        (shader_dir / f"Frame38112_EID{event_id}.shader").write_text(
            make_shader(event_id, source), encoding="utf-8"
        )
    constants = load_constants(args.constants_json, args.copy_constants_json)
    write_constants(unity_dir / "Frame38112DeferredConstants.generated.cs", constants)
