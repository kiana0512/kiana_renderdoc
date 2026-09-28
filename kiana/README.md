# Kiana RenderDoc v11

## 安装与使用

运行 `kiana_RenderDoc_1.47.11_x64_Setup.exe`，默认安装到当前用户的
`%LOCALAPPDATA%\Kiana RenderDoc`。从开始菜单启动 **Kiana RenderDoc**。
安装包内置 MCP 所需 Python 和依赖，不需要另外安装 Python。

鸣潮使用已验证的启动配置：程序路径指向 `Wuthering Waves.exe`，工作目录为其所在目录，
命令行参数 `-krqlv=hd`，勾选 **Capture Child Processes**，取消 **Allow Fullscreen**。
看到游戏叠加层显示 `Capturing D3D12` 后按 F12 抓帧；在连接窗口打开捕获并另存为 RDC。

功能开关位于 **Tools > Kiana > Toggle ...**，点击后弹窗显示所有开关的当前状态：

| 开关 | 默认 | 作用 |
| --- | --- | --- |
| mcp_enabled | 开 | 允许本地 MCP 客户端连接 |
| vulkan_linked_capture | 关 | 下次启动目标程序时联动抓取已初始化的 Vulkan 设备 |
| fbx_export | 开 | 导出当前绘制的 FBX |
| export_textures | 开 | 同时导出绑定纹理及绑定关系清单 |
| unreal_vertex_layout | 关 | 使用本次鸣潮样本验证的 ATTRIBUTE0–5 顶点布局 |

鸣潮模型导出：选择角色对应的三角形 Drawcall，打开 `unreal_vertex_layout`，点击
**Export selected draw to FBX + textures**，选择输出目录。其他游戏不一定使用相同布局；
可通过 MCP `export_fbx` 的 `attribute_map` 指定属性及分量，例如 `ATTRIBUTE4:xy`。
导出的是输入网格，包含可获得的法线、切线、颜色和最多三组 UV；不还原骨骼、动画、
着色器形变和原始材质。纹理单独输出 PNG，并以 JSON 清单记录绑定关系，不猜测材质贴图语义。

连接 MCP：安装结束后生成 `mcp-client.json` 和 `mcp-codex.toml`，按客户端支持的格式添加。
先打开 Kiana，再连接 MCP。多个窗口使用 `list_instances` / `select_instance` 选择。
便携目录移动后运行 `configure_mcp.cmd` 更新配置路径。安装器不会修改其他客户端的设置。

Unity/D3D11 游戏可由 MCP 调用 `capture_kiana_d3d11`。`unity_safe_mode` 默认开启，
减少早期系统/显卡厂商模块挂钩，同时可随时关闭做兼容回归。工具会保存 RDC、诊断日志，
并自动回放验证动作、绘制、资源和着色器数量。D3D12 目标可使用
`capture_nsight_d3d12`，再调用 `convert_nsight_to_rdc` 生成并验证 Kiana RDC。

Vulkan 联动已用同一 GPU 上的两个独立 VkInstance/VkDevice 验证抓取及回放。
每个设备产生单独的 RDC；不合并多设备，也不解除 RenderDoc 对单个 VkInstance 多设备的限制。
尚未验证所有模拟器和多物理 GPU 场景，因此默认关闭。

本版本保留 v8 的早期 DXGI/D3D12 挂钩修复。旧版程序及已有 RDC 不会被安装包删除。
该构建以 RenderDoc 1.47 Development 为基础，具体测试范围见 `VALIDATION.md`。
鸣潮与绝区零的实战参数、MCP 示例和完整故障判断见
[`DEBUGGING_AND_USAGE_CN.md`](DEBUGGING_AND_USAGE_CN.md)。
查询 D3D12 GPU 计时需要 Windows Developer Mode；未开启时 MCP 会返回提示。

Based on RenderDoc 1.47. Start **kiana_qrenderdoc.exe**. Python APIs remain named
`renderdoc` and `qrenderdoc` for extension compatibility.

The validated RenderTest v8 package and existing RDC files are not overwritten.
The early DXGI / D3D12 export hooks from v8 are retained.

## Feature switches

Tools > Kiana exposes independent switches, stored in `%APPDATA%/Kiana/features.json`:

* `mcp_enabled`: local MCP bridge, on by default.
* `vulkan_linked_capture`: off by default. When enabled, newly launched applications
  inherit `KIANA_VULKAN_MULTIDEVICE=1`. A presenting capturer also starts the other
  initialized, idle Vulkan capturers and ends/discards them together. Each device
  writes its own RDC file. This does not merge devices into one replay or remove
  RenderDoc's underlying restrictions on multiple devices in a single VkInstance.
* `fbx_export`: on by default. Select a triangle draw and use
  **Tools > Kiana > Export selected draw to FBX + textures**.
* `export_textures`: on by default. Export bound read-only textures alongside FBX.
* `unreal_vertex_layout`: off by default. Opt-in ATTRIBUTE0–5 mapping validated
  against the Wuthering Waves capture; it is not a universal Unreal layout.

Vulkan switching affects future launches, not processes that are already running.
Set `KIANA_DISABLE_EXTENSION=1` to start without the bundled extension.

FBX exports input-assembly positions, available normals/tangent XYZ, three UV sets
and vertex colors. Triangle lists and strips (including restart) are supported.
Coordinates, scale and UVs are kept unchanged. Export does not reconstruct rigs,
animation, shader deformation or original material semantics. Every export uses
a new folder with a binding manifest; textures are PNG previews at mip/slice zero.
Unsupported attributes are reported; missing/ambiguous positions fail explicitly.
Use MCP's `position_attribute` argument for nonstandard attribute names.

## MCP

The package contains a separate Python 3.12 runtime for MCP. RenderDoc's embedded
Python 3.6 remains unchanged. Import the settings in `mcp-client.json` into an MCP
client, or start `python_mcp/python.exe mcp/launch.py` as a stdio MCP server.

Open Kiana first. `ping` does not require a capture. Use `get_capture_status`,
`get_draw_calls`, `get_pipeline_state`, `get_bound_textures`, `export_fbx`, etc.
Use `capture_kiana_d3d11` for verified direct D3D11 capture with optional Unity
safe mode. Use `capture_nsight_d3d12` plus `convert_nsight_to_rdc` for the
evidence-preserving Nsight D3D12 bridge.
Use `analyze_render_reconstruction` after opening an RDC to generate a pass-by-pass
Markdown/JSON report, output previews, focus-event shader analysis and recommended
geometry events for FBX export.
Use `list_instances` / `select_instance` when more than one GUI is open.
Mailboxes are scoped by installation and GUI instance. Requests have unique IDs,
atomic UTF-8 publication, deadlines and matched responses. No network listener.

The bridge runs with the GUI user's filesystem permissions; use it with trusted
local MCP clients. No extension is installed into the previous v8 application.

## Source and licenses

MCP tools adapted from [Hengle/RenderDocMCP2](https://github.com/Hengle/RenderDocMCP2),
commit `4e8581b3674723ce8306fbad52f2b140fdc7b7c9` (MIT, StellaAstra).
Kiana replaces its PySide2 poller and shared single-request mailbox.
The FBX writer and linked capture implementation are local additions inspired by
[this article](https://zhuanlan.zhihu.com/p/2057780832874582470).
RenderDoc and MinHook licenses are included separately.
