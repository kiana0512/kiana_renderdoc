export type AnalysisResource = {
  resourceId?: number
  name: string
  slot: string
  role: string
  format: string
  width: number
  height: number
}

export type CompositionStage = {
  eventId: number
  ordinal: number
  name: string
  sourceName: string
  kind: 'draw' | 'dispatch' | 'clear' | 'copy' | 'present'
  semanticKind?: string
  bindingName?: string
  boundTextures?: AnalysisResource[]
  numIndices: number
  numInstances: number
  outputResourceIds: number[]
  previewPath: string
}

export type AnalysisModule = {
  module: string
  displayName: string
  confidence: number
  passNumber: number
  passName: string
  eventStart: number
  eventEnd: number
  representativeEvent: number
  drawCount: number
  dispatchCount: number
  actionKind: 'draw' | 'dispatch' | 'none'
  totalIndices: number
  vertexShader: number
  fragmentShader: number
  computeShader: number
  outputs: AnalysisResource[]
  textures: AnalysisResource[]
  reasons: string[]
  missing: string[]
  previewPath: string
  stages: CompositionStage[]
}

export type ReverseWorkflowStage = {
  id: string
  title: string
  status: 'complete' | 'partial' | 'blocked' | 'pending' | 'failed'
  detail: string
  artifact: string
}

export type ReverseWorkflow = {
  path: string
  status: string
  profile: string
  targetEngine: 'unity' | 'unreal'
  stages: ReverseWorkflowStage[]
  skills: string[]
  poseExports: { attempted: number; valid: number; failed: number; manifest: string }
  truth: { proven?: string; inferred?: string; blocked?: string }
}

export type WorkspacePayload = {
  mode: 'demo' | 'capture'
  capturePath: string
  captureName: string
  captureBytes: number
  api: string
  frameNumber: number
  thumbnailDataUrl: string
  manifestPath: string
  packageDirectory: string
  coverage: {
    passes: number
    modules: number
    indexedActions: number
    geometryExports: number
    evidenceExports: number
    frameDraws: number
  }
  modules: AnalysisModule[]
  assetGraph?: {
    path: string
    objects: number
    materials: number
    shaders: number
    textures: number
    classificationCounts: Record<string, number>
    skinnedEventIds: number[]
    characterEventIds: number[]
    animation: Record<string, unknown>
  }
  reconstructionContract?: {
    path: string
    counts: Record<string, number>
    characterEventIds: number[]
  }
  truthPolicy?: { fact?: string; inference?: string; unknown?: string }
  reverseWorkflow?: ReverseWorkflow
}

export type AnalysisProgress = { percent: number; message: string; done?: boolean; error?: string }
export type AnalysisRequest = { capturePath: string; outputDirectory: string; engine: 'unreal' | 'unity'; maxGeometry: number; maxCharacterPoses?: number }
export type CaptureProject = { name: string; executablePath: string; workingDirectory: string; captureDirectory: string; arguments: string; profile: 'UnrealD3D12' | 'UnityD3D11Safe'; hookChildren: boolean; referenceAllResources: boolean; captureCallstacks: boolean; allowFullscreen: boolean; captureFrame: number; resolutionWidth: number; resolutionHeight: number; windowMode: 'windowed' | 'borderless' | 'fullscreen'; elevate: boolean; autoAnalyze: boolean; manualCapture: boolean }
export type CapturePreset = CaptureProject & { id: 'wuthering' | 'zzz'; detected: boolean; description: string }
export type CaptureProgress = AnalysisProgress & {
  phase: 'launching' | 'capturing' | 'verifying' | 'analyzing' | 'complete' | 'failed'
  capturePath?: string
  workspace?: WorkspacePayload
  projectName?: string
  executablePath?: string
  outputDirectory?: string
  targetPid?: number
  api?: string
  sessionActive?: boolean
}
export type CaptureHistoryEntry = { capturePath: string; captureName: string; captureBytes: number; frameNumber: number; modifiedAt: number; manifestPath: string; analyzed: boolean }
export type RuntimeStatus = { desktop: boolean; connected: boolean; bridgeConnected: boolean; engineMcp: boolean; engineMcpUrl: string; renderdocMcp: boolean; renderdocMcpUrl: string; ueMcp: boolean; ueMcpUrl: string; unityMcp: boolean; unityPort: number; unityProject: string; unityVersion: string; mcpTools: number; bridgePid: number; kianaRoot: string; sourceRoot: string; captureCore: boolean; inspector: boolean; python: boolean; analysisWorker: boolean }
export type UnityStatus = { connected: boolean; port: number; project: string; version: string }

export type KianaApi = {
  loadWorkspace: () => Promise<WorkspacePayload | null>
  getCaptureHistory: () => Promise<CaptureHistoryEntry[]>
  openCapture: (capturePath: string) => Promise<WorkspacePayload>
  selectRdc: () => Promise<WorkspacePayload | null>
  runAnalysis: (request: AnalysisRequest) => Promise<WorkspacePayload>
  launchCapture: (project: CaptureProject) => Promise<{ pid: number; logPath: string; outputDirectory: string }>
  triggerCapture: () => Promise<{ triggered: boolean; outputDirectory: string }>
  recoverCapture: () => Promise<(CaptureProgress & { presetId?: string }) | null>
  getCapturePresets: () => Promise<CapturePreset[]>
  selectExecutable: () => Promise<string | null>
  selectDirectory: () => Promise<string | null>
  openInspector: (capturePath: string) => Promise<void>
  openPath: (path: string) => Promise<string>
  saveViewportScreenshot: () => Promise<string | null>
  getRuntimeStatus: () => Promise<RuntimeStatus>
  callRenderdoc: (method: string, params?: Record<string, unknown>) => Promise<unknown>
  getUnityStatus: () => Promise<UnityStatus>
  callUnity: (command: string, params?: Record<string, unknown>, projectPath?: string) => Promise<unknown>
  previewTexture: (resourceId: number, name: string) => Promise<{ path: string; dataUrl: string; result: Record<string, unknown> }>
  previewStage: (eventId: number, resourceId: number, name: string) => Promise<{ path: string; dataUrl: string; result: Record<string, unknown> }>
  loadImage: (path: string) => Promise<string>
  setZoom: (factor: number) => Promise<number>
  copyText: (text: string) => Promise<void>
  onAnalysisProgress: (callback: (progress: AnalysisProgress) => void) => () => void
  onCaptureProgress: (callback: (progress: CaptureProgress) => void) => () => void
  minimize: () => void
  maximize: () => void
  close: () => void
}
