// ===== shader #0 =====
// Decompiled by d3dasm-decompiler.
cbuffer cb0_buffer : register(b0)
{
    float4 cb0[175];
};
cbuffer cb1_buffer : register(b1)
{
    float4 cb1[1];
};
SamplerState s0 : register(s0);
Texture2D<float4> t0 : register(t0);
Texture2D<float4> t1 : register(t1);

void main(float4 v1 : TEXCOORD0, out precise float4 o0 : SV_Target0)
{
    precise float4 r0;
    r0 = t1.Sample(s0, (v1.xy * cb0[172].xy + cb0[172].zw)) * cb1[0].yyyy;
    precise float4 r0_2;
    r0_2 = t0.Sample(s0, v1.xy) * cb1[0].xxxx + r0;
    precise float4 r0_3;
    r0_3 = t1.Sample(s0, (v1.xy * cb0[173].xy + cb0[173].zw)) * cb1[0].zzzz + r0_2;
    o0 = t1.Sample(s0, (v1.xy * cb0[174].xy + cb0[174].zw)) * cb1[0].wwww + r0_3;
    return;
}

