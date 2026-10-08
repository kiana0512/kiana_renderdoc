# Kiana RenderDoc 1.47 v12 验证记录

日期：2026-10-08。Windows x64。

- 原始本地修改已保存到提交 `8f222a7`。
- 分支：`codex/kiana-v12-upstream-20261008`。
- 合并上游 `origin/v1.x`，提交 `4924d00`；包含 36 个新增提交。
- Git 自动合并成功，无冲突；保留 Kiana 自定义功能。
- 完整 `renderdoc.sln` Development/x64 构建通过；修复后的 `renderdoc.vcxproj` 增量构建通过。
- 15 项 Kiana Python 回归通过，覆盖 IPC、FBX、Nsight 元数据及重建报告。
- 原有 DXGI/D3D12 早期导出测试在冷/热加载下通过。
- 导出地址兼容模式在冷/热加载下通过：解析地址一致，D3D11/D3D12 WARP 设备
  可开始/丢弃捕获，TLS、DllMain、DLL 重载、名称/序号解析和 RemoveHooks 恢复正常。
- 异常/退出观察测试通过：关闭时不生成日志，开启时记录访问违例和 `ExitProcess(999)`，
  两种模式的应用 SEH 处理和退出码均保持原样。

## 绝区零：v12 独立抓帧与回放

- 参数：`-force-d3d11 -screen-fullscreen 0 -screen-width 1280 -screen-height 720`。
- Unity 安全模式开启，捕获子进程开启。
- 文件：`E:\renderdoc\test-results\zzz-v12-20261008\capture_frame900.rdc`。
- 大小：99,442,432 字节。
- SHA-256：`f4297ce0b0e0b0958812fd8ee1769d7ed3134f93dbb22fc62a9f2bea82a9ef2b`。
- D3D11，314 个动作、265 次绘制、8 次计算、897 个资源、180 个着色器。
- 独立回放成功，最后事件 3668。

## 崩坏：星穹铁道：启动退出与修复验证

测试游戏版本 4.6.0，Unity 2019.4.34f1。普通启动正常。原有注入在第一帧前退出，
诊断记录到 `UnityPlayer.dll+0x1c41c` 调用 `ExitProcess(999)`，未记录所监听的异常。
D3D11、D3D12 和 NVAPI 对照均出现相同退出堆栈。图形导出诊断与只读反汇编定位到
`CreateDXGIFactory` 返回地址的模块范围检查；旧包装器地址落在 Kiana DLL 中。

设置 `KIANA_EXPORT_IDENTITY=1` 后，使用系统导出原始地址和入口 detour，成功启动
并完成 D3D11 设备/交换链注册、抓帧及独立回放。只修改 Kiana 捕获端代码。

- 文件：`E:\renderdoc\test-results\starrail-v12-diag-20261008-identity\capture_frame901.rdc`。
- 排队捕获帧 900，实际保存帧 901；27 秒内完成捕获。
- 大小：275,775,217 字节。
- SHA-256：`f3de8d25580800b16d16a9703baf2a9724157659b02a83daa52e2798ee6c37c8`。
- D3D11，189 个动作、167 次绘制、7 次计算、578 个资源、80 个着色器。
- 独立回放成功，最后事件 2333。
- 此次启用异常/退出观察日志；成功后未再记录 `ExitProcess(999)`。目标后来以代码 0
  结束。测试范围为启动到抓帧，未验证登录后长时间游戏。

同一修复还完成 D3D12 实测：引擎、目标 API 和独立回放均确认为 D3D12。

- 文件：`E:\renderdoc\test-results\starrail-v12-observed-20261008-20-d3d12\capture_frame716.rdc`。
- 启动 20 秒后触发捕获；大小 2,690,500 字节。
- SHA-256：`2e4eef71503d91941adbd782d91490c8885cfcc6f9d55b39234c7bce05352b8f`。
- 62 个动作、37 次绘制、137 个资源、29 个着色器，最后事件 944，独立回放 Success。

视觉核对发现 D3D12 样本的缩略图为黑色；启动 45 秒后的补充捕获也仍为黑色。
通过独立回放在最终 Present 事件导出交换链纹理后确认是黑色输出，不能将 API 回放
成功等同于有效游戏画面。崩铁默认推荐 D3D11；D3D12 画面兼容性仍待验证。

- 补充文件：`E:\renderdoc\test-results\starrail-v12-observed-20261008-45-d3d12\capture_frame2160.rdc`。
- 大小 2,639,897 字节；SHA-256：`b3f5e2e349d0ed601edfff2a371e8559d2be991f1bfaa9e3bbc3a2190a8f7a5d`。
- 同样为 37 次绘制，最终输出：同目录 `present.png`。

手动入口：便携目录内 `launch-export-identity.cmd`。MCP 设置
`preserve_export_identity=true`、`unity_safe_mode=true`、`hook_children=false`。
详细诊断开关与操作见 `DEBUGGING_AND_USAGE_CN.md`。

用户确认鸣潮正常并要求停止测试；本次未将中断测试计为 v12 完成抓帧验证。

## 崩坏 3：D3D11 / D3D12

游戏版本 9.1.0，Unity 2017.4.18f1。两个后端均使用导出地址兼容模式，关闭捕获子进程，
启动 30 秒后触发一帧捕获。引擎日志、目标 API 注册和 RDC 回放 API 均一致。

| 请求 / 实际 API | 帧号 | 绘制 | 资源 / 着色器 | RDC 大小 | 独立回放 |
| --- | ---: | ---: | --- | ---: | --- |
| D3D11 / D3D11 | 11478 | 89 | 322 / 66 | 46,065,596 字节 | Success |
| D3D12 / D3D12 | 8115 | 81 | 236 / 51 | 46,696,077 字节 | Success |

- D3D11：`E:\renderdoc\test-results\bh3-v12-observed-20261008-30\capture_frame11478.rdc`。
- D3D11 SHA-256：`14be795812854effd218d51067855c86f8e44269e7542ea2358be2f9f8c46d4f`。
- D3D12：`E:\renderdoc\test-results\bh3-v12-observed-20261008-30-d3d12\capture_frame8115.rdc`。
- D3D12 SHA-256：`65919e37f066b672318c2dbec507aaae8104368514ddb7d01d4a65e70e0e117d`。
- 预览确认是游戏的协议提示/加载界面；此轮未验证登录后战斗。
- D3D12 的最终 Present 纹理也已在独立回放中导出核对，画面正常。
- 早期帧 900 也能回放，但只有一次绘制，因此使用延迟捕获样本作为结果。

## 原神：空指针启动崩溃修复与后端测试

游戏版本 7.1.0，Unity 2017.4.30f1。原有捕获 DLL 启动后约 7 秒退出，代码
`0xC0000005`，异常地址 `YuanShen.exe+0xab4874`，读取地址 NULL。
设备创建标志 `0x81` 含 `D3D11_CREATE_DEVICE_PREVENT_ALTERING_LAYER_SETTINGS_FROM_REGISTRY`。
RenderDoc 会返回未包装的设备，却在系统调用中传入 NULL 上下文输出，随后也没有补回
调用者请求的真实上下文。修复保持未包装设备路径，同时将上下文输出传给系统实现。

新增 WARP 回归覆盖未包装的 device/context 和仅 context 两种创建方式；均通过。
修复后两次游戏启动均未记录所监听的异常，也没有在观察期间自行退出：

| 启动参数 | 实际引擎 API | 观察时间 | 抓帧结果 |
| --- | --- | ---: | --- |
| `-force-d3d11` | Direct3D 11 | 77 秒 | 没有完成 RDC |
| `-force-d3d12` | Direct3D 11 | 52 秒 | 参数未切换到 D3D12，没有完成 RDC |

上述对照仍未注册可捕获设备。进一步添加 opt-in 的
`KIANA_D3D11_CAPTURE_OVERRIDE=1`，明确启用设备包装，继续保留传给系统的应用标志。
同时修复仅请求上下文时临时设备的生命周期，使上下文正确取得并包装后再释放临时引用。
WARP 冷/热加载验证覆盖开关关闭/开启、设备/上下文和仅上下文两种输出，并检查实际
包装器所属模块；均通过。

原神实际 D3D11 抓帧通过：

- 文件：`E:\renderdoc\test-results\genshin-v12-observed-20261008-30-d3d11-override\capture_frame14579.rdc`。
- 启动 30 秒后触发捕获，34 秒内保存；大小 109,965,653 字节。
- SHA-256：`92f3410b84852b83acc3ba92b1c89ef44e5d5c70030d6db28d7d96e478d04b27`。
- 584 个动作、535 次绘制、22 次计算、751 个资源、106 个着色器。
- 最后事件 5810；独立回放 Success，无致命错误；观察日志没有记录所监听的异常。
- 预览确认实际画面为原神云海场景及资源下载界面。

最终便携包代码提交 `140c1e2`。经公开 MCP D3D11 编排函数再次验证新参数传递和
保存/回放，`preserve_export_identity=true`、`wrap_opted_out_devices=true` 均生效。
该次未开启异常/退出观察器，文件为
`E:\renderdoc\test-results\genshin-v12-final-20261008\capture_frame12000.rdc`。
捕获时仍处于较早的启动画面，仅 3 次绘制；实际云海画面的验证以上面的延迟捕获为准。

手动入口 `launch-genshin-capture.cmd`；MCP 设置 `preserve_export_identity=true`、
`wrap_opted_out_devices=true`、`unity_safe_mode=true`、`hook_children=false`。
本次未验证出该安装版本可使用 D3D12。对照测试进程由助手在等待超时后结束，退出码 0。
日志目录：`E:\renderdoc\test-results\genshin-v12-observed-20261008-30-d3d11` 和
`E:\renderdoc\test-results\genshin-v12-observed-20261008-20-d3d12`。

此前 v11 的测试结果保存在 `VALIDATION.md`，不作为 v12 的验证结果。

## GitHub main 合并回归

将 v12 源码快照 `fce519b` 的变更合入现有主分支 `96cb6fe`，保留 Kiana Studio、
Studio 启动/子进程捕获协议、事件指定的顶点阶段导出和 OBJ 导出。`studio/` 文件树
与合并前完全一致；未将本地 RDC、构建产物或第三方依赖二进制加入此次提交。

合并后检查：

- Native 源码与上述游戏实测版本一致；在带本地构建依赖的原工作目录重新构建
  x64 Development，完整解决方案通过。
- 在合并目录运行 Python 单元测试：19 项通过，包括四项 Studio 捕获协议测试。
  FBX 测试改用临时目录，干净检出无需预先运行 Native 测试。
- 在合并目录运行 Native 图形挂钩测试，使用本次重新构建的捕获 DLL：默认配置、
  导出地址兼容模式，以及 D3D11 设备包装开关开启/关闭，冷/热加载全部通过。
- 异常观察器开启/关闭均通过：SEH 继续传播，`ExitProcess(999)` 保持原退出码。
- Python 语法编译与 Git 补丁空白检查通过。

此项回归未重新启动游戏，实际抓帧结果和后端限制以上文记录为准。
