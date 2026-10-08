"""Exercise Studio's capture protocol without launching or hooking a game."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location('studio_capture', Path(__file__).parents[1] / 'mcp/worker/rdoc_studio_capture.py')
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)
job_spec = importlib.util.spec_from_file_location('capture_job', Path(__file__).parents[1] / 'mcp/src/capture_job.py')
job = importlib.util.module_from_spec(job_spec)
job_spec.loader.exec_module(job)


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
    def simulate(self, targets, manual=False, result='ok', trigger=False, stop=False):
        with tempfile.TemporaryDirectory() as directory:
            config = dict(output=directory, executable='game.exe', working_dir=directory, arguments=[], frame=12,
                          timeout_seconds=2, manual=manual, hook_children=True, allow_fullscreen=False,
                          reference_all_resources=False, capture_callstacks=False)
            if trigger:
                Path(directory, 'trigger-capture.json').write_text(json.dumps(dict(id='once', frames=1)))
            if stop:
                Path(directory, 'stop-capture.json').write_text('{}')
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

    def test_stop_disconnects_control_without_triggering_or_terminating_the_game(self):
        game = Target('game.exe', 'D3D11')
        code, state = self.simulate({1: game}, manual=True, stop=True)
        self.assertEqual(code, 0)
        self.assertEqual(state['status'], 'stopped')
        self.assertFalse(state['session_active'])
        self.assertEqual(game.triggers, 0)
        self.assertEqual(state['captures'], [])


class BootstrapTests(unittest.TestCase):
    def test_cli_accepts_explicit_game_compatibility_flags(self):
        args = job.parser().parse_args(['--executable', 'game.exe', '--working-dir', '.', '--output', '.', '--runtime', '.',
                                       '--preserve-export-identity', '--wrap-opted-out-devices'])
        self.assertTrue(args.preserve_export_identity)
        self.assertTrue(args.wrap_opted_out_devices)

    def run_bootstrap(self, enabled):
        args = NS(unity_safe=enabled, preserve_export_identity=enabled, wrap_opted_out_devices=enabled)
        observed = {}
        def main(config):
            observed.update({key: os.environ[key] for key in ('KIANA_UNITY_SAFE_MODE', 'KIANA_EXPORT_IDENTITY', 'KIANA_D3D11_CAPTURE_OVERRIDE')})
            observed['config'] = config
            return 7
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            script = job.bootstrap_script(args, root / 'worker.py', root / 'config.json', root, root / 'bootstrap.py')
            with patch.dict(os.environ, {key: '1' for key in ('KIANA_UNITY_SAFE_MODE', 'KIANA_EXPORT_IDENTITY', 'KIANA_D3D11_CAPTURE_OVERRIDE')}), patch('runpy.run_path', return_value={'main': main}), patch('sys.argv', []):
                with self.assertRaises(SystemExit) as raised:
                    exec(compile(script, '<capture-bootstrap>', 'exec'), {})
                self.assertEqual(raised.exception.code, 7)
            self.assertEqual(observed.pop('config'), str(root / 'config.json'))
        return observed

    def test_compatibility_is_set_inside_the_elevated_bootstrap(self):
        self.assertEqual(set(self.run_bootstrap(True).values()), {'1'})

    def test_default_profile_clears_inherited_compatibility_flags(self):
        self.assertEqual(set(self.run_bootstrap(False).values()), {'0'})


if __name__ == '__main__':
    unittest.main()
