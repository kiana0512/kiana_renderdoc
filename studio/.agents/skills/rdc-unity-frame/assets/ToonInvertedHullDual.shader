Shader "Kiana/ToonInvertedHullDual"
{
    Properties
    {
        _InkColor ("Ink", Color) = (0.022,0.018,0.050,1)
        _ReferenceWidthPx ("Reference width, pixels", Range(0,4)) = 1
        _CapturedOutlineXYBlend ("Captured outline VS XY blend", Range(0,1)) = 0
        _ZTest ("Depth test", Float) = 4
        _ZWrite ("Depth write", Float) = 0
        _StencilRef ("Stencil reference", Float) = 0
        _StencilReadMask ("Stencil read mask", Float) = 255
        _StencilWriteMask ("Stencil write mask", Float) = 0
        _StencilCompFront ("Stencil front compare", Float) = 8
        _StencilCompBack ("Stencil back compare", Float) = 8
        _StencilPassFront ("Stencil front pass", Float) = 0
        _StencilPassBack ("Stencil back pass", Float) = 0
    }
    SubShader
    {
        Tags { "Queue"="Geometry+20" "RenderType"="Opaque" }
        Cull Off
        ZWrite [_ZWrite]
        ZTest [_ZTest]
        Stencil
        {
            Ref [_StencilRef]
            ReadMask [_StencilReadMask]
            WriteMask [_StencilWriteMask]
            CompFront [_StencilCompFront]
            CompBack [_StencilCompBack]
            PassFront [_StencilPassFront]
            PassBack [_StencilPassBack]
        }
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma target 3.0
            #include "UnityCG.cginc"
            float4 _InkColor;
            float _ReferenceWidthPx;
            float _CapturedOutlineXYBlend;
            float _RdcDepthFlip;
            struct appdata { float4 vertex : POSITION; float3 normal : NORMAL; float4 outlineClip : TEXCOORD5; };
            struct v2f { float4 vertex : SV_POSITION; };
            v2f vert(appdata v)
            {
                v2f o;
                float4 clip = UnityObjectToClipPos(v.vertex);
                float4 normalTip = UnityObjectToClipPos(
                    float4(v.vertex.xyz + normalize(v.normal) * 0.01, 1));
                float2 halfSize = float2(1440, 684);
                float2 direction =
                    (normalTip.xy / normalTip.w - clip.xy / clip.w) * halfSize;
                direction /= max(length(direction), 0.00001);
                clip.xy += direction * (_ReferenceWidthPx / halfSize) * clip.w;
                if (_RdcDepthFlip > 0.5 && _CapturedOutlineXYBlend > 0.0 &&
                    v.outlineClip.w > 0.0)
                {
                    float2 sourceXY = float2(v.outlineClip.x, -v.outlineClip.y) *
                        (clip.w / v.outlineClip.w);
                    clip.xy = lerp(clip.xy, sourceXY, _CapturedOutlineXYBlend);
                }
                clip.z = lerp(clip.z, clip.w - clip.z, _RdcDepthFlip);
                o.vertex = clip;
                return o;
            }
            fixed4 frag(v2f i, float faceSign : VFACE) : SV_Target
            {
                // The captured camera reverses handedness relative to the
                // editable Scene view. Keep the visible shell side distinct.
                clip(_RdcDepthFlip > 0.5 ? faceSign : -faceSign);
                return _InkColor;
            }
            ENDCG
        }
    }
}
