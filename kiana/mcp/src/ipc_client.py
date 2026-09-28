"""Use the same protocol as the portable GUI extension."""
import importlib.util
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("KIANA_HOME", str(ROOT))
spec = importlib.util.spec_from_file_location("kiana_transport", ROOT / "extensions/kiana_bridge/transport.py")
transport = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transport)
IPCClient = transport.IPCClient
instances = transport.instances
