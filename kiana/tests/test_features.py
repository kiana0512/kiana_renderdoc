"""Pure-data regression tests; no GPU required."""
import concurrent.futures
import importlib.util
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import threading
import time
import types
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.modules.setdefault("renderdoc", types.ModuleType("renderdoc"))


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "extensions/kiana_bridge" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fbx = load("fbx", "fbx_export.py")
rpc = load("rpc", "transport.py")


class MeshTests(unittest.TestCase):
    def test_strip_restart_and_winding(self):
        self.assertEqual(fbx.triangles([0,1,2,3,65535,4,5,6], "TriangleStrip",65535),
                         [(0,1,2),(2,1,3),(4,5,6)])
        self.assertEqual(fbx.triangles([0,0,1,2], "TriangleStrip"),[(1,0,2)])

    def test_invalid_topology(self):
        with self.assertRaises(ValueError):
            fbx.triangles([0,1],"TriangleList")
        with self.assertRaises(ValueError):
            fbx.triangles([0,1,2],"PatchList_3CPs")

    def test_normalized_and_packed(self):
        fmt = types.SimpleNamespace(compType="SNorm",compByteWidth=1,compCount=4,type="Regular")
        self.assertEqual(fbx.decode(bytes([128,0,127,64]),0,fmt)[:3],[-1,0,1])
        fmt.type, fmt.compType = "R10G10B10A2", "UNorm"
        self.assertEqual(fbx.decode(struct.pack("<I",0xFFFFFFFF),0,fmt),[1,1,1,1])

    def test_nonfinite_rejected(self):
        fmt = types.SimpleNamespace(compType="Float",compByteWidth=4,compCount=3,type="Regular")
        with self.assertRaises(ValueError):
            fbx.decode(struct.pack("<fff",0,float("nan"),0),0,fmt)

    def test_write_fixture(self):
        mesh = {"position":[[0.,0.,0.],[1.,0.,0.],[0.,1.,0.]],"triangles":[(0,1,2)],
                "normal":[[0.,0.,1.]]*3,"tangent":[[1.,0.,0.]]*3,
                "uv0":[[0.,0.],[1.,0.],[0.,1.]],"uv1":[[0.5,0.5]]*3,"uv2":[[1.,1.]]*3,
                "color":[[1.,0.,0.,1.]]*3}
        out = ROOT.parent / "build-early-exports" / "fbx-fixture.fbx"
        fbx.write_fbx(str(out),mesh)
        self.assertTrue(out.stat().st_size > 100)


class TransportTests(unittest.TestCase):
    def test_concurrent_requests_and_unicode(self):
        with tempfile.TemporaryDirectory() as home:
            old = os.environ.get("KIANA_HOME")
            os.environ["KIANA_HOME"] = home
            box = Path(rpc.mailbox_root()) / "123-test"
            rpc.atomic_json(str(box / "instance.json"),dict(pid=os.getpid(),heartbeat=time.time(),enabled=True))
            stop = threading.Event()
            def serve():
                while not stop.wait(.005):
                    for request in box.glob("*.request.json"):
                        data = json.loads(request.read_text(encoding="utf-8"))
                        request.unlink()
                        rpc.atomic_json(str(box / (data["id"]+".response.json")),
                                        dict(id=data["id"],result=data["params"]))
            worker = threading.Thread(target=serve)
            worker.start()
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
                    futures = [pool.submit(rpc.IPCClient(5).call,"echo",{"index":i,"text":"琪亚娜"}) for i in range(24)]
                    results = [f.result() for f in futures]
                self.assertEqual([r["index"] for r in results],list(range(24)))
                self.assertTrue(all(r["text"] == "琪亚娜" for r in results))
                self.assertEqual(list(box.glob("*.request.json")),[])
                self.assertEqual(list(box.glob("*.response.json")),[])
            finally:
                stop.set()
                worker.join()
                (box / "instance.json").unlink()
                if old is None:
                    os.environ.pop("KIANA_HOME",None)
                else:
                    os.environ["KIANA_HOME"] = old


if __name__ == "__main__":
    unittest.main()
