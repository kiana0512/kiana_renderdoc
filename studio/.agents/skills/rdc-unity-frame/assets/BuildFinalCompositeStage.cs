using System;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace Kiana.Frame38112
{
    // RDC intermediate images isolate the final-composite mapping. They are
    // temporary stage inputs, never a substitute for the native 3D and UI passes.
    public static class BuildFinalCompositeStage
    {
        const string Root = "Assets/Kiana";
        const string ScenePath = Root + "/Scenes/Frame38112_FinalComposite_Stage2475.unity";
        const string NativeScenePath = Root + "/Scenes/Frame38112_GBuffer5_World.unity";
        const string StageDir = Root + "/StageReferences";
        const string MeshDir = Root + "/Meshes/FinalComposite";
        const string MatDir = Root + "/Materials/FinalComposite";

        [Serializable] class Manifest
        {
            public int sourceWidth, sourceHeight, eventId, inputResourceId;
            public Vertex[] vertices;
            public int[] indices;
        }
        [Serializable] class Vertex { public float[] clip, color, uv; }

        static void Folder(string parent, string name)
        {
            if (!AssetDatabase.IsValidFolder(parent + "/" + name))
                AssetDatabase.CreateFolder(parent, name);
        }

        static Texture2D StageTexture(string name)
        {
            string path = StageDir + "/" + name + ".png";
            var importer = AssetImporter.GetAtPath(path) as TextureImporter;
            if (importer == null) throw new FileNotFoundException(path);
            importer.textureType = TextureImporterType.Default;
            importer.sRGBTexture = true;
            importer.alphaSource = TextureImporterAlphaSource.FromInput;
            importer.alphaIsTransparency = false;
            importer.mipmapEnabled = false;
            importer.textureCompression = TextureImporterCompression.Uncompressed;
            importer.maxTextureSize = 4096;
            importer.filterMode = FilterMode.Bilinear;
            importer.wrapMode = TextureWrapMode.Clamp;
            importer.SaveAndReimport();
            return AssetDatabase.LoadAssetAtPath<Texture2D>(path);
        }

        static Mesh SaveMesh(string name, Vector3[] positions, Vector2[] uv, Color[] colors, int[] triangles)
        {
            string path = MeshDir + "/" + name + ".asset";
            var mesh = AssetDatabase.LoadAssetAtPath<Mesh>(path);
            if (!mesh) mesh = new Mesh(); else mesh.Clear();
            mesh.name = name;
            mesh.vertices = positions;
            mesh.uv = uv;
            if (colors != null) mesh.colors = colors;
            mesh.triangles = triangles;
            mesh.RecalculateBounds();
            if (!AssetDatabase.Contains(mesh)) AssetDatabase.CreateAsset(mesh, path);
            else EditorUtility.SetDirty(mesh);
            return mesh;
        }

        static Material SaveMaterial(string name, Shader shader, Texture texture, int queue)
        {
            string path = MatDir + "/" + name + ".mat";
            var material = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (!material) { material = new Material(shader); AssetDatabase.CreateAsset(material, path); }
            material.shader = shader;
            material.mainTexture = texture;
            material.renderQueue = queue;
            EditorUtility.SetDirty(material);
            return material;
        }

        static GameObject ImportNativeCharacter(Scene destination)
        {
            var source = EditorSceneManager.OpenScene(NativeScenePath, OpenSceneMode.Additive);
            var roots = source.GetRootGameObjects();
            if (roots.Length != 1 || roots[0].GetComponentsInChildren<Renderer>(true).Length < 26)
                throw new InvalidDataException("Captured G-buffer character scene is incomplete");

            var characterRoot = roots[0];
            SceneManager.MoveGameObjectToScene(characterRoot, destination);
            characterRoot.name = "Native 3D character — RDC mesh draws and captured camera";
            // Keep the meshes editable and visible in Scene view. The temporary
            // full-frame composite remains the Game-camera input until the
            // captured postprocess is driven from this native camera.
            foreach (var tr in characterRoot.GetComponentsInChildren<Transform>(true))
                tr.gameObject.layer = 31;
            foreach (var nativeCamera in characterRoot.GetComponentsInChildren<Camera>(true))
            {
                nativeCamera.enabled = false;
                nativeCamera.tag = "Untagged";
            }
            EditorSceneManager.CloseScene(source, true);
            return characterRoot;
        }

        [MenuItem("Kiana/Build Frame 38112 Final Composite Stage 2475")]
        public static string Build()
        {
            Folder(Root, "StageReferences");
            Folder(Root + "/Meshes", "FinalComposite");
            Folder(Root + "/Materials", "FinalComposite");
            var manifest = JsonUtility.FromJson<Manifest>(File.ReadAllText(
                Root + "/Manifest/Frame38112_Stage2475.json"));
            if (manifest == null || manifest.eventId != 2475 || manifest.vertices.Length != 4)
                throw new InvalidDataException("Missing EID2475 captured quad");
            var background = StageTexture("EID2456-RID1181-BG-TEMP");
            if (!Shader.Find("Kiana/NativeFinalStage"))
                throw new InvalidOperationException("Native final-stage shader missing");

            var stageScene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var cameraObject = new GameObject("RDC final output camera — 3840 x 2160");
            var camera = cameraObject.AddComponent<Camera>();
            camera.tag = "MainCamera";
            camera.orthographic = true;
            camera.orthographicSize = 1f;
            camera.aspect = (float)manifest.sourceWidth / manifest.sourceHeight;
            camera.nearClipPlane = .01f;
            camera.farClipPlane = 10f;
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = Color.black;
            camera.allowHDR = false;
            camera.allowMSAA = false;
            camera.cullingMask = 0;
            camera.transform.position = new Vector3(0, 0, -2);
            PlayerSettings.colorSpace = ColorSpace.Gamma;

            var nativeCharacter = ImportNativeCharacter(stageScene);
            var source = cameraObject.AddComponent<NativeCharacterCompositeSource>();
            source.capturedCamera = nativeCharacter.GetComponentInChildren<Camera>(true);
            source.backgroundStageReference = background;
            source.renderNativeCharacter = true;
            source.characterScreenExtent = new Vector2(
                (manifest.vertices[0].clip[0] / manifest.vertices[0].clip[3] + 1f) * .5f,
                (manifest.vertices[2].clip[0] / manifest.vertices[2].clip[3] + 1f) * .5f);

            EditorSceneManager.SaveScene(stageScene, ScenePath);
            AssetDatabase.SaveAssets();
            Selection.activeGameObject = nativeCharacter;
            var sceneView = SceneView.lastActiveSceneView;
            if (sceneView != null)
            {
                Bounds bounds = default;
                bool hasBounds = false;
                foreach (var renderer in nativeCharacter.GetComponentsInChildren<Renderer>(true))
                {
                    if (!hasBounds) { bounds = renderer.bounds; hasBounds = true; }
                    else bounds.Encapsulate(renderer.bounds);
                }
                if (hasBounds) sceneView.Frame(bounds, false);
            }
            return ScenePath;
        }

        [MenuItem("Kiana/Capture Frame 38112 Final Composite Stage 2475")]
        public static string Capture()
        {
            var camera = Camera.main;
            if (!camera) throw new InvalidOperationException("Open final composite stage first");
            int width = 3840, height = 2160;
            var rt = new RenderTexture(width, height, 24, RenderTextureFormat.ARGB32);
            var oldTarget = camera.targetTexture;
            var oldActive = RenderTexture.active;
            try
            {
                camera.targetTexture = rt;
                camera.Render();
                RenderTexture.active = rt;
                var image = new Texture2D(width, height, TextureFormat.RGBA32, false);
                image.ReadPixels(new Rect(0, 0, width, height), 0, 0);
                image.Apply();
                string path = Root + "/Validation/FinalComposite-Stage2475-TEMP.png";
                File.WriteAllBytes(path, image.EncodeToPNG());
                UnityEngine.Object.DestroyImmediate(image);
                return path;
            }
            finally
            {
                camera.targetTexture = oldTarget;
                RenderTexture.active = oldActive;
                UnityEngine.Object.DestroyImmediate(rt);
            }
        }
    }
}
