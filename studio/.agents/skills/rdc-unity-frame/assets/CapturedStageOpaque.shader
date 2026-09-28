Shader "Kiana/CapturedStageOpaque"
{
    Properties { _MainTex ("Stage image", 2D) = "black" {} }
    SubShader
    {
        Tags { "RenderType"="Opaque" "Queue"="Background" }
        Cull Off ZWrite Off ZTest Always
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"
            sampler2D _MainTex;
            struct Input { float4 vertex : POSITION; float2 uv : TEXCOORD0; };
            struct Output { float4 vertex : SV_POSITION; float2 uv : TEXCOORD0; };
            Output vert(Input input)
            {
                Output output;
                output.vertex = UnityObjectToClipPos(input.vertex);
                output.uv = input.uv;
                return output;
            }
            fixed4 frag(Output input) : SV_Target { return tex2D(_MainTex, input.uv); }
            ENDCG
        }
    }
}
