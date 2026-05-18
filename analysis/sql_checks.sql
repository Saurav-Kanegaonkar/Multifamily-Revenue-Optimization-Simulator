-- SQL appendix for a multifamily revenue optimization review.
-- Written in portable warehouse-style SQL for interview discussion.

with latest_week as (
  select max(week_start) as week_start
  from weekly_metrics
),
latest_metrics as (
  select wm.*
  from weekly_metrics wm
  join latest_week lw
    on wm.week_start = lw.week_start
),
property_health as (
  select
    property_id,
    property_name,
    market,
    asset_stage,
    units,
    occupancy,
    exposure_next_60,
    concession_pct,
    actual_noi,
    budget_noi,
    (actual_noi - budget_noi) / nullif(budget_noi, 0) as noi_variance_pct
  from latest_metrics
)
select
  market,
  count(*) as asset_count,
  sum(units) as units,
  sum(units * occupancy) / nullif(sum(units), 0) as weighted_occupancy,
  avg(concession_pct) as avg_concession_pct,
  sum(actual_noi - budget_noi) / nullif(sum(budget_noi), 0) as noi_variance_pct
from property_health
group by market
order by noi_variance_pct asc;

-- Pricing review queue with comp context.

select
  pr.property_name,
  pr.market,
  pr.asset_stage,
  pr.current_rent,
  pr.comp_rent,
  pr.recommended_rent,
  pr.recommended_change_pct,
  pr.absorption_risk_score,
  pr.expected_monthly_noi_lift,
  pr.approval_lane,
  pr.rationale
from pricing_recommendations pr
order by
  case pr.approval_lane
    when 'Hold for pricing call' then 1
    when 'Regional review' then 2
    else 3
  end,
  pr.absorption_risk_score desc;

-- Forecast watchlist for regional operations follow-up.

select
  property_name,
  market,
  asset_stage,
  occupancy_gap_to_target,
  leasing_velocity_4wk,
  traffic_trend_pct,
  noi_variance_pct,
  exposure_next_60,
  priority_score,
  corrective_action
from forecast_watchlist
where priority_score >= 55
order by priority_score desc;
