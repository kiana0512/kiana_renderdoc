using System;
using System.IO;
using UnityEditor;
using UnityEngine;

namespace KianaFrameReconstruction
{
    // Restore the RDC IA index sequence on the existing Unity Mesh asset.
    // FBX conversion preserves triangles but can reorder overlapping layers.
    public static class ApplyCapturedPSIndices
    {
        private const string Source = "Assets/Kiana/MeshData/PSIndices";

        [MenuItem("Kiana/Apply Captured RDC Index Order")]
        public static string ApplyAll()
        {
            if (!Directory.Exists(Source)) return "No captured index overrides";
            int updated = 0;
            foreach (var file in Directory.GetFiles(Source, "EID*.bytes"))
            {
                ApplyFile(file);
                updated++;
            }
            AssetDatabase.SaveAssets();
            return "Restored RDC index order on " + updated + " Mesh assets";
        }

        public static string ApplyOne(int eid)
        {
            ApplyFile(Source + "/EID" + eid + ".bytes");
            AssetDatabase.SaveAssets();
            return "Restored RDC index order on EID " + eid;
        }

        private static void ApplyFile(string file)
        {
            string id = Path.GetFileNameWithoutExtension(file);
            Mesh mesh = AssetDatabase.LoadAssetAtPath<Mesh>("Assets/Kiana/Meshes/" + id + ".asset");
            if (mesh == null) throw new InvalidDataException("Missing mesh " + id);
            byte[] bytes = File.ReadAllBytes(file);
            if (bytes.Length != mesh.triangles.Length * 4)
                throw new InvalidDataException("Index stream size mismatch for " + id);
            int[] indices = new int[bytes.Length / 4];
            Buffer.BlockCopy(bytes, 0, indices, 0, bytes.Length);
            foreach (int index in indices)
                if (index < 0 || index >= mesh.vertexCount)
                    throw new InvalidDataException("Out of range index on " + id);
            mesh.triangles = indices;
            EditorUtility.SetDirty(mesh);
        }
    }
}
