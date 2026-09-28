Shader "Kiana/ToonInvertedHull"
{
    Properties
    {
        _InkColor ("Ink", Color) = (0.022,0.018,0.050,1)
        _ReferenceWidthPx ("RDC 2880x1368 shell width, pixels", Range(0,4)) = 2
        _Cull ("Cull", Float) = 1
        _ZTest ("Depth test", Float) = 4
    }
    SubShader
    {
        Tags { "Queue"="Geometry+20" "RenderType"="Opaque" }
        Cull [_Cull]
        ZWrite Off
        ZTest [_ZTest]
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"
            float4 _InkColor;
            float _ReferenceWidthPx;
            struct appdata { float4 vertex : POSITION; float3 normal : NORMAL; };
            struct v2f { float4 vertex : SV_POSITION; };
            v2f vert(appdata v)
            {
                v2f o;
                float4 clip = UnityObjectToClipPos(v.vertex);
                float4 normalTip = UnityObjectToClipPos(
                    float4(v.vertex.xyz + normalize(v.normal) * 0.01, 1));
                float2 referenceHalfSize = float2(1440, 684);
                float2 screenDirection =
                    (normalTip.xy / normalTip.w - clip.xy / clip.w) * referenceHalfSize;
                screenDirection /= max(length(screenDirection), 0.00001);
                clip.xy += screenDirection * (_ReferenceWidthPx / referenceHalfSize) * clip.w;
                o.vertex = clip;
                return o;
            }
            fixed4 frag(v2f i) : SV_Target { return _InkColor; }
            ENDCG
        }
    }
}
