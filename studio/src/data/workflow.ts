import type { AnalysisModule, WorkspacePayload } from './types'

export const emptyWorkspace: WorkspacePayload = {
  mode: 'empty', capturePath: '', captureName: '', captureBytes: 0, api: '未读取', frameNumber: 0,
  thumbnailDataUrl: '', manifestPath: '', packageDirectory: '', modules: [],
  coverage: { passes: 0, modules: 0, indexedActions: 0, geometryExports: 0, evidenceExports: 0, frameDraws: 0 },
}

const explanations: Record<string, { name: string; meaning: string; lookFor: string }> = {
  scene_geometry: { name: '角色与场景', meaning: '这一组绘制可能在生成角色或场景的基础形状和表面信息。', lookFor: '查看模型片段和绑定贴图。一次绘制可能只对应物体的一部分。' },
  depth_shadow: { name: '深度与阴影', meaning: '这一层可能记录遮挡关系或为阴影准备深度信息。', lookFor: '深度图通常是灰度画面，不能当成最终材质颜色。' },
  sky_atmosphere: { name: '天空与大气', meaning: '这一组资源可能用于天空、雾或大气效果。', lookFor: '结合实际输出判断，资源尺寸和绑定不能单独证明用途。' },
  transparent_effects: { name: '透明与特效', meaning: '这一层可能叠加透明表面、粒子或其他效果。', lookFor: '查看颜色和透明通道，确认它影响的是哪个画面区域。' },
  post_process: { name: '画面后期', meaning: '这一层可能调整已经绘制的画面，例如颜色或模糊效果。', lookFor: '比较这一层的输入与输出。没有模型输出也可能是正常情况。' },
  compute_post: { name: '计算与辅助处理', meaning: '这里是计算任务，可能处理贴图或辅助数据。', lookFor: '它不一定直接出现在屏幕上，也不一定能导出模型。' },
  ui: { name: '界面与合成', meaning: '这一组绘制可能组合界面元素或屏幕画面。', lookFor: '“界面”是自动分类，需要结合实际输出与贴图确认。' },
  auxiliary: { name: '用途待确认', meaning: '现有证据还不足以确定这一层的美术用途。', lookFor: '保留未知结论，查看真实资源或交给技术美术进一步检查。' },
}

export function explainModule(module: AnalysisModule) {
  return explanations[module.module] || explanations.auxiliary
}

export function workflowStep(workspace: WorkspacePayload): number {
  if (workspace.mode !== 'capture') return 1
  return workspace.manifestPath ? 3 : 2
}
