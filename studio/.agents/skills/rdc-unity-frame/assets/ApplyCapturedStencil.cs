using System;
using UnityEditor;
using UnityEngine;

namespace KianaFrameReconstruction
{
    // RenderDoc's per-face stencil state is kept separate from the material
    // shader candidate switch, so stage captures can test state independently.
    public static class ApplyCapturedStencil
    {
        const string Root = "Assets/Kiana";

        [Serializable] class Manifest { public Draw[] draws; }
        [Serializable] class Draw
        {
            public int eid, reference, readMask, writeMask;
            public int frontCompare, backCompare, frontPass, backPass;
            public bool enabled;
        }

        public static int ApplyThrough(int throughEventId, bool swapFaces)
        {
            var asset = AssetDatabase.LoadAssetAtPath<TextAsset>(
                Root + "/Manifest/gbuffer5-stencil.json");
            if (asset == null) throw new Exception("Missing G-buffer stencil manifest");
            var manifest = JsonUtility.FromJson<Manifest>(asset.text);
            if (manifest.draws == null || manifest.draws.Length != 26)
                throw new Exception("Expected 26 captured stencil states");
            int applied = 0;
            foreach (var draw in manifest.draws)
            {
                if (draw.eid > throughEventId) continue;
                var material = AssetDatabase.LoadAssetAtPath<Material>(
                    $"{Root}/Materials/EID{draw.eid}_GBuffer3D.mat");
                if (material == null || !material.HasProperty("_StencilRef"))
                    throw new Exception("Missing stencil shader/material EID " + draw.eid);
                material.SetInt("_StencilRef", draw.enabled ? draw.reference : 0);
                material.SetInt("_StencilReadMask", draw.enabled ? draw.readMask : 0);
                material.SetInt("_StencilWriteMask", draw.enabled ? draw.writeMask : 0);
                material.SetInt("_StencilCompFront", draw.enabled ?
                    (swapFaces ? draw.backCompare : draw.frontCompare) : 8);
                material.SetInt("_StencilCompBack", draw.enabled ?
                    (swapFaces ? draw.frontCompare : draw.backCompare) : 8);
                material.SetInt("_StencilPassFront", draw.enabled ?
                    (swapFaces ? draw.backPass : draw.frontPass) : 0);
                material.SetInt("_StencilPassBack", draw.enabled ?
                    (swapFaces ? draw.frontPass : draw.backPass) : 0);
                applied++;
            }
            return applied;
        }

        public static int ResetAll()
        {
            int reset = 0;
            var asset = AssetDatabase.LoadAssetAtPath<TextAsset>(
                Root + "/Manifest/gbuffer5-stencil.json");
            var manifest = JsonUtility.FromJson<Manifest>(asset.text);
            foreach (var draw in manifest.draws)
            {
                var material = AssetDatabase.LoadAssetAtPath<Material>(
                    $"{Root}/Materials/EID{draw.eid}_GBuffer3D.mat");
                material.SetInt("_StencilRef", 0);
                material.SetInt("_StencilReadMask", 0);
                material.SetInt("_StencilWriteMask", 0);
                material.SetInt("_StencilCompFront", 8);
                material.SetInt("_StencilCompBack", 8);
                material.SetInt("_StencilPassFront", 0);
                material.SetInt("_StencilPassBack", 0);
                reset++;
            }
            return reset;
        }
    }
}
