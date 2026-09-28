// ===== shader #0 =====
// Decompiled by d3dasm-decompiler.
cbuffer cb0_buffer : register(b0)
{
    float4 cb0[139];
};
cbuffer cb1_buffer : register(b1)
{
    float4 cb1[30];
};
SamplerState s0 : register(s0);
SamplerState s1 : register(s1);
SamplerState s2 : register(s2);
SamplerState s3 : register(s3);
Texture2D<float4> t0 : register(t0);
Texture2D<float4> t1 : register(t1);
Texture2D<float4> t2 : register(t2);
Texture2D<float4> t3 : register(t3);
Texture2D<float4> t4 : register(t4);

void main(float4 v1 : TEXCOORD0, out precise float4 o0 : SV_Target0)
{
    precise uint r0;
    r0 = (0.0 < cb1[11].w) ? 0xffffffffu : 0u;
    precise float2 r0_9;
    precise float2 r1_2;
    precise float4 r2;
    if (r0 != 0u)
    {
        precise float4 r1;
        r1 = t2.Sample(s2, v1.xy);
        precise float2 r0_8;
        r0_8 = r1.xy * float2(0.1, 0.1);
        r1_2 = r1.xy * float2(0.1, 0.1) + v1.xy;
        precise float2 r1_3;
        r1_3 = (r1.zz * r0_8) * cb1[11].ww;
        r2 = r1_3.xyxy * cb1[11].xxyy + r0_8.xyxy;
        r0_9 = r1_3 * cb1[11].zz + r0_8;
    }
    else
    {
        r1_2 = v1.xy;
        r2 = float4(0.0, 0.0, 0.0, 0.0);
        r0_9 = float2(0.0, 0.0);
    }
    precise float4 r3_3;
    precise float4 r4;
    if (0.5 < cb1[24].w)
    {
        precise float2 r1_4;
        r1_4 = (v1.xy * float2(2.0, 2.0) + float2(-1.0, -1.0)) + (-(cb1[24].xy + float2(-0.5, -0.5)));
        precise float2 r3;
        r3 = ((dot(r1_4, r1_4).xx * r1_4) * cb1[12].zz) * float2(-0.33333334, -0.33333334);
        precise float r3_4;
        r3_4 = 0.0001;
        precise float r3_2;
        r3_2 = cb1[12].z * 0.94280905;
        precise float2 r1_5;
        r1_5 = r3_2.xx * (exp2((log2((sqrt(dot(r3, r3)) / r3_2)) * cb1[24].z)).xx * (rsqrt(dot(float3(r3, r3_4), float3(r3, r3_4))).xx * r3));
        r3_3.xyz = t0.Sample(s0, (r1_5 * cb1[27].ww + (r0_9 + v1.xy))).zzz * cb1[27].xyz + (t0.Sample(s0, (r1_5 * cb1[25].ww + (r2.xy + v1.xy))).xxx * cb1[25].xyz + (t0.Sample(s0, (r1_5 * cb1[26].ww + (r2.zw + v1.xy))).yyy * cb1[26].xyz));
        r4 = t0.Sample(s0, r1_2).wxyz;
    }
    else
    {
        if (r0 != 0u)
        {
            r3_3 = t0.Sample(s0, (r0_9 + v1.xy));
            r3_3.x = t0.Sample(s0, (r2.xy + v1.xy)).x;
            r3_3.y = t0.Sample(s0, (r2.zw + v1.xy)).y;
        }
        else
        {
            r3_3 = t0.Sample(s0, r1_2);
        }
        r4 = t0.Sample(s0, r1_2).wxyz;
    }
    precise uint2 r0_10;
    r0_10 = (float2(0.0, 0.0) < cb1[21].xy) ? uint2(0xffffffffu, 0xffffffffu) : uint2(0u, 0u);
    if (((r0_10.y | r0_10.x) & ((cb1[21].z < 0.5) ? 0xffffffffu : 0u)) != 0u)
    {
        precise float r0_2;
        r0_2 = (r1_2.y * cb0[138].y) * cb1[28].x;
        precise float r0_11;
        r0_11 = r0_2 + r0_2;
        precise float2 r0_12;
        r0_12 = (((r0_11 >= (-r0_11)) ? 0xffffffffu : 0u).xx != 0u) ? float2(2.0, 0.5) : float2(-2.0, -0.5);
        precise float r0_3;
        r0_3 = frac((r0_12.y * r0_2));
        precise float r0_14;
        r0_14 = r0_3 * r0_12.x;
        precise float r0_4;
        r0_4 = cb1[28].z * (((1.0 < r0_14) ? ((-r0_12.x) * r0_3 + 2.0) : r0_14) * 2.0 + -1.0) + r1_2.x;
        precise float r0_15;
        r0_15 = cb0[138].w * cb0[138].x;
        precise float4 r2_2;
        r2_2 = t3.Sample(s3, float2(r0_4, (cb1[29].z * ((0.5 >= frac((((r0_4 + abs(cb1[29].y)) * r0_15 + (-(r1_2.y * cb1[29].y))) / dot(cb1[29].xx, r0_15.xx)))) ? 0.99999 : -1.0) + r1_2.y)));
        precise float3 r0_5;
        r0_5 = (asfloat(((r2_2.xyz >= float3(0.3, 0.3, 0.3)) ? uint3(0xffffffffu, 0xffffffffu, 0xffffffffu) : uint3(0u, 0u, 0u)) & uint3(1065353216u, 1065353216u, 1065353216u)) * ((exp2((log2(abs(r2_2.xyz)) * float3(0.33333334, 0.33333334, 0.33333334))) * float3(1.4938016, 1.4938016, 1.4938016) + (-r2_2.xyz)) + float3(-0.7, -0.7, -0.7)) + r2_2.xyz) * cb1[21].xxx;
        precise float3 r2_3;
        r2_3 = (((0.5 < cb1[22].x) ? 0xffffffffu : 0u).xxx != 0u) ? (r4.xxx * (dot(r3_3.xyz, float3(0.299, 0.587, 0.114)).xxx * r0_5 + (-r0_5)) + r0_5) : r0_5;
        if (r0_10.y != 0u)
        {
            r2_3 = (t4.Sample(s0, (r1_2 * cb1[20].xy + cb1[20].zw)).xyz * cb1[21].yyy) * r0_5 + r2_3;
        }
        r3_3.xyz = r2_3 + r3_3.xyz;
        o0.w = saturate((r2_3.z + (r2_3.y + r2_3.x)) * 0.3333 + r4.x);
    }
    else
    {
        o0.w = r4.x;
    }
    if (0.0 < cb1[7].z)
    {
        precise float2 r0_13;
        r0_13 = abs((r1_2 + (-cb1[7].xy))) * cb1[7].zz;
        precise float r0_6;
        r0_6 = r0_13.x * cb1[6].w;
        r3_3.xyz = (exp2((log2(max(((-dot(float2(r0_6, r0_13.y), float2(r0_6, r0_13.y))) + 1.0), 0.0)) * cb1[7].w)).xxx * ((-cb1[6].xyz) + float3(1.0, 1.0, 1.0)) + cb1[6].xyz) * r3_3.xyz;
    }
    if (0.0 < cb1[13].x)
    {
        precise float r0_7;
        r0_7 = t1.Sample(s1, (v1.xy * cb1[8].xy + cb1[8].zw)).w + -0.5;
        r3_3.xyz = (((r0_7 + r0_7).xxx * r3_3.xyz) * cb1[13].xxx) * (cb1[13].y * (-sqrt(dot(r3_3.xyz, float3(0.2126729, 0.7151522, 0.072175)))) + 1.0).xxx + r3_3.xyz;
    }
    o0.xyz = saturate(r3_3.xyz);
    return;
}

