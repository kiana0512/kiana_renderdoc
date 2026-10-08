# Kiana Studio Electron

Kiana Studio 是面向 GPU 抓帧、渲染逆向和场景重建的 Windows 桌面工作台。界面使用 Electron、React、TypeScript、decius.css 与 React Mosaic；RenderDoc 捕获、RDC 回放和 Python 分析继续由本机 Kiana RenderDoc 运行时完成。

Studio 0.3 默认提供面向美术的“获取画面 → 拆解画面 → 查看素材与依据”引导。
第一次使用请看 [美术使用流程](docs/ARTIST_WORKFLOW_CN.md)。详细检查模式保留 EID、Pass、Shader 和资源查询。
用途分类基于规则推测；捕获文件记录、推测和待确认信息在界面中明确区分。

## 当前能力

- 提供绝区零、崩铁、崩坏 3、原神、鸣潮的预设和启动前检查，接通 Kiana v12 兼容开关。
- 默认手动截取并确认预览后分析，F12 / PrintScreen 在工作台中触发已就绪的捕获会话。
- 读取 RDC 头中的实际 D3D11/D3D12 信息；游戏引擎单独确认。
- 结束捕获连接时保留游戏进程和已经保存的 RDC。
- 导入 RDC，并通过 `kiana_renderdoccmd.exe thumb` 生成最高 2560px 的真实预览。
- 读取重建清单，显示 Pass、Draw、事件范围、Shader、纹理和输出资源。
- 调用 `native_job.py` 执行本地自动分析，并以 NDJSON 进度更新 UI。
- 可调整、拖拽和重新排列场景树、视口、Pass Timeline 与 Inspector 面板，也可一键最大化视口与恢复工作台。
- 打开重建包目录；高级检查仍由 `kiana_qrenderdoc.exe` 承担。
- 内置本地运行时状态页，直接检查捕获核心、Inspector、Python 与 MCP 分析进程。
- 恢复最近打开的实际 RDC，以及界面密度与缩放；Electron 使用原生页面缩放保持自适应。

## 已接通的界面操作

| 区域 | 操作 |
| --- | --- |
| 美术引导 | 获取画面、确认后分析、查看素材与用途依据；失败信息保留并可重试 |
| 游戏启动 | 五个游戏预设、路径记忆、启动前检查、就绪后截取、结束捕获会话 |
| 分析结果 | 真实操作与导出项统计、绘制层选择、推测说明、原始依据和缺失信息 |
| 预览 | RDC 整帧预览、资源纹理、指定 EID 输出；真实导出失败时显示错误 |
| 详细检查 | Pass / EID 定位、Shader 和资源查询、打开原生 GPU Inspector |
| 桌面与布局 | 文件夹与日志入口、窗口控制、工作台截图、可调整面板、密度与缩放 |

详细模式中的场景候选、用途分类和重建映射仍需人工核对；界面上的对象控制不代表原始游戏场景或骨骼已完整恢复。

## 安全边界

Renderer 不启用 Node.js。`contextIsolation` 与 Chromium sandbox 均开启，preload 只暴露明确的 Kiana API。外部导航、新窗口和权限请求默认拒绝。文件、进程和 Shell 操作全部在主进程完成。

## 开发

```powershell
cd studio
npm ci
npm run dev
```

浏览器视觉调试：

```powershell
npm run dev:web
```

检查与构建：

```powershell
npm run typecheck
npm run lint
npm run test:workflow
npm run build
npm run dist
```

安装包生成到 `release\Kiana Studio Setup 0.3.0.exe`。

## 本地依赖

运行时按内置运行时、`KIANA_HOME`、本地便携目录和 `%LOCALAPPDATA%\Kiana RenderDoc` 查找，所需组件为：

- `kiana_renderdoccmd.exe`
- `kiana_qrenderdoc.exe`
- `python_mcp\python.exe`

安装包包含 `resources/kiana/mcp` 与 `resources/kiana/extensions`，保留 Python 包结构。开发时可用 `KIANA_SOURCE_HOME` 指向源码中的 `kiana` 目录。
捕获数据与分析包只在本机处理。

## 设计基准

- `docs/design/kiana-electron-production-spec.png`：产品工作台视觉基准。
- `docs/design/qa-1680x1050.png`：1680×1050 实际渲染验收图。
- `docs/design/qa-2560x1440.png`：2560×1440 自适应验收图。

基础组件来自 [decius.css](https://deciuscss.com/)，停靠布局来自 [React Mosaic](https://github.com/nomcopter/react-mosaic)，桌面安全模型遵循 [Electron Process Model](https://www.electronjs.org/docs/latest/tutorial/process-model) 与 [Electron Security](https://www.electronjs.org/docs/latest/tutorial/security)。
