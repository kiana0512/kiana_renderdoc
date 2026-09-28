import unittest

from kiana.mcp.src.reconstruction_report import classify_pass, group_passes


class ReconstructionReportTests(unittest.TestCase):
    def test_groups_flattened_pass_markers(self):
        actions = [
            {"name": "Colour Pass #1 (1 Targets)", "outputs": [10]},
            {"name": "Action 1", "eventId": 4, "numIndices": 3},
            {"name": "Depth-only Pass #1", "outputs": []},
            {"name": "Action 2", "eventId": 9, "numIndices": 12},
        ]
        groups = group_passes(actions)
        self.assertEqual([item["name"] for item in groups],
                         ["Colour Pass #1 (1 Targets)", "Depth-only Pass #1"])
        self.assertEqual(groups[0]["actions"][0]["eventId"], 4)

    def test_classifies_geometry_post_and_ui(self):
        geometry = classify_pass("Colour Pass #2", 4, 1000,
                                 {"numIndices": 900, "outputs": [1, 2, 3]},
                                 {"vertexInputs": [{"name": "POSITION"}]}, [])
        post = classify_pass("Colour Pass #3", 1, 3,
                             {"numIndices": 3, "outputs": [1]},
                             {"vertexInputs": []}, [])
        ui = classify_pass("Colour Pass #4", 40, 900,
                           {"numIndices": 600, "outputs": [1]},
                           {"vertexInputs": [{"name": "POSITION"}]},
                           [{"texName": "Font Texture"}])
        self.assertEqual(geometry, "场景几何/G-buffer")
        self.assertEqual(post, "全屏后处理/拷贝")
        self.assertEqual(ui, "UI/文字/图标合成")


if __name__ == "__main__":
    unittest.main()
