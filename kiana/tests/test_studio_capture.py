"""Exercise Studio's capture protocol without launching or hooking a game."""
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location('studio_capture', Path(__file__).parents[1] / 'mcp/worker/rdoc_studio_capture.py')
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)


class Target:
    def __init__(self, name, api, messages=()):
        self.name, self.api, self.messages = name, api, list(messages)
        self.connected, self.triggers, self.queued = True, 0, []

    def GetPID(self): return 100 if 'launcher' in self.name else 200
    def GetTarget(self): return self.name
    def GetAPI(self): return self.api
    def Connected(self): return self.connected
    def Shutdown(self): self.connected = False
    def ReceiveMessage(self, _):
        if self.messages:
            message = self.messages.pop(0)
            if message.type == 'child': self.connected = False
            return message
        return NS(type='noop')
    def QueueCapture(self, frame, count):
        self.queued.append((frame, count))
        self.messages.append(NS(type='capture', newCapture=NS(path='test.rdc')))
    def TriggerCapture(self, count):
        self.triggers += count
        self.messages.append(NS(type='capture', newCapture=NS(path='test.rdc')))


class CaptureTests(unittest.TestCase):
    def simulate(self, targets, manual=False, result='ok', trigger=False):
        with tempfile.TemporaryDirectory() as directory:
            config = dict(output=directory, executable='game.exe', working_dir=directory, arguments=[], frame=12,
                          timeout_seconds=2, manual=manual, hook_children=True, allow_fullscreen=False,
                          reference_all_resources=False, capture_callstacks=False)
            if trigger:
                Path(directory, 'trigger-capture.json').write_text(json.dumps(dict(id='once', frames=1)))
            clock = NS(value=1.0)
            def sleep(seconds): clock.value += seconds
            rd = NS(CaptureOptions=lambda: NS(), SetDebugLogFile=lambda path: None,
                    ResultCode=NS(Succeeded='ok'), ExecuteAndInject=lambda *args: NS(result=result, ident=1),
                    CreateTargetControl=lambda host, ident, name, force: targets.get(ident),
                    TargetControlMessageType=NS(Noop='noop', NewChild='child', NewCapture='capture', Disconnected='disconnected'))
            with patch.object(worker.time, 'monotonic', lambda: clock.value), patch.object(worker.time, 'sleep', sleep):
                code = worker.run(rd, config)
            return code, json.loads(Path(directory, 'direct-capture-result.json').read_text(encoding='utf-8'))

    def test_launch_failure_is_terminal_and_reported(self):
        code, state = self.simulate({}, result='Access denied')
        self.assertEqual(code, 1)
        self.assertIn('Access denied', state['error'])
        self.assertFalse(state['session_active'])

    def test_launcher_exit_follows_announced_child(self):
        launcher = Target('launcher.exe', '', [NS(type='child', newChild=NS(ident=2))])
        game = Target('Client-Win64-Shipping.exe', 'D3D12')
        code, state = self.simulate({1: launcher, 2: game})
        self.assertEqual(code, 0)
        self.assertEqual(state['pid'], 200)
        self.assertEqual(game.queued, [(12, 1)])
        self.assertEqual(state['captures'], ['test.rdc'])

    def test_manual_trigger_is_consumed_once(self):
        game = Target('game.exe', 'D3D11')
        _, state = self.simulate({1: game}, manual=True, trigger=True)
        self.assertEqual(game.triggers, 1)
        self.assertEqual(game.queued, [])
        self.assertEqual(state['last_trigger_id'], 'once')
        self.assertEqual(state['captures'], ['test.rdc'])

    def test_launcher_graphics_are_not_reported_as_game_ready(self):
        launcher = Target('launcher_main.exe', 'D3D11')
        _, state = self.simulate({1: launcher}, manual=True, trigger=True)
        self.assertEqual(launcher.triggers, 0)
        self.assertEqual(state['pid'], 0)
        self.assertEqual(state['captures'], [])


if __name__ == '__main__':
    unittest.main()
