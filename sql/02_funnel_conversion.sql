CREATE OR REPLACE TABLE funnel_conversion AS
WITH counts AS (
    SELECT
        COUNT(*) AS total_opportunities,
        COUNT(*) FILTER (WHERE deal_stage <> 'Prospecting') AS reached_engaging,
        COUNT(*) FILTER (WHERE deal_stage IN ('Won', 'Lost')) AS closed_opportunities,
        COUNT(*) FILTER (WHERE deal_stage = 'Won') AS won_opportunities,
        COUNT(*) FILTER (WHERE deal_stage = 'Lost') AS lost_opportunities,
        COUNT(*) FILTER (WHERE deal_stage = 'Engaging') AS active_engaging,
        COUNT(*) FILTER (WHERE deal_stage = 'Prospecting') AS active_prospecting
    FROM mart_opportunities
)
SELECT 1 AS stage_order, 'Prospecting → Engaging/reached' AS transition,
       total_opportunities AS denominator,
       reached_engaging AS numerator,
       reached_engaging * 1.0 / total_opportunities AS conversion_rate
FROM counts
UNION ALL
SELECT 2, 'Engaging/reached → Closed', reached_engaging, closed_opportunities,
       closed_opportunities * 1.0 / reached_engaging
FROM counts
UNION ALL
SELECT 3, 'Engaging/reached → Won', reached_engaging, won_opportunities,
       won_opportunities * 1.0 / reached_engaging
FROM counts
UNION ALL
SELECT 4, 'Closed → Won', closed_opportunities, won_opportunities,
       won_opportunities * 1.0 / closed_opportunities
FROM counts
ORDER BY stage_order;
