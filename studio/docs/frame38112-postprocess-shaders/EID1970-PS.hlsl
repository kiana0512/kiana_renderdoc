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
    r0 = min(max((cb0[173].xyxy * float4(-18.3031, -18.3031, -16.32244, -16.32244) + v1.xyxy), v2.xyxy), v2.zwzw);
    precise float4 r0_2;
    r0_2 = t0.Sample(s0, r0.xy) * float4(0.00008280537, 0.00008280537, 0.00008280537, 0.00008280537) + (t0.Sample(s0, r0.zw) * float4(0.0003933866, 0.0003933866, 0.0003933866, 0.0003933866));
    precise float4 r1;
    r1 = min(max((cb0[173].xyxy * float4(-14.34241, -14.34241, -12.36296, -12.36296) + v1.xyxy), v2.xyxy), v2.zwzw);
    precise float4 r0_3;
    r0_3 = t0.Sample(s0, r1.zw) * float4(0.005201502, 0.005201502, 0.005201502, 0.005201502) + (t0.Sample(s0, r1.xy) * float4(0.001563755, 0.001563755, 0.001563755, 0.001563755) + r0_2);
    precise float4 r1_2;
    r1_2 = min(max((cb0[173].xyxy * float4(-10.38401, -10.38401, -8.405515, -8.405515) + v1.xyxy), v2.xyxy), v2.zwzw);
    precise float4 r0_4;
    r0_4 = t0.Sample(s0, r1_2.zw) * float4(0.03372603, 0.03372603, 0.03372603, 0.03372603) + (t0.Sample(s0, r1_2.xy) * float4(0.01447843, 0.01447843, 0.01447843, 0.01447843) + r0_3);
    precise float4 r1_3;
    r1_3 = min(max((cb0[173].xyxy * float4(-6.427385, -6.427385, -4.449542, -4.449542) + v1.xyxy), v2.xyxy), v2.zwzw);
    precise float4 r0_5;
    r0_5 = t0.Sample(s0, r1_3.zw) * float4(0.1072673, 0.1072673, 0.1072673, 0.1072673) + (t0.Sample(s0, r1_3.xy) * float4(0.06574705, 0.06574705, 0.06574705, 0.06574705) + r0_4);
    precise float4 r1_4;
    r1_4 = min(max((cb0[173].xyxy * float4(-2.471902, -2.471902, -0.4943747, -0.4943747) + v1.xyxy), v2.xyxy), v2.zwzw);
    precise float4 r0_6;
    r0_6 = t0.Sample(s0, r1_4.zw) * float4(0.1673879, 0.1673879, 0.1673879, 0.1673879) + (t0.Sample(s0, r1_4.xy) * float4(0.1464697, 0.1464697, 0.1464697, 0.1464697) + r0_5);
    precise float4 r1_5;
    r1_5 = min(max((cb0[173].xyxy * float4(1.48313, 1.48313, 3.460702, 3.460702) + v1.xyxy), v2.xyxy), v2.zwzw);
    precise float4 r0_7;
    r0_7 = t0.Sample(s0, r1_5.zw) * float4(0.1281654, 0.1281654, 0.1281654, 0.1281654) + (t0.Sample(s0, r1_5.xy) * float4(0.1601027, 0.1601027, 0.1601027, 0.1601027) + r0_6);
    precise float4 r1_6;
    r1_6 = min(max((cb0[173].xyxy * float4(5.438433, 5.438433, 7.416409, 7.416409) + v1.xyxy), v2.xyxy), v2.zwzw);
    precise float4 r0_8;
    r0_8 = t0.Sample(s0, r1_6.zw) * float4(0.04814892, 0.04814892, 0.04814892, 0.04814892) + (t0.Sample(s0, r1_6.xy) * float4(0.08586894, 0.08586894, 0.08586894, 0.08586894) + r0_7);
    precise float4 r1_7;
    r1_7 = min(max((cb0[173].xyxy * float4(9.394713, 9.394713, 11.37342, 11.37342) + v1.xyxy), v2.xyxy), v2.zwzw);
    precise float4 r0_9;
    r0_9 = t0.Sample(s0, r1_7.zw) * float4(0.008873496, 0.008873496, 0.008873496, 0.008873496) + (t0.Sample(s0, r1_7.xy) * float4(0.02259492, 0.02259492, 0.02259492, 0.02259492) + r0_8);
    precise float4 r1_8;
    r1_8 = min(max((cb0[173].xyxy * float4(13.35262, 13.35262, 15.33235, 15.33235) + v1.xyxy), v2.xyxy), v2.zwzw);
    precise float4 r0_10;
    r0_10 = t0.Sample(s0, r1_8.zw) * float4(0.0008019903, 0.0008019903, 0.0008019903, 0.0008019903) + (t0.Sample(s0, r1_8.xy) * float4(0.002916224, 0.002916224, 0.002916224, 0.002916224) + r0_9);
    precise float4 r1_9;
    r1_9 = min(max((cb0[173].xyxy * float4(17.31269, 17.31269, 19.0, 19.0) + v1.xyxy), v2.xyxy), v2.zwzw);
    o0 = t0.Sample(s0, r1_9.zw) * float4(0.00002509824, 0.00002509824, 0.00002509824, 0.00002509824) + (t0.Sample(s0, r1_9.xy) * float4(0.0001845513, 0.0001845513, 0.0001845513, 0.0001845513) + r0_10);
    return;
}

