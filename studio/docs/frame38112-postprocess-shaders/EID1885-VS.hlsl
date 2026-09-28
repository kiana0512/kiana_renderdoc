// ===== shader #0 =====
// Decompiled by d3dasm-decompiler.
cbuffer cb0_buffer : register(b0)
{
    float4 cb0[176];
};

void main(uint v0_raw : SV_VertexID0, out precise float4 o0 : SV_POSITION0, out precise float4 o1 : TEXCOORD0, out precise float4 o2 : TEXCOORD1)
{
    uint4 v0 = uint4(v0_raw, 0u, 0u, 0u);
    precise int r0;
    r0 = asint(v0.x >> 1u);
    precise float2 r1;
    r1 = float2(uint2(asuint(r0), (asuint(asint(v0.x & 1u) + r0) & 1u)));
    precise float r1_3;
    r1_3 = (-r1.y) + 1.0;
    precise float4 r1_2;
    r1_2 = float4(r1.x, r1_3, r1.x, r1_3) * cb0[172].xyxy + cb0[172].zwzw;
    o0.xy = (r1 * float2(2.0, 2.0) + float2(-1.0, -1.0)) * cb0[171].xy + cb0[171].zw;
    o0.zw = float2(1.0, 1.0);
    o1 = cb0[175].xyxy * float4(1.0, 1.0, 1.0, -1.0) + r1_2.zwzw;
    o2 = cb0[175].xyxy * float4(-1.0, -1.0, -1.0, 1.0) + r1_2;
    return;
}

