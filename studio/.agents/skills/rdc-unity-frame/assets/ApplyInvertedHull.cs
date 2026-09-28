using System;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace KianaFrameReconstruction
{
    public static class ApplyInvertedHull
    {
        static readonly int[] Visible = { 1057, 1078, 1091, 1107, 1118,
                                          1143, 1183 };
        static readonly int[] EmptyInSource = { 1130, 1161 };
        // Source EID1331 changes only 313 RT0 pixels. Without its stencil
        // restriction, this duplicate hull darkens 11k unrelated pixels.
        static readonly int[] DeferredStencil = { 1331 };

        static float SourceWidthPx(int eid)
        {
            switch (eid)
            {
                case 1057: return 0.235f;
                case 1078: return 1.951f;
                case 1091: return 1.933f;
                case 1107: return 2.051f;
                case 1118: return 2.119f;
                case 1143: return 2.043f;
                case 1183: return 1.825f;
                case 1331: return 1.825f;
                default: throw new ArgumentOutOfRangeException(nameof(eid));
            }
        }

        [MenuItem("Kiana/Apply Native Inverted Hull Outlines")]
        public static string ApplyAll()
        {
            var root = GameObject.Find("Frame 38112 — 3D G-buffer reconstruction");
            if (root == null) throw new Exception("Open G-buffer world scene");
            var shader = Shader.Find("Kiana/ToonInvertedHullDual");
            if (shader == null || !shader.isSupported) throw new Exception("Hull shader missing");
            const string folder = "Assets/Kiana/Materials/OutlineHull";
            Directory.CreateDirectory(folder);
            int applied = 0;
            foreach (Transform group in root.transform)
                foreach (Transform child in group)
                {
                    int eid = 0;
                    foreach (int value in Visible)
                        if (child.name.StartsWith("EID " + value + " —")) eid = value;
                    if (eid == 0)
                    {
                        foreach (int value in EmptyInSource)
                            if (child.name.StartsWith("EID " + value + " —"))
                                child.gameObject.SetActive(false);
                        foreach (int value in DeferredStencil)
                            if (child.name.StartsWith("EID " + value + " —"))
                                child.gameObject.SetActive(false);
                        continue;
                    }
                    string path = $"{folder}/EID{eid}_Hull.mat";
                    var material = AssetDatabase.LoadAssetAtPath<Material>(path);
                    if (material == null)
                    {
                        material = new Material(shader);
                        AssetDatabase.CreateAsset(material, path);
                    }
                    material.shader = shader;
                    // Source RT0 changed-pixel medians for the two hair hull
                    // draws. PS31479 varies the ink by pixel; these constants
                    // are the best tested single-color approximations.
                    Color ink = eid == 1107
                        ? new Color(20f / 255f, 17f / 255f, 50f / 255f, 1f)
                        : eid == 1183
                            ? new Color(20f / 255f, 19f / 255f, 42f / 255f, 1f)
                            : new Color(0.022f, 0.018f, 0.050f, 1f);
                    material.SetColor("_InkColor", ink);
                    // EID1183's source median screen displacement is 1.825 px.
                    // Same-camera final-frame A/B favors 1.8 over 1, 2, 2.2.
                    float width = eid == 1107 ? 2f : eid == 1183 ? 1.8f : 1f;
                    material.SetFloat("_ReferenceWidthPx", width);
                    // The RDC post-VS clip stream is stored in mesh UV5. Use
                    // its exact XY for the captured camera, while retaining
                    // Unity depth and the editable Scene-view hull.
                    material.SetFloat("_CapturedOutlineXYBlend", 1f);
                    material.SetFloat("_ZTest", 4f);
                    material.renderQueue = 3000;
                    EditorUtility.SetDirty(material);
                    var renderer = child.GetComponent<Renderer>();
                    if (renderer == null) throw new Exception("Outline renderer missing " + eid);
                    renderer.sharedMaterial = material;
                    child.gameObject.SetActive(true);
                    applied++;
                }
            AssetDatabase.SaveAssets();
            EditorSceneManager.MarkSceneDirty(root.scene);
            EditorSceneManager.SaveScene(root.scene);
            return $"Saved {applied} native 3D inverted-hull outlines; 2 source-empty and 1 stencil-deferred draws inactive";
        }
    }
}
