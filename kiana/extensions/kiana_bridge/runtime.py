"""PySide-free polling and user settings for the bundled Kiana extension."""
import json
import os
import threading
import time
import uuid

from .transport import atomic_json, mailbox_root

DEFAULTS = {"mcp_enabled": True, "vulkan_linked_capture": False,
            "fbx_export": True, "export_textures": True, "unreal_vertex_layout": False}


def settings_path():
    return os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "Kiana", "features.json")


def settings():
    result = dict(DEFAULTS)
    try:
        with open(settings_path(), encoding="utf-8") as f:
            for k, v in json.load(f).items():
                if k in result and isinstance(v, bool):
                    result[k] = v
    except (OSError, ValueError):
        pass
    return result


def apply_settings(values):
    # Inherited by applications launched after changing this option.
    os.environ["KIANA_VULKAN_MULTIDEVICE"] = "1" if values["vulkan_linked_capture"] else "0"


def update_settings(changes):
    values = settings()
    for k, v in changes.items():
        if k not in DEFAULTS or not isinstance(v, bool):
            raise ValueError("Expected a boolean feature setting: " + k)
        values[k] = v
    atomic_json(settings_path(), values)
    apply_settings(values)
    return values


class JsonPoller:
    def __init__(self, handler, ctx):
        self.handler = handler
        self.ctx = ctx
        self.box = os.path.join(mailbox_root(), str(os.getpid()) + "-" + uuid.uuid4().hex[:8])
        self.stop_event = threading.Event()
        self.busy = threading.Event()

    def start(self):
        self.thread = threading.Thread(target=self.run, name="Kiana MCP mailbox")
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        # Never join on the GUI thread: pending UI invocation can hold the worker.
        try:
            os.remove(os.path.join(self.box, "instance.json"))
        except OSError:
            pass

    def run(self):
        os.makedirs(self.box, exist_ok=True)
        while not self.stop_event.wait(0.2):
            try:
                enabled = settings()["mcp_enabled"]
                atomic_json(os.path.join(self.box, "instance.json"),
                            {"pid": os.getpid(), "heartbeat": time.time(), "enabled": enabled})
                # Responses whose clients timed out are safe to clean by age.
                for name in os.listdir(self.box):
                    path = os.path.join(self.box, name)
                    try:
                        if name.endswith(".response.json") and time.time() - os.path.getmtime(path) > 600:
                            os.remove(path)
                    except FileNotFoundError:
                        pass  # A client consumed its own response concurrently.
                if not enabled or self.busy.is_set():
                    continue
                for name in sorted(os.listdir(self.box)):
                    if not name.endswith(".request.json"):
                        continue
                    path = os.path.join(self.box, name)
                    with open(path, encoding="utf-8") as f:
                        request = json.load(f)
                    os.remove(path)
                    rid = request.get("id", "")
                    if name != rid + ".request.json" or request.get("deadline", 0) < time.time():
                        continue
                    self.busy.set()

                    def invoke(req=request, request_id=rid):
                        try:
                            if not self.stop_event.is_set() and req["deadline"] >= time.time():
                                response = self.handler(req)
                                atomic_json(os.path.join(self.box, request_id + ".response.json"), response)
                        finally:
                            self.busy.clear()

                    try:
                        self.ctx.Extensions().GetMiniQtHelper().InvokeOntoUIThread(invoke)
                    except Exception:
                        self.busy.clear()
                        raise
                    break
            except Exception as e:
                print("[Kiana MCP] Mailbox error: %s" % e)


def register_menus(ctx, qrd, export_callback):
    for key in DEFAULTS:
        def toggle(context, data, feature=key):
            values = update_settings({feature: not settings()[feature]})
            message = "\n".join("%s: %s" % (k, "ON" if v else "OFF") for k, v in sorted(values.items()))
            message += "\n\nVulkan changes apply to subsequently launched applications."
            context.Extensions().MessageDialog(message, "Kiana feature switches")
        ctx.Extensions().RegisterWindowMenu(qrd.WindowMenu.Tools, ["Kiana", "Toggle " + key], toggle)
    ctx.Extensions().RegisterWindowMenu(qrd.WindowMenu.Tools, ["Kiana", "Export selected draw to FBX + textures"], export_callback)
