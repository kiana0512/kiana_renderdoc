using System;
using System.IO;
using UnityEditor;
using UnityEngine;

namespace KianaFrameReconstruction
{
    // Checks the actual live Unity transforms, not only the source manifest math.
    public static class AuditCapturedPose
    {
        [Serializable] class Manifest { public EventTransform[] events; }
        [Serializable] class EventTransform { public int eventId; public float[] localToWorld; }
        [Serializable] class Report { public string scene; public PoseRow[] events; }
        [Serializable] class PoseRow
        {
            public int eventId;
            public int vertices;
            public float maxWorldPositionError;
            public float meanWorldPositionError;
            public float maxMatrixError;
        }

        [MenuItem("Kiana/Audit Captured Pose")]
        public static string Run()
        {
            var asset = AssetDatabase.LoadAssetAtPath<TextAsset>("Assets/Kiana/Manifest/gbuffer5-transforms.json");
            if (asset == null) throw new Exception("Missing captured transform manifest");
            var manifest = JsonUtility.FromJson<Manifest>(asset.text);
            var report = new Report { scene = UnityEngine.SceneManagement.SceneManager.GetActiveScene().path,
                                      events = new PoseRow[manifest.events.Length] };
            float overall = 0f;
            for (int i = 0; i < manifest.events.Length; i++)
            {
                var entry = manifest.events[i];
                var expected = new Matrix4x4();
                for (int row = 0; row < 4; row++)
                    for (int col = 0; col < 4; col++)
                        expected[row, col] = entry.localToWorld[row * 4 + col];
                var objectName = "EID " + entry.eventId + " — 3D mesh, " +
                    FindIndexCount(entry.eventId) + " indices";
                GameObject go = null;
                foreach (var candidate in Resources.FindObjectsOfTypeAll<GameObject>())
                    if (candidate.scene.IsValid() && candidate.name == objectName)
                    { go = candidate; break; }
                if (go == null) throw new Exception("Missing live EID " + entry.eventId);
                var mesh = go.GetComponent<MeshFilter>().sharedMesh;
                var actual = go.transform.localToWorldMatrix;
                var rowReport = new PoseRow { eventId = entry.eventId, vertices = mesh.vertexCount };
                for (int row = 0; row < 4; row++)
                    for (int col = 0; col < 4; col++)
                        rowReport.maxMatrixError = Mathf.Max(rowReport.maxMatrixError,
                            Mathf.Abs(actual[row, col] - expected[row, col]));
                var vertices = mesh.vertices;
                double sum = 0;
                foreach (var vertex in vertices)
                {
                    float error = Vector3.Distance(actual.MultiplyPoint3x4(vertex),
                        expected.MultiplyPoint3x4(vertex));
                    rowReport.maxWorldPositionError = Mathf.Max(rowReport.maxWorldPositionError, error);
                    sum += error;
                }
                rowReport.meanWorldPositionError = (float)(sum / vertices.Length);
                overall = Mathf.Max(overall, rowReport.maxWorldPositionError);
                report.events[i] = rowReport;
            }
            const string path = "F:/KianaStudioElectron/docs/frame38112-unity-pose-audit.json";
            File.WriteAllText(path, JsonUtility.ToJson(report, true));
            return "Audited " + report.events.Length + " live meshes; max world-position error " +
                overall.ToString("G9") + "; " + path;
        }

        // Source RT is stored inverted. Rotate clip X and Y for an upright,
        // source-matched preview without modifying the captured pose or scene.
        [MenuItem("Kiana/Capture Upright RDC Pose Preview")]
        public static string CaptureUpright()
        {
            var source = Camera.main;
            if (source == null) throw new Exception("Missing RDC camera");
            var temporary = new GameObject("Temporary upright pose preview");
            var camera = temporary.AddComponent<Camera>();
            var target = new RenderTexture(2880, 1368, 24, RenderTextureFormat.ARGB32);
            Texture2D image = null;
            try
            {
                camera.CopyFrom(source);
                temporary.transform.SetPositionAndRotation(source.transform.position,
                    source.transform.rotation);
                camera.enabled = false;
                var rotate = Matrix4x4.identity;
                rotate.m00 = -1f;
                rotate.m11 = -1f;
                camera.projectionMatrix = rotate * source.projectionMatrix;
                camera.cullingMatrix = rotate * source.cullingMatrix;
                camera.targetTexture = target;
                Shader.SetGlobalFloat("_RdcDepthFlip", 1f);
                Shader.SetGlobalFloat("_RdcFaceFlip", 1f);
                camera.Render();
                RenderTexture.active = target;
                image = new Texture2D(2880, 1368, TextureFormat.RGB24, false);
                image.ReadPixels(new Rect(0, 0, 2880, 1368), 0, 0);
                image.Apply();
                const string path = "F:/KianaStudioElectron/docs/frame38112-unity-pose-upright.png";
                File.WriteAllBytes(path, image.EncodeToPNG());
                return path;
            }
            finally
            {
                Shader.SetGlobalFloat("_RdcDepthFlip", 0f);
                Shader.SetGlobalFloat("_RdcFaceFlip", 0f);
                RenderTexture.active = null;
                UnityEngine.Object.DestroyImmediate(image);
                UnityEngine.Object.DestroyImmediate(target);
                UnityEngine.Object.DestroyImmediate(temporary);
            }
        }

        static int FindIndexCount(int eid)
        {
            var mesh = AssetDatabase.LoadAssetAtPath<Mesh>("Assets/Kiana/Meshes/EID" + eid + ".asset");
            if (mesh == null) throw new Exception("Missing mesh EID " + eid);
            return mesh.triangles.Length;
        }
    }
}
