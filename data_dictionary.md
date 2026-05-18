# Data Dictionary

| File | Grain | Purpose |
| --- | --- | --- |
| `data/properties.csv` | Property asset | Portfolio inventory with stage, market, housing type, unit count, regional owner, and strategy lane. |
| `data/weekly_metrics.csv` | Property by week | Operating history used for occupancy, leasing velocity, traffic conversion, concessions, exposure, and NOI variance. |
| `data/market_comps.csv` | Property by week | Comp-set rent position, comp occupancy, submarket traffic index, and new supply pressure. |
| `data/pricing_recommendations.csv` | Property pricing recommendation | AIRM-style recommendation queue with current rent, recommended rent, approval lane, confidence, risk, expected NOI lift, and rationale. |
| `data/pricing_approval_log.csv` | Property approval record | Decision owner, reason code, and pricing system context for the approval workflow. |
| `data/recommended_actions.csv` | Property action | Regional operating action tied to pricing, lease-up, NOI variance, or exposure risk. |
| `analysis/outputs/forecast_watchlist.csv` | Property | Ranked watchlist for regional action, including target occupancy gap, leasing velocity, traffic trend, NOI variance, exposure, and corrective action. |
| `analysis/outputs/pricing_priority_queue.csv` | Property pricing recommendation | Copy of the pricing queue for analysis review and export. |
| `analysis/outputs/summary.json` | Portfolio | Top-level metrics used by the static console. |
