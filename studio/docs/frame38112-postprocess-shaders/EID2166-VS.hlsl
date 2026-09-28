// ===== shader #0 =====
// Decompiled by d3dasm-decompiler.
cbuffer cb0_buffer : register(b0)
{
    float4 cb0[106];
};
cbuffer cb1_buffer : register(b1)
{
    float4 cb1[4];
};

void main(float4 v0 : POSITION0, float4 v1 : TEXCOORD0, out precise float4 o0 : SV_POSITION0, out precise float4 o1 : TEXCOORD0, out precise float4 o2 : TEXCOORD1)
{
    precise float4 r0;
    r0 = (cb1[2] * v0.zzzz + (cb1[0] * v0.xxxx + (v0.yyyy * cb1[1]))) + cb1[3];
    o0 = cb0[105] * r0.wwww + (cb0[104] * r0.zzzz + (cb0[102] * r0.xxxx + (r0.yyyy * cb0[103])));
    o1.xy = v1.xy;
    o2 = float4(0.0, 0.0, 0.0, 0.0);
    return;
}

