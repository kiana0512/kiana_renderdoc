import { contextBridge, ipcRenderer } from 'electron'
import type { AnalysisProgress, AnalysisRequest, CaptureProgress, CaptureProject, KianaApi } from '../../src/data/types.js'

const api: KianaApi = {
  loadWorkspace: () => ipcRenderer.invoke('workspace:load'),
  getCaptureHistory: () => ipcRenderer.invoke('workspace:history'),
  openCapture: (capturePath: string) => ipcRenderer.invoke('workspace:open-capture', capturePath),
  selectRdc: () => ipcRenderer.invoke('dialog:select-rdc'),
  runAnalysis: (request: AnalysisRequest) => ipcRenderer.invoke('analysis:run', request),
  launchCapture: (project: CaptureProject) => ipcRenderer.invoke('capture:launch', project),
  triggerCapture: () => ipcRenderer.invoke('capture:trigger'),
  recoverCapture: () => ipcRenderer.invoke('capture:recover'),
  getCapturePresets: () => ipcRenderer.invoke('capture:presets'),
  selectExecutable: () => ipcRenderer.invoke('dialog:select-executable'),
  selectDirectory: () => ipcRenderer.invoke('dialog:select-directory'),
  openInspector: (capturePath: string) => ipcRenderer.invoke('inspector:open', capturePath),
  openPath: (path: string) => ipcRenderer.invoke('shell:open-path', path),
  saveViewportScreenshot: () => ipcRenderer.invoke('viewport:save-screenshot'),
  getRuntimeStatus: () => ipcRenderer.invoke('runtime:status'),
  callRenderdoc: (method: string, params: Record<string, unknown> = {}) => ipcRenderer.invoke('renderdoc:call', method, params),
  getUnityStatus: () => ipcRenderer.invoke('unity:status'),
  callUnity: (command: string, params: Record<string, unknown> = {}, projectPath?: string) => ipcRenderer.invoke('unity:command', command, params, projectPath),
  previewTexture: (resourceId: number, name: string) => ipcRenderer.invoke('resource:preview-texture', resourceId, name),
  previewStage: (eventId: number, resourceId: number, name: string) => ipcRenderer.invoke('resource:preview-stage', eventId, resourceId, name),
  loadImage: (path: string) => ipcRenderer.invoke('resource:image', path),
  setZoom: (factor: number) => ipcRenderer.invoke('window:set-zoom', factor),
  copyText: (text: string) => ipcRenderer.invoke('clipboard:write-text', text),
  onAnalysisProgress: (callback: (progress: AnalysisProgress) => void) => {
    const listener = (_event: Electron.IpcRendererEvent, progress: AnalysisProgress) => callback(progress)
    ipcRenderer.on('analysis:progress', listener)
    return () => ipcRenderer.removeListener('analysis:progress', listener)
  },
  onCaptureProgress: (callback: (progress: CaptureProgress) => void) => {
    const listener = (_event: Electron.IpcRendererEvent, progress: CaptureProgress) => callback(progress)
    ipcRenderer.on('capture:progress', listener)
    return () => ipcRenderer.removeListener('capture:progress', listener)
  },
  minimize: () => ipcRenderer.send('window:minimize'),
  maximize: () => ipcRenderer.send('window:maximize'),
  close: () => ipcRenderer.send('window:close'),
}

contextBridge.exposeInMainWorld('kiana', api)
