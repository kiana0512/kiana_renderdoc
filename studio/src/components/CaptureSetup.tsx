import { useEffect, useState } from 'react'
import { customCapture, gamePresets } from '../data/captureProfiles'
import type { CaptureCheck, CapturePreset, CaptureProject } from '../data/types'

export function CaptureSetup({ onClose, onLaunch }: { onClose: () => void; onLaunch: (project: CaptureProject) => Promise<void> }) {
  const [presets, setPresets] = useState<CapturePreset[]>(() => gamePresets('KianaCaptures'))
  const [presetId, setPresetId] = useState('zzz')
  const [project, setProject] = useState<CaptureProject>(() => gamePresets('KianaCaptures')[0])
  const [check, setCheck] = useState<CaptureCheck | null>(null)
  const [error, setError] = useState('')
  const [launching, setLaunching] = useState(false)
  const selected = presets.find(preset => preset.id === presetId)
  const choose = (preset: CapturePreset) => {
    let paths: Partial<CaptureProject> = {}
    try { paths = JSON.parse(localStorage.getItem(`kiana-game-path-v12-${preset.id}`) || '{}') } catch { /* use the preset */ }
    setPresetId(preset.id); setProject({ ...preset, executablePath: paths.executablePath || preset.executablePath, workingDirectory: paths.workingDirectory || preset.workingDirectory, captureDirectory: paths.captureDirectory || preset.captureDirectory }); setCheck(null); setError('')
  }
  useEffect(() => {
    let active = true
    void window.kiana?.getCapturePresets().then(items => { if (active && items.length) { setPresets(items); choose(items.find(item => item.detected) || items[0]) } }).catch(reason => { if (active) setError(String(reason)) })
    return () => { active = false }
  }, [])
  const set = <K extends keyof CaptureProject>(key: K, value: CaptureProject[K]) => { setProject(current => ({ ...current, [key]: value })); setCheck(null); setError('') }
  const browse = async (key: 'executablePath' | 'captureDirectory') => {
    try {
      const value = key === 'executablePath' ? await window.kiana?.selectExecutable() : await window.kiana?.selectDirectory()
      if (value) { set(key, value); if (key === 'executablePath') set('workingDirectory', value.replace(/[\\/][^\\/]+$/, '')) }
    } catch (reason) { setError(reason instanceof Error ? reason.message : String(reason)) }
  }
  const validate = async () => {
    if (!window.kiana) { setError('浏览器只能预览界面。请使用桌面版检查路径并启动游戏。'); return null }
    const value = await window.kiana.checkCapture(project); setCheck(value); return value
  }
  const launch = async () => {
    setLaunching(true); setError('')
    try {
      const value = await validate()
      if (!value?.ok) return
      localStorage.setItem(`kiana-game-path-v12-${presetId}`, JSON.stringify({ executablePath: project.executablePath, workingDirectory: project.workingDirectory, captureDirectory: project.captureDirectory }))
      await onLaunch(project)
    } catch (reason) { setError(reason instanceof Error ? reason.message : String(reason)) }
    finally { setLaunching(false) }
  }
  return <div className="modal-backdrop"><section className="capture-dialog artist-capture-dialog" role="dialog" aria-modal="true" aria-label="获取游戏画面"><header><b>获取游戏画面</b><button aria-label="关闭启动设置" onClick={onClose} disabled={launching}>×</button></header><div className="dialog-body">
    <p className="capture-intro">选择游戏 → 确认程序位置 → 启动后进入目标场景 → 截取当前画面。</p>
    <div className="capture-presets">{presets.map(preset => <button key={preset.id} aria-pressed={presetId === preset.id} className={presetId === preset.id ? 'selected' : ''} onClick={() => choose(preset)} disabled={launching}><span><b>{preset.name}</b><small>{preset.description}</small></span><em>{preset.detected ? '已找到程序' : '路径待确认'}</em></button>)}</div>
    <button className="text-action" onClick={() => { setPresetId('custom'); setProject({ ...customCapture, captureDirectory: presets[0]?.captureDirectory.replace(/[\\/][^\\/]+$/, '') || '' }); setCheck(null) }}>使用其他游戏 / 自定义配置</button>
    {selected && <p className="capture-note">{selected.limitation}</p>}
    <label>游戏程序的位置<div className="path-field"><input aria-label="游戏程序的位置" value={project.executablePath} onChange={event => set('executablePath', event.target.value)} /><button className="dcs-btn" onClick={() => void browse('executablePath')}>选择 EXE…</button></div><small>选择游戏程序；安装在其他目录时，请手动选择。</small></label>
    <label>画面保存到<div className="path-field"><input aria-label="画面保存到" value={project.captureDirectory} onChange={event => set('captureDirectory', event.target.value)} /><button className="dcs-btn" onClick={() => void browse('captureDirectory')}>选择文件夹…</button></div></label>
    <section className="capture-outcome"><b>启动之后做什么？</b><p>等游戏进入你要研究的场景，再点击工作台的“截取当前画面”。保存的是一帧绘制数据（RDC），不是录像。</p><p>先检查预览是否正确，再分析画面；默认不会在启动或下载画面上自动分析。</p></section>
    <details className="capture-advanced"><summary>高级设置（通常不需要修改）</summary>
      <label>项目名称<input value={project.name} onChange={event => set('name', event.target.value)} /></label>
      <label>工作目录<input value={project.workingDirectory} onChange={event => set('workingDirectory', event.target.value)} /></label>
      <div className="dialog-grid"><label>游戏引擎<select aria-label="游戏引擎" value={project.engine} onChange={event => { const engine = event.target.value as CaptureProject['engine']; set('engine', engine); set('profile', engine === 'unity' ? 'UnityD3D11Safe' : 'UnrealD3D12') }}><option value="unity">Unity</option><option value="unreal">Unreal</option></select></label><label>图形后端<select aria-label="图形后端" value={project.profile} onChange={event => set('profile', event.target.value as CaptureProject['profile'])}>{project.engine === 'unity' ? <><option value="UnityD3D11Safe">D3D11（推荐）</option><option value="UnityD3D12" disabled={presetId !== 'bh3' && presetId !== 'custom'}>D3D12（崩坏 3 已验证）</option></> : <option value="UnrealD3D12">D3D12</option>}</select></label><label>宽度<input type="number" value={project.resolutionWidth} onChange={event => set('resolutionWidth', Number(event.target.value))} /></label><label>高度<input type="number" value={project.resolutionHeight} onChange={event => set('resolutionHeight', Number(event.target.value))} /></label><label>窗口模式<select value={project.windowMode} onChange={event => set('windowMode', event.target.value as CaptureProject['windowMode'])}><option value="windowed">窗口</option><option value="borderless">无边框</option><option value="fullscreen">全屏</option></select></label></div>
      <label>附加启动参数<input value={project.arguments} onChange={event => set('arguments', event.target.value)} /></label>
      <div className="dialog-options">{([{ key: 'hookChildren', text: '跟踪游戏子进程' }, { key: 'preserveExportIdentity', text: '保留图形导出地址（崩铁 / 崩坏 3 / 原神）' }, { key: 'wrapOptedOutDevices', text: '启用设备包装（原神）' }, { key: 'referenceAllResources', text: '保留全部资源' }, { key: 'captureCallstacks', text: '记录调用栈' }, { key: 'allowFullscreen', text: '允许独占全屏' }, { key: 'elevate', text: '需要时以管理员权限启动' }, { key: 'manualCapture', text: '进入目标画面后手动截取' }, { key: 'autoAnalyze', text: '捕获后自动分析（使用所选引擎）' }] as const).map(option => <label key={option.key}><input type="checkbox" checked={project[option.key]} onChange={event => set(option.key, event.target.checked)} />{option.text}</label>)}</div>
      {!project.manualCapture && <label>自动截取帧号<input type="number" min="1" value={project.captureFrame} onChange={event => set('captureFrame', Number(event.target.value))} /></label>}
    </details>
    {check && <section className={check.ok ? 'capture-check ok' : 'workflow-error'} role="status"><b>{check.ok ? '设置检查通过，可以启动' : '请先修正以下设置'}</b>{check.problems.map(problem => <p key={problem}>{problem}</p>)}<details><summary>查看检查详情</summary><p>运行时：{check.runtimeDirectory}</p><code>{check.arguments.join(' ')}</code></details></section>}
    {error && <p className="workflow-error" role="alert">{error}</p>}
  </div><footer><button className="dcs-btn" disabled={launching} onClick={() => void validate().catch(reason => setError(String(reason)))}>检查设置</button><button className="dcs-btn" onClick={onClose} disabled={launching}>取消</button><button className="dcs-btn dcs-btn--primary" disabled={launching || !project.executablePath} onClick={() => void launch()}>{launching ? '检查并启动中…' : '启动游戏，准备截取'}</button></footer></section></div>
}
