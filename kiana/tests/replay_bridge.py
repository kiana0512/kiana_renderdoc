"""Exercise packaged bridge handlers against a real capture on the replay thread."""
import base64
import json
import os
import sys
import traceback
import renderdoc as rd

root = os.environ.get('KIANA_TEST_ROOT', os.getcwd())
package = os.environ['KIANA_TEST_PACKAGE']
sys.path.insert(0, os.path.join(package, 'extensions'))
import kiana_bridge as bridge
report = {'passed': False, 'checks': []}
cap = controller = None
try:
    cap = rd.OpenCaptureFile()
    result = cap.OpenFile(os.path.join(root, 'dist/RenderTest-1.47-EarlyHooks-v8-x64/test-results/wuthering-v8_frame3070.rdc'), 'rdc', None)
    assert result.OK(), result.Message()
    result, controller = cap.OpenCapture(rd.ReplayOptions(), None)
    assert result.OK(), result.Message()
    class Context:
        def IsCaptureLoaded(self): return True
        def CurEvent(self): return 3925
        def Replay(self): return self
        def BlockInvoke(self, fn): fn(controller)
    bridge._ctx = Context()
    controller.SetFrameEvent(3925, True)
    texture = next(t for t in controller.GetTextures() if t.width > 1 and t.height > 1 and t.depth == 1 and t.msSamp == 1)
    buffer = next(b for b in controller.GetBuffers() if b.length >= 64)
    queries = [
        ('get_textures', {}), ('get_buffers', {}), ('get_resources', {}),
        ('get_pipeline_state', {'event_id':3925}), ('get_bound_textures', {'event_id':3925}),
        ('get_texture_info', {'resource_id':int(texture.resourceId)}),
        ('get_texture_data', {'resource_id':int(texture.resourceId)}),
        ('get_buffer_data', {'resource_id':int(buffer.resourceId),'length':64}),
        ('pick_pixel', {'resource_id':int(texture.resourceId),'x':0,'y':0}),
        ('find_by_resource', {'resource_id':int(texture.resourceId)}),
        ('get_debug_messages', {}), ('enumerate_counters', {}),
        ('get_action_timings', {'event_ids':[3925]})]
    for name, params in queries:
        response = bridge.handle_request({'id':name,'method':name,'params':params})
        if name == 'get_action_timings' and 'error' in response and 'Windows Developer Mode' in response['error']['message']:
            assert controller.GetFatalErrorStatus().OK()
            report['checks'].append('get_action_timings: developer-mode guard (no GPU counter execution)')
            continue
        assert 'error' not in response, response
        assert response['result'] is not None, name
        json.dumps(response)
        if name == 'get_texture_data':
            data = response['result']
            assert len(base64.b64decode(data['base64'], validate=True)) == data['returned_bytes']
        report['checks'].append(name)
    report['passed'] = controller.GetFatalErrorStatus().OK()
except Exception:
    report['error'] = traceback.format_exc()
finally:
    if controller: controller.Shutdown()
    if cap: cap.Shutdown()
with open(os.path.join(root,'build-early-exports/kiana-bridge-real.json'),'w') as f:
    json.dump(report,f,indent=2)
sys.exit(0)
