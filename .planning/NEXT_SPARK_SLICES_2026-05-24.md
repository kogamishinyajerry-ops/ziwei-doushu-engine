# Codex 5.3 Spark 施工切片

这些切片按小步、可逆、可验收设计。每个切片都可交给 `gpt-5.3-codex-spark` 单独执行；不要并行执行会改同一文件的切片。

当前状态:

- Done: Slice 1 启动依赖与测试可移植
- Done: Slice 2 API smoke tests
- Done: Slice 3 修复身宫干支 bug
- Done: Slice 4 API/前端错误契约与启动端口
- Done: Slice 5 算法可信度金标准测试
- Done: Slice 6 README 与交接入口
- Done: Slice 7 降级路径质量标记
- Done: Slice 8 LLM 依赖与 provider 契约
- Next: Slice 9 前端质量标记提示

## Slice 1: 启动依赖与测试可移植

Objective:
修复本地启动和测试环境契约，使新环境不会因为 `ephem`/依赖缺失或机器绝对路径导致失败。

Scope:
- `start.sh`
- `tests/test_phase1.py`
- `tests/test_phase2.py`
- 必要时只读查看 `requirements.txt`

Constraints:
- 不改业务算法。
- 不改 API 响应字段。
- 不删除现有测试断言。

Done when:
1. `start.sh` 使用 `requirements.txt` 安装/校验依赖，已有 `.venv` 缺包时也能补齐。
2. `tests/test_phase1.py` 和 `tests/test_phase2.py` 不再依赖 `/Users/Zhuanz/ziwei-doushu` 绝对路径。
3. `.venv/bin/python -m pytest -q tests/test_phase1.py tests/test_phase2.py` exits 0。
4. 3 个 `PytestReturnNotNoneWarning` 已消除，或明确保留原因并有注释。

Stop if:
- 需要新增依赖但 `requirements.txt` 没有对应包且无法解释用途。
- 需要改 `ziwei/` 业务代码才能让测试通过。

## Slice 2: API smoke tests

Objective:
新增最小 API 冒烟测试，锁住当前可展示路径。

Scope:
- 新增 `tests/test_api_smoke.py`
- 只读查看 `ziwei/api/server.py`

Constraints:
- 不改后端实现。
- 不依赖真实网络或外部模型 Key。

Done when:
1. `tests/test_api_smoke.py` 覆盖 `/api/health`, `/api/chart/full`, `/api/bazi`, `/api/hepan`, `/api/ask`。
2. 每个测试断言关键字段，而不是只断言 200。
3. 至少包含一个无效输入返回 400/422 的测试。
4. `.venv/bin/python -m pytest -q tests/test_api_smoke.py` exits 0。

Stop if:
- FastAPI TestClient 不可用且无法从现有依赖解释原因。
- 某 API 必须调用真实外部 LLM 才能通过。

## Slice 3: 修复身宫干支 bug

Objective:
用测试复现并修复 `chart.shen_palace` 使用命宫天干的问题。

Scope:
- `ziwei/chart/engine.py`
- 新增或更新 `tests/test_phase2.py` 或 `tests/test_chart_engine.py`

Constraints:
- 先写失败测试，再改实现。
- 不改十二宫排布算法本身，除非测试证明根因在 `place_palaces`。
- 不改 API 字段名。

Done when:
1. 测试能证明 `chart.shen_palace` 等于实际 `is_body` 宫位的 `stem + branch`。
2. 至少覆盖 2 个身宫不在命宫的样例。
3. `.venv/bin/python -m pytest -q tests/test_phase2.py` exits 0，或新增测试文件 exits 0。
4. `.venv/bin/python -m pytest -q` exits 0。

Stop if:
- 发现不同紫微斗数流派对身宫干支字段定义有冲突，需要产品确认。

## Slice 4: API/前端错误契约与启动端口

Objective:
统一用户可见错误、端口和版本信号，降低演示失败率。

Scope:
- `ziwei/api/server.py`
- `desktop/index.html`
- `frontend/index.html`
- `start.sh`

Constraints:
- 不改排盘结果。
- 不做 UI 大改版。
- 不引入前端构建系统。

Done when:
1. 前端 fetch 都检查 `resp.ok`，错误展示读取 `detail` 或兼容 `error`。
2. `start.sh` 与 `server.py` 默认端口一致，文案一致。
3. FastAPI app version 与 `/api/health` version 一致，或有单一版本来源。
4. 如配置 CORS，只允许本地开发和明确来源，不使用无边界生产默认。
5. `.venv/bin/python -m pytest -q` exits 0。

Stop if:
- 需要决定生产域名或部署拓扑。
- 需要新增框架或打包系统。

## Slice 5: 算法可信度金标准测试

Objective:
建立最小命理/历法金标准测试层，先暴露不确定性，不急着改算法。

Scope:
- 新增 `tests/test_calendar_goldens.py`
- 新增或更新 `tests/test_limits.py`
- 必要时只读查看 `ziwei/calendar/*`, `ziwei/chart/limits.py`, `ziwei/chart/engine.py`

Constraints:
- 优先新增测试，不改算法。
- 所有样例必须写清楚来源或仓库内推导依据。
- 不把“打印可看”当成验收。

Done when:
1. Done: `tests/test_calendar_goldens.py` 覆盖春节农历转换、立春年前后年柱、23:00 子时日柱边界、真太阳时跨时辰样例。
2. Done: `tests/test_limits.py` 覆盖 `calculate_daxian` 的结构、12 个区间、年龄连续性，以及命盘大限映射一致性。
3. Done: 当前算法未触发新失败；未引入静默跳过。
4. Done: `.venv/bin/python -m pytest -q tests/test_calendar_goldens.py tests/test_limits.py` -> `9 passed`。

Stop if:
- 缺少可信样例来源，无法判断预期值。
- 发现需要先统一流派规则。

## Slice 6: README 与交接入口

Objective:
补齐新人/下一个 agent 可直接使用的项目入口文档。

Scope:
- `README.md`
- `.env.example`
- 可链接 `.planning/TAKEOVER_REPORT_2026-05-24.md`

Constraints:
- 文档如实说明本地回退、算法风险和未完成测试。
- 不夸大“专业准确”或“已生产可用”。

Done when:
1. Done: `README.md` 包含安装、启动、测试、主要 API、前端入口、环境变量、算法可信度和已知风险。
2. Done: `.env.example` 列出 LLM 相关 Key 的可选项、本地回退行为和当时的 provider 风险说明。
3. Done: README 明确推荐先执行 `.venv/bin/python -m pytest -q` 和 `.venv/bin/python -m compileall -q ziwei`。

Stop if:
- 需要确认品牌/商业定位文案。

## Slice 7: 降级路径质量标记

Objective:
让当前“看似成功”的回退路径变得可观测，先暴露质量信号，不重写算法。

Scope:
- `ziwei/chart/engine.py`
- `ziwei/api/server.py`
- 必要时新增或更新 `tests/test_api_smoke.py` / `tests/test_chart_engine.py`
- 只读查看 `ziwei/calendar/*`, `ziwei/analysis/llm_prompt.py`

Constraints:
- 不改排盘主算法。
- 不改现有 API 字段语义；如需新增字段，只新增兼容字段。
- 不引入数据库、队列、监控系统或新框架。
- 不把所有 fallback 一次性重构完；优先覆盖真太阳时、农历、LLM 三个用户最容易误判的路径。

Done when:
1. Done: 命盘和 API 响应能暴露 `quality_flags` 字段，标明真太阳时、农历、LLM/local reading 状态。
2. Done: `tests/test_chart_engine.py::test_unknown_city_emits_solar_time_quality_flag` 证明未知城市真太阳时路径有可见质量信号。
3. Done: `tests/test_chart_engine.py::test_lunar_conversion_fallback_emits_quality_flag` 证明农历回退路径有可见质量信号。
4. Done: `tests/test_api_smoke.py::test_reading_local_fallback_emits_llm_quality_flag` 证明 LLM 缺 key 本地解读有可见质量信号。
5. Done: `.venv/bin/python -m pytest -q` -> `32 passed`。

Stop if:
- 需要决定正式 API 契约版本或破坏现有前端字段。
- 发现 fallback 语义和产品文案需要用户确认。
- 质量标记需要大范围改动 `ziwei/analysis/*` 才能保持一致。

## Slice 8: LLM 依赖与 provider 契约

Objective:
收口 `/api/reading` 的 LLM 依赖与 provider 路由，避免配置了 key 却无感走错 provider 或本地回退。

Scope:
- `requirements.txt`
- `ziwei/analysis/llm_prompt.py`
- `ziwei/api/server.py`
- `tests/test_api_smoke.py` 或新增聚焦 LLM 配置测试
- `README.md` / `.env.example` 仅同步真实契约

Constraints:
- 不接入真实外部 LLM 网络调用；用 monkeypatch/fake client 验证路由。
- 不新增 provider 框架或配置系统。
- 不删除本地回退能力。
- 不暴露或写入真实 API key。

Done when:
1. Done: `requests` 已加入 `requirements.txt`，`tests/test_llm_provider.py::test_requests_is_declared_runtime_dependency` 验证依赖声明和 import。
2. Done: auto 顺序为 Minimax -> DeepSeek -> OpenAI，`OPENAI_API_KEY` 不再误路由到 DeepSeek。
3. Done: `/api/reading` 新增兼容可选 `provider=auto|minimax|deepseek|openai`，并有 fake LLM 无网络测试覆盖。
4. Done: `.venv/bin/python -m pytest -q` -> `37 passed`。

Stop if:
- 需要真实 provider 凭证或外部网络才能验证。
- 需要产品确认默认 provider 优先级。
- 需要改动公开 API 参数且没有兼容默认值。

## Slice 9: 前端质量标记提示

Objective:
让用户在页面上看到关键 `quality_flags`，避免未知城市、农历回退或 LLM 本地回退被误读为完整精确输出。

Scope:
- `desktop/index.html`
- `frontend/index.html`
- 可只读查看 `README.md`, `ziwei/api/server.py`

Constraints:
- 不改后端 API。
- 不做 UI 大改版。
- 不引入前端构建系统。
- 只展示已有 `quality_flags`，不发明新的后端状态。

Done when:
1. Done: `desktop/index.html` 新增 `renderQualityFlags(flags)`，排盘结果展示 `solar_time` / `lunar`，问答上下文可展示 `chart.quality_flags` 或顶层 `quality_flags` 中的 `llm`。
2. Done: `frontend/index.html` 在旧版结果首屏渲染 `cd.quality_flags`，并对缺失、非对象或新增字段做空值守卫。
3. Done: `tests/test_frontend_quality_flags.py` 覆盖桌面入口和旧前端的静态渲染契约。
4. Done: 前端脚本语法检查通过。
5. Done: `.venv/bin/python -m pytest -q` -> `39 passed`。
6. Done: 本地服务 `/` 返回桌面入口，未知城市 `/api/chart/full` 响应包含 `quality_flags.solar_time.status=unknown_city`。

Stop if:
- 需要决定正式 UI 文案或品牌语气。
- 需要新增前端框架、打包流程或图标库。

## Slice 10: 解读入口与分析质量标记收口

Objective:
明确 `/api/reading` 是否需要成为前端可见入口，并补齐剩余分析模块的质量/来源标记，避免用户把规则解读、LLM 解读和回退解读混为一类。

Scope:
- `ziwei/api/server.py`
- `ziwei/analysis/*`
- `desktop/index.html`
- `tests/test_api_smoke.py`
- 可更新 `README.md`

Constraints:
- 不引入新 LLM provider。
- 不改既有 `/api/chart/full` 响应字段含义。
- 不做大版式重构。
- 如果需要产品文案或入口定位决策，先停下记录选项。

Done when:
1. Done: `reading_frontend_strategy=defer_frontend_connection`，本切片暂不把 `/api/reading` 接入桌面或旧前端。
2. Done: `/api/ask` 新增兼容顶层 `source` 和 `quality_flags.analysis`，区分 `advisor_rules` 与 `local_fallback`。
3. Done: `/api/reading` 新增兼容顶层 `source`，并在 `reading.source` / `reading.source_detail` 区分 `llm`、provider 和 `local_rules`。
4. Done: `tests/test_api_smoke.py` 覆盖规则问答、本地回退和 LLM 解读来源。
5. Done: `tests/test_frontend_quality_flags.py` 覆盖前端不调用 `/api/reading` 且文档记录 `defer_frontend_connection`。
6. Done: `.venv/bin/python -m pytest -q` -> `42 passed`。

Stop if:
- 需要决定正式产品文案或收费/权限入口。
- 需要真实 LLM 凭证才能验证。
- 需要改变现有 API 的兼容默认行为。

## Slice 11: 深度分析与流年降级范围标记

Objective:
把 `deep_analyzer.py`、`analyzer.py`、`liunian.py` 中仍可能被用户误读为完整实现的简化/占位路径标成可见质量范围。

Scope:
- `ziwei/analysis/deep_analyzer.py`
- `ziwei/analysis/analyzer.py`
- `ziwei/analysis/liunian.py`
- `ziwei/api/server.py`
- 聚焦测试文件

Constraints:
- 不重写算法。
- 不改变现有数值输出含义。
- 只新增兼容质量/范围字段。

Done when:
1. 深度分析、基础分析、流年接口能标识 `full|partial|simplified` 范围。
2. 测试覆盖至少一个 partial/simplified 信号。
3. `.venv/bin/python -m pytest -q` exits 0。

Stop if:
- 需要决定具体流派算法取舍。
- 需要重写分析模型才能判断质量范围。
