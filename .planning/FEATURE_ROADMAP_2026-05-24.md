# 产品差异化构建 Roadmap (2026-05-24)

定位: **「透明 · 可验证 · 诚实 · 教你看懂」的紫微工具** —— 不对标测测的黑箱+占卜师
marketplace, 而是把刚完成的工程级算法审计 (68 tests + 结构不变量 + Codex 异源验证)
变成产品灵魂。详细战略见本 session 对话记录。

用户已选定先做三项 (按依赖+风险排序执行)。**状态: A/B/C/D 全部完成。**

## 深水区 (第二批, 全部完成 · 95 passed · 已 push)
- **E 专业传统盘面**: 12宫地支4×4布局 + 中宫命主 + 三方四正点击高亮 (Playwright 视觉验证)。
- **②命盘可验证指纹**: `fingerprint.py` 确定性 SHA-256, 同生辰可复算校验, UI 展示。
- **①AI诚实顾问层**: advisor `_apply_honesty_layer` — grounding 来源 + 高风险护栏
  (健康/婚否/财务/法律→不下决定论+封顶confidence) + 局限声明; /api/ask 暴露; 前端渲染。
- **③圆形飞星连线图**: `flying.py` 宫干飞化(SSOT) → 轮图叠加化忌飞星红线;
  附带修复轮图/八字面板 pre-existing `data` 作用域 bug (Playwright 视觉验证)。

全部状态: 95 passed, 25 提交, 已 push github.com/kogamishinyajerry-ops/ziwei-doushu-engine。

## Phase A — 安星规则即数据 + /api/explain (基础, 最先)
- `ziwei/chart/explain.py`: 给定 ChartData, 为每颗星产出 {规则名, 公式, 推导(代入实际索引), 出处}。
- 复用已加固的安星规则注释 (寅申轴/七杀空三破军/禄前羊刃后陀罗…)。
- `/api/explain` 端点 (或 chart/full 增 explain 字段, 兼容)。
- 测试: 关键星 explain 数据正确 + 推导索引自洽。
- 价值: 透明层 + 星盘 hover 的共同地基。

## Phase B — 专业级交互星盘 (前端, 消费 A)
- 12 宫 grid (传统紫微 4x4 布局 + 中宫信息)。
- hover/click 星曜 → 展开 explain。
- 三方四正高亮 + 四化连线。
- 服务"教你看懂", 非纯炫。

## Phase C — 流派切换器 (引擎 variant, 默认=已验证行为)
- generate_chart 增 school/variant 参数 (默认 mainstream)。
- 首个 toggle: 火铃"宋版"巳酉丑异本 (Codex 已确认存在的真实变体)。
- 每选项附出处+差异说明; 默认必须 == 当前 68-green 行为。
- 诚实原则: 不臆造流派差异, 只暴露真实存在的。

## Phase D — 算法可信度公开页
- 渲染 invariant tests + Codex 异源验证 + quality_flags 含义。
- 把工程严谨变成信任营销资产 (测测不敢公开算法对错)。

## 不做 (与定位冲突 / 重运营)
- 真人占卜师 marketplace · 体系广度铺开(塔罗/西占/六爻) · 重社区运营。

## 验证基线
每阶段: `.venv/bin/python -m pytest -q` 全绿 + compileall; 原子提交; 默认排盘行为不回归。
