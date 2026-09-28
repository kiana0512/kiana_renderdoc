// ===== shader #0 =====
// Decompiled by d3dasm-decompiler.
void main(uint v0_raw : SV_VertexID0, out precise float4 o0 : SV_POSITION0, out precise float4 o1 : TEXCOORD0)
{
    uint4 v0 = uint4(v0_raw, 0u, 0u, 0u);
    precise int r0;
    r0 = asint(v0.x >> 1u);
    precise float2 r1;
    r1 = float2(uint2(asuint(r0), (asuint(asint(v0.x & 1u) + r0) & 1u)));
    o0.xy = r1 * float2(2.0, 2.0) + float2(-1.0, -1.0);
    o1.xy = float2(r1.x, ((-r1.y) + 1.0));
    o0.zw = float2(1.0, 1.0);
    return;
}

