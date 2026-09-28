import unittest

from kiana.mcp.src.scene_reconstruction import classify_module, infer_unreal_attribute_map


class SceneReconstructionTests(unittest.TestCase):
    def test_classifies_gbuffer_geometry_with_evidence(self):
        module, confidence, reasons = classify_module({
            "category": "场景几何/G-buffer",
            "representative": {"numIndices": 83844},
            "pipeline": {"vertexInputs": [{"name": "ATTRIBUTE0"}]},
            "textures": [],
            "output_info": [],
        })
        self.assertEqual(module, "scene_geometry")
        self.assertGreaterEqual(confidence, 0.9)
        self.assertTrue(any("G-buffer" in reason for reason in reasons))

    def test_classifies_volume_texture_as_sky_atmosphere(self):
        module, confidence, reasons = classify_module({
            "category": "几何/透明物/界面网格",
            "representative": {"numIndices": 96},
            "pipeline": {"vertexInputs": [{"name": "ATTRIBUTE"}]},
            "textures": [{"texName": "3D Texture 30808", "format": "R8_UNORM",
                          "width": 1024, "height": 1024}],
            "output_info": [],
        })
        self.assertEqual(module, "sky_atmosphere")
        self.assertGreater(confidence, 0.7)
        self.assertTrue(any("体纹理" in reason for reason in reasons))

    def test_keeps_uncertain_stage_explicit(self):
        module, confidence, reasons = classify_module({
            "category": "合成/辅助 Pass", "representative": {},
            "pipeline": {}, "textures": [], "output_info": [],
        })
        self.assertEqual(module, "auxiliary")
        self.assertLessEqual(confidence, 0.5)
        self.assertTrue(reasons)

    def test_maps_stripped_unreal_vertex_semantics(self):
        mapping = infer_unreal_attribute_map({"vertexInputs": [
            {"name": "ATTRIBUTE0", "format": "R32G32B32_FLOAT"},
            {"name": "ATTRIBUTE1", "format": "R8G8B8A8_SNORM"},
            {"name": "ATTRIBUTE2", "format": "R8G8B8A8_SNORM"},
            {"name": "ATTRIBUTE5", "format": "R16G16_FLOAT"},
            {"name": "ATTRIBUTE13", "format": "B8G8R8A8_UNORM"},
        ]})
        self.assertEqual(mapping["position"], "ATTRIBUTE0")
        self.assertEqual(mapping["normal"], "ATTRIBUTE1")
        self.assertEqual(mapping["tangent"], "ATTRIBUTE2")
        self.assertEqual(mapping["uv0"], "ATTRIBUTE5")
        self.assertEqual(mapping["color"], "ATTRIBUTE13")


if __name__ == "__main__":
    unittest.main()
