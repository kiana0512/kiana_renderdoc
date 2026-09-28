using UnityEngine;

namespace KianaFrameReconstruction
{
    [ExecuteAlways]
    [RequireComponent(typeof(Camera))]
    public sealed class CapturedToonOutline : MonoBehaviour
    {
        public Color ink = new Color(0.035f, 0.028f, 0.080f, 1f);
        [Range(0.5f, 4f)] public float thicknessPx = 1.2f;
        [Range(0.0001f, 0.1f)] public float depthThreshold = 0.008f;
        [Range(0.01f, 1f)] public float normalThreshold = 0.32f;
        [Range(0f, 1f)] public float strength = 0.9f;
        Material material;

        void OnEnable()
        {
            // Color silhouette is stable under the captured camera's custom
            // projection; Unity's replacement depth-normal prepass is not.
        }

        void OnDisable()
        {
            if (material != null) DestroyImmediate(material);
            material = null;
        }

        void OnRenderImage(RenderTexture source, RenderTexture destination)
        {
            if (material == null)
            {
                var shader = Shader.Find("Hidden/Kiana/CapturedToonOutline");
                if (shader == null || !shader.isSupported)
                {
                    Graphics.Blit(source, destination);
                    return;
                }
                material = new Material(shader) { hideFlags = HideFlags.HideAndDontSave };
            }
            material.SetColor("_InkColor", ink);
            material.SetFloat("_ThicknessPx", thicknessPx);
            material.SetFloat("_DepthThreshold", depthThreshold);
            material.SetFloat("_NormalThreshold", normalThreshold);
            material.SetFloat("_InkStrength", strength);
            Graphics.Blit(source, destination, material);
        }
    }
}
