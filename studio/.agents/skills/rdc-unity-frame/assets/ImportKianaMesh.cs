using System;
using System.IO;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace KianaFrameReconstruction
{
    // Import mesh streams converted from Kiana's captured current-pose FBX.
    public static class ImportKianaMesh
    {
        [MenuItem("Kiana/Import Captured Meshes")]
        public static string ImportAll()
        {
            string result = ImportFolder("Assets/Kiana/MeshData", "Assets/Kiana/Meshes");
            return result + "; " + ApplyCapturedPSUV.ApplyAll() + "; " + ApplyCapturedPSIndices.ApplyAll();
        }

        [MenuItem("Kiana/Import G-buffer VSOut Meshes")]
        public static string ImportPostVS()
        {
            return ImportFolder("Assets/Kiana/MeshData/PostVS", "Assets/Kiana/Meshes/PostVS");
        }

        private static string ImportFolder(string sourceFolder, string destinationFolder)
        {
            Directory.CreateDirectory(destinationFolder);
            int count = 0;
            foreach (var path in Directory.GetFiles(sourceFolder, "EID*.bytes"))
            {
                var name = Path.GetFileNameWithoutExtension(path);
                var destination = destinationFolder + "/" + name + ".asset";
                Mesh mesh = AssetDatabase.LoadAssetAtPath<Mesh>(destination);
                using (var reader = new BinaryReader(File.OpenRead(path)))
                {
                    var magic = new string(reader.ReadChars(4));
                    if (magic != "KMF1") throw new InvalidDataException(path + " has an unsupported format");
                    int vertexCount = reader.ReadInt32();
                    int indexCount = reader.ReadInt32();
                    if (vertexCount <= 0 || indexCount <= 0 || indexCount % 3 != 0)
                        throw new InvalidDataException(path + " has invalid topology");
                    var vertices = Read3(reader, vertexCount);
                    var normals = Read3(reader, vertexCount);
                    var tangents = Read4(reader, vertexCount);
                    var colors = ReadColors(reader, vertexCount);
                    var uv0 = Read2(reader, vertexCount);
                    var uv1 = Read2(reader, vertexCount);
                    var uv2 = Read2(reader, vertexCount);
                    var triangles = new int[indexCount];
                    for (int i = 0; i < indexCount; i++) triangles[i] = reader.ReadInt32();
                    if (reader.BaseStream.Position != reader.BaseStream.Length)
                        throw new InvalidDataException(path + " has extra bytes");

                    if (mesh == null)
                        mesh = new Mesh { name = name };
                    else
                        mesh.Clear(); // Keep the asset GUID and every scene MeshFilter reference.
                    mesh.indexFormat = IndexFormat.UInt32;
                    mesh.vertices = vertices;
                    mesh.normals = normals;
                    mesh.tangents = tangents;
                    mesh.colors = colors;
                    mesh.uv = uv0;
                    mesh.uv2 = uv1;
                    mesh.uv3 = uv2;
                    mesh.triangles = triangles;
                    mesh.RecalculateBounds();
                    if (!AssetDatabase.Contains(mesh)) AssetDatabase.CreateAsset(mesh, destination);
                    else EditorUtility.SetDirty(mesh);
                    count++;
                }
            }
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            return "Imported " + count + " meshes from " + sourceFolder;
        }

        private static Vector3[] Read3(BinaryReader reader, int count)
        {
            var result = new Vector3[count];
            for (int i = 0; i < count; i++) result[i] = new Vector3(reader.ReadSingle(), reader.ReadSingle(), reader.ReadSingle());
            return result;
        }

        private static Vector4[] Read4(BinaryReader reader, int count)
        {
            var result = new Vector4[count];
            for (int i = 0; i < count; i++) result[i] = new Vector4(reader.ReadSingle(), reader.ReadSingle(), reader.ReadSingle(), reader.ReadSingle());
            return result;
        }

        private static Color[] ReadColors(BinaryReader reader, int count)
        {
            var result = new Color[count];
            for (int i = 0; i < count; i++) result[i] = new Color(reader.ReadSingle(), reader.ReadSingle(), reader.ReadSingle(), reader.ReadSingle());
            return result;
        }

        private static Vector2[] Read2(BinaryReader reader, int count)
        {
            var result = new Vector2[count];
            for (int i = 0; i < count; i++) result[i] = new Vector2(reader.ReadSingle(), reader.ReadSingle());
            return result;
        }
    }
}
