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
    r0 = min(max((cb0[173].xyxy * float4(-4.095285, -4.095285, -2.222628, -2.222628) + v1.xyxy), v2.xyxy), v2.zwzw);
    precise float4 r0_2;
    r0_2 = t0.Sample(s0, r0.xy) * float4(0.005704662, 0.005704662, 0.005704662, 0.005704662) + (t0.Sample(s0, r0.zw) * float4(0.1334844, 0.1334844, 0.1334844, 0.1334844));
    precise float4 r1;
    r1 = min(max((cb0[173].xyxy * float4(-0.437803, -0.437803, 1.320767, 1.320767) + v1.xyxy), v2.xyxy), v2.zwzw);
    precise float4 r0_3;
    r0_3 = t0.Sample(s0, r1.zw) * float4(0.3234969, 0.3234969, 0.3234969, 0.3234969) + (t0.Sample(s0, r1.xy) * float4(0.501892, 0.501892, 0.501892, 0.501892) + r0_2);
    precise float4 r1_2;
    r1_2 = min(max((cb0[173].xyxy * float4(3.147974, 3.147974, 5.0, 5.0) + v1.xyxy), v2.xyxy), v2.zwzw);
    o0 = t0.Sample(s0, r1_2.zw) * float4(0.0005435675, 0.0005435675, 0.0005435675, 0.0005435675) + (t0.Sample(s0, r1_2.xy) * float4(0.03487847, 0.03487847, 0.03487847, 0.03487847) + r0_3);
    return;
}

