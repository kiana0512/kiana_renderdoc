Shader "Hidden/Kiana/CapturedToonOutline"
{
    Properties
    {
        _MainTex ("Scene", 2D) = "white" {}
        _InkColor ("Ink", Color) = (0.035,0.028,0.080,1)
        _ThicknessPx ("Width in pixels", Range(0.5,4)) = 1.2
        _DepthThreshold ("Background threshold", Range(0.0001,0.1)) = 0.008
        _NormalThreshold ("Reserved", Range(0.01,1)) = 0.32
        _InkStrength ("Strength", Range(0,1)) = 0.9
    }
    SubShader
    {
        Cull Off ZWrite Off ZTest Always
        Pass
        {
            CGPROGRAM
            #pragma vertex vert_img
            #pragma fragment frag
            #include "UnityCG.cginc"
            sampler2D _MainTex;
            float4 _MainTex_TexelSize;
            float4 _InkColor;
            float _ThicknessPx, _DepthThreshold, _NormalThreshold, _InkStrength;

            float4 frag(v2f_img i) : SV_Target
            {
                float4 scene = tex2D(_MainTex, i.uv);
                float centerValue = max(scene.r, max(scene.g, scene.b));
                float exterior = 0;
                float2 pixel = _MainTex_TexelSize.xy * _ThicknessPx;
                [unroll] for (int j = 0; j < 4; j++)
                {
                    float2 offset = j == 0 ? float2(pixel.x, 0) :
                                    j == 1 ? float2(-pixel.x, 0) :
                                    j == 2 ? float2(0, pixel.y) : float2(0, -pixel.y);
                    float3 neighbor = tex2D(_MainTex, i.uv + offset).rgb;
                    exterior = max(exterior,
                        1.0 - step(_DepthThreshold, max(neighbor.r, max(neighbor.g, neighbor.b))));
                }
                float ink = step(_DepthThreshold, centerValue) * exterior * _InkStrength;
                return float4(lerp(scene.rgb, _InkColor.rgb, ink), scene.a);
            }
            ENDCG
        }
    }
}
