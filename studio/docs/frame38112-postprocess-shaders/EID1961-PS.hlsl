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
    r0 = min(max((cb0[173].xyxy * float4(-14.26509, -14.26509, -12.29338, -12.29338) + v1.xyxy), v2.xyxy), v2.zwzw);
    precise float4 r0_2;
    r0_2 = t0.Sample(s0, r0.xy) * float4(0.00014632, 0.00014632, 0.00014632, 0.00014632) + (t0.Sample(s0, r0.zw) * float4(0.0009470967, 0.0009470967, 0.0009470967, 0.0009470967));
    precise float4 r1;
    r1 = min(max((cb0[173].xyxy * float4(-10.32336, -10.32336, -8.354863, -8.354863) + v1.xyxy), v2.xyxy), v2.zwzw);
    precise float4 r0_3;
    r0_3 = t0.Sample(s0, r1.zw) * float4(0.01727958, 0.01727958, 0.01727958, 0.01727958) + (t0.Sample(s0, r1.xy) * float4(0.004646272, 0.004646272, 0.004646272, 0.004646272) + r0_2);
    precise float4 r1_2;
    r1_2 = min(max((cb0[173].xyxy * float4(-6.387677, -6.387677, -4.421542, -4.421542) + v1.xyxy), v2.xyxy), v2.zwzw);
    precise float4 r0_4;
    r0_4 = t0.Sample(s0, r1_2.zw) * float4(0.1042022, 0.1042022, 0.1042022, 0.1042022) + (t0.Sample(s0, r1_2.xy) * float4(0.04872663, 0.04872663, 0.04872663, 0.04872663) + r0_3);
    precise float4 r1_3;
    r1_3 = min(max((cb0[173].xyxy * float4(-2.456162, -2.456162, -0.4912108, -0.4912108) + v1.xyxy), v2.xyxy), v2.zwzw);
    precise float4 r0_5;
    r0_5 = t0.Sample(s0, r1_3.zw) * float4(0.207937, 0.207937, 0.207937, 0.207937) + (t0.Sample(s0, r1_3.xy) * float4(0.1690129, 0.1690129, 0.1690129, 0.1690129) + r0_4);
    precise float4 r1_4;
    r1_4 = min(max((cb0[173].xyxy * float4(1.473654, 1.473654, 3.438778, 3.438778) + v1.xyxy), v2.xyxy), v2.zwzw);
    precise float4 r0_6;
    r0_6 = t0.Sample(s0, r1_4.zw) * float4(0.1373738, 0.1373738, 0.1373738, 0.1373738) + (t0.Sample(s0, r1_4.xy) * float4(0.1940565, 0.1940565, 0.1940565, 0.1940565) + r0_5);
    precise float4 r1_5;
    r1_5 = min(max((cb0[173].xyxy * float4(5.404496, 5.404496, 7.371121, 7.371121) + v1.xyxy), v2.xyxy), v2.zwzw);
    precise float4 r0_7;
    r0_7 = t0.Sample(s0, r1_5.zw) * float4(0.03003788, 0.03003788, 0.03003788, 0.03003788) + (t0.Sample(s0, r1_5.xy) * float4(0.07376206, 0.07376206, 0.07376206, 0.07376206) + r0_6);
    precise float4 r1_6;
    r1_6 = min(max((cb0[173].xyxy * float4(9.338933, 9.338933, 11.30817, 11.30817) + v1.xyxy), v2.xyxy), v2.zwzw);
    precise float4 r0_8;
    r0_8 = t0.Sample(s0, r1_6.zw) * float4(0.002171654, 0.002171654, 0.002171654, 0.002171654) + (t0.Sample(s0, r1_6.xy) * float4(0.009275736, 0.009275736, 0.009275736, 0.009275736) + r0_7);
    precise float4 r1_7;
    r1_7 = min(max((cb0[173].xyxy * float4(13.27902, 13.27902, 15.0, 15.0) + v1.xyxy), v2.xyxy), v2.zwzw);
    o0 = t0.Sample(s0, r1_7.zw) * float4(0.00003878852, 0.00003878852, 0.00003878852, 0.00003878852) + (t0.Sample(s0, r1_7.xy) * float4(0.0003853923, 0.0003853923, 0.0003853923, 0.0003853923) + r0_8);
    return;
}

