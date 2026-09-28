// ===== shader #0 =====
// Decompiled by d3dasm-decompiler.
cbuffer cb0_buffer : register(b0)
{
    float4 cb0[168];
};
SamplerState s0 : register(s0);
SamplerState s1 : register(s1);
Texture2D<float4> t0 : register(t0);
Texture2D<float4> t1 : register(t1);
Texture2D<float4> t2 : register(t2);
Texture2D<float4> t3 : register(t3);
Texture2D<float4> t4 : register(t4);

void main(noperspective float4 v0 : SV_POSITION0, float4 v1 : TEXCOORD0, out precise float4 o0 : SV_Target0, out precise float4 o1 : SV_Target1)
{
    precise int2 r0;
    r0 = int2(v0.xy);
    precise float r0_11;
    r0_11 = t0.Load(int3(r0, 0)).x;
    precise int3 r1;
    r1 = r0.xxy + int3(-1, 1, -1);
    precise int r1_9;
    r1_9 = 0;
    precise float r2;
    r2 = t0.Load(int3(r1.xz, r1_9)).x;
    precise float r0_10;
    r0_10 = t0.Load(int3(r1.yz, r1_9)).x;
    precise float3 r2_2;
    r2_2 = (((r2 >= r0_11) ? 0xffffffffu : 0u).xxx != 0u) ? float3(r2, asfloat(r1.xz)) : float3(r0_11, asfloat(r0));
    precise float3 r1_2;
    r1_2 = (((r0_10 >= r2_2.x) ? 0xffffffffu : 0u).xxx != 0u) ? float3(r0_10, asfloat(r1.yz)) : r2_2;
    precise int3 r0_2;
    r0_2 = r0.xyx + int3(-1, 1, 1);
    precise int r0_12;
    r0_12 = 0;
    precise float r2_3;
    r2_3 = t0.Load(int3(r0_2.xy, r0_12)).x;
    precise float3 r1_3;
    r1_3 = (((r2_3 >= r1_2.x) ? 0xffffffffu : 0u).xxx != 0u) ? float3(r2_3, asfloat(r0_2.xy)) : r1_2;
    precise float4 r0_3;
    r0_3 = t1.Load(int3(((((t0.Load(int3(r0_2.zy, r0_12)).x >= r1_3.x) ? 0xffffffffu : 0u).xx != 0u) ? r0_2.zy : asint(r1_3.yz)), 0));
    precise float2 r0_4;
    r0_4 = r0_3.xy + float2(-0.49803922, -0.49803922);
    precise float2 r1_7;
    r1_7 = r0_4 + r0_4;
    precise float2 r0_5;
    r0_5 = (((0.5 < cb0[167].x) ? 0xffffffffu : 0u).xx != 0u) ? float2(0.0, 0.0) : (float2(((-asint((float2(0.0, 0.0) < r0_4) ? uint2(0xffffffffu, 0xffffffffu) : uint2(0u, 0u))) + asint((r0_4 < float2(0.0, 0.0)) ? uint2(0xffffffffu, 0xffffffffu) : uint2(0u, 0u)))) * (r1_7 * r1_7));
    precise float2 r1_4;
    r1_4 = (((0.5 < (abs(ddy_coarse(r0_3.w)) + abs(ddx_coarse(r0_3.w)))) ? 0xffffffffu : 0u).xx != 0u) ? float2(1.0, 1.0) : float2(r0_3.w, t1.SampleLevel(s0, v1.xy, 0.0).w);
    precise float4 r2_4;
    r2_4 = (-asfloat((((0.5 >= r1_4.x) ? 0xffffffffu : 0u) & 1065353216u).xxxx)) * cb0[140].zwzw + v1.xyxy;
    precise float4 r3;
    r3 = t2.SampleLevel(s0, r2_4.zw, 0.0);
    precise float2 r1_5;
    r1_5 = (-r0_5) + v1.xy;
    if (0.1 < abs(((-t4.SampleLevel(s1, r1_5, 0.0).x) + r0_3.z)))
    {
        o0 = r3;
        o1.x = r0_3.z;
        return;
    }
    else
    {
        precise float4 r4;
        r4 = t3.SampleLevel(s0, r1_5, 0.0);
        precise float4 r2_5;
        r2_5 = cb0[138].zwzw * float4(-0.5, -0.5, 0.5, 0.5) + r2_4;
        precise float4 r5;
        r5 = t2.SampleLevel(s0, r2_5.xy, 0.0);
        precise float4 r6;
        r6 = t2.SampleLevel(s0, r2_5.zw, 0.0);
        precise float4 r2_6;
        r2_6 = ((-(r6 + (t2.SampleLevel(s0, r2_5.xw, 0.0) + (r5 + t2.SampleLevel(s0, r2_5.zy, 0.0))))) * float4(0.25, 0.25, 0.25, 0.25) + r3) * cb0[139].xxxx + r3;
        precise float3 r2_7;
        r2_7 = min(max(r2_6.xyz, float3(0.0, 0.0, 0.0)), float3(65472.0, 65472.0, 65472.0));
        precise float3 r1_6;
        r1_6 = (((r5.xyz + r6.xyz) * float3(4.0, 4.0, 4.0) + (-(r3.xyz + r3.xyz))) + r2_7) * float3(0.14285715, 0.14285715, 0.14285715);
        precise float3 r5_2;
        r5_2 = rcp((max(r5.z, max(r5.y, r5.x)) + 1.0)).xxx * r5.xyz;
        precise float3 r6_2;
        r6_2 = rcp((max(r6.z, max(r6.y, r6.x)) + 1.0)).xxx * r6.xyz;
        precise float r0_9;
        r0_9 = rcp((max(r2_7.z, max(r2_7.y, r2_7.x)) + 1.0));
        precise float3 r7;
        r7 = r0_9.xxx * r2_7;
        precise float2 r1_8;
        r1_8 = min((sqrt(dot(r0_5, r0_5)).xx * float2(80.0, 5000.0)), float2(1.0, 1.0)) * float2(-3.75, -0.25) + float2(4.0, 0.95);
        precise float r0_6;
        r0_6 = (-dot(r7, float3(0.2126729, 0.7151522, 0.072175))) + dot((rcp((max(r1_6.z, max(r1_6.y, r1_6.x)) + 1.0)).xxx * r1_6), float3(0.2126729, 0.7151522, 0.072175));
        precise float3 r8;
        r8 = (-r1_8.xxx) * abs(r0_6.xxx) + min(r5_2, r6_2);
        precise float3 r5_3;
        r5_3 = r1_8.xxx * abs(r0_6.xxx) + max(r5_2, r6_2);
        precise float3 r6_3;
        r6_3 = (r8 + r5_3) * float3(0.5, 0.5, 0.5);
        precise float3 r4_2;
        r4_2 = r4.xyz * rcp((max(r4.z, max(r4.y, r4.x)) + 1.0)).xxx + (-r6_3);
        precise float3 r5_4;
        r5_4 = abs((((-r8) + r5_3) * float3(0.5, 0.5, 0.5))) / max(abs(r4_2), float3(0.0001, 0.0001, 0.0001));
        o0.w = saturate(saturate((-r2_6.w) + r4.w) * 0.25 + r2_6.w);
        precise float3 r0_7;
        r0_7 = r1_8.yyy * ((-r2_7) * r0_9.xxx + (r4_2 * min(min(r5_4.z, min(r5_4.y, r5_4.x)), 1.0).xxx + r6_3)) + r7;
        precise float3 r0_8;
        r0_8 = min(max((r0_7 * rcp(((-max(r0_7.z, max(r0_7.y, r0_7.x))) + 1.0)).xxx), float3(0.0, 0.0, 0.0)), float3(65472.0, 65472.0, 65472.0));
        o0.xyz = r1_4.yyy * ((-r0_8) + r3.xyz) + r0_8;
        o1.x = r0_3.z;
        return;
    }
}

