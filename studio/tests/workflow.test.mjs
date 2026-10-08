import test from 'node:test'
import assert from 'node:assert/strict'
import { captureArguments, captureReady, gamePresets, knownEngine, splitArguments } from '../src/data/captureProfiles.ts'
import { emptyWorkspace, explainModule, workflowStep } from '../src/data/workflow.ts'

test('five presets preserve the validated launch and compatibility settings', () => {
  const presets = gamePresets('C:\\Captures', path => path === 'D:\\miHoYo Launcher\\games\\Genshin Impact Game\\YuanShen.exe')
  assert.equal(presets.length, 5)
  const genshin = presets.find(item => item.id === 'genshin')
  assert.equal(genshin.detected, true)
  assert.equal(genshin.preserveExportIdentity, true)
  assert.equal(genshin.wrapOptedOutDevices, true)
  assert.equal(genshin.hookChildren, false)
  assert.equal(presets.find(item => item.id === 'zzz').preserveExportIdentity, false)
  assert.equal(presets.find(item => item.id === 'wuthering').arguments, '-krqlv=hd')
  assert.ok(presets.every(item => item.manualCapture && !item.autoAnalyze && !item.elevate && !item.allowFullscreen))
})

test('backend switching keeps Unity independent of D3D12 and avoids duplicate flags', () => {
  const bh3 = gamePresets('C:\\Captures').find(item => item.id === 'bh3')
  const args = captureArguments({ ...bh3, profile: 'UnityD3D12', arguments: '-force-d3d11 -screen-width 1920 -screen-height 1080' })
  assert.equal(bh3.engine, 'unity')
  assert.ok(args.includes('-force-d3d12'))
  assert.ok(!args.includes('-force-d3d11'))
  assert.equal(args.filter(value => value === '-screen-width').length, 1)
  assert.equal(args[args.indexOf('-screen-width') + 1], '1280')
  assert.equal(knownEngine('C:/Captures/bh3/frame.rdc'), 'unity')
  assert.equal(knownEngine('C:/captures/unknown-D3D12.rdc'), undefined)
})

test('Windows argument parsing preserves quoted paths, empty arguments and escaped quotes', () => {
  assert.deepEqual(splitArguments(String.raw`-config "C:\Game Files\settings.json" "" -name "a\"b"`), ['-config', 'C:\\Game Files\\settings.json', '', '-name', 'a"b'])
  assert.throws(() => splitArguments('"unfinished'), /引号/)
})

test('live processes and launcher graphics do not arm capture before a ready target', () => {
  assert.equal(captureReady({ status: 'waiting_for_graphics', session_active: true, pid: 1, api: 'D3D11' }), false)
  assert.equal(captureReady({ status: 'waiting_for_capture', session_active: true, pid: 1, api: 'Unknown' }), false)
  assert.equal(captureReady({ status: 'waiting_for_capture', session_active: true, pid: 1, api: 'D3D11', capture_in_progress: true }), false)
  assert.equal(captureReady({ status: 'waiting_for_capture', session_active: true, pid: 1, api: 'D3D11' }), true)
  assert.equal(captureReady({ status: 'waiting_for_capture', session_active: false, pid: 1, api: 'D3D11' }), false)
})

test('the artist workflow advances only after real capture and analysis artifacts', () => {
  assert.equal(workflowStep(emptyWorkspace), 1)
  assert.equal(workflowStep({ ...emptyWorkspace, mode: 'demo', manifestPath: 'example.json' }), 1)
  assert.equal(workflowStep({ ...emptyWorkspace, mode: 'capture' }), 2)
  assert.equal(workflowStep({ ...emptyWorkspace, mode: 'capture', manifestPath: 'real.json' }), 3)
  assert.match(explainModule({ module: 'scene_geometry' }).meaning, /可能/)
  assert.equal(explainModule({ module: 'unknown' }).name, '用途待确认')
})
