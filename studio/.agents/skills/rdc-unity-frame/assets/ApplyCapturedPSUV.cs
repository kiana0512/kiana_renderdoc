using System;
using System.IO;
using UnityEditor;
using UnityEngine;

namespace KianaFrameReconstruction
{
    // Restore the exact pixel-shader v0.zw stream when FBX UV2 differs from VSOut.
    // Updates the existing Mesh asset, so scene MeshFilter references stay intact.
    public static class ApplyCapturedPSUV
    {
        [MenuItem("Kiana/Apply Captured PS UV Streams")]
        public static string ApplyAll()
        {
            const string source = "Assets/Kiana/MeshData/PSUV";
            if (!Directory.Exists(source)) return "No captured PS UV overrides";
            int updated = 0;
            foreach (var file in Directory.GetFiles(source, "EID*.bytes"))
            {
                string id = Path.GetFileNameWithoutExtension(file);
                Mesh mesh = AssetDatabase.LoadAssetAtPath<Mesh>("Assets/Kiana/Meshes/" + id + ".asset");
                if (mesh == null) throw new InvalidDataException("Missing mesh " + id);
                byte[] bytes = File.ReadAllBytes(file);
                if (bytes.Length != mesh.vertexCount * 8)
                    throw new InvalidDataException("UV stream size mismatch for " + id);
                var uv = new Vector2[mesh.vertexCount];
                using (var reader = new BinaryReader(new MemoryStream(bytes)))
                    for (int i = 0; i < uv.Length; i++)
                        uv[i] = new Vector2(reader.ReadSingle(), reader.ReadSingle());
                mesh.uv3 = uv;
                EditorUtility.SetDirty(mesh);
                updated++;
            }
            AssetDatabase.SaveAssets();
            return "Restored PS v0.zw on " + updated + " Mesh assets";
        }
    }
}
