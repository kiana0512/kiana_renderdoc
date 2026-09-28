using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace Kiana.Frame38112
{
    // Builds a separate, editable stage from UI draw post-VS vertices. It never changes
    // the current G-buffer scene and never uses the final-frame reference as a texture.
    public static class BuildCapturedUIBackground
    {
        [Serializable] private class Manifest { public int sourceWidth; public int sourceHeight; public Draw[] draws; }
        [Serializable] private class Draw { public int eid; public string texture; public Vertex[] vertices; public int[] indices; }
        [Serializable] private class Vertex { public float[] clip; public float[] color; public float[] uv; }

        public static string Build()
        {
            const string root = "Assets/Kiana";
            const string manifestPath = root + "/Manifest/Frame38112_UIBackground_PostVS.json";
            const string scenePath = root + "/Scenes/Frame38112_UIBackground_Draws.unity";
            const string meshDir = root + "/Meshes/UIBackground";
            const string matDir = root + "/Materials/UIBackground";
            const string previewPath = root + "/Validation/UIBackground-EID2237-2307.png";
            var manifest = JsonUtility.FromJson<Manifest>(File.ReadAllText(manifestPath));
            if (manifest == null || manifest.draws == null || manifest.draws.Length != 4)
                throw new InvalidDataException("Expected four captured UI background draws");
            if (!AssetDatabase.IsValidFolder(meshDir)) AssetDatabase.CreateFolder(root + "/Meshes", "UIBackground");
            if (!AssetDatabase.IsValidFolder(matDir)) AssetDatabase.CreateFolder(root + "/Materials", "UIBackground");
            var shader = Shader.Find("Kiana/CapturedUIBackground");
            if (!shader) throw new InvalidOperationException("CapturedUIBackground shader missing");

            string previousScene = SceneManager.GetActiveScene().path;
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            try
            {
                var cameraObject = new GameObject("RDC UI stage camera — 3840 x 2160");
                var camera = cameraObject.AddComponent<Camera>();
                camera.orthographic = true;
                camera.orthographicSize = 1f;
                camera.aspect = (float)manifest.sourceWidth / manifest.sourceHeight;
                camera.clearFlags = CameraClearFlags.SolidColor;
                camera.backgroundColor = Color.black;
                camera.nearClipPlane = 0.01f;
                camera.farClipPlane = 10f;
                cameraObject.transform.position = new Vector3(0, 0, -2);
                cameraObject.transform.rotation = Quaternion.identity;
                camera.depthTextureMode = DepthTextureMode.None;
                var rootObject = new GameObject("Frame 38112 — native RDC UI background draws");
                for (int n = 0; n < manifest.draws.Length; n++)
                {
                    var draw = manifest.draws[n];
                    var texturePath = root + "/Textures/Background/" + draw.texture + ".png";
                    var texture = AssetDatabase.LoadAssetAtPath<Texture2D>(texturePath);
                    if (!texture) throw new FileNotFoundException(texturePath);
                    string meshPath = meshDir + "/EID" + draw.eid + ".asset";
                    var mesh = AssetDatabase.LoadAssetAtPath<Mesh>(meshPath);
                    bool newMesh = !mesh;
                    if (newMesh) mesh = new Mesh();
                    else mesh.Clear();
                    mesh.name = "EID " + draw.eid + " captured quad";
                    var positions = new Vector3[draw.vertices.Length];
                    var uvs = new Vector2[positions.Length];
                    var colors = new Color[positions.Length];
                    for (int i = 0; i < positions.Length; i++)
                    {
                        var v = draw.vertices[i];
                        positions[i] = new Vector3(v.clip[0] / v.clip[3] * camera.aspect,
                            v.clip[1] / v.clip[3], n * -0.001f);
                        uvs[i] = new Vector2(v.uv[0], v.uv[1]);
                        colors[i] = new Color(v.color[0], v.color[1], v.color[2], v.color[3]);
                    }
                    mesh.vertices = positions;
                    mesh.uv = uvs;
                    mesh.colors = colors;
                    mesh.triangles = draw.indices;
                    mesh.RecalculateBounds();
                    if (newMesh) AssetDatabase.CreateAsset(mesh, meshPath);
                    else EditorUtility.SetDirty(mesh);
                    string materialPath = matDir + "/EID" + draw.eid + ".mat";
                    var material = AssetDatabase.LoadAssetAtPath<Material>(materialPath);
                    if (!material) { material = new Material(shader); AssetDatabase.CreateAsset(material, materialPath); }
                    material.shader = shader;
                    material.mainTexture = texture;
                    material.renderQueue = 3000 + n;
                    EditorUtility.SetDirty(material);
                    var go = new GameObject("EID " + draw.eid + " — " + draw.texture);
                    go.transform.SetParent(rootObject.transform, false);
                    go.AddComponent<MeshFilter>().sharedMesh = mesh;
                    go.AddComponent<MeshRenderer>().sharedMaterial = material;
                }
                EditorSceneManager.SaveScene(scene, scenePath);
                var rt = new RenderTexture(1920, 1080, 24, RenderTextureFormat.ARGB32);
                var oldTarget = camera.targetTexture;
                var oldActive = RenderTexture.active;
                try
                {
                    camera.targetTexture = rt;
                    camera.Render();
                    RenderTexture.active = rt;
                    var image = new Texture2D(1920, 1080, TextureFormat.RGBA32, false);
                    image.ReadPixels(new Rect(0, 0, 1920, 1080), 0, 0);
                    image.Apply();
                    File.WriteAllBytes(previewPath, image.EncodeToPNG());
                    UnityEngine.Object.DestroyImmediate(image);
                }
                finally { camera.targetTexture = oldTarget; RenderTexture.active = oldActive; UnityEngine.Object.DestroyImmediate(rt); }
                AssetDatabase.SaveAssets();
                AssetDatabase.Refresh();
                return scenePath + " preview=" + previewPath;
            }
            finally
            {
                if (!string.IsNullOrEmpty(previousScene)) EditorSceneManager.OpenScene(previousScene);
            }
        }
    }
}
