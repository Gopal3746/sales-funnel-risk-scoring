CREATE OR REPLACE TABLE attrition_diagnostics AS
WITH base AS (
    SELECT
        COUNT(*) AS total_opportunities,
        COUNT(*) FILTER (WHERE deal_stage = 'Prospecting') AS still_prospecting,
        COUNT(*) FILTER (WHERE deal_stage = 'Engaging') AS still_engaging,
        COUNT(*) FILTER (WHERE deal_stage = 'Lost') AS lost_after_engagement,
        COUNT(*) FILTER (WHERE deal_stage = 'Won') AS won_after_engagement
    FROM mart_opportunities
)
SELECT
    'Post-engagement / close decision' AS observed_attrition_point,
    lost_after_engagement AS lost_deals,
    won_after_engagement AS won_deals,
    lost_after_engagement * 1.0 / (lost_after_engagement + won_after_engagement) AS loss_rate_among_closed,
    still_engaging AS unresolved_engaging,
    still_prospecting AS unresolved_prospecting,
    'The source has no full stage-event log; all closed losses have an engage_date, so attrition can only be located after engagement rather than assigned to invented intermediate stages.' AS interpretation
FROM base;
