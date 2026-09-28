// ===== shader #0 =====
// Decompiled by d3dasm-decompiler.
cbuffer cb0_buffer : register(b0)
{
    float4 cb0[174];
};
SamplerState s0 : register(s0);
Texture2D<float4> t0 : register(t0);

void main(float4 v1 : TEXCOORD0, float4 v2 : TEXCOORD1, out precise float4 o0 : SV_Target0)
{
    precise float4 r0;
    r0 = min(max((cb0[173].xyxy * float4(-7.15882, -7.15882, -5.227498, -5.227498) + v1.xyxy), v2.xyxy), v2.zwzw);
    precise float4 r0_2;
    r0_2 = t0.Sample(s0, r0.xy) * float4(0.0009648678, 0.0009648678, 0.0009648678, 0.0009648678) + (t0.Sample(s0, r0.zw) * float4(0.01512981, 0.01512981, 0.01512981, 0.01512981));
    precise float4 r1;
    r1 = min(max((cb0[173].xyxy * float4(-3.314762, -3.314762, -1.417412, -1.417412) + v1.xyxy), v2.xyxy), v2.zwzw);
    precise float4 r0_3;
    r0_3 = t0.Sample(s0, r1.zw) * float4(0.2889, 0.2889, 0.2889, 0.2889) + (t0.Sample(s0, r1.xy) * float4(0.1009583, 0.1009583, 0.1009583, 0.1009583) + r0_2);
    precise float4 r1_2;
    r1_2 = min(max((cb0[173].xyxy * float4(0.4722446, 0.4722446, 2.364548, 2.364548) + v1.xyxy), v2.xyxy), v2.zwzw);
    precise float4 r0_4;
    r0_4 = t0.Sample(s0, r1_2.zw) * float4(0.1897708, 0.1897708, 0.1897708, 0.1897708) + (t0.Sample(s0, r1_2.xy) * float4(0.3564036, 0.3564036, 0.3564036, 0.3564036) + r0_3);
    precise float4 r1_3;
    r1_3 = min(max((cb0[173].xyxy * float4(4.268898, 4.268898, 6.190808, 6.190808) + v1.xyxy), v2.xyxy), v2.zwzw);
    precise float4 r0_5;
    r0_5 = t0.Sample(s0, r1_3.zw) * float4(0.004253626, 0.004253626, 0.004253626, 0.004253626) + (t0.Sample(s0, r1_3.xy) * float4(0.04346563, 0.04346563, 0.04346563, 0.04346563) + r0_4);
    o0 = t0.Sample(s0, min(max((cb0[173].xy * float2(8.0, 8.0) + v1.xy), v2.xy), v2.zw)) * float4(0.0001532399, 0.0001532399, 0.0001532399, 0.0001532399) + r0_5;
    return;
}

