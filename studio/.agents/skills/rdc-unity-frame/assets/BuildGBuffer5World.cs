using System;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace KianaFrameReconstruction
{
    public static class BuildGBuffer5World
    {
        const string Root = "Assets/Kiana";
        const string ScenePath = Root + "/Scenes/Frame38112_GBuffer5_World.unity";
        // Captured raster states are inventoried, but this mapping distorts the
        // current Unity Scene view. Keep the visually verified baseline active.
        const bool ApplyCapturedRasterState = false;
        [Serializable] class BindingManifest { public EventBinding[] events; }
        [Serializable] class EventBinding
        {
            public int eventId;
            public int indices;
            public int albedoResourceId;
            public int fragmentShader;
            public TextureBinding[] textures;
        }
        [Serializable] class TextureBinding
        {
            public int slot;
            public int resourceId;
            public string stage;
            public string role;
        }
        [Serializable] class TransformManifest
        {
            public float[] cameraPosition;
            public float[] viewProjection;
            public EventTransform[] events;
        }
        [Serializable] class StateManifest { public EventState[] events; }
        [Serializable] class EventState
        {
            public int eventId;
            public int unityCullMode;
            public bool depthWrites;
        }
        [Serializable] class EventTransform
        {
            public int eventId;
            public float[] localToWorld;
            public float firstVertexClipMaxError;
        }

        [MenuItem("Kiana/Build G-buffer 5 3D World")]
        public static string Build()
        {
            var bindingSource = AssetDatabase.LoadAssetAtPath<TextAsset>(Root + "/Manifest/gbuffer5-bindings.json");
            var transformSource = AssetDatabase.LoadAssetAtPath<TextAsset>(Root + "/Manifest/gbuffer5-transforms.json");
            var stateSource = AssetDatabase.LoadAssetAtPath<TextAsset>(Root + "/Manifest/gbuffer5-states.json");
            if (bindingSource == null || transformSource == null || stateSource == null)
                throw new Exception("Missing G-buffer manifests");
            var bindings = JsonUtility.FromJson<BindingManifest>(bindingSource.text);
            var transforms = JsonUtility.FromJson<TransformManifest>(transformSource.text);
            var states = JsonUtility.FromJson<StateManifest>(stateSource.text);
            if (bindings.events.Length != 26 || transforms.events.Length != 26 || states.events.Length != 26)
                throw new Exception("Expected exactly 26 pass-5 draws");
            var shader = Shader.Find("Kiana/CapturedAlbedo");
            if (shader == null) throw new Exception("Missing Kiana/CapturedAlbedo shader");

            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var skyShader = Shader.Find("Kiana/GBufferBlackSkybox");
            if (skyShader == null) throw new Exception("Missing Kiana/GBufferBlackSkybox shader");
            const string skyPath = Root + "/Materials/GBuffer5_BlackSkybox.mat";
            var blackSkybox = AssetDatabase.LoadAssetAtPath<Material>(skyPath);
            if (blackSkybox == null)
            {
                blackSkybox = new Material(skyShader) { name = "GBuffer5_BlackSkybox" };
                AssetDatabase.CreateAsset(blackSkybox, skyPath);
            }
            else blackSkybox.shader = skyShader;
            RenderSettings.skybox = blackSkybox;
            RenderSettings.fog = false;
            var root = new GameObject("Frame 38112 — 3D G-buffer reconstruction");
            var baseDraws = new GameObject("Base G-buffer meshes — IA plus RDC per-draw matrices");
            baseDraws.transform.SetParent(root.transform, false);
            var laterDraws = new GameObject("Later G-buffer draws — eye active, variants pending");
            laterDraws.transform.SetParent(root.transform, false);
            int totalIndices = 0;
            int drawOrder = 0;
            Bounds worldBounds = new Bounds();
            bool haveBounds = false;
            foreach (var draw in bindings.events)
            {
                EventTransform record = null;
                foreach (var candidate in transforms.events)
                    if (candidate.eventId == draw.eventId) { record = candidate; break; }
                if (record == null) throw new Exception("Missing transform EID " + draw.eventId);
                EventState renderState = null;
                foreach (var candidate in states.events)
                    if (candidate.eventId == draw.eventId) { renderState = candidate; break; }
                if (renderState == null) throw new Exception("Missing state EID " + draw.eventId);
                var mesh = AssetDatabase.LoadAssetAtPath<Mesh>($"{Root}/Meshes/EID{draw.eventId}.asset");
                if (mesh == null) throw new Exception("Missing 3D IA mesh EID " + draw.eventId);
                if (mesh.triangles.Length != draw.indices) throw new Exception("Index count mismatch EID " + draw.eventId);
                bool basePass = draw.eventId <= 1035;
                var go = new GameObject($"EID {draw.eventId} — 3D mesh, {draw.indices} indices");
                go.transform.SetParent(basePass ? baseDraws.transform : laterDraws.transform, false);
                var localToWorld = MatrixFromRows(record.localToWorld);
                var pos = localToWorld.GetColumn(3);
                var forwardColumn = localToWorld.GetColumn(2);
                var upColumn = localToWorld.GetColumn(1);
                var forward = new Vector3(forwardColumn.x, forwardColumn.y, forwardColumn.z);
                var up = new Vector3(upColumn.x, upColumn.y, upColumn.z);
                go.transform.SetPositionAndRotation(new Vector3(pos.x, pos.y, pos.z),
                                                     Quaternion.LookRotation(forward, up));
                go.AddComponent<MeshFilter>().sharedMesh = mesh;
                var renderer = go.AddComponent<MeshRenderer>();
                var material = new Material(shader) { name = $"EID{draw.eventId}_GBuffer3D" };
                foreach (var texture in draw.textures)
                {
                    var bound = LoadCapturedTexture(texture.resourceId);
                    if (bound == null) throw new Exception("Missing bound texture RID " + texture.resourceId);
                    var property = "_Slot" + texture.slot;
                    if (material.HasProperty(property)) material.SetTexture(property, bound);
                    if (texture.resourceId == 42021 && material.HasProperty("_Slot7Array"))
                    {
                        var array = AssetDatabase.LoadAssetAtPath<Texture2DArray>(
                            $"{Root}/Textures/Arrays/RID42021.asset");
                        if (array == null) throw new Exception("Missing full RID42021 texture array");
                        material.SetTexture("_Slot7Array", array);
                    }
                    if (texture.resourceId == draw.albedoResourceId) material.mainTexture = bound;
                }
                var path = $"{Root}/Materials/EID{draw.eventId}_GBuffer3D.mat";
                var existing = AssetDatabase.LoadAssetAtPath<Material>(path);
                if (existing != null) AssetDatabase.DeleteAsset(path);
                AssetDatabase.CreateAsset(material, path);
                material.SetFloat("_Cull", ApplyCapturedRasterState ? renderState.unityCullMode : 0f);
                material.SetFloat("_ZWrite", ApplyCapturedRasterState && !renderState.depthWrites ? 0f : 1f);
                material.SetFloat("_ZTest", 4f);
                material.SetFloat("_RdcPixelShader", draw.fragmentShader);
                material.SetFloat("_RdcFamilyEnabled", draw.fragmentShader == 31475 ||
                    draw.fragmentShader == 42681 || draw.fragmentShader == 33678 ? 1f : 0f);
                material.renderQueue = 2000 + drawOrder++;
                EditorUtility.SetDirty(material);
                renderer.sharedMaterial = material;
                if (!basePass && draw.eventId != 1273) go.SetActive(false);
                if (basePass)
                {
                    if (haveBounds) worldBounds.Encapsulate(renderer.bounds);
                    else { worldBounds = renderer.bounds; haveBounds = true; }
                }
                totalIndices += draw.indices;
            }
            if (totalIndices != 663852) throw new Exception("Pass-5 index coverage mismatch");
            foreach (var state in states.events)
            {
                var persisted = AssetDatabase.LoadAssetAtPath<Material>(
                    $"{Root}/Materials/EID{state.eventId}_GBuffer3D.mat");
                if (persisted == null) throw new Exception("Material missing EID " + state.eventId);
                persisted.SetFloat("_Cull", ApplyCapturedRasterState ? state.unityCullMode : 0f);
                persisted.SetFloat("_ZWrite", ApplyCapturedRasterState && !state.depthWrites ? 0f : 1f);
                EditorUtility.SetDirty(persisted);
            }
            AssetDatabase.SaveAssets();
            ApplyCapturedMaterialFamilies.Apply();
            var cameraObject = new GameObject("RDC camera — captured view and projection");
            cameraObject.transform.SetParent(root.transform, false);
            var camera = cameraObject.AddComponent<Camera>();
            camera.tag = "MainCamera";
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = Color.black;
            camera.nearClipPlane = 0.01f;
            camera.farClipPlane = 100f;
            camera.aspect = 2880f / 1368f;
            var vp = MatrixFromRows(transforms.viewProjection);
            var forwardDirection = new Vector3(vp.m30, vp.m31, vp.m32).normalized;
            var upProjection = new Vector3(vp.m10, vp.m11, vp.m12);
            var upDirection = (upProjection - Vector3.Dot(upProjection, forwardDirection) * forwardDirection).normalized;
            cameraObject.transform.SetPositionAndRotation(
                new Vector3(transforms.cameraPosition[0], transforms.cameraPosition[1], transforms.cameraPosition[2]),
                Quaternion.LookRotation(forwardDirection, upDirection));
            camera.projectionMatrix = vp * camera.worldToCameraMatrix.inverse;
            camera.cullingMatrix = vp;
            var capturedCamera = cameraObject.AddComponent<CapturedCameraMatrix>();
            capturedCamera.viewProjection = transforms.viewProjection;
            capturedCamera.Apply();

            ApplyEyeHairLayer.ApplyAll();

            EditorSceneManager.SaveScene(SceneManager.GetActiveScene(), ScenePath);
            EditorSceneManager.OpenScene(ScenePath);
            Camera.main.GetComponent<CapturedCameraMatrix>().Apply();
            AssetDatabase.SaveAssets();
            Selection.activeGameObject = root;
            if (SceneView.lastActiveSceneView != null && haveBounds)
                SceneView.lastActiveSceneView.Frame(worldBounds, false);
            return $"Opened native 3D G-buffer scene: 26 draws, {totalIndices} indices, world bounds {worldBounds}";
        }

        public static string InspectState(int eventId)
        {
            var source = AssetDatabase.LoadAssetAtPath<TextAsset>(Root + "/Manifest/gbuffer5-states.json");
            var states = JsonUtility.FromJson<StateManifest>(source.text);
            foreach (var state in states.events)
                if (state.eventId == eventId)
                    return $"EID {eventId}: Unity Cull {state.unityCullMode}, depth writes {state.depthWrites}";
            return "State missing";
        }

        public static string ValidateBaseColorBindings()
        {
            var source = AssetDatabase.LoadAssetAtPath<TextAsset>(Root + "/Manifest/gbuffer5-bindings.json");
            var bindings = JsonUtility.FromJson<BindingManifest>(source.text);
            int mapped = 0, procedural = 0;
            foreach (var draw in bindings.events)
            {
                var material = AssetDatabase.LoadAssetAtPath<Material>(
                    $"{Root}/Materials/EID{draw.eventId}_GBuffer3D.mat");
                if (material == null) throw new Exception("Missing material EID " + draw.eventId);
                if (draw.albedoResourceId == 0) { procedural++; continue; }
                var expected = AssetDatabase.LoadAssetAtPath<Texture2D>(
                    $"{Root}/Textures/RID{draw.albedoResourceId}.png");
                if (expected == null || material.mainTexture != expected)
                    throw new Exception("Base color mismatch EID " + draw.eventId);
                mapped++;
            }
            return $"Base color: {mapped}/26 draws mapped to RDC PNGs; {procedural} draws have no albedo binding";
        }

        [MenuItem("Kiana/Upgrade G-buffer Float Texture Bindings")]
        public static string UpgradeFloatTextureBindings()
        {
            var source = AssetDatabase.LoadAssetAtPath<TextAsset>(Root + "/Manifest/gbuffer5-bindings.json");
            var bindings = JsonUtility.FromJson<BindingManifest>(source.text);
            int replacements = 0;
            foreach (var draw in bindings.events)
            {
                var material = AssetDatabase.LoadAssetAtPath<Material>(
                    $"{Root}/Materials/EID{draw.eventId}_GBuffer3D.mat");
                if (material == null) throw new Exception("Missing material EID " + draw.eventId);
                foreach (var texture in draw.textures)
                {
                    // EID992 face-lightmap PNG reproduces the captured
                    // PS31476 nose control values. Keep that validated
                    // binding when upgrading the other float resources.
                    if (draw.eventId == 992 && texture.slot == 4) continue;
                    var exrPath = $"{Root}/Textures/HDR/RID{texture.resourceId}.exr";
                    var hdr = AssetDatabase.LoadAssetAtPath<Texture2D>(exrPath);
                    if (hdr == null) continue;
                    var property = "_Slot" + texture.slot;
                    if (!material.HasProperty(property)) continue;
                    material.SetTexture(property, hdr);
                    EditorUtility.SetDirty(material);
                    replacements++;
                }
            }
            AssetDatabase.SaveAssets();
            return $"Upgraded {replacements} G-buffer material slots to source-precision EXR";
        }

        [MenuItem("Kiana/Configure G-buffer Float Texture Importers")]
        public static string ConfigureFloatTextureImporters()
        {
            var resourceIds = new[] { 25406, 42862, 42880, 42887, 42888, 42967, 42968 };
            int configured = 0;
            foreach (var resourceId in resourceIds)
            {
                var path = $"{Root}/Textures/HDR/RID{resourceId}.exr";
                var importer = AssetImporter.GetAtPath(path) as TextureImporter;
                if (importer == null) throw new Exception("Missing float texture importer: " + path);
                importer.sRGBTexture = false;
                importer.textureCompression = TextureImporterCompression.Uncompressed;
                importer.SaveAndReimport();
                configured++;
            }
            return $"Configured {configured} float EXRs as linear, uncompressed textures";
        }

        [MenuItem("Kiana/Bind G-buffer Texture Array RID42021")]
        public static string BindTextureArray()
        {
            var array = AssetDatabase.LoadAssetAtPath<Texture2DArray>(
                $"{Root}/Textures/Arrays/RID42021.asset");
            if (array == null || array.depth != 16)
                throw new Exception("Expected full 16-slice RID42021 texture array");
            var source = AssetDatabase.LoadAssetAtPath<TextAsset>(Root + "/Manifest/gbuffer5-bindings.json");
            var bindings = JsonUtility.FromJson<BindingManifest>(source.text);
            int count = 0;
            foreach (var draw in bindings.events)
            {
                bool usesArray = false;
                foreach (var texture in draw.textures)
                    if (texture.resourceId == 42021 && texture.slot == 7) usesArray = true;
                if (!usesArray) continue;
                var material = AssetDatabase.LoadAssetAtPath<Material>(
                    $"{Root}/Materials/EID{draw.eventId}_GBuffer3D.mat");
                if (material == null || !material.HasProperty("_Slot7Array"))
                    throw new Exception("Array-capable material missing EID " + draw.eventId);
                material.SetTexture("_Slot7Array", array);
                EditorUtility.SetDirty(material);
                count++;
            }
            AssetDatabase.SaveAssets();
            return $"Bound full RID42021 array to {count} G-buffer draw materials";
        }

        static Texture2D LoadCapturedTexture(int resourceId)
        {
            var exr = AssetDatabase.LoadAssetAtPath<Texture2D>($"{Root}/Textures/HDR/RID{resourceId}.exr");
            return exr != null ? exr : AssetDatabase.LoadAssetAtPath<Texture2D>($"{Root}/Textures/RID{resourceId}.png");
        }

        static Matrix4x4 MatrixFromRows(float[] v)
        {
            if (v == null || v.Length != 16) throw new Exception("Expected row-major 4x4 matrix");
            var matrix = new Matrix4x4();
            for (int row = 0; row < 4; row++)
                for (int col = 0; col < 4; col++)
                    matrix[row, col] = v[row * 4 + col];
            return matrix;
        }
    }
}
