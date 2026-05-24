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

## 深水区 (第三批, 全部完成 · 120 passed · 已 push)
- **③飞星图四类线切换**: 轮图 .fly-toggle 切换 化禄(绿)/化权(黄)/化科(蓝)/化忌(红)/全部/隐藏;
  drawWheelChart 按 window._flyingType 过滤+按类型着色; 默认化忌(无回归)。
- **①AI 顾问接真实 LLM**: advisor.advise() 编排 — 规则引擎确定性初判 + 真实 LLM 润色,
  HONEST_ADVISOR_SYSTEM 强制 6 条诚实铁律(不编造盘面没有的星/引用依据/标不确定/高风险不下定论);
  命盘事实作"唯一可用依据"注入; LLM 成功替换 answer 但保留全部诚实层 metadata + local_answer 对照;
  无 key/网络失败/use_llm=False/needs_chart → 回退本地(离线可用)。/api/ask 增 use_llm/provider;
  前端 LLM 开关 + 来源徽标(🤖真实AI润色/📐规则引擎)。真实 DeepSeek 端到端验证通过。
- **②指纹可分享二维码/校验页**: verify.py 复算比对 + segno 纯 Python 零依赖 SVG 二维码(离线);
  /api/verify + /api/fingerprint/qr; 指纹可点击 → 分享弹层(QR+校验链接+复制+SHA256);
  ?verify=1 扫码进入 → 自动独立复算 → ✅一致/⚠️不一致横幅。任何人可自验, 翻转"结果你只能信"。

全部状态: 120 passed, 28 提交, 已 push。新增依赖 segno (纯 Python QR)。

## 专属深度报告 (个性化 + 专属感 · 犀利专业直言型 · 134 passed · 已 push)
用户诉求: "个性化专业分析、有独特个性、让用户觉得专属"。做法 = 巴纳姆反面: 不做通用套话,
把这张盘**独有的结构特征**拎出来具体锚定。
- **signature.py**: extract_signature() 确定性抽取命主组合/最强弱宫(吉煞庙旺打分)/
  化忌落宫(最大隐性成本)/化禄(天赋红利)/优势引擎/能量漏洞/大限红利窗口/稀缺度/开篇 top3 专属锚点。
- generate_personal_report(): SIGNATURE_REPORT_SYSTEM 犀利专业直言 + 诚实铁律
  (引用具体星宫四化大限/非确定性/高风险不下定论/给方向不给宿命); 无 key 回退本地犀利拼装(离线)。
- /api/report 端点; 前端排盘后自动加载「专属命盘深度解读」卡(3 锚点卡 + markdown 长文 + 来源徽标 + 重新生成)。
- 真实 DeepSeek 端到端验证质量高(犀利、具体、专属、诚实)。31 提交全 push。

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
