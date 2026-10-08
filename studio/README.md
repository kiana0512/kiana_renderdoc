# Kiana Studio Electron

Kiana Studio 是面向 GPU 抓帧、渲染逆向和场景重建的 Windows 桌面工作台。界面使用 Electron、React、TypeScript、decius.css 与 React Mosaic；RenderDoc 捕获、RDC 回放和 Python 分析继续由本机 Kiana RenderDoc 运行时完成。

## 当前能力

- 从游戏路径启动 D3D12 / Unity D3D11 Safe 捕获会话。
- 导入 RDC，并通过 `kiana_renderdoccmd.exe thumb` 生成最高 2560px 的真实预览。
- 读取重建清单，显示 Pass、Draw、事件范围、Shader、纹理和输出资源。
- 调用 `native_job.py` 执行本地自动分析，并以 NDJSON 进度更新 UI。
- 可调整、拖拽和重新排列场景树、视口、Pass Timeline 与 Inspector 面板，也可一键最大化视口与恢复工作台。
- 打开重建包目录；高级检查仍由 `kiana_qrenderdoc.exe` 承担。
- 内置本地运行时状态页，直接检查捕获核心、Inspector、Python 与 MCP 分析进程。
- 工作区会保存当前帧、对象、界面密度与缩放；Electron 使用原生页面缩放保持自适应。

## 已接通的界面操作

| 区域 | 操作 |
| --- | --- |
| 顶部 | 一键抓帧、自动分析、导出重建包、完整桌面菜单、窗口控制、MCP/运行时状态 |
| 项目栏 | 帧切换与全界面同步、分组折叠、重建目录选择、导入 RDC、新建捕获项目 |
| 场景树 | 场景/资源切换、实时搜索、层级折叠、对象选择、对象显隐、资源类别选择 |
| 视口 | R/G/B/A 通道、Beauty/Wireframe/Overdraw、叠加层、拾取/截图/选择/移动/旋转、视角、1:1、最大化 |
| Timeline | Pass 彩条定位、EID/名称搜索、Pass 表选择、下一个 Pass、禁用/Draw/资源高亮证据选项 |
| Inspector | 基本信息、材质/Shader、重建映射、LOD、折叠区、材质与纹理选择、Shader 标识复制、参考/重建滑杆 |
| 布局 | 面板拖动、交换、停靠和尺寸调整；窄窗口应用菜单；1120、1360、2200px 响应式断点 |

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
npm run build
npm run dist
```

安装包生成到 `release\Kiana Studio Setup 0.2.0.exe`。

## 本地依赖

默认从 `%LOCALAPPDATA%\Kiana RenderDoc` 读取：

- `kiana_renderdoccmd.exe`
- `kiana_qrenderdoc.exe`
- `python_mcp\python.exe`
- `mcp\src\native_job.py`

可用 `KIANA_HOME` 覆盖运行时目录。捕获数据与重建包只在本机处理。

## 设计基准

- `docs/design/kiana-electron-production-spec.png`：产品工作台视觉基准。
- `docs/design/qa-1680x1050.png`：1680×1050 实际渲染验收图。
- `docs/design/qa-2560x1440.png`：2560×1440 自适应验收图。

基础组件来自 [decius.css](https://deciuscss.com/)，停靠布局来自 [React Mosaic](https://github.com/nomcopter/react-mosaic)，桌面安全模型遵循 [Electron Process Model](https://www.electronjs.org/docs/latest/tutorial/process-model) 与 [Electron Security](https://www.electronjs.org/docs/latest/tutorial/security)。
