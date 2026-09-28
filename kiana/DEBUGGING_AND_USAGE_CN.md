# Kiana RenderDoc 1.47 v11：抓帧、MCP 与调试使用说明

本文适用于本仓库的 Kiana RenderDoc v11，记录 2026-09-23 的真实验证结果，
并给出鸣潮、绝区零、D3D11、D3D12、MCP 和 Nsight 桥接的完整操作方法。

## 1. 实战案例一：鸣潮（UE5 / D3D12）

### 1.1 问题与修复

早期故障不是编译、管理员权限、子进程连接或 IAT 修改失败。游戏已经渲染，
但渲染模块的 `D3D12CreateDevice` 导入槽位在设备创建之后才被扫描替换，
因此没有设备创建调用进入包装函数，连接页一直显示 `API: None`。

v8 起保留的修复会提前挂钩 DXGI/D3D12 系统导出入口，使设备在渲染模块初始化时
就能被包装。v11 的 Unity 安全模式是独立开关，默认路径不变，所以不会回退鸣潮修复。

### 1.2 已验证启动配置

- 程序：`D:\Wuthering Waves\Wuthering Waves Game\Wuthering Waves.exe`
- 工作目录：`D:\Wuthering Waves\Wuthering Waves Game`
- 参数：`-krqlv=hd`
- 开启：**Capture Child Processes**
- 关闭：**Allow Fullscreen**

点击 Launch 后，在真正负责渲染的 `Client-Win64-Shipping.exe` 连接页确认
`API: D3D12`。游戏叠加层显示 `Capturing D3D12` 后按 `F12` 或 `PrintScreen`。
用户已经确认该路径可生成并回放真实游戏画面的 RDC。

### 1.3 Nsight → RDC 实测

鸣潮 D3D12 样本完成以下离线链路：

```text
Nsight .ngfx-capture
  -> 提取捕获内置的官方回放器
  -> GFXReconstruct 记录隔离回放
  -> Kiana RenderDoc 再捕获
  -> 独立回放验证 RDC
```

源最终 Present 截图与 RDC 回放截图逐像素一致（MAE 0）。验证样本包含
759 个动作、45 次绘制和 9 次计算。桥接保留源 SHA-256、脱敏元数据、
函数流、对象列表、日志、源截图和逐阶段结果；原始 `.ngfx-capture` 始终是权威源文件。

## 2. 实战案例二：绝区零（Unity / D3D11）

### 2.1 为什么 Nsight 没有 HUD

启动器界面虽然提供“使用 DX12 启动”，但本次直接启动和诊断日志都显示主程序调用
`D3D11CreateDevice`。Nsight Graphics 2026 可以建立连接，但明确报告：

```text
API is unsupported: D3D11, specific function used: D3D11CreateDevice
```

因此没有有效 D3D12 HUD，也不会生成 D3D11 捕获。旧 Nsight 2023 能抓普通
D3D11 示例，但旧版已经按用户要求卸载，且它没有为该目标生成可持久化的捕获文件。

### 2.2 成功的 Kiana 参数

- 程序：`D:\miHoYo Launcher\games\ZenlessZoneZero Game\ZenlessZoneZero.exe`
- 工作目录：`D:\miHoYo Launcher\games\ZenlessZoneZero Game`
- 参数：`-force-d3d11 -screen-fullscreen 0 -screen-width 1280 -screen-height 720`
- Unity 安全模式：开启
- 捕获子进程：开启
- 自动捕获帧：900

成功时左上角显示 `Capturing D3D11`。本次输出：

- 文件：`capture_frame900.rdc`
- 大小：124,105,782 字节
- SHA-256：`931f7ffd715a9c36d7e7fcd77a63bf6e441458bae5bb52709f131e3e32aeed27`
- API：D3D11，frame 900
- 403 个动作、348 次绘制、8 次计算
- 218 个纹理、186 个缓冲区、1022 个资源、202 个着色器
- 最后事件：4671
- 独立回放：Success

### 2.3 Unity 安全模式做了什么

设置 `KIANA_UNITY_SAFE_MODE=1` 后，Kiana 减少早期系统图形导出挂钩，并避免改写
已知 NVIDIA、AMD 和 Intel UMD 模块的导入表。D3D11 设备和交换链仍由 Kiana 正常包装。
该开关只影响新启动的进程，可关闭做兼容回归；默认 D3D12 早期挂钩路径保持不变。

## 3. 选择正确的抓帧路径

| 目标 API | 首选路径 | 说明 |
| --- | --- | --- |
| D3D11 | `capture_kiana_d3d11` | Unity 安全模式默认开启，抓后自动验证 RDC |
| D3D12，Kiana 可直接挂钩 | Kiana GUI | 鸣潮已验证 |
| D3D12，直接挂钩不兼容 | `capture_nsight_d3d12` → `convert_nsight_to_rdc` | 使用 Nsight 2026 官方 CLI |
| Vulkan 多设备 | 开启 `vulkan_linked_capture` 后重新启动 | 每个设备生成独立 RDC |

不要用 Nsight 2026 抓 D3D11。它可以启动程序，但不会生成有效 D3D11 捕获。

## 4. Kiana GUI：Unity / D3D11 手动抓帧

1. 打开 `kiana_qrenderdoc.exe`，进入 **Launch Application**。
2. 填入游戏 EXE 和 EXE 所在工作目录。
3. ZZZ 填入：

   ```text
   -force-d3d11 -screen-fullscreen 0 -screen-width 1280 -screen-height 720
   ```

4. 在环境变量对话框新增：

   ```text
   KIANA_UNITY_SAFE_MODE=1
   KIANA_CAPTURE_DIAGNOSTICS=1
   ```

5. 勾选 **Capture Child Processes**；测试时建议关闭 **Allow Fullscreen**。
6. 点击 **Launch**。看到 `Capturing D3D11` 表示设备和交换链已注册。
7. 按 `F12` 或 `PrintScreen` 抓帧，在连接页打开捕获并另存为 RDC。

## 5. MCP 安装与连接

安装包生成：

- `mcp-client.json`：通用 MCP 客户端配置。
- `mcp-codex.toml`：Codex 配置片段。
- `configure_mcp.cmd`：移动便携目录后重新生成绝对路径。

先启动 Kiana，再连接 MCP。建议顺序：

1. `ping`
2. `get_capture_status`
3. 多窗口时调用 `list_instances`，再调用 `select_instance`
4. `open_capture`
5. `get_frame_summary`、`get_draw_calls`、`get_pipeline_state`、
   `get_bound_textures`、`reverse_shader` 等分析工具

MCP 使用本地 stdio 和带请求 ID 的文件 IPC，不开启网络监听。

## 6. MCP：一键抓取 Unity / D3D11

工具：`capture_kiana_d3d11`

ZZZ 示例：

```json
{
  "executable": "D:\\miHoYo Launcher\\games\\ZenlessZoneZero Game\\ZenlessZoneZero.exe",
  "working_dir": "D:\\miHoYo Launcher\\games\\ZenlessZoneZero Game",
  "arguments": [
    "-force-d3d11",
    "-screen-fullscreen", "0",
    "-screen-width", "1280",
    "-screen-height", "720"
  ],
  "output_dir": "D:\\KianaCaptures\\zzz-frame900",
  "capture_frame": 900,
  "unity_safe_mode": true,
  "hook_children": true,
  "terminate_after_capture": false,
  "open_after": true,
  "timeout_seconds": 300
}
```

成功返回 `capture`、`bytes`、`sha256`、API、帧号、动作/绘制/计算/资源/着色器数量，
以及诊断日志和验证文件。工具先抓帧，再由独立回放会话验证；只有回放成功才返回
`status=capture_saved`。`terminate_after_capture=false` 时游戏在完成后保持运行。

## 7. MCP：Nsight D3D12 → RDC

先调用 `capture_nsight_d3d12`：

```json
{
  "executable": "D:\\Game\\Game.exe",
  "working_dir": "D:\\Game",
  "arguments": "-force-d3d12 -screen-fullscreen 0",
  "output_dir": "D:\\KianaCaptures\\nsight-source",
  "capture_frame": 1200,
  "terminate_after_capture": false,
  "timeout_seconds": 900
}
```

得到 `.ngfx-capture` 后调用：

```json
{
  "capture_path": "D:\\KianaCaptures\\nsight-source\\Game-frame1200.ngfx-capture",
  "output_dir": "D:\\KianaCaptures\\game-rdc",
  "open_after": true
}
```

输出目录包含源证据、GFXReconstruct 中间流、RDC、逐阶段日志、截图对比和
`bridge-result.json`。源 `.ngfx-capture` 不被修改。

## 8. MCP：一键生成渲染还原报告

打开 RDC 后调用 `analyze_render_reconstruction`：

```json
{
  "output_dir": "D:\\KianaAnalysis\\zzz-frame900",
  "focus_event_ids": "116,3583,4635",
  "save_previews": true
}
```

工具会自动完成：

1. 按 RenderDoc 的 Colour / Compute / Depth-only 标记重建 Pass 顺序。
2. 统计每个 Pass 的事件范围、Draw 数和索引数。
3. 读取输出纹理尺寸/格式并保存每个 Pass 的第一张输出预览。
4. 选择每个 Pass 最大索引 DrawCall，读取管线、顶点布局和绑定纹理。
5. 区分场景 G-buffer、深度/阴影、全屏后处理、计算处理和 UI 合成。
6. 对 `focus_event_ids` 额外导出管线、纹理及像素着色器反汇编。
7. 输出 `render-reconstruction-report.md` 和完整 JSON。

ZZZ frame900 实测识别到 19 个 Pass，并推荐 EID 116、1827、2569 作为主要几何入口：

- EID 116：登录场景建筑，四 MRT G-buffer，绑定高度图以及建筑 D/N/M 贴图。
- EID 1827：1272×720 主场景 G-buffer，额外绑定 Unity 光照贴图。
- EID 3583：半分辨率全屏后处理；组合 `_TAART1` 和临时缓冲，不应导出为模型。
- Pass #15：游戏本体 UI/字体层。
- Pass #16：账号登录 UI 覆盖层。

对 EID 116 调用 `export_fbx` 已成功输出 9,869 顶点、6,233 三角形，包含
POSITION、NORMAL、TANGENT、COLOR、三组 UV 和 6 张绑定纹理；同时可用
`export_drawcall` 保存 DXBC 着色器反汇编和所有纹理。

推荐的还原顺序是：几何/G-buffer → 深度/阴影 → 光照和透明物 → TAA/模糊/色调映射
等全屏处理 → 游戏 UI → 外部账号 UI。这样不需要从 4,000 多个事件逐个猜测。

## 9. 常见故障

| 现象 | 判断 | 处理 |
| --- | --- | --- |
| `API: None` | 设备在挂钩前创建，或创建路径未覆盖 | D3D12 使用早期挂钩；D3D11 用安全模式重启 |
| Nsight 2026 无 HUD，日志含 `D3D11CreateDevice` | 目标实际为 D3D11 | 使用 `capture_kiana_d3d11` |
| HUD 显示 `Capturing D3D11` | Kiana 挂钩成功 | 等待自动帧或按 F12 |
| 目标约 5 秒退出，退出码 999 | 目标主动拒绝图形调试插桩 | 不做保护绕过；换允许调试的目标或官方路径 |
| RDC 保存但分析异常 | 需要验证回放 | 查看 `verification.json` 和 `renderdoc-debug.log` |
| D3D12 GPU 计时提示 Developer Mode | Windows 未开放所需运行时能力 | 只在需要计数器时开启 Developer Mode |

星铁实测属于目标主动拒绝插桩：Kiana 建立控制连接后目标以 999 退出；
Nsight 2023 识别到 Present 后也无法进入 interception-ready。本仓库不包含反作弊绕过、
模块隐藏或保护禁用逻辑。

## 10. 输出文件

直接 D3D11 抓帧目录：

```text
capture_frameNNN.rdc
direct-capture-config.json
direct-capture-result.json
renderdoc-debug.log
verify-config.json
verification.json
```

Nsight 桥接目录还包含脱敏元数据、函数/对象清单、源截图、GFXReconstruct 中间流和
逐阶段日志。

## 11. FBX、纹理和 Vulkan 功能

选择目标三角形 Drawcall，使用
**Tools > Kiana > Export selected draw to FBX + textures**。鸣潮样本需开启
`unreal_vertex_layout`。输出包含输入装配阶段可获得的顶点、索引、法线、切线、
颜色、最多三组 UV、绑定纹理 PNG 和 JSON 清单；不重建骨骼、动画、着色器形变或材质语义。

`vulkan_linked_capture` 默认关闭。开启后对新启动程序生效；同一次联动中的每个设备
生成独立 RDC，不把多个设备合并为一个回放文件。

## 12. 构建与验证

主 DLL：

```powershell
$vswhere = 'C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe'
$msbuild = & $vswhere -latest -products * -requires Microsoft.Component.MSBuild `
  -find MSBuild\**\Bin\MSBuild.exe | Select-Object -First 1
& $msbuild E:\renderdoc\renderdoc\renderdoc.vcxproj /m `
  /p:Configuration=Development /p:Platform=x64 /p:SolutionDir=E:\renderdoc\
```

MCP：

```powershell
python -m py_compile kiana\mcp\src\direct_capture.py kiana\mcp\src\server.py
python -m unittest kiana.tests.test_nsight_bridge -v
```

完整验证依据见 `VALIDATION.md`。
