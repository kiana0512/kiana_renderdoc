using System;
using System.Collections.Generic;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace KianaFrameReconstruction
{
    // Keep the source PS identity on each existing material. This operation
    // updates materials in place, preserving scene references and GUIDs.
    public static class ApplyCapturedMaterialFamilies
    {
        const string Root = "Assets/Kiana";

        [Serializable] class Manifest { public Entry[] events; }
        [Serializable] class Entry
        {
            public int eventId;
            public int fragmentShader;
            public int albedoResourceId;
        }
        [Serializable] class TableManifest { public TableDraw[] draws; }
        [Serializable] class TableDraw { public int eid; public MaterialBand[] bands; }
        [Serializable] class MaterialBand
        {
            public int band;
            public float[] tint;
            public float arraySlice;
            public float weight;
            public float strengthCap;
            public float mode;
        }
        [Serializable] class OutlineManifest { public OutlineDraw[] draws; }
        [Serializable] class OutlineDraw { public int eid; public OutlineBand[] bands; }
        [Serializable] class OutlineBand { public int band; public float[] color; }
        [Serializable] class FaceManifest { public FaceDraw[] draws; }
        [Serializable] class FaceDraw { public int eid; public FaceRow[] colorRows; }
        [Serializable] class FaceRow { public int register; public float[] value; }

        [MenuItem("Kiana/Apply Captured Material Families")]
        public static string Apply()
        {
            ConfigureEyeLookupImporter();
            ConfigureBodyAlbedoImporter();
            ConfigureFaceTextureImporters();
            var source = AssetDatabase.LoadAssetAtPath<TextAsset>(Root + "/Manifest/gbuffer5-bindings.json");
            if (source == null) throw new Exception("Missing gbuffer5-bindings.json");
            var manifest = JsonUtility.FromJson<Manifest>(source.text);
            if (manifest.events == null || manifest.events.Length != 26)
                throw new Exception("Expected 26 G-buffer draw bindings");
            var allowed = new HashSet<int> { 31475, 42681, 31476, 33678, 31478,
                31479, 24167, 31480, 31489, 31482 };
            int changed = 0;
            foreach (var draw in manifest.events)
            {
                if (!allowed.Contains(draw.fragmentShader))
                    throw new Exception("Unrecognized PS " + draw.fragmentShader + " EID " + draw.eventId);
                var path = $"{Root}/Materials/EID{draw.eventId}_GBuffer3D.mat";
                var material = AssetDatabase.LoadAssetAtPath<Material>(path);
                if (material == null) throw new Exception("Missing material " + path);
                if (material.shader == null || material.shader.name != "Kiana/CapturedAlbedo")
                    throw new Exception("Unexpected material shader " + path);
                if (!material.HasProperty("_RdcPixelShader") || !material.HasProperty("_RdcFamilyEnabled"))
                    throw new Exception("Import updated CapturedAlbedo.shader before applying families");
                material.SetFloat("_RdcPixelShader", draw.fragmentShader);
                // Body and PS31489 eye paths passed same-state stage gates.
                // Face and outline paths remain source-guided candidates.
                bool bodyPath = draw.fragmentShader == 31475 || draw.fragmentShader == 42681 ||
                                draw.fragmentShader == 33678;
                bool eyePath = draw.fragmentShader == 31489;
                material.SetFloat("_RdcFamilyEnabled", bodyPath || eyePath ? 1f : 0f);
                if (draw.eventId == 992)
                {
                    // PS31476 t3 alpha and the first t4 face-lightmap read
                    // create the nose shade. The original EXR binding did
                    // not reproduce source t4 samples; RID25406 PNG does.
                    material.SetTexture("_Slot4", AssetDatabase.LoadAssetAtPath<Texture2D>(
                        Root + "/Textures/RID25406.png"));
                    material.SetFloat("_UseCapturedMipBias", 1f);
                    material.SetFloat("_CapturedMipBias", -2f);
                    material.SetFloat("_UseSourceFaceNose", 1f);
                }
                if (bodyPath)
                {
                    // All nine body-family draws in frame 38112 have
                    // cb3[106].x=0. Their t2 overlay sample executes, but
                    // the following movc discards it from the color path.
                    material.SetFloat("_CapturedOverlaySelect", 0f);
                    // Same-state draw ROI gates: -2 sample bias improves
                    // 858, 875, 912 and 945. EID895 slightly regressed.
                    bool validatedMipBias = draw.eventId == 858 || draw.eventId == 875 ||
                                            draw.eventId == 912 || draw.eventId == 945;
                    material.SetFloat("_UseCapturedMipBias", validatedMipBias ? 1f : 0f);
                    material.SetFloat("_CapturedMipBias", -2f);
                    // EID945 art gate: this modest toon shade improves the
                    // captured RT0 stage while preserving skin color. The
                    // material's AO/specular/rim controls remain zero until
                    // each one has a source-guided material-region check.
                    if (draw.eventId == 858)
                    {
                        // t5.b separates the pale/cyan shaft from its flower
                        // and ribbon. Preserve the existing shaft lighting;
                        // toon + PS31475 late diffuse belongs to the lower
                        // t5.b regions. RDC draw MAE 24.258 -> 16.654.
                        material.SetFloat("_UseArtToon", 1f);
                        material.SetFloat("_ArtShadeStrength", 0.25f);
                        material.SetFloat("_UseSourceLateDiffuse", 1f);
                        material.SetFloat("_UseSourceWeaponRegionShade", 1f);
                    }
                    if (draw.eventId == 945)
                    {
                        // PS31475 t3 uses sample_b with cb0[199].x=-2.
                        // A same-state EID945 gate improved IoU and MAE.
                        material.SetFloat("_UseArtToon", 1f);
                        material.SetFloat("_ArtShadeStrength", 0.5f);
                        material.SetFloat("_ArtAO", 0f);
                        material.SetFloat("_ArtSpecularStrength", 0f);
                        material.SetFloat("_ArtRimStrength", 0f);
                    }
                    if (draw.eventId == 912)
                    {
                        // Body_2_M high-G brooch region: metal-gated
                        // highlight improved this draw's source ROI MAE.
                        // The same-stage source mask has +14.4/255 Unity
                        // luminance before the toon boundary calibration;
                        // shade 1 / threshold .8 lowers EID912 RGB MAE
                        // 25.2 -> 19.8 while retaining sharp white glints.
                        material.SetFloat("_UseArtToon", 1f);
                        material.SetFloat("_ArtShadeStrength", 1f);
                        material.SetFloat("_ArtShadowThreshold", 0.8f);
                        material.SetFloat("_ArtAO", 0f);
                        material.SetFloat("_ArtSpecularStrength", 1f);
                        material.SetFloat("_ArtRimStrength", 0f);
                        material.SetFloat("_UseSourceMetal912", 1f);
                        material.SetFloat("_SourceMetalSpecScale", 27f);
                        material.SetFloat("_SourceMetalLightFloor", 0.8f);
                        material.SetFloat("_SourceMetalBlend", 0.3f);
                    }
                    if (draw.eventId == 875 || draw.eventId == 895)
                    {
                        // Umbrella and rear-hair regions each improved by
                        // several RGB MAE points with a full toon light band.
                        material.SetFloat("_UseArtToon", 1f);
                        material.SetFloat("_ArtShadeStrength", 1f);
                        material.SetFloat("_ArtAO", 0f);
                        material.SetFloat("_ArtSpecularStrength", 0f);
                        material.SetFloat("_ArtRimStrength", 0f);
                    }
                    if (draw.eventId == 875)
                    {
                        // Same-camera source changed-region A/B: 0.1 -> 0.6
                        // reduces EID875 RT0 MAE 18.072 -> 12.665. This is
                        // a fitted toon terminator, pending the full PS path.
                        material.SetFloat("_ArtShadowThreshold", 0.6f);
                        // EID875 t5/t7 source samples are linear. Their
                        // Unity-imported values follow the sRGB curve, e.g.
                        // t5.r .718 vs RDC .471 and t7 slice 4 .482 vs .198.
                        // Decode these two inputs only: same-draw RT0 MAE
                        // drops 12.665 -> 9.923 on 629,460 changed pixels.
                        material.SetFloat("_DecodeCapturedAux", 1f);
                        material.SetFloat("_DecodePaletteSRGB", 1f);
                        material.SetFloat("_DecodeAuxNormal", 0f);
                        material.SetFloat("_DecodeAuxControl", 0f);
                        // PS31475 431-432 and 529-545 apply a second,
                        // t5.g-driven diffuse response after t7. Same-draw
                        // source mask MAE 9.923 -> 8.392 in EID875.
                        material.SetFloat("_UseSourceLateDiffuse", 1f);
                          // PS31475 instructions 182-329 and 396-424 now
                          // reproduce the captured canopy light bands and
                          // prelight tone. The previous polynomial fit stays
                          // available only as a disabled diagnostic.
                          material.SetFloat("_UseUmbrellaNormalShadow", 0f);
                          material.SetFloat("_UseSourceUmbrellaTone", 1f);
                          material.SetFloat("_UseSourceUmbrellaBands", 1f);
                    }
                    if (draw.eventId == 895)
                    {
                        // RDC PS31475 t5.b identifies the outer back-hair
                        // crescent. Traced bright pixels and same-draw ROI
                        // both improve with the opt-in color contribution.
                        material.SetFloat("_UseSourceBackHairCrescent", 0f);
                        material.SetFloat("_UseSourceBackHairTone", 1f);
                        // PS31475 late t5.g diffuse also improves the full
                        // EID895 hair draw 16.471 -> 14.027 RGB MAE. Reapply
                        // the traced crescent after this diffuse term so its
                        // bright source pixel remains (167,169,250).
                        material.SetFloat("_UseSourceLateDiffuse", 1f);
                        // Same-stage RDC RT0: the hair draw was +13.2/255
                        // in mean luminance. Channel-wise calibration lowers
                        // changed-region MAE 14.1 -> 10.0 while the t5
                        // crescent remains at its source-matched value.
                        material.SetColor("_SourceHairToneRGB",
                            new Color(0.90f, 0.83f, 0.95f, 1f));
                    }
                    if (draw.eventId == 968)
                    {
                        // PS42681 EID968 uses t7 slice 12 with tangent-view UV
                        // shear and cyan cb3 tint. Source draw delta ROI MAE
                        // falls 104.209 -> 26.171 on 1,975 changed pixels.
                        material.SetFloat("_UseSourceGem", 1f);
                        material.SetFloat("_DecodeCapturedAux", 1f);
                        material.SetFloat("_DecodeAuxControl", 1f);
                        material.SetFloat("_DecodePaletteSRGB", 1f);
                    }
                    if (draw.eventId == 945)
                    {
                        // PS31475 EID945 skin band: source normal/light dot
                        // selects the dark core, pink transition and lit
                        // skin colors. Source-sampled ramp lowers draw-delta
                        // MAE 10.516 -> 8.947 on 532,385 changed pixels.
                        material.SetFloat("_UseSourceSkinLayer", 1f);
                    }
                    if (draw.eventId == 1035)
                    {
                        // Same-state RT0 changed-region sweep: the art path
                        // with zero extra shade improved 31.1860 to 30.1169.
                        // Stronger shade moved away from the captured hair.
                        material.SetFloat("_UseArtToon", 1f);
                        material.SetFloat("_ArtShadeStrength", 0f);
                        material.SetFloat("_ArtAO", 0f);
                        material.SetFloat("_ArtSpecularStrength", 0f);
                        material.SetFloat("_ArtRimStrength", 0f);
                        // EID1035 PS33678 trace: crescent pixels retain
                        // t3 color where t5.b and the t4 normal-Y band meet.
                        // Same-state source draw ROI: 22.734 -> 22.711 MAE.
                        material.SetFloat("_UseSourceHairMaskHighlight", 1f);
                        // PS33678 46-47 reads the curved specular shape from
                        // t5 blue. EID1035 traced adjacent gray pixels have
                        // identical t3=.84 but source r3.x becomes 1 on the
                        // arc and 0 outside. Restore its color addition and
                        // source 435-436 late diffuse in this draw only.
                        material.SetFloat("_UseSourceFrontHairArc", 1f);
                        material.SetFloat("_SourceFrontHairArcStrength", 0.13f);
                        material.SetFloat("_UseSourceLateDiffuse", 1f);
                        // The source arc stays outside this midtone gain;
                        // EID1035 draw MAE 18.7 -> 12.9 on the RDC mask.
                        material.SetColor("_SourceHairToneRGB",
                            new Color(0.90f, 0.84f, 0.93f, 1f));
                    }
                    // PS31475 array blend is post-lighting. The source
                    // band table improves the umbrella EID875 draw ROI;
                    // hair EID895 is neutral and 912/945 regress badly.
                    material.SetFloat("_UseCapturedWeaponPalette",
                        draw.eventId == 875 ? 1f : 0f);
                }
                if (eyePath)
                {
                    // RDC EID1273 RT0: RGB = One / InvSrcAlpha,
                    // alpha = InvDstAlpha / One. Depth test on, writes off.
                    material.SetFloat("_SrcBlend", (float)BlendMode.One);
                    material.SetFloat("_DstBlend", (float)BlendMode.OneMinusSrcAlpha);
                    material.SetFloat("_SrcBlendAlpha", (float)BlendMode.OneMinusDstAlpha);
                    material.SetFloat("_DstBlendAlpha", (float)BlendMode.One);
                    material.SetFloat("_ZWrite", 0f);
                }
                EditorUtility.SetDirty(material);
                changed++;
            }
            var tableSource = AssetDatabase.LoadAssetAtPath<TextAsset>(Root + "/Manifest/gbuffer5-material-tables.json");
            if (tableSource == null) throw new Exception("Missing gbuffer5-material-tables.json");
            var tables = JsonUtility.FromJson<TableManifest>(tableSource.text);
            if (tables.draws == null || tables.draws.Length != 9)
                throw new Exception("Expected nine body-family band tables");
            foreach (var draw in tables.draws)
            {
                var material = AssetDatabase.LoadAssetAtPath<Material>(
                    $"{Root}/Materials/EID{draw.eid}_GBuffer3D.mat");
                if (material == null || draw.bands == null || draw.bands.Length != 5)
                    throw new Exception("Invalid material table EID " + draw.eid);
                foreach (var band in draw.bands)
                {
                    if (band.band < 0 || band.band > 4 || band.tint == null || band.tint.Length != 3)
                        throw new Exception("Invalid band EID " + draw.eid);
                    material.SetVector("_Band" + band.band + "Tint",
                        new Vector4(band.tint[0], band.tint[1], band.tint[2], 0));
                    material.SetVector("_Band" + band.band + "Control",
                        new Vector4(band.arraySlice, band.weight, band.strengthCap, band.mode));
                }
                EditorUtility.SetDirty(material);
            }
            var outlineSource = AssetDatabase.LoadAssetAtPath<TextAsset>(
                Root + "/Manifest/gbuffer5-outline-material-tables.json");
            if (outlineSource == null) throw new Exception("Missing outline material tables");
            var outlines = JsonUtility.FromJson<OutlineManifest>(outlineSource.text);
            if (outlines.draws == null || outlines.draws.Length != 10)
                throw new Exception("Expected ten outline-family tables");
            foreach (var draw in outlines.draws)
            {
                var material = AssetDatabase.LoadAssetAtPath<Material>(
                    $"{Root}/Materials/EID{draw.eid}_GBuffer3D.mat");
                if (material == null || draw.bands == null || draw.bands.Length < 3)
                    throw new Exception("Invalid outline table EID " + draw.eid);
                foreach (var band in draw.bands)
                {
                    if (band.band < 0 || band.band > 4 || band.color == null || band.color.Length != 4)
                        throw new Exception("Invalid outline band EID " + draw.eid);
                    material.SetVector("_OutlineBand" + band.band,
                        new Vector4(band.color[0], band.color[1], band.color[2], band.color[3]));
                }
                EditorUtility.SetDirty(material);
            }
            var faceSource = AssetDatabase.LoadAssetAtPath<TextAsset>(
                Root + "/Manifest/gbuffer5-face-material-tables.json");
            if (faceSource == null) throw new Exception("Missing face material tables");
            var faces = JsonUtility.FromJson<FaceManifest>(faceSource.text);
            if (faces.draws == null || faces.draws.Length != 4)
                throw new Exception("Expected four face-family tables");
            foreach (var draw in faces.draws)
            {
                var material = AssetDatabase.LoadAssetAtPath<Material>(
                    $"{Root}/Materials/EID{draw.eid}_GBuffer3D.mat");
                if (material == null || draw.colorRows == null || draw.colorRows.Length != 7)
                    throw new Exception("Invalid face table EID " + draw.eid);
                foreach (var row in draw.colorRows)
                {
                    if (row.register < 29 || row.register > 35 || row.value == null || row.value.Length != 4)
                        throw new Exception("Invalid face color row EID " + draw.eid);
                    material.SetVector("_FaceColor" + row.register,
                        new Vector4(row.value[0], row.value[1], row.value[2], row.value[3]));
                }
                EditorUtility.SetDirty(material);
            }
            AssetDatabase.SaveAssets();
            return $"Assigned PS families to {changed}/26 materials, nine body, ten outline and four face tables";
        }

        static void ConfigureEyeLookupImporter()
        {
            // Eye VS t1 is a 16x16 UNORM data lookup, not a color atlas.
            const string path = Root + "/Textures/RID23285.png";
            var importer = AssetImporter.GetAtPath(path) as TextureImporter;
            if (importer == null) throw new Exception("Missing Eye_E RID23285 importer");
            if (!importer.sRGBTexture && importer.filterMode == FilterMode.Point &&
                !importer.mipmapEnabled && importer.textureCompression == TextureImporterCompression.Uncompressed)
                return;
            importer.sRGBTexture = false;
            importer.filterMode = FilterMode.Point;
            importer.mipmapEnabled = false;
            importer.textureCompression = TextureImporterCompression.Uncompressed;
            importer.SaveAndReimport();
        }

        static void ConfigureBodyAlbedoImporter()
        {
            // RenderDoc t3 RID42974 is BC7_SRGB. Unity's default PNG import
            // recompressed it to DXT5; keep the decoded source texels intact
            // while preserving mips for the captured -2 sample bias.
            const string path = Root + "/Textures/RID42974.png";
            var importer = AssetImporter.GetAtPath(path) as TextureImporter;
            if (importer == null) throw new Exception("Missing Body_1_D RID42974 importer");
            if (importer.sRGBTexture && importer.mipmapEnabled &&
                importer.textureCompression == TextureImporterCompression.Uncompressed)
                return;
            importer.sRGBTexture = true;
            importer.mipmapEnabled = true;
            importer.textureCompression = TextureImporterCompression.Uncompressed;
            importer.SaveAndReimport();
        }

        static void ConfigureFaceTextureImporters()
        {
            // Source t3 is BC7_SRGB and t4 is a float lightmap. Keep their
            // exported PNG control values without an extra DXT5 pass.
            foreach (var name in new[] { "RID42972.png", "RID25406.png" })
            {
                var path = Root + "/Textures/" + name;
                var importer = AssetImporter.GetAtPath(path) as TextureImporter;
                if (importer == null) throw new Exception("Missing face texture " + path);
                if (importer.textureCompression == TextureImporterCompression.Uncompressed &&
                    importer.mipmapEnabled) continue;
                importer.textureCompression = TextureImporterCompression.Uncompressed;
                importer.mipmapEnabled = true;
                importer.SaveAndReimport();
            }
        }
    }
}
