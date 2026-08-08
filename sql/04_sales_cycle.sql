CREATE OR REPLACE TABLE sales_cycle_summary AS
SELECT
    deal_stage AS outcome,
    COUNT(*) AS deals,
    AVG(cycle_days) AS avg_cycle_days,
    MEDIAN(cycle_days) AS median_cycle_days,
    quantile_cont(cycle_days, 0.25) AS p25_cycle_days,
    quantile_cont(cycle_days, 0.75) AS p75_cycle_days,
    quantile_cont(cycle_days, 0.90) AS p90_cycle_days,
    quantile_cont(cycle_days, 0.95) AS p95_cycle_days
FROM mart_opportunities
WHERE is_closed = 1
GROUP BY deal_stage
ORDER BY deal_stage;

CREATE OR REPLACE TABLE sales_cycle_distribution AS
SELECT
    CASE
        WHEN cycle_days <= 30 THEN '0–30 days'
        WHEN cycle_days <= 60 THEN '31–60 days'
        WHEN cycle_days <= 90 THEN '61–90 days'
        WHEN cycle_days <= 120 THEN '91–120 days'
        ELSE '121+ days'
    END AS cycle_bucket,
    COUNT(*) AS deals,
    AVG(won) AS win_rate
FROM mart_opportunities
WHERE is_closed = 1
GROUP BY 1
ORDER BY MIN(cycle_days);
