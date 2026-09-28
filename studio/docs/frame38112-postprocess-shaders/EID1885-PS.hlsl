// ===== shader #0 =====
// Decompiled by d3dasm-decompiler.
cbuffer cb0_buffer : register(b0)
{
    float4 cb0[2];
};
SamplerState s0 : register(s0);
Texture2D<float4> t0 : register(t0);

void main(float4 v1 : TEXCOORD0, float4 v2 : TEXCOORD1, out precise float4 o0 : SV_Target0)
{
    precise float4 r0;
    r0 = ((t0.SampleLevel(s0, v1.xy, 0.0) + t0.SampleLevel(s0, v1.zw, 0.0)) + t0.SampleLevel(s0, v2.xy, 0.0)) + t0.SampleLevel(s0, v2.zw, 0.0);
    o0.w = (r0.w * 0.25);
    o0.xyz = max((r0.xyz * float3(0.25, 0.25, 0.25) + (-cb0[1].xxx)), float3(0.0, 0.0, 0.0)) * cb0[1].yyy;
    return;
}

