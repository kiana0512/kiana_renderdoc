Shader "Kiana/CapturedFinalComposite"
{
    Properties { _MainTex ("Captured stage input", 2D) = "white" {} }
    SubShader
    {
        Tags { "RenderType"="Transparent" "Queue"="Transparent" }
        Cull Off ZWrite Off ZTest Always
        Blend One OneMinusSrcAlpha
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"
            sampler2D _MainTex;
            struct Input { float4 vertex : POSITION; float2 uv : TEXCOORD0; float4 color : COLOR; };
            struct Output { float4 vertex : SV_POSITION; float2 uv : TEXCOORD0; float4 color : COLOR; };
            Output vert(Input input)
            {
                Output output;
                output.vertex = UnityObjectToClipPos(input.vertex);
                output.uv = input.uv;
                output.color = input.color;
                return output;
            }
            fixed4 frag(Output input) : SV_Target
            {
                fixed4 sampleColor = tex2D(_MainTex, input.uv);
                // EID2475 / PS31769: (t0 + cb0[10]) * vertexColor; cb0[10] is zero.
                sampleColor *= input.color;
                sampleColor.rgb *= input.color.a;
                return sampleColor;
            }
            ENDCG
        }
    }
}
