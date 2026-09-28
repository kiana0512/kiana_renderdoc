# Kiana RenderDoc 1.47 v11 — 验证记录

日期：2026-09-23。Windows x64，RTX 4070 Ti SUPER。
基于 RenderDoc 1.47 Development，源提交 755ab657ef06cedcbfbf8fb5ac7c4a9d1a6e6f4c 加本地修改。

## 已验证

- MSBuild Development / x64 构建成功。
- 早期 DXGI/D3D12 挂钩：冷/热加载、TLS、DllMain、模块重新加载、名称/序号查找、
  SDK 配置、DXGI 工厂、WARP 设备、开始/丢弃捕获及恢复原始代码均通过。
- 联动协调器：24 项断言，包括开关、重复触发、结束、丢弃及设备销毁。
- 实际 Vulkan 测试：同一 GPU 的两个独立 VkInstance/VkDevice。
  开启得到两份 RDC，关闭得到一份，联动设备中途销毁时保留主设备的一份。
  四份 RDC 均回放成功，读取缓冲区分别得到预期的 0x12340000 / 0x12340001。
- Python 测试：6 项通过，覆盖网格编码、拓扑/重启索引、错误输入及 24 并发 RPC 请求。
- MCP：46 个工具注册；ping、捕获状态查询、直接 D3D11 抓帧及渲染还原报告通过。
  实际 D3D12 捕获验证了纹理、缓冲区、资源、管线、绑定纹理、像素、资源使用、调试信息和计数器枚举。
- Unity/D3D11 安全模式：绝区零 frame900 抓取及独立回放验证成功。RDC 为 124,105,782 字节，
  包含 403 个动作、348 次绘制、8 次计算、1022 个资源和 202 个着色器。
- D3D11 MCP 端到端回归：示例 frame60 抓取、SHA-256 记录及独立回放验证成功。
- ZZZ frame900 渲染还原报告：识别 19 个 Pass，输出逐 Pass 预览；推荐 EID 116、1827、2569。
  EID 116 成功导出 9,869 顶点、6,233 三角形的 FBX、三组 UV、颜色及 6 张纹理。
- Nsight D3D12 桥接：鸣潮样本完成 Nsight→GFXReconstruct→RDC 链路，最终画面逐像素一致。
- FBX：鸣潮 frame3070 的 event3925 导出 8629 顶点、3634 三角形，包含法线、切线、颜色、
  三组 UV 和绑定纹理 PNG；独立 ufbx 解析器验证成功。

## 范围与限制

- 用户已确认旧 v8 能正常抓取并回放鸣潮。新包保留该挂钩路径，并通过上述回归；
  没有对所有游戏重新进行人工启动测试。
- Vulkan 联动默认关闭。没有声称已验证所有模拟器、多物理 GPU 或单 VkInstance 多设备场景。
- FBX 输出输入网格和纹理文件、绑定清单；不重建原始骨骼、动画、着色器形变或材质语义。
- 本机未开启 Windows Developer Mode。D3D12 GPU 计时/计数器执行被提前阻止并返回提示；
  已验证这一保护路径，不计作真实 GPU 计时成功。计数器枚举可正常使用。
- MCP 并非全部 46 个工具都经过逐项端到端验证；复杂着色器调试仍依赖原生 RenderDoc 和驱动支持。
- 安装包在本机编译生成；未替用户执行正式安装，也未在干净虚拟机验证安装。

MCP 上游：Hengle/RenderDocMCP2，提交 4e8581b3674723ce8306fbad52f2b140fdc7b7c9。
Python MCP 依赖固定在 requirements.lock.txt；MCP 1.30.0，Python 3.12.11。
