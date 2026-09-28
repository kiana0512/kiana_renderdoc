"""Local, correlated file RPC. Compatible with embedded Python 3.6.

Each installation and GUI process has its own mailbox. Publication is atomic;
clients never delete another client's requests or consume its responses.
"""
import hashlib
import json
import os
import tempfile
import time
import uuid


def installation_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def mailbox_root():
    root = os.environ.get("KIANA_HOME", installation_root())
    key = hashlib.sha256(os.path.normcase(os.path.realpath(root)).encode("utf-8")).hexdigest()[:16]
    return os.path.join(tempfile.gettempdir(), "kiana_mcp", key)


def atomic_json(path, value):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + "." + uuid.uuid4().hex + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(value, f, ensure_ascii=False, default=str)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def instances():
    root = mailbox_root()
    found = []
    if os.path.isdir(root):
        for name in os.listdir(root):
            try:
                with open(os.path.join(root, name, "instance.json"), encoding="utf-8") as f:
                    data = json.load(f)
                if time.time() - data["heartbeat"] < 10 and data.get("enabled") and process_alive(data["pid"]):
                    data["mailbox"] = os.path.join(root, name)
                    found.append(data)
            except (OSError, ValueError, KeyError):
                pass
    return sorted(found, key=lambda d: d["pid"])


def process_alive(pid):
    if os.name == "nt":
        import ctypes
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.restype = ctypes.c_void_p
        kernel.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        handle = kernel.OpenProcess(0x100000, False, int(pid))
        if not handle:
            return ctypes.get_last_error() == 5  # An elevated GUI may deny this query.
        try:
            return kernel.WaitForSingleObject(handle, 0) == 258
        finally:
            kernel.CloseHandle(handle)
    try:
        os.kill(int(pid), 0)
        return True
    except OSError:
        return False


class IPCClient:
    def __init__(self, timeout=120.0):
        self.timeout = timeout
        self.pid = int(os.environ.get("KIANA_PID", "0"))

    def is_bridge_alive(self):
        try:
            return self.call("ping", {}, timeout=3).get("status") == "ok"
        except Exception:
            return False

    def call(self, method, params, timeout=None):
        choices = instances()
        if self.pid:
            choices = [i for i in choices if i["pid"] == self.pid]
        if len(choices) != 1:
            raise RuntimeError("Select exactly one Kiana GUI instance (list_instances/select_instance). Active PIDs: %s" %
                               [i["pid"] for i in choices])
        box = choices[0]["mailbox"]
        rid = uuid.uuid4().hex
        request = os.path.join(box, rid + ".request.json")
        response = os.path.join(box, rid + ".response.json")
        deadline = time.time() + (self.timeout if timeout is None else timeout)
        atomic_json(request, {"id": rid, "method": method, "params": params, "deadline": deadline})
        try:
            while time.time() < deadline:
                try:
                    with open(response, encoding="utf-8") as f:
                        data = json.load(f)
                except (FileNotFoundError, PermissionError, json.JSONDecodeError):
                    # On Windows the bridge creates/replaces the response before its
                    # writer handle is fully released. Treat that short sharing window
                    # exactly like an incomplete response instead of failing the RPC.
                    time.sleep(0.05)
                    continue
                if data.get("id") != rid:
                    raise RuntimeError("Mismatched RPC response")
                if "error" in data:
                    raise RuntimeError(str(data["error"]))
                return data.get("result")
            raise TimeoutError("Kiana request timed out; an already running operation may still finish: " + method)
        finally:
            for path in (request, response):
                try:
                    os.remove(path)
                except FileNotFoundError:
                    pass
