using System;
using System.IO;
using UnityEditor;
using UnityEngine;

namespace KianaFrameReconstruction
{
    // Temporary A/B capture. Never saves modified materials or scene state.
    public static class DiagnoseEyeStencil
    {
        public static string CaptureHairCull(int cull)
        {
            var hair = AssetDatabase.LoadAssetAtPath<Material>(
                "Assets/Kiana/Materials/EID1313_GBuffer3D.mat");
            var previous = hair.GetInt("_Cull");
            try
            {
                hair.SetInt("_Cull", cull);
                var path = CaptureGBuffer5Stages.Capture(1331);
                var output = Path.ChangeExtension(path, null) + "-hair-cull" + cull + ".png";
                File.Copy(path, output, true);
                return output;
            }
            finally { hair.SetInt("_Cull", previous); }
        }

        public static string CaptureHairAlpha()
        {
            var hair = AssetDatabase.LoadAssetAtPath<Material>(
                "Assets/Kiana/Materials/EID1313_GBuffer3D.mat");
            var oldDebug = hair.GetFloat("_DebugOutput");
            var oldSource = hair.GetInt("_SrcBlend");
            var oldDest = hair.GetInt("_DstBlend");
            try
            {
                hair.SetFloat("_DebugOutput", 7);
                hair.SetInt("_SrcBlend", 1);
                hair.SetInt("_DstBlend", 0);
                var path = CaptureGBuffer5Stages.Capture(1313);
                var output = Path.ChangeExtension(path, null) + "-hair-alpha-debug.png";
                File.Copy(path, output, true);
                return output;
            }
            finally
            {
                hair.SetFloat("_DebugOutput", oldDebug);
                hair.SetInt("_SrcBlend", oldSource);
                hair.SetInt("_DstBlend", oldDest);
            }
        }

        public static string Inspect()
        {
            var result = "";
            foreach (var transform in UnityEngine.Object.FindObjectsByType<Transform>(FindObjectsInactive.Include))
            {
                if (!transform.name.StartsWith("EID 1313") &&
                    !transform.name.StartsWith("EID 1035")) continue;
                var renderer = transform.GetComponent<MeshRenderer>();
                var mesh = transform.GetComponent<MeshFilter>()?.sharedMesh;
                result += transform.name + ":self=" + transform.gameObject.activeSelf +
                    ":hierarchy=" + transform.gameObject.activeInHierarchy +
                    ":material=" + (renderer == null ? "none" : renderer.sharedMaterial.name) +
                    ":position=" + transform.position + ":bounds=" + (mesh == null ? "none" : mesh.bounds.ToString()) +
                    ":vertex0=" + (mesh == null ? "none" : mesh.vertices[0].ToString()) + ";";
            }
            return result;
        }
        [Serializable] class Manifest { public Draw[] draws; }
        [Serializable] class Draw
        {
            public int eid, reference, readMask, writeMask;
            public int frontCompare, backCompare, frontPass, backPass;
        }

        static readonly int[] Ids = { 992, 1008, 1035, 1313 };
        static readonly string[] Names = {
            "_StencilRef", "_StencilReadMask", "_StencilWriteMask",
            "_StencilCompFront", "_StencilCompBack",
            "_StencilPassFront", "_StencilPassBack"
        };

        public static string Run(bool swapFaces)
        {
            return RunVariant(swapFaces, false);
        }

        public static string RunVariant(bool swapFaces, bool symmetricEye)
        {
            return RunVariant(swapFaces, symmetricEye, false);
        }

        public static string RunVariant(bool swapFaces, bool symmetricEye, bool sourceHairAlpha)
        {
            return RunVariant(swapFaces, symmetricEye, sourceHairAlpha, false);
        }

        public static string RunVariant(bool swapFaces, bool symmetricEye, bool sourceHairAlpha,
                                        bool hairDepthAlways)
        {
            var manifest = JsonUtility.FromJson<Manifest>(AssetDatabase.LoadAssetAtPath<TextAsset>(
                "Assets/Kiana/Manifest/gbuffer5-stencil.json").text);
            var materials = new Material[Ids.Length];
            var original = new int[Ids.Length, Names.Length];
            var hair = AssetDatabase.LoadAssetAtPath<Material>(
                "Assets/Kiana/Materials/EID1313_GBuffer3D.mat");
            string[] hairNames = { "_UseSourceHairAlpha", "_SrcBlend", "_DstBlend",
                                   "_SrcBlendAlpha", "_DstBlendAlpha", "_ZTest" };
            var originalHair = new int[hairNames.Length];
            for (int i = 0; i < hairNames.Length; i++)
                originalHair[i] = hair.GetInt(hairNames[i]);
            GameObject hairObject = null;
            foreach (var transform in UnityEngine.Object.FindObjectsByType<Transform>(FindObjectsInactive.Include))
                if (transform.name.StartsWith("EID 1313")) { hairObject = transform.gameObject; break; }
            if (hairObject == null) throw new Exception("Missing EID 1313 scene object");
            bool originalActive = hairObject.activeSelf;
            for (int i = 0; i < Ids.Length; i++)
            {
                materials[i] = AssetDatabase.LoadAssetAtPath<Material>(
                    $"Assets/Kiana/Materials/EID{Ids[i]}_GBuffer3D.mat");
                if (materials[i] == null) throw new Exception("Missing material " + Ids[i]);
                for (int j = 0; j < Names.Length; j++)
                    original[i, j] = materials[i].GetInt(Names[j]);
            }
            try
            {
                for (int i = 0; i < Ids.Length; i++)
                {
                    Draw draw = null;
                    foreach (var entry in manifest.draws)
                        if (entry.eid == Ids[i]) { draw = entry; break; }
                    if (draw == null) throw new Exception("Missing stencil state " + Ids[i]);
                    var values = new[] { draw.reference, draw.readMask, draw.writeMask,
                        swapFaces ? draw.backCompare : draw.frontCompare,
                        swapFaces ? draw.frontCompare : draw.backCompare,
                        swapFaces ? draw.backPass : draw.frontPass,
                        swapFaces ? draw.frontPass : draw.backPass };
                    if (symmetricEye && Ids[i] == 1008)
                    {
                        values[5] = 2;
                        values[6] = 2;
                    }
                    if (symmetricEye && (Ids[i] == 1035 || Ids[i] == 1313))
                    {
                        values[3] = draw.frontCompare;
                        values[4] = draw.frontCompare;
                    }
                    for (int j = 0; j < Names.Length; j++) materials[i].SetInt(Names[j], values[j]);
                }
                if (sourceHairAlpha)
                {
                    hair.SetInt("_UseSourceHairAlpha", 1);
                    hair.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
                    hair.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
                    hair.SetInt("_SrcBlendAlpha", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
                    hair.SetInt("_DstBlendAlpha", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
                }
                if (hairDepthAlways) hair.SetInt("_ZTest", (int)UnityEngine.Rendering.CompareFunction.Always);
                hairObject.SetActive(true);
                var suffix = (symmetricEye ? "symmetric" : (swapFaces ? "swap" : "noswap")) +
                    (sourceHairAlpha ? "-alpha" : "") + (hairDepthAlways ? "-zalways" : "");
                var paths = new[] { CaptureGBuffer5Stages.Capture(1008),
                                    CaptureGBuffer5Stages.Capture(1035),
                                    CaptureGBuffer5Stages.Capture(1313),
                                    CaptureGBuffer5Stages.Capture(1331) };
                foreach (var path in paths)
                    File.Copy(path, Path.ChangeExtension(path, null) + "-eye-stencil-" + suffix + ".png", true);
                return suffix;
            }
            finally
            {
                hairObject.SetActive(originalActive);
                for (int i = 0; i < hairNames.Length; i++)
                    hair.SetInt(hairNames[i], originalHair[i]);
                for (int i = 0; i < Ids.Length; i++)
                    for (int j = 0; j < Names.Length; j++)
                        materials[i].SetInt(Names[j], original[i, j]);
            }
        }
    }
}
