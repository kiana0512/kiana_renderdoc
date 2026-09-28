# Frame 38112 续作索引

2026-09-27 最新审计先读 [阴影／描边阶段记录](frame38112-2026-09-27-shadow-outline-audit.md)。当前 Unity 保存的 EID875 法线明暗和 EID1313 眼前发片色调仍是 **RT0 近似拟合**，不是 1:1 源 shader；用户明确要求替换为 RDC PS 原始计算。新增 EID875 像素追踪 `frame38112-eid875-light-trace.json`：PS31475 指令 28/31 采 t3/t4，46/49 采 t5/t6，93 采 t0，136–153 对 t8 进行八次 PCF，182–212 根据法线与光方向构造色阶，266–330 选 cb3 材质颜色，431–545 组合漫反射/材质/光照。采样伞布三像素的 t8 八次比较值均为 1，t5/t6 在此紫色区域近似常值；暗紫过渡不能归因为 t8 遮挡，也不能简单称为 AO 贴图。下一步应逐指令移植 182–330 与 431–545 的源链，和 EID945 皮肤、EID895 头发复用家族实现，每步用相邻 EID 源 RT0 差分验收。EID1273 局部眼底黑边仍缺，见审计记录；RT1–RT3 和深度仍待验证。

目标：`E:/KianaCaptures/ZenlessZoneZero/绝区零-1790334599799/capture_frame38112.rdc` 的 G-buffer 材质艺术效果，在 `F:/KianaFrame38112Unity` 的可编辑 3D 场景中还原。当前工作仓库是 `F:/KianaStudioElectron`。优先完成各材质的明暗、高光、rim、描边，再做后续背景/UI 合成。不要每轮重新扫完整 RDC；先读此页、`docs/frame38112-reconstruction.md` 和 `docs/frame38112-shading-feature-map.json`。

## 固定入口

- Unity 场景：`Assets/Kiana/Scenes/Frame38112_GBuffer5_World.unity`；材质：`Assets/Kiana/Materials/EID*_GBuffer3D.mat`。
- 可重复源代码：`.agents/skills/rdc-unity-frame/assets/CapturedAlbedo.shader`、`ApplyCapturedMaterialFamilies.cs`、`ApplyEyeHairLayer.cs`；复制到 Unity 对应路径后刷新，再分别调用应用器。`BuildGBuffer5World.cs` 重建场景时会调用眼部发片应用器。
- 源 PS31475 反汇编：`E:/KianaCaptures/ZenlessZoneZero/绝区零-1790334599799/analysis-frame38112/gbuffer5-shaders-all/EID858-fragment.txt`。EID858/875/895/912/945 等共享此 PS，但各 draw 的常量和贴图不同。
- 逐 draw 输入：`docs/frame38112-gbuffer5-pixel-constants.json`、`docs/frame38112-material-tables.json`、`Assets/Kiana/Manifest/gbuffer5-bindings.json`。
- 源 RT0 快照：`E:/KianaCaptures/ZenlessZoneZero/绝区零-1790334599799/analysis-frame38112/gbuffer5-early-snapshots/EID<id>-RID53242.png`。EID945 全阶段源图另在 `gbuffer5-snapshots/`。
- Unity 捕获入口：`CaptureGBuffer5Stages.Capture(eid)`，阶段图存 `Assets/Kiana/Validation/StageRenders/EID<id>-through.png`。比较脚本 `.agents/skills/rdc-unity-frame/scripts/compare_stage_pngs.py`。逐 draw 只比较该 EID 相邻源快照改变的像素。
- 当前 EID945 皮肤分层 draw 变化区 MAE **8.947**；EID992 鼻尖 **6.643→2.074**；EID1107 后发描边源变化区 **47.202→21.159**。最新头发 EID895/1035 **14.1→10.0** / **18.7→12.9**，金属饰件 EID912 **25.2→19.8**。完整 EID1331 同相机 RT0 源前景交集 MAE **11.158**、IoU **0.98519**，当前图 `F:/KianaFrame38112Unity/Assets/Kiana/Validation/StageRenders/EID1331-hair-metal-tone-saved.png`。这只是 RT0 阶段分数，不代表全部材质或四 RT 完成。
- 姿态基线：`docs/frame38112-unity-pose-audit.json` 是 26 个**现场 Unity 网格**与源矩阵的逐顶点世界坐标审计，最大差 0.00006104；`docs/frame38112-unity-pose-upright.png` 是不改动网格的正向捕获视角图，源图 `docs/frame38112-gbuffer-upright.png`。两者前景 IoU 0.986129。自由 Scene 视角不可作为 RDC 姿态差异的唯一证据；先用 `AuditCapturedPose.Run()` / `CaptureUpright()` 核对同相机。

## 已验收的材质设置

| Draw | 区域 | 已保存的处理 |
| --- | --- | --- |
| 875 | 伞 | toon shade 1、分界阈值 .6、t7 post-light blend、t5/t7 分别解码、PS31475 t5.g 的 matcap 后漫反射、albedo mip bias -2；高光/完整方向光仍缺源路径 |
| 895 | 后发 | toon shade 1、t5.b 月牙亮带局部补色、PS31475 后段漫反射、源 RGB 中间色校准 `(0.90,0.83,0.95)`；t7、mip bias 关闭；同阶段变化区 MAE 14.1→10.0 |
| 912 | 胸前金属 | 保留高绿区域高光 1、toon shade 1 / 分界 .8、mip bias -2；新增 PS31475 指令 431–434 的独立 diffuse/F0 分支，仅在 t5.g 金属区以 0.30 混合；独立 F0 高光 scale 27。119,264 个变化像素 MAE 18.688→15.676。t7、rim、错误顺序的 t5.g 后乘仍关闭 |
| 945 | 身体 | toon shade .5、mip bias -2、RID42974 未压缩导入；源采样皮肤三层暖色受光 `_UseSourceSkinLayer=1`，draw MAE 10.516→8.947；金属高光、rim 仍关闭 |
| 968 | 胸前青色宝石 | PS42681 band 0 / t7 slice 12 的切线视角 UV、青蓝色 tint、t5/t6/t7 分槽解码和源光照；局部变化区 MAE 104.209→26.171 |
| 992 | 脸与鼻尖 | t3 alpha + t4 面部控制图，t3 mip bias -2、两张 PNG 未压缩；源变化区 MAE 6.643→2.074；最终明暗为局部拟合，完整 PS31476 光链待移植 |
| 1035 | 前发弧形高光 | PS33678 t5.b 弧形遮罩、t4 法线局部响应、后段漫反射；源 RGB 中间色校准 `(0.90,0.84,0.93)` 排除弧线，亮线保留；同阶段变化区 MAE 18.7→12.9；用户已确认弧线方向正确 |
| 1107 | 后发描边 | 用户指定发尾：单独用源线色中位 RGB(20,17,50)、2px 倒壳；源变化区 MAE 47.202→21.159，召回率 .590→.964；逐像素紫色层待移植 |
| 1183 | 前发与脸旁深紫黑影 | 源 EID1161→1183 差分定位；源描边颜色中位 RGB(20,19,42)、VS 位移中位 1.825px。Unity 保存 RGB(20,19,42)、1.8px 倒壳，发尾窗口源像素召回率 .551→.796，最终同相机 RT0 前景 MAE 11.158→11.103；逐像素调色仍待移植 |

原始 BC7 DDS 直接绑定会因颜色空间不匹配严重退步。后发逐级 PNG mip 资源已导入作诊断，但 EID895 误差 16.7488→16.7815，未绑定。相关证据、失败实验详见 `docs/frame38112-reconstruction.md` 末节。

## 当前立即处理

1. 前发 EID1035 / PS33678：`docs/frame38112-hair-arc-trace.json` **纠正旧归因**：t3 只有底色/宽亮带，细弧线来自 t5 蓝通道遮罩触发源 PS 高光。相邻灰发像素 t3 都约 .84，t5.b 为 .424/0，源高光判定 1/0，最终亮线/线外相差约 35 RGB。Unity 已保存 `_UseSourceFrontHairArc=.13` 和后段漫反射，源变化区 MAE `22.715→18.694`；裁图 `docs/front-arc-source.png`、`docs/front-arc-saved.png`，用户确认视觉方向正确。现用 t4 G 近似源半向量门限，暗发 `(881,1066)` 仍差约 30–50 RGB；后续移植完整半向量/光常量，避免把近似当逆向结束。
2. 后发 EID895 月牙：`docs/frame38112-back-hair-trace.json` 确认亮点 t5.b≈.232、邻近暗带 t5.b=0；已保存 EID895 专用补色并保存源 `0.96*(1−t5.g)` 后段漫反射，源 draw 变化区 MAE `16.471→14.027`。继续恢复 PS31475 的完整受光与高光方程，通用 rim 的失败候选保持关闭。
3. 皮肤、鼻尖与脸发暗影：`docs/frame38112-skin-layer-trace.json` 证明源 v4 与原 Unity bitangent 反号，现已修正。新增 `SourceSkinRamp` 用 9 个同坐标源样本恢复腋下暗芯、粉色过渡、亮肤色；PS31475 指令 183–330 的源法线点光值/分段颜色寄存器已有证据，现为拟合曲线，尚未逐指令移植。肩臂窗口 MAE `7.176→5.380`，暗芯 `(1155,348)` 源/Unity 都 `(130,98,105)`。鼻尖见 `docs/frame38112-nose-trace.json`：EID992 / PS31476 的 t3 alpha 与 t4 `v0.zy` 控制图生成局部暗色；已保存未压缩 `RID42972.png`/`RID25406.png`、mip bias -2 和 `_UseSourceFaceNose=1`，鼻尖源 `(112,75,74)`、Unity `(112,76,75)`。新补 `docs/frame38112-face-sdf-trace.json` 逐指令查 8 个脸颊/额头点：源 SDF 判定和色乘数全部为 1，当前帧这些位置没有缺失的整脸暗层。眼旁黑影则来自 EID1008 暗底、EID1035 模板避让、EID1313 半透明发片，不属于鼻尖同一遮罩。EID1313 已激活并保存源 alpha/混合、对称眼部模板与 CullFront；眼旁 alpha 调试值与源追踪同为约 .349，脸部窗口 MAE `16.459→14.935`。下一步核对 EID1313 多片重叠、PS 输出色和 EID1008 眼底颜色；细节见重建文档末节。
4. 描边：当前 8 个可见 EID 使用 `ToonInvertedHullDual.shader`。EID1107 后发为源中位深紫 RGB(20,17,50)、2px；EID1183 前发发尾为 RGB(20,19,42)、1.8px；其他 draw 仍为1px，EID1331 仍为0。源 PS31479 的 t2 颜色、t3 分段、光照导致逐像素紫色变化，单色中位只是已量化改进，不能称为彩色描边完成；下一步移植 PS31479 颜色并单独校正其余 EID 宽度/模板。
5. 四个 G-buffer RT 尚未一一对齐；当前 Unity 只输出 RT0。金属、粗糙、自发光、投影阴影和后续合成仍有明显差距，按材质区域逐项对照。

2026-09-27 同场景批量重捕获后按源相邻 RT0 的变化像素排序：伞 EID875 **629,460 px / MAE 18.07→12.67→9.923→8.392**（toon 分界、t5/t7 源值与 PS31475 后段漫反射）、身体 EID945 **532,385 / 10.514**、后发 EID895 **494,241 / 16.471**、前发 EID1035 **154,139 / 22.72**、胸前饰件 EID912 **119,264 / 24.030**。掩码数量随源相邻快照/差值门槛略有变化。不要用全图黑背景稀释后的 5.448 判断材质已对齐。伞暗点 `(240,528)` 从 Unity `(120,118,164)` 到 `(31,34,80)`，源 `(41,45,83)`；邻近亮点 Unity `(73,51,108)`、源 `(73,49,102)`。RDC 追踪显示该区 t8 投影比较全为 1；深色来自 t5 band 2 / t7 slice 4 与 `0.96×(1−t5.g)` 的后段受光。t4 法线已经对齐，不要将所有 EXR 一起解码；t6 虽有源/Unity 颜色编码差异，当前候选使 draw MAE 9.923→10.855，暂不保存。对 EID945、EID912、EID895 独立开 t5/t7/t6 候选，分别为 10.625 vs 原 10.514、40.403 vs 24.030、16.472 vs 16.471，全部复原。详见重建文档末节和 `docs/frame38112-umbrella-shadow-trace.json`。

EID968 胸前宝石已恢复：`docs/frame38112-gem-trace.json` 追踪 PS42681 319–371、418–543，源 t7 slice 12、cb3 band 0 tint `(0,.491,1)`，UV 使用 `v0*(10.32,9.08)+(1,0) - .33*t6.x*dot(view,normal)^2*切线视角`。Unity 中源 UV 的 V 与导入贴图 V 反向，恢复后 3 个追踪点的 t7 UV 与 RDC 相差约 .001。t5/t6/t7 需各自做 sRGB 解码；只有这个 draw 开启。源 EID945→968 的 1,975 变化像素，Unity MAE **104.209→26.171**；像素 `(930,580)` 源 `(0,223,255)`、Unity `(0,222,255)`。余差主要是宝石边缘及高光图案，后续仍需补齐 PS42681 完整方向光。验证用 `compare_draw_delta.py`，候选图 `EID968-through-gem-source-v5.png`。该脚本截帧会覆盖 `EID968-through.png`，比较前须把每个候选复制为不同文件。

2026-09-28 已按 `docs/frame38112-eid912-metal-trace.json` 落地 EID912 的首个隔离源分支：`r12=.96*(1-t5.g)*base` 与 `r13=lerp(.04,base,t5.g)` 分开进入漫反射和高光。全量替换会把 MAE 18.688 恶化到 24.852，按真实 Unity 重渲染扫描 0.20/0.25/0.30/0.35/0.40 后，0.30 最优。随后固定 0.30 扫描独立 F0 高光，scale 27 最优，最终 MAE **15.676**；该较大系数补偿当前近似 spec lobe 的能量，不能冒充 PS31475 的真实 roughness 方程。下一步补 435–528 的真实 roughness/half-vector，把经验 scale 移除，再做彩色描边、眼旁黑影与后发局部暗带。其余三个 G-buffer RT 仍未完成。

## 执行约定

Unity CLI：`C:/Users/RT/AppData/Local/Unity/bin/unity.exe command eval '<C#表达式>' --project-path F:/KianaFrame38112Unity --timeout 120 --format json`。修改 shader 后复制到 Unity、`AssetDatabase.Refresh()`，随后另一次 eval 调应用器。先检查目标 GameObject 的 `activeSelf`；禁用对象的材质 A/B 会出现虚假的“无变化”。每个新分支做同状态开/关捕获，只有原图与 Unity 的局部形状及颜色都改善才保存；失败参数复原。每轮将结果追加重建文档并更新本页，免重扫。
