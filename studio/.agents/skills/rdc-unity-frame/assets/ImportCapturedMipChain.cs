using System;
using System.IO;
using UnityEditor;
using UnityEngine;

namespace KianaFrameReconstruction
{
    // Rebuild a Unity Texture2D from RenderDoc's color-managed per-mip PNGs.
    // This retains the captured mip shapes without recompressing the atlas.
    public static class ImportCapturedMipChain
    {
        const string Root = "Assets/Kiana/Textures";

        public static string Import(int resourceId)
        {
            string prefix = $"{Root}/MipSources/RID{resourceId}-mip";
            int count = 0;
            while (File.Exists($"{prefix}{count:00}.png")) count++;
            if (count < 2) throw new Exception("Missing source mip chain for RID" + resourceId);

            Texture2D source = null;
            Texture2D texture = null;
            try
            {
                source = new Texture2D(2, 2, TextureFormat.RGBA32, false, true);
                source.LoadImage(File.ReadAllBytes($"{prefix}00.png"), false);
                texture = new Texture2D(source.width, source.height,
                    TextureFormat.RGBA32, true, true);
                if (texture.mipmapCount != count)
                    throw new Exception($"RID{resourceId}: expected {texture.mipmapCount} mips, found {count}");
                for (int mip = 0; mip < count; mip++)
                {
                    if (mip > 0)
                        source.LoadImage(File.ReadAllBytes($"{prefix}{mip:00}.png"), false);
                    if (source.width != Math.Max(1, texture.width >> mip) ||
                        source.height != Math.Max(1, texture.height >> mip))
                        throw new Exception($"RID{resourceId} mip {mip} dimensions mismatch");
                    texture.SetPixels32(source.GetPixels32(), mip);
                }
                texture.Apply(false, false);
                texture.name = $"RID{resourceId}_CapturedMips";
                texture.filterMode = FilterMode.Bilinear;
                texture.wrapMode = TextureWrapMode.Repeat;
                var path = $"{Root}/SourceMips/RID{resourceId}.asset";
                Directory.CreateDirectory(Path.GetDirectoryName(path));
                var existing = AssetDatabase.LoadAssetAtPath<Texture2D>(path);
                if (existing != null) AssetDatabase.DeleteAsset(path);
                AssetDatabase.CreateAsset(texture, path);
                AssetDatabase.SaveAssets();
                texture = null;
                return path;
            }
            finally
            {
                if (source != null) UnityEngine.Object.DestroyImmediate(source);
                if (texture != null) UnityEngine.Object.DestroyImmediate(texture);
            }
        }
    }
}
