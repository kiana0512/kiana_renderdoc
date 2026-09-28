using System;
using System.IO;
using UnityEditor;
using UnityEngine;

namespace KianaFrameReconstruction
{
    // Same-scene scalar A/B without persisting the trial value.
    public static class ProbeMaterialScalar
    {
        public static string CapturePaletteActivation(int eid, float mask, float control,
                                                       float palette, string label, int throughEid)
        {
            var material = AssetDatabase.LoadAssetAtPath<Material>(
                $"Assets/Kiana/Materials/EID{eid}_GBuffer3D.mat");
            float oldUse = material.GetFloat("_UseCapturedWeaponPalette");
            float oldMask = material.GetFloat("_DecodeCapturedAux");
            float oldControl = material.GetFloat("_DecodeAuxControl");
            float oldPalette = material.GetFloat("_DecodePaletteSRGB");
            try
            {
                material.SetFloat("_UseCapturedWeaponPalette", 1f);
                material.SetFloat("_DecodeCapturedAux", mask);
                material.SetFloat("_DecodeAuxControl", control);
                material.SetFloat("_DecodePaletteSRGB", palette);
                var path = CaptureGBuffer5Stages.Capture(throughEid);
                var output = Path.ChangeExtension(path, null) +
                    $"-EID{eid}-activation-{label}.png";
                File.Copy(path, output, true);
                return output;
            }
            finally
            {
                material.SetFloat("_UseCapturedWeaponPalette", oldUse);
                material.SetFloat("_DecodeCapturedAux", oldMask);
                material.SetFloat("_DecodeAuxControl", oldControl);
                material.SetFloat("_DecodePaletteSRGB", oldPalette);
            }
        }

        public static string CapturePaletteDecode(int eid, float mask, float control,
                                                   float palette, string label, int throughEid)
        {
            var material = AssetDatabase.LoadAssetAtPath<Material>(
                $"Assets/Kiana/Materials/EID{eid}_GBuffer3D.mat");
            float oldMask = material.GetFloat("_DecodeCapturedAux");
            float oldControl = material.GetFloat("_DecodeAuxControl");
            float oldPalette = material.GetFloat("_DecodePaletteSRGB");
            try
            {
                material.SetFloat("_DecodeCapturedAux", mask);
                material.SetFloat("_DecodeAuxControl", control);
                material.SetFloat("_DecodePaletteSRGB", palette);
                var path = CaptureGBuffer5Stages.Capture(throughEid);
                var output = Path.ChangeExtension(path, null) +
                    $"-EID{eid}-palette-{label}.png";
                File.Copy(path, output, true);
                return output;
            }
            finally
            {
                material.SetFloat("_DecodeCapturedAux", oldMask);
                material.SetFloat("_DecodeAuxControl", oldControl);
                material.SetFloat("_DecodePaletteSRGB", oldPalette);
            }
        }

        public static string CapturePair(int eid, string propertyA, float valueA,
                                         string propertyB, float valueB,
                                         string label, int throughEid)
        {
            var material = AssetDatabase.LoadAssetAtPath<Material>(
                $"Assets/Kiana/Materials/EID{eid}_GBuffer3D.mat");
            float oldA = material.GetFloat(propertyA);
            float oldB = material.GetFloat(propertyB);
            try
            {
                material.SetFloat(propertyA, valueA);
                material.SetFloat(propertyB, valueB);
                var path = CaptureGBuffer5Stages.Capture(throughEid);
                var output = Path.ChangeExtension(path, null) +
                    $"-EID{eid}-{label}.png";
                File.Copy(path, output, true);
                return output;
            }
            finally
            {
                material.SetFloat(propertyA, oldA);
                material.SetFloat(propertyB, oldB);
            }
        }

        public static string CaptureAuxDecode(int eid, float normal, float mask,
                                              float control, string label, int throughEid)
        {
            var material = AssetDatabase.LoadAssetAtPath<Material>(
                $"Assets/Kiana/Materials/EID{eid}_GBuffer3D.mat");
            float oldNormal = material.GetFloat("_DecodeAuxNormal");
            float oldMask = material.GetFloat("_DecodeCapturedAux");
            float oldControl = material.GetFloat("_DecodeAuxControl");
            try
            {
                material.SetFloat("_DecodeAuxNormal", normal);
                material.SetFloat("_DecodeCapturedAux", mask);
                material.SetFloat("_DecodeAuxControl", control);
                var path = CaptureGBuffer5Stages.Capture(throughEid);
                var output = Path.ChangeExtension(path, null) +
                    $"-EID{eid}-aux-{label}.png";
                File.Copy(path, output, true);
                return output;
            }
            finally
            {
                material.SetFloat("_DecodeAuxNormal", oldNormal);
                material.SetFloat("_DecodeCapturedAux", oldMask);
                material.SetFloat("_DecodeAuxControl", oldControl);
            }
        }

        public static string CaptureShadowPair(int eid, float threshold, Color shadow,
                                               string label, int throughEid)
        {
            var material = AssetDatabase.LoadAssetAtPath<Material>(
                $"Assets/Kiana/Materials/EID{eid}_GBuffer3D.mat");
            float oldThreshold = material.GetFloat("_ArtShadowThreshold");
            Color oldShadow = material.GetColor("_ArtShadowColor");
            try
            {
                material.SetFloat("_ArtShadowThreshold", threshold);
                material.SetColor("_ArtShadowColor", shadow);
                var path = CaptureGBuffer5Stages.Capture(throughEid);
                var output = Path.ChangeExtension(path, null) + $"-EID{eid}-shadow-{label}.png";
                File.Copy(path, output, true);
                return output;
            }
            finally
            {
                material.SetFloat("_ArtShadowThreshold", oldThreshold);
                material.SetColor("_ArtShadowColor", oldShadow);
            }
        }

        public static string CaptureColor(int materialEid, string property, Color value, string label,
                                          int throughEid)
        {
            var material = AssetDatabase.LoadAssetAtPath<Material>(
                $"Assets/Kiana/Materials/EID{materialEid}_GBuffer3D.mat");
            if (material == null || !material.HasProperty(property))
                throw new Exception("Missing material color " + materialEid + " / " + property);
            Color previous = material.GetColor(property);
            try
            {
                material.SetColor(property, value);
                var path = CaptureGBuffer5Stages.Capture(throughEid);
                var output = Path.ChangeExtension(path, null) +
                    $"-EID{materialEid}-{property.TrimStart('_')}-{label}.png";
                File.Copy(path, output, true);
                return output;
            }
            finally { material.SetColor(property, previous); }
        }

        public static string Capture(int materialEid, string property, float value, int throughEid)
        {
            var material = AssetDatabase.LoadAssetAtPath<Material>(
                $"Assets/Kiana/Materials/EID{materialEid}_GBuffer3D.mat");
            if (material == null || !material.HasProperty(property))
                throw new Exception("Missing material property " + materialEid + " / " + property);
            float previous = material.GetFloat(property);
            try
            {
                material.SetFloat(property, value);
                var path = CaptureGBuffer5Stages.Capture(throughEid);
                var suffix = $"-EID{materialEid}-{property.TrimStart('_')}-{value:0.###}";
                var output = Path.ChangeExtension(path, null) + suffix + ".png";
                File.Copy(path, output, true);
                return output;
            }
            finally { material.SetFloat(property, previous); }
        }
    }
}
