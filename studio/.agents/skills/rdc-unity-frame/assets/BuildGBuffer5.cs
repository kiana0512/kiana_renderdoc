using System;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace KianaFrameReconstruction
{
    public static class BuildGBuffer5
    {
        const string Root = "Assets/Kiana";
        const string ScenePath = Root + "/Scenes/Frame38112_GBuffer5_VSOut.unity";

        [Serializable] class Manifest { public int frame; public int pass; public int[] size; public Event[] events; }
        [Serializable] class Event
        {
            public int eventId;
            public int indices;
            public int albedoResourceId;
            public Binding[] textures;
        }
        [Serializable] class Binding { public int slot; public int resourceId; public string stage; public string role; }

        [MenuItem("Kiana/Build G-buffer 5 VSOut")]
        public static string Build()
        {
            var source = AssetDatabase.LoadAssetAtPath<TextAsset>(Root + "/Manifest/gbuffer5-bindings.json");
            if (source == null) throw new Exception("Missing G-buffer manifest");
            var manifest = JsonUtility.FromJson<Manifest>(source.text);
            if (manifest.frame != 38112 || manifest.pass != 5 || manifest.events.Length != 26)
                throw new Exception("Manifest does not describe the expected frame-38112 G-buffer pass");
            var shader = Shader.Find("Kiana/PostVSAlbedo");
            if (shader == null) throw new Exception("Missing Kiana/PostVSAlbedo shader");
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var root = new GameObject("Frame 38112 — G-buffer 5 captured VSOut geometry");
            var draws = new GameObject("26 RDC draw events — 663852 indices");
            draws.transform.SetParent(root.transform, false);
            int built = 0;
            int indices = 0;
            foreach (var record in manifest.events)
            {
                var mesh = AssetDatabase.LoadAssetAtPath<Mesh>($"{Root}/Meshes/PostVS/EID{record.eventId}.asset");
                if (mesh == null) throw new Exception("Missing VSOut mesh EID " + record.eventId);
                if (mesh.triangles.Length != record.indices)
                    throw new Exception("Triangle index mismatch EID " + record.eventId);
                var go = new GameObject($"EID {record.eventId} — VSOut {record.indices} indices");
                go.transform.SetParent(draws.transform, false);
                go.AddComponent<MeshFilter>().sharedMesh = mesh;
                var renderer = go.AddComponent<MeshRenderer>();
                var material = new Material(shader) { name = $"EID{record.eventId}_PostVSAlbedo" };
                if (record.albedoResourceId != 0)
                {
                    var diffuse = AssetDatabase.LoadAssetAtPath<Texture2D>(
                        $"{Root}/Textures/RID{record.albedoResourceId}.png");
                    if (diffuse == null) throw new Exception("Missing diffuse EID " + record.eventId);
                    material.mainTexture = diffuse;
                }
                var matPath = $"{Root}/Materials/EID{record.eventId}_PostVSAlbedo.mat";
                var existing = AssetDatabase.LoadAssetAtPath<Material>(matPath);
                if (existing != null) AssetDatabase.DeleteAsset(matPath);
                AssetDatabase.CreateAsset(material, matPath);
                renderer.sharedMaterial = material;
                built++;
                indices += record.indices;
            }
            if (built != 26 || indices != 663852) throw new Exception("G-buffer draw coverage mismatch");
            var cameraObject = new GameObject("G-buffer reference camera — 2880x1368 clip plane");
            cameraObject.transform.SetParent(root.transform, false);
            var camera = cameraObject.AddComponent<Camera>();
            camera.tag = "MainCamera";
            camera.orthographic = true;
            camera.orthographicSize = 1f;
            camera.aspect = 2880f / 1368f;
            camera.nearClipPlane = 0.01f;
            camera.farClipPlane = 10f;
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = Color.black;
            cameraObject.transform.position = new Vector3(0, 0, -2);
            cameraObject.transform.rotation = Quaternion.identity;
            EditorSceneManager.SaveScene(SceneManager.GetActiveScene(), ScenePath);
            EditorSceneManager.OpenScene(ScenePath);
            AssetDatabase.SaveAssets();
            Selection.activeGameObject = root;
            return $"Opened {ScenePath}: {built} actual pass-5 draws, {indices} indices";
        }
    }
}
