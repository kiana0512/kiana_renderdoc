import type { AnalysisModule, WorkspacePayload } from './types'

const raw = [
  [1, 'Compute Pass #1', 'compute_post', .86, 0, 0, 0, 420, 445],
  [2, 'Colour Pass #1 (1 Targets + Depth)', 'transparent_effects', .70, 3, 24, 471, 462, 485],
  [3, 'Compute Pass #2', 'compute_post', .86, 0, 0, 0, 492, 4227],
  [4, 'Colour Pass #2 (1 Targets)', 'ui', .90, 42, 252, 657, 657, 4229],
  [5, 'Colour Pass #3 (7 Targets + Depth)', 'scene_geometry', .96, 14, 281880, 1124, 995, 1195],
  [6, 'Colour Pass #4 (7 Targets + Depth)', 'scene_geometry', .96, 14, 525108, 1331, 1226, 4232],
  [7, 'Depth-only Pass #1', 'depth_shadow', .94, 4, 144, 1424, 1424, 1444],
  [8, 'Compute Pass #3', 'compute_post', .86, 0, 0, 0, 1452, 4235],
  [9, 'Depth-only Pass #2', 'depth_shadow', .94, 10, 368784, 1974, 1882, 1997],
  [10, 'Depth-only Pass #3', 'depth_shadow', .94, 10, 11937, 2023, 2010, 2127],
  [11, 'Colour Pass #5 (1 Targets + Depth)', 'sky_atmosphere', .86, 30, 503, 2455, 2139, 2574],
  [12, 'Colour Pass #6 (1-2 Targets + Depth)', 'transparent_effects', .70, 30, 42408, 2861, 2588, 2985],
  [13, 'Compute Pass #4', 'compute_post', .86, 25, 75, 3163, 2992, 4241],
  [14, 'Colour Pass #7 (1 Targets)', 'transparent_effects', .70, 61, 3267, 3986, 3463, 4243],
] as const

const names: Record<string, string> = { compute_post: '计算着色', transparent_effects: '透明 / 特效', ui: 'UI 合成', scene_geometry: '场景几何 / G-buffer', depth_shadow: '深度 / 阴影', sky_atmosphere: '天空 / 大气 / 体积' }

const modules: AnalysisModule[] = raw.map(([passNumber, passName, module, confidence, drawCount, totalIndices, representativeEvent, eventStart, eventEnd]) => ({
  passNumber, passName, module, displayName: names[module], confidence, drawCount, totalIndices, representativeEvent, eventStart, eventEnd,
  dispatchCount: module === 'compute_post' ? Math.max(1, drawCount) : 0, actionKind: module === 'compute_post' ? 'dispatch' : representativeEvent ? 'draw' : 'none',
  vertexShader: representativeEvent ? representativeEvent + 101 : 0, fragmentShader: representativeEvent ? representativeEvent + 209 : 0, computeShader: module === 'compute_post' ? representativeEvent + 301 : 0,
  outputs: representativeEvent ? [{ name: '2D Render Target', slot: 'RT0', role: 'output', format: 'R16G16B16A16_FLOAT', width: 2560, height: 1440 }] : [], stages: [],
  textures: representativeEvent ? [
    { name: 'SceneColor', slot: 't0', role: 'albedo', format: 'BC7', width: 2048, height: 2048 },
    { name: 'NormalRoughness', slot: 't1', role: 'normal', format: 'BC5', width: 2048, height: 2048 },
    { name: 'MaterialMask', slot: 't2', role: 'mask', format: 'BC7', width: 1024, height: 1024 },
  ] : [], reasons: [names[module]], missing: [], previewPath: '',
}))

export const demoWorkspace: WorkspacePayload = {
  mode: 'demo',
  capturePath: 'E:\\renderdoc\\test-results.rdc', captureName: 'test-results.rdc', captureBytes: 953167607, api: 'D3D12', frameNumber: 3070,
  thumbnailDataUrl: './wuthering-preview.jpg', manifestPath: 'E:\\renderdoc\\test-results\\wuthering-reconstruction-package-v2\\reconstruction-manifest.json',
  packageDirectory: 'E:\\renderdoc\\test-results\\wuthering-reconstruction-package-v2',
  coverage: { passes: 14, modules: 14, indexedActions: 409, geometryExports: 2, evidenceExports: 7, frameDraws: 243 }, modules,
}
