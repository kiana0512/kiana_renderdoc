# Frame 38112 → Unity 6.6 重建记录

更新：2026-09-26。目标是在 Unity 原生重建模型、姿态、G-buffer 材质、背景、后处理和 2D UI，与 RDC 的 3840×2160 最终输出比较。最终帧 PNG 仅作参考，不作为重建内容贴到四边形上。

| 输入 | 路径或数值 |
| --- | --- |
| RDC | `E:\KianaCaptures\ZenlessZoneZero\绝区零-1790334599799\capture_frame38112.rdc` |
| 分析目录 | `E:\KianaCaptures\ZenlessZoneZero\绝区零-1790334599799\analysis-frame38112` |
| Unity 工程 | `F:\KianaFrame38112Unity`，Unity 6.6.3f1 |
| 当前可编辑 3D 场景 | `Assets/Kiana/Scenes/Frame38112_GBuffer5_World.unity` |
| 捕获概况 | D3D11；207 draws；38 dispatches；13 个分析 pass |
| G-buffer pass 5 | EID 821–1332；26 draws；663,852 indices；2880×1368；RT 53242/53246/53250/53254；深度 53238 |

## 阶段与现状

| 阶段 | 已完成的证据 | 尚未通过的验收 |
| --- | --- | --- |
| 1. Draw 与纹理清单 | `Assets/Kiana/Manifest/gbuffer5-bindings.json` 列出 26 个精确 EID 和 24 个唯一绑定贴图，含 fragment 与 vertex 槽位；已修正旧清单遗漏 EID 1202、1287。| 扩展到其余 12 个 pass，区分“绑定”与“实际采样”。 |
| 2. 3D 几何与姿态 | 26 个 IA 网格导入 Unity Mesh，每 draw 用自己的 VS `cb1[0..3]` 局部到世界矩阵。前 10 个基础 draw 的全部顶点与 VSOut 最大 clip 误差 < 0.000185；是真 3D 网格，有厚度。| EID 1057–1202/1331 的额外 VS 位移未实现；EID 1202 最大误差约 0.066。骨骼和动画时间轴尚未恢复。 |
| 3. 相机与眼部 | `cb0[127..130]` 加 `cb0[21].xy` 得到捕获 VP；`CapturedCameraMatrix.cs` 在场景重开后恢复投影。EID 1273 眼部 draw 已纳入场景；26 个 draw 的剔面及深度写入状态已提取。EID 1273 的 Eye_E 顶点查表与 426/426 个 VSOut 完全一致，并已按源 RT0 混合、关闭深度写入。已按 EID 固定 Unity draw 顺序，并仅在 RDC 相机渲染时翻转深度。| 其他材质的模板、混合、原 shader 与某些后期眼部 draw 尚未复现；剔面仍保留已验证的双面基线。 |
| 4. 贴图与材质 | 脸部 atlas `RID42972`、眼部资源 `RID23285` 已导出。EID 992 的 VS 把 IA `TEXCOORD0` 传给 PS `v0.xy`，PS 在 `t3` 采样 albedo；当前 Unity shader 翻转 UV 的 V 后，脸底色和红瞳回到对应区域。6 张 BC6 材质图与面部浮点 lightmap 已按线性 `RGBAHalf` EXR 导入并绑定 22 个材质槽；`RID42021` 已按源 DDS 导入 256×256×16 BC7 数组并绑定 7 个材质。26 个 Unity 材质标记各自源 PS，9 个身体 draw 的动态 band 表写入各材质；眼部专用顶点查表和 RT0 混合已启用。| 全部 10 个源 PS 的输出方程、4 个 G-buffer RT、mask、overlay、结构化光源、阴影、描边和多数透明材质仍未完整复现。脸部和描边候选路径待阶段验收。 |
| 5. 背景、后处理、UI | G-buffer 场景黑底已保存；UI 的四个背景 draw 已按 RDC 顶点、UV、贴图做成独立 Unity 场景。| 其余 UI draw、阶段合成和最终画面尚未完成。 |
| 6. 像素验证 | 已按 EID 导出 pass 5 的 RID 53242 阶段快照。经 UV 与第一版法线光照修正，EID 945 前景 IoU 98.93%、RGB MAE 19.11/255；旧版 EID 945 为 97.94%、43.63。| 颜色、阴影、线条和材质仍未过关；其他后期 draw、UI 与最终 3840×2160 对照未通过。 |

## 关键定位结果

1. **脸部贴图方向错误已定位。** RDC 面部 VS 将输入 `v4.xy` 原样传给 PS `v0.xy`，PS 使用 `v0.xy` 采样 `t3` (`RID42972`)；Kiana FBX 的第一个 UV 块就是该输入。导出的 PNG 在 Unity 采样方向与 D3D 坐标不同，shader 改为 `float2(u, 1-v)` 后，单独的脸由额头/脸颊错误白块恢复出肤色与红瞳。验证图：`Assets/Kiana/Validation/gbuffer5-face-eye-flipv.png`。这只修正纹理方向，尚未通过整体遮挡和原 shader 验证。
2. **眼白是中间阶段。** RID 53242 的逐 EID 截图：EID 1035 后呈白色；EID 1273 改动 4,462 像素（x 888–1144、y 873–924），红色虹膜出现；EID 1331 是 pass 5 最终状态。EID 1273 还绑定 VS 槽 1 `Eye_E` 资源 `RID23285`，不能只把 face atlas 当作全部眼部效果。
3. **3D 位置以整网格验证。** `scripts/validate_gbuffer_vertices.py` 对每个 IA 顶点应用对应的 `cb1` 和 VP，与捕获 VSOut 比较。EID 992 面部和 EID 1273 眼部等基础 draw 最大误差 < 0.00019。高误差 draw 对应额外 VS 处理；不再以手调脸位置掩盖问题。
4. **Game 视图遮挡已定位并纠正。** 原先 Unity 不按 RDC EID 次序绘制同队列 opaque 网格，且捕获相机下的深度排序方向与 RDC 相反，因此 EID 992 脸被先前网格挡住。`CapturedAlbedo.shader` 仅在捕获相机渲染时以 `z' = w - z` 换算深度；`CapturedCameraMatrix` 通过 `OnPreRender/OnPostRender` 控制全局值，Scene 视图维持普通深度。材质 queue 固定为 `2000 + draw 序号`，EID 992/1035 现按源画面覆盖脸。Unity Scene 视图截图 `Assets/Kiana/Validation/scene-after-camera-only-depth.png` 确认角色和眼睛正常。**暂未启用**直接映射的剔面/模板/混合，失败诊断图 `gbuffer5-world-perdrawstate-final.png` 仍留作证据。

## 2026-09-26 阶段对照

取 RDC 的 RID 53242 快照与 Unity `Assets/Kiana/Validation/StageRenders/` 同尺寸 PNG；`scripts/compare_stage_pngs.py` 以 RGB 任一通道大于 8 为前景，统计交并比和交集内 RGB 平均绝对误差。这里测的是 **G-buffer 5 的阶段输出**，不是最终 RT。下表是修复背面 UV 以前的历史基线；当前 EID 858–945 数值见后文。

| EID | 前景 IoU | RGB MAE / 255 | 当前判断 |
| ---: | ---: | ---: | --- |
| 945 | 0.9794 | 43.63 | 身体正面和伞位置对齐；材质暗部差明显。 |
| 992 | 0.9888 | 39.51 | 脸出现且位置对齐；脸部 shader/颜色仍简化。 |
| 1035 | 0.9900 | 39.79 | 眼白中间阶段可见。 |
| 1273 | 0.9820 | 41.48 | 红色虹膜可见；Unity 目前只启用基础 10 draw 加 EID 1273，源画面还包含其余阶段 draw，不能将此数值当作 pass 5 完成。 |

已从 RDC 导出 pass 5 的 10 种唯一像素 shader，并用 `scripts/analyze_shader_texture_slots.py` 对 26 个 draw 的静态采样指令和绑定清单交叉核对，结果在 `docs/frame38112-gbuffer5-shader-slots.json`。有纹理绑定的 shader 均静态引用所有绑定的 fragment 纹理槽；`t1` 是 structured buffer，单列处理。**这不代表当前 Unity shader 已使用这些纹理**：Unity 当前颜色路径采样 albedo `t3`，并在法线光照路径采样 normal `t4`；材质 mask、overlay、阴影仍需逐 shader 实现。EID 1202、1287 的源像素 shader 无纹理绑定，按程序常量和顶点数据处理。

像素阶段的全部 26 个 draw 的常量缓冲已由 `scripts/inspect_pixel_cbuffers.py` 从独立 RDC 回放导出为分析目录的 `gbuffer5-pixel-cbuffers-all.json`；`scripts/build_gbuffer5_pixel_constants.py` 结合反汇编，只保留实际指令直接引用的寄存器，生成仓库内 `docs/frame38112-gbuffer5-pixel-constants.json`。EID 945 的 PS 31475 绑定 `cb0` 3392 B、`cb1` 464 B、`cb2` 656 B、`cb3` 2048 B；脸部 EID 992 的 PS 31476 有 `cb3` 1376 B。两者的基础 albedo 乘色常量分别为 `cb3[38].rgb=(1,1,1)` 和 `cb3[29].rgb=(1,1,1)`，因此伞/服饰暗部与 RDC 差 40 左右的 RGB 误差并非遗漏了一个统一的贴图 Tint。源 PS 在 albedo 之外继续读取法线、mask、overlay、阴影、逐像素光照，并向 4 个 G-buffer RT 输出；下一步要按这条数据流逐 shader 实现和核对，不能以全局调暗替代。

纹理格式审计发现 `RID42862/42880/42887/42888/42967/42968` 是 **BC6_UFLOAT**，RenderDoc 原始通道峰值达 1.26–9.31；8 位 PNG 会截断或量化这些材质数据。已通过运行中的 Kiana RenderDoc 导出 mip 0 EXR 到分析目录 `gbuffer5-hdr-textures/`，复制进 Unity `Assets/Kiana/Textures/HDR/`，设置线性、未压缩导入；Unity 校验 `RID42888` 为 2048×2048 `RGBAHalf`、`sRGB=false`。`RID25406` 面部浮点 lightmap 也同样处理。`RID42021` 是 16 slice 的 BC7_SRGB 数组：单 PNG 只覆盖第一层，现用 RenderDoc DDS 导出并通过 `assets/ImportKianaTextureArray.cs` 导入真正的 `Texture2DArray`，Unity 校验 256×256×16 BC7，绑定到 7 个 draw 的 `_Slot7Array`。目前只保留源 mip 0；后续要核对其他 mip 的采样影响。**绑定成功不代表已被现有 Unity shader 采样。**

EID 1331 将全部 26 个 draw 强制启用的诊断结果为前景 IoU 0.9823、RGB MAE 46.47，比 EID 1273 基线更差；RDC 源 EID 1273→1331 仅约 1,327 像素变化。说明后续 draw 不能只按原队列打开，需复现各自的深度/模板/混合、VS 位移和像素 shader。诊断截图 `Assets/Kiana/Validation/StageRenders/EID1331-through.png`，场景启用状态已由捕捉工具恢复。

Unity 6.6 安装 `F:\unity_\6000.6.3f1` 缺失 Package Manager Server，2026-09-26 改从完整的 `F:\unity_\6000.6.3f1-x86_64` 启动，Pipeline 连接正常。Kiana Studio 和 `kiana_qrenderdoc.exe` 已启动。Scene 视图使用相机专用深度修正后再次截图验证。

## 可复现脚本与下一步

### 2026-09-26：背面发丝 UV 与第一版法线光照

用户指出 Scene 视图后发出现大片黑色条纹。对照 PS 31475 反汇编：`cb3[116].x=1` 的 draw 在背面用 `v0.zw` 采样 `t3/t4/t5`；此前 Unity 把 FBX 第三个 UV 块当成 `v0.zw`，但它实际对应另一个 VS 输出。`scripts/audit_ps_uv_streams.py` 将 KMF 与 VSOut 按顶点核对，发现 EID 858/875/928/945 的 UV 差值最大分别为 0.750/0.859/0.649/0.925。已将真正的 VSOut `v0.zw` 写入 `Assets/Kiana/MeshData/PSUV/`，`ApplyCapturedPSUV.cs` 原位修正现有 Mesh 的 `uv3`。导入器 `ImportKianaMesh.ImportAll()` 现在保留 Mesh 资产 GUID，并自动重施 UV 覆盖；重新导入不会断开场景引用或把后发改回错误纹理。Scene 后视角记录：`Assets/Kiana/Validation/scene-rear-hair-uv3.png`。RDC 当前帧的 EID 945 视角没有完整展示背面发型，因此后视角仍需单独来源验证，不能称为 1:1。

相机投影下 Unity `VFACE` 符号与源 PS 相反。`CapturedCameraMatrix.cs` 只在 RDC 相机渲染期间设 `_RdcFaceFlip=1`，结束恢复为 0；Scene 视图独立显示。源 PS 的法线采样分支已作为 Unity shader 的可调试路径实现，读取 `t4` normal，按 tangent/bitangent/normal 与正反面组成世界法线。EID 945 的源法线 RT 53254 与 Unity `_DebugOutput=1` 截图对照：前景 IoU 0.99065、RGB MAE 15.92/255。调试模式已恢复为 0；仍要核实 TBN 细节和全部面部材质分支。

`scripts/fit_stage_lighting.py` 从 RDC EID 945 颜色 RT 53242、法线 RT 53254 与 Unity 纯贴图渲染，仅在约 1 万个肤色样本上拟合了**诊断用**环境项加单方向漫反射：方向 `(-0.134544, 0.944284, 0.300376)`、环境 0.787676、漫反射 0.281438。Unity 场景根上的 `CapturedLightingParameters` 持久设置这组参数，六个首批角色材质启用 `_UseCapturedLight`。它改善了整幅 pass 阶段误差，但**不是**游戏的全局光照系统：PS 31475 的 `t1` structured light buffer、mask、overlay、阴影、特定材质响应尚未搬入 Unity。用户指出的“黑皮”不应靠统一肤色调暗解决；当前是由 normal 决定局部明暗的临时模型。

| EID | UV 修正后纯贴图 MAE | 加法线光照后 MAE | 加光照后 IoU |
| ---: | ---: | ---: | ---: |
| 858 | 33.37 | 24.31 | 0.9950 |
| 875 | 29.04 | 21.71 | 0.9984 |
| 895 | 30.42 | 21.95 | 0.9971 |
| 912 | 30.22 | 22.24 | 0.9892 |
| 928 | 30.22 | 22.24 | 0.9892 |
| 945 | 27.36 | 19.11 | 0.9893 |

比较图在 `Assets/Kiana/Validation/StageRenders/EID*-simple-light.png`。这些误差按前景交集 RGB 计算、单位 0–255；IoU 高只说明位置/轮廓接近。EID 945 的局部皮肤仍缺捕获 PS 的非线性漫反射、投影阴影与高光，金属和发丝也缺对应材质分支。下一步按 PS 31475 的 `t5/t6/t7/t8` 和 `t1` 数据流逐项移植，并分别对 RT 53242/53246/53250/53254 做图像验收，再扩展到其他 PS 和后续 pass。

- `.agents/skills/rdc-unity-frame/scripts/inspect_postvs.py` 用 Kiana 内置 `kiana_qrenderdoc.exe --python=...` 独立回放，获取 post-VS、VS CB；证据为 `docs/frame38112-vs-cbuffers.json` 和 `docs/frame38112-postvs-probe.json`。
- `build_gbuffer5_manifest.py`、`build_gbuffer5_transforms.py` 生成 Unity 的纹理槽和 per-EID 变换 manifest；`validate_gbuffer_vertices.py` 验证整网格 clip 坐标。
- `export_gbuffer_snapshots.py` 按 EID 导出 RT 53242；`inspect_gbuffer_shaders.py` 导出 VS/PS 反汇编；`inspect_gbuffer_state.py` 与 `build_gbuffer5_states.py` 保存逐 draw 光栅/深度状态及 Unity 材质参数。
- `inspect_pixel_cbuffers.py` 提取 26 个 draw 的 PS 常量缓冲；`build_gbuffer5_pixel_constants.py` 与反汇编交叉核对，只将被 shader 指令直接引用的寄存器写入仓库证据文件。
- `assets/BuildGBuffer5World.cs`、`CapturedCameraMatrix.cs`、`CapturedAlbedo.shader` 构造当前 Unity 原生 3D 阶段；`CaptureGBuffer5Stages.cs` 临时切换 draw 启用状态，渲染后恢复；`scripts/compare_stage_pngs.py` 比对源/Unity PNG。修改后复制到 Unity 工程，通过 Unity CLI 刷新并让 Editor 保存场景。
- `assets/BuildGBuffer5World.cs` 的 `ConfigureFloatTextureImporters()` 和 `UpgradeFloatTextureBindings()` 可重现 EXR 导入/绑定；`assets/ImportKianaTextureArray.cs` 从 RenderDoc DDS 读取 16 个 BC7 slice，`BindTextureArray()` 将其绑定到相应材质。2026-09-26 Scene 视图截图 `Assets/Kiana/Validation/scene-after-hdr-binding.png` 核对角色、脸和红瞳仍正常，相机全局 `_RdcDepthFlip=0`。
- 2026-09-25 收尾核验：`ValidateBaseColorBindings()` 在 Unity Editor 验证 **24/26** draw 的材质 `mainTexture` 指向正确 RDC PNG，另 2 个 draw（EID 1202、1287）在绑定清单中原本无 albedo；5 个唯一 base color PNG 均存在。EID 992/1273 的 `_Cull=0,_ZWrite=1`，眼部 draw 启用，已保存当前场景。
- 接下来核实 G-buffer 5 的实际 shader 采样及材质 mask/法线/描边，复现 EID 1057–1331 额外 VS 位移、Eye_E 和 stencil/blend；逐 draw 对照 RT 53242/53246/53250/53254 与深度 53238。此后按 pass 6–13 推进背景、后处理与 UI，并与最终 3840×2160 RT 对照。每个阶段留下截图和数值比较。

`Frame38112_GBuffer5_VSOut.unity` 只用于裁剪空间投影校验，其平面不是 3D 成果。`Frame38112_ExactOutput.unity` 是早期参考图展示，也不是目标成果。

### 2026-09-26：材质家族、像素追踪与同场景验收

用户确认当前主要差距是材质几乎只有 basecolor，因此这一轮先覆盖 **全部 26 个材质的源 PS 身份**，暂缓局部像素微调。`docs/frame38112-gbuffer5-shader-slots.json` 列出 10 个 PS ID：31475、42681、31476、33678、31478、31479、24167、31480、31489、31482。源反汇编表明它们不能共享同一套纹理语义：身体类 PS31475/42681/33678 的 `t3` 是颜色、`t4` 是法线、`t5/t6` 是材质控制、`t7` 是分层数组；脸类 PS31476/31480/31489 的 `t3` 是颜色、`t4` 是面部浮点 lightmap；描边类 PS31478/31479 的 `t2` 是颜色，31479 的 `t3` 是 band 控制，`t4` 是阴影纹理。PS24167 的颜色来自顶点输入 `v1.x`，PS31482 没有颜色纹理采样而执行 discard/深度相关逻辑。此前的 Unity 共用 shader 把所有 `t4` 当法线，是材质结构错误。

`assets/CapturedAlbedo.shader` 增加 `_RdcPixelShader` 和分家代码；`assets/ApplyCapturedMaterialFamilies.cs` 原位写入 26 个现有 Material，避免重建场景和 GUID。`assets/BuildGBuffer5World.cs` 也写入 PS ID，并在将来重建时调用家族赋值器。`scripts/extract_material_tables.py` 现同时覆盖 PS31475/42681/33678，生成 `docs/frame38112-material-tables.json`：**9 个身体 draw、6 套不同 band 表**。五个 band 的源 tint、数组 slice、weight、cap、mode 已逐材质写入 `_Band0..4Tint` 与 `_Band0..4Control`。此前 EID945 硬编码候选已改为读取逐材质 band。材质数组候选仍由 `_UseCapturedWeaponPalette` 控制，因 EID945 旧版候选会恶化 MAE，当前保持关闭；写入参数不等于源 PS 已完成。

分家代码对脸类的 `t4` 不再当法线解码，并给 face/eye、outline、常量、discard 类设置不同候选路径。对 **同一当前 Unity 场景** 做 `_RdcFamilyEnabled` A/B：EID992 关闭脸候选 MAE **18.276**，开启 **18.525**；早期 EID1273 未接入 Eye_E 与源混合状态时，关闭候选 MAE **21.403**，开启 **21.493**。脸与描边候选仍关闭；眼部候选在后续恢复源顶点查表及混合状态并重新通过 A/B 后已启用，详见下文。`EID992-before-families.png` 是更早状态的历史阶段图，39.51→18.53 的表面改善包含中途几何/材质状态变化，**不能归因于本次分家**。同状态 A/B 的数值才用于开关决策。

直接 RDC 像素追踪可用 `scripts/inspect_pixel_trace.py` 配合 `scripts/run_bundled_renderdoc_python.ps1`，证据 `docs/frame38112-pixel-trace-eid945.json`、`docs/frame38112-pixel-trace-eid945-bands.json` 和 `docs/frame38112-pixel-trace-candidates.json`。源 PS31475 的 `t2` CharacterOverlayTex 约为 0.5 中性值；指令 70–71 在内部寄存器做 **base + overlay − 0.5**，而旧 Unity 诊断直接相加造成 MAE 50.55。随后还有条件选择、材质数组和非线性光照，不能把单条采样直接接到最终色。`inspect_pixel_history.py` 对几个已知像素的 PixelHistory 返回空修改列表，尽管 RT 资源尺寸正确；该接口在当前 D3D11 回放路径的证据不足，未据此推断无绘制。

`scripts/restore_rdc_index_order.py` 审计 IA/KMF 三角形与 RDC 原索引：26/26 unordered 三角形集合一致，但 21/26 的排列顺序不同；审计为 `docs/frame38112-index-order-audit.json`。原始索引已存于 Unity `Assets/Kiana/MeshData/PSIndices/`，`assets/ApplyCapturedPSIndices.cs` 可在导入后恢复源顺序。单独对 EID945 应用后，仅 1 像素变化，MAE 19.111935→19.111889，因此序列不同真实存在，但不是当前主要着色误差；不要用它解释脸/材质问题。

`scripts/extract_outline_material_tables.py` 从 PS31478/31479 的逐 draw `cb3` 提取 **10 个描边材质** 的调色表：PS31478 用 `cb3[36..38]`，PS31479 用 `cb3[49..53]`，结果为 `docs/frame38112-outline-material-tables.json`。Unity 每个描边 Material 的 `_OutlineBand0..4` 已分别写入，EID1078 的 band0 `(.5018245,.4401477,.5943396,1)` 在现场读取核验通过。候选 shader 使用 PS31479 的 `t3.r` 选择 band、`t2` 采样颜色；源 `v5.w` 顶点选择量现已精确映射，详见下文。后续 HSV/光照输出尚未实现，因此描边候选仍关闭。

`scripts/extract_face_material_tables.py` 另将 PS31476/31480 的 **4 个脸部 draw** 的 `cb3[29..35]` 色彩/明暗行写入 `docs/frame38112-face-material-tables.json` 和 Unity 各材质 `_FaceColor29..35`。EID992 的 `_FaceColor30.y=0.913099` 已现场读取核验。眼部 PS31489 使用另一套寄存器与预乘 alpha 输出，不得直接套用脸部 `cb3` 表。shader 中脸部 lightmap 候选仍需要确定 `v0.zw` 的 Unity 数据流及源 PS 后段光照方程，因此保持关闭。

当前材质覆盖的准确表述：**26/26 绑定源 PS ID，9/9 身体类 band 表、10/10 描边类调色表、4/4 脸部固定色彩行已绑定；眼部 EID1273 顶点查表已验证并启用；0/26 达到源像素 shader 的全部采样与四 RT 输出等价。** `docs/frame38112-material-coverage.json` 记录每个 EID 的已执行颜色采样、待实现槽位及这些参数绑定状态。下一轮先完善每一材质家族的有效颜色、法线/lightmap、mask、光照、阴影和透明方程，按 EID 原始状态依次开启后续 draw；逐家族比较同分辨率 RT 53242/53246/53250/53254 与 Unity 输出。不能把仅有 PS 分组或纹理绑槽写成“材质还原完成”。

### 2026-09-26：场景黑底与 RDC 原生 UI 背景第一批 draw

Unity `Frame38112_GBuffer5_World.unity` 的 Scene 视图原来显示 Unity 默认棕色天空和地面，误导对 G-buffer 阶段的判断。现已用 `GBufferBlackSkybox.shader` 和 `GBuffer5_BlackSkybox.mat` 将此场景的天空盒设为纯黑、关闭雾；Scene 视图仍能自由检查真实 3D 网格。截图 `Assets/Kiana/Validation/scene-gbuffer-black-skybox.png` 已在 Unity 6.6 现场核对并保存。黑底对应 **pass 5 阶段**，并不表示最终 2D 背景完成。

从 RDC UI 段确认 EID 2237/2246 绑定 `GeneralPageBG2`（RID 30499，4096×716），EID 2280 绑定 `GeneralBgLight`（RID 30512，280×160），EID 2307 绑定 `GeneralPageBG1`（RID 30497，2056×128）。资源通过 Kiana 导出到 `Assets/Kiana/Textures/Background/`，包含各自 alpha，而不是截取最终画面。`inspect_postvs.py` 导出了这四个 draw 的 post-VS 顶点和六个原始 index；`scripts/build_ui_postvs_manifest.py` 生成仓库证据 `docs/frame38112-ui-background-draws.json`，并复制到 Unity Manifest。Unity 的 `BuildCapturedUIBackground.Build()` 据此建立独立 `Frame38112_UIBackground_Draws.unity`：四个 MeshRenderer、四个材质、独立贴图和透明混合 shader。1920×1080 中间结果为 `Assets/Kiana/Validation/UIBackground-EID2237-2307.png`，能看到深色斜向字样和条纹；构建后自动回到用户原来的 G-buffer 场景。

这四个 draw 只覆盖背景的一部分。当前 shader 对 PS 5556 的 `texture × vertexColor` 与预乘 alpha 做了基础映射；其 `cb0` 分支、mask `t1`、精确混合状态和其余 UI draw 尚需逐项核对，最终 RT 背景亮度/位置也尚未做像素误差验收。后续先核对这四个 draw 的源输出，再补完整 UI 顺序，最后与角色 pass 合成。不要把 G-buffer 黑底或背景小场景称为 1:1 最终帧。

材质诊断补充：`CapturedAlbedo.shader` 的 `_DebugOutput=2` 可显示源 `t5` material mask；`scripts/analyze_material_mask.py` 按 mask 分段统计 EID 945 源/Unity RGB 误差。第一分段约 11.4 万像素、MAE 54.8，主要落在伞区域；直接乘 `cb3` 调色系数的 0.5 和 1.0 试验将总体 MAE 从 19.11 提高到 19.86/24.84，因此试验分支已撤销，原材质和 `_DebugOutput=0` 已恢复。该结果提示继续查 PS 的材质分支/阴影，而非直接统一压暗。

继续按 PS 31475 的指令 46–62、330–389 追踪后，确认 `t5.r` 选材质 band，`t6.g` 参与纹理数组叠加强度，数组层/着色/混合模式来自动态读取的 `cb3[band+5/10/15]`。`scripts/extract_material_tables.py` 从六个 draw 的完整 PS 常量缓冲生成 `docs/frame38112-material-tables.json`：EID 858/875、895、912/928、945 共 **四套不同材质表**，不能共用一组纹理数组层。EID 945 的层号为 100/0/1/2/3，其中 100 表示跳过；早期统一使用 1/13/4/14/15 是 EID 858 的表，套在 EID 945 上不成立。

`scripts/build_material_coverage.py` 将 26 个 draw 的绑定清单、各 PS 静态读槽和 Unity 当前颜色路径交叉生成 `docs/frame38112-material-coverage.json`，同一文件也已导入 Unity Manifest。审计结果是 **0/26 个 draw 达到源 shader 的完整读槽覆盖**；这是当前实施状态清单，并不意味着所有静态指令分支在该帧都实际执行。后续以它逐项确认真正执行的分支和四个 RT 的输出，再把状态改为完成。

Unity shader 中增加了 EID 945 的源指令候选分支供诊断，但只把它接到现有近似光照后仍使 EID 945 MAE 从 19.11 变成 **24.69**；误差主要在 band 2，表明完整的前段光照、数组采样坐标和该分支的位置仍需恢复。`_UseCapturedWeaponPalette` 已保持关闭，当前可见角色仍使用较优基线。候选分支不计入已完成材质；后续先复现 `t1` 光源/阴影与四个 G-buffer 输出，再按每套表启用并逐 EID 验收。

### 2026-09-26：结构化光照绑定与材质分支校验

通过 Kiana bridge 的 `PipeState.GetReadOnlyResources(Pixel)` 逐项核实 EID 858/875/895/912/928/945/992/1035：PS 槽 `t1` 实际绑定 **RID 24248 `EntityGpuDataBuffer`**，描述符 8192 B、每条 128 B。先前根据资源名称推测的 RID 19818 `GPULightDataForChar` 不是这些 draw 的 `t1`。EID 945 的 `cb0[196].x` 按整数为 1，`cb2[2].z=0`，所以 PS 31475 指令 94–102 读取第 0 条。该条偏移 0 为 `(1,1,1,50)`；源指令的 `wxyz` 重排得到半径 50 和白色 RGB；偏移 16 为光源位置 `(590.54559,17.58489,16.03023,1)`。原始绑定和各偏移浮点值已存入 `docs/frame38112-entity-light-binding.json`，同一 JSON 导入 Unity Manifest。

可复用的 `.agents/skills/rdc-unity-frame/scripts/inspect_pixel_structured_buffers.py` 会在独立 RDC 回放中逐事件导出 PS 非纹理只读缓冲的资源 ID、步长和首条原始字节；这轮绑定值已先通过正在运行的 Kiana bridge 确认。脚本已通过 Python 语法检查，后续独立回放时还需核对实际输出与 bridge 一致。

`CapturedAlbedo.shader` 增加可开关的 `_UseCapturedPointLight`，`CapturedLightingParameters.cs` 保存捕获位置与半径。用源位置方向和一个简化距离衰减替代现有固定方向，在 2880×1368 EID 945 对照中得到 MAE **20.13**，劣于原 **19.11**，因此材质开关保持 0。这说明已恢复 **输入数据**，并没有恢复源 PS 的完整非线性光照响应；不能将点光测试当成完成的全局光照。

进一步逐指令核对材质数组：EID 945 的 `cb3[band+15].z` 五个值全为 0，指令 350–353 的 `v0.xy × 5` UV 分支实际不执行。现将候选分支的数组坐标改成源指令 344–347 的法线投影 `dot(normal, cb0[119..121].xy) × 0.5 + 0.5`，并把候选材质叠加移到近似光照之前。但候选开启仍得到 MAE **24.48**，主要是 band 2 从 17.47 升到 52.39；已关掉 `_UseCapturedWeaponPalette`。源 `t2` 为 RID 5819 `CharacterOverlayTex`，PS 指令 68–70 确实在内部 `r1` 累加其采样，但把该加法直接接入当前简化颜色输出的单独诊断达到 MAE **50.55**，因此 `_UseCapturedOverlay` 也保持 0。源 PS 在这之后还有指令 163–329 的光照和 392 以后的非线性材质映射，必须按数据流接到正确寄存器与输出路径，再逐步开放这两支。

这轮测试没有改坏当前场景：Unity 编译支持新 shader，EID 945 的三个候选开关均为 0（点光、数组材质、overlay），黑色 G-buffer 天空盒仍在。证据图位于 `Assets/Kiana/Validation/StageRenders/EID945-pointlight.png`、`EID945-palette-sourceuv.png`、`EID945-overlay.png`；场景继续使用原来的 19.11 基线。下一步针对 PS 31475 的 `r1/r2` 颜色流和 `o0` 输出逐段复现，先在 EID 945 验收，再复制到共用该 PS 的其他 EID。

### 2026-09-26：眼部顶点查表与源混合状态

EID1273 的源 VS31487 从 IA `v3.x`（KMF 顶点色 R）取得压缩索引：乘 255，低/高 nibble 分别给 `Eye_E` RID23285 的 x 与 y；源 VS 采样后向 PS `v5` 传 `(2×RGB,A)`。`scripts/audit_eye_vertex_lookup.py` 对 `EID1273.bytes`、RDC `EID1273.vsout.bin` 和 16×16 `RID23285.png` 的 **426/426 个顶点**逐一核对，四通道平均和最大绝对误差均为 **0**；原始审计在 `docs/frame38112-eye-vertex-audit.json`。导出 PNG 的行向对应 `y=15-highNibble`；以未经翻转的行取样，平均误差为 0.7029。Unity shader 现于顶点阶段按该索引采样 `_Slot1`，贴图导入明确设为线性、Point、无 mip、未压缩；`ApplyCapturedMaterialFamilies.cs` 可重复施加这些设置。

`scripts/inspect_color_blends.py` 从 RDC 取到 EID1273 RT0 的 RGB 混合为 `One / InvSrcAlpha`，alpha 混合为 `InvDstAlpha / One`；RT2/RT3 也启用混合，但当前 Unity 单 RT 阶段只复现 RT0。RDC 该 draw 开启深度测试、关闭深度写入。`CapturedAlbedo.shader` 新增可按材质设置的独立 RGB/alpha 混合因子；Unity EID1273 材质设置上述 RT0 因子及 `_ZWrite=0`。EID945、992、1057、1078 的源 RT0 未启用混合。源枚举及每个 RT 的原始结果保存在 `docs/frame38112-color-blends.json`。

在同一场景与源 EID1273 RID53242 比较，先后两张 Unity 2880×1368 截图为 `EID1273-eye-blend-baseline.png` 和 `EID1273-eye-source-blend.png`。前景 IoU **0.982067→0.982152**，全前景交集 RGB MAE **21.403→21.366**。眼部 ROI `(888,873)-(1145,925)` 的有效重叠 **12212→12238** 像素，重叠处 MAE **16.109→11.510**。因此启用 EID1273 眼部路径并固化到材质应用器。该进步只证明眼部局部和 RT0 组合改善；其 face-lightmap 方程、RT2/RT3 混合及最终画面尚未等价。

### 2026-09-26：描边顶点控制流

PS31478/31479 的源 `v5.w` 并非通用顶点 alpha。VS 对 IA `v3.z`（KMF 顶点色 B 的 UNORM8 原始字节）做位运算：PS31478 的两个 draw 为 `0.9 - 0.2 × (byte & 3)`，PS31479 的八个 draw 为 `(byte >> 5) & 1`。`scripts/audit_outline_vertex_control.py` 将十个 KMF 网格与 RDC VSOut 对照，**67,540/67,540 顶点**的 `v5.w` 完全匹配；各 draw 的 PS `v1.xy` 与网格 UV0 最大误差也为 **0**。详情 `docs/frame38112-outline-vertex-audit.json`。KMF 浮点值乘 255 可能在整数边界略低，因此审计先恢复最近的 UNORM8 字节，避免 32 被误取成 31。

Unity 候选描边路径已用该顶点色位解码代替先前错误的 alpha 阈值，并用验证过的 `v1.xy` 采样 `t2/t3`。在 EID1057 的同场景诊断中，源 RID53242 对照的纯基线为 IoU **0.990128**、MAE **19.781**；开启这条候选为 IoU **0.990125**、MAE **21.537**。故材质应用器仍将描边候选关闭，保留新输入解码供继续实现源 HSV、光照及阴影方程。诊断图为 `EID1057-outline-baseline.png`、`EID1057-outline-candidate.png`，测试后现场材质已恢复候选关闭。

### 2026-09-26：脸部与眼部 lightmap 的 PS 输入坐标

源 PS31476/31480/31489 对 `t4` 面部浮点 lightmap 首次采样使用 **`v0.zy`**，后续另一次使用 `v0.xy`；此前 Unity 候选误把 `v0.zw` 整组当首次 UV。`scripts/export_face_psuv.py` 审计 EID992/1008/1236/1252/1273：每个 draw 的 PS `v0.xy` 与 KMF UV0 完全相同，但 KMF 第三 UV 块与源 `v0.zw` 最大差值约 **1.26–1.31**。已把真正的 PS `v0.zw` 写入五个 Unity Mesh 的 uv3，保留原 Mesh 资产和场景引用；`docs/frame38112-face-psuv-audit.json` 记录顶点数与误差，Unity EID992 第一个 uv3 顶点读回 `(0.546599,-0.355301)` 与 VSOut 一致。shader 脸部候选改在 `float2(uv3.x, uv0.y)` 读取首次 lightmap。眼部已启用路径的 EID1273 阶段像素保持一致。

按同一当前场景对 EID992 再做 A/B：关闭脸部候选 IoU **0.990034**、MAE **18.276**；开启候选 IoU 相同、MAE **19.734**。因此恢复关闭状态。输入坐标已经归位，误差留在源 PS 的后续面部明暗/高光、shadow 和输出组合方程。诊断图为 `EID992-faceuv-baseline.png` 与 `EID992-faceuv-candidate.png`。

### 2026-09-26：身体材质 overlay 的帧内选择条件

逐项读取九个身体类 draw（EID858/875/895/912/928/945/968/1035/1313）的像素 `cb3[106].x`，全部为 **0**。PS31475 的指令 67–73、PS42681 的 58–64 与 PS33678 的 67–73 都采样 `t2` 并计算 `albedo + overlay - 0.5`，随后以 `cb3[106].x > 0.5` 的结果 `movc` 选择颜色；本帧全部选择原本的 `t3` albedo 路径。也就是说 `CharacterOverlayTex` 在这些 draw 中**有绑定、有采样，但其结果没有进入颜色输出**。Unity 的 `_CapturedOverlaySelect` 已按此固定为 0，`docs/frame38112-material-coverage.json` 单列 `sourceSampledButColorDiscardedSlots:[2]`。这说明“所有贴图都要检查”需要记录实际数据流，不能强迫每张绑定贴图都改变这一帧的像素。其他贴图槽是否同样被帧内分支丢弃，仍需逐 shader 审计。

### 2026-09-26：末段纯顶点色与无颜色 draw

补导出源 RID53242 的 EID1202/1287/1313 快照，并用 `scripts/compare_stage_deltas.py` 算逐段差分：EID1161→1202 改动 **8,246** 像素；EID1273→1287 的颜色 RT 改动 **0**；EID1287→1313 改动 **1,019** 像素。PS24167（EID1202）只有两条指令：`o0.rgb=v1.x`、`o0.a=1`，源 VS 把 IA `v2.x` 原样送往 `v1.x`；1,349 个 VSOut 值与 KMF 顶点色 R 全部一致。Unity 中的常量家族候选因此具有正确的颜色输入，但 EID1202 的 VS 位移/覆盖尚未对齐。单独开启候选，整图 IoU 从 **0.982393 降到 0.909311**，说明目前不能把该 draw 加入可见场景；测试后对象和材质开关均恢复原状。对照 `EID1202-constant-off.png` 与 `EID1202-constant-on.png`。PS31482（EID1287）对 RT0 确认为本帧无颜色增量，仍需核对深度/其余目标，不能把它视为整个 pass 无作用。

**下一验收点。** 先逐指令恢复身体 PS31475/42681/33678 的实际光照和材质数组结果，并分开对照四个 G-buffer RT；再完成脸部 PS31476/31480 的 lightmap、阴影和高光方程，以及描边 PS31478/31479 的 HSV/光照路径。每一族用源前后 EID 快照及同状态 Unity A/B 才开启。随后补 EID1202 的 VS 位移、其余晚期 draw 和背景/UI 合成。当前所有 26 个材质**仍未达到 1:1 完整 shader 输出**，但输入、状态和失败实验已保存，重启 Unity 后可复现。

### 2026-09-26：按美术效果拆解材质，而不是追逐零像素误差

用户明确了验收方向：Unity 场景的卡通材质、受光与最终合成要在观感上基本还原。逐像素指标用于定位范围、验证改动，不能代替材质判断。参照图是 **frame 38112 的 RDC EID945 G-buffer RT0**；`docs/frame38112-stage945-art-comparison.png` 左侧为源，中间为原 Unity 阶段，右侧为第一次试验。原 Unity 主要缺金属亮边、深色布料层次和头发受光，整体统一压暗肤色会恶化观感。按身体 PS31475 与面部 PS31476 的指令及绑定整理的 `docs/frame38112-shading-feature-map.json` 分别追踪 basecolor、normal、材质分区、AO/遮蔽、明暗、投影阴影、高光、边缘光、面部阈值、描边、混合与四 RT 合成；每项都区分了捕获证据、Unity 现状和下一道验收。G-buffer 是多目标结果；这些特征的证据也包括绑定纹理、PS/VS 指令、常量与深度模板状态，不能推断每项都独占一个 G-buffer 通道。

`CapturedAlbedo.shader` 现在有可调的卡通材质候选：明暗阈值与柔边、独立的辅助遮蔽、材质 mask 控制的高光、视角边缘光。第一次直接把 `t6.b` 当 AO 乘上全部颜色使 EID945 皮肤整片变灰，阶段 MAE 19.11→26.11，故**不能把该通道确认为 AO，也不能这样全身套用**。关掉这项，并分别测试材质高光、边缘光和明暗。该材质的高光与边缘光候选尚未改善对应源画面，因此仍关闭。只启用 0.5 强度的温和明暗分层后，EID945 前景 IoU 0.989259→0.989302、交集 RGB MAE **19.1119→18.7508**；肤色未再统一变灰。`ApplyCapturedMaterialFamilies.cs` 已将这组参数固定在 EID945（`_UseArtToon=1`、`_ArtShadeStrength=0.5`、AO/spec/rim=0），Unity 重建后可重复施加。已从保存材质再次捕获 `EID945-art-saved.png`，数值与临时候选一致。其余八个身体 draw 未直接套用该组值。

源 PS31475 的 `t5/t6`（指令 46–50）不是一张通用 AO 贴图：`t5.r` 选择分层，`t5` 的其他分量进入高光控制，`t6.b` 进入后续阴影衰减分支；t8 是比较采样的投影阴影，t7 是 16 层材质阵列。局部金属饰件可能属于早于 EID945 的 draw，因此下一步先用逐 draw 差分定位金属、布料、头发、肤色各自的 EID/材质分区，再给高光、边缘光、暗部单独设定响应。面部 PS31476 的 `t3.a`、`t4` 与指令 98–110 的阈值表达式有 SDF 式面部遮蔽的线索，但其语义和坐标仍待逐像素寄存器追踪，不把当前简单 face-light 候选称为完成的 SDF。

### 2026-09-26：按 draw 批量推进 G-buffer 材质

用户指出腹部、头发月牙亮带及 matcap 缺失。用相邻源 RT53242 快照确认 EID858 为手杖、875 为伞、895 为后发、912 为胸前饰件、945 为身体/皮肤；对应源变化掩码记录在 `frame38112-early-draw-color-deltas.json`。这避免将金属高光误调到 EID945 皮肤。所有 A/B 都从当前同一 Unity 场景状态捕获，并只比较该 draw 的源变化区域。

| EID / 区域 | 当前试验 | 源变化区 RGB MAE，关→开 | 决策 |
| --- | --- | ---: | --- |
| 875 / 伞 | 卡通明暗强度 1 | 21.9313→18.5218 | 保留 |
| 895 / 后发 | 卡通明暗强度 1 | 22.2868→16.7492 | 保留；月牙亮带仍未复现 |
| 912 / 饰件 | 仅高 G 材质区域的高光强度 1 | 25.9154→24.5257 | 保留；通用 rim 无效 |
| 875 / 伞 | t7 材质数组分层，修正为光照后混合 | 18.5039→17.9937 | 保留 |
| 895 / 后发 | 同一 t7 候选 | 16.7488→16.7509 | 关闭 |
| 912 / 饰件 | 同一 t7 候选 | 24.4837→79.0298 | 关闭，公式/区域仍未对齐 |
| 945 / 身体 | 同一 t7 候选 | 11.1832→27.1442 | 关闭，不能全身套用 |

源 PS31475 的 t3/t4/t5/t6 使用 `sample_b(..., cb0[199].x)`，本帧 `cb0[199].x=-2`。Unity 的 RID42974 之前把源 BC7_SRGB 解码 PNG 再压为 DXT5。已把该身体贴图保持 sRGB、mip 开启、**无二次纹理压缩**（RGBA32），并在 EID858/875/912/945 对 t3 应用源 mip 偏移；EID895 的 A/B 略退步，暂不启用。RID42974 原图本身含有红色弯钩状肚脐纹样，因此不能仅凭该标记判定 UV 错；腹部受光的硬暗部仍与源不同。t4/t5/t6 偏移候选同场 A/B 几乎无差别，保持关闭。

共享身体 PS 的 t7 路径还发现运算顺序错误：源指令 330–389 在基础光照后的 `r1.xyz` 混合材质层，Unity 旧版在光照前处理；源 mode 0 是替换插值、mode 1 是相加、mode 2 是 overlay。shader 已按顺序与模式改正，但 **这仍是部分移植**，不能把 t7 已绑定或 EID875 的局部改善称作完整 matcap。源高光指令 435–528、投影比较采样 136–160、头发月牙亮带、面部 SDF、描边深度/模板及 RT1/RT2/RT3 均待实现。当前 Unity Game 捕获只对照 RT0；还不能声称 G-buffer 完成。

将伞、后发、饰件和身体这四个有效设置一起保存后，EID945 全图前景交集 RGB MAE 从上一次 18.7508 降至 16.3139；再启用伞的 t7 分层后降至 **16.0963**，IoU 约 **0.98930**。源 RT0 与 Unity 同为 2880×1368。保存的图是 `F:/KianaFrame38112Unity/Assets/Kiana/Validation/StageRenders/EID945-batched-family-matcap.png`。这是阶段进展，不是质量验收完成。下一大步按源 PS 分段移植高光与阴影，并给四个 G-buffer 输出分别建立验收图。

原始 BC7 DDS 与 RenderDoc PNG 的颜色编码不同。RID42842 的 DDS 解码 RGB 与 PNG 平均相差 42.21/255；把 DDS RGB 做约 2.2 次幂后只差 1.27/255。直接将五张源 DDS 绑定到 Unity 材质使 EID875/895/912/945 的局部误差大幅增大，因此没有保存这种绑定。`scripts/export_texture_dds.py` 和 `docs/frame38112-albedo-dds-config.json` 保留原始 DDS 与 mip 链作为证据；`scripts/export_texture_mips.py`、`assets/ImportCapturedMipChain.cs` 另外导出并导入 RID42842 的逐级颜色管理 PNG mip，Unity 得到 RGBA32、12 mip 的诊断资源。后发 EID895 使用该资源时误差由 16.7488 略升至 16.7815，也未绑定到已保存材质。这一实验说明不能把未经颜色空间核对的原始压缩纹理直接替换当前 PNG 贴图；后续材质工作先攻克源 PS 的高光、rim 与描边分支。

### 2026-09-27：直接追踪 RDC 的前发亮带

本轮直接用 `kiana_qrenderdoc.exe --python=inspect_pixel_trace.py` 打开目标 `capture_frame38112.rdc`，在 **EID1035 / PS33678** 跟踪了前发亮带 `(945,1042)`、`(948,1050)`，前发暗部 `(881,1066)` 等像素。完整配置与逐指令寄存器分别保存在 `docs/frame38112-front-hair-trace-config.json`、`docs/frame38112-front-hair-trace.json`，不是从截图推断。源 `t3` albedo 的亮带采样值分别为 `(0.660,0.688,0.887)`、`(0.789,0.797,0.853)`；最终 RT0 为 `(0.662,0.717,0.954)`、`(0.804,0.842,0.902)`。所以亮带的**形状已在 t3 贴图中**，源 PS 又对颜色做了局部增强。两像素在指令 597 后的边缘项均为 0，不能把这里的月牙误认成通用 rim。

关键通道是 PS33678 指令 46 的 `t5.zxwy` 资源重排：寄存器 `r3.x` 取自 **t5.b**。上述亮带的值为 `0.577`、`0.961`；暗部 `(881,1066)` 的 t5.b 虽也为 `0.957`，但 t4 法线纹理 G 分量是 `0.442`，亮带则约 `0.663–0.668`，且暗部源 RT0 约 `(0.328,0.303,0.587)`。单独按 t5.b 提亮会毁掉阴影，因此候选同时要求 t5.b 和 t4.g 命中。此前误把寄存器 `r3.x` 当 t5.r，A/B 使 EID1035 draw ROI MAE `22.734→38.534`，已撤销。仅 t5.b 的候选为 `22.734→22.857`，也未启用。加入 t4.g 后为 **`22.734→22.711`**；亮带 `(945,1042)` 的 Unity RGB 从 `(145,153,195)` 到 `(167,183,237)`，源为 `(169,183,243)`；暗部 `(881,1066)` 保持 `(131,135,177)`。这个有限改进已保存到 EID1035 材质和应用器，阶段图 `EID1035-hair-blue-normal-candidate.png`。它仍是局部材质近似，不等同完整 PS33678。

同状态测试 EID1035 的 t3 mip bias `-2` 只改变 1,021 像素，draw 误差基本不变；完全关闭现有 art light 则将 draw ROI MAE `22.734→31.211`，因此两者均未保存。对 **EID895 / PS31475** 启用先前的通用 hair rim 候选使 draw ROI MAE `16.861→20.949`，而 `(1420,457)` 等已追踪的源亮带像素在 Unity 候选中甚至没有变化；该候选继续保持关闭。后发需要按 PS31475 的输入法线、材质 band、源光照和深度/颜色组合重新定位，不能从 EID1035 复制规则。

描边诊断另有进展但暂不影响当前可见场景：RenderDoc `EID1057/1161` 后 VS clip 已导出并存入 Mesh UV5；Unity 捕获相机分支修正 Y 符号后，EID1057 源改变的 692 个像素全部落在 Unity 候选覆盖内，但 Unity 同时改动了 **133,994** 个像素，说明颜色计算前的深度、模板和扩张 VS 仍未对齐，不能开启。源逐 draw 模板配置在 `docs/frame38112-gbuffer5-stencil.json`，对应 Unity ShaderLab 参数和编辑器应用器已备好。保留这条诊断路线，同时把主线转向材质区域和美术效果。

### 2026-09-26：全身姿态与 Scene 视角复核

用户指出并非只有伞，而是整个身体姿态都与参考不符。先检查了**实际运行中的 Unity 网格**，没有只重新计算源 manifest：`assets/AuditCapturedPose.cs` 对场景内 26 个 MeshFilter 的每个顶点，用 `Transform.localToWorldMatrix` 与 RDC `cb1[0..3]` 重建矩阵分别求世界坐标；最大差 **0.00006104 世界单位**，逐 draw 记录在 `docs/frame38112-unity-pose-audit.json`。26 个源矩阵的三轴均为单位长度、正交且行列式约 1；原场景的矩阵分解没有丢失缩放或镜像。此前 `validate_gbuffer_vertices.py` 又将基础 EID858–1035 的**全部顶点**投到源后 VS clip，最大差 **0.0001842**；包括伞 EID875、身体 EID945、脸 EID992。此结论仅针对 RDC frame 38112 的已捕获静态姿态，尚未恢复骨骼与动画。

源 RT0 导出的图像上下颠倒。`AuditCapturedPose.CaptureUpright()` 用同一个 Unity 捕获 VP 旋转 clip X/Y，单独保存 `docs/frame38112-unity-pose-upright.png`，不修改网格、Scene 或源相机。与源 `docs/frame38112-gbuffer-upright.png` 对比：前景交并比 **0.986129**，源前景覆盖 **0.99809**；手、伞、头、肩及躯干轮廓在同一摄像机下对应。用户截图中的可编辑 Scene 视图相机约 `(21.66°,212.63°,0.28°)`，而捕获相机约 `(38.27°,199.90°,201.94°)` 且使用自定义 VP，不能把自由视角截图和 RDC 输出直接当作同一姿态比较。已恢复用户原 Scene 观察视角；没有为了截图观感随意旋转身体或伞。若要以不同于本帧 G-buffer 的 UI 立绘姿态作为 3D 目标，须将该目标单独标明并重新建立姿态源证据。

### 2026-09-26：描边厚度按 RDC 顶点位移标定

原始后 VS clip 直接接入 Unity 后，EID1143 源只改 14,639 像素，候选却改 549,156 像素；模板限制后仍有约 535,100 个区域外像素变化，因此此路径没有启用。另做了真正的 3D 倒壳 `assets/ToonInvertedHull.shader` 与 `ApplyInvertedHull.cs`，8 个源有色差的描边 draw 已保存到场景，EID1130/1161 在源 RT0 零色差，保持关闭。第一次统一世界宽度 .003 的诊断改变 27,967 像素、与源变化重合 8,092 像素，画面看起来偏厚。此后不再任意按比例缩放：从相同顶点的源 base/outline 后 VS 屏幕坐标测得中位宽度，按 2880×1368 参考分辨率逐 draw 写入 `_ReferenceWidthPx`：EID1057 0.235、1078 1.951、1091 1.933、1107 2.051、1118 2.119、1143 2.043、1183/1331 1.825 px。Unity shader 和材质已更新保存；这些是源位移的**中位数**，并非逐顶点源扩张方程，最终描边颜色/深度/覆盖仍待进一步对齐。

### 2026-09-27：描边、皮肤法线基底与后发月牙的同相机核验

用户指出整体材质差距仍大，且当前 Game 与 Scene 曾因描边测试不同步。查明旧 `ToonInvertedHull.shader` 在 RDC 捕获相机下没有匹配的深度翻转：EID1057 的源 RT0 有 692 个变化像素，Unity 旧倒壳为 **0**。直接翻转深度但沿用旧 `_Cull=1` 会将大片角色涂黑；这次失败已撤销。另建 `ToonInvertedHullDual.shader`，按捕获相机 `_RdcDepthFlip` 用 VFACE 选壳面，并仅在该相机翻转深度。当前 8 个可见描边 draw 已以 **1.0 参考像素**保存到场景，2 个源 RT0 零变化 draw 仍禁用；`ApplyInvertedHull.cs` 可重放。阶段 `EID1057` 源 692、Unity 585、重合 460 像素；其余 EID1078/1091/1107/1118/1143/1183 的源变化掩码召回率依次约 56.5%/60.0%/59.0%/51.9%/52.7%/61.1%。EID1331 的源 313 像素目前 Unity 为 0，待独立修正。`EID1331-dual-all-1px.png` 与源同相机全图 RGB MAE 为 6.827，旧恢复版为 7.079。**这仍是深色倒壳近似，源 PS31478/31479 的逐材质彩色线、逐顶点宽度与模板状态未完整还原。**

更关键的皮肤分层问题来自法线基底。`docs/frame38112-skin-layer-trace.json` 在 EID945 / PS31475 追踪肩部暗部 `(1123,358)`、邻近亮部 `(1120,330)`、`(1100,380)`；源 t3 与导入 PNG 一致，源 `v2` 法线、`v3` 切线与 Unity 调试输出也一致，但源 `v4` 副切线与 Unity 计算值**逐点反号**。例如暗部源 v4 `(0.365,0.919,0.134)`，Unity 原值 `(-0.365,-0.922,-0.137)`。`CapturedAlbedo.shader` 的副切线叉积现取反；改后调试法线 RT 对三点的源编码分别为 `(0.363,0.240,0.904)`、`(0.284,0.500,0.951)`、`(0.416,0.681,0.958)`，Unity 对应 `(0.357,0.243,0.906)`、`(0.286,0.498,0.953)`、`(0.412,0.678,0.957)`。暗部源 RGB `(137,102,106)`，Unity 由 `(184,153,143)` 变为 `(128,106,106)`。EID945 全图前景交集 RGB MAE `16.039→15.696`；EID1331 在 1px 描边条件下 `17.595→17.343`。这是有法线 RT 证据的基底修正，仍不代表皮肤完整 SDF/投影阴影实现。

`docs/frame38112-back-hair-trace.json` 追踪 EID895 / PS31475 的后发外侧亮带 `(1411,428)` 等点。亮点的 t5.b≈0.232、t3≈`(0.625,0.609,0.855)`、最终 RT0≈`(0.661,0.667,0.983)`；旁边暗带 `(1400,470)` 的 t5.b=0。这与 EID1035 的规则不同。EID895 专用 `_UseSourceBackHairCrescent` 仅按 t5.b 的这段分区补入已采样 t3 颜色；亮点 Unity RGB 从 `(154,150,212)` 到 `(167,169,250)`，源为 `(169,170,251)`。EID895 源 draw 变化区 MAE `16.509→16.486`，只改 1,674 像素；开关已保存到材质和应用器。旧通用 rim 仍关闭。当前整体 EID1331 图为 `F:/KianaFrame38112Unity/Assets/Kiana/Validation/StageRenders/EID1331-current-20260927.png`，源同相机全图 MAE 6.726、源前景交集 MAE 17.336。脸/发交界黑影、金属/粗糙/自发光、面部 SDF、完整 G-buffer 四 RT 和后续合成仍是明显缺口，不能将上述局部改善称为材质对齐完成。

### 2026-09-27：眼部发片暗影的 draw 顺序、模板与透明混合

逐阶段源 RT0 与 Unity 截图确认眼旁黑影并非单纯的脸部调色。源在 EID992 的 `(1150,920)` 为 `(133,87,116)`；**EID1008** 将其写为 `(25,2,2)`；EID1035 在该点被模板排除，颜色不变；EID1313 透明叠加后为 `(81,71,71)`。此前将 EID1035 说成暗底来源是错误归因，现已纠正。证据为 `docs/frame38112-eye-hair-blend.json`、`docs/frame38112-gbuffer5-stencil.json`、`docs/frame38112-face-hair-shadow-trace.json`、相邻源 RT0 图。EID1035 的 RT0 **关闭混合**，EID1313 的 RT0 为 `SrcAlpha / InvSrcAlpha`。PS33678 指令 49、53、79–91 表明 EID1313 的 alpha 由相机方向和 t6 遮罩形成：三个眼旁追踪点的输出 alpha 约 `.349/.368/.348`。源 t6 的视图/资源 swizzle 不能只按 HLSL `wxyz` 字面映射到 PNG 的 A；眼旁 UV `.4135,.7860` 的追踪值 `.2218` 与导出 RID42851 的 **R=56/255** 对应，而 PNG A=255。

Unity 原场景中 EID1313 GameObject 原本被禁用，所以先前调它的混合、深度都不会改变画面。测试了原正反面模板、交换正反面和双面眼部模板：前两者分别让亮发片盖住眼睛或错误遮掉眼白；双面版本让 EID1008 的标记留在眼部，EID1035 用 `NotEqual` 避开，EID1313 用 `Equal` 叠加。`DiagnoseEyeStencil.cs` 在 `try/finally` 中临时修改材料和激活状态，各试验图保存在 `StageRenders/EID*-eye-stencil-*.png`。EID1313 单纯激活并保持不透明会退步；加入源 PS alpha 形式、RID42851 红通道及正确 RT0 混合后，脸部窗口 `[1020:1260,850:1000]` 平均 RGB MAE 从 **16.459 降到 15.157**，全图从 **6.726 降到 6.712**。已保存 `ApplyEyeHairLayer.cs` 对四个相关 draw 的模板和 EID1313 激活/混合状态；重建场景时 `BuildGBuffer5World.cs` 也会调用它。当前同相机图为 `F:/KianaFrame38112Unity/Assets/Kiana/Validation/StageRenders/EID1331-through.png`。

该修复仍非像素对齐：源 `(1150,920)/(1150,900)` 分别 `(81,71,71)/(85,71,70)`，Unity 现为 `(118,107,121)/(98,77,78)`；`(1170,920)` 的眼底亮度也有差。PS 方向项使用源 `cb0[55]` 与 `cb2[6]`，但 Unity EID1313 网格现场位置和源 fragment 的 `v2.w/v3.w/v4.w` 尚未逐点对应；需先查其 VS 输出/几何输入，再校准 alpha 和眼部材质，不能给脸整体加黑。测试将 t6 换成 PNG A 后 alpha 退化为 1、脸部误差回到 16.737，已撤销；把 EID1313 深度改 Always 并未改善，也未保存。当前只是 RT0、单一视角的阶段结果，RT1/2/3、描边彩色层、面部 SDF、完整皮肤双层明暗和高光仍需继续。

追加核验：`_DebugOutput=7` 直接显示 Unity EID1313 的 alpha，`(1150,920)` 为 **89/255≈0.349**，与 RDC PS 追踪 `0.348937` 几乎相同。因此剩余偏亮不是 alpha 公式本身；EID1035 和 EID1313 的现场网格、变换也相同，先前只看局部 bounds 推断二者位置不同并不成立。进一步发现 EID1313 原材质 `_Cull=0` 双面渲染，源为 CullBack。只在此 draw 测试 Unity `_Cull=1/2`：`_Cull=1` 的全图 MAE **6.708**、脸部窗口 **14.935**，`_Cull=2` 分别 **6.709/15.039**，双面基线 **6.712/15.157**。`_Cull=1` 使首个暗影点从 `(118,107,121)` 到 `(94,77,75)`，更接近源 `(81,71,71)`；已保存并写入 `ApplyEyeHairLayer.cs`，最终同相机 `EID1331-through.png` 与 A/B 候选哈希相同。说明源 D3D CullBack 在本捕获相机/网格绕序下对应 Unity CullFront，不能照抄枚举值。仍有眼底区域、PS 输出颜色和全身材质误差；上述量化只覆盖 RT0。

### 2026-09-27：以材质面积排序，伞面明暗分界 A/B

在当前保存场景一次捕获 EID858/875/895/912/928/945/968/992/1008/1035/1313/1331，使用各源相邻 RT0 快照差分作 draw 掩码。最大面积缺口为 EID875 伞（629,448 像素、RGB MAE 18.072）、EID945 身体（532,338、10.51）、EID895 后发（494,035、16.48）；EID1035 前发（154,139、22.72）与 EID912 饰件（118,800、24.10）也明显。EID968 虽有 MAE 104.21，源 RT0 只改 1,975 像素。此排序明确区分高误差小细节与大面积材质问题，避免被黑背景稀释后的全图 MAE 误导。

伞面源 `(240,528)` RGB `(41,45,83)`，Unity 初始 `(120,118,164)`；这块暗区不随现有 `_ArtShadowColor` 的 0.7→0.4 候选改变，说明它未进入当前近似的暗分支。全局乘 t6.b 的 `_ArtAO=0.5/1` 虽使该点降低，却把伞 draw 总 MAE 从 **18.072** 推高到 **35.183/78.291**，已撤销，不能把 AO 贴图直接当整伞阴影。只扫现有 toon terminator `_ArtShadowThreshold` 的 0.3/0.6/0.9 时，源变化区 MAE 为 **15.668/12.665/15.919**；组合 0.6 与更暗 shadow color 0.55 反而为 13.838，0.9 与 0.4 为 32.503。保留 **0.6**，其完整 EID1331 RT0 全图 MAE 从 **6.708→6.069**，源前景从 **17.324→15.651**。设置已保存到 EID875 材质和 `ApplyCapturedMaterialFamilies.cs`，重新捕获的 `EID1331-through.png`、`EID875-through.png` 均与 A/B 候选哈希相同。`ProbeMaterialScalar.cs` 使单值/颜色/成对参数诊断在 `try/finally` 中恢复，避免试验值污染场景。

该 0.6 是根据同相机源 RT0 **拟合的艺术分界**，不是已经反编译完成的 PS31475 阴影方程。伞左侧成片暗块仍偏亮，后发和身体材质差异也大。下一步沿源 PS31475 的 t6、法线、投影比较及 t7 材质层数据流定位该暗块，分别看明暗与高光，不再直接给全物体 AO 倍率。

### 2026-09-27：伞面 t5 分区与 t7 matcap 的源值校准

继续直接读 `capture_frame38112.rdc` 的 **EID875 / PS31475**，逐指令追踪 `(240,528)` 深紫区、`(240,624)`、`(500,624)` 和 `(700,400)`。配置与原始寄存器保存在 `docs/frame38112-umbrella-shadow-trace-config.json`、`docs/frame38112-umbrella-shadow-trace.json`；`scripts/summarize_pixel_trace.py` 可按指令范围摘录，避免再打开整份大 JSON。四点的 t8 投影比较均为 1，指令 161 的阴影因子亦为 1，所以伞左深色**不是此帧 t8 投影阴影造成的**。深色点源 t5 `zxwy` 重排后的红通道 `r3.y=.4714`，指令 58–62 选 band 2、t7 **slice 4**；t7 UV 约 `(.857,.515)`，采样 RGB `(0.198,0.198,0.198)`，alpha 1。相邻 `(240,624)` 的红通道 `.7021` 则选 band 1、slice 13。

同一 Unity 捕获像素的 t4 法线贴图约 `(134,139,123)/255`，与源 t4 `(0.529,0.545,0.498)` 相合；最终 mapped normal `(65,212,199)/255` 也与源 `(-.487,.665,.566)` 的编码吻合。因此**不解码 t4**。但 Unity 导入的 t5 RGB 在深点为 `(183,162,143)/255`，源对应 `(0.471,0.363,0.275)`；t6 的 `.722/.349` 对应源 `.479/.099`；t7 slice 4 在该点为约 `.482`，源为 `.198`。这些值逐通道符合线性转 sRGB，不能用同一解码开关覆盖 t4/t5/t6/t7。Unity 项目为 Gamma 色彩空间，仍需逐贴图验证实际进口及采样，而不是仅凭项目设置推断。

`CapturedAlbedo.shader` 将 t4/t5/t6 和 t7 的可选解码分开，并把 t7 的源 blend mask 路径改为可用 t6.b 的 `min(5.1*x,1)` 低值扩张。逐候选在 **629,460 个源 EID875 改变像素**比较：原保存状态 MAE **12.665**；仅解码 t7 为 **10.629**；解码 t5+t7 为 **9.923**；同时解码 t5/t6/t7 为 **10.855**；三张辅助贴图 t4/t5/t6 全解码则约 **30.666**。因此只保存 EID875 的 `_DecodeCapturedAux=1`（t5）、`_DecodePaletteSRGB=1`（t7），t4/t6 保持 0。源深点 RGB `(41,45,83)`，Unity 从 `(120,118,164)` 到 `(50,50,114)`；另一点 `(240,624)` 保持 `(78,51,103)`，源 `(73,49,102)`。整张 EID1331 RT0 全图 MAE **6.069→5.688**、源前景 **15.651→14.646**。已写入 EID875 材质和 `ApplyCapturedMaterialFamilies.cs`，Unity 当前图 `StageRenders/EID1331-through.png`。所有诊断材质在 `try/finally` 中恢复；阶段标准图在候选后重新捕获。

这还不是完整的伞或身体 PS。尤其 t6 原寄存器 `.099` 与 Unity 贴图 `.349` 的偏差已证实，但按现有近似光照/混合链解码反而扩大整片误差；应追指令 334–388 的所有条件和指令 619–663 的最终受光、反射计算，再启用 t6。后发 EID895、身体 EID945、脸、描边、四 RT 输出也仍待逐材质核对。不要把本次 t5/t7 的改善泛化为所有纹理都应做 sRGB 解码。

追加原 PS 后段核验：指令 **431–432** 把 `r0.x=t5.g × cb3[106].w` 转为 `0.96×(1−r0.x)`，乘到 matcap 后颜色；指令 **529–545** 再叠加方向光与 `cb0[2]` 环境项。EID875 深点 t5.g=`.363`，漫反射权重约 `.612`；亮点 t5.g=0，权重 `.96`。源深点 matcap 后 `r1≈(.273,.279,.475)`，最终 `o0≈(.160,.178,.326)`；亮点从 `(.329,.213,.412)` 到 `(.286,.193,.400)`。Unity 新增伞专用 `_UseSourceLateDiffuse`，使用捕获的环境常量和四个追踪点约 `.928/.978/.990` 的方向光 RGB。EID875 源变化区 MAE **9.923→8.392**；深点 Unity `(50,50,114)→(31,34,80)`，源 `(41,45,83)`；亮点 `(78,51,103)→(73,51,108)`，源 `(73,49,102)`。方向光 RGB 当前是局部样本近似，尚未移植该 PS 的完整逐像素 r11 数据流。设置已保存到材质与应用器，保存后 EID875 截图和候选哈希相同。完整 EID1331 RT0 全图 MAE **5.688→5.488**、源前景 **14.646→14.124**。

同一 t5/t7 校正与 t6 候选在其他 draw 单独测试，并未硬套：EID945 身体原 MAE **10.514**，启用原 t7 为 26.424、解码 t5+t7 为 12.237、再解码 t6 为 10.625，均较原值差；EID912 饰件原 24.030，解码 t5+t7 为 39.252，t6 一并解码为 40.403；EID895 后发原 16.471，解码 t5+t7 为 16.469，差值低于值得保存的幅度，t6 一并解码为 16.472。三者开关全部复原，候选阶段图保存在 `StageRenders/EID<id>-through-EID<id>-activation-*.png`。这些结果证明源 PS 虽共享，贴图、band table 与现有 Unity 近似光照不同，仍需按区域完成源路径；伞面只是其中一块已明显改进的材质。
## 2026-09-27：EID968 胸前青色宝石的 PS42681 路径

用户指出当前材质与目标 G-buffer 差距仍大。对照完整 EID1331 RT0，Unity 胸前宝石是灰色，RDC 为亮青色。这个区域由 EID968 / PS42681 生成，EID945→968 的源 RT0 仅改变 1,975 像素。源像素 `(930,580)` 为 `(0,223,255)`，旧 Unity `(126,127,126)`。先修这个醒目的材质分支，再回到更大面积的头发、皮肤和伞面。

- 使用 `docs/frame38112-gem-trace-config.json` 和 `scripts/inspect_pixel_trace.py` 追踪源 `(930,580)`、`(940,600)`、`(950,605)`，原始数据 `docs/frame38112-gem-trace.json`。PS 反汇编：`analysis-frame38112/gbuffer5-shaders-all/EID968-fragment.txt`。
- PS42681 指令 319–324 由 t5 选择 band 0；t7 **slice 12** 是宝石的图案。band 0 tint `(0,.491041,1)`、weight `3.59`、UV scale `(10.32,9.08)`、offset `(1,0)`。指令 343–370 使用法线/切线/副切线、视角以及 t6.x 对 t7 UV 做切线方向偏移。指令 336、363–365 的平方因子是 **dot(view,normal)**，并非 t3 alpha。指令 338–341 的 `pow(dot(view,normal),5.33)` 调制图案。指令 418–420 乘以 `0.96*(1-t5.g)`，531/543 又乘方向光并叠加 cb0[2] 环境项。
- Unity 导入贴图的 V 与源 `v0` 反向；仅 t7 坐标构造处反转 V。t4 法线保持原采样；t5、t6、t7 各自解码后才与源值对应。三处 t7 UV：源 `.621,.172` / `.404,.485` / `.432,.579`；Unity `.620,.173` / `.404,.486` / `.431,.580`。源 t7 RGB 三处约 `.291,.284,.275` / `.417,.421,.399` / `.085,.085,.077`。
- 光照的 PS315–317 `r10` 在三处追踪为暗带 `(.731,.711,.739)`、亮带 `(.967,.984,.965)`，当前 Unity 用法线方向阈值在两端插值。它是这处材质经过源像素验证的局部近似，完整 PS 光照仍待移植。
- 同状态对比：EID968 变化区 1,975 像素的 RGB MAE，基线 **104.209**，首次未反 V 的候选 **65.862**，反 V 并修正视角平方/分槽解码 **46.773**，加入源后段光照 **31.844**，补 t5 解码后 **26.171**。像素 `(930,580)` 源 `(0,223,255)`、保存版 Unity `(0,222,255)`；`(940,600)` 都为 `(0,255,255)`；`(950,605)` 源 `(0,79,146)`、Unity `(0,77,149)`。全 EID1331 RT0 更新后全图 RGB MAE **5.448**、前景交集 **13.978**，源前景 IoU **0.9840**。
- 实现：`CapturedAlbedo.shader` 的 `_UseSourceGem` 分支，仅 EID968 开启；`ApplyCapturedMaterialFamilies.cs` 固化四个 EID968 属性，Unity 材质已保存。候选截图 `F:/KianaFrame38112Unity/Assets/Kiana/Validation/StageRenders/EID968-through-gem-source-v5.png`；最终同相机图 `EID1331-through.png`。
- 捕获陷阱：`CaptureGBuffer5Stages.Capture(968)` 每次覆盖同名 `EID968-through.png`。A/B 时必须立刻复制为不同文件，再用新增 `scripts/compare_draw_delta.py` 比较相邻源 RT0 改变的像素。此前将候选与被覆盖的“基线”比得出逐字节相同，是验证脚本使用错误，已更正。

完整图直接对照仍显示后发、前发月牙亮带、伞面暗区、脸发暗影、皮肤分层、描边和金属饰件差距明显。不能将 EID968 的局部改进或全图黑背景稀释的 5.448 视为整帧材质完成。下一步按大面积 ROI 移植 PS31475/PS33678 的高光和后段光照，逐个 draw 留存候选与局部指标。

### 2026-09-27：EID1035 前发弧形高光的真正来源与 Unity 分支

用户指出前发高光应是一条连续弧线，旧 `_UseSourceHairMaskHighlight` 只让零散像素回到 t3 底色。按相同像素坐标裁出 RDC `EID1035-RID53242.png` 与 Unity `EID1035-late-baseline.png`，证据图 `docs/front-arc-source.png`、`docs/front-arc-unity.png`；源浅色发束上清楚有弧线，而旧 Unity 缺线。再次从原始 RDC 追踪 EID1035 / PS33678 的 `(978,1050)` 与旁边 `(978,1042)`、`(1085,1064)` 与 `(1085,1056)`，以及彩发、暗发点；配置 `docs/frame38112-hair-arc-trace-config.json`，完整寄存器 `docs/frame38112-hair-arc-trace.json`。**修正早先“亮带形状已在 t3”这一不完整归因：t3 负责发束底色和宽明暗，细而连续的弧形高光来自 t5 蓝通道遮罩加 PS 高光分支。**

| RDC 像素 | t3 基色 | t5.b / 指令 47 的 r3.x | 指令 482 的高光判定 | 指令 485 的高光色 r7 | 最终 RT0 |
| --- | --- | --- | --- | --- | --- |
| 弧线 `(978,1050)` | `(0.840,0.840,0.840)` | `.424` | `1` | `(.15,.15,.15)` | `(230,239,241)` |
| 线外 `(978,1042)` | `(0.840,0.840,0.840)` | `0` | `0` | `0` | `(194,202,205)` |
| 弧线 `(1085,1064)` | `(0.840,0.840,0.840)` | `.625` | `1` | `(.15,.15,.15)` | `(232,241,245)` |
| 线外 `(1085,1056)` | `(0.839,0.839,0.839)` | `0` | `0` | `0` | `(193,202,206)` |

源 PS 指令 46–47 以 `t5.zxwy` 读取蓝色遮罩到 r3.x，477–485 结合高光几何项与 cb3 强度，将遮罩变为 `r7=.15`，532–549 将高光叠到 RT0。源 t7 在这些点采样常值 `.216` 且混合权重为 0，不生成弧形。与线外相邻点 t3 基色完全相同，证明不能只调 basecolor 或泛 rim。PS33678 的完整半向量、局部光常量和后续配色尚未完整移植；当前 Unity 用 t5 蓝色纹理维持**源弧线形状**，以 t4 法线 G 与底色饱和度做局部响应近似。这并非在屏幕空间画固定弧线。暗发 `(881,1066)` 的源 t5.b 也很高、源高光判定同为 1，但整体 RT0 仍深，说明源的底色/受光层另有影响；Unity 的局部门限避免把该暗区错误刷白，后续须换成完整源方程。

`CapturedAlbedo.shader` 新增 `_UseSourceFrontHairArc` 和强度，EID1035 材质启用 `0.13` 并启用 PS33678 的 `0.96*(1−t5.g)` 后段漫反射；`ApplyCapturedMaterialFamilies.cs` 同步固化，材质已保存在 Unity。`docs/front-arc-saved.png` 对照源裁图可见浅色前发两条弧线及外侧紫发延伸。源 EID1008→1035 的 **154,205 个 RT0 变化像素**上，RGB MAE 从 **22.715→18.694**；其中只开旧后段漫反射与局部回底色为 18.806，弧线补充进一步改善。弧上 `(978,1050)` 源 `(230,239,241)`、Unity `(226,235,240)`；`(1085,1064)` 源 `(232,241,245)`、Unity `(234,245,249)`；暗发 `(881,1066)` 源 `(84,77,150)`、Unity `(120,133,180)`，是尚未解决的明显差距。保存图 `F:/KianaFrame38112Unity/Assets/Kiana/Validation/StageRenders/EID1035-arc-saved.png`；完整 EID1331 RT0 同相机图 `EID1331-front-arc-saved.png` 的前景交集 MAE **13.196**、IoU **0.9840**。后发弧线、皮肤、金属、完整四 RT 仍待继续。

### 2026-09-27：EID945 皮肤暗芯、粉色过渡、亮区的源值分层

用户指定腋下至上臂的皮肤渐变。`docs/skin-layer-source.png` 和旧 Unity `docs/skin-layer-unity.png` 同坐标裁图表明，源 RT0 是暗芯→粉色过渡→亮肤色，旧 Unity 简化 toon 阈值把过渡压成灰色硬边。已有 `docs/frame38112-skin-layer-trace.json` 证明 t3 底色变化很小、t4 法线与源在副切线反号修正后吻合。本次进一步核对 **PS31475 指令 183–330**：源主光方向约 `(-.258453,.963558,.068975)`；三个追踪点的源法线点光值分别为 `-.375/.174/.456`，Unity 同位置法线调试得到 `-.365/.169/.452`。源分段颜色寄存器 r11 在指令 330 分别约 `(.692,.591,.634)`、`(.916,.833,.843)`、`(.968,.980,.939)`，确认渐变主要来自源受光分段与颜色表，不是将另一张粉色贴图覆盖皮肤，也不能用单一 AO 乘数表达。源 t5 红通道在皮肤点为 1，选中该材质分区。

当前 `CapturedAlbedo.shader` 新增仅 EID945 使用的 `_UseSourceSkinLayer`：在源 t5 皮肤分区和暖色 t3 范围内，以源光方向点积查询从 9 个 RDC/Unity 同坐标样本反推的多段 RGB 曲线。它保留 t3 细节与已有法线基底，取代这块材质原先的灰色二段 toon 输出；**它是源采样拟合，尚非 PS31475 指令 183–330 的逐指令移植**。关键对照：暗芯 `(1155,348)` 源/Unity 都 `(130,98,105)`；粉色过渡 `(1165,385)` 源 `(166,132,129)`、Unity `(164,130,128)`；亮肤 `(1100,380)` 源 `(190,172,158)`、Unity `(190,171,158)`。`docs/skin-layer-candidate.png` 可直观看到粉色过渡恢复。源 EID928→945 的 532,385 个 RT0 变化像素 MAE **10.516→8.947**；肩臂窗口 `[940:1360,230:550]` MAE **7.176→5.380**。设置已保存到 EID945 材质与 `ApplyCapturedMaterialFamilies.cs`，保存后阶段截图哈希与候选一致。完整 EID1331 同相机 RT0 前景交集 MAE **13.196→12.712**、IoU **0.9840**，保存图 `F:/KianaFrame38112Unity/Assets/Kiana/Validation/StageRenders/EID1331-skin-and-arc-saved.png`。

继续逆向同一个皮肤分层点：`scripts/analyze_skin_light_mix.py` 直接读取保存的 RDC 像素 trace，复算 PS31475 指令 318–329 的三色混合，结果见 `docs/frame38112-skin-band-mix.json`。肩部暗芯 `(1123,358)` 的 `N·L=-0.374869`，暗层权重 `1`，选中暖灰粉 `(.724,.602,.634)`，指令 330 得到 `(.691888,.590758,.634076)`；过渡 `(1120,330)` 的 `N·L=.173635`，中层权重 `.794288`，得到 `(.915821,.832833,.843110)`；亮区 `(1100,380)` 的 `N·L=.456018`，亮层权重 `1`，得到 `(.968239,.979661,.938983)`。复算与 trace 寄存器最大差 `2.2e-8`。指令 192 将法线点光与 t5 蓝通道衍生偏移相加来移动色带位置；266–273 从 `cb3[39..48]` 选两套材质分区颜色；318–329 再混合原光照、暗/中色和亮色。这个证据明确皮肤粉色阴影来自材质颜色表与分段受光，而不只是 basecolor、AO 或贴图映射。当前 Unity 九点曲线仍是对最终 RT0 的近似：它没有接上源指令 330 后的 matcap、漫反射和高光全链路，因此暂不以只还原中间 `r11` 的候选覆盖已验收画面。

仍需逐指令恢复源的具体分段函数、结构化光源/投影与各色表，并用皮肤其他区域验证，不要将 9 个样本的近似外推为整身完全一致。当前金属、伞面、面部 SDF、后发高光、彩色描边和其他三个 G-buffer RT 仍未完成。

### 2026-09-27：鼻尖与眼发交界阴影的来源核验

直接追踪 RDC **EID992 / PS31476**，配置 `docs/frame38112-nose-trace-config.json`，原始寄存器 `docs/frame38112-nose-trace.json`。鼻尖 `(970,825)` 的源 RT0 为 `(112,75,74)`；邻点 `(971,820)` 为 `(159,126,125)`，正常脸面 `(973,830)` 为 `(199,181,177)`。这些点的 t3 **RGB 近似相同**，但鼻尖 t3 alpha 约 `.514`，邻近正常面 alpha 为 `1`。PS 指令 19 用 `cb0[199].x=-2` 的 mip bias 读取 t3，指令 21 首次用 `v0.zy` 读取 t4 面部光照/控制图；所选像素的 t4 红通道依次约 `.132/.190/.500`。指令 95–110 将 alpha、脸部遮罩和受光阈值组合，后续方向光链仍参与最终颜色。由此鼻尖局部暗色不是丢失的 mesh 或 t3 RGB 图案，也不应在屏幕固定位置补一笔。

Unity 原绑定 `RID25406.exr` 的鼻尖 t4 红色约 `.400`，与 RDC `.132` 不符；从同一捕获导出的 `RID25406.png` 未压缩导入后读回约 `.129`，其余测试点也匹配。EID992 的 `RID42972.png` 改为未压缩，并按源 mip bias `-2` 采样 t3。`CapturedAlbedo.shader` 增加仅 PS31476 / EID992 启用的 `_UseSourceFaceNose`；t3 alpha 与 t4 控制图驱动局部鼻尖明暗。当前最终 RGB 响应仍是**源证据驱动的局部拟合**，尚非 PS31476 全部后段光照指令的逐条移植。`ApplyCapturedMaterialFamilies.cs` 固化贴图/参数，`BuildGBuffer5World.cs` 跳过 EID992 t4 自动升级回不匹配的 EXR。

同场景开关对照：鼻尖从旧 Unity `(203,176,165)` 到 `(112,76,75)`，源为 `(112,75,74)`；邻点 Unity `(160,127,126)`，源 `(159,126,125)`。源 EID968→992 的 124,262 个 RT0 变化像素中，RGB MAE **6.643→2.074**。全 EID1331 源前景交集 MAE **12.712→12.583**，IoU 约 `.984`。证据图 `docs/face-nose-baseline.png`、`docs/face-nose-candidate.png`、`docs/face-nose-final-candidate.png`；保存后的 `F:/KianaFrame38112Unity/Assets/Kiana/Validation/StageRenders/EID1331-face-nose-saved.png` 与候选 SHA256 同为 `301E07081A9BDB3A9ABB75268687485D71302E88FFCBF2503CC3CEF34FCFD5F0`。

**眼睛与头发相接的黑影是另一条绘制链**：EID1008 写深色眼底，EID1035 通过模板测试避开相应区域，EID1313 再以部分透明发片覆盖。EID1313 的 t6 通道重排、源 alpha 约 `.349`、混合和剔除方向已按现场证据接入；先前局部脸窗口 MAE `16.459→14.935`。鼻尖修正没有把这块黑影当作鼻尖遮罩统一变黑。眼发交界仍有边缘、叠色及多片覆盖差异，需要沿 EID1008→1035→1313 相邻快照继续逐片验证。

### 2026-09-27：眼底逐层复核与用户指定的后发月牙/深紫描边

重新从当前 Unity 捕获 EID992、1008、1035、1313、1331，与相同 EID 的 RDC RT0 对齐。可重复脚本 `.agents/skills/rdc-unity-frame/scripts/analyze_eye_hair_stages.py`，输出 `docs/frame38112-eye-hair-stage-audit.json`。在脸窗口 `[1020:1260,850:1000]`，EID992 目标/Unity 的 `(1150,920)` 为 `(133,87,116)/(133,88,117)`，EID1008 变成 `(25,2,2)/(29,3,3)`，EID1313 后为 `(81,71,71)/(94,77,77)`。右缘 `(1170,920)` 从 EID1008 已偏差：源 `(55,5,5)`、Unity `(132,93,92)`，之后到 EID1313 为 `(80,62,84)/(125,118,154)`。EID1008 / PS31476 的新像素追踪保存在 `docs/frame38112-eye-base-trace.json`，源 t3 `(1170,920)` 采样约 `(.258,.027,.025)`、最终 `(.216,.019,.018)`；Unity 在此像素很像脸底与暗层的部分覆盖。仅为 EID1008 临时开 t3 mip bias -2，脸窗口 MAE `4.81884→4.81743`，右缘仍 `(133,93,92)`，故恢复原值。没有证据把剩余眼影误差归为纹理 mip 或鼻尖遮罩；下一步需查轮廓子像素覆盖与 EID1313 输出颜色。

用户给出“当前/目标”发尾裁图，按形状与 RDC EID1331 同相机图定位到 **EID895 后发、EID1107 后发描边**，对照图 `docs/back-hair-user-region-comparison.png`。源 EID895 高光核心 `(1411,428)` 为 `(169,170,251)`，Unity `(167,169,250)`；也就是说最亮点已经基本对齐，整体观感的差距主要在周围的受光和线色，不能靠统一增加高光强度解决。EID895 t3 调试在该点 `(157,154,217)`，源 trace t3 约 `(159,155,218)`；未压缩 `RID42842.png` 仅使 draw MAE `14.032→14.060`、发尾窗口 `6.430→6.435`，已恢复压缩设置。中间发色点 `(1400,470)` 源 `(136,140,222)`、Unity `(147,158,227)`，说明剩余偏亮来自 PS31475 受光/材质层而非缺少一张颜色贴图。

逐阶段确定 **EID1107 描边**将发尾线条写入 RT0：同一像素 `(1409,429)` 在源 EID1091→1107 从 `(166,167,245)` 到 `(37,32,91)`，Unity 从 `(168,170,251)` 到 `(6,5,13)`。Unity 使用统一近黑 `_InkColor=(.022,.018,.050)`，而 RDC EID1107 线色是多级深紫。源变化区 8,802 像素的中位 RGB `(19,17,47)`，用户指定发尾窗口 2,672 像素中位 `(20,17,50)`；临时试 `(20,17,50)/(25,22,65)/(34,29,87)` 后，第一项的 EID1107 源变化区 MAE 最低，**47.202→43.989**，发尾源变化区 **51.220→46.027**，故只给 EID1107 保存 `(20,17,50)`，其他 draw 未改。随后仅对此 draw 测试 1.0–2.2 px 宽度：源变化像素召回率从 **.590**（1 px）到 **.964**（2 px），发尾 RT0 窗口 MAE 从 **7.640→6.872**；2.2 px 虽继续降低源变化掩码 MAE，但精度从 .768 降至 .725、窗口 MAE 回升，因此保存 **2 px**。这与其源后 VS 位移中位 2.051 px 一致，且不把此前整身“过厚”的描边统一加粗。EID1107 的源变化区 MAE 从原近黑/1px **47.202→21.159**；完整 EID1331 同相机源前景交集 MAE **12.583→12.481**。代码 `ApplyInvertedHull.cs`、现场 `EID1107_Hull.mat`、图 `docs/back-hair-outline-aligned.png` 与 `EID1331-back-hair-outline-saved.png` 已保存。

EID1107 源 PS31479 实际使用 t2 颜色、t3 分段与光照形成**逐像素**紫色线，目前 Unity 倒壳仍是单色；目标此处 `(37,32,91)` 与 `(30,26,71)` 等变化不能由中位色精确复现。剩余工作是将 PS31479 的颜色计算与壳线覆盖分别接入，并逐 EID 验证。面部也尚未完整实现或验证目标 SDF 受光；鼻尖 t3 alpha/t4 控制图的局部修正不能代替整脸 SDF 对照。

### 2026-09-27：EID992 面部 SDF 在当前帧的实际贡献

另取脸部 8 点 `(1020,790)`, `(1050,800)`, `(1050,850)`, `(1050,920)`, `(1100,850)`, `(1100,950)`, `(1150,800)`, `(1200,850)`，逐指令记录在 `docs/frame38112-face-sdf-trace.json`，配置在同名 `-config.json`。源 PS31476 指令 98–110 使用 `cb2[5]·normalize(v3)`、`cb2[6]·normalize(v3)`、`cb3[76].zw=(.85,.62)` 和 t3 alpha 形成 50 倍硬阈值，再将结果用于颜色乘数。该 8 点 t3 alpha 均为 1、阈值均为 1、判定均为 1、最终 SDF 颜色乘数均为 `(1,1,1)`。原鼻尖追踪的 4 点也在同一分支，只有 `(970,825)` 的源局部暖暗色乘数约 `(.700,.595,.590)`，由面部控制图/底色路径决定。故**这帧已核验的脸颊和额头点不存在遗漏的整脸 SDF 暗层**；鼻尖局部与眼边黑影分别要查 t3/t4 局部响应及 EID1008/EID1313 叠层。Unity 仍未逐指令移植完整 PS31476，不能据此称面部 shader 已完成。

对相同相机 EID992 RT0 的脸部窗口 `[820:1270,700:1120]`，源 EID968→992 的 110,105 个变化像素 RGB MAE 2.141；向内腐蚀 5px 后的 101,683 像素 MAE 2.004，90.15% 的内部像素最大通道误差不超过 5/255。`docs/face-sdf-current-audit.png` 显示明显剩余误差集中在眼、头发边界与鼻尖等局部，不应通过全脸统一压黑或提高金属度处理。

### 2026-09-27：同阶段 RGB 色调审计与头发中间色

用户并排图指出 Unity 整体观感较亮。新增 `.agents/skills/rdc-unity-frame/scripts/audit_stage_tone.py` 对每个 EID 的**源相邻阶段变化像素**计算源/Unity RGB 和亮度，结果 `docs/frame38112-stage-tone-audit.json`。改动前 EID875 伞平均亮度 +1.9/255、EID945 身体 +6.1、EID992 脸 −0.0，而 EID895 后发 +13.2、EID1035 前发 +20.9、EID912 金属饰件 +14.5。故不对全画面统一调暗；也不能只凭金属度解释已着色 RT0 中头发的差值。

同阶段源变化区算得后发平均 RGB 误差 `(Unity−RDC)=(+8.536,+15.211,+7.633)`，前发 `(13.762,23.694,14.575)`。先试灰度系数 .85：后发/前发 MAE `14.1→12.8` / `18.7→15.8`，但蓝通道变得过暗。于是根据逐通道均值求取 EID895 `_SourceHairToneRGB=(.90,.83,.95)`、EID1035 `(.90,.84,.93)`，只作用于各自头发中间色。后发在 t5.b 月牙恢复**之前**校正；前发用 t5.b 与 t4.g 的弧形遮罩排除亮线，然后叠加原有高光。亮线 `(978,1050)/(1085,1064)` Unity 恢复到 `(226,235,240)/(234,245,249)`，源 `(230,239,241)/(232,241,245)`；后发亮点 `(1411,428)` Unity `(167,169,250)`，源 `(169,170,251)`。

最终同阶段变化区：EID895 491,562 px 平均 RGB 差 `(−.154,+.095,−.033)`、MAE **10.0**；EID1035 154,139 px 平均差 `(.790,1.084,1.300)`、MAE **12.9**。EID1331 全前景交集 MAE **12.481→11.420**，IoU .98514。已保存 Unity 两个材质、`CapturedAlbedo.shader`、`ApplyCapturedMaterialFamilies.cs` 和 `Assets/Kiana/Validation/StageRenders/EID1331-hair-tone-saved.png`。这是按当前单帧 RT0 数据校准的中间色补偿，**不是**完整移植 PS31475/33678 的方向光、金属度或其它 G-buffer 输出；后发 `(1363,571)` 仍偏暗，个别局部仍需分区修复。材质 YAML 中 `_SourceHairToneGain=.85` 是 A/B 试验遗留的未使用属性，shader 现只读取 `_SourceHairToneRGB`。

同轮测试了 EID912 金属饰件的 `_ArtSpecularStrength=1→0`。亮度偏差 +14.5→+9.9/255，但源变化区 RGB MAE **25.3→27.4**，说明该高光不能直接删掉；已恢复强度 1，重新生成 `frame38112-stage-tone-audit.json`。大误差主要聚在源图 `(839:1065,527:723)` 和 `(1041:1176,528:666)` 的饰件/衣服区域，后续需分开追踪 PS31475 t5 材质层、t7、半向量高光与光照颜色。当前关于“金属度导致整体过亮”的判断未获 A/B 支持；RT0 颜色与其它 RT 的金属/粗糙数据应分别验证。

继续追踪 EID912 的 5 点，见 `docs/frame38112-eid912-metal-trace.json`；裁图 `docs/eid912-metal-source-unity.png` 直观看到源深色饰件配窄白反射，而旧 Unity 的底面呈大面积灰色。暗点 `(890,560)` 源 `(72,84,110)`、Unity 旧 `(155,154,155)`，源 t5.g≈.731，PS31475 指令 431–432 先以 `.96×(1−t5.g)` 调漫反射，指令 435–532 的高光项随后单独加入。将 Unity 现有 `_UseSourceLateDiffuse` **直接接在已含高光的颜色后**，整块亮度误差由 +8.5 变 −21.6、MAE 21.5→28.4，验证了乘错运算顺序；已关闭，后续应分别构造漫反射与高光再按源顺序合成。

保留现有高光，EID912 `_ArtShadeStrength=0→1`、toon 分界阈值 .1→.6→.8→.9 的同阶段变化区 MAE 分别为 **25.2→24.6→21.5→19.8→21.3**；因此保存阈值 **.8**。源/Unity EID912 平均亮度从 `54.1/68.5` 变 `54.1/56.5`，色调差 +14.4→+2.4/255。`ApplyCapturedMaterialFamilies.cs` 与现场材质已保存；EID1331 全前景交集 MAE **11.420→11.158**，IoU .98519，图 `F:/KianaFrame38112Unity/Assets/Kiana/Validation/StageRenders/EID1331-hair-metal-tone-saved.png`。这是基于 RT0 的明暗边界改进，白色高光分布仍未完全吻合源 PS。

又测试把现有 Art Spec 项在 t5.g 衰减后加回，EID912 MAE **19.8→26.9**、亮度差 +2.4→−21.2；当前 Art Spec 数值不足以代表源 PS31475 指令 435–532 的反射。该候选 shader 与材质开关均撤销，重捕获图与已保存版本逐字节一致。需要移植源半向量、粗糙/强度控制和分段 tint，而不是调整现有高光的运算位置。
## 2026-09-27 前发发尾的深紫黑影：EID1183

用户指出最终 RT0 的发尾和脸旁缺深黑阴影。同相机取 `(1010,1040)`：源 EID1143 仍为肤色，EID1161→1183 后成为 RGB `(33,29,84)`；原 Unity 到 EID1331 仍为肤色 `(200,179,175)`。因此这块黑影至少有一部分来自 EID1183 / PS31479 的前发倒壳描边覆盖，不能用头发金属度或全局降亮度处理。源阶段文件在 `analysis-frame38112/gbuffer5-outline-snapshots/EID1183-RID53242.png`，Unity 同阶段图在 `Assets/Kiana/Validation/StageRenders/EID1183-through.png`。

在发尾 ROI `x=800..1250,y=850..1280`，源 EID1161→1183 改变 4,706 像素，颜色中位 RGB `(20,19,42)`；源 VS 屏幕位移中位 1.825px。原 Unity 1px 常量墨色 `(6,5,13)` 仅覆盖源改变像素的 0.551，源变化区 RGB MAE 50.862。`audit_outline_draw.py` 增加 union/ROI 误差及误检、漏检统计后，保持相同相机和场景测试：1.8px + 源中位色的召回 0.796、精度 0.549、源变化区 MAE 31.510、整个 ROI MAE 12.099；2.2px 召回 0.839、精度 0.510、ROI MAE 12.188；2.4px 的精度降至 0.481、ROI MAE 12.295。更宽虽然能命中个别黑点，也明显增加脸部/眼周误覆盖。

最终 EID1331 同相机源前景交集 MAE：原保存图 11.158，1.8px 11.103，2px 11.111，2.2px 11.128。最终发尾 ROI 的全像素 MAE：原 12.573，1.8px 12.277，2.2px 12.375。选 1.8px 并保存 EID1183 材质墨色 RGB `(20,19,42)`；可重复应用器 `.agents/skills/rdc-unity-frame/assets/ApplyInvertedHull.cs` 与 Unity `Assets/Kiana/Editor/ApplyInvertedHull.cs` 已同步。最终对照图 `docs/hair-tip-final-audit.png`、保存阶段图 `Assets/Kiana/Validation/StageRenders/EID1331-front-hair-shadow-saved.png`。

限制：源 PS31479 墨色随像素变化，当前 shader 用单一中位色；`(1010,1040)` 在 1.8px 下为 `(110,99,109)`，仍未达到源 `(33,29,84)`。继续时应检查该点 EID1183 的三角形覆盖及源 PS31479 的 t2/t3 分段颜色，恢复每像素阴影，而非全局扩大 hull。倒壳与后续眼部 draw 的遮挡顺序也需保留。

试过仅对捕获相机用 EID1183 的原始 VSOut clip（网格 UV5 已有 6,342 个值）：发尾源差分召回为 1，但误涂 119,769 个 ROI 像素，最终前景 MAE 21.290，远劣于 1.8px 版本的 11.103。源顶点本身不足以重现覆盖，必须同时恢复模板/深度/剔除规则。诊断分支已撤销；重新刷新 shader 后 `EID1331-through.png` 与保存版 SHA256 相同。

## 2026-09-28：G-buffer 四附件收尾契约

本轮不再把 RT0 的观感当作 G-buffer 完成。RDC EID1331 的四个颜色附件与深度已同时导出：RT0 `R16G16B16A16_FLOAT`、RT1 `R8G8B8A8_UNORM`、RT2/RT3 `R10G10B10A2_UNORM`、深度 `D24S8`。原始 DDS 保存在 Unity 工程的 `CapturedData/GBuffer/EID1331/`；可视化 mip0 作为明确标注的参考资产保存在 `Assets/Kiana/Reference/GBuffer/`，由 `Frame38112_EID1331_GBufferReference.asset` 统一引用。五个参考 PNG 与 RenderDoc 导出文件的 SHA256 逐字节一致。它们只作为后续 pass 的临时输入和验收 oracle，不能标为 Unity 原生重建结果。

找到并修复了会同时破坏 RT0 光照与 RT3 法线的两个公共错误：源 VS 使用 `cross(N,T) * tangent.w`，旧 Unity shader 额外取反了 bitangent；四张 body normal 为线性 `R8G8B8A8_UNORM`，旧导入设置却是 sRGB。现已恢复源 TBN 符号、线性未压缩法线导入和 `cb0[199].x=-2` 的 mip bias。相同场景 EID1331 RT0 前景 RGB MAE 从约 10.007 降到 **9.551/255**；EID858 从 16.722 降到 **16.482/255**。几何覆盖继续保持接近 1，但这不代表材质方程完成。

当前 G-buffer 阶段的边界记录在 `Assets/Kiana/Validation/GBufferPhaseSummary.json`：RT0 的各 PS 方程仍有近似分支；RT1 辅助光/高光链未完整移植；RT2 的上一帧运动量未移植；RT3 还要按 face、outline、eye 等 PS 家族恢复各自写出和 stencil/depth 覆盖。为避免在这一阶段无限消耗，后续合成从 Unity 原生 G-buffer 输出继续；EID1331 的精确附件仅用于同 EID A/B 和定位误差，不能接进运行时画面。

纠正：曾把 EID1331 的 RDC RT0 临时接到 `NativeCharacterCompositeSource` 的 Game 输出，这会把参考图误显示为 Unity 重建结果。该运行时入口已经完全删除，最终相机不再包含 `useCapturedGBufferCheckpoint` 或参考纹理字段。RDC 五附件现在只存在于独立验证资产中，用于离线差分；Game/Scene 中的人物必须来自 Unity 网格和 shader。重新抓取的原生 RT0 为 `Assets/Kiana/Validation/MRT/EID1331-RT0.png`，前景 RGB MAE **9.544/255**、P95 **34/255**；最终相机原生图为 `Assets/Kiana/Validation/FinalComposite-Stage2475-NATIVE.png`。此数值是 G-buffer 主线的当前收尾点，后续转入 EID1335–1387 深度金字塔/灯光列表和 EID1392–1511 Deferred Shading；参考图只能作为验收 oracle，不能再次作为运行时输入。

## 2026-09-28：EID1403–1511 原生延迟链

已将 DXBC→HLSL 固化进 `.agents/skills/rdc-unity-frame/`：批量导出脚本一次打开 RDC，保存每个 EID 的 VS/PS DXBC、反编译 HLSL、SHA256 和工具提交；固定使用 `coconutbird/d3dasm` `a292206` 与 `napbat/cfglib` `6e57c16`。Unity 生成器为 EID1403、1419、1429、1447、1466、1484、1511 分别生成独立 ShaderLab pass 和捕获常量数组，不提前合并阶段。

修正了两项会让输出先异常着色再全黑的状态翻译错误。RenderDoc 的 `CompareFunction=6` 来自 `replay_enums.h`，含义是 `Equal`，不能按 D3D12 原生数字表解释为 `NotEqual`。另外，原角色深度预阶段在可见角色像素留下 stencil bit `0x80`；EID1419 用 Ref 144 / ReadMask 160 选择该材质家族。Unity 现将这个预阶段位并入原生几何写入，同时保留各 draw 的低位 stencil。对本帧，EID1419 改写 RID53286；1429/1447/1466/1484 因 stencil 不命中而保持结果；EID1511 将 RID53286 一比一复制到最终工作目标。D32S8 深度目标为 RID53238，shader 读取的 RID53259 是同一底层资源的 SRV 视图。

逐级原生检查点保存在 `Assets/Kiana/Validation/DeferredNative/`，每级同时有 EXR 和 PNG。EID1419 到 EID1484 的 Unity 文件逐字节相同，符合该帧 RDC 中 RID53286 只有 EID1419 发生变化的事实；EID1511 工作复制与 EID1419 文件也一致。与 RDC 比较时，EID1419 的角色覆盖 IoU **0.99540**、前景 union RGB MAE **12.707/255**、P95 **43/255**；EID1511 对 RID53294 为 MAE **12.778/255**、P95 **42/255**。误差主要继承 EID1331 尚未完全还原的 RT1/RT2/RT3 和少数 RT0 材质方程，不能称像素完全一致。

最终 Game 视图现在由 Unity 网格→原生 G-buffer→EID1419 延迟着色→EID1511 复制→背景合成驱动，RDC 快照仍只用于离线比较。`NativeCharacterCompositeSource` 保留显式路由开关，任何后续阶段失败都能回退到可见的原生角色渲染，不再让实验 pass 把主画面变黑。数值报告为 `Assets/Kiana/Validation/DeferredNative/deferred-validation.json`，左右对照为 `EID1419-reference-vs-native.png`。
