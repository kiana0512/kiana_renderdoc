using System;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.SceneManagement;

namespace KianaFrameReconstruction
{
    // Frame 38112: EID1008 marks the eye, EID1035 avoids it, and EID1313
    // blends a second front-hair layer across the marked pixels.
    public static class ApplyEyeHairLayer
    {
        [MenuItem("Kiana/Apply Frame 38112 Eye Hair Layer")]
        public static void ApplyAll()
        {
            SetStencil(992, 128, 128, 255, 8, 2, 0);
            SetStencil(1008, 144, 128, 255, 8, 2);
            SetStencil(1035, 144, 144, 128, 6, 2);
            SetStencil(1313, 144, 144, 128, 3, 2);

            var hair = GetMaterial(1313);
            hair.SetFloat("_UseSourceHairAlpha", 1);
            hair.SetInt("_SrcBlend", (int)BlendMode.SrcAlpha);
            hair.SetInt("_DstBlend", (int)BlendMode.OneMinusSrcAlpha);
            hair.SetInt("_SrcBlendAlpha", (int)BlendMode.SrcAlpha);
            hair.SetInt("_DstBlendAlpha", (int)BlendMode.OneMinusSrcAlpha);
            // D3D source culls the opposite winding under this Unity camera.
            // Cull Front is the measured one-layer match for the eye pixels.
            hair.SetInt("_Cull", (int)CullMode.Front);
            // EID1313's captured RT0 change mask is 1,019 pixels around the
            // eyes. The source-over-Unity fit on that mask selects this RGB
            // scale while the exact PS33678 color chain is still incomplete.
            hair.SetColor("_Tint", new Color(0.62f, 0.67f, 0.75f, 1f));
            EditorUtility.SetDirty(hair);

            bool found = false;
            foreach (var transform in UnityEngine.Object.FindObjectsByType<Transform>(FindObjectsInactive.Include))
            {
                if (!transform.name.StartsWith("EID 1313")) continue;
                transform.gameObject.SetActive(true);
                found = true;
                break;
            }
            if (!found) throw new Exception("EID 1313 scene object missing");
            AssetDatabase.SaveAssets();
            var scene = SceneManager.GetActiveScene();
            EditorSceneManager.MarkSceneDirty(scene);
        }

        static Material GetMaterial(int eid)
        {
            var material = AssetDatabase.LoadAssetAtPath<Material>(
                $"Assets/Kiana/Materials/EID{eid}_GBuffer3D.mat");
            if (material == null) throw new Exception("Missing material EID " + eid);
            return material;
        }

        static void SetStencil(int eid, int reference, int readMask, int writeMask,
                               int compare, int pass, int backPass = 2)
        {
            // Source front/back tests differ. Unity's captured projection and
            // imported winding disagree here, so the symmetric eye mask is
            // the measured, same-camera candidate for these four draws.
            var material = GetMaterial(eid);
            material.SetInt("_StencilRef", reference);
            material.SetInt("_StencilReadMask", readMask);
            material.SetInt("_StencilWriteMask", writeMask);
            material.SetInt("_StencilCompFront", compare);
            material.SetInt("_StencilCompBack", compare);
            material.SetInt("_StencilPassFront", pass);
            material.SetInt("_StencilPassBack", backPass);
            EditorUtility.SetDirty(material);
        }
    }
}
