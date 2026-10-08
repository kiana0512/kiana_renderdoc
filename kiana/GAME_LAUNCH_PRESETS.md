# Kiana v12 游戏默认启动参数

验证日期：2026-10-08，Windows x64，RTX 4070 Ti SUPER。使用本次修复后的便携目录
`E:\renderdoc\dist\Kiana-1.47-v12-release-x64`。下面的参数用于 Kiana 的
**Launch Application**；工作目录填对应 EXE 所在文件夹。

## 快速选择

| 游戏 | 默认 API | D3D11 实测 | D3D12 实测 | 启动 Kiana 的入口 |
| --- | --- | --- | --- | --- |
| 绝区零 | D3D11 | 抓帧、回放通过 | 本轮未测试 | `kiana_qrenderdoc.exe` |
| 鸣潮 | D3D12 | 本轮未测试 | 用户确认正常；按要求停止重测 | `kiana_qrenderdoc.exe` |
| 崩坏：星穹铁道 | D3D11 | 抓帧、回放通过 | 可保存/回放，但输出黑色，暂不推荐 | `launch-export-identity.cmd` |
| 崩坏 3 | D3D11 | 抓帧、回放通过 | 抓帧、回放通过 | `launch-export-identity.cmd` |
| 原神 | D3D11 | 抓帧、回放通过 | `-force-d3d12` 未生效，实际仍为 D3D11 | `launch-genshin-capture.cmd` |

两个 CMD 都会打开便携目录内的新 Kiana 窗口。进入该窗口的 **Launch Application**
填写下面的游戏配置。脚本设置的环境变量会传给新启动的目标；也可以直接在 GUI
的环境变量对话框按下表设置。抓帧快捷键为 **F12** 或 **PrintScreen**。

## 共用捕获设置与环境变量

全部关闭 **Allow Fullscreen**。Unity 游戏推荐窗口化参数：

```text
-force-d3d11 -screen-fullscreen 0 -screen-width 1280 -screen-height 720
```

崩坏 3 的 D3D12 已验证有实际画面，可将第一项改成 `-force-d3d12`，其他参数保持相同。
崩铁的 D3D12 试验保存了 RDC，但最终输出为黑色，默认继续使用 D3D11。

| 游戏 | Capture Child Processes | KIANA_UNITY_SAFE_MODE | KIANA_EXPORT_IDENTITY | KIANA_D3D11_CAPTURE_OVERRIDE |
| --- | --- | --- | --- | --- |
| 绝区零 | 开 | `1` | `0` | `0` |
| 鸣潮 | 开 | `0` | `0` | `0` |
| 崩铁 | 关 | `1` | `1` | `0` |
| 崩坏 3 | 关 | `1` | `1` | `0` |
| 原神 | 关 | `1` | `1` | `1` |

`KIANA_EXPORT_IDENTITY=1` 保留系统图形导出的原始地址，并通过入口 detour 捕获。
`KIANA_D3D11_CAPTURE_OVERRIDE=1` 明确启用 D3D11 设备包装；原神需要此项。
这两个兼容开关在普通入口默认关闭。

## 绝区零

- 程序：`D:\miHoYo Launcher\games\ZenlessZoneZero Game\ZenlessZoneZero.exe`
- 工作目录：`D:\miHoYo Launcher\games\ZenlessZoneZero Game`
- 参数：`-force-d3d11 -screen-fullscreen 0 -screen-width 1280 -screen-height 720`
- 自动捕获帧：`900`；也可进入目标界面后按 F12。
- 本次验证：D3D11，265 次绘制、8 次计算，RDC 独立回放通过。

## 鸣潮

- 程序：`D:\Wuthering Waves\Wuthering Waves Game\Wuthering Waves.exe`
- 工作目录：`D:\Wuthering Waves\Wuthering Waves Game`
- 参数：`-krqlv=hd`
- 勾选捕获子进程，连接实际渲染进程 `Client-Win64-Shipping.exe`。
- 确认连接页显示 **D3D12** 后，在目标画面按 F12。
- 用户已确认正常，本轮按要求停止测试；既有配置沿用此前验证结果。

## 崩坏：星穹铁道

- 程序：`D:\miHoYo Launcher\games\Star Rail Game\StarRail.exe`
- 工作目录：`D:\miHoYo Launcher\games\Star Rail Game`
- 默认参数：`-force-d3d11 -screen-fullscreen 0 -screen-width 1280 -screen-height 720`
- D3D12 试验参数：`-force-d3d12 -screen-fullscreen 0 -screen-width 1280 -screen-height 720`
- D3D11 可排队捕获第 `900` 帧，已验证 167 次绘制、7 次计算，回放为列车/星空画面。
- D3D12 在启动 20 秒和 45 秒后均保存了 RDC，37 次绘制，回放 API 无错误；最终
  Present 纹理仍是黑色，未验证出有效游戏画面，暂不作为推荐配置。
- 修复前的 `ExitProcess(999)` 启动退出由导出地址兼容模式解决。

## 崩坏 3

- 程序：`D:\miHoYo Launcher\games\Honkai Impact 3rd Game\BH3.exe`
- 工作目录：`D:\miHoYo Launcher\games\Honkai Impact 3rd Game`
- 默认参数：`-force-d3d11 -screen-fullscreen 0 -screen-width 1280 -screen-height 720`
- D3D12 参数：`-force-d3d12 -screen-fullscreen 0 -screen-width 1280 -screen-height 720`
- 推荐启动约 `30` 秒、看到目标界面后按 F12。该游戏启动阶段帧率较高，第 900 帧
  可能只有启动画面。
- D3D11：89 次绘制；D3D12：81 次绘制，两份 RDC 均回放通过。

## 原神

- 程序：`D:\miHoYo Launcher\games\Genshin Impact Game\YuanShen.exe`
- 工作目录：`D:\miHoYo Launcher\games\Genshin Impact Game`
- 参数：`-force-d3d11 -screen-fullscreen 0 -screen-width 1280 -screen-height 720`
- 使用 `launch-genshin-capture.cmd`，或在启动环境中启用上表的三个开关。
- 推荐启动约 `30` 秒、看到目标界面后按 F12。
- 本次实际捕获：约 110 MB，535 次绘制、22 次计算、106 个着色器，独立回放通过。
- 本次安装版本传入 `-force-d3d12` 后仍使用 Direct3D 11，推荐保持上述 D3D11 参数。

原神还需要设备包装开关。只启用导出地址兼容模式可以修复启动空指针崩溃，但设备
仍未进入捕获路径，无法保存 RDC。

## MCP 的 D3D11 参数

| 游戏 | unity_safe_mode | preserve_export_identity | wrap_opted_out_devices | hook_children |
| --- | --- | --- | --- | --- |
| 绝区零 | `true` | `false` | `false` | `true` |
| 崩铁 / 崩坏 3 | `true` | `true` | `false` | `false` |
| 原神 | `true` | `true` | `true` | `false` |

调用 `capture_kiana_d3d11`，传入对应 `executable`、`working_dir` 和参数列表。
`output_dir` 应为新目录或空目录。该工具保存后会独立回放验证 RDC。
游戏启动帧率不同，手动捕获时以目标画面已出现为准。

需要定位新故障时，可另外开启 `KIANA_CAPTURE_DIAGNOSTICS=1`。
异常/退出堆栈记录还需要 `KIANA_CRASH_DIAGNOSTICS=1` 和指向现有目录的
`KIANA_CRASH_LOG`。这两个诊断开关不属于日常抓帧必需参数。

本轮验证范围是启动、加载或协议提示界面；尚未验证登录后的长时间战斗。
文件路径、SHA-256 和完整回归记录见 [VALIDATION_V12.md](VALIDATION_V12.md)。
