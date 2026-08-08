CREATE OR REPLACE TABLE stalled_deals AS
WITH norms AS (
    SELECT
        product,
        regional_office,
        quantile_cont(cycle_days, 0.75) AS historical_stage_norm_days
    FROM mart_opportunities
    WHERE is_closed = 1 AND cycle_days IS NOT NULL
    GROUP BY ALL
),
scored AS (
    SELECT
        o.opportunity_id,
        o.sales_agent,
        o.manager,
        o.regional_office,
        o.product,
        o.account,
        o.engage_date,
        o.days_in_stage,
        n.historical_stage_norm_days,
        o.days_in_stage * 1.0 / NULLIF(n.historical_stage_norm_days, 0) AS stall_ratio
    FROM mart_opportunities o
    LEFT JOIN norms n USING (product, regional_office)
    WHERE o.deal_stage = 'Engaging'
)
SELECT
    *,
    stall_ratio >= 2.0 AS stalled
FROM scored
ORDER BY stall_ratio DESC;
