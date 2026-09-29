import { app, BrowserWindow, clipboard, dialog, ipcMain, shell } from 'electron'
import { spawn, spawnSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import { cpSync, existsSync, mkdirSync, readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs'
import { connect as connectSocket } from 'node:net'
import { basename, dirname, extname, join, resolve } from 'node:path'
import { opaquePngPreview } from './opaquePng.js'

if (!app.isPackaged && process.env.KIANA_CDP_PORT) {
  app.commandLine.appendSwitch('remote-debugging-address', '127.0.0.1')
  app.commandLine.appendSwitch('remote-debugging-port', process.env.KIANA_CDP_PORT)
}

const packagedDriveRoot = resolve(dirname(process.execPath), '..', '..', '..')
const runtimeCandidates = [
  join(process.resourcesPath, 'kiana-runtime'),
  process.env.KIANA_HOME,
  join(packagedDriveRoot, 'KianaRenderDoc', 'x64', 'Development'),
  resolve(process.cwd(), '..', 'KianaRenderDoc', 'x64', 'Development'),
  join(process.env.LOCALAPPDATA || '', 'Kiana RenderDoc'),
].filter((value): value is string => Boolean(value))
const kianaRoot = runtimeCandidates.find(value => existsSync(join(value, 'kiana_renderdoccmd.exe'))) || runtimeCandidates[0]
const sourceHomeCandidates = [
  process.env.KIANA_SOURCE_HOME,
  join(kianaRoot, 'kiana'),
  'E:\\renderdoc\\kiana',
  resolve(process.cwd(), '..', 'renderdoc', 'kiana'),
  kianaRoot,
].filter((value): value is string => Boolean(value))
const kianaHome = sourceHomeCandidates.find(value => existsSync(join(value, 'mcp', 'src', 'server.py'))) || kianaRoot
const kianaSourceRoot = basename(kianaHome).toLowerCase() === 'kiana' ? dirname(kianaHome) : kianaHome
const commandPath = join(kianaRoot, 'kiana_renderdoccmd.exe')
const guiPath = join(kianaRoot, 'kiana_qrenderdoc.exe')
// 打包机 venv 可能仍指向 C:\Python314；存在 python.exe 不代表它能启动。
const pythonCandidates = [
  process.env.KIANA_PYTHON,
  join(kianaRoot, 'python_mcp', 'python.exe'),
  join(process.env.LOCALAPPDATA || '', 'Kiana RenderDoc', 'python_mcp', 'python.exe'),
  join(kianaSourceRoot, '.venv', 'Scripts', 'python.exe'),
].filter((value): value is string => Boolean(value))
const pythonPath = pythonCandidates.find(value => {
  if (!existsSync(value)) return false
  return spawnSync(value, ['-c', 'import mcp'], { windowsHide: true, timeout: 8000, encoding: 'utf8' }).status === 0
}) || pythonCandidates[0]
const workerCandidates = [join(kianaHome, 'mcp', 'src', 'native_job.py'), join(kianaRoot, 'mcp', 'src', 'native_job.py')]
const workerPath = workerCandidates.find(existsSync) || workerCandidates[0]
const captureJobCandidates = [join(kianaHome, 'mcp', 'src', 'capture_job.py'), join('E:\\renderdoc\\kiana', 'mcp', 'src', 'capture_job.py')]
const captureJobPath = captureJobCandidates.find(existsSync) || captureJobCandidates[0]
const unityCliCandidates = [
  process.env.KIANA_UNITY_CLI,
  join(process.env.LOCALAPPDATA || '', 'Unity', 'bin', 'unity.exe'),
].filter((value): value is string => Boolean(value))
const unityCliPath = unityCliCandidates.find(existsSync) || unityCliCandidates[0]
const unityProjectCandidates = [
  process.env.KIANA_UNITY_PROJECT,
  'E:\\KianaFrame38112Workspace\\KianaFrame38112Unity',
  'F:\\KianaFrame38112Unity',
].filter((value): value is string => Boolean(value))
const defaultUnityProject = unityProjectCandidates.find(existsSync) || unityProjectCandidates[0]
const defaultCapture = process.env.KIANA_DEFAULT_CAPTURE || 'E:\\renderdoc\\test-results.rdc'
const defaultManifest = process.env.KIANA_DEFAULT_MANIFEST || 'E:\\renderdoc\\test-results\\wuthering-reconstruction-package-v2\\reconstruction-manifest.json'
const defaultThumbnail = join(process.env.LOCALAPPDATA || '', 'Kiana Studio', 'thumbnails', 'FAA43D3CD2698F38FFFC.jpg')
const maxProcessOutput = 8 * 1024 * 1024

const displayNames: Record<string, string> = {
  scene_geometry: '场景几何 / G-buffer', sky_atmosphere: '天空 / 大气 / 体积', depth_shadow: '深度 / 阴影',
  transparent_effects: '透明 / 特效', post_process: '后处理', compute_post: '计算着色', ui: 'UI 合成', auxiliary: '辅助阶段',
}

function ensureFile(filePath: string, label: string) {
  if (!existsSync(filePath) || !statSync(filePath).isFile()) throw new Error(`${label}不存在：${filePath}`)
}

function parseJsonOutput(value: string) {
  const text = String(value || '').trim()
  if (!text) return {}
  try { return JSON.parse(text) } catch { /* Some helpers print a diagnostic before their JSON result. */ }
  const lines = text.split(/\r?\n/).map(line => line.trim()).filter(Boolean)
  for (let index = lines.length - 1; index >= 0; index -= 1) {
    try { return JSON.parse(lines[index]) } catch { /* Continue to the previous complete line. */ }
  }
  throw new Error('运行时返回的 JSON 无法解析')
}

function pythonEnvironment(extra: NodeJS.ProcessEnv = {}) {
  // Kiana 运行目录带有 Python 3.6 的 _ctypes.pyd；把根目录放进 PYTHONPATH
  // 会覆盖 MCP Python 3.14 的标准库并导致服务启动后导入 uvicorn 失败。
  return { ...process.env, ...extra, KIANA_HOME: kianaHome, PYTHONUTF8: '1' }
}

function resolveManifestArtifact(value: unknown, manifestPath: string) {
  const original = String(value || '')
  if (!original || existsSync(original)) return original
  const normalized = original.replace(/\//g, '\\')
  const lower = normalized.toLowerCase()
  for (const marker of ['\\analysis\\', '\\evidence\\', '\\geometry\\', '\\character-current-pose\\', '\\contract-v1\\']) {
    const offset = lower.lastIndexOf(marker)
    if (offset < 0) continue
    const candidate = join(dirname(manifestPath), normalized.slice(offset + 1))
    if (existsSync(candidate)) return candidate
  }
  return original
}

function resource(value: Record<string, unknown>, output: boolean) {
  const number = (key: string) => Number(value[key] || 0)
  const text = (key: string) => String(value[key] || '')
  return {
    resourceId: number('resourceId') || number('id'),
    name: output ? text('name') : text('texName') || text('name'), slot: output ? 'RT' : `t${number('slot')}`,
    role: output ? 'output' : text('role'), format: text('fmt') || text('format'),
    width: output ? number('w') : number('width'), height: output ? number('h') : number('height'),
  }
}

function parseManifest(manifestPath: string) {
  ensureFile(manifestPath, '分析清单')
  const root = JSON.parse(readFileSync(manifestPath, 'utf8')) as Record<string, any>
  const coverage = root.coverage || {}
  const reportPath = join(dirname(manifestPath), 'analysis', 'render-reconstruction-report.json')
  const report = existsSync(reportPath) ? JSON.parse(readFileSync(reportPath, 'utf8')) : { passes: [] }
  const reportPasses = new Map<number, Record<string, any>>((report.passes || []).map((item: Record<string, any>) => [Number(item.number || 0), item]))
  const actionIndexPath = join(dirname(manifestPath), 'action-index.json')
  const actionIndex = existsSync(actionIndexPath) ? JSON.parse(readFileSync(actionIndexPath, 'utf8')) : { actions: [] }
  const indexedActions = (actionIndex.actions || []) as Record<string, any>[]
  const assetGraph = root.asset_graph || {}
  const contract = root.reconstruction_contract || {}
  const reverseWorkflow = root.ai_reverse_workflow || {}
  return {
    manifestPath,
    packageDirectory: dirname(manifestPath),
    coverage: {
      passes: Number(coverage.passes || 0), modules: Number(coverage.modules || 0), indexedActions: Number(coverage.indexed_actions || 0),
      geometryExports: Number(coverage.geometry_exports || 0), evidenceExports: Number(coverage.evidence_exports || 0), frameDraws: Number(coverage.frame_draws || 0),
    },
    assetGraph: {
      path: resolveManifestArtifact(assetGraph.path, manifestPath), objects: Number(assetGraph.objects || 0), materials: Number(assetGraph.materials || 0),
      shaders: Number(assetGraph.shaders || 0), textures: Number(assetGraph.textures || 0), classificationCounts: assetGraph.classification_counts || {},
      skinnedEventIds: assetGraph.skinned_event_ids || [], characterEventIds: assetGraph.character_event_ids || [], animation: assetGraph.animation || {},
    },
    reconstructionContract: {
      path: resolveManifestArtifact(contract.path, manifestPath), counts: contract.counts || {}, characterEventIds: contract.character_event_ids || [],
    },
    truthPolicy: root.truth_policy || {},
    reverseWorkflow: reverseWorkflow.path ? {
      path: resolveManifestArtifact(reverseWorkflow.path, manifestPath), status: String(reverseWorkflow.status || 'pending'), profile: String(reverseWorkflow.profile || ''),
      targetEngine: reverseWorkflow.target_engine === 'unreal' ? 'unreal' : 'unity', stages: reverseWorkflow.stages || [], skills: reverseWorkflow.skills || [],
      poseExports: { attempted: Number(reverseWorkflow.pose_exports?.attempted || 0), valid: Number(reverseWorkflow.pose_exports?.valid || 0), failed: Number(reverseWorkflow.pose_exports?.failed || 0), manifest: resolveManifestArtifact(reverseWorkflow.pose_exports?.manifest, manifestPath) },
      truth: reverseWorkflow.truth || {},
    } : undefined,
    modules: (root.modules || []).map((item: Record<string, any>) => {
      const reportPass = reportPasses.get(Number(item.pass_number || 0)) || {}
      const compute = item.module === 'compute_post'
      const eventStart = Number(item.event_range?.[0] || 0)
      const eventEnd = Number(item.event_range?.[1] || 0)
      const stagePrefix: Record<string, string> = {
        compute_post: '计算 / 着色', scene_geometry: 'G-buffer 几何', transparent_effects: '透明合成',
        post_process: '后处理合成', ui: 'UI 图标 / 状态', auxiliary: '光照 / 辅助', depth_shadow: '深度 / 阴影', sky_atmosphere: '天空 / 大气',
      }
      const declaredStages = new Map<number, Record<string, any>>((item.composition_stages || []).map((value: Record<string, any>) => [Number(value.event_id || value.eventId || 0), value]))
      const stageRows = indexedActions.filter(action => {
        const eventId = Number(action.eventId || 0); const flags = Number(action.flags || 0)
        return eventId >= eventStart && eventId <= eventEnd && Boolean((flags & 2) || (flags & 4) || (flags & 1048576) || (flags & 2097152) || (flags & 256))
      })
      const stages = stageRows.map((action, index) => {
        const eventId = Number(action.eventId || 0)
        const flags = Number(action.flags || 0)
        const declared = declaredStages.get(eventId) || {}
        const outputResourceIds = (action.outputs || []).map((value: unknown) => Number(typeof value === 'object' && value ? (value as Record<string, unknown>).resourceId || (value as Record<string, unknown>).id : value || 0)).filter((value: number) => value > 0)
        const kind = (flags & 256) ? 'present' : (flags & 2097152) ? 'copy' : (flags & 1048576) ? 'clear' : (flags & 4) ? 'dispatch' : 'draw'
        const special = eventId === 1610 ? '胸前透明衣料' : eventId === 1868 ? '角色透明叠加' : kind === 'clear' ? `${displayNames[item.module] || 'Pass'}起点 · 清屏` : kind === 'copy' ? '场景底图复制' : kind === 'present' ? '最终画面提交' : ''
        return {
          eventId, ordinal: index + 1, name: String(declared.name || declared.label || special || `${stagePrefix[item.module] || '合成步骤'} ${String(index + 1).padStart(2, '0')}`),
          sourceName: String(action.name || `Action ${index + 1}`), kind,
          semanticKind: String(declared.semantic_kind || declared.semanticKind || kind), bindingName: String(declared.binding_name || declared.bindingName || ''),
          boundTextures: (declared.bound_textures || declared.boundTextures || []).map((value: Record<string, unknown>) => resource(value, false)),
          numIndices: Number(action.numIndices || 0), numInstances: Number(action.numInstances || 0), outputResourceIds, previewPath: '',
        }
      })
      return ({
      module: item.module || 'auxiliary', displayName: displayNames[item.module] || '辅助阶段', confidence: Number(item.confidence || 0),
      passNumber: Number(item.pass_number || 0), passName: item.pass_name || '', eventStart,
      eventEnd, representativeEvent: Number(item.representative_event || reportPass.representative?.eventId || (compute ? item.event_range?.[1] : 0) || 0), drawCount: Number(item.draw_count || 0),
      dispatchCount: Number(item.dispatch_count || reportPass.dispatch_count || (compute ? 1 : 0)), actionKind: item.action_kind || reportPass.action_kind || (compute ? 'dispatch' : Number(item.draw_count || 0) ? 'draw' : 'none'),
      totalIndices: Number(item.total_indices || 0), vertexShader: Number(item.shader_ids?.vertex || 0), fragmentShader: Number(item.shader_ids?.fragment || 0), computeShader: Number(item.shader_ids?.compute || reportPass.pipeline?.shaders?.compute?.shaderId || 0),
      outputs: (item.outputs || []).map((value: Record<string, unknown>) => resource(value, true)),
      textures: (item.bound_textures || []).map((value: Record<string, unknown>) => resource(value, false)), reasons: item.reasons || [], missing: item.missing || [], previewPath: resolveManifestArtifact(reportPass.preview?.saved, manifestPath), stages,
    })}),
  }
}

function findManifest(capturePath: string) {
  const captureDirectory = dirname(capturePath)
  const captureStem = basename(capturePath, extname(capturePath)).toLowerCase()
  const frameToken = basename(capturePath).match(/frame[_-]?(\d+)/i)?.[1] || ''
  const candidates = [join(captureDirectory, 'reconstruction-manifest.json'), join(captureDirectory, 'analysis', 'reconstruction-manifest.json')]
  const captureCount = readdirSync(captureDirectory, { withFileTypes: true }).filter(entry => entry.isFile() && extname(entry.name).toLowerCase() === '.rdc').length
  for (const entry of readdirSync(captureDirectory, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue
    const name = entry.name.toLowerCase()
    const belongsToCapture = name.includes(captureStem) || Boolean(frameToken && new RegExp(`frame[_-]?${frameToken}(?:\\D|$)`, 'i').test(name))
    const unambiguousLegacyFolder = captureCount <= 1 && ['analysis', 'reconstruction'].includes(name)
    if (!belongsToCapture && !unambiguousLegacyFolder) continue
    candidates.push(join(captureDirectory, entry.name, 'reconstruction-manifest.json'))
  }
  return candidates.filter(existsSync).sort((left, right) => statSync(right).mtimeMs - statSync(left).mtimeMs)[0] || ''
}

function captureHistory() {
  const found = new Set<string>()
  const roots = new Set<string>(['E:\\KianaCaptures'])
  const remembered = loadWorkspace()
  if (remembered?.capturePath) roots.add(dirname(remembered.capturePath))
  const visit = (directory: string, depth: number) => {
    if (depth > 4 || found.size >= 200 || !existsSync(directory)) return
    let entries: any[] = []
    try { entries = readdirSync(directory, { withFileTypes: true }) } catch { return }
    for (const entry of entries) {
      if (found.size >= 200) break
      const path = join(directory, entry.name)
      if (entry.isDirectory()) visit(path, depth + 1)
      else if (entry.isFile() && extname(entry.name).toLowerCase() === '.rdc') found.add(resolve(path))
    }
  }
  for (const root of roots) visit(root, 0)
  return Array.from(found).map(capturePath => {
    const info = statSync(capturePath); const manifestPath = findManifest(capturePath)
    return { capturePath, captureName: basename(capturePath), captureBytes: info.size, frameNumber: inferFrameNumber(capturePath), modifiedAt: info.mtimeMs, manifestPath, analyzed: Boolean(manifestPath) }
  }).sort((left, right) => right.modifiedAt - left.modifiedAt)
}

function imageDataUrl(filePath: string, showRgbIgnoringAlpha = false) {
  if (!existsSync(filePath)) return ''
  const mime = extname(filePath).toLowerCase() === '.png' ? 'image/png' : 'image/jpeg'
  const raw = readFileSync(filePath)
  const image = showRgbIgnoringAlpha && mime === 'image/png' ? opaquePngPreview(raw) : raw
  return `data:${mime};base64,${image.toString('base64')}`
}

function inferFrameNumber(capturePath: string) {
  return Number(basename(capturePath).match(/frame[_-]?(\d+)/i)?.[1] || 0)
}

function workspace(capturePath = defaultCapture, manifestPath = '', thumbnailPath = defaultThumbnail, frameNumber = inferFrameNumber(capturePath)) {
  ensureFile(capturePath, 'RDC 文件')
  const parsed = manifestPath && existsSync(manifestPath) ? parseManifest(manifestPath) : {
    manifestPath: '', packageDirectory: dirname(capturePath),
    coverage: { passes: 0, modules: 0, indexedActions: 0, geometryExports: 0, evidenceExports: 0, frameDraws: 0 }, modules: [],
    assetGraph: { path: '', objects: 0, materials: 0, shaders: 0, textures: 0, classificationCounts: {}, skinnedEventIds: [], characterEventIds: [], animation: {} },
    reconstructionContract: { path: '', counts: {}, characterEventIds: [] }, truthPolicy: {}, reverseWorkflow: undefined,
  }
  const captureKey = capturePath.toLowerCase()
  return { ...parsed, mode: 'capture' as const, capturePath, captureName: basename(capturePath) || 'capture.rdc', captureBytes: statSync(capturePath).size, api: captureKey.includes('zzz') || captureKey.includes('zenlesszonezero') ? 'D3D11' : 'D3D12', frameNumber, thumbnailDataUrl: imageDataUrl(thumbnailPath) }
}

function ensureRuntimeExtension() {
  const source = join(kianaHome, 'extensions', 'kiana_bridge')
  const target = join(kianaRoot, 'extensions', 'kiana_bridge')
  if (existsSync(source) && resolve(source).toLowerCase() !== resolve(target).toLowerCase()) {
    cpSync(source, target, { recursive: true, force: true })
  }
  const configPath = join(process.env.APPDATA || '', 'kiana_qrenderdoc', 'UI.config')
  try {
    mkdirSync(dirname(configPath), { recursive: true })
    const config = existsSync(configPath) ? JSON.parse(readFileSync(configPath, 'utf8')) : {}
    const extensions = new Set<string>(Array.isArray(config.AlwaysLoad_Extensions) ? config.AlwaysLoad_Extensions : [])
    extensions.add('kiana_bridge'); config.AlwaysLoad_Extensions = Array.from(extensions)
    writeFileSync(configPath, JSON.stringify(config, null, 4), 'utf8')
  } catch { /* A malformed external UI config must not block Studio startup. */ }
}

function capturePresets() {
  const first = (values: string[]) => values.find(existsSync) || values[0]
  const wuthering = first([
    'G:\\Wuthering Waves\\Wuthering Waves Game\\Wuthering Waves.exe',
    'D:\\Wuthering Waves\\Wuthering Waves Game\\Wuthering Waves.exe',
    'E:\\Wuthering Waves\\Wuthering Waves Game\\Wuthering Waves.exe',
    'E:\\Wuthering Waves Game\\Wuthering Waves.exe',
  ])
  const zzz = first([
    'E:\\ZenlessZoneZero Game\\ZenlessZoneZero.exe',
    'D:\\miHoYo Launcher\\games\\ZenlessZoneZero Game\\ZenlessZoneZero.exe',
    'D:\\HoYoPlay\\games\\ZenlessZoneZero Game\\ZenlessZoneZero.exe',
  ])
  const captureRoot = existsSync('E:\\') ? 'E:\\KianaCaptures' : join(app.getPath('documents'), 'KianaCaptures')
  return [
    { id: 'wuthering', name: '鸣潮', description: 'UE5 · D3D12 · 4K · 子进程早期挂钩', executablePath: wuthering, workingDirectory: dirname(wuthering), captureDirectory: join(captureRoot, 'WutheringWaves'), arguments: '-krqlv=hd', profile: 'UnrealD3D12', hookChildren: true, referenceAllResources: false, captureCallstacks: false, allowFullscreen: true, captureFrame: 1200, resolutionWidth: 3840, resolutionHeight: 2160, windowMode: 'borderless', elevate: true, autoAnalyze: true, manualCapture: true, detected: existsSync(wuthering) },
    { id: 'zzz', name: '绝区零', description: 'Unity · D3D11 安全模式 · 4K · 已实机验证', executablePath: zzz, workingDirectory: dirname(zzz), captureDirectory: join(captureRoot, 'ZenlessZoneZero'), arguments: '-force-d3d11', profile: 'UnityD3D11Safe', hookChildren: true, referenceAllResources: false, captureCallstacks: false, allowFullscreen: false, captureFrame: 900, resolutionWidth: 3840, resolutionHeight: 2160, windowMode: 'borderless', elevate: true, autoAnalyze: true, manualCapture: true, detected: existsSync(zzz) },
  ]
}

function workspaceStatePath() { return join(app.getPath('userData'), 'last-workspace.json') }

function rememberWorkspace(capturePath: string, manifestPath: string, thumbnailPath: string) {
  mkdirSync(app.getPath('userData'), { recursive: true })
  writeFileSync(workspaceStatePath(), JSON.stringify({ capturePath, manifestPath, thumbnailPath }, null, 2), 'utf8')
}

function loadWorkspace() {
  if (existsSync(workspaceStatePath())) {
    try {
      const saved = JSON.parse(readFileSync(workspaceStatePath(), 'utf8')) as { capturePath?: string; manifestPath?: string; thumbnailPath?: string }
      if (saved.capturePath && existsSync(saved.capturePath)) return workspace(saved.capturePath, saved.manifestPath && existsSync(saved.manifestPath) ? saved.manifestPath : findManifest(saved.capturePath), saved.thumbnailPath || defaultThumbnail)
    } catch { /* An invalid recent-workspace record should not block startup. */ }
  }
  if (existsSync(defaultCapture)) return workspace(defaultCapture, existsSync(defaultManifest) ? defaultManifest : findManifest(defaultCapture), defaultThumbnail)
  return null
}

function run(executable: string, args: string[], env: NodeJS.ProcessEnv = process.env) {
  return new Promise<{ code: number; stdout: string; stderr: string }>((resolveRun, reject) => {
    const child = spawn(executable, args, { windowsHide: true, env })
    let stdout = ''; let stderr = ''
    const append = (current: string, value: Buffer) => (current + value.toString()).slice(-maxProcessOutput)
    const timeout = setTimeout(() => child.kill(), 120_000)
    child.stdout?.on('data', value => { stdout = append(stdout, value) })
    child.stderr?.on('data', value => { stderr = append(stderr, value) })
    child.once('error', error => { clearTimeout(timeout); reject(error) })
    child.once('close', code => { clearTimeout(timeout); resolveRun({ code: code ?? -1, stdout, stderr }) })
  })
}

function splitArguments(commandLine: string) {
  const result: string[] = []; let current = ''; let quoted = false
  for (const character of commandLine || '') {
    if (character === '"') { quoted = !quoted; continue }
    if (/\s/.test(character) && !quoted) { if (current) { result.push(current); current = '' } }
    else current += character
  }
  if (current) result.push(current)
  return result
}

function captureArguments(project: any) {
  const width = Math.max(640, Math.min(7680, Number(project.resolutionWidth) || 1280))
  const height = Math.max(480, Math.min(4320, Number(project.resolutionHeight) || 720))
  const mode = ['windowed', 'borderless', 'fullscreen'].includes(project.windowMode) ? project.windowMode : 'windowed'
  const values = splitArguments(String(project.arguments || ''))
  if (project.profile === 'UnityD3D11Safe') values.push('-screen-fullscreen', mode === 'fullscreen' ? '1' : '0', '-screen-width', String(width), '-screen-height', String(height), ...(mode === 'borderless' ? ['-popupwindow'] : []))
  else values.push(`-ResX=${width}`, `-ResY=${height}`, mode === 'fullscreen' ? '-fullscreen' : '-windowed', ...(mode === 'borderless' ? ['-borderless'] : []))
  return values
}

async function probeRuntime() {
  const probePort = (port: number) => new Promise<boolean>(resolvePort => {
    const socket = connectSocket({ host: '127.0.0.1', port })
    const done = (value: boolean) => { socket.destroy(); resolvePort(value) }
    socket.setTimeout(450); socket.once('connect', () => done(true)); socket.once('timeout', () => done(false)); socket.once('error', () => done(false))
  })
  const [renderdocMcp, ueMcp] = await Promise.all([probePort(8765), probePort(8011)])
  const unity = await probeUnity()
  const base = { desktop: true, connected: existsSync(commandPath) && existsSync(guiPath), bridgeConnected: false, engineMcp: renderdocMcp, engineMcpUrl: 'http://127.0.0.1:8765/mcp', renderdocMcp, renderdocMcpUrl: 'http://127.0.0.1:8765/mcp', ueMcp, ueMcpUrl: 'http://127.0.0.1:8011/mcp', unityMcp: unity.connected, unityPort: unity.port, unityProject: unity.project, unityVersion: unity.version, mcpTools: 0, bridgePid: 0, kianaRoot, sourceRoot: kianaSourceRoot, captureCore: existsSync(commandPath), inspector: existsSync(guiPath), python: existsSync(pythonPath), analysisWorker: existsSync(workerPath) }
  if (!base.python || !existsSync(join(kianaHome, 'mcp', 'src', 'ipc_client.py'))) return base
  const source = [
    'import json,sys',
    `sys.path.insert(0, ${JSON.stringify(join(kianaHome, 'mcp'))})`,
    'from src.ipc_client import IPCClient, instances',
    'from src.server import mcp',
    'active=instances()',
    'reply=IPCClient(timeout=2).call("ping",{},timeout=2)',
    'tools=len(mcp._tool_manager._tools)',
    'print(json.dumps({"active":active,"reply":reply,"tools":tools}))',
  ].join(';')
  try {
    const result = await run(pythonPath, ['-c', source], pythonEnvironment({ KIANA_PID: backendProcessPid ? String(backendProcessPid) : '' }))
    const data = parseJsonOutput(result.stdout)
    return { ...base, bridgeConnected: data.reply?.status === 'ok', mcpTools: Number(data.tools || 0), bridgePid: Number(data.reply?.pid || 0) }
  } catch { return base }
}

async function probeUnity() {
  const offline = { connected: false, port: 0, project: defaultUnityProject || '', version: '' }
  if (!unityCliPath || !existsSync(unityCliPath)) return offline
  try {
    const result = await run(unityCliPath, ['--format', 'json', 'status'])
    if (result.code !== 0) return offline
    const payload = parseJsonOutput(result.stdout)
    const instances = Array.isArray(payload?.data?.instances) ? payload.data.instances : []
    const target = instances.find((item: any) => resolve(String(item.project || '')).toLowerCase() === resolve(defaultUnityProject || '').toLowerCase()) || instances[0]
    if (!target || target.state !== 'ready') return offline
    return { connected: true, port: Number(target.port || 0), project: String(target.project || defaultUnityProject || ''), version: String(target.version || '') }
  } catch { return offline }
}

async function callUnity(command: string, params: Record<string, unknown> = {}, projectPath = defaultUnityProject, timeout = 120) {
  if (!/^[a-z][a-z0-9_]{1,63}$/.test(command)) throw new Error('无效的 Unity Pipeline 命令')
  if (!unityCliPath || !existsSync(unityCliPath)) throw new Error('未找到 Unity CLI')
  if (!projectPath || !existsSync(projectPath)) throw new Error(`Unity 工程不存在：${projectPath || '未配置'}`)
  const args = ['--format', 'json', 'command', command]
  if (command === 'eval' && typeof params.code === 'string') args.push(params.code)
  for (const [key, value] of Object.entries(params)) {
    if (key === 'code' && command === 'eval') continue
    if (!/^[a-z][a-z0-9_]{0,63}$/.test(key) || value === undefined || value === null || value === false) continue
    args.push(`--${key}`)
    if (value !== true) args.push(typeof value === 'string' ? value : JSON.stringify(value))
  }
  args.push('--project-path', resolve(projectPath), '--timeout', String(Math.max(1, Math.min(600, timeout))))
  const result = await run(unityCliPath, args)
  if (result.code !== 0) throw new Error(result.stderr || `Unity Pipeline 命令 ${command} 失败`)
  return parseJsonOutput(result.stdout)
}

let backendProcessPid = 0
let backendCapturePath = ''
function ensureHeadlessBackend() {
  if (backendProcessPid || !existsSync(guiPath)) return
  ensureRuntimeExtension()
  const child = spawn(guiPath, [], { detached: true, windowsHide: true, env: { ...process.env, KIANA_HOME: kianaHome, PYTHONUTF8: '1' } })
  backendProcessPid = child.pid || 0
  child.once('exit', () => { if (backendProcessPid === child.pid) { backendProcessPid = 0; backendCapturePath = '' } })
  child.unref()
}

let engineMcpProcess: ReturnType<typeof spawn> | null = null
function ensureEngineMcpServer() {
  if (engineMcpProcess || !existsSync(pythonPath) || !existsSync(join(kianaHome, 'mcp', 'src', 'launch_http.py'))) return
  const launcher = join(kianaHome, 'mcp', 'src', 'launch_http.py')
  const child = spawn(pythonPath, [launcher, '--port', '8765'], {
    // RenderDoc's runtime root contains python36.dll. Keeping it out of the
    // process CWD prevents Windows DLL search from shadowing Python 3.14's DLLs.
    cwd: dirname(pythonPath), windowsHide: true,
    env: pythonEnvironment({ KIANA_PID: backendProcessPid ? String(backendProcessPid) : '' }),
  })
  engineMcpProcess = child
  child.once('exit', () => { if (engineMcpProcess === child) engineMcpProcess = null })
  child.unref()
}

async function callRenderdoc(method: string, params: Record<string, unknown> = {}, timeout = 120) {
  if (!/^[a-z][a-z0-9_]{1,63}$/.test(method)) throw new Error('无效的 RenderDoc API 名称')
  ensureHeadlessBackend()
  const source = [
    'import json,sys',
    `sys.path.insert(0, ${JSON.stringify(join(kianaHome, 'mcp'))})`,
    'from src.ipc_client import IPCClient',
    `reply=IPCClient(timeout=${timeout}).call(${JSON.stringify(method)},json.loads(${JSON.stringify(JSON.stringify(params))}),timeout=${timeout})`,
    'print(json.dumps(reply,ensure_ascii=False))',
  ].join(';')
  let lastError = ''
  for (let attempt = 0; attempt < 24; attempt += 1) {
    const result = await run(pythonPath, ['-c', source], pythonEnvironment({ KIANA_PID: backendProcessPid ? String(backendProcessPid) : '' }))
    if (result.code === 0) return parseJsonOutput(result.stdout)
    lastError = result.stderr || `RenderDoc API ${method} 调用失败`
    const starting = /Active PIDs:\s*\[\]|No Kiana GUI|did not start|not ready/i.test(lastError)
    if (!starting || attempt === 23) break
    await new Promise(resolveDelay => setTimeout(resolveDelay, 500))
  }
  throw new Error(lastError || `RenderDoc API ${method} 调用失败`)
}

async function openCaptureInBackend(capturePath: string) {
  for (let attempt = 0; attempt < 12; attempt += 1) {
    try { await callRenderdoc('open_capture', { capture_path: capturePath }, 180); backendCapturePath = resolve(capturePath); return } catch {
      if (attempt < 11) await new Promise(resolveDelay => setTimeout(resolveDelay, 1000))
    }
  }
}

async function createThumbnail(capturePath: string) {
  const cache = join(app.getPath('userData'), 'thumbnails'); mkdirSync(cache, { recursive: true })
  const thumbnail = join(cache, `${createHash('sha256').update(capturePath).digest('hex').slice(0, 20)}.jpg`)
  const result = await run(commandPath, ['thumb', '--out', thumbnail, '--format', 'jpg', '--max-size', '2560', capturePath])
  if (result.code !== 0) throw new Error(result.stderr || '无法生成 RDC 预览')
  return thumbnail
}

function createWindow() {
  const window = new BrowserWindow({
    width: 1680, height: 1050, minWidth: 1180, minHeight: 720, show: false, frame: false, backgroundColor: '#0a0e13',
    icon: app.isPackaged ? process.execPath : join(__dirname, '../../build/icon.ico'),
    webPreferences: { preload: join(__dirname, '../preload/index.cjs'), nodeIntegration: false, contextIsolation: true, sandbox: true },
  })
  window.webContents.setWindowOpenHandler(() => ({ action: 'deny' }))
  window.webContents.on('will-navigate', event => event.preventDefault())
  window.webContents.session.setPermissionRequestHandler((_webContents, _permission, callback) => callback(false))
  window.once('ready-to-show', () => window.show())
  if (process.env.ELECTRON_RENDERER_URL) window.loadURL(process.env.ELECTRON_RENDERER_URL)
  else window.loadFile(join(__dirname, '../renderer/index.html'))
  return window
}

type CaptureSession = { output: string; pid: number; targetPid: number; executable?: string; triggered: boolean; processed: Set<string>; processing: boolean; monitoring?: boolean }

let activeCaptureSession: CaptureSession | null = null
const captureSessions = new Map<string, CaptureSession>()

function readCaptureState(output: string): any | null {
  const statePath = join(output, 'direct-capture-result.json')
  if (!existsSync(statePath)) return null
  try { return JSON.parse(readFileSync(statePath, 'utf8')) } catch { return null }
}

function isProcessAlive(pidValue: unknown): boolean {
  const pid = Number(pidValue || 0)
  if (!Number.isInteger(pid) || pid <= 0) return false
  if (process.platform === 'win32') {
    const result = spawnSync('tasklist.exe', ['/FI', `PID eq ${pid}`, '/FO', 'CSV', '/NH'], { encoding: 'utf8', windowsHide: true })
    return result.status === 0 && new RegExp(`"${pid}"(?:,|$)`).test(String(result.stdout || ''))
  }
  try { process.kill(pid, 0); return true } catch { return false }
}

function captureTriggerPending(session: CaptureSession, state: any): boolean {
  if (state?.capture_in_progress) return true
  if (!session.triggered) return false
  try {
    const trigger = JSON.parse(readFileSync(join(session.output, 'trigger-capture.json'), 'utf8'))
    return !trigger.id || String(state?.last_trigger_id || '') !== String(trigger.id)
  } catch { return false }
}

let analysisQueue: Promise<void> = Promise.resolve()
let queuedAnalyses = 0

function enqueueAnalysisJob(capturePath: string, output: string, engine: 'unity' | 'unreal', maxGeometry: number, maxCharacterPoses: number, onProgress: (percent: number, message: string) => void) {
  queuedAnalyses += 1
  const position = queuedAnalyses
  if (position > 1) onProgress(0, `已加入分析队列 · 前方 ${position - 1} 个任务`)
  const runJob = async () => {
    onProgress(1, '分析 Worker 已启动')
    const workerSource = readFileSync(workerPath, 'utf8')
    const workerArgs = [workerPath, '--capture', capturePath, '--output', output, '--engine', engine, '--max-geometry', String(maxGeometry)]
    if (workerSource.includes('"--ai-auto"') || workerSource.includes("'--ai-auto'")) workerArgs.push('--ai-auto')
    if (workerSource.includes('"--max-character-poses"') || workerSource.includes("'--max-character-poses'")) workerArgs.push('--max-character-poses', String(maxCharacterPoses))
    const child = spawn(pythonPath, workerArgs, { cwd: kianaSourceRoot, windowsHide: true, env: pythonEnvironment({ KIANA_PID: backendProcessPid ? String(backendProcessPid) : '' }) })
    let buffer = ''; let stderr = ''; let manifestPath = ''
    child.stderr.on('data', value => { stderr = (stderr + value.toString()).slice(-maxProcessOutput) })
    child.stdout.on('data', value => {
      buffer += value.toString(); const lines = buffer.split(/\r?\n/); buffer = lines.pop() || ''
      for (const line of lines) try { const message = JSON.parse(line); if (message.type === 'progress') onProgress(Number(message.percent || 0), String(message.message || '正在分析')); if (message.type === 'result') manifestPath = resolve(message.manifest) } catch { /* ignore malformed worker diagnostics */ }
    })
    const code = await new Promise<number>(resolveCode => child.once('close', value => resolveCode(value ?? -1)))
    if (code !== 0 || !manifestPath) throw new Error(stderr || '分析进程没有生成重建清单')
    return manifestPath
  }
  const job = analysisQueue.catch(() => undefined).then(runJob)
  analysisQueue = job.then(() => undefined, () => undefined).finally(() => { queuedAnalyses = Math.max(0, queuedAnalyses - 1) })
  return job
}

function discoverLiveCaptureSession(executable?: string): CaptureSession | null {
  const wanted = executable ? resolve(executable).toLowerCase() : ''
  const candidates: Array<{ session: CaptureSession; modified: number }> = []
  for (const session of captureSessions.values()) {
    const state = readCaptureState(session.output)
    const targetPid = Number(state?.pid || session.targetPid || 0)
    if (!state || state.session_active === false || !isProcessAlive(targetPid)) continue
    const stateExecutable = String(state.executable || session.executable || '').toLowerCase()
    if (wanted && stateExecutable !== wanted) continue
    candidates.push({ session: { ...session, targetPid: Number(state.pid || session.targetPid || 0) }, modified: statSync(join(session.output, 'direct-capture-result.json')).mtimeMs })
  }
  const roots = ['E:\\KianaCaptures', join(app.getPath('documents'), 'KianaCaptures')]
  const visit = (directory: string, depth: number) => {
    if (!existsSync(directory) || depth > 2) return
    const state = readCaptureState(directory)
    if (state && state.session_active !== false && isProcessAlive(state.pid)) {
      const stateExecutable = String(state.executable || '').toLowerCase()
      if (!wanted || stateExecutable === wanted) {
        const known = captureSessions.get(directory)
        candidates.push({ session: known || { output: directory, pid: 0, targetPid: Number(state.pid || 0), executable: String(state.executable || ''), triggered: Boolean(state.capture_in_progress), processed: new Set<string>((state.captures || []).map(String)), processing: false }, modified: statSync(join(directory, 'direct-capture-result.json')).mtimeMs })
      }
    }
    if (depth === 2) return
    for (const entry of readdirSync(directory, { withFileTypes: true })) if (entry.isDirectory()) visit(join(directory, entry.name), depth + 1)
  }
  for (const root of roots) visit(root, 0)
  candidates.sort((a, b) => b.modified - a.modified)
  const selected = candidates[0]?.session || null
  if (selected) { captureSessions.set(selected.output, selected); activeCaptureSession = selected }
  return selected
}

// 同一工作台只保留一个回放后端，避免重复启动把 16 GB 显存占满。
const primaryInstance = app.requestSingleInstanceLock()
if (!primaryInstance) app.quit()
else app.on('second-instance', () => {
  const active = BrowserWindow.getAllWindows()[0]
  if (active) { if (active.isMinimized()) active.restore(); active.focus() }
})

if (primaryInstance) app.whenReady().then(() => {
  ensureRuntimeExtension()
  ensureHeadlessBackend()
  ensureEngineMcpServer()
  const window = createWindow()
  ipcMain.handle('workspace:load', () => { const value = loadWorkspace(); if (value) void openCaptureInBackend(value.capturePath); return value })
  ipcMain.handle('workspace:history', () => captureHistory())
  ipcMain.handle('workspace:open-capture', async (_event, value: string) => {
    const capturePath = resolve(String(value || '')); ensureFile(capturePath, 'RDC 文件')
    const manifestPath = findManifest(capturePath)
    const cache = join(app.getPath('userData'), 'thumbnails'); mkdirSync(cache, { recursive: true })
    const thumbnail = join(cache, `${createHash('sha256').update(capturePath).digest('hex').slice(0, 20)}.jpg`)
    if (!existsSync(thumbnail)) await createThumbnail(capturePath)
    rememberWorkspace(capturePath, manifestPath, thumbnail); void openCaptureInBackend(capturePath)
    return workspace(capturePath, manifestPath, thumbnail)
  })
  ipcMain.handle('dialog:select-rdc', async () => {
    const result = await dialog.showOpenDialog(window, { properties: ['openFile'], filters: [{ name: 'RenderDoc Capture', extensions: ['rdc'] }] })
    if (result.canceled || !result.filePaths[0]) return null
    const capturePath = resolve(result.filePaths[0]); ensureFile(capturePath, 'RDC 文件')
    ensureFile(commandPath, 'Kiana 捕获核心')
    const thumbnail = await createThumbnail(capturePath)
    const manifestPath = findManifest(capturePath)
    rememberWorkspace(capturePath, manifestPath, thumbnail)
    void openCaptureInBackend(capturePath)
    return workspace(capturePath, manifestPath, thumbnail)
  })
  ipcMain.handle('dialog:select-executable', async () => {
    const result = await dialog.showOpenDialog(window, { properties: ['openFile'], filters: [{ name: 'Windows Executable', extensions: ['exe'] }] })
    return result.canceled ? null : result.filePaths[0] || null
  })
  ipcMain.handle('dialog:select-directory', async () => {
    const result = await dialog.showOpenDialog(window, { properties: ['openDirectory', 'createDirectory'] })
    return result.canceled ? null : result.filePaths[0] || null
  })
  ipcMain.handle('analysis:run', async (event, request: { capturePath: string; outputDirectory: string; engine: string; maxGeometry: number; maxCharacterPoses?: number }) => {
    ensureFile(resolve(request.capturePath), 'RDC 文件'); ensureFile(pythonPath, 'Kiana Python'); ensureFile(workerPath, 'Kiana 分析进程')
    const output = resolve(request.outputDirectory)
    const manifestPath = await enqueueAnalysisJob(resolve(request.capturePath), output, request.engine === 'unity' ? 'unity' : 'unreal', Math.max(1, Math.min(32, Number(request.maxGeometry) || 32)), Math.max(1, Math.min(64, Number(request.maxCharacterPoses) || 32)), (percent, message) => { if (!event.sender.isDestroyed()) event.sender.send('analysis:progress', { percent, message }) })
    event.sender.send('analysis:progress', { percent: 100, message: '重建包已生成', done: true })
    const capturePath = resolve(request.capturePath); const resolvedManifest = resolve(manifestPath)
    const thumbnail = join(app.getPath('userData'), 'thumbnails', `${createHash('sha256').update(capturePath).digest('hex').slice(0, 20)}.jpg`)
    rememberWorkspace(capturePath, resolvedManifest, thumbnail)
    void openCaptureInBackend(capturePath)
    return workspace(capturePath, resolvedManifest, thumbnail)
  })
  ipcMain.handle('capture:presets', () => capturePresets())
  ipcMain.handle('capture:recover', () => {
    const session = discoverLiveCaptureSession()
    if (!session) return null
    const state = readCaptureState(session.output)
    const targetPid = Number(state?.pid || session.targetPid || 0)
    if (!state || state.session_active === false || !isProcessAlive(targetPid)) {
      captureSessions.delete(session.output)
      if (activeCaptureSession?.output === session.output) activeCaptureSession = null
      return null
    }
    const executablePath = String(state.executable || session.executable || '')
    const preset = capturePresets().find(item => resolve(String(item.executablePath || '')).toLowerCase() === resolve(executablePath).toLowerCase())
    const api = [...(state.messages || [])].reverse().find((item: any) => item?.api)?.api || 'Unknown'
    return { phase: state.capture_in_progress ? 'capturing' : 'capturing', percent: state.capture_in_progress ? 48 : 28, message: state.capture_in_progress ? '已触发当前帧，等待 RDC 写入' : `已恢复实时连接 · PID ${state.pid || session.targetPid || '—'} · 可截取当前游戏帧`, projectName: preset?.name || basename(executablePath, extname(executablePath)) || '实时捕获会话', executablePath, outputDirectory: session.output, targetPid: Number(state.pid || session.targetPid || 0), api, sessionActive: true, presetId: preset?.id || '' }
  })
  ipcMain.handle('capture:launch', async (event, project: any) => {
    const executable = resolve(String(project.executablePath || '')); ensureFile(executable, '游戏可执行文件'); ensureFile(pythonPath, 'Kiana Python'); ensureFile(captureJobPath, 'Kiana 捕获进程')
    const working = project.workingDirectory ? resolve(project.workingDirectory) : dirname(executable)
    const parent = resolve(project.captureDirectory || join(working, 'KianaCaptures')); mkdirSync(parent, { recursive: true })
    const existingSession = discoverLiveCaptureSession(executable)
    if (existingSession) {
      const state = readCaptureState(existingSession.output) || {}
      const sessionMeta = { projectName: String(project.name || basename(executable)), executablePath: executable, outputDirectory: existingSession.output, targetPid: Number(state.pid || existingSession.targetPid || 0), api: [...(state.messages || [])].reverse().find((item: any) => item?.api)?.api || (project.profile === 'UnityD3D11Safe' ? 'D3D11' : 'D3D12') }
      const send = (value: Record<string, unknown>) => { if (!event.sender.isDestroyed()) event.sender.send('capture:progress', { ...sessionMeta, ...value }) }
      event.sender.send('capture:progress', { phase: 'capturing', percent: 28, message: `已恢复实时连接 · PID ${state.pid || existingSession.targetPid || '—'} · 点击“截取当前游戏帧”`, projectName: String(project.name || basename(executable)), executablePath: executable, outputDirectory: existingSession.output, targetPid: Number(state.pid || existingSession.targetPid || 0), api: [...(state.messages || [])].reverse().find((item: any) => item?.api)?.api || (project.profile === 'UnityD3D11Safe' ? 'D3D11' : 'D3D12'), sessionActive: true })
      if (existingSession.monitoring) return { pid: existingSession.pid, targetPid: Number(state.pid || existingSession.targetPid || 0), logPath: join(existingSession.output, 'direct-capture-result.json'), outputDirectory: existingSession.output, recovered: true }
      existingSession.monitoring = true
      const recoveredTimer = setInterval(() => {
        const next = readCaptureState(existingSession.output)
        if (!next) return
        existingSession.targetPid = Number(next.pid || existingSession.targetPid || 0)
        if (next.session_active === false || !isProcessAlive(existingSession.targetPid)) { clearInterval(recoveredTimer); existingSession.monitoring = false; captureSessions.delete(existingSession.output); if (activeCaptureSession?.output === existingSession.output) activeCaptureSession = null; send({ phase: 'failed', percent: 0, message: '目标游戏已退出，实时捕获会话结束', error: 'target_disconnected', sessionActive: false }); return }
        if (next.capture_in_progress) send({ phase: 'capturing', percent: 48, message: '已触发当前帧，等待 RDC 写入', sessionActive: true })
        else if (!existingSession.processing && !captureTriggerPending(existingSession, next)) { existingSession.triggered = false; send({ phase: 'capturing', percent: 28, message: `实时连接成功 · PID ${existingSession.targetPid} · 点击“截取当前游戏帧”`, sessionActive: true }) }
        for (const value of next.captures || []) {
          const capturePath = resolve(String(value))
          if (existingSession.processed.has(capturePath) || !existsSync(capturePath)) continue
          existingSession.processed.add(capturePath); existingSession.processing = true
          void (async () => {
            try {
              send({ phase: 'verifying', percent: 62, message: 'RDC 已写入，正在生成帧预览', sessionActive: true })
              const thumbnail = await createThumbnail(capturePath)
              rememberWorkspace(capturePath, '', thumbnail)
              send({ phase: 'complete', percent: 100, message: project.autoAnalyze ? '当前帧已保存并加入分析队列' : '当前帧已保存', done: true, capturePath, workspace: workspace(capturePath, '', thumbnail), sessionActive: true })
              let manifestPath = ''
              if (project.autoAnalyze) {
                const analysisOutput = join(existingSession.output, `analysis-frame${inferFrameNumber(capturePath) || Date.now()}`)
                manifestPath = await enqueueAnalysisJob(capturePath, analysisOutput, project.profile === 'UnityD3D11Safe' ? 'unity' : 'unreal', 12, 12, (percent, message) => send({ phase: 'analyzing', percent: Math.max(1, percent), message, sessionActive: true }))
              }
              if (manifestPath) { rememberWorkspace(capturePath, manifestPath, thumbnail); send({ phase: 'complete', percent: 100, message: '当前帧自动分析完成', done: true, capturePath, workspace: workspace(capturePath, manifestPath, thumbnail), sessionActive: true }) }
            } catch (error) { send({ phase: 'failed', percent: 0, message: error instanceof Error ? error.message : '实时帧处理失败', error: error instanceof Error ? error.message : String(error), sessionActive: true }) }
            finally { existingSession.processing = false; existingSession.triggered = false }
          })()
        }
      }, 900)
      return { pid: existingSession.pid, targetPid: Number(state.pid || existingSession.targetPid || 0), logPath: join(existingSession.output, 'direct-capture-result.json'), outputDirectory: existingSession.output, recovered: true }
    }
    const output = join(parent, `${String(project.name || 'capture').replace(/[<>:"/\\|?*]/g, '-')}-${Date.now()}`)
    const manualCapture = project.manualCapture !== false
    const args = [captureJobPath, '--executable', executable, '--working-dir', working, '--output', output, '--arguments-json', JSON.stringify(captureArguments(project)), '--frame', String(Math.max(1, Number(project.captureFrame) || 900)), '--timeout', manualCapture ? '86400' : '300', ...(project.profile === 'UnityD3D11Safe' ? ['--unity-safe'] : []), ...(project.hookChildren ? ['--hook-children'] : []), ...(project.referenceAllResources ? ['--reference-all-resources'] : []), ...(project.captureCallstacks ? ['--capture-callstacks'] : []), ...(project.allowFullscreen ? ['--allow-fullscreen'] : []), ...(project.elevate ? ['--elevate'] : []), ...(manualCapture ? ['--manual'] : [])]
    const child = spawn(pythonPath, args, { cwd: kianaSourceRoot, windowsHide: true, env: pythonEnvironment() })
    const session: CaptureSession = { output, pid: child.pid || 0, targetPid: 0, executable, triggered: false, processed: new Set<string>(), processing: false, monitoring: true }
    activeCaptureSession = session
    captureSessions.set(output, session)
    const sessionMeta = { projectName: String(project.name || executable.split(/[\\/]/).pop() || '游戏'), executablePath: executable, outputDirectory: output, api: project.profile === 'UnityD3D11Safe' ? 'D3D11' : 'D3D12' }
    const send = (value: Record<string, unknown>) => { if (!event.sender.isDestroyed()) event.sender.send('capture:progress', { ...sessionMeta, targetPid: session.targetPid || undefined, ...value }) }
    send({ phase: 'launching', percent: 4, message: project.elevate ? '等待 Windows UAC 确认并启动游戏' : '正在启动游戏' })
    let buffer = ''; let stderr = ''; let captureResult: any = null
    child.stderr.on('data', value => { stderr = (stderr + value.toString()).slice(-maxProcessOutput) })
    child.stdout.on('data', value => {
      buffer += value.toString(); const lines = buffer.split(/\r?\n/); buffer = lines.pop() || ''
      for (const line of lines) try { const message = JSON.parse(line); if (message.type === 'progress') send({ phase: message.percent >= 60 ? 'verifying' : 'capturing', ...message }); if (message.type === 'result') captureResult = message.result; if (message.type === 'error') send({ phase: 'failed', percent: 0, message: message.message, error: message.message }) } catch { /* ignore worker diagnostics */ }
    })
    const processLiveCapture = async (capturePathValue: string) => {
      const capturePath = resolve(capturePathValue)
      if (session.processed.has(capturePath) || !existsSync(capturePath)) return
      session.processed.add(capturePath); session.processing = true; session.triggered = false
      try {
        send({ phase: 'verifying', percent: 62, message: 'RDC 已写入，正在生成帧预览' })
        const thumbnail = await createThumbnail(capturePath)
        rememberWorkspace(capturePath, '', thumbnail)
        const captured = workspace(capturePath, '', thumbnail)
        send({ phase: 'complete', percent: 100, message: project.autoAnalyze ? '当前帧已保存并加入分析队列' : '当前帧已保存', done: true, capturePath, workspace: captured, sessionActive: true })
        let manifestPath = ''
        if (project.autoAnalyze) {
          const analysisOutput = join(output, `analysis-frame${inferFrameNumber(capturePath) || Date.now()}`)
          manifestPath = await enqueueAnalysisJob(capturePath, analysisOutput, project.profile === 'UnityD3D11Safe' ? 'unity' : 'unreal', 12, 12, (percent, message) => send({ phase: 'analyzing', percent: Math.max(1, percent), message, sessionActive: true }))
        }
        if (manifestPath) { rememberWorkspace(capturePath, manifestPath, thumbnail); send({ phase: 'complete', percent: 100, message: '当前帧自动分析完成', done: true, capturePath, workspace: workspace(capturePath, manifestPath, thumbnail), sessionActive: true }) }
        setTimeout(() => send({ phase: 'capturing', percent: 28, message: `实时连接中 · PID ${session.targetPid || '—'} · 可继续截取当前帧`, sessionActive: true }), 1200)
      } catch (error) {
        send({ phase: 'failed', percent: 0, message: error instanceof Error ? error.message : '实时帧处理失败', error: error instanceof Error ? error.message : String(error), sessionActive: true })
      } finally { session.processing = false }
    }
    const stateTimer = setInterval(() => {
      const statePath = join(output, 'direct-capture-result.json')
      if (!existsSync(statePath)) return
       try {
         const state = JSON.parse(readFileSync(statePath, 'utf8')); session.targetPid = Number(state.pid || session.targetPid || 0)
         const detectedApi = [...(state.messages || [])].reverse().find((item: any) => item?.api)?.api
         if (detectedApi) sessionMeta.api = String(detectedApi)
         if (state.status === 'launching') send({ phase: 'launching', percent: 12, message: '游戏进程正在注入 Kiana' })
         if (state.status === 'waiting_for_capture') send({ phase: 'capturing', percent: 28, message: manualCapture ? `实时连接成功 · PID ${session.targetPid} · 点击“截取当前帧”` : `已连接图形 API，等待 Frame ${project.captureFrame}`, sessionActive: manualCapture })
         if (state.status === 'capturing') send({ phase: 'capturing', percent: 48, message: '已触发当前帧，等待 RDC 写入', sessionActive: manualCapture })
         for (const capture of state.captures || []) void processLiveCapture(String(capture))
         if (manualCapture && (state.session_active === false || (session.targetPid > 0 && !isProcessAlive(session.targetPid))) && !session.processing) { clearInterval(stateTimer); captureSessions.delete(output); if (activeCaptureSession?.output === output) activeCaptureSession = null; send({ phase: 'failed', percent: 0, message: '目标游戏已退出，实时捕获会话结束', error: 'target_disconnected', sessionActive: false }) }
       } catch { /* state may be mid-write */ }
    }, 900)
    void (async () => {
      const code = await new Promise<number>(resolveCode => child.once('close', value => resolveCode(value ?? -1)))
      if (!manualCapture) clearInterval(stateTimer)
      if (!manualCapture && activeCaptureSession?.output === output) activeCaptureSession = null
      if (manualCapture) return
      if (code !== 0 || !captureResult?.capture) throw new Error(stderr || '捕获进程没有生成已验证的 RDC')
      const capturePath = resolve(captureResult.capture); ensureFile(capturePath, 'RDC 文件')
      let manifestPath = ''
      if (project.autoAnalyze) {
        const analysisOutput = join(output, 'analysis')
        manifestPath = await enqueueAnalysisJob(capturePath, analysisOutput, project.profile === 'UnityD3D11Safe' ? 'unity' : 'unreal', 12, 12, (percent, message) => send({ phase: 'analyzing', percent: Math.max(1, percent), message }))
      }
      const thumbnail = await createThumbnail(capturePath)
      rememberWorkspace(capturePath, manifestPath, thumbnail)
      const payload = workspace(capturePath, manifestPath, thumbnail, Number(captureResult.frame_number || project.captureFrame || 0))
      send({ phase: 'complete', percent: 100, message: project.autoAnalyze ? '抓帧、验证与分析全部完成' : '抓帧与验证完成', done: true, capturePath, workspace: payload })
    })().catch(error => send({ phase: 'failed', percent: 0, message: error instanceof Error ? error.message : '端到端捕获失败', error: error instanceof Error ? error.message : String(error) }))
    return { pid: child.pid || 0, logPath: join(output, 'direct-capture-result.json'), outputDirectory: output }
  })
  ipcMain.handle('capture:trigger', () => {
    const session = (activeCaptureSession && readCaptureState(activeCaptureSession.output)?.session_active !== false) ? activeCaptureSession : discoverLiveCaptureSession()
    if (!session) throw new Error('当前没有等待抓帧的注入会话')
    const statePath = join(session.output, 'direct-capture-result.json')
    if (!existsSync(statePath)) throw new Error('捕获 Worker 尚未完成注入，请稍后再试')
    const state = JSON.parse(readFileSync(statePath, 'utf8'))
    if (!captureTriggerPending(session, state)) session.triggered = false
    if (session.triggered) throw new Error('当前帧正在写入，请稍候')
    if (state.session_active === false) throw new Error('目标游戏已退出，请重新一键注入')
    if (state.capture_in_progress) throw new Error('目标正在保存上一帧，请稍候')
    writeFileSync(join(session.output, 'trigger-capture.json'), JSON.stringify({ id: `${Date.now()}-${Math.random()}`, frames: 1, requestedAt: new Date().toISOString() }), 'utf8')
    session.triggered = true
    activeCaptureSession = session
    return { triggered: true, outputDirectory: session.output, targetPid: session.targetPid }
  })
  ipcMain.handle('inspector:open', (_event, capturePath: string) => { ensureFile(resolve(capturePath), 'RDC 文件'); ensureFile(guiPath, 'Kiana Inspector'); ensureRuntimeExtension(); spawn(guiPath, [resolve(capturePath)], { detached: true, windowsHide: false, env: { ...process.env, KIANA_HOME: kianaHome, PYTHONUTF8: '1' } }).unref() })
  ipcMain.handle('shell:open-path', (_event, target: string) => { const path = resolve(target); if (!existsSync(path)) throw new Error(`路径不存在：${path}`); return shell.openPath(path) })
  ipcMain.handle('viewport:save-screenshot', async () => {
    const result = await dialog.showSaveDialog(window, {
      title: '保存 Kiana Studio 工作台快照',
      defaultPath: join(app.getPath('pictures'), `kiana-frame-${Date.now()}.png`),
      filters: [{ name: 'PNG Image', extensions: ['png'] }],
    })
    if (result.canceled || !result.filePath) return null
    const image = await window.webContents.capturePage()
    writeFileSync(result.filePath, image.toPNG())
    return result.filePath
  })
  ipcMain.handle('runtime:status', () => probeRuntime())
  ipcMain.handle('renderdoc:call', (_event, method: string, params: Record<string, unknown>) => callRenderdoc(method, params || {}))
  ipcMain.handle('unity:status', () => probeUnity())
  ipcMain.handle('unity:command', (_event, command: string, params: Record<string, unknown>, projectPath?: string) => callUnity(command, params || {}, projectPath || defaultUnityProject))
  ipcMain.handle('resource:preview-texture', async (_event, resourceId: number, name: string) => {
    if (!Number.isInteger(Number(resourceId)) || Number(resourceId) <= 0) throw new Error('该资源没有有效的 RenderDoc Resource ID')
    const cache = join(app.getPath('userData'), 'resource-previews'); mkdirSync(cache, { recursive: true })
    const safeName = String(name || 'texture').replace(/[^a-z0-9._-]+/gi, '-').slice(0, 64) || 'texture'
    const outputPath = join(cache, `${Number(resourceId)}-${safeName}.png`)
    const result = await callRenderdoc('save_texture', { resource_id: Number(resourceId), output_path: outputPath, mip: 0, slice: -1 }, 120) as Record<string, unknown>
    const saved = resolve(String(result.saved || outputPath)); ensureFile(saved, 'RenderDoc 导出的纹理预览')
    return { path: saved, dataUrl: imageDataUrl(saved), result }
  })
  ipcMain.handle('resource:preview-stage', async (_event, eventId: number, resourceId: number, name: string) => {
    if (!Number.isInteger(Number(eventId)) || Number(eventId) <= 0) throw new Error('合成步骤没有有效的 EID')
    if (!Number.isInteger(Number(resourceId)) || Number(resourceId) <= 0) throw new Error('合成步骤没有有效的输出 Resource ID')
    const cache = join(app.getPath('userData'), 'composition-previews'); mkdirSync(cache, { recursive: true })
    const safeName = String(name || 'stage').replace(/[^a-z0-9._-]+/gi, '-').slice(0, 48) || 'stage'
    const remembered = loadWorkspace()
    const captureKey = createHash('sha256').update(String(remembered?.capturePath || 'capture')).digest('hex').slice(0, 12)
    const outputPath = join(cache, `${captureKey}-eid-${Number(eventId)}-rid-${Number(resourceId)}-${safeName}.png`)
    // 相同 RID 在多个 EID 导出完全相同的像素时，不能宣称已经验证逐步历史。
    const duplicateOf = (saved: string) => {
      const digest = createHash('sha256').update(readFileSync(saved)).digest('hex')
      const prefix = `${captureKey}-eid-`
      const ridMarker = `-rid-${Number(resourceId)}-`
      for (const file of readdirSync(cache)) {
        if (!file.startsWith(prefix) || !file.includes(ridMarker)) continue
        const otherEvent = Number(file.slice(prefix.length).split('-')[0])
        if (!otherEvent || otherEvent === Number(eventId)) continue
        const other = join(cache, file)
        if (createHash('sha256').update(readFileSync(other)).digest('hex') === digest) return otherEvent
      }
      return 0
    }
    if (existsSync(outputPath)) return { path: outputPath, dataUrl: imageDataUrl(outputPath, true), result: { cached: true, eventId: Number(eventId), resourceId: Number(resourceId), duplicateOf: duplicateOf(outputPath) } }
    if (remembered?.capturePath && backendCapturePath.toLowerCase() !== resolve(remembered.capturePath).toLowerCase())
      await openCaptureInBackend(remembered.capturePath)
    // SetFrameEvent + SaveTexture must remain atomic because the extension
    // restores RenderDoc's previous event after each API request.
    const result = await callRenderdoc('save_texture', { event_id: Number(eventId), resource_id: Number(resourceId), output_path: outputPath, mip: 0, slice: -1 }, 120) as Record<string, unknown>
    const saved = resolve(String(result.saved || outputPath)); ensureFile(saved, 'RenderDoc 合成步骤预览')
    return { path: saved, dataUrl: imageDataUrl(saved, true), result: { ...result, eventId: Number(eventId), resourceId: Number(resourceId), duplicateOf: duplicateOf(saved) } }
  })
  ipcMain.handle('resource:image', (_event, value: string) => { const path = resolve(String(value || '')); ensureFile(path, '图像资源'); if (!['.png', '.jpg', '.jpeg'].includes(extname(path).toLowerCase())) throw new Error('仅允许加载分析导出的图像'); return imageDataUrl(path, /[\\/]pass-previews[\\/]/i.test(path)) })
  ipcMain.handle('window:set-zoom', (_event, factor: number) => { const value = Math.max(0.8, Math.min(1.25, Number(factor) || 1)); window.webContents.setZoomFactor(value); return value })
  ipcMain.handle('clipboard:write-text', (_event, value: string) => { clipboard.writeText(String(value).slice(0, 8192)) })
  ipcMain.on('window:minimize', () => window.minimize())
  ipcMain.on('window:maximize', () => window.isMaximized() ? window.unmaximize() : window.maximize())
  ipcMain.on('window:close', () => window.close())
})
app.on('before-quit', () => {
  if (engineMcpProcess && !engineMcpProcess.killed) engineMcpProcess.kill()
  if (backendProcessPid) {
    try { process.kill(backendProcessPid) } catch { /* The backend may already have exited. */ }
    backendProcessPid = 0
  }
})

app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit() })
