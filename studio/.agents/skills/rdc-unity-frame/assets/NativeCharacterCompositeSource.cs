using UnityEngine;

namespace Kiana.Frame38112
{
    // Final camera composites an actual render of the 3D character.
    // The stage background remains an RDC reference until its UI draws are rebuilt.
    [ExecuteAlways]
    [RequireComponent(typeof(Camera))]
    public sealed class NativeCharacterCompositeSource : MonoBehaviour
    {
        [Header("01 - Native 3D G-buffer")]
        public bool renderNativeCharacter = true;
        public Camera capturedCamera;
        public int sourceWidth = 2880;
        public int sourceHeight = 1368;

        [Header("02 - Final composite")]
        public bool showBackground = true;
        public Texture2D backgroundStageReference;
        public Vector2 characterScreenExtent = new Vector2(-0.05208332f, 1.1302084f);

        [Header("03 - Character tone / color grade")]
        public bool enableColorGrade = true;
        public Vector3 toneGain = new Vector3(0.916f, 0.949f, 0.747f);
        public Vector3 toneLift = new Vector3(0.259f, 0.267f, 0.402f);

        [Header("04 - Character bloom")]
        public bool enableBloom = false;
        [Range(0, 1)] public float bloomIntensity = 0.12f;

        RenderTexture nativeFrame;
        Material compositeMaterial;

        void OnPreCull()
        {
            if (!renderNativeCharacter || !capturedCamera) return;
            if (!nativeFrame || nativeFrame.width != sourceWidth || nativeFrame.height != sourceHeight)
            {
                ReleaseFrame();
                nativeFrame = new RenderTexture(sourceWidth, sourceHeight, 24,
                    RenderTextureFormat.ARGB32, RenderTextureReadWrite.sRGB);
                nativeFrame.name = "Frame38112 native 3D render";
                nativeFrame.hideFlags = HideFlags.DontSave;
                nativeFrame.Create();
            }

            var oldTarget = capturedCamera.targetTexture;
            var oldFlags = capturedCamera.clearFlags;
            var oldColor = capturedCamera.backgroundColor;
            var oldMask = capturedCamera.cullingMask;
            try
            {
                capturedCamera.targetTexture = nativeFrame;
                capturedCamera.clearFlags = CameraClearFlags.SolidColor;
                capturedCamera.backgroundColor = Color.clear;
                capturedCamera.cullingMask = 1 << 31;
                var matrix = capturedCamera.GetComponent<KianaFrameReconstruction.CapturedCameraMatrix>();
                if (matrix) matrix.Apply();
                capturedCamera.Render();
            }
            finally
            {
                capturedCamera.targetTexture = oldTarget;
                capturedCamera.clearFlags = oldFlags;
                capturedCamera.backgroundColor = oldColor;
                capturedCamera.cullingMask = oldMask;
            }
        }

        void OnRenderImage(RenderTexture source, RenderTexture destination)
        {
            if (!nativeFrame)
            {
                Graphics.Blit(source, destination);
                return;
            }
            if (!compositeMaterial)
            {
                var shader = Shader.Find("Kiana/NativeFinalStage");
                if (!shader) { Graphics.Blit(source, destination); return; }
                compositeMaterial = new Material(shader) { hideFlags = HideFlags.DontSave };
            }
            compositeMaterial.SetTexture("_BackgroundTex", backgroundStageReference);
            compositeMaterial.SetTexture("_CharacterTex", nativeFrame);
            compositeMaterial.SetVector("_CharacterExtent", characterScreenExtent);
            compositeMaterial.SetFloat("_ShowBackground", showBackground ? 1f : 0f);
            compositeMaterial.SetFloat("_EnableColorGrade", enableColorGrade ? 1f : 0f);
            compositeMaterial.SetVector("_ToneGain", toneGain);
            compositeMaterial.SetVector("_ToneLift", toneLift);
            compositeMaterial.SetFloat("_BloomIntensity", enableBloom ? bloomIntensity : 0f);
            Graphics.Blit(source, destination, compositeMaterial);
        }

        void OnDisable()
        {
            ReleaseFrame();
            if (compositeMaterial)
            {
                if (Application.isPlaying) Destroy(compositeMaterial);
                else DestroyImmediate(compositeMaterial);
                compositeMaterial = null;
            }
        }

        void ReleaseFrame()
        {
            if (!nativeFrame) return;
            nativeFrame.Release();
            if (Application.isPlaying) Destroy(nativeFrame);
            else DestroyImmediate(nativeFrame);
            nativeFrame = null;
        }
    }
}
