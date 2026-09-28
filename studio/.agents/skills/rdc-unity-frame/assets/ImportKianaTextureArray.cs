using System;
using System.IO;
using UnityEditor;
using UnityEngine;

namespace KianaFrameReconstruction
{
    public static class ImportKianaTextureArray
    {
        const string Source = "Assets/Kiana/Textures/Arrays/RID42021.dds";
        const string Target = "Assets/Kiana/Textures/Arrays/RID42021.asset";

        [MenuItem("Kiana/Import RDC Texture Array RID42021")]
        public static string Import()
        {
            // RenderDoc DDS DX10 export, mip 0. Do not treat a 16-slice source
            // as one PNG. BC7 DXGI 99 is the sRGB variant of this array.
            var data = File.ReadAllBytes(Source);
            if (data.Length < 148 || data[0] != 'D' || data[1] != 'D' ||
                data[2] != 'S' || data[3] != ' ' ||
                BitConverter.ToUInt32(data, 84) != 0x30315844)
                throw new Exception("Expected DDS with DX10 header");
            int height = BitConverter.ToInt32(data, 12);
            int width = BitConverter.ToInt32(data, 16);
            int mips = BitConverter.ToInt32(data, 28);
            int dxgiFormat = BitConverter.ToInt32(data, 128);
            int dimension = BitConverter.ToInt32(data, 132);
            int slices = BitConverter.ToInt32(data, 140);
            if (width != 256 || height != 256 || mips != 1 ||
                dxgiFormat != 99 || dimension != 3 || slices != 16)
                throw new Exception($"Unexpected DDS layout: {width}x{height}, {mips} mips, " +
                                    $"DXGI {dxgiFormat}, dimension {dimension}, {slices} slices");
            int bytesPerSlice = ((width + 3) / 4) * ((height + 3) / 4) * 16;
            if (data.Length != 148 + bytesPerSlice * slices)
                throw new Exception("DDS payload size does not match 16 BC7 slices");
            var texture = new Texture2DArray(width, height, slices, TextureFormat.BC7, false, false)
            {
                name = "RID42021 Avatar UI 16 slices"
            };
            for (int slice = 0; slice < slices; slice++)
            {
                var block = new byte[bytesPerSlice];
                Buffer.BlockCopy(data, 148 + slice * bytesPerSlice, block, 0, bytesPerSlice);
                texture.SetPixelData(block, 0, slice);
            }
            texture.Apply(false, true);
            var prior = AssetDatabase.LoadAssetAtPath<Texture2DArray>(Target);
            if (prior != null) AssetDatabase.DeleteAsset(Target);
            AssetDatabase.CreateAsset(texture, Target);
            AssetDatabase.SaveAssets();
            return $"Imported RDC RID42021 texture array: {slices} BC7 sRGB slices";
        }
    }
}
