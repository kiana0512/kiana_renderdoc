Shader "Kiana/NativeFinalStage"
{
    Properties
    {
        _BackgroundTex ("RDC background stage reference", 2D) = "black" {}
        _CharacterTex ("Native 3D render", 2D) = "black" {}
        _CharacterExtent ("Captured output X extent", Vector) = (0, 1, 0, 0)
        _ShowBackground ("Show background", Float) = 1
        _EnableColorGrade ("Enable character color grade", Float) = 1
        _ToneGain ("Character gain", Vector) = (1,1,1,0)
        _ToneLift ("Character lift", Vector) = (0,0,0,0)
        _BloomIntensity ("Character bloom intensity", Float) = 0
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
            sampler2D _BackgroundTex;
            sampler2D _CharacterTex;
            float4 _CharacterExtent;
            float _ShowBackground;
            float _EnableColorGrade;
            float3 _ToneGain;
            float3 _ToneLift;
            float _BloomIntensity;
            fixed4 frag(v2f_img i) : SV_Target
            {
                float2 uv = i.uv;
                fixed4 background = tex2D(_BackgroundTex, uv) * _ShowBackground;
                float x = (uv.x - _CharacterExtent.x) /
                    (_CharacterExtent.y - _CharacterExtent.x);
                float inside = step(0.0, x) * step(x, 1.0);
                fixed4 character = tex2D(_CharacterTex, float2(x, 1.0 - uv.y));
                float a = character.a * inside;
                float3 graded = lerp(character.rgb,
                    saturate(character.rgb * _ToneGain + _ToneLift), _EnableColorGrade);
                float3 bloom = 0;
                if (_BloomIntensity > 0)
                {
                    float2 p = float2(x, 1.0 - uv.y);
                    float2 dx = float2(12.0 / 2880.0, 0);
                    float2 dy = float2(0, 12.0 / 1368.0);
                    bloom += tex2D(_CharacterTex, p + dx).rgb;
                    bloom += tex2D(_CharacterTex, p - dx).rgb;
                    bloom += tex2D(_CharacterTex, p + dy).rgb;
                    bloom += tex2D(_CharacterTex, p - dy).rgb;
                    bloom *= _BloomIntensity * 0.25;
                }
                return fixed4(graded * a + bloom * inside +
                    background.rgb * (1.0 - a), 1.0);
            }
            ENDCG
        }
    }
}
