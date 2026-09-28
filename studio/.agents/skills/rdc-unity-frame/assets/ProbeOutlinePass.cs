using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEngine;

namespace KianaFrameReconstruction
{
    // Temporary A/B probe. Restores scene and materials after each capture.
    public static class ProbeOutlinePass
    {
        static readonly int[] OutlineIds = { 1057, 1078, 1091, 1107, 1118,
                                             1130, 1143, 1161, 1183, 1331 };
        static readonly string[] Keys = { "_StencilRef", "_StencilReadMask", "_StencilWriteMask",
            "_StencilCompFront", "_StencilCompBack", "_StencilPassFront", "_StencilPassBack",
            "_RdcFamilyEnabled", "_UseCapturedOutlineClip", "_Cull", "_ZTest", "_OutlineDepthOffset" };

        public static string RunDepth(int eid, int zTest, float depthOffset = 0f,
                                      bool stencilOutside = false)
        {
            var root = GameObject.Find("Frame 38112 — 3D G-buffer reconstruction");
            if (root == null) throw new Exception("Open G-buffer world scene");
            GameObject target = null;
            foreach (Transform group in root.transform)
                foreach (Transform child in group)
                    if (child.name.StartsWith("EID " + eid + " —")) target = child.gameObject;
            if (target == null) throw new Exception("Outline draw object missing " + eid);
            var material = AssetDatabase.LoadAssetAtPath<Material>(
                $"Assets/Kiana/Materials/EID{eid}_GBuffer3D.mat");
            if (material == null) throw new Exception("Outline material missing " + eid);
            var old = new float[Keys.Length];
            for (int i = 0; i < Keys.Length; i++) old[i] = material.GetFloat(Keys[i]);
            bool active = target.activeSelf;
            try
            {
                target.SetActive(true);
                material.SetFloat("_RdcFamilyEnabled", 1f);
                material.SetFloat("_Cull", 1f);
                material.SetFloat("_UseCapturedOutlineClip", 1f);
                material.SetFloat("_ZTest", zTest);
                material.SetFloat("_OutlineDepthOffset", depthOffset);
                ApplyCapturedStencil.ApplyThrough(eid, false);
                if (stencilOutside)
                {
                    material.SetFloat("_StencilRef", 0f);
                    material.SetFloat("_StencilReadMask", 128f);
                    material.SetFloat("_StencilCompFront", 6f);
                    material.SetFloat("_StencilCompBack", 6f);
                }
                string source = CaptureGBuffer5Stages.Capture(eid);
                string output = $"Assets/Kiana/Validation/StageRenders/EID{eid}-outline-z{zTest}-offset{depthOffset:F4}-stencil{stencilOutside}.png";
                File.Copy(source, output, true);
                return output;
            }
            finally
            {
                target.SetActive(active);
                for (int i = 0; i < Keys.Length; i++)
                    material.SetFloat(Keys[i], old[i]);
                ApplyCapturedStencil.ResetAll();
            }
        }

        public static string Run(int singleEid = 0)
        {
            var root = GameObject.Find("Frame 38112 — 3D G-buffer reconstruction");
            if (root == null) throw new Exception("Open G-buffer world scene");
            var objects = new Dictionary<int, GameObject>();
            foreach (Transform group in root.transform)
                foreach (Transform child in group)
                    foreach (int eid in OutlineIds)
                        if (child.name.StartsWith("EID " + eid + " —"))
                            objects[eid] = child.gameObject;
            if (objects.Count != OutlineIds.Length) throw new Exception("Outline draw object missing");
            var materials = new Dictionary<int, Material>();
            var values = new Dictionary<int, float[]>();
            var active = new Dictionary<int, bool>();
            foreach (int eid in OutlineIds)
            {
                var m = AssetDatabase.LoadAssetAtPath<Material>(
                    $"Assets/Kiana/Materials/EID{eid}_GBuffer3D.mat");
                if (m == null) throw new Exception("Outline material missing " + eid);
                materials[eid] = m;
                var old = new float[Keys.Length];
                for (int i = 0; i < Keys.Length; i++) old[i] = m.GetFloat(Keys[i]);
                values[eid] = old;
                active[eid] = objects[eid].activeSelf;
            }
            var path = "Assets/Kiana/Validation/StageRenders/";
            int through = singleEid > 0 ? singleEid : 1331;
            string stem = "EID" + through + "-outline";
            try
            {
                File.Copy(CaptureGBuffer5Stages.Capture(through), path + stem + "-base.png", true);
                foreach (int eid in OutlineIds)
                {
                    if (singleEid > 0 && eid != singleEid) continue;
                    objects[eid].SetActive(true);
                    materials[eid].SetFloat("_RdcFamilyEnabled", 1f);
                    materials[eid].SetFloat("_Cull", 1f); // source culls front faces
                    materials[eid].SetFloat("_UseCapturedOutlineClip", 1f);
                }
                foreach (bool swapFaces in new[] { false, true })
                {
                    ApplyCapturedStencil.ApplyThrough(through, swapFaces);
                    File.Copy(CaptureGBuffer5Stages.Capture(through),
                        path + stem + "-stencil-" + (swapFaces ? "swapped" : "source") + ".png", true);
                }
                return "Captured baseline and two stencil/cull outline variants";
            }
            finally
            {
                foreach (int eid in OutlineIds)
                {
                    objects[eid].SetActive(active[eid]);
                    for (int i = 0; i < Keys.Length; i++)
                        materials[eid].SetFloat(Keys[i], values[eid][i]);
                }
                // Base materials were touched only by the stencil probe.
                ApplyCapturedStencil.ResetAll();
            }
        }
    }
}
