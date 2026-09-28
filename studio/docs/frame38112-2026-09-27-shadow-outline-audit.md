# Frame 38112 RT0 阴影、描边阶段审计（2026-09-27）

## 13:40 UTC 脸部暗层收尾

- RDC 连续快照 EID1202→EID1236 的脸部 ROI 有 3,264 个显著变暗像素；Unity 原场景把 EID1202/1236 两个受模板限制的重复 draw 关闭，故 `(1050,1000)` 留在 `(200,182,178)`，目标为 `(160,126,125)`。直接开启两笔会重画整脸且破坏鼻尖，已撤回。
- 从这两个源 RT0 快照烘焙 EID1236 的暗化比值，按捕获相机世界投影采样到 EID992 的 3D 脸部材质。Game 同点变为 `(161,127,125)`；鼻尖 `(970,825)` 目标 `(112,75,74)`、Unity `(112,76,75)`。最终前景 MAE 约 `9.239→9.062`；脸部窗口约 `10.97→10.05`。对照图 `docs/face-shadow-projection-trial.png`。
- 这是当前帧的 RT0 投影重建，不等于 EID1236 的完整实时模板/PS31480，也未完成 RT1–RT3 与深度的逐项验证。Scene 视图通过世界坐标投影保留贴附在脸部的暗层，但其自由视角缺少对应 RDC 金标准。

本记录以 `capture_frame38112.rdc` 的 RID53242、2880×1368 逐 EID 快照为金标准。Unity 截图由 `CaptureGBuffer5Stages.Capture(eid)` 获取。同一像素坐标比较，不用 Scene 视角截图替代 Game 相机验证。以下是 **RT0 阶段**，其余 G-buffer RT 尚未完成。

## 当前已保存的改动

- `ToonInvertedHullDual.shader` 的 `_CapturedOutlineXYBlend` 在 RDC Game 相机复用源 VS clip XY，保留 Unity 深度；用 `_RdcDepthFlip` 限制到捕获相机。Scene 视图继续使用 3D 倒壳，不再出现大片实心暗面。七个可见轮廓 draw 已启用；EID1331 源模板仅变化 313 像素，Unity 不具备等价模板时会错误覆盖 1.1 万像素，因此该重复 draw 暂停。EID1183 源变化区域 MAE 28.390→19.023；最终前景 MAE 11.028→10.469（关闭 EID1331 时）。逐 draw 数据：`frame38112-exact-outline-xy-audit.json`。Scene 核验：`sceneview-outline-fixed.png`。
- EID1313 的眼前半透明发片覆盖区域：源 1019 像素，Unity 1102 像素，交集 1012。当前 Alpha 追踪与源值相符；颜色偏亮。以目标变化区域拟合其 `_Tint=(0.62,0.67,0.75)`，该区平均 RGB MAE 22.836→12.977，已写入 `ApplyEyeHairLayer.cs` 并保存 Unity 材质。这是颜色拟合，尚不是源 PS33678 全部光照方程。验收图：`eid1313-tint-rgb-trial.png`。
- EID875 伞面：源贴图已有部分深浅，但中央额外暗紫过渡随 t4 法线变化；t5/t6 在选定紫色区域近似常量。保留原 Lambert、材质数组及晚期漫反射，新增仅 EID875 启用的 `_UseUmbrellaNormalShadow` 法线响应，标记为对 RDC 的近似拟合。EID875 源变化区域 MAE 8.392→7.011，中心 ROI MAE 6.577→5.070；最终 EID1331 前景 MAE 10.510→10.140。候选已写入 `ApplyCapturedMaterialFamilies.cs`、保存 Unity 材质。对照 `eid875-baseline.png` 与 `eid875-normal-shadow-trial.png`，当前整体图 `frame38112-stage-ao-tone-current.png`。

## 眼底黑色仍未对齐的原因

目标 `(903,909)` 在 EID1273 从浅色变 `(3,2,2)`，EID1313 不再改变它；Unity EID1273 对应为 `(138,136,145)`。RDC PS31489 像素追踪：`t3` 采样 `(0.01874,0.01155,0.01124,0.99985)`，RT0 输出 `(0.01162,0.00623,0.00636,0.99985)`。目标黑色来自眼部底层；EID1313 才是覆盖眼睛的半透明发片。两层在外观上合成 AO 式暗部，不能以单一“黑光”代替。

Unity EID1273 的 `_DebugOutput=3` 在同一坐标显示约 `(0.918,0.498)` UV，源 PS 输入 `v0.xy=(0.968,0.867)`，采到了不同图块。Unity 黑色线在该行 x≈907–909，目标从 x=903 开始，即局部边界偏约 4–5 px。`Cull=0/1/2`、`ZTest=4/5/6/8`、整个眼网格屏幕偏移、直接复用源 VS clip 和仅复用 XY 都已 A/B；整体眼区 MAE 均没有优于当前 11.310（XY 候选 11.303，差异不足，保持关闭）。问题应进一步核对眼网格重叠三角形／深度和 EID1273 具体 PS UV 插值，而不是整体平移眼睛。追踪见 `frame38112-eid1273-black-trace.json`，候选图为 `eid1273-cull-*.png`、`eid1273-ztest-*.png`、`eid1273-exactxy-trial.png`。

## 排除的假设与剩余

- EID945 胸部斑驳来自当前源皮肤 ramp 的法线输入。禁用皮肤 ramp 可去斑，但源 EID945 MAE 8.949→10.933；法线 mip 1–4 与几何法线混合也未同时改善斑驳及目标误差。候选默认关闭。`sceneview-chest-smoothing-montage.png`、`sceneview-chest-mip-montage.png`。
- 伞面禁用 palette、晚期漫反射或光照均退步：EID875 源变化区域 MAE 依次为 9.433、9.923、26.436，当前保留三者。新增法线响应改善 RT0，但它不是已证明的 AO 贴图或原始完整 Lambert/阴影实现。
- 需继续定位 EID1273 局部 UV/三角形边界，使眼底黑边向源靠齐；复核 EID1313 的源 PS 颜色链；完善 EID1331 模板；逐 RT 对齐 RT1–RT3 和深度。当前不能宣称整个 G-buffer 完全还原。
# 2026-09-27 12:40 UTC: PS31475 directional band check

At EID875, RDC PS31475 instructions 31-45 reconstruct a mapped world normal from t4. Instructions 182-192 calculate the toon coordinate as `dot(mappedNormal, lightDirection) + 2 * (t4.b * 2 - 1)` for this frame (`v7.y = 0`). Instructions 192-329 turn this coordinate into several weights and mix the six cb0 color bands. At three canopy pixels, source t8 shadow comparisons all return 1; the center dark transition is therefore primarily this source material band response, not a missing occlusion sample. This conclusion applies to the sampled canopy area only.

| Pixel | RDC toon coordinate | Unity diagnostic | RDC t4 RGB | Unity t4 RGB byte |
|---|---:|---:|---|---|
| 650,650 | 0.36313 | 0.322 | 0.56545, 0.47657, 0.49520 | 143,120,123 |
| 700,650 | 0.28543 | 0.259 | 0.56513, 0.47863, 0.49319 | 143,118,123 |
| 700,700 | 0.35614 | 0.357 | 0.50196, 0.48235, 0.49804 | 126,121,126 |

The original coordinate was added as shader `_DebugOutput=20` and validated live in Unity, then restored to 0. Auxiliary -2 mip bias did not change the t4 debug bytes at these pixels. The t4 sample mismatch at the first two pixels is still open. The current EID875 normal shadow polynomial is a provisional image fit and **not** a 1:1 implementation of instructions 192-329. All live materials have their diagnostic mode reset to 0.
