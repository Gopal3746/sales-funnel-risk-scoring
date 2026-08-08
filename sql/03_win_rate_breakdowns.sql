CREATE OR REPLACE TABLE win_rate_by_rep AS
SELECT
    sales_agent,
    manager,
    regional_office,
    COUNT(*) AS closed_deals,
    SUM(won) AS won_deals,
    AVG(won) AS win_rate,
    SUM(CASE WHEN won = 1 THEN close_value ELSE 0 END) AS won_revenue
FROM mart_opportunities
WHERE is_closed = 1
GROUP BY ALL
HAVING COUNT(*) >= 25
ORDER BY win_rate DESC, closed_deals DESC;

CREATE OR REPLACE TABLE win_rate_by_segment AS
SELECT
    COALESCE(sector, 'Unknown') AS sector,
    COUNT(*) AS closed_deals,
    SUM(won) AS won_deals,
    AVG(won) AS win_rate,
    AVG(sales_price) AS avg_list_price
FROM mart_opportunities
WHERE is_closed = 1
GROUP BY 1
ORDER BY win_rate DESC;

CREATE OR REPLACE TABLE win_rate_by_product AS
SELECT
    product,
    series,
    COUNT(*) AS closed_deals,
    SUM(won) AS won_deals,
    AVG(won) AS win_rate,
    AVG(close_value) FILTER (WHERE won = 1) AS avg_won_value
FROM mart_opportunities
WHERE is_closed = 1
GROUP BY ALL
ORDER BY win_rate DESC;
