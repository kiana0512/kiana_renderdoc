# Frame 38112：双 MCP 接线与 EID912 金属分支

日期：2026-09-28

## 运行链

- Kiana Studio Electron 同时探测两个真实端点：Kiana RenderDoc MCP `http://127.0.0.1:8765/mcp` 与 Unity Pipeline `127.0.0.1:7800`。
- RenderDoc HTTP MCP 已完成 initialize/list_tools，返回 47 个工具；包含 `open_capture`、`get_pipeline_state` 与 `export_fbx`。
- 通过 HTTP MCP 打开 `E:/KianaFrame38112Workspace/Frame38112Capture/capture_frame38112.rdc`，状态为 D3D11、Frame 38112、207 draws、38 dispatches、3346 calls。
- MCP 查询 EID912 得到 VS31464、PS31475、8 个 fragment textures、4 个 fragment cbuffers、RT0–RT3 为 RID53242/53246/53250/53254、Depth RID53238。
- Unity 6000.6.3f1 工程在 7800 ready，编译及控制台均为 0 error / 0 warning。

安装版此前缺少 `mcp/src/launch_http.py`，且 Studio 会把安装目录错误上溯到 AppData。现已修正运行时根目录选择，并把 streamable HTTP 启动器加入 `E:/renderdoc/kiana/mcp/src/launch_http.py`。Studio 启动后会拉起本机 8765 服务，状态栏只在端口真实可连接时显示 RenderDoc MCP 在线。

## EID912 A/B

金标准：相邻源快照 EID895→EID912 在 RID53242 上的 119,264 个变化像素。基线和候选均由同一 Unity Game 相机调用 `CaptureGBuffer5Stages.Capture(912)` 生成。

| 候选 | changed-region RGB MAE |
| --- | ---: |
| 保存前基线 | 18.6877 |
| 源分支 100% | 24.8518（拒绝） |
| blend 0.20 | 17.9940 |
| blend 0.25 | 17.9038 |
| **blend 0.30** | **17.8549** |
| blend 0.35 | 17.8631 |
| blend 0.40 | 17.9294 |

新增 `_UseSourceMetal912` 独立开关。分支依照 PS31475：

- 指令 431–432：`diffuse = .96 * (1 - t5.g) * base`；
- 指令 433–434：`F0 = lerp(.04, base, t5.g)`；
- 漫反射与高光分别计算后再合成，不再把 t5.g 衰减乘到已含高光的最终颜色上；
- 仅 EID912 开启，且通过 `_SourceMetalBlend=0.30` 限制在已验证区间。

固定 blend 0.30 后继续扫描独立 F0 spec scale：0/0.5/1/1.5/2/3/3.5/4/5/6/8/10/12/16/20/24/27/30/32/35/40/50/70/100。scale 27 的实拍 MAE 最低，为 **15.6761**，相对本轮基线改善约 16.1%，已保存。scale 27 是对当前近似半向量 lobe 能量不足的补偿；在恢复 PS31475 指令 435–528 的真实 roughness/half-vector 后应重新标定并尽量移除。

保存图：

- `Assets/Kiana/Validation/StageRenders/EID912-source-metal-baseline-20260928.png`
- `Assets/Kiana/Validation/StageRenders/EID912-source-metal-candidate-blend030.png`
- `Assets/Kiana/Validation/StageRenders/EID912-source-metal-spec2700.png`
- `Assets/Kiana/Validation/FinalComposite-Stage2475-TEMP.png`

最终复捕获 EID1331 与 4K FinalComposite 成功，Unity 控制台仍为零错误。下一轮继续用 PS31475 指令 435–528 恢复 roughness、half-vector 和白色反射分布；每个候选继续保留开关并以相邻源 RT0 差分验收。
