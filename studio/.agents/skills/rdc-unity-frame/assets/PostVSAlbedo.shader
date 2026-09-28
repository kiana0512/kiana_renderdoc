Shader "Kiana/PostVSAlbedo"
{
    Properties
    {
        _MainTex ("Captured diffuse", 2D) = "white" {}
        _Tint ("Tint", Color) = (1,1,1,1)
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" "Queue"="Geometry" }
        Cull Off
        ZWrite On
        ZTest LEqual
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"
            sampler2D _MainTex;
            fixed4 _Tint;
            struct appdata
            {
                float4 vertex : POSITION;
                float2 uvOverW : TEXCOORD0;
                float2 reciprocalW : TEXCOORD1;
            };
            struct v2f
            {
                float4 position : SV_POSITION;
                float2 uvOverW : TEXCOORD0;
                float reciprocalW : TEXCOORD1;
            };
            v2f vert(appdata input)
            {
                v2f output;
                output.position = UnityObjectToClipPos(input.vertex);
                output.uvOverW = input.uvOverW;
                output.reciprocalW = input.reciprocalW.x;
                return output;
            }
            fixed4 frag(v2f input) : SV_Target
            {
                float2 uv = input.uvOverW / max(input.reciprocalW, 1e-8);
                return fixed4(tex2D(_MainTex, uv).rgb * _Tint.rgb, 1);
            }
            ENDCG
        }
    }
}
