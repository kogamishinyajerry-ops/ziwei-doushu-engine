# Ziwei Doushu MVP

Local FastAPI MVP for Zi Wei Dou Shu chart generation, calendar/ganzhi calculation,
relationship matching, bazi analysis, and local/optional LLM-assisted readings.

This repository is currently best treated as a local demo and engineering
workbench. It has smoke tests and focused calendar/limit golden tests, but it is
not a production service or an authoritative astrology engine.

## Current Entry Points

- Web UI: `http://localhost:8088/`
- API app: `ziwei.api.server:app`
- Main chart engine: `ziwei/chart/engine.py`
- Current takeover notes: `.planning/TAKEOVER_REPORT_2026-05-24.md`
- Current slice plan: `.planning/NEXT_SPARK_SLICES_2026-05-24.md`

The `/` route serves `desktop/index.html` when present. If that file is absent,
it falls back to `frontend/index.html`.

## Install And Run

Recommended local path:

```bash
cd /Users/Zhuanz/ziwei-doushu
./start.sh
```

`start.sh` creates `.venv` when needed, installs `requirements.txt`, and starts
Uvicorn on port `8088`.

Runtime dependencies in `requirements.txt` are `numpy`, `ephem`, `fastapi`,
`uvicorn`, `pydantic`, `jinja2`, and `requests`. The LLM HTTP path uses
`requests`; provider failures still fall back to local reading content.

To use a different port:

```bash
PORT=8090 ./start.sh
```

Manual equivalent:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn ziwei.api.server:app --host 0.0.0.0 --port 8088
```

## Verify First

Run these before handing work to another agent:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m compileall -q ziwei
```

Current verified result (after the 2026-05-24 deep-takeover optimization):

- `.venv/bin/python -m pytest -q` -> `78 passed`
- `.venv/bin/python -m compileall -q ziwei` -> passed

## Main API Routes

| Route | Method | Purpose |
| --- | --- | --- |
| `/api/health` | GET | Health and app version |
| `/api/chart` | GET/POST | Basic chart payload |
| `/api/chart/text` | GET | Text chart rendering |
| `/api/chart/full` | GET | Chart plus analysis payload |
| `/api/cities` | GET | City longitude lookup for true solar time |
| `/api/reading` | GET | LLM-assisted reading, with local fallback and optional `provider=auto|minimax|deepseek|openai` |
| `/api/liunian` | GET | Ziwei yearly transit analysis |
| `/api/hepan` | GET/POST | Two-person compatibility analysis |
| `/api/bazi` | GET | Bazi and bazi yearly transit analysis |
| `/api/ask` | GET/POST | Local intelligent Q&A, optionally with chart data |

Example:

```bash
curl 'http://localhost:8088/api/chart/full?year=1998&month=3&day=21&hour=8&minute=30&name=星辰&gender=男&city=北京'
```

## Quality Flags

Chart JSON responses include a compatible `quality_flags` object. Existing
fields are unchanged.

Current chart flags:

- `quality_flags.solar_time`: `not_requested`, `checked`, `corrected`,
  `unknown_city`, or `failed`; `fallback` is `true` when the requested city could
  not be matched or correction failed.
- `quality_flags.lunar`: `ok` or `fallback`; `fallback` is `true` when lunar
  conversion falls back to a jieqi-based approximation.

`/api/reading` also returns a top-level `quality_flags.llm` flag. A no-key local
reading is reported as:

```json
{
  "status": "local_fallback",
  "fallback": true,
  "source": "local"
}
```

`/api/reading` also includes top-level `source`:

- `source: "llm"` when an LLM provider returned content.
- `source: "local"` when the endpoint returned local generated content.

The nested `reading.source_detail` field records the provider name or
`local_rules`.

`/api/ask` is rule-based. Its response includes top-level `source` and
`quality_flags.analysis`:

- `source: "advisor_rules"` for rule-based answers.
- `source: "local_fallback"` when the question needs chart data but none was
  provided.
- `quality_flags.analysis.status`: `rule_based` or `local_fallback`.

The static front-ends render these flags defensively. Missing or newly added
flag groups are ignored by the UI instead of failing the chart render path.

### Reading Front-End Strategy

`reading_frontend_strategy: defer_frontend_connection`

`/api/reading` is currently an API capability, not a front-end entry point. The
static front-ends intentionally do not call `/api/reading`; they only render
quality flags that are present in the responses they already fetch. This keeps
rule-based Q&A, local generated reading, and LLM-assisted reading separated
until the product entry point and wording are explicitly decided.

## Environment Variables

See `.env.example` for the available variables.

Important: the app does not currently auto-load `.env`. Export variables in the
shell, pass them before `./start.sh`, or use a dotenv runner.

```bash
export ZIWEI_CORS_ORIGINS=http://localhost:8088,http://127.0.0.1:8088
export MINIMAX_API_KEY=...
./start.sh
```

Runtime variables used by the current code:

- `PORT`: server port for `start.sh` and direct `python -m ziwei.api.server`.
- `ZIWEI_CORS_ORIGINS`: comma-separated allowed origins. Defaults to local
  development origins on `8088`, `8080`, and `3000`.
- `MINIMAX_API_KEY`, `MINIMAX_BASE_URL`, `MINIMAX_MODEL`: preferred LLM path.
- `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`, `DEEPSEEK_MODEL`: fallback LLM path
  for the current auto-detection branch.
- `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL`: supported by the lower
  level helper when OpenAI provider is selected.

If no usable LLM key is configured, `/api/reading` returns a local generated
reading. If a provider call fails, the helper also falls back to local content.

Current auto-detection order is `MINIMAX_API_KEY`, then `DEEPSEEK_API_KEY`, then
`OPENAI_API_KEY`. `/api/reading` also accepts a compatible optional `provider`
query parameter. Example:

```bash
curl 'http://localhost:8088/api/reading?year=1998&month=3&day=21&hour=8&minute=30&provider=openai'
```

## Algorithm Confidence And Known Limits

- Core main-star placement is now guarded by structural invariant tests
  (`tests/test_chart_invariants.py`). These lock canonical, school-independent
  rules: 紫微/天府 寅申-axis symmetry, 破军⇄天相 and 七杀⇄天府 opposition,
  the 紫微-series / 天府-series within-series offsets, 12-palace bijection,
  exactly four canonical 四化, and 擎羊/陀罗/左辅/右弼/文昌/文曲 placement.
  The 2026-05-24 optimization fixed three P0 main-star placement bugs found
  this way: 天府-series on the wrong (卯酉) reflection axis, 廉贞 at `紫微-7`
  (should be `-8`), and 破军 at `天府+7` (should be `+10`, "七杀空三破军").
  These misplaced 8+ main stars on every chart before the fix.
- Auxiliary-star tables (`tests/test_aux_star_goldens.py`) are golden-locked
  and were independently cross-checked (Codex web research). This caught a
  地劫/地空 顺逆 swap (now 地劫 advances, 地空 retreats from 亥) and aligned
  丁-year 天魁/天钺 to the mainstream table. 禄存, 天马, and 火星/铃星
  (mainstream 中州派/全书 table, all groups 顺行) were verified already-correct.
- These tests verify *structural / tabular* correctness, not interpretive
  depth. Interpretation text, school-specific 流派 variants (e.g. the minority
  宋版 火铃 巳酉丑 variant), and second-level solar-term precision remain
  sample/rule-locked, not authoritatively benchmarked.
- Public API input validation is mostly scoped to years `1900..2100`, valid
  month/day ranges, and valid hour/minute ranges. Do not document broader date
  support without new tests.
- Calendar and limit behavior is covered by focused tests for 2024 Chinese New
  Year, the 2024 lichun year-pillar boundary, 23:00 zi-hour day rollover, true
  solar time hour crossing, daxian continuity, and chart daxian mapping. These
  tests are reproducible, but they do not claim second-level solar-term
  precision or settle all school differences.
- Some paths intentionally degrade or approximate: unknown cities use no true
  solar-time correction, lunar conversion has fallback behavior, and LLM
  readings fall back to local deterministic text when configuration, dependency,
  or provider calls are unavailable.
- API smoke tests prove routes return structured responses. They do not prove
  full astrology correctness.
- Use this project for local demonstration and engineering validation. It should
  not be used as the sole basis for investment, marriage, health, legal, or
  other high-stakes decisions.
- `/api/liunian` defaults `target_year` to the current calendar year
  (`datetime.now().year`); pass it explicitly for reproducible results.
- `desktop/` and several `ziwei/analysis/*` files were already untracked or
  dirty during takeover. Do not delete or reset them as cleanup.
- The UI and API are designed for local use. Production deployment still needs a
  separate decision on domain, CORS policy, secrets loading, process management,
  and observability.

Risk matrix for future work:

| Confidence source | Failure mode | Impact | Next signal to add |
| --- | --- | --- | --- |
| Calendar and ganzhi rules | Solar-term precision or school variance | Four pillars and boundary dates | Broader golden cases |
| Built-in city database | Unknown city or approximate match | True solar time and hour branch | Already exposed by `quality_flags.solar_time` |
| Local analysis rules | Simplified or fallback interpretation | Reading depth and wording | `quality_flags.analysis` |
| Optional LLM provider | Missing key or provider call failure | `/api/reading` content source | Local fallback exposed by `quality_flags.llm`; provider route covered by tests |

## Recommended Next Slice

Next bounded work should add deeper analysis-level flags for the remaining
silent analysis submodules, or expand `/api/reading` into an explicit product
entry point if LLM-assisted reading is meant to be user-facing.
