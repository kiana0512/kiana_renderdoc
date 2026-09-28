Shader "Kiana/CapturedAlbedo"
{
    Properties
    {
        _MainTex ("RDC Albedo", 2D) = "white" {}
        _Tint ("Tint", Color) = (1,1,1,1)
        _DecodeSRGB ("Decode captured sRGB albedo", Float) = 0
        _UseCapturedMipBias ("Use captured texture mip bias", Float) = 0
        _UseCapturedAuxMipBias ("Use captured normal/mask mip bias", Float) = 0
        _CapturedMipBias ("Captured body cb0[199].x", Float) = -2
        _UseCapturedWeaponPalette ("EID945 palette diagnostic (unvalidated)", Float) = 0
        _DecodeCapturedAux ("Decode Unity-imported EXR t5 RGB", Float) = 0
        _DecodeAuxNormal ("Decode Unity-imported EXR t4 RGB", Float) = 0
        _DecodeAuxControl ("Decode Unity-imported EXR t6 RGB", Float) = 0
        _DecodePaletteSRGB ("Decode Unity-imported t7 array RGB", Float) = 0
        _UseSourceLateDiffuse ("PS31475 post-matcap t5.g diffuse", Float) = 0
        _UseSourceMetal912 ("EID912 PS31475 separated diffuse/specular", Float) = 0
        _SourceMetalSpecScale ("EID912 source specular scale", Range(0,48)) = 27
        _SourceMetalLightFloor ("EID912 source light response floor", Range(0,1)) = 0.8
        _SourceMetalBlend ("EID912 verified source branch blend", Range(0,1)) = 0.3
        _UseSourceWeaponRegionShade ("PS31475 weapon t5.b region shade", Float) = 0
        _UseUmbrellaNormalShadow ("EID875 normal-driven canopy shade fit", Float) = 0
        _UseSourceUmbrellaTone ("EID875 PS31475 instructions 396-424", Float) = 0
        _UseSourceUmbrellaBands ("EID875 PS31475 canopy source bands", Float) = 0
        _UseSourceSkinExact ("EID945 PS31475 source skin bands", Float) = 0
        _SourceHairToneRGB ("Measured RDC hair midtone RGB", Color) = (1,1,1,1)
        _UseSourceGem ("PS42681 tangent-view cyan matcap", Float) = 0
        _DebugOutput ("0=color, 20=PS31475 source toon coordinate", Float) = 0
        _UseCapturedLight ("Apply captured light approximation", Float) = 0
        _UseArtToon ("Art-directed toon response", Float) = 0
        _ArtShadowColor ("Toon shadow color", Color) = (0.70,0.68,0.79,1)
        _ArtShadowThreshold ("Toon light threshold", Range(-1,1)) = 0.1
        _ArtShadowSoftness ("Toon terminator softness", Range(0.001,1)) = 0.2
        _ArtShadeStrength ("Toon shade blend", Range(0,1)) = 0.25
        _ArtAO ("Auxiliary occlusion strength", Range(0,1)) = 0
        _ArtSpecularColor ("Toon highlight color", Color) = (0.82,0.9,1,1)
        _ArtSpecularStrength ("Toon highlight strength", Range(0,2)) = 0.5
        _ArtSpecularPower ("Toon highlight sharpness", Range(2,128)) = 48
        _ArtRimColor ("View rim color", Color) = (0.50,0.62,1,1)
        _ArtRimStrength ("View rim strength", Range(0,2)) = 0.16
        _ArtRimPower ("View rim width", Range(1,16)) = 5
        _UseSourceHairRim ("PS31475 hair edge response", Float) = 0
        _SourceHairRimStrength ("PS31475 hair edge response strength", Range(0,1)) = 0.2
        _UseSourceHairMaskHighlight ("PS33678 front hair mask highlight", Float) = 0
        _UseSourceFrontHairArc ("PS33678 front hair curved specular", Float) = 0
        _SourceFrontHairArcStrength ("PS33678 front hair curved specular strength", Range(0,0.2)) = 0.13
        _UseSourceSkinLayer ("PS31475 source skin color layers", Float) = 0
        _SkinNormalSmoothing ("Skin ramp geometry normal blend", Range(0,1)) = 0
        _SkinNormalMipLevel ("Skin ramp normal mip level", Range(0,4)) = 0
        _UseSourceFaceNose ("PS31476 face alpha and lightmap nose", Float) = 0
        _UseCapturedFaceShadow ("EID1236 stencil-limited face shadow", Float) = 0
        _FaceShadowTex ("EID1236 RT0 darkening ratio", 2D) = "black" {}
        _FaceShadowVP0 ("Captured face shadow VP row 0", Vector) = (1,0,0,0)
        _FaceShadowVP1 ("Captured face shadow VP row 1", Vector) = (0,1,0,0)
        _FaceShadowVP3 ("Captured face shadow VP row 3", Vector) = (0,0,0,1)
        _UseSourceBackHairCrescent ("PS31475 back hair crescent candidate", Float) = 0
        _UseSourceBackHairTone ("EID895 captured back hair tone", Float) = 0
        _UseSourceHairAlpha ("PS33678 transparent hair alpha", Float) = 0
        _UseCapturedPointLight ("Diagnostic: RDC t1 point-light direction", Float) = 0
        _UseCapturedOverlay ("Diagnostic: RDC t2 CharacterOverlayTex", Float) = 0
        _CapturedOverlaySelect ("RDC cb3[106].x overlay color select", Float) = 0
        _RdcPixelShader ("Captured pixel shader resource ID", Float) = 31475
        _RdcFamilyEnabled ("Use source pixel shader family inputs", Float) = 0
        _FlipV ("Flip captured V", Float) = 1
        _UseBackfaceUV3 ("Use captured backface UV3 branch", Float) = 0
        _InvertFaceSign ("Invert front-face sign", Float) = 0
        _Cull ("Captured Cull", Float) = 0
        _SrcBlend ("Captured RGB source blend", Float) = 1
        _DstBlend ("Captured RGB destination blend", Float) = 0
        _SrcBlendAlpha ("Captured alpha source blend", Float) = 1
        _DstBlendAlpha ("Captured alpha destination blend", Float) = 0
        _ZWrite ("Captured Depth Write", Float) = 1
        _ZTest ("Captured Depth Test", Float) = 4
        _StencilRef ("Captured stencil reference", Float) = 0
        _StencilReadMask ("Captured stencil read mask", Float) = 0
        _StencilWriteMask ("Captured stencil write mask", Float) = 0
        _StencilCompFront ("Captured front stencil compare", Float) = 8
        _StencilCompBack ("Captured back stencil compare", Float) = 8
        _StencilPassFront ("Captured front stencil pass", Float) = 0
        _StencilPassBack ("Captured back stencil pass", Float) = 0
        _OutlineExtrusionPx ("Diagnostic outline screen displacement in pixels", Float) = 0
        _OutlineDepthOffset ("Diagnostic outline clip depth offset", Float) = 0
        _UseCapturedOutlineClip ("Captured-camera source outline VS clip", Float) = 0
        _EyeScreenOffsetPx ("Eye draw screen offset XY, captured camera only", Vector) = (0,0,0,0)
        _Slot0 ("RDC Slot 0", 2D) = "white" {}
        _Slot1 ("RDC Slot 1", 2D) = "white" {}
        _Slot2 ("RDC Slot 2", 2D) = "white" {}
        _Slot3 ("RDC Slot 3", 2D) = "white" {}
        _Slot4 ("RDC Slot 4", 2D) = "white" {}
        _Slot5 ("RDC Slot 5", 2D) = "white" {}
        _Slot6 ("RDC Slot 6", 2D) = "white" {}
        _Slot7 ("RDC Slot 7", 2D) = "white" {}
        _Slot8 ("RDC Slot 8", 2D) = "white" {}
        _Slot9 ("RDC Slot 9", 2D) = "white" {}
        _Slot7Array ("RDC Slot 7 full 16-slice array", 2DArray) = "" {}
        _Band0Tint ("RDC material band 0 tint", Vector) = (1,1,1,0)
        _Band1Tint ("RDC material band 1 tint", Vector) = (1,1,1,0)
        _Band2Tint ("RDC material band 2 tint", Vector) = (1,1,1,0)
        _Band3Tint ("RDC material band 3 tint", Vector) = (1,1,1,0)
        _Band4Tint ("RDC material band 4 tint", Vector) = (1,1,1,0)
        _Band0Control ("slice weight cap mode 0", Vector) = (100,1,1,0)
        _Band1Control ("slice weight cap mode 1", Vector) = (100,1,1,0)
        _Band2Control ("slice weight cap mode 2", Vector) = (100,1,1,0)
        _Band3Control ("slice weight cap mode 3", Vector) = (100,1,1,0)
        _Band4Control ("slice weight cap mode 4", Vector) = (100,1,1,0)
        _OutlineBand0 ("PS31478/31479 band 0", Vector) = (1,1,1,1)
        _OutlineBand1 ("PS31478/31479 band 1", Vector) = (1,1,1,1)
        _OutlineBand2 ("PS31478/31479 band 2", Vector) = (1,1,1,1)
        _OutlineBand3 ("PS31479 band 3", Vector) = (1,1,1,1)
        _OutlineBand4 ("PS31479 band 4", Vector) = (1,1,1,1)
        _FaceColor29 ("Face cb3[29] base", Vector) = (1,1,1,1)
        _FaceColor30 ("Face cb3[30] specular", Vector) = (1,1,1,1)
        _FaceColor31 ("Face cb3[31] shade A", Vector) = (1,1,1,1)
        _FaceColor32 ("Face cb3[32] shade B", Vector) = (1,1,1,1)
        _FaceColor33 ("Face cb3[33] shade C", Vector) = (1,1,1,1)
        _FaceColor34 ("Face cb3[34] shade D", Vector) = (1,1,1,1)
        _FaceColor35 ("Face cb3[35] shade E", Vector) = (1,1,1,1)
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" "Queue"="Geometry" }
        Cull [_Cull]
        Blend [_SrcBlend] [_DstBlend], [_SrcBlendAlpha] [_DstBlendAlpha]
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
            #pragma target 4.5
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"
            sampler2D _MainTex;
            sampler2D _Slot1;
            sampler2D _Slot2;
            sampler2D _Slot3;
            sampler2D _Slot4;
            sampler2D _Slot5;
            sampler2D _Slot6;
            sampler2D _Slot8;
            sampler2D _FaceShadowTex;
            UNITY_DECLARE_TEX2DARRAY(_Slot7Array);
            float4 _MainTex_ST;
            fixed4 _Tint;
            float _DecodeSRGB;
            float _UseCapturedMipBias;
            float _UseCapturedAuxMipBias;
            float _CapturedMipBias;
            float _UseCapturedWeaponPalette;
            float _DecodeCapturedAux;
            float _DecodeAuxNormal;
            float _DecodeAuxControl;
            float _DecodePaletteSRGB;
            float _UseSourceLateDiffuse;
            float _UseSourceMetal912;
            float _SourceMetalSpecScale;
            float _SourceMetalLightFloor;
            float _SourceMetalBlend;
            float _UseSourceWeaponRegionShade;
            float _UseUmbrellaNormalShadow;
            float _UseSourceUmbrellaTone;
            float _UseSourceUmbrellaBands;
            float _UseSourceSkinExact;
            float _UseSourceGem;
            float _DebugOutput;
            float _UseCapturedLight;
            float _UseArtToon;
            float4 _ArtShadowColor;
            float _ArtShadowThreshold, _ArtShadowSoftness, _ArtShadeStrength, _ArtAO;
            float4 _ArtSpecularColor;
            float _ArtSpecularStrength, _ArtSpecularPower;
            float4 _ArtRimColor;
            float _ArtRimStrength, _ArtRimPower;
            float _UseSourceHairRim, _SourceHairRimStrength, _UseSourceHairMaskHighlight;
            float _UseSourceFrontHairArc, _SourceFrontHairArcStrength;
            float4 _SourceHairToneRGB;
            float _UseSourceSkinLayer;
            float _SkinNormalSmoothing;
            float _SkinNormalMipLevel;
            float _UseSourceFaceNose;
            float _UseCapturedFaceShadow;
            float4 _FaceShadowVP0, _FaceShadowVP1, _FaceShadowVP3;
            float _UseSourceBackHairCrescent;
            float _UseSourceBackHairTone;
            float _UseSourceHairAlpha;
            float _UseCapturedPointLight;
            float _UseCapturedOverlay;
            float _CapturedOverlaySelect;
            float _RdcPixelShader;
            float _RdcFamilyEnabled;
            float4 _CapturedPointLightPosition;
            float _CapturedPointLightRadius;
            float4 _CapturedLightDirection;
            float _CapturedAmbient;
            float _CapturedDiffuse;
            float _FlipV;
            float _UseBackfaceUV3;
            float _InvertFaceSign;
            float _RdcDepthFlip;
            float _RdcFaceFlip;
            float _OutlineExtrusionPx;
            float _OutlineDepthOffset;
            float4 _EyeScreenOffsetPx;
            float _UseCapturedOutlineClip;
            float4 _Band0Tint, _Band1Tint, _Band2Tint, _Band3Tint, _Band4Tint;
            float4 _Band0Control, _Band1Control, _Band2Control, _Band3Control, _Band4Control;
            float4 _OutlineBand0, _OutlineBand1, _OutlineBand2, _OutlineBand3, _OutlineBand4;
            float4 _FaceColor29, _FaceColor30, _FaceColor31, _FaceColor32;
            float4 _FaceColor33, _FaceColor34, _FaceColor35;
            float3 DecodeSRGB(float3 color)
            {
                float3 low = color / 12.92;
                float3 high = pow((color + 0.055) / 1.055, 2.4);
                return lerp(low, high, step(0.04045, color));
            }
            float3 SourceSkinRamp(float nDotL)
            {
                // EID945 PS31475 source skin pixels and their t3 ratios:
                // nDotL -.78 -> (.67,.60,.68), -.37 -> (.71,.64,.71),
                // -.1 -> (.84,.78,.82), +.17 -> (.93,.87,.90),
                // +.31 -> (.97,.92,.94), +.44 -> (.98,1.01,1.00).
                // This samples the source multi-band response from PS
                // instructions 183-330; the exact piecewise shader algebra
                // remains to be transcribed.
                float3 result = float3(0.67, 0.60, 0.68);
                result = lerp(result, float3(0.71, 0.64, 0.71), smoothstep(-0.78, -0.37, nDotL));
                result = lerp(result, float3(0.84, 0.78, 0.82), smoothstep(-0.37, -0.10, nDotL));
                result = lerp(result, float3(0.93, 0.87, 0.90), smoothstep(-0.10, 0.17, nDotL));
                result = lerp(result, float3(0.97, 0.92, 0.94), smoothstep(0.17, 0.31, nDotL));
                return lerp(result, float3(0.98, 1.01, 1.00), smoothstep(0.31, 0.44, nDotL));
            }
            float3 SourceUmbrellaTone(float3 baseColor, float3 mappedNormal,
                                      float3 geometryNormal)
            {
                // PS31475 instructions 396-424, v7.z=0 and r9.y=1 in EID875.
                float3 lightDir = normalize(float3(-0.25845319, 0.96355820, 0.06897497));
                float mappedDot = dot(mappedNormal, lightDir);
                float geometryDot = dot(geometryNormal, lightDir);
                float brightness = dot(baseColor, float3(0.29, 0.60, 0.11));
                float gammaBase = 1.4375 + brightness * 0.2875;
                float shape = saturate(1.0 - 3.0 * (geometryDot - mappedDot));
                shape = min(2.0 * shape * sqrt(shape), 1.0);
                float sourceBlend = 0.5 * mappedDot + 0.5;
                float direct = saturate(mappedDot);
                float lightMix = 0.5 * (sourceBlend * shape - direct) + direct;
                float exponent = gammaBase + lightMix * (1.0 - gammaBase);
                float value = max(baseColor.r, max(baseColor.g, baseColor.b));
                float3 adjusted = value > 1.0 ? baseColor / value : baseColor;
                float3 powered = pow(max(adjusted, 0.00001), exponent);
                float3 halfTone = 0.5 * (powered + baseColor);
                return lerp(halfTone, powered, saturate(geometryDot));
            }
            float3 SourceBodyBandLight(float3 worldPosition,
                                       float toonCoordinate,
                                       float3 colorA, float3 colorB)
            {
                // EID875 PS31475 instructions 169-177, 192-329 for the
                // purple canopy's cb3[40]/[45] band. In this captured frame
                // r3.y=1, v7.x=1, cb2[40].y=1 and t1 slot strengths are 1.
                float spot = saturate(dot(worldPosition,
                    float3(0.190631, -0.333783, -0.319768)) - 113.58054);
                float3 initialLight = 1.0 + spot *
                    (float3(0.701960802, 0.779064238, 0.839215696) + 0.2 - 1.0);
                float distanceToPoint = length(float3(600.4092407,
                    2.06727004, 0.9980399) - worldPosition);
                float p = 0.05; // cb3[103/104] selected by source shadow band
                float x = (3.0 * toonCoordinate + 3.0) / (2.0 - 3.0 * p);
                float y = (3.0 * toonCoordinate - 1.5 * p + 1.0) /
                          (2.0 - 3.0 * p);
                float w = (3.0 * toonCoordinate - 4.5 * p - 1.0) /
                          (2.0 - 3.0 * p);
                float3 complementary = 1.0 - float3(x, y, w);
                float3 transition =
                    (toonCoordinate + float3(0.3333, -0.3333, -0.3333)) / p +
                    float3(0.5, 0.5, -0.5);
                float3 inverseTransition = 1.0 - transition;
                float3 mainWeights = saturate(float3(
                    complementary.x,
                    min(x, inverseTransition.x),
                    min(complementary.y, transition.x)));
                float upperEdge = saturate(min(y, inverseTransition.y));
                float middle = saturate(min(transition.y, inverseTransition.z));
                float upper = saturate(min(complementary.z, transition.z));
                float finalEdge = saturate(w);
                float colorWeight = saturate(distanceToPoint * 0.43725);
                float3 bandA = colorA + 0.000061;
                float3 bandB = colorB + 0.000061;
                float3 adjustedA = lerp(saturate(bandA /
                    max(dot(bandA, float3(0.33333, 0.33333, 0.33333)), 0.00001)), bandA, colorWeight);
                float3 adjustedB = lerp(saturate(bandB /
                    max(dot(bandB, float3(0.33333, 0.33333, 0.33333)), 0.00001)), bandB, colorWeight);
                float3 diffuse =
                    float3(1.0, 0.950000, 0.966000) * adjustedA * upperEdge +
                    float3(0.800000, 0.720000, 0.748387) * adjustedA * mainWeights.z +
                    float3(0.776000, 0.760000, 0.800000) * adjustedB * mainWeights.y +
                    float3(0.702529, 0.674118, 0.749020) * adjustedB * mainWeights.x;
                float3 bandLight = initialLight *
                    (upper * float3(1.0, 0.985000, 0.920000) +
                     middle * float3(1.0, 0.875000, 0.850000) + finalEdge);
                return bandLight + initialLight *
                    min(1.0, 1.0 / max(initialLight.r,
                    max(initialLight.g, initialLight.b))) * diffuse;
            }
            float4 SampleBodyAux(sampler2D source, float2 uv, float decodeFlag)
            {
                float4 sampled = _UseCapturedAuxMipBias > 0.5
                    ? tex2Dbias(source, float4(uv, 0, _CapturedMipBias))
                    : tex2D(source, uv);
                // Frame 38112 RID42888 EXR: Unity's gamma-space import
                // returns 0.718/0.635/0.561 where the RDC t5 sample is
                // 0.471/0.363/0.275. The inverse sRGB transfer restores
                // the source shader's material-band and normal inputs.
                if (decodeFlag > 0.5)
                    sampled.rgb = DecodeSRGB(sampled.rgb);
                return sampled;
            }
            struct appdata
            {
                float4 vertex : POSITION;
                float3 normal : NORMAL;
                float4 tangent : TANGENT;
                float2 uv : TEXCOORD0;
                float2 uv3 : TEXCOORD2;
                float4 outlineClip : TEXCOORD4;
                fixed4 color : COLOR;
            };
            struct v2f
            {
                float4 vertex : SV_POSITION;
                float2 uv : TEXCOORD0;
                float2 uv3 : TEXCOORD1;
                float3 worldNormal : TEXCOORD2;
                float3 worldPosition : TEXCOORD5;
                float3 worldTangent : TEXCOORD3;
                float3 worldBitangent : TEXCOORD4;
                fixed4 color : COLOR;
                float4 eyeLookup : TEXCOORD6;
                float outlineControl : TEXCOORD7;
            };
            v2f vert(appdata input)
            {
                v2f output;
                output.vertex = UnityObjectToClipPos(input.vertex);
                output.vertex.z = lerp(output.vertex.z, output.vertex.w - output.vertex.z, _RdcDepthFlip);
                if ((_RdcPixelShader == 31478 || _RdcPixelShader == 31479) && _OutlineDepthOffset != 0.0)
                    output.vertex.z += _OutlineDepthOffset * output.vertex.w;
                output.uv = TRANSFORM_TEX(float2(input.uv.x, lerp(input.uv.y, 1.0 - input.uv.y, _FlipV)), _MainTex);
                output.uv3 = float2(input.uv3.x, lerp(input.uv3.y, 1.0 - input.uv3.y, _FlipV));
                output.worldNormal = UnityObjectToWorldNormal(input.normal);
                output.worldPosition = mul(unity_ObjectToWorld, input.vertex).xyz;
                output.worldTangent = UnityObjectToWorldDir(input.tangent.xyz);
                // RDC PS31475 v4 is opposite Unity's default bitangent for
                // this captured mesh stream. Verified at EID945 skin pixels.
                output.worldBitangent = -cross(output.worldNormal, output.worldTangent) * input.tangent.w;
                output.color = input.color;
                output.eyeLookup = 1;
                output.outlineControl = 0;
                if (_RdcPixelShader == 31478 && _OutlineExtrusionPx > 0.0)
                {
                    // Source VS31467 expands the outline in projected camera
                    // space. This screen-pixel variant is a geometry/stencil
                    // diagnostic until its exact cb3[75/77/85] path is ported.
                    float3 viewNormal = mul((float3x3)UNITY_MATRIX_V, output.worldNormal);
                    float2 direction = viewNormal.xy / max(length(viewNormal.xy), 0.0001);
                    output.vertex.xy += direction * _OutlineExtrusionPx *
                        float2(2.0 / 2880.0, 2.0 / 1368.0) * output.vertex.w;
                }
                if (_RdcPixelShader == 31478 || _RdcPixelShader == 31479)
                {
                    // VS source v3.z is KMF COLOR.b. Recover the UNORM8 byte
                    // before applying source bit operations. The result was
                    // checked against 67,540 captured VSOut v5.w values.
                    float packedBlue = floor(input.color.b * 255.0 + 0.5);
                    if (_RdcPixelShader == 31478)
                        output.outlineControl = 0.9 - 0.2 * fmod(packedBlue, 4.0);
                    else
                        output.outlineControl = fmod(floor(packedBlue / 32.0), 2.0);
                }
                if (_RdcPixelShader == 31489)
                {
                    // Eye VS EID1273 instructions 79, 218-228: v3.x stores
                    // an 8-bit index. Its low/high nibbles select a texel in
                    // the bound 16x16 Eye_E texture (VS t1, RID23285).
                    float packed = floor(input.color.r * 255.0 + 0.5);
                    float x = packed - 16.0 * floor(packed / 16.0);
                    float y = 15.0 - floor(packed / 16.0);
                    float2 uvEye = float2((x + 0.5) / 16.0, 1.0 - (y + 0.5) / 16.0);
                    output.eyeLookup = tex2Dlod(_Slot1, float4(uvEye, 0, 0)) * float4(2, 2, 2, 1);
                }
                if ((_RdcPixelShader == 31478 || _RdcPixelShader == 31479) &&
                    _UseCapturedOutlineClip > 0.5 &&
                    _RdcDepthFlip > 0.5)
                {
                    // UV5 holds source SV_POSITION from RDC VSOut. This
                    // isolates PS/raster validation from the still incomplete
                    // outline VS offset while Scene view keeps native 3D.
                    // Unity's direct clip SV_POSITION uses the opposite Y
                    // sign from RenderDoc's D3D11 post-VS stream here.
                    output.vertex = float4(input.outlineClip.x, -input.outlineClip.y,
                        input.outlineClip.w - input.outlineClip.z + _OutlineDepthOffset * input.outlineClip.w,
                        input.outlineClip.w);
                }
                if (_RdcPixelShader == 31489 && _UseCapturedOutlineClip > 0.5 &&
                    _RdcDepthFlip > 0.5 && input.outlineClip.w > 0.0)
                    output.vertex.xy = float2(input.outlineClip.x, -input.outlineClip.y) *
                                       (output.vertex.w / input.outlineClip.w);
                if (_RdcPixelShader == 31489 && _RdcDepthFlip > 0.5)
                    output.vertex.xy += float2(_EyeScreenOffsetPx.x * 2.0 / 2880.0,
                                               -_EyeScreenOffsetPx.y * 2.0 / 1368.0) * output.vertex.w;
                return output;
            }
            float3 WeaponPalette(float3 baseColor, v2f input, float2 baseUV, float3 mappedNormal)
            {
                // PS 31475 EID 945, instructions 46-62 and 330-389. The
                // layer number, tint and blend mode come from cb3[band+10],
                // cb3[band+5] and cb3[band+15]; t6.g is the blend mask.
                float mask = saturate(SampleBodyAux(_Slot5, baseUV, _DecodeCapturedAux).r);
                int band = clamp(4 - (int)floor(mask * 5.0), 0, 4);
                float4 control = band == 0 ? _Band0Control : band == 1 ? _Band1Control :
                                 band == 2 ? _Band2Control : band == 3 ? _Band3Control : _Band4Control;
                if (control.x > 50.0) return baseColor;
                float4 auxiliary = saturate(SampleBodyAux(_Slot6, baseUV, _DecodeAuxControl));
                float3 tint = (band == 0 ? _Band0Tint : band == 1 ? _Band1Tint :
                               band == 2 ? _Band2Tint : band == 3 ? _Band3Tint : _Band4Tint).rgb;
                // PS 31475 instructions 344-358. For EID 945 all five
                // cb3[band+15].z values are zero, so the v0 UV addition at
                // instructions 350-353 is inactive. Time offset is also zero.
                float2 arrayUV = float2(dot(mappedNormal, float3(-0.9509623, 0.2933192, 0.0981571)),
                                        dot(mappedNormal, float3(0.1557515, 0.7282799, -0.6673454)))
                                 * 0.5 + 0.5;
                float4 layer = UNITY_SAMPLE_TEX2DARRAY(_Slot7Array, float3(arrayUV, control.x));
                if (_DecodePaletteSRGB > 0.5) layer.rgb = DecodeSRGB(layer.rgb);
                // PS31475 334-344, 359-375: t6.b is the source mask.
                // Low values are expanded by 5.1, then capped at one.
                // EID875 source .099 -> .505 before band strength .83.
                float maskStrength = _DecodeAuxControl > 0.5
                    ? (auxiliary.b <= 0.2 ? min(auxiliary.b * 5.1, 1.0) : auxiliary.b)
                    : auxiliary.g;
                float strength = saturate(maskStrength * layer.a * control.z);
                float3 layerColor = layer.rgb * tint;
                // cb3[band+15].y selects replace, additive or overlay.
                // The source applies this to the already lit r1 color at
                // instructions 359-387, not to the raw t3 albedo.
                if (control.w < 0.5)
                    return lerp(baseColor, layerColor * control.y, strength);
                if (control.w < 1.5)
                    return baseColor + strength * layerColor * control.y;
                float3 overlay = lerp(0.5,
                    saturate((layerColor - 0.5) * control.y + layerColor), strength);
                return lerp(2.0 * baseColor * overlay,
                            1.0 - 2.0 * (1.0 - baseColor) * (1.0 - overlay),
                            step(0.5, baseColor));
            }
            fixed4 frag(v2f input, fixed faceSign : VFACE) : SV_Target
            {
                // The captured projection reverses Unity's VFACE sign. Keep
                // Scene-view orbiting independent of the RDC camera.
                bool invertFace = (_InvertFaceSign > 0.5) != (_RdcFaceFlip > 0.5);
                bool backface = invertFace ? faceSign > 0 : faceSign < 0;
                float2 baseUV = (_UseBackfaceUV3 > 0.5 && backface) ? input.uv3 : input.uv;
                // Source PS families do not share slot semantics. In particular,
                // t4 is a face lightmap for PS31476/31480/31489 and a shadow
                // texture for PS31479; treating all t4 data as a normal map
                // corrupts face and outline shading.
                bool bodyFamily = _RdcPixelShader == 31475 || _RdcPixelShader == 42681 || _RdcPixelShader == 33678;
                bool faceFamily = _RdcPixelShader == 31476 || _RdcPixelShader == 31480 || _RdcPixelShader == 31489;
                bool outlineFamily = _RdcPixelShader == 31478 || _RdcPixelShader == 31479;
                if (_RdcFamilyEnabled > 0.5 && _RdcPixelShader == 24167)
                    return fixed4(input.color.rrr, 1);
                if (_RdcFamilyEnabled > 0.5 && _RdcPixelShader == 31482)
                    discard;
                if (_DebugOutput > 5.5 && _DebugOutput < 6.5)
                    return fixed4(normalize(input.worldBitangent) * 0.5 + 0.5, 1);
                if (_DebugOutput > 4.5 && _DebugOutput < 5.5)
                    return fixed4(normalize(input.worldTangent) * 0.5 + 0.5, 1);
                if (_DebugOutput > 3.5 && _DebugOutput < 4.5)
                    return fixed4(normalize(input.worldNormal) * 0.5 + 0.5, 1);
                if (_DebugOutput > 2.5 && _DebugOutput < 3.5) return fixed4(frac(baseUV), 0, 1);
                if (_DebugOutput > 1.5 && _DebugOutput < 2.5)
                    return fixed4(saturate(outlineFamily ? tex2D(_Slot3, baseUV).rgb : tex2D(_Slot5, baseUV).rgb), 1);
                if (_DebugOutput > 7.5 && _DebugOutput < 8.5)
                    return fixed4(SampleBodyAux(_Slot4, baseUV, _DecodeAuxNormal).rgb, 1);
                if (_DebugOutput > 8.5 && _DebugOutput < 9.5)
                    return fixed4(SampleBodyAux(_Slot5, baseUV, _DecodeCapturedAux).rgb, 1);
                if (_DebugOutput > 9.5 && _DebugOutput < 10.5)
                    return fixed4(SampleBodyAux(_Slot6, baseUV, _DecodeAuxControl).rgb, 1);
                float3 mappedNormal = normalize(input.worldNormal);
                if (bodyFamily && (_DebugOutput > 0.5 || _UseCapturedLight > 0.5))
                {
                    float3 normalSample = saturate(SampleBodyAux(_Slot4, baseUV, _DecodeAuxNormal).rgb);
                    float2 normalXY = normalSample.xy * 2.0 - 1.004;
                    float normalZ = sqrt(1.0 - min(dot(normalXY, normalXY), 1.0));
                    mappedNormal = normalize(normalXY.y * input.worldBitangent +
                        normalXY.x * input.worldTangent +
                        (backface ? -normalZ : normalZ) * input.worldNormal);
                }
                if (_DebugOutput > 0.5 && _DebugOutput < 1.5)
                    return fixed4(mappedNormal * 0.5 + 0.5, 1);
                if (bodyFamily && _DebugOutput > 19.5 && _DebugOutput < 20.5)
                {
                    // PS31475/PS33678 instructions 182-192. Frame 38112
                    // has v7.y=0, so the source toon coordinate is the
                    // world-normal directional dot plus twice decoded t4.z.
                    // Keep this diagnostic separate from the approximate
                    // color path until the cb0[3..14] band mix is ported.
                    float3 sourceLight = normalize(float3(-0.25845319,
                        0.96355820, 0.06897497));
                    float normalBlue = saturate(SampleBodyAux(_Slot4,
                        baseUV, _DecodeAuxNormal).b);
                    float toonCoordinate = dot(mappedNormal, sourceLight) +
                        2.0 * (normalBlue * 2.0 - 1.0);
                    return fixed4(toonCoordinate.xxx, 1);
                }
                if (_DebugOutput > 10.5 && _DebugOutput < 12.5)
                {
                    float bandMask = saturate(SampleBodyAux(_Slot5, baseUV, _DecodeCapturedAux).r);
                    int debugBand = clamp(4 - (int)floor(bandMask * 5.0), 0, 4);
                    float4 debugControl = debugBand == 0 ? _Band0Control : debugBand == 1 ? _Band1Control :
                                          debugBand == 2 ? _Band2Control : debugBand == 3 ? _Band3Control : _Band4Control;
                    float2 debugUV = float2(dot(mappedNormal, float3(-0.9509623, 0.2933192, 0.0981571)),
                                             dot(mappedNormal, float3(0.1557515, 0.7282799, -0.6673454)))
                                     * 0.5 + 0.5;
                    float4 debugLayer = UNITY_SAMPLE_TEX2DARRAY(_Slot7Array, float3(debugUV, debugControl.x));
                    return _DebugOutput < 11.5 ? fixed4(debugLayer.rgb, 1) :
                        fixed4(debugLayer.aaa, 1);
                }
                // Body PS31475 and hair variant PS33678 both use sample_b
                // for t3 with cb0[199].x. Per-draw opt-in preserves the
                // audited baseline for families without a validated mip path.
                float3 color = ((bodyFamily || faceFamily) && _UseCapturedMipBias > 0.5)
                    ? tex2Dbias(_MainTex, float4(baseUV, 0, _CapturedMipBias)).rgb
                    : tex2D(_MainTex, baseUV).rgb;
                if (_DecodeSRGB > 0.5) color = DecodeSRGB(color);
                color *= _Tint.rgb;
                if (_RdcPixelShader == 31476 && _DebugOutput > 15.5 && _DebugOutput < 16.5)
                {
                    float faceAlpha = _UseCapturedMipBias > 0.5 ?
                        tex2Dbias(_MainTex, float4(baseUV, 0, _CapturedMipBias)).a :
                        tex2D(_MainTex, baseUV).a;
                    float faceMap = tex2D(_Slot4, float2(input.uv3.x, input.uv.y)).r;
                    return fixed4(faceMap, faceAlpha, 0, 1);
                }
                if (_RdcPixelShader == 31476 && _DebugOutput > 16.5 && _DebugOutput < 17.5)
                {
                    float2 faceMapUV = float2(input.uv3.x, input.uv.y);
                    return fixed4(tex2D(_Slot4, faceMapUV).r,
                                  tex2D(_Slot4, float2(faceMapUV.x, 1.0 - faceMapUV.y)).r,
                                  0, 1);
                }
                if (_RdcPixelShader == 31476 && _DebugOutput > 17.5 && _DebugOutput < 19.5)
                {
                    float2 faceMapUV = float2(input.uv3.x, input.uv.y);
                    if (_DebugOutput > 18.5) faceMapUV.y = 1.0 - faceMapUV.y;
                    return fixed4(tex2D(_Slot4, faceMapUV).rgb, 1);
                }
                if (_DebugOutput > 12.5 && _DebugOutput < 13.5)
                    return fixed4(color, 1);
                if (_UseSourceGem > 0.5 && _RdcPixelShader == 42681)
                {
                    // EID968 PS42681 319-371: band 0 selects t7 slice 12.
                    // cb3[0]=(10.32,9.08,1,0); cb3[15].w=.33.
                    // The captured v2/v3/v4 basis is normal/tangent/bitangent.
                    // This UV shear follows the source view vector in that basis.
                    float3 sourceView = normalize(float3(600.4092407, 2.06727004, 0.9980399)
                                                  - input.worldPosition);
                    float3 n = normalize(input.worldNormal);
                    float3 t = normalize(input.worldTangent);
                    float3 b = normalize(input.worldBitangent);
                    float2 shear = float2(dot(sourceView, t), dot(sourceView, b));
                    shear /= max(length(sourceView), 0.0001);
                    float sourceMask = saturate(SampleBodyAux(_Slot6, baseUV, _DecodeAuxControl).r);
                    // PS42681 336 and 363 use dot(view, mapped normal)^2,
                    // not the albedo texture alpha.
                    float sourceAlpha = saturate(dot(sourceView, n));
                    // The array UV uses source v0, while imported 2D assets
                    // and Unity mesh UVs use the flipped V convention.
                    float2 sourceUV = float2(baseUV.x, 1.0 - baseUV.y);
                    float2 gemUV = sourceUV * float2(10.32, 9.08) + float2(1, 0) -
                                   0.33 * sourceMask * sourceAlpha * sourceAlpha * shear;
                    float3 gem = UNITY_SAMPLE_TEX2DARRAY(_Slot7Array, float3(gemUV, 12)).rgb;
                    float fresnel = pow(max(dot(sourceView, n), 0.01), 5.33);
                    if (_DebugOutput > 12.5 && _DebugOutput < 13.5)
                        return fixed4(frac(gemUV), 0, 1);
                    if (_DebugOutput > 13.5 && _DebugOutput < 14.5)
                        return fixed4(gem, 1);
                    if (_DebugOutput > 14.5 && _DebugOutput < 15.5)
                        return fixed4(sourceMask, sourceAlpha, fresnel, 1);
                    if (_DecodePaletteSRGB > 0.5) gem = DecodeSRGB(gem);
                    float3 gemColor = gem * 4.0 * float3(0, 0.491041124, 1) * 3.59 * fresnel;
                    float diffuseWeight = 0.96 * (1.0 - saturate(
                        SampleBodyAux(_Slot5, baseUV, _DecodeCapturedAux).g));
                    // PS42681 315-317 produces r10, then 531/543 combine
                    // r12=.96*(1-t5.g)*r1 with r10 and cb0[2]*r1.
                    // These two r10 endpoints come from traced EID968 pixels
                    // on opposite sides of the directional light band.
                    float lightDot = dot(n, normalize(float3(-0.25845319, 0.96355820, 0.06897497)));
                    float lightBand = smoothstep(0.24, 0.65, lightDot);
                    float3 sourceLight = lerp(float3(0.731, 0.711, 0.739),
                                              float3(0.967, 0.984, 0.965), lightBand);
                    return fixed4(gemColor *
                                  (float3(0.046724804, 0.070532210, 0.094339609) +
                                   diffuseWeight * sourceLight), 1);
                }
                float sourceHairAlpha = 1.0;
                if (_UseSourceHairAlpha > 0.5 && _RdcPixelShader == 33678)
                {
                    // EID1313 PS33678 instructions 49, 53 and 88-91 use the
                    // t6.wxyz view swizzle. At traced eye UV .4135,.7860,
                    // r0.y=.2218 matches exported RID42851 red byte 56;
                    // this channel lowers the hair alpha over the eyes.
                    // The source draw blends SrcAlpha/InvSrcAlpha on RT0.
                    float3 sourceView = normalize(float3(600.4092407, 2.06727004, 0.9980399)
                                                  - input.worldPosition);
                    float facing = saturate((dot(float3(0.66608936, 0.17003131, 0.72623307),
                                                   sourceView) - 0.3) * 1.428571);
                    float mask = saturate(SampleBodyAux(_Slot6, baseUV, _DecodeAuxControl).r);
                    sourceHairAlpha = saturate(1.0 - facing * (1.0 - mask));
                }
                if (_DebugOutput > 6.5 && _DebugOutput < 7.5)
                    return fixed4(sourceHairAlpha.xxx, 1);
                if (_RdcFamilyEnabled > 0.5 && faceFamily)
                {
                    // PS31476/31480 first sample face t4 at v0.zy, then
                    // sample a second channel at v0.xy. The captured
                    // v0.zw stream is restored in Mesh.uv3; z is not the V
                    // coordinate for the first lightmap read.
                    // This conservative response keeps the full texture range
                    // available while later CB/light equations are ported.
                    float3 faceControl = tex2D(_Slot4, float2(input.uv3.x, input.uv.y)).rgb;
                    color *= _FaceColor29.rgb;
                    color *= lerp(_FaceColor34.rgb, _FaceColor31.rgb, saturate(faceControl.r));
                    if (_RdcPixelShader == 31489)
                    {
                        // PS31489 writes premultiplied color at instr. 539.
                        float alpha = tex2D(_Slot3, baseUV).a * input.eyeLookup.a;
                        color *= input.eyeLookup.rgb;
                        return fixed4(color * alpha, alpha);
                    }
                }
                if (_UseSourceFaceNose > 0.5 && _RdcPixelShader == 31476)
                {
                    // EID992 PS31476: t4 first sample at v0.zy selects the
                    // nose/face shade; t3 alpha blends its warm shadow color
                    // at instructions 95-110. The recovered controls use the
                    // source face lightmap PNG and the uncompressed t3 atlas.
                    // The final RGB response remains a localized fit while
                    // the downstream source light chain is being ported.
                    float2 faceUV = float2(input.uv3.x, input.uv.y);
                    float faceMap = tex2D(_Slot4, faceUV).r;
                    float faceAlpha = _UseCapturedMipBias > 0.5 ?
                        tex2Dbias(_MainTex, float4(baseUV, 0, _CapturedMipBias)).a :
                        tex2D(_MainTex, baseUV).a;
                    float faceLit = smoothstep(0.18, 0.45, faceMap);
                    float3 directional = lerp(float3(0.785, 0.715, 0.760),
                                             float3(0.980, 1.030, 1.070), faceLit);
                    float alphaShade = smoothstep(0.50, 0.98, faceAlpha);
                    float3 detail = lerp(float3(0.68, 0.575, 0.57), 1.0, alphaShade);
                    color *= directional * detail;
                }
                if (_UseCapturedFaceShadow > 0.5 && _RdcPixelShader == 31476)
                {
                    // EID1236 draws the face again only where EID1202's
                    // stencil excludes it. Store that measured RT0 ratio
                    // in the captured camera projection and project it onto
                    // the face's world surface for both Game and Scene views.
                    float4 world = float4(input.worldPosition, 1.0);
                    float3 clip = float3(dot(_FaceShadowVP0, world),
                                         dot(_FaceShadowVP1, world),
                                         dot(_FaceShadowVP3, world));
                    float2 ndc = clip.xy / max(clip.z, 0.00001);
                    if (clip.z > 0.0 && all(abs(ndc) <= 1.0))
                    {
                        float4 shadow = tex2D(_FaceShadowTex, ndc * 0.5 + 0.5);
                        color *= lerp(float3(1,1,1), shadow.rgb, shadow.a);
                    }
                }
                if (_RdcFamilyEnabled > 0.5 && outlineFamily)
                {
                    // PS31478/31479 use t2 as visible color. The PS31478
                    // value and light response below follows instructions
                    // 112-163; PS31479 still needs its separate t3/t4 path.
                    float3 sourceColor = tex2D(_Slot2, input.uv).rgb;
                    float4 bandTint;
                    if (_RdcPixelShader == 31479)
                    {
                        float mask = tex2D(_Slot3, input.uv).r;
                        int band = clamp(4 - (int)floor(mask * 5.0), 0, 4);
                        bandTint = band == 0 ? _OutlineBand0 : band == 1 ? _OutlineBand1 :
                                   band == 2 ? _OutlineBand2 : band == 3 ? _OutlineBand3 : _OutlineBand4;
                    }
                    else
                    {
                        bandTint = input.outlineControl < 0.6 ? _OutlineBand2 :
                                   input.outlineControl < 0.8 ? _OutlineBand1 : _OutlineBand0;
                    }
                    float3 outline = sourceColor * bandTint.rgb;
                    if (_RdcPixelShader == 31478)
                    {
                        // Source cb3[29]=(1,1,1,1), cb0[2] is ambient,
                        // cb0[18] is diffuse, cb3[50] is the selected light
                        // direction for both EID1057 and EID1161. Their
                        // t0 is UnityRed, t1[0] light RGB is white, and
                        // VS extra-light count is zero in frame 38112.
                        float value = max(sourceColor.r, max(sourceColor.g, sourceColor.b));
                        float minimum = min(sourceColor.r, min(sourceColor.g, sourceColor.b));
                        float saturation = (value - minimum) / (value + 0.0001);
                        float adjustedValue = 0.6 + 0.2 * saturation - 0.2 * value;
                        float3 sourceLightDir = normalize(float3(-0.25845319, 0.96355820, 0.06897497));
                        float lambert = saturate((dot(normalize(input.worldNormal), sourceLightDir) - 0.28) * 10.000001);
                        float brightness = value * adjustedValue * (0.5 + 0.5 * lambert);
                        outline *= brightness / max(value, 0.0001);
                        outline *= float3(0.046724804, 0.070532210, 0.094339609) +
                                   float3(0.776000023, 0.759999990, 0.800000012);
                    }
                    return fixed4(outline, 1);
                }
                // PS 31475 instructions 68-71: v0.xy * cb3[106].y (40)
                // samples t2, adds its RGB and removes the neutral 0.5.
                // The later source conditional is still pending, so this
                // candidate remains disabled in the saved materials.
                if (_UseCapturedOverlay > 0.5 && _CapturedOverlaySelect > 0.5)
                    color = max(0, color + tex2D(_Slot2, input.uv * 40.0).rgb - 0.5);
                float3 lightVector = _CapturedPointLightPosition.xyz - input.worldPosition;
                float3 lightDirection = _UseCapturedPointLight > 0.5
                    ? normalize(lightVector) : normalize(_CapturedLightDirection.xyz);
                float ndotl = saturate(dot(mappedNormal, lightDirection));
                if (_UseArtToon > 0.5 && bodyFamily)
                {
                    float3 unlitAlbedo = color;
                    // Art-directed approximation of the captured anime
                    // response. Source PS31475 samples material t5/t6 at
                    // instructions 46-50, uses t6.b in shadow attenuation
                    // (53-161), t5.b/t5.a in specular control (435-528),
                    // and writes its lit color at 662. These are separate
                    // controls, never a uniform darkening of skin/albedo.
                    float4 materialMask = saturate(SampleBodyAux(_Slot5, baseUV, _DecodeCapturedAux));
                    float4 auxiliary = saturate(SampleBodyAux(_Slot6, baseUV, _DecodeAuxControl));
                    // In the captured Body_2_M texture the metallic brooch
                    // occupies the high-green band while its ribbon is
                    // magenta/low-green. This is an art-region selector,
                    // not a claim that G is a universal metalness channel.
                    float metalRegion = smoothstep(0.4, 0.7, materialMask.g);
                    float lightBand = smoothstep(_ArtShadowThreshold - _ArtShadowSoftness,
                        _ArtShadowThreshold + _ArtShadowSoftness, dot(mappedNormal, lightDirection));
                    float3 toonShade = lerp(_ArtShadowColor.rgb, 1.0, lightBand);
                    float3 shade = lerp(1.0, toonShade, _ArtShadeStrength);
                    float occlusion = lerp(1.0, auxiliary.b, _ArtAO);
                    float3 viewDir = normalize(_WorldSpaceCameraPos - input.worldPosition);
                    float3 halfDir = normalize(lightDirection + viewDir);
                    float gloss = lerp(0.45, 1.0, materialMask.a);
                    float spec = pow(saturate(dot(mappedNormal, halfDir)),
                        _ArtSpecularPower * gloss);
                    spec *= materialMask.b * metalRegion * _ArtSpecularStrength * lightBand;
                    float rim = pow(1.0 - saturate(dot(mappedNormal, viewDir)), _ArtRimPower);
                    rim *= metalRegion * _ArtRimStrength * (0.35 + 0.65 * lightBand);
                    // PS31475 583-593 uses two smooth edge thresholds,
                    // selected by the material/light branch. EID895 traces
                    // show an active scalar at one crescent pixel, but this
                    // generic approximation fails the draw ROI A/B and stays off.
                    float sourceEdge = 1.0 - saturate(dot(mappedNormal, viewDir));
                    float sourceRim = smoothstep(0.60, 0.90, sourceEdge);
                    sourceRim *= _UseSourceHairRim * _SourceHairRimStrength;
                    color = color * (_CapturedAmbient + _CapturedDiffuse * ndotl) * shade * occlusion +
                        _ArtSpecularColor.rgb * spec + _ArtRimColor.rgb * rim +
                        float3(1.0, 0.92, 0.90) * sourceRim;
                    if (_UseSourceMetal912 > 0.5 && _RdcPixelShader == 31475)
                    {
                        // PS31475 431-434 separates the metal path before
                        // lighting: r12=.96*(1-t5.g)*base and
                        // r13=lerp(.04,base,t5.g). Instructions 529-532 then
                        // add the specular path to lit r12. Keeping those two
                        // terms separate avoids attenuating an already-added
                        // highlight (the failed late-diffuse experiment).
                        float diffuseWeight912 = 0.96 * (1.0 - materialMask.g);
                        float3 sourceDiffuse912 = unlitAlbedo * diffuseWeight912;
                        float3 sourceF0912 = lerp(0.04.xxx, unlitAlbedo, materialMask.g);
                        float sourceLight912 = lerp(_SourceMetalLightFloor, 0.98, lightBand);
                        // The constant is the measured cb0[2] contribution at
                        // representative EID912 pixels after the r12/r13 join.
                        float3 sourceAmbient912 = float3(0.03, 0.055, 0.095);
                        float3 sourceMetal912 = sourceDiffuse912 * sourceLight912 +
                            sourceAmbient912 + sourceF0912 * spec * _SourceMetalSpecScale;
                        color = lerp(color, sourceMetal912, metalRegion * _SourceMetalBlend);
                    }
                    if (_UseSourceSkinLayer > 0.5 && _RdcPixelShader == 31475)
                    {
                        // t5 red=1 selects the skin band in EID945; the
                        // warm t3 channel ordering excludes white fabric.
                        float skinBand = smoothstep(0.94, 0.98, materialMask.r) *
                            smoothstep(0.03, 0.08, unlitAlbedo.r - unlitAlbedo.g) *
                            smoothstep(0.00, 0.03, unlitAlbedo.g - unlitAlbedo.b);
                        float3 sourceLight = normalize(float3(-0.25845319, 0.96355820, 0.06897497));
                        float3 skinRampNormal = mappedNormal;
                        if (_SkinNormalMipLevel > 0.01)
                        {
                            float3 skinNormalSample = saturate(tex2Dlod(_Slot4,
                                float4(baseUV, 0, _SkinNormalMipLevel)).rgb);
                            if (_DecodeAuxNormal > 0.5)
                                skinNormalSample = DecodeSRGB(skinNormalSample);
                            float2 skinXY = skinNormalSample.xy * 2.0 - 1.004;
                            float skinZ = sqrt(1.0 - min(dot(skinXY, skinXY), 1.0));
                            skinRampNormal = normalize(skinXY.y * input.worldBitangent +
                                skinXY.x * input.worldTangent +
                                (backface ? -skinZ : skinZ) * input.worldNormal);
                        }
                        float3 skinNormal = normalize(lerp(skinRampNormal,
                            normalize(input.worldNormal), _SkinNormalSmoothing));
                        float3 skinColor = unlitAlbedo * SourceSkinRamp(dot(skinNormal, sourceLight));
                        color = lerp(color, skinColor, skinBand);
                    }
                    if (_RdcPixelShader == 33678 && _UseSourceHairMaskHighlight > 0.5 &&
                        _UseSourceLateDiffuse < 0.5)
                    {
                        // In traced EID1035 crescent pixels, t5.b is 0.577/0.961
                        // after the source t5.zxwy resource swizzle,
                        // t3 already carries the crescent shape, and the source
                        // edge-light term is zero. Restore the t3 contribution
                        // only in this mask band; the rest keeps its dark layer.
                        float hairNormalY = saturate(SampleBodyAux(_Slot4, baseUV, _DecodeAuxNormal).g);
                        float hairBand = smoothstep(0.40, 0.55, materialMask.b) *
                            smoothstep(0.54, 0.62, hairNormalY);
                        color = lerp(color, unlitAlbedo * float3(1.01, 1.05, 1.07), hairBand);
                    }
                    if (_RdcPixelShader == 31475 && _UseSourceBackHairCrescent > 0.5 &&
                        _UseSourceLateDiffuse < 0.5)
                    {
                        // EID895 crescent trace: t5.b=0.232, t3=(.625,.609,.855),
                        // o0=(.661,.667,.983). Nearby unlit band t5.b=0.
                        float crescent = smoothstep(0.06, 0.20, materialMask.b);
                        color = lerp(color, unlitAlbedo * float3(1.06, 1.10, 1.15), crescent);
                    }
                    if (_UseCapturedWeaponPalette > 0.5)
                        color = WeaponPalette(color, input, baseUV, mappedNormal);
                    if (_UseSourceUmbrellaTone > 0.5 && _RdcPixelShader == 31475 &&
                        unlitAlbedo.r > unlitAlbedo.g * 1.15 &&
                        unlitAlbedo.b > unlitAlbedo.g * 1.35)
                        color = SourceUmbrellaTone(unlitAlbedo, mappedNormal,
                            normalize(input.worldNormal));
                    if (_DebugOutput > 20.5 && _DebugOutput < 21.5 &&
                        _RdcPixelShader == 31475)
                        return fixed4(color, 1);
                    if (_UseSourceLateDiffuse > 0.5 &&
                        (_RdcPixelShader == 31475 || _RdcPixelShader == 33678))
                    {
                        // Source PS31475 431-432 / PS33678 435-436:
                        // r12 = .96*(1-t5.g)*r1.
                        // At 529-545 this is multiplied by the captured
                        // directional light and ambient cb0[2] is added.
                        float sourceGreen = saturate(SampleBodyAux(
                            _Slot5, baseUV, _DecodeCapturedAux).g);
                        float diffuseWeight = 0.96 * (1.0 - sourceGreen);
                        color *= float3(0.046724804, 0.070532210, 0.094339609) +
                                 diffuseWeight * float3(0.928, 0.978, 0.990);
                    }
                    // Capture-matched midtone calibration is applied before
                    // t5 crescent/arc restoration so the bright mask remains
                    // controlled by source textures, not a global dimmer.
                    if (_UseSourceBackHairTone > 0.5)
                        color *= _SourceHairToneRGB.rgb;
                    if (_RdcPixelShader == 31475 && _UseSourceBackHairCrescent > 0.5 &&
                        _UseSourceLateDiffuse > 0.5)
                    {
                        float crescent = smoothstep(0.06, 0.20, materialMask.b);
                        color = lerp(color, unlitAlbedo * float3(1.06, 1.10, 1.15), crescent);
                    }
                    if (_RdcPixelShader == 33678 && _UseSourceHairMaskHighlight > 0.5 &&
                        _UseSourceLateDiffuse > 0.5)
                    {
                        float hairNormalY = saturate(SampleBodyAux(_Slot4, baseUV, _DecodeAuxNormal).g);
                        float hairBand = smoothstep(0.40, 0.55, materialMask.b) *
                            smoothstep(0.54, 0.62, hairNormalY);
                        color = lerp(color, unlitAlbedo * float3(1.01, 1.05, 1.07), hairBand);
                    }
                    if (_RdcPixelShader == 33678 && _UseSourceFrontHairArc > 0.5)
                    {
                        // EID1035 PS33678 46-47 reads the blue channel of t5
                        // into r3.x. Instructions 477-485 turn its curved mask
                        // into a specular term; 532-549 add it to RT0. At
                        // (978,1050)/(1085,1064), t3 is nearly uniform gray
                        // but r3.x changes 0 -> 1 across the arc. The t4 G
                        // gate approximates the missing source half-vector
                        // response and rejects shadowed hair such as
                        // (881,1066). No screen-space crescent is painted.
                        float hairNormalY = saturate(SampleBodyAux(_Slot4, baseUV, _DecodeAuxNormal).g);
                        float arcMask = smoothstep(0.12, 0.30, materialMask.b) *
                                        smoothstep(0.45, 0.475, hairNormalY);
                        float saturation = max(unlitAlbedo.r, max(unlitAlbedo.g, unlitAlbedo.b)) -
                                           min(unlitAlbedo.r, min(unlitAlbedo.g, unlitAlbedo.b));
                        float colored = smoothstep(0.10, 0.24, saturation) *
                                        (1.0 - smoothstep(0.50, 0.56, hairNormalY));
                        float gray = 1.0 - smoothstep(0.10, 0.24, saturation);
                        // The source arc pixels already matched within a few
                        // bytes. Restrict tone calibration to the surrounding
                        // midtones; preserve the texture-gated crescent.
                        color *= lerp(_SourceHairToneRGB.rgb, float3(1,1,1), arcMask);
                        color += arcMask * _SourceFrontHairArcStrength *
                                 (gray * float3(1.05, 0.87, 0.80) +
                                  colored * float3(0.25, 0.50, 0.60));
                    }
                    if (_UseSourceWeaponRegionShade > 0.5)
                    {
                        // EID858: t5.b marks the pale/cyan shaft near 1,
                        // while the flower and blue ribbon occupy lower bands.
                        // Preserve shaft color while applying the recovered
                        // toon response to the latter material regions.
                        float region = 1.0 - smoothstep(0.85, 0.98, materialMask.b);
                        float3 baselineLit = unlitAlbedo *
                            (_CapturedAmbient + _CapturedDiffuse * ndotl);
                        color = lerp(baselineLit, color, region);
                    }
                    if (_UseUmbrellaNormalShadow > 0.5 &&
                        unlitAlbedo.r > unlitAlbedo.g * 1.15 &&
                        unlitAlbedo.b > unlitAlbedo.g * 1.35)
                    {
                        // EID875 canopy: t5/t6 are nearly constant across the
                        // purple panels, while the source shade follows t4
                        // normal variation. Fitted against RT0 EID875 only.
                        float3 n = mappedNormal;
                        float3 shade = float3(1.276, 1.156, 1.181)
                            + n.x * float3(-0.282, -0.316, -0.124)
                            + n.y * float3(-0.027, 0.053, -0.100)
                            + n.z * float3(-0.261, -0.240, -0.190)
                            + n.x * n.x * float3(-0.076, -0.052, -0.020)
                            + n.y * n.y * float3(-0.297, -0.257, -0.105)
                            + n.x * n.y * float3(0.464, 0.459, 0.195);
                        color *= clamp(shade, 0.5, 1.5);
                    }
                    if (_UseSourceUmbrellaBands > 0.5 &&
                        _RdcPixelShader == 31475 &&
                        unlitAlbedo.r > unlitAlbedo.g * 1.15 &&
                        unlitAlbedo.b > unlitAlbedo.g * 1.35)
                    {
                        float3 sourceLight = normalize(float3(-0.25845319,
                            0.96355820, 0.06897497));
                        float normalBlue = saturate(SampleBodyAux(_Slot4,
                            baseUV, _DecodeAuxNormal).b);
                        float toonCoordinate = dot(mappedNormal, sourceLight) +
                            2.0 * (normalBlue * 2.0 - 1.0);
                        float3 bandLight = SourceBodyBandLight(input.worldPosition,
                            toonCoordinate,
                            float3(0.669870, 0.655030, 0.787410),
                            float3(0.552550, 0.480550, 0.603830));
                        if (_DebugOutput > 21.5 && _DebugOutput < 22.5)
                            return fixed4(bandLight, 1);
                        float3 sourceTone = SourceUmbrellaTone(unlitAlbedo,
                            mappedNormal, normalize(input.worldNormal));
                        color = sourceTone *
                            (float3(0.046724804, 0.070532210, 0.094339609) +
                             0.96 * bandLight);
                    }
                    if (_UseSourceSkinExact > 0.5 && _RdcPixelShader == 31475)
                    {
                        // PS31475 EID945 t5.x=1 selects cb3[39] and cb3[44].
                        // The source color transform at 394 is inactive for
                        // this material, so RT0 is t3*(cb0[2]+.96*r11).
                        float skin = smoothstep(0.94, 0.98, materialMask.r) *
                            smoothstep(0.03, 0.08,
                                unlitAlbedo.r - unlitAlbedo.g) *
                            smoothstep(0.00, 0.03,
                                unlitAlbedo.g - unlitAlbedo.b);
                        float3 sourceLight = normalize(float3(-0.25845319,
                            0.96355820, 0.06897497));
                        float normalBlue = saturate(SampleBodyAux(_Slot4,
                            baseUV, _DecodeAuxNormal).b);
                        float toonCoordinate = dot(mappedNormal, sourceLight) +
                            2.0 * (normalBlue * 2.0 - 1.0);
                        float3 bandLight = SourceBodyBandLight(input.worldPosition,
                            toonCoordinate,
                            float3(1.0, 0.9131, 0.8879),
                            float3(0.8796, 0.6939, 0.6939));
                        if (_DebugOutput > 22.5 && _DebugOutput < 23.5)
                            return fixed4(bandLight, 1);
                        float3 exactColor = unlitAlbedo *
                            (float3(0.046724804, 0.070532210, 0.094339609) +
                             0.96 * bandLight);
                        color = lerp(color, exactColor, skin);
                    }
                    return fixed4(color, sourceHairAlpha);
                }
                if (_UseCapturedLight > 0.5)
                {
                    // t1[0] contains a 50-unit radius. Keep its attenuation
                    // separate from the prior fitted ambient/diffuse terms.
                    float attenuation = _UseCapturedPointLight > 0.5
                        ? saturate(1.0 - dot(lightVector, lightVector) /
                          max(_CapturedPointLightRadius * _CapturedPointLightRadius, 0.001))
                        : 1.0;
                    color *= _CapturedAmbient + _CapturedDiffuse * ndotl * attenuation;
                }
                if (_UseCapturedWeaponPalette > 0.5)
                    color = WeaponPalette(color, input, baseUV, mappedNormal);
                return fixed4(color, sourceHairAlpha);
            }
            ENDCG
        }
    }
}
