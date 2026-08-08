# Sales Funnel & Deal Scoring

A sales analytics project that combines **DuckDB + SQL funnel analysis**, **propensity-to-close modeling**, **stalled-deal detection**, **SHAP explainability**, and an optional **Claude API** summary inside a Streamlit dashboard.

The project is framed around a practical sales-management question:

> Where is pipeline attrition actually happening, which open deals deserve attention, and what evidence can a sales rep use to prioritize follow-up?

## Results at a glance

| Metric | Result |
|---|---:|
| CRM opportunities | 8,800 |
| Closed opportunities | 6,711 |
| Won | 4,238 |
| Lost | 2,473 |
| Closed win rate | 63.2% |
| Reached Engaging | 8,300 / 8,800 (94.3%) |
| Reached Engaging → Closed | 80.9% |
| Reached Engaging → Won | 51.1% |
| Median close cycle | 45 days |
| LightGBM 5-fold ROC-AUC | 0.554 ± 0.009 |
| Selected holdout ROC-AUC | 0.554 |
| Q4 temporal stress-test ROC-AUC | 0.527 |
| Open opportunities scored | 2,089 |
| Stalled Engaging deals flagged | 783 |

## Business finding before modeling

**Observed losses occur after engagement in the available CRM history.** The CRM contains 2,473 Lost opportunities and every closed loss has an `engage_date`. Among closed opportunities, 36.8% are lost. Because the source does not contain a complete opportunity-event history, funnel analysis is limited to the stages represented in the dataset.

The SQL analysis highlights the unresolved Engaging backlog and post-engagement loss rate before predictive modeling is applied.

## Key findings

**Funnel:** 8,300 of 8,800 opportunities reached Engaging or a terminal outcome, a 94.3% observed progression rate. Of those, 6,711 had closed by the snapshot and 4,238 were Won. The 63.2% win rate applies to closed opportunities, while the 51.1% Engaging-to-Won rate uses all opportunities known to have reached Engaging in the denominator.

**Cycle time:** Closed opportunities have a 45-day median cycle and an 85-day P75. Won opportunities take longer in this dataset — a 57-day median versus 14 days for Lost opportunities — so long duration by itself is not treated as evidence of likely loss. The stalled-deal rule instead asks whether an *open* Engaging deal is far beyond the historical duration norm for its product and region.

**Stalled pipeline:** The transparent rule `days in Engaging >= 2 × product/region historical P75 close cycle` flags 783 current Engaging opportunities. This is intentionally interpretable: a sales manager can audit why a deal was flagged without needing an anomaly model.

**Propensity model:** LightGBM beats the logistic baseline in 5-fold ROC-AUC (0.554 vs. 0.505). The model is useful mainly as a ranking layer rather than a highly accurate forecast. A Q4 temporal stress test drops to 0.527 ROC-AUC, which is reported to make the model limitation visible instead of hiding temporal drift.

**Explainability:** The risk table combines close propensity with stall severity and surfaces SHAP contributions for high-risk deals. SHAP is used to explain model behavior, not to claim that a feature caused a deal to win or lose.

## Dataset

Public **CRM Sales Opportunities** data for a fictitious B2B computer-hardware company.

Kaggle source: `https://www.kaggle.com/datasets/innocentmfa/crm-sales-opportunities`

Maven Analytics source: `https://mavenanalytics.io/data-playground/crm-sales-opportunities`

The repository includes the four small source CSVs for reproducibility. A GitHub mirror is used by `scripts/download_data.py` so cloning the project does not require Kaggle authentication.

### Source limitation that matters

The pipeline table has only:

`Prospecting → Engaging → Won / Lost`

It does **not** contain lead source or a complete sequence of qualification/proposal/negotiation timestamps. For that reason:

- win-rate analysis uses account sector, product, region, and sales representative.
- stage-to-stage metrics are limited to transitions supported by the observed states.
- stalled-deal logic uses time since `engage_date`, the only available live-stage timestamp.

## Architecture

```text
CSV source data
     │
     ▼
DuckDB raw tables
     │
     ├── SQL funnel conversion
     ├── SQL win-rate breakdowns
     ├── SQL cycle-time distribution
     ├── SQL attrition diagnostic
     └── SQL stalled-deal benchmark
     │
     ▼
Python feature layer
     │
     ├── Logistic regression baseline
     ├── LightGBM comparison
     ├── SHAP explanations
     └── Open-deal scoring
     │
     ▼
Streamlit dashboard
     ├── Funnel visualization
     ├── Risk-ranked open deals
     ├── Stalled-deal filters
     ├── Model benchmark
     ├── SHAP per deal
     └── Optional Claude one-sentence summary
```

## Repository structure

```text
sales-funnel-deal-scoring/
├── artifacts/                 # model metrics, scores, SHAP output, trained model
├── dashboard/app.py           # Streamlit app
├── data/raw/                  # public source CSVs
├── docs/
│   ├── deployment.md
│   ├── methodology.md
├── scripts/
│   ├── build_warehouse.py
│   ├── download_data.py
│   ├── run_analysis.py
│   ├── train_models.py
│   └── verify_project.py
├── sql/
│   ├── 01_mart_opportunities.sql
│   ├── 02_funnel_conversion.sql
│   ├── 03_win_rate_breakdowns.sql
│   ├── 04_sales_cycle.sql
│   ├── 05_attrition.sql
│   └── 06_stalled_deals.sql
├── src/sales_funnel/
├── tests/
├── Makefile
└── requirements.txt
```

## Quick start

Python 3.12 is recommended.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
make demo
make app
```

`make demo` builds the DuckDB warehouse, trains/evaluates the models, generates open-deal scores and SHAP artifacts, runs the analytical summary, and verifies key counts.

## SQL analyses

The SQL layer answers the business questions before model training:

```sql
-- Where do observed losses occur?
SELECT * FROM attrition_diagnostics;

-- Stage progression / conversion
SELECT * FROM funnel_conversion ORDER BY stage_order;

-- Rep performance
SELECT * FROM win_rate_by_rep ORDER BY win_rate DESC;

-- Segment performance
SELECT * FROM win_rate_by_segment ORDER BY win_rate DESC;

-- Cycle time
SELECT * FROM sales_cycle_summary;

-- Stalled deals
SELECT * FROM stalled_deals WHERE stalled ORDER BY stall_ratio DESC;
```

## Modeling design

### Leakage policy

The model excludes fields that are unavailable before outcome:

- `close_date`
- `close_value`
- final `deal_stage`
- `cycle_days`
- Won/Lost label derivatives

Available predictors include sales rep/team, product, account firmographics, list price, and engagement calendar features.

### Benchmark

| Model | 5-fold ROC-AUC |
|---|---:|
| Logistic regression | 0.505 ± 0.009 |
| LightGBM | **0.554 ± 0.009** |

The selected LightGBM model scores 0.554 ROC-AUC on the fixed stratified holdout and 0.527 on a later Q4 temporal stress test.

Outcome-derived fields are excluded from model training to prevent target leakage.

## Stalled-deal detection

For each product × regional-office segment:

```text
historical norm = P75(close_date - engage_date) among closed deals
stall ratio     = current days in Engaging / historical norm
flag stalled    = stall ratio >= 2.0
```

Result: **783 Engaging deals flagged**.

## Claude integration

The dashboard works without any external API. Set these variables to enable Claude-generated one-sentence summaries:

```bash
export ANTHROPIC_API_KEY="..."
export ANTHROPIC_MODEL="claude-haiku-4-5"
streamlit run dashboard/app.py
```

The fallback summary remains deterministic so the dashboard can run without paid API credentials.

## Tests and validation

```bash
pytest -q
python scripts/verify_project.py
```

The verification script checks:

- 8,800 unique opportunities.
- source stage domain.
- 4,238 Won and 2,473 Lost records.
- model-selection result.
- no outcome fields in the feature list.
- all 2,089 open opportunities receive scores.
- stalled-deal detection returns a non-empty priority set.


## Deployment

See [`docs/deployment.md`](docs/deployment.md). Streamlit Community Cloud needs your GitHub/Streamlit account authorization, so deployment is the one step that cannot be completed from an offline project build.

## Reproducibility note

All reported metrics are generated from the included source files and project pipeline. The dataset describes a fictitious company, so results should be interpreted in that context rather than as real production sales performance.
