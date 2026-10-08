import type { CapturePreset, CaptureProject } from './types.js'

export const customCapture: CaptureProject = {
  name: '自定义游戏', executablePath: '', workingDirectory: '', captureDirectory: '', arguments: '-force-d3d11',
  profile: 'UnityD3D11Safe', engine: 'unity', preserveExportIdentity: false, wrapOptedOutDevices: false,
  hookChildren: false, referenceAllResources: false, captureCallstacks: false, allowFullscreen: false,
  captureFrame: 900, resolutionWidth: 1280, resolutionHeight: 720, windowMode: 'windowed',
  elevate: false, autoAnalyze: false, manualCapture: true,
}

export function gamePresets(captureRoot: string, exists: (path: string) => boolean = () => false): CapturePreset[] {
  const definitions = [
    { id: 'zzz', name: '绝区零', folder: 'ZenlessZoneZero Game', exe: 'ZenlessZoneZero.exe', description: 'D3D11 · 抓帧与回放通过', limitation: 'D3D12 本轮未验证。', children: true, identity: false, override: false },
    { id: 'starrail', name: '崩坏：星穹铁道', folder: 'Star Rail Game', exe: 'StarRail.exe', description: 'D3D11 · 使用启动兼容配置', limitation: 'D3D12 的最终画面为黑色，使用 D3D11。', children: false, identity: true, override: false },
    { id: 'bh3', name: '崩坏 3', folder: 'Honkai Impact 3rd Game', exe: 'BH3.exe', description: 'D3D11 · D3D12 也已验证', limitation: '当前预设使用 D3D11；可在高级设置中切换 D3D12。', children: false, identity: true, override: false },
    { id: 'genshin', name: '原神', folder: 'Genshin Impact Game', exe: 'YuanShen.exe', description: 'D3D11 · 使用原神抓帧兼容配置', limitation: '已验证云海加载画面。当前版本的 D3D12 参数仍使用 D3D11。', children: false, identity: true, override: true },
    { id: 'wuthering', name: '鸣潮', folder: '', exe: '', description: 'D3D12 · 跟踪实际游戏子进程', limitation: '用户已确认可用，本轮未重新测试。', children: true, identity: false, override: false },
  ] as const
  return definitions.map(game => {
    const paths = game.id === 'wuthering'
      ? ['D', 'E', 'G', 'C'].map(drive => `${drive}:\\Wuthering Waves\\Wuthering Waves Game\\Wuthering Waves.exe`)
      : ['D', 'E', 'C', 'G'].flatMap(drive => ['miHoYo Launcher', 'HoYoPlay'].map(launcher => `${drive}:\\${launcher}\\games\\${game.folder}\\${game.exe}`))
    const executablePath = paths.find(exists) || paths[0]
    return { ...customCapture, id: game.id, name: game.name, description: game.description, limitation: game.limitation,
      executablePath, workingDirectory: executablePath.replace(/[\\/][^\\/]+$/, ''),
      captureDirectory: `${captureRoot}\\${game.id}`, detected: paths.some(exists), hookChildren: game.children,
      profile: game.id === 'wuthering' ? 'UnrealD3D12' : 'UnityD3D11Safe', engine: game.id === 'wuthering' ? 'unreal' : 'unity',
      arguments: game.id === 'wuthering' ? '-krqlv=hd' : '-force-d3d11',
      preserveExportIdentity: game.identity, wrapOptedOutDevices: game.override }
  })
}

// Windows command-line quoting: backslashes before a quote have special meaning.
export function splitArguments(commandLine: string): string[] {
  const result: string[] = []
  let value = '', quoted = false, started = false
  for (let index = 0; index < commandLine.length; index++) {
    const character = commandLine[index]
    if (character === '\\') {
      let count = 1
      while (commandLine[index + 1] === '\\') { count++; index++ }
      if (commandLine[index + 1] === '"') {
        value += '\\'.repeat(Math.floor(count / 2)); index++
        if (count % 2) value += '"'
        else quoted = !quoted
      } else value += '\\'.repeat(count)
      started = true
    } else if (character === '"') { quoted = !quoted; started = true }
    else if (/\s/.test(character) && !quoted) { if (started) result.push(value); value = ''; started = false }
    else { value += character; started = true }
  }
  if (quoted) throw new Error('启动参数的引号没有闭合，请检查高级设置。')
  if (started) result.push(value)
  return result
}

export function captureArguments(project: CaptureProject): string[] {
  const values = splitArguments(project.arguments || '')
  if (/(?:^|[\\/])launcher(?:_main)?\.exe$/i.test(project.executablePath)) return values
  if (project.engine === 'unity') {
    const controlled = new Set(['-screen-fullscreen', '-screen-width', '-screen-height'])
    const args = values.filter((value, index) => !controlled.has(value) && !controlled.has(values[index - 1]) && !['-force-d3d11', '-force-d3d12', '-popupwindow'].includes(value))
    return [...args, project.profile === 'UnityD3D12' ? '-force-d3d12' : '-force-d3d11', '-screen-fullscreen', project.windowMode === 'fullscreen' ? '1' : '0',
      '-screen-width', String(project.resolutionWidth), '-screen-height', String(project.resolutionHeight), ...(project.windowMode === 'borderless' ? ['-popupwindow'] : [])]
  }
  // Keep the verified Wuthering launcher arguments. Its child chooses the backend.
  return values
}

export function captureReady(state: { status?: string; session_active?: boolean; capture_in_progress?: boolean; pid?: number; api?: string } | null): boolean {
  return Boolean(state?.session_active && state.status === 'waiting_for_capture' && !state.capture_in_progress && state.pid && state.api && !['none', 'unknown'].includes(state.api.toLowerCase()))
}

export function knownEngine(capturePath: string): 'unity' | 'unreal' | undefined {
  if (/starrail|star.?rail|bh3|honkai|genshin|yuanshen|zenless|zzz/i.test(capturePath)) return 'unity'
  if (/wuthering|mingchao/i.test(capturePath)) return 'unreal'
  return undefined
}
