# Data Notes

This project uses synthetic, workflow-shaped data for a multifamily owner, developer, and property management portfolio across Texas and select Southwest markets. The data is not real property performance.

## Generated Tables

- `properties.csv`: 18 property assets with market, submarket, housing type, asset stage, units, regional manager, and strategy lane.
- `weekly_metrics.csv`: 288 property-week operating rows covering occupancy, availability, traffic, tours, applications, signed leases, renewals, rent, concessions, exposure, and NOI.
- `market_comps.csv`: 288 property-week comp signals covering comp rent, subject rent position, comp occupancy, traffic index, and new supply.
- `pricing_recommendations.csv`: 18 AIRM-style pricing recommendations with current rent, comp rent, recommended rent, confidence, absorption risk, expected NOI lift, and approval lane.
- `pricing_approval_log.csv`: 18 approval records showing decision owner, reason code, and pricing-system context.
- `recommended_actions.csv`: 18 operating actions tied to pricing, lease-up, NOI variance, or exposure risk.

## Synthetic Generation Method

The generator in `scripts/score_operating_data.py` creates assets across San Antonio, Austin, Dallas Fort Worth, Houston, Irving, and Phoenix. Asset stages are stabilized, lease-up, and turnaround. Housing types include market-rate, affordable, and senior housing.

Occupancy is modeled by asset stage. Stabilized assets center near 94 percent, lease-up assets center near 74 percent with gradual improvement, and turnaround assets center near 88 percent. Traffic, tours, applications, signed leases, and renewals are derived from availability, demand factor, and conversion ranges. Rent and concessions vary by market rent factor, asset stage, occupancy, and exposure. NOI variance compares modeled actual NOI to a budget run rate. Market comps are generated around subject rent with submarket traffic and supply pressure.

Pricing recommendations use a transparent score. Rent movement responds to comp rent position, occupancy gap, traffic trend, concessions, and 60 day exposure. Forecast watchlist priority rises with target occupancy gap, negative NOI variance, exposure, concessions, and falling traffic.
