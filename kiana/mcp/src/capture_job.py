"""Kiana Studio capture adapter. Progress is emitted as newline-delimited JSON."""
import argparse
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def emit(kind, **values):
    print(json.dumps(dict(type=kind, **values), ensure_ascii=False), flush=True)


def read_state(path):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return {}


def launch(gui, script, cwd, elevate):
    """Use the normal Windows UAC flow; never bypass or answer its prompt."""
    arguments = [str(gui), "--python=" + str(script)]
    if not elevate:
        return subprocess.Popen(arguments, cwd=str(cwd), stdin=subprocess.DEVNULL,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    class ShellExecuteInfo(ctypes.Structure):
        _fields_ = [("cbSize", wintypes.DWORD), ("fMask", wintypes.ULONG),
                    ("hwnd", wintypes.HWND), ("lpVerb", wintypes.LPCWSTR),
                    ("lpFile", wintypes.LPCWSTR), ("lpParameters", wintypes.LPCWSTR),
                    ("lpDirectory", wintypes.LPCWSTR), ("nShow", ctypes.c_int),
                    ("hInstApp", wintypes.HINSTANCE), ("lpIDList", ctypes.c_void_p),
                    ("lpClass", wintypes.LPCWSTR), ("hkeyClass", wintypes.HKEY),
                    ("dwHotKey", wintypes.DWORD), ("hIcon", wintypes.HANDLE),
                    ("hProcess", wintypes.HANDLE)]
    info = ShellExecuteInfo()
    info.cbSize = ctypes.sizeof(info)
    info.fMask = 0x40  # SEE_MASK_NOCLOSEPROCESS
    info.lpVerb = "runas"
    info.lpFile = str(gui)
    info.lpParameters = subprocess.list2cmdline(arguments[1:])
    info.lpDirectory = str(cwd)
    info.nShow = 0
    shell = ctypes.WinDLL("shell32", use_last_error=True)
    shell.ShellExecuteExW.argtypes = [ctypes.POINTER(ShellExecuteInfo)]
    shell.ShellExecuteExW.restype = wintypes.BOOL
    if not shell.ShellExecuteExW(ctypes.byref(info)):
        code = ctypes.get_last_error()
        if code == 1223:
            raise RuntimeError("已取消 Windows 管理员权限确认，游戏未启动")
        raise ctypes.WinError(code)
    return ElevatedProcess(info.hProcess)


class ElevatedProcess:
    def __init__(self, handle):
        self.handle = handle
        self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        self.kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        self.kernel.CloseHandle.argtypes = [wintypes.HANDLE]

    def poll(self):
        code = wintypes.DWORD()
        if not self.kernel.GetExitCodeProcess(self.handle, ctypes.byref(code)):
            raise ctypes.WinError(ctypes.get_last_error())
        return None if code.value == 259 else code.value

    def close(self):
        self.kernel.CloseHandle(self.handle)


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    for name in ("executable", "working-dir", "output", "runtime"):
        result.add_argument("--" + name, required=True)
    result.add_argument("--arguments-json", default="[]")
    result.add_argument("--frame", type=int, default=900)
    result.add_argument("--timeout", type=int, default=300)
    for name in ("unity-safe", "preserve-export-identity", "wrap-opted-out-devices", "hook-children", "reference-all-resources", "capture-callstacks",
                 "allow-fullscreen", "elevate", "manual", "check"):
        result.add_argument("--" + name, action="store_true")
    return result


def prepare(args):
    executable = Path(args.executable).resolve()
    working = Path(args.working_dir).resolve()
    gui = Path(args.runtime).resolve() / "kiana_qrenderdoc.exe"
    worker = Path(__file__).resolve().parents[1] / "worker" / "rdoc_studio_capture.py"
    for path in (executable, gui, worker):
        if not path.is_file():
            raise FileNotFoundError("文件不存在：" + str(path))
    if not working.is_dir():
        raise ValueError("工作目录不存在：" + str(working))
    arguments = json.loads(args.arguments_json)
    if not isinstance(arguments, list) or any(not isinstance(item, str) for item in arguments):
        raise ValueError("arguments-json 必须是字符串数组")
    if args.frame < 1 or args.timeout < 1:
        raise ValueError("捕获帧和超时必须大于零")
    config = dict(executable=str(executable), working_dir=str(working), arguments=arguments,
                  output=str(Path(args.output).resolve()), frame=args.frame, timeout_seconds=args.timeout,
                  manual=args.manual, hook_children=args.hook_children,
                  unity_safe=args.unity_safe, preserve_export_identity=args.preserve_export_identity,
                  wrap_opted_out_devices=args.wrap_opted_out_devices,
                  reference_all_resources=args.reference_all_resources,
                  capture_callstacks=args.capture_callstacks, allow_fullscreen=args.allow_fullscreen)
    return gui, worker, config


def finish_capture(gui, worker, output, state):
    capture = Path(state['captures'][-1])
    if not capture.is_file():
        raise RuntimeError('捕获进程未生成 RDC 文件')
    emit('progress', percent=65, message='正在验证捕获文件')
    verify_config = output / 'verify-config.json'
    verify_result = output / 'verification.json'
    verify_config.write_text(json.dumps(dict(capture=str(capture), result=str(verify_result))), encoding='utf-8')
    script = output / 'verify-bootstrap.py'
    script.write_text('import os, runpy, sys\n'
                      + 'sys.argv = [' + repr(str(script)) + ']\n'
                      + "os.environ['KIANA_NSIGHT_VERIFY_CONFIG'] = " + repr(str(verify_config)) + '\n'
                      + 'runpy.run_path(' + repr(str(worker.parent / 'rdoc_verify.py')) + ')\n', encoding='utf-8')
    process = launch(gui, script, output, False)
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        report = read_state(verify_result)
        if report.get('stage') == 'complete' and report.get('ok'):
            emit('result', result=dict(capture=str(capture), api=report.get('api'),
                                      frame_number=report.get('frame_number'), verification=str(verify_result)))
            return 0
        if report.get('error') or process.poll() is not None:
            report = read_state(verify_result)
            if report.get('stage') == 'complete' and report.get('ok'):
                emit('result', result=dict(capture=str(capture), api=report.get('api'),
                                          frame_number=report.get('frame_number'), verification=str(verify_result)))
                return 0
            raise RuntimeError('RDC 验证失败：' + str(report.get('error') or report.get('fatal_error') or '回放进程提前退出'))
        time.sleep(0.3)
    raise TimeoutError('RDC 验证超时；捕获文件保留在 ' + str(capture))


def bootstrap_script(args, worker, config_path, output, script):
    return ("import os, runpy, sys, json, traceback\n"
                      + 'sys.argv = [' + repr(str(script)) + ']\n'
                      + "os.environ['KIANA_UNITY_SAFE_MODE'] = " + repr("1" if args.unity_safe else "0") + "\n"
                      + "os.environ['KIANA_EXPORT_IDENTITY'] = " + repr("1" if args.preserve_export_identity else "0") + "\n"
                      + "os.environ['KIANA_D3D11_CAPTURE_OVERRIDE'] = " + repr("1" if args.wrap_opted_out_devices else "0") + "\n"
                      + "try:\n"
                      + "    worker = runpy.run_path(" + repr(str(worker)) + ")\n"
                      + "    sys.exit(worker['main'](" + repr(str(config_path)) + "))\n"
                      + "except Exception:\n"
                      + "    with open(" + repr(str(output / 'direct-capture-result.json')) + ", 'w', encoding='utf-8') as report:\n"
                      + "        json.dump(dict(status='failed', session_active=False, error=traceback.format_exc()), report)\n"
                      + "    sys.exit(1)\n")


def main():
    args = parser().parse_args()
    gui, worker, config = prepare(args)
    if args.check:
        emit("result", result=dict(valid=True, runtime=str(gui), worker=str(worker)))
        return 0
    output = Path(config["output"])
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise ValueError("捕获输出目录必须为空，避免覆盖已有会话")
    config_path = output / "direct-capture-config.json"
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    # qrenderdoc's Python console does not define __file__. Pass only explicit paths.
    # Environment is set inside the bootstrap so it also survives Windows elevation.
    script = output / "capture-bootstrap.py"
    script.write_text(bootstrap_script(args, worker, config_path, output, script), encoding="utf-8")
    emit("progress", percent=4, message="等待 Windows 权限确认" if args.elevate else "正在启动捕获进程")
    child = launch(gui, script, Path(config["working_dir"]), args.elevate)
    state_path = output / "direct-capture-result.json"
    deadline = time.monotonic() + args.timeout + 30
    previous = None
    try:
        while time.monotonic() < deadline:
            state = read_state(state_path)
            status = state.get("status")
            if status != previous:
                messages = {"launching": "正在注入目标程序", "waiting_for_graphics": "等待游戏图形 API 和子进程",
                            "waiting_for_capture": "游戏图形 API 已连接，可以抓帧", "capturing": "正在保存当前帧"}
                if status in messages:
                    emit("progress", percent=28 if status == "waiting_for_capture" else 12, message=messages[status])
                previous = status
            if status == "failed":
                raise RuntimeError(state.get("error", "捕获进程失败"))
            if status == "capture_saved" and not args.manual:
                return finish_capture(gui, worker, output, state)
            if state.get("session_active") is False:
                if state.get("status") == "stopped":
                    emit("result", result=state)
                    return 0
                if not state.get("captures"):
                    raise RuntimeError("目标连接已结束，没有生成 RDC")
                emit("result", result=state)
                return 0
            if child.poll() is not None:
                # A final atomic state may have been written after this iteration's read.
                state = read_state(state_path)
                if state.get("status") == "capture_saved" and state.get("captures"):
                    return finish_capture(gui, worker, output, state)
                raise RuntimeError(state.get("error") or "捕获进程提前退出；请检查 RenderDoc 日志")
            time.sleep(0.3)
        raise TimeoutError("捕获会话超时")
    finally:
        if isinstance(child, ElevatedProcess):
            child.close()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        emit("error", message=str(error))
        sys.exit(1)
