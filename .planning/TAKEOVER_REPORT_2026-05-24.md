# ziwei-doushu 接手报告

生成时间: 2026-05-24
模式: 多 agent 只读接手 + 本地验证

## 接手结论

这是一个单体 Python/FastAPI 紫微斗数排盘 MVP。后端集中在 `ziwei/api/server.py`，核心排盘入口是 `ziwei/chart/engine.py::generate_chart`，前端是静态 HTML。当前默认入口 `/` 优先返回 `desktop/index.html`，旧版 `frontend/index.html` 作为 fallback。

项目不是空架子，已经具备可演示链路:

- 命盘排盘: `/api/chart/full`
- 八字分析: `/api/bazi`
- 合盘合婚: `/api/hepan`
- 智能问答: `/api/ask`
- 流年/阅读/城市辅助接口: `/api/liunian`, `/api/reading`, `/api/cities`

当前最需要先接住的是运行契约、测试覆盖、算法可信度标记和已有未提交改动边界，而不是继续扩新功能。

## 执行更新

2026-05-24 后续已完成:

- Slice 1: `start.sh` 改为使用 `requirements.txt` 补齐依赖；Phase1/Phase2 测试路径改为可移植；pytest return-value warnings 已消除。
- Slice 2: 新增 `tests/test_api_smoke.py`，覆盖 `/api/health`, `/api/chart/full`, `/api/bazi`, `/api/hepan`, `/api/ask` 和无效输入。
- Slice 3: 新增 `tests/test_chart_engine.py`，用 TDD 修复 `chart.shen_palace` 身宫天干错误。
- Slice 4: 统一 app/health 版本、`start.sh`/`server.py` 默认端口、本地 CORS 预检、桌面版和旧前端错误响应解析。
- Slice 5: 新增 `tests/test_calendar_goldens.py` 与 `tests/test_limits.py`，锁定春节农历转换、立春年柱边界、23:00 子时、真太阳时跨时辰、大限结构和命盘映射一致性。
- Slice 6: 新增 `README.md` 与 `.env.example`，补齐安装、启动、测试、API、环境变量、LLM 回退和算法可信度边界。
- Slice 7: 新增 `quality_flags` 兼容字段，暴露真太阳时、农历、`/api/reading` LLM/local reading 回退状态。
- Slice 8: 收口 LLM provider 契约，`requests` 纳入依赖，auto provider 顺序改为 Minimax -> DeepSeek -> OpenAI，并为 `/api/reading` 增加兼容 `provider` 查询参数。
- 当前验证结果: `.venv/bin/python -m pytest -q` 为 `37 passed`；`.venv/bin/python -m compileall -q ziwei` 通过。

## 当前工作树状态

接手时工作树已有未提交/未跟踪内容，未做回滚:

- Modified: `ziwei/api/server.py`
- Modified: `ziwei/analysis/__init__.py`
- Untracked: `desktop/`
- Untracked: `ziwei/analysis/advisor.py`
- Untracked: `ziwei/analysis/bazi.py`
- Untracked: `ziwei/analysis/hepan.py`

这些文件正好覆盖桌面版、合盘、八字、问答等新增功能面。后续施工必须先确认这些内容属于当前主线，不能当作可丢弃临时文件。

## 核心数据流

用户表单 -> `/api/chart/full` 等 API -> `generate_chart` -> 真太阳时校正 -> 四柱 -> 农历 -> 十二宫 -> 安星 -> 四化/大限 -> `chart_to_dict(..., include_analysis=True)` -> 深度分析/人格/稀有度/姓名学/合盘/八字等扩展 -> JSON -> 前端渲染。

关键模块:

- `ziwei/calendar/*`: 节气、干支、农历、真太阳时。
- `ziwei/chart/*`: 十二宫、星曜、四化、大限、小限、总引擎。
- `ziwei/analysis/*`: 基础分析、深度分析、流年、合盘、八字、问答、LLM prompt 包装。
- `ziwei/api/server.py`: API 和页面入口。
- `desktop/index.html`: 当前主展示入口。
- `frontend/index.html`: 旧版/移动式兜底入口。

## 已验证事实

本地已执行:

- `.venv/bin/python -m pytest -q`
  - 结果: `42 passed`。
- `.venv/bin/python -m compileall -q ziwei`
  - 结果: 通过。
- `tests/test_api_smoke.py`
  - 覆盖 `/api/health`, CORS 预检, `/api/chart/full`, `/api/bazi`, `/api/hepan`, `/api/ask`, 无效输入。
- `tests/test_calendar_goldens.py`
  - 覆盖 2024 春节农历锚点、2024 立春前后年柱、23:00 子时日柱、乌鲁木齐真太阳时跨时辰、未知城市不校正。
- `tests/test_limits.py`
  - 覆盖大限 12 段结构、年龄连续性、命盘大限映射和宫位字段一致性。
- `tests/test_chart_engine.py` / `tests/test_api_smoke.py`
  - 覆盖 `quality_flags.solar_time` 未知城市、`quality_flags.lunar` 回退、`quality_flags.llm` 本地解读回退。
- `tests/test_llm_provider.py` / `tests/test_api_smoke.py`
  - 覆盖 `requests` 运行依赖声明、auto provider 顺序、OpenAI key 不误路由、`/api/reading` fake LLM provider 路由。
- `tests/test_frontend_quality_flags.py`
  - 覆盖 `desktop/index.html` 和 `frontend/index.html` 的 `quality_flags` 静态渲染契约与缺失字段守卫。
- `tests/test_api_smoke.py`
  - 覆盖 `/api/ask` 的 `source` / `quality_flags.analysis`，以及 `/api/reading` 的 `source` / `reading.source_detail`。

这些验证能锁住当前可演示行为和关键边界，但仍不等价于命理算法权威验证。

## P0 风险

1. 命理算法可信度仍是“样例锁定”，不是权威背书。
   - 已补春节、立春、23:00 子时、真太阳时和大限边界测试。
   - 仍未覆盖所有流派差异、秒级节气精度或全部地域出生地。

2. 部分分析降级仍未统一质量标记。
   - 真太阳时、农历和 LLM/local reading 已有 `quality_flags`。
   - 深度分析、姓名/原型/人格分析等局部 `except Exception` 路径仍可能静默跳过。

3. `/api/reading` 的产品入口已暂时延后。
   - `reading_frontend_strategy=defer_frontend_connection`。
   - 前端已经能展示已有 `quality_flags`，但仍不主动调用 `/api/reading`。
   - LLM 解读是独立 API 能力，不应被误认为主排盘页已经调用。

## 已缓解风险

1. 启动依赖契约已闭环。
   - `start.sh` 现在用 `requirements.txt` 创建/补齐 `.venv`。
   - `lunar.py` 所需 `ephem` 会通过 `requirements.txt` 安装。

2. 身宫干支字段曾存在已复现 bug，现已修复。
   - 原问题: `ziwei/chart/engine.py` 用命宫天干拼身宫地支生成 `chart.shen_palace`。
   - 已新增 `tests/test_chart_engine.py` 覆盖两个身宫不在命宫样例和一个身宫在命宫边界样例。
   - 当前实现按 `layout.shen_index` 反查身宫名，再取该宫天干拼地支。

3. API/前端错误契约已收口。
   - 前端 fetch 现在检查 `resp.ok` 并读取 `detail` / `error`。
   - app version 与 `/api/health` version 已统一为 `0.8.0`。

4. 测试覆盖已补第一层。
   - 新增 API smoke、命盘身宫、大限和历法金标准测试。

5. 关键回退路径已有第一层可观测性。
   - 命盘 JSON 暴露 `quality_flags.solar_time` 和 `quality_flags.lunar`。
   - `/api/reading` 顶层暴露 `quality_flags.llm`。

6. LLM provider 契约已收口。
   - `requests` 已列入 `requirements.txt`。
   - auto provider 顺序为 Minimax -> DeepSeek -> OpenAI。
   - `/api/reading` 支持兼容可选 `provider` 参数。

7. 前端已开始显式展示质量标记。
   - `desktop/index.html` 在排盘结果展示命盘质量提示，问答上下文可复用 `chart.quality_flags` 或顶层 `quality_flags`。
   - `frontend/index.html` 在旧版结果首屏展示 `cd.quality_flags`。
   - 新增 `tests/test_frontend_quality_flags.py` 锁住缺失字段守卫和静态渲染契约。

8. 解读来源契约已收口第一层。
   - `/api/ask` 顶层 `source` 区分 `advisor_rules` 与 `local_fallback`。
   - `/api/ask` 暴露 `quality_flags.analysis`，并合并命盘自身质量标记。
   - `/api/reading` 顶层 `source` 区分 `llm` 与 `local`，`reading.source_detail` 区分 provider 或 `local_rules`。

## P1 风险

- `/api/liunian` 默认 `target_year=2026`，后续会随时间漂移。
- `README.md` 和 `.env.example` 已存在，但 `.env` 当前不会自动加载。
- CORS 默认只覆盖本地开发 origin；生产域名/部署拓扑仍未决策。
- `desktop/` 与多个 `ziwei/analysis/*` 文件仍是接手时已有未跟踪/脏改动，不能当作临时文件清理。

## 当前 /goal

```text
/goal 深度接手 /Users/Zhuanz/ziwei-doushu，完成架构、运行健康、API/前端、命理算法可信度和产品路线的多 agent 审计，并产出 repo-local 接手文档与下一步施工切片。

Scope:
  - 只读审计并新增 `.planning/TAKEOVER_REPORT_2026-05-24.md` 与 `.planning/NEXT_SPARK_SLICES_2026-05-24.md`。
  - 不改 `ziwei/`、`tests/`、`desktop/`、`frontend/`、`start.sh` 的业务行为。

Constraints:
  - 遵守用户提供的 AGENTS.md: 小步、可逆、先验收、不得 drive-by refactor。
  - 当前工作树已有未提交改动，不能回滚或覆盖。
  - Codex 负责总控，Codex 5.3 Spark 可作为并行只读/小切片施工 agent。

Done when:
  1. `.venv/bin/python -m pytest -q` 已执行并记录结果。
  2. `.venv/bin/python -m compileall -q ziwei` 已执行并记录结果。
  3. 核心 API smoke 结果已记录。
  4. 明确列出 P0/P1 风险和可复现证据。
  5. 下一步 Spark 施工切片具备文件范围、约束、验收命令和停止条件。

Stop if:
  - 发现需要改业务代码才能继续完成接手文档。
  - 发现未提交用户改动与接手文档新增文件发生同路径冲突。
  - `.venv` 不存在且无法用现有依赖运行任何验证命令。
```

## 建议接手顺序

1. 已完成: 启动依赖闭环 + 测试路径可移植。
2. 已完成: API smoke tests，锁住当前可展示路径。
3. 已完成: TDD 修复 `shen_palace` 干支 bug。
4. 已完成: 统一 API/前端错误契约、端口和版本信号。
5. 已完成: 做历法/大限的金标准样例测试。
6. 已完成: 补 README、`.env.example` 和交接入口文档。
7. 已完成: 为真太阳时、农历、LLM/local reading 等回退路径增加质量标记。
8. 已完成: 收口 LLM 依赖与 provider 契约，避免 key 配置后无感误路由或本地回退。
9. 已完成: 在前端展示 `quality_flags`，让用户看见未知城市、农历回退或 LLM 本地回退提示。
10. 已完成: 明确 `/api/reading` 暂不成为前端可见入口，并补齐 `/api/ask` / `/api/reading` 第一层来源质量标记。
11. 下一步: 为深度分析、基础分析和流年中的简化/占位路径补齐范围标记。
