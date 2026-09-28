using System;
using System.IO;
using UnityEditor;
using UnityEngine;

namespace KianaFrameReconstruction
{
    public static class ProbeScreenOutline
    {
        public static string Run(int eid, float thicknessPx = 1.2f,
                                 float normalThreshold = 0.32f)
        {
            var camera = Camera.main;
            if (camera == null) throw new Exception("Captured camera missing");
            var old = camera.GetComponent<CapturedToonOutline>();
            bool created = old == null;
            if (created) old = camera.gameObject.AddComponent<CapturedToonOutline>();
            float oldThickness = old.thicknessPx;
            float oldNormal = old.normalThreshold;
            bool wasEnabled = old.enabled;
            try
            {
                old.enabled = true;
                old.thicknessPx = thicknessPx;
                old.normalThreshold = normalThreshold;
                string source = CaptureGBuffer5Stages.Capture(eid);
                string output = $"Assets/Kiana/Validation/StageRenders/EID{eid}-screen-outline-{thicknessPx:F1}-{normalThreshold:F2}.png";
                File.Copy(source, output, true);
                return output;
            }
            finally
            {
                if (created) UnityEngine.Object.DestroyImmediate(old);
                else
                {
                    old.thicknessPx = oldThickness;
                    old.normalThreshold = oldNormal;
                    old.enabled = wasEnabled;
                }
            }
        }
    }
}
