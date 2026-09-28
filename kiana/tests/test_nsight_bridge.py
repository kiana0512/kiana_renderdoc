"""Focused tests for the Nsight bridge's security and fidelity helpers."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from kiana.mcp.src import nsight_bridge


class NsightBridgeTests(unittest.TestCase):
    def test_metadata_secrets_are_redacted_recursively(self):
        source = {
            "primary_api": "D3D12",
            "process_environment": ["TOKEN=secret"],
            "process_command_line": "game.exe --password secret",
            "nested": {"process_environment": ["API_KEY=secret"]},
        }
        clean = nsight_bridge.sanitize_metadata(source)
        text = json.dumps(clean)
        self.assertNotIn("secret", text)
        self.assertEqual(clean["primary_api"], "D3D12")

    def test_source_command_counts(self):
        functions = [
            {"function_name": "ID3D12GraphicsCommandList_DrawIndexedInstanced"},
            {"function_name": "ID3D12GraphicsCommandList_DrawInstanced"},
            {"function_name": "ID3D12GraphicsCommandList_Dispatch"},
            {"function_name": "IDXGISwapChain_Present"},
        ]
        self.assertEqual(nsight_bridge.count_source_commands(functions), {
            "events": 4, "draws": 2, "dispatches": 1, "presents": 1})

    def test_non_d3d12_is_rejected_before_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            capture = root / "test.ngfx-capture"
            capture.write_bytes(b"capture")
            out = root / "output"

            def metadata(_nsight, _source, option):
                if option == "--metadata":
                    return json.dumps({"primary_api": "D3D11"})
                raise AssertionError("No other evidence should be queried")

            with patch.object(nsight_bridge, "_find_nsight", return_value=capture), \
                 patch.object(nsight_bridge, "_metadata", side_effect=metadata):
                with self.assertRaisesRegex(ValueError, "D3D12"):
                    nsight_bridge.convert_nsight_to_rdc(str(capture), str(out))


if __name__ == "__main__":
    unittest.main()
