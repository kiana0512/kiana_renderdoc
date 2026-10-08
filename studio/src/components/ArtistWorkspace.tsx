import type { ReactNode } from 'react'
import type { AnalysisModule, AnalysisProgress, CaptureProgress, RuntimeStatus, WorkspacePayload } from '../data/types'
import { explainModule, workflowStep } from '../data/workflow'

type Props = {
  workspace: WorkspacePayload; selected: AnalysisModule; runtime: RuntimeStatus | null; progress: AnalysisProgress | null;
  capture: CaptureProgress | null; busy: boolean; ready: boolean; error: string; resourceContent: ReactNode;
  onCapture: () => void; onImport: () => void; onAnalyze: () => void; onTrigger: () => void; onSelect: (module: AnalysisModule) => void;
  onExport: () => void; onTechnical: () => void; onExample: () => void; onLogs: () => void; onRuntime: () => void; onStop: () => void;
}

export function ArtistWorkspace(props: Props) {
  const { workspace, selected, progress, capture, busy, ready, error } = props
  const step = workflowStep(workspace)
  const real = workspace.mode === 'capture'
  const analyzed = real && Boolean(workspace.manifestPath)
  const explanation = explainModule(selected)
  const failure = error || capture?.error || progress?.error
  return <main className="artist-workspace">
    <aside className="artist-guide">
      <span className="artist-eyebrow">从一张游戏画面开始</span><h1>看懂画面是怎么组成的</h1>
      <p>保存当前画面的 GPU 数据，再查看绘制层、贴图和可导出的模型片段。</p>
      <ol className="workflow-steps" aria-label="使用步骤">
        {['获取画面', '拆解画面', '查看素材与依据'].map((name, index) => <li key={name} aria-current={step === index + 1 ? 'step' : undefined} className={step === index + 1 ? 'current' : step > index + 1 ? 'complete' : ''}><b>{index + 1}</b><div><strong>{name}</strong><span>{index === 0 ? '启动游戏后截取，或打开已有 RDC' : index === 1 ? '确认画面正确，再分析结构与资源' : '查看真实数据，核对自动推测'}</span></div></li>)}
      </ol>
      <div className="artist-actions"><button className="dcs-btn dcs-btn--primary" onClick={props.onCapture}>启动游戏获取画面</button><button className="dcs-btn" onClick={props.onImport}>打开已有画面文件（RDC）</button></div>
      {capture && <section className="artist-session" aria-live="polite"><b>{capture.projectName || '游戏捕获会话'}</b><p>{capture.message}</p>{ready && <><p>切回游戏，停在你要研究的画面，再回这里截取。</p><button className="dcs-btn dcs-btn--primary" onClick={props.onTrigger}>截取当前画面</button></>}{capture.sessionActive && <button className="text-action" onClick={props.onStop}>结束捕获会话（游戏继续运行）</button>}{capture.outputDirectory && <button className="text-action" onClick={props.onLogs}>打开捕获与日志文件夹</button>}</section>}
      {real && !analyzed && <section className="artist-session"><b>下一步：先确认右侧画面</b><p>如果是黑屏、启动画面或下载界面，请回游戏重新截取。</p><button className="dcs-btn dcs-btn--primary" disabled={busy || !props.runtime?.analysisWorker || !props.runtime?.python} onClick={props.onAnalyze}>{busy ? '正在拆解画面…' : '分析这张画面'}</button></section>}
      {progress && !progress.done && !progress.error && real && <div className="artist-progress" role="status"><p>{progress.message}</p><progress max="100" value={progress.percent} /></div>}
      {failure && <section className="workflow-error" role="alert"><b>这一步没有完成</b><p>{failure}</p><span>画面文件会保留。检查设置或日志后可以重试。</span><button className="text-action" onClick={props.onLogs}>查看文件与日志</button></section>}
      <button className="text-action" onClick={props.onRuntime}>检查本地运行环境</button>
      <details className="artist-glossary"><summary>第一次使用：几个词是什么意思？</summary><p><b>RDC</b> 是保存一帧绘制过程的文件，不是录像。</p><p><b>绘制层（Pass）</b> 是组成画面的一组 GPU 操作。</p><p><b>事件编号（EID）</b> 用来定位其中一次操作。</p><p><b>贴图 / 输出图</b> 可能是颜色、法线、遮罩、深度或中间计算结果，需要结合证据判断。</p><p>单帧数据不包含完整游戏工程，也无法直接恢复完整骨骼动画。</p></details>
    </aside>
    <section className="artist-content">
      <header className="artist-content-header"><div><span className="artist-eyebrow">{real ? '来自本地捕获文件' : workspace.mode === 'demo' ? '示例数据 · 非你的游戏画面' : '尚未获取画面'}</span><h2>{real ? workspace.captureName : workspace.mode === 'demo' ? '示例：认识工作台' : '先选择一张想研究的画面'}</h2></div>{real && <button className="dcs-btn" onClick={props.onTechnical}>打开详细检查</button>}</header>
      {props.resourceContent || <div className="artist-frame">{workspace.thumbnailDataUrl ? <img src={workspace.thumbnailDataUrl} alt={real ? '捕获文件中的整帧预览' : '明确标记的工作台示例'} /> : <div className="artist-empty"><span>01</span><h2>从游戏截一帧，或打开 RDC 文件</h2><p>拿到画面后，这里会显示真实预览。确认是你想研究的场景，再开始分析。</p><button className="dcs-btn" onClick={props.onExample}>先看看示例（非真实捕获）</button></div>}</div>}
      {real && <div className="artist-frame-caption"><span>整帧预览 · {workspace.api} · {(workspace.captureBytes / 1024 / 1024).toFixed(1)} MB</span><span>这是捕获参考，尚不能证明完整场景已还原。</span></div>}
      {analyzed && <section className="artist-results"><header><div><h2>这张画面包含什么？</h2><p>分类由绘制和资源规则推测；选择一层查看依据。</p></div><button className="dcs-btn" onClick={props.onExport}>打开分析素材文件夹</button></header>
        <div className="artist-facts"><div><b>{workspace.coverage.frameDraws}</b><span>真实绘制操作</span></div><div><b>{workspace.coverage.passes}</b><span>已索引的绘制层</span></div><div><b>{workspace.coverage.geometryExports}</b><span>已导出的几何片段</span></div><div><b>{workspace.coverage.evidenceExports}</b><span>已导出的证据项</span></div></div>
        <div className="artist-result-grid"><nav aria-label="画面层列表">{workspace.modules.map(module => <button key={module.passNumber} onClick={() => props.onSelect(module)} aria-pressed={selected.passNumber === module.passNumber}><span>{String(module.passNumber).padStart(2, '0')}</span><div><b>{explainModule(module).name}</b><small>{module.drawCount} 次绘制 · {module.textures.length} 项绑定资源</small></div><em>自动推测</em></button>)}</nav><article className="artist-explanation"><span className="inference-badge">用途：自动推测</span><h3>{explanation.name}</h3><p>{explanation.meaning}</p><h4>现在可以看什么</h4><p>{explanation.lookFor}</p><h4>文件里确实记录了</h4><p>{selected.drawCount} 次绘制、{selected.dispatchCount} 次计算，{selected.outputs.length} 项输出资源、{selected.textures.length} 项绑定贴图。资源数量指清单中已记录的项。</p><details><summary>查看原始判定依据</summary>{selected.reasons.length ? selected.reasons.map((reason, index) => <p key={index}>{reason}</p>) : <p>清单没有提供分类依据，需人工核对。</p>}{selected.missing.length > 0 && <p>缺失信息：{selected.missing.join('、')}</p>}</details><button className="dcs-btn" onClick={props.onTechnical}>检查这一层的真实输出和贴图</button></article></div>
        <div className="artist-truth"><b>待确认的内容</b><p>原始物体名称、完整材质关系、骨骼和动画未由单帧数据证明。导出的模型可能是片段；纹理用途与“角色 / 场景”分类需要你核对。</p>{workspace.reverseWorkflow && <details><summary>查看重建步骤状态</summary>{workspace.reverseWorkflow.stages.map(stage => <p key={stage.id}><b>{stage.title}</b> · {({ complete: '已完成', partial: '部分完成', blocked: '需要补充证据', pending: '尚未执行', failed: '失败' })[stage.status]}<br />{stage.detail}</p>)}</details>}</div>
      </section>}
    </section>
  </main>
}
