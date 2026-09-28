using System;
using System.Collections.Generic;
using System.IO;
using System.Text.RegularExpressions;
using UnityEditor;
using UnityEngine;

namespace KianaFrameReconstruction
{
    // Capture diagnostic passes without leaving the user's visible scene altered.
    public static class CaptureGBuffer5Stages
    {
        public static string Capture(int throughEventId, bool isolated = false,
                                     bool includeInactiveVariants = false)
        {
            var root = GameObject.Find("Frame 38112 — 3D G-buffer reconstruction");
            if (root == null) throw new Exception("Open Frame38112_GBuffer5_World first");
            var camera = Camera.main;
            if (camera == null) throw new Exception("Captured camera missing");
            var groups = new List<GameObject>();
            var objects = new List<GameObject>();
            var active = new List<bool>();
            foreach (Transform group in root.transform)
            {
                if (!group.name.Contains("G-buffer")) continue;
                groups.Add(group.gameObject);
                foreach (Transform child in group)
                {
                    var match = Regex.Match(child.name, @"^EID (\d+)");
                    if (!match.Success) continue;
                    objects.Add(child.gameObject);
                    active.Add(child.gameObject.activeSelf);
                }
            }
            var groupActive = new List<bool>();
            foreach (var group in groups) groupActive.Add(group.activeSelf);
            RenderTexture previousTarget = camera.targetTexture;
            RenderTexture previousActive = RenderTexture.active;
            RenderTexture target = null;
            Texture2D output = null;
            try
            {
                foreach (var group in groups) group.SetActive(true);
                for (int i = 0; i < objects.Count; i++)
                {
                    var id = int.Parse(Regex.Match(objects[i].name, @"^EID (\d+)").Groups[1].Value);
                    objects[i].SetActive(isolated ? id == throughEventId :
                                         id <= throughEventId && (active[i] || includeInactiveVariants));
                }
                target = new RenderTexture(2880, 1368, 24, RenderTextureFormat.ARGB32);
                target.Create();
                camera.targetTexture = target;
                camera.GetComponent<CapturedCameraMatrix>().Apply();
                camera.Render();
                RenderTexture.active = target;
                output = new Texture2D(2880, 1368, TextureFormat.RGBA32, false);
                output.ReadPixels(new Rect(0, 0, 2880, 1368), 0, 0);
                output.Apply();
                var path = $"Assets/Kiana/Validation/StageRenders/EID{throughEventId}-{(isolated ? "isolated" : "through")}.png";
                Directory.CreateDirectory(Path.GetDirectoryName(path));
                File.WriteAllBytes(path, output.EncodeToPNG());
                return path;
            }
            finally
            {
                camera.targetTexture = previousTarget;
                RenderTexture.active = previousActive;
                for (int i = 0; i < objects.Count; i++) objects[i].SetActive(active[i]);
                for (int i = 0; i < groups.Count; i++) groups[i].SetActive(groupActive[i]);
                if (output != null) UnityEngine.Object.DestroyImmediate(output);
                if (target != null) { target.Release(); UnityEngine.Object.DestroyImmediate(target); }
            }
        }
    }
}
