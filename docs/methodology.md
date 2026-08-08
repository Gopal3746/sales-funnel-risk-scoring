# Methodology

## 1. Dataset and analytical boundary

The project uses the public CRM Sales Opportunities dataset associated with Maven Analytics and mirrored on Kaggle. It contains 8,800 opportunity snapshots plus account, product, and sales-team dimensions.

The critical limitation is structural: the opportunity table contains only four observed states — Prospecting, Engaging, Won, and Lost — and only stores the date the Engaging state began plus the final close date. There is no event log for qualification, proposal, negotiation, or other intermediate stages.

The project therefore does not manufacture a richer funnel than the source supports.

## 2. Funnel reconstruction

The funnel uses only states implied by the source:

1. All opportunities: 8,800.
2. Reached Engaging or a terminal state: 8,300. This is every row not still in Prospecting.
3. Closed: 6,711 Won or Lost opportunities.
4. Won: 4,238 opportunities.

This produces:

- Prospecting → reached Engaging: 94.3%.
- Reached Engaging → Closed: 80.9% as of the dataset snapshot.
- Reached Engaging → Won: 51.1%.
- Closed → Won: 63.2%.

Every recorded Lost opportunity has an engage date. The available data therefore places observed losses after engagement, but it does not contain enough event history to locate losses within more granular intermediate stages.

## 3. Sales-cycle analysis

For closed opportunities, cycle length is `close_date - engage_date`.

- Median: 45 days.
- Mean: 48.0 days.
- P75: 85 days.
- P90: 104 days.
- P95: 114.5 days.

Won deals have a 57-day median cycle, while Lost deals have a 14-day median. This is descriptive, not causal.

## 4. Propensity-to-close model

Training data contains only historically closed opportunities. The target is Won = 1, Lost = 0.

Predictors are restricted to fields observable by the Engaging stage: rep, manager, region, product, product series/list price, account sector/location/revenue/employees/age, and engagement calendar features.

Leakage fields are explicitly excluded: `close_date`, `close_value`, final `deal_stage`, `cycle_days`, and outcome labels.

Two models are compared:

- Logistic regression baseline.
- LightGBM gradient-boosted trees.

Five-fold stratified cross-validation:

- Logistic regression ROC-AUC: 0.505 ± 0.009.
- LightGBM ROC-AUC: 0.554 ± 0.009.

Selected LightGBM holdout ROC-AUC: 0.554. A Q4 temporal stress test scores 0.527 ROC-AUC. The modest discrimination is reported intentionally because this public dataset contains limited pre-close signal.

## 5. Stalled-deal rule

For each product × regional-office segment, the project computes the historical P75 close-cycle duration among closed deals. An open Engaging opportunity is flagged when:

`days_in_engaging >= 2.0 × segment_P75_cycle_days`

This flags 783 Engaging opportunities in the dataset snapshot. The rule is easy to explain to a sales manager and avoids pretending that anomaly detection is necessary when a transparent threshold is sufficient.

## 6. Explainability

For the selected LightGBM model, SHAP TreeExplainer is run on transformed features. The artifact stores the top three absolute SHAP contributions for the 100 highest-risk open opportunities.

SHAP values explain why the model score moved relative to its baseline; they do not establish causation.

## 7. Deal-risk summaries

The dashboard always has a deterministic one-sentence summary. If `ANTHROPIC_API_KEY` is configured, the user can regenerate the sentence with Claude Haiku. The prompt sends only the selected deal facts used in the dashboard and requests one concise, action-oriented sentence.
