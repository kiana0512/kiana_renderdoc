using UnityEngine;

namespace KianaFrameReconstruction
{
    // A measured starting point for pass 5, not the original game's lighting system.
    [ExecuteAlways]
    public sealed class CapturedLightingParameters : MonoBehaviour
    {
        [SerializeField] Vector3 direction = new Vector3(-0.134544f, 0.944284f, 0.300376f);
        [SerializeField, Range(0, 2)] float ambient = 0.787676f;
        [SerializeField, Range(0, 2)] float diffuse = 0.281438f;
        [SerializeField] Vector3 entityLightPosition = new Vector3(590.545593f, 17.584890f, 16.030233f);
        [SerializeField] float entityLightRadius = 50f;

        void OnEnable() => Apply();
        void OnValidate() => Apply();
        void Update() => Apply();

        public void Apply()
        {
            Vector3 unit = direction.sqrMagnitude > 1e-8f ? direction.normalized : Vector3.up;
            Shader.SetGlobalVector("_CapturedLightDirection", new Vector4(unit.x, unit.y, unit.z, 0));
            Shader.SetGlobalFloat("_CapturedAmbient", ambient);
            Shader.SetGlobalFloat("_CapturedDiffuse", diffuse);
            // PS t1[0] is RID 24248, not GPULightDataForChar. The optional
            // point-light diagnostic uses these captured bytes when enabled.
            Shader.SetGlobalVector("_CapturedPointLightPosition",
                new Vector4(entityLightPosition.x, entityLightPosition.y, entityLightPosition.z, 1));
            Shader.SetGlobalFloat("_CapturedPointLightRadius", entityLightRadius);
        }
    }
}
