// ===== shader #0 =====
// Decompiled by d3dasm-decompiler.
SamplerState s0 : register(s0);
Texture2D<float4> t0 : register(t0);

void main(float4 v1 : TEXCOORD0, float4 v2 : TEXCOORD1, out precise float4 o0 : SV_Target0)
{
    o0 = (((t0.SampleLevel(s0, v1.xy, 0.0) + t0.SampleLevel(s0, v1.zw, 0.0)) + t0.SampleLevel(s0, v2.xy, 0.0)) + t0.SampleLevel(s0, v2.zw, 0.0)) * float4(0.25, 0.25, 0.25, 0.25);
    return;
}

