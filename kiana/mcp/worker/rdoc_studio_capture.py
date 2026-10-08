"""Embedded Python 3.6 worker implementing Studio's live capture file protocol."""
import json
import os
from pathlib import Path
import subprocess
import time
import traceback


def run(rd, config):
    output = Path(config['output'])
    state_path = output / 'direct-capture-result.json'
    state = dict(status='launching', executable=config['executable'], captures=[], messages=[],
                 session_active=True, capture_in_progress=False, pid=0)
    targets, pending, queued = {}, {}, set()
    started = time.monotonic()

    def save():
        state['elapsed_seconds'] = round(time.monotonic() - started, 2)
        temp = state_path.with_suffix('.tmp')
        temp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
        os.replace(str(temp), str(state_path))

    try:
        save()
        rd.SetDebugLogFile(str(output / 'renderdoc-debug.log'))
        options = rd.CaptureOptions()
        options.hookIntoChildren = config['hook_children']
        options.allowFullscreen = config['allow_fullscreen']
        options.refAllResources = config['reference_all_resources']
        options.captureCallstacks = config['capture_callstacks']
        result = rd.ExecuteAndInject(config['executable'], config['working_dir'],
                                     subprocess.list2cmdline(config['arguments']), [],
                                     str(output / 'capture'), options, False)
        state['launch_result'] = str(result.result)
        if result.result != rd.ResultCode.Succeeded:
            raise RuntimeError('游戏启动或注入失败：' + str(result.result))
        pending[result.ident] = time.monotonic() + 15
        state['status'] = 'waiting_for_graphics'
        last_connect, last_save = 0, 0
        while time.monotonic() - started < config['timeout_seconds']:
            now = time.monotonic()
            if now - last_connect >= 0.5:
                last_connect = now
                for ident, deadline in list(pending.items()):
                    target = rd.CreateTargetControl('', ident, 'Kiana Studio', False)
                    if target and target.Connected():
                        targets[ident] = target
                        del pending[ident]
                    else:
                        if target:
                            target.Shutdown()
                        if now >= deadline:
                            del pending[ident]
            for ident, target in list(targets.items()):
                # Drain child notifications before dropping a disconnected launcher.
                for _ in range(100):
                    message = target.ReceiveMessage(None)
                    if message.type == rd.TargetControlMessageType.Noop:
                        break
                    state['messages'].append(dict(type=str(message.type), api=target.GetAPI(), pid=target.GetPID()))
                    state['messages'] = state['messages'][-60:]
                    if message.type == rd.TargetControlMessageType.Disconnected:
                        break
                    if message.type == rd.TargetControlMessageType.NewChild and message.newChild.ident:
                        pending[message.newChild.ident] = now + 15
                    if message.type == rd.TargetControlMessageType.NewCapture:
                        capture = str(message.newCapture.path)
                        if capture not in state['captures']:
                            state['captures'].append(capture)
                        state['capture_in_progress'] = False
                        state['status'] = 'waiting_for_capture' if config['manual'] else 'capture_saved'
                if not target.Connected():
                    target.Shutdown()
                    del targets[ident]
            if state['status'] == 'capture_saved':
                break
            state['targets'] = [dict(ident=ident, pid=t.GetPID(), name=t.GetTarget(), api=t.GetAPI())
                                for ident, t in targets.items()]
            if (output / 'stop-capture.json').is_file() and not state['capture_in_progress']:
                state['status'] = 'stopped'
                break
            # Launcher web views are not the game's renderer.
            ready = [(ident, t) for ident, t in targets.items()
                     if str(t.GetAPI()).lower() not in ('', 'none', 'unknown')
                     and not any(name in t.GetTarget().lower() for name in ('launcher', 'webview'))]
            if ready:
                ident, target = ready[-1]
                state['pid'], state['api'] = target.GetPID(), target.GetAPI()
                if not state['capture_in_progress']:
                    state['status'] = 'waiting_for_capture'
                if not config['manual'] and ident not in queued:
                    target.QueueCapture(config['frame'], 1)
                    queued.add(ident)
                trigger = output / 'trigger-capture.json'
                if config['manual'] and trigger.is_file() and not state['capture_in_progress']:
                    try:
                        request = json.loads(trigger.read_text(encoding='utf-8-sig'))
                    except (ValueError, OSError):
                        request = {}
                    if request.get('id') and request['id'] != state.get('last_trigger_id'):
                        target.TriggerCapture(1)
                        state.update(last_trigger_id=request['id'], capture_in_progress=True, status='capturing')
            if not targets and not pending:
                if state['captures']:
                    state['status'] = 'disconnected'
                    break
                raise RuntimeError('启动进程已退出，未连接到游戏子进程或图形 API')
            if not ready and now - started > min(180, config['timeout_seconds']):
                raise RuntimeError('未连接到游戏图形 API；请检查启动器是否成功启动游戏')
            if now - last_save > 0.5:
                save()
                last_save = now
            time.sleep(0.05)
        else:
            raise RuntimeError('捕获会话超时')
    except Exception as error:
        state.update(status='failed', error=str(error), traceback=traceback.format_exc())
    finally:
        for target in targets.values():
            target.Shutdown()
        state['session_active'] = False
        state['capture_in_progress'] = False
        save()
    return 0 if state['status'] == 'stopped' or (state['captures'] and state['status'] != 'failed') else 1


def main(config_path):
    import renderdoc as rd
    return run(rd, json.loads(Path(config_path).read_text(encoding='utf-8')))
