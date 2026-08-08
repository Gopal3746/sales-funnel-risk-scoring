# Data

This project uses the public **CRM Sales Opportunities** dataset associated with Maven Analytics and mirrored on Kaggle.

Raw files included for reproducibility:

- `sales_pipeline.csv` — 8,800 opportunities
- `accounts.csv` — account firmographics
- `products.csv` — product family and list price
- `sales_teams.csv` — rep, manager, and region

The source CRM only records four observed states: `Prospecting`, `Engaging`, `Won`, and `Lost`. It does **not** contain a full stage-event history. The project therefore avoids inventing intermediate stages. Funnel conversion is reconstructed only from states that are supported by the timestamps and status fields.
