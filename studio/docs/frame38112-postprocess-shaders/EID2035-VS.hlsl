// ===== shader #0 =====
// Decompiled by d3dasm-decompiler.
void main(uint v0_raw : SV_VertexID0, out precise float4 o0 : SV_POSITION0, out precise float4 o1 : TEXCOORD0)
{
    uint4 v0 = uint4(v0_raw, 0u, 0u, 0u);
    precise float2 r0;
    r0 = float2(uint2((((v0.x << (1u & 31u)) & (((1u << (1u & 31u)) - 1u) << (1u & 31u))) | (0u & ~(((1u << (1u & 31u)) - 1u) << (1u & 31u)))), (v0.x & 2u)));
    o0.xy = r0 * float2(2.0, 2.0) + float2(-1.0, -1.0);
    o1.xy = float2(r0.x, ((-r0.y) + 1.0));
    o0.zw = float2(1.0, 1.0);
    return;
}

