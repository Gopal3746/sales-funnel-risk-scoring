CREATE OR REPLACE TABLE mart_opportunities AS
WITH pipeline AS (
    SELECT
        opportunity_id,
        sales_agent,
        CASE WHEN product = 'GTXPro' THEN 'GTX Pro' ELSE product END AS product,
        account,
        deal_stage,
        TRY_CAST(engage_date AS DATE) AS engage_date,
        TRY_CAST(close_date AS DATE) AS close_date,
        TRY_CAST(close_value AS DOUBLE) AS close_value
    FROM raw_sales_pipeline
),
accounts AS (
    SELECT
        account,
        CASE WHEN sector = 'technolgy' THEN 'technology' ELSE sector END AS sector,
        TRY_CAST(year_established AS INTEGER) AS year_established,
        TRY_CAST(revenue AS DOUBLE) AS revenue,
        TRY_CAST(employees AS INTEGER) AS employees,
        office_location,
        subsidiary_of
    FROM raw_accounts
)
SELECT
    p.opportunity_id,
    p.sales_agent,
    p.product,
    p.account,
    p.deal_stage,
    p.engage_date,
    p.close_date,
    p.close_value,
    t.manager,
    t.regional_office,
    pr.series,
    TRY_CAST(pr.sales_price AS DOUBLE) AS sales_price,
    a.sector,
    a.year_established,
    a.revenue,
    a.employees,
    a.office_location,
    a.subsidiary_of,
    CASE WHEN p.deal_stage IN ('Won', 'Lost') THEN 1 ELSE 0 END AS is_closed,
    CASE WHEN p.deal_stage = 'Won' THEN 1 WHEN p.deal_stage = 'Lost' THEN 0 ELSE NULL END AS won,
    CASE
        WHEN p.deal_stage IN ('Won', 'Lost')
        THEN date_diff('day', p.engage_date, p.close_date)
        ELSE NULL
    END AS cycle_days,
    CASE
        WHEN p.deal_stage = 'Engaging'
        THEN date_diff('day', p.engage_date, (SELECT MAX(TRY_CAST(close_date AS DATE)) FROM raw_sales_pipeline))
        ELSE NULL
    END AS days_in_stage
FROM pipeline p
LEFT JOIN raw_sales_teams t USING (sales_agent)
LEFT JOIN raw_products pr ON p.product = pr.product
LEFT JOIN accounts a USING (account);
