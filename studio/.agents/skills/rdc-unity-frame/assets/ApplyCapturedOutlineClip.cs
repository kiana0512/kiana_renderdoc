using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEngine;

namespace KianaFrameReconstruction
{
    // Frame-specific post-VS reference. UV5 is read only by the captured
    // camera diagnostic branch; the Mesh vertices remain editable 3D geometry.
    public static class ApplyCapturedOutlineClip
    {
        [MenuItem("Kiana/Apply Captured Outline VS Clip")]
        public static string ApplyAll()
        {
            const string source = "Assets/Kiana/MeshData/OutlineClip";
            int count = 0;
            foreach (var file in Directory.GetFiles(source, "EID*.bytes"))
            {
                string id = Path.GetFileNameWithoutExtension(file);
                var mesh = AssetDatabase.LoadAssetAtPath<Mesh>(
                    "Assets/Kiana/Meshes/" + id + ".asset");
                if (mesh == null) throw new InvalidDataException("Missing " + id);
                byte[] bytes = File.ReadAllBytes(file);
                if (bytes.Length != mesh.vertexCount * 16)
                    throw new InvalidDataException("Clip stream size mismatch " + id);
                var clip = new List<Vector4>(mesh.vertexCount);
                using (var reader = new BinaryReader(new MemoryStream(bytes)))
                    for (int i = 0; i < mesh.vertexCount; i++)
                        clip.Add(new Vector4(reader.ReadSingle(), reader.ReadSingle(),
                                             reader.ReadSingle(), reader.ReadSingle()));
                mesh.SetUVs(4, clip);
                EditorUtility.SetDirty(mesh);
                count++;
            }
            AssetDatabase.SaveAssets();
            return "Restored source VS clip into UV5 on " + count + " 3D Mesh assets";
        }
    }
}
