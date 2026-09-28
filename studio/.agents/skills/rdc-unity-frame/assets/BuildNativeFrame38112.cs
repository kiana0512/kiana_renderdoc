using System;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace KianaFrameReconstruction
{
    public static class BuildNativeFrame38112
    {
        const string Root = "Assets/Kiana";
        const string ScenePath = Root + "/Scenes/Frame38112_NativeReconstruction.unity";

        [Serializable] class BindingManifest { public EventRecord[] events; }
        [Serializable] class EventRecord { public int event_id; public Binding[] fragment_textures; }
        [Serializable] class Binding { public int slot; public int resourceId; public string role; }

        [MenuItem("Kiana/Build Native Frame 38112")]
        public static string Build()
        {
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var root = new GameObject("Frame 38112 — native RDC mesh reconstruction");
            var shader = Shader.Find("Kiana/CapturedAlbedo");
            if (shader == null) throw new Exception("Missing Kiana/CapturedAlbedo shader");
            var text = AssetDatabase.LoadAssetAtPath<TextAsset>(Root + "/Manifest/character-bindings.json");
            if (text == null) throw new Exception("Missing character texture binding manifest");
            var manifest = JsonUtility.FromJson<BindingManifest>(text.text);
            var visibleStage = new GameObject("Pass 5 — character G-buffer color draws");
            visibleStage.transform.SetParent(root.transform, false);
            var laterStage = new GameObject("Later character outline, face detail and transparency draws");
            laterStage.transform.SetParent(root.transform, false);
            var bounds = new Bounds();
            bool any = false;
            int built = 0;
            foreach (var record in manifest.events)
            {
                var eid = record.event_id;
                var mesh = AssetDatabase.LoadAssetAtPath<Mesh>($"{Root}/Meshes/EID{eid}.asset");
                if (mesh == null) throw new Exception("Missing imported mesh EID " + eid);
                var go = new GameObject($"EID {eid} — captured {mesh.vertexCount} vertices");
                bool visible = eid <= 1057;
                go.transform.SetParent(visible ? visibleStage.transform : laterStage.transform, false);
                go.AddComponent<MeshFilter>().sharedMesh = mesh;
                var renderer = go.AddComponent<MeshRenderer>();
                var matPath = $"{Root}/Materials/EID{eid}_Captured.mat";
                var material = AssetDatabase.LoadAssetAtPath<Material>(matPath);
                if (material == null)
                {
                    material = new Material(shader);
                    AssetDatabase.CreateAsset(material, matPath);
                }
                material.shader = shader;
                Texture2D texture = null;
                foreach (var binding in record.fragment_textures)
                {
                    var bound = AssetDatabase.LoadAssetAtPath<Texture2D>($"{Root}/Textures/RID{binding.resourceId}.png");
                    if (bound == null) continue;
                    var property = "_Slot" + binding.slot;
                    if (material.HasProperty(property)) material.SetTexture(property, bound);
                    if (binding.role == "albedo") texture = bound;
                }
                material.mainTexture = texture;
                material.SetColor("_Tint", Color.white);
                EditorUtility.SetDirty(material);
                renderer.sharedMaterial = material;
                if (visible)
                {
                    if (any) bounds.Encapsulate(renderer.bounds); else { bounds = renderer.bounds; any = true; }
                }
                built++;
            }
            laterStage.SetActive(false);
            root.transform.rotation = Quaternion.Euler(0, 0, -90);
            bounds = new Bounds(); any = false;
            foreach (var renderer in visibleStage.GetComponentsInChildren<MeshRenderer>())
            {
                if (any) bounds.Encapsulate(renderer.bounds); else { bounds = renderer.bounds; any = true; }
            }
            var cameraObject = new GameObject("RDC scene camera — native render");
            var camera = cameraObject.AddComponent<Camera>();
            camera.tag = "MainCamera";
            camera.orthographic = true;
            camera.aspect = 16f / 9f;
            camera.orthographicSize = Math.Max(bounds.extents.y, bounds.extents.x * 9f / 16f) * 1.1f;
            camera.nearClipPlane = 0.01f;
            camera.farClipPlane = 100f;
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = new Color(0.035f, 0.035f, 0.055f, 1);
            camera.transform.position = bounds.center - Vector3.right * 5f;
            camera.transform.rotation = Quaternion.LookRotation(bounds.center - camera.transform.position, Vector3.up);
            var stage = new GameObject("Capture stage — further RDC passes pending");
            stage.transform.SetParent(root.transform, false);
            float cameraSize = camera.orthographicSize;
            EditorSceneManager.SaveScene(SceneManager.GetActiveScene(), ScenePath);
            EditorSceneManager.OpenScene(ScenePath);
            AssetDatabase.SaveAssets();
            Selection.activeGameObject = root;
            var sceneView = SceneView.lastActiveSceneView;
            if (sceneView != null) sceneView.Frame(bounds, false);
            return $"Native scene opened: {ScenePath}; {built} mesh draw objects; camera size {cameraSize}; bounds {bounds}";
        }
    }
}
