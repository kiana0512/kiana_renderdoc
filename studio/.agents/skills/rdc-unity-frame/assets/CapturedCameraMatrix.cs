using UnityEngine;

namespace KianaFrameReconstruction
{
    [ExecuteAlways]
    [RequireComponent(typeof(Camera))]
    public sealed class CapturedCameraMatrix : MonoBehaviour
    {
        public float[] viewProjection;

        void OnEnable() { Apply(); }
        void OnValidate() { Apply(); }
        void LateUpdate() { Apply(); }
        void OnPreRender()
        {
            Shader.SetGlobalFloat("_RdcDepthFlip", 1f);
            Shader.SetGlobalFloat("_RdcFaceFlip", 1f);
        }
        void OnPostRender()
        {
            Shader.SetGlobalFloat("_RdcDepthFlip", 0f);
            Shader.SetGlobalFloat("_RdcFaceFlip", 0f);
        }
        void OnDisable()
        {
            Shader.SetGlobalFloat("_RdcDepthFlip", 0f);
            Shader.SetGlobalFloat("_RdcFaceFlip", 0f);
        }

        public void Apply()
        {
            if (viewProjection == null || viewProjection.Length != 16) return;
            var matrix = new Matrix4x4();
            for (int row = 0; row < 4; row++)
                for (int col = 0; col < 4; col++)
                    matrix[row, col] = viewProjection[row * 4 + col];
            var camera = GetComponent<Camera>();
            camera.projectionMatrix = matrix * camera.worldToCameraMatrix.inverse;
            camera.cullingMatrix = matrix;
        }
    }
}
