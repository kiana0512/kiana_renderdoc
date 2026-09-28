using System;
using System.IO;
using UnityEditor;
using UnityEngine;

namespace KianaFrameReconstruction
{
    public static class ProbeInvertedHull
    {
        static readonly int[] OutlineIds = { 1057, 1078, 1091, 1107, 1118,
                                             1130, 1143, 1161, 1183, 1331 };

        public static string RunAll(float width = 0.003f)
        {
            var root = GameObject.Find("Frame 38112 — 3D G-buffer reconstruction");
            if (root == null) throw new Exception("Open G-buffer world scene");
            var targets = new System.Collections.Generic.List<GameObject>();
            var renderers = new System.Collections.Generic.List<Renderer>();
            var original = new System.Collections.Generic.List<Material>();
            var active = new System.Collections.Generic.List<bool>();
            foreach (Transform group in root.transform)
                foreach (Transform child in group)
                    foreach (int eid in OutlineIds)
                        if (child.name.StartsWith("EID " + eid + " —"))
                        {
                            targets.Add(child.gameObject);
                            renderers.Add(child.GetComponent<Renderer>());
                            original.Add(child.GetComponent<Renderer>().sharedMaterial);
                            active.Add(child.gameObject.activeSelf);
                        }
            if (targets.Count != OutlineIds.Length) throw new Exception("Expected 10 outlines");
            var shader = Shader.Find("Kiana/ToonInvertedHull");
            var candidate = new Material(shader) { hideFlags = HideFlags.HideAndDontSave };
            candidate.SetFloat("_Width", width);
            candidate.SetFloat("_Cull", 1f);
            candidate.renderQueue = 3000;
            try
            {
                for (int i = 0; i < targets.Count; i++)
                {
                    targets[i].SetActive(true);
                    renderers[i].sharedMaterial = candidate;
                }
                string source = CaptureGBuffer5Stages.Capture(1331);
                string output = $"Assets/Kiana/Validation/StageRenders/EID1331-hull-all-{width:F4}.png";
                File.Copy(source, output, true);
                return output;
            }
            finally
            {
                for (int i = 0; i < targets.Count; i++)
                {
                    renderers[i].sharedMaterial = original[i];
                    targets[i].SetActive(active[i]);
                }
                UnityEngine.Object.DestroyImmediate(candidate);
            }
        }

        public static string Run(int eid, float width, int cull = 1)
        {
            var root = GameObject.Find("Frame 38112 — 3D G-buffer reconstruction");
            if (root == null) throw new Exception("Open G-buffer world scene");
            GameObject target = null;
            foreach (Transform group in root.transform)
                foreach (Transform child in group)
                    if (child.name.StartsWith("EID " + eid + " —")) target = child.gameObject;
            if (target == null) throw new Exception("Outline draw object missing " + eid);
            var renderer = target.GetComponent<Renderer>();
            if (renderer == null) throw new Exception("Renderer missing " + eid);
            var shader = Shader.Find("Kiana/ToonInvertedHull");
            if (shader == null || !shader.isSupported) throw new Exception("Hull shader missing");
            bool active = target.activeSelf;
            var original = renderer.sharedMaterial;
            var material = new Material(shader) { hideFlags = HideFlags.HideAndDontSave };
            material.SetFloat("_Width", width);
            material.SetFloat("_Cull", cull);
            material.renderQueue = 3000;
            try
            {
                target.SetActive(true);
                renderer.sharedMaterial = material;
                string source = CaptureGBuffer5Stages.Capture(eid);
                string output = $"Assets/Kiana/Validation/StageRenders/EID{eid}-hull-{width:F4}-cull{cull}.png";
                File.Copy(source, output, true);
                return output;
            }
            finally
            {
                renderer.sharedMaterial = original;
                target.SetActive(active);
                UnityEngine.Object.DestroyImmediate(material);
            }
        }
    }
}
