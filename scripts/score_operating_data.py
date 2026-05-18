import csv
import json
import math
import random
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUTPUTS = ROOT / "analysis" / "outputs"
RNG = random.Random(42)

MARKETS = [
    ("San Antonio", "Northwest", 1.00, 0.95),
    ("San Antonio", "Medical Center", 1.04, 1.02),
    ("Austin", "Round Rock", 1.18, 1.08),
    ("Austin", "South Austin", 1.22, 1.04),
    ("Irving", "Las Colinas", 1.16, 1.03),
    ("Dallas Fort Worth", "Arlington", 1.08, 0.98),
    ("Houston", "Katy", 1.06, 0.99),
    ("Phoenix", "Mesa", 1.10, 1.00),
]

NAMES = [
    "Cedar Vista",
    "Mission Ridge",
    "Parkline",
    "Alta Quarry",
    "Live Oak Crossing",
    "Riverbend",
    "Canyon Commons",
    "Bluebonnet Flats",
    "Juniper Yard",
    "Lantana Square",
    "Mesa Verde",
    "The Alamo Lofts",
    "Mariposa Commons",
    "Silverleaf",
    "Southtown Station",
    "Avion Ridge",
    "Hill Country Villas",
    "Catalina Pointe",
]

UNIT_MIX = {
    "Studio": 0.70,
    "1BR": 0.86,
    "2BR": 1.12,
    "3BR": 1.35,
}


def clamp(value, low, high):
    return max(low, min(high, value))


def pct(value):
    return round(value * 100, 1)


def write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_properties():
    stages = ["Stabilized", "Stabilized", "Lease-up", "Turnaround"]
    housing = ["Market-rate", "Market-rate", "Affordable", "Senior"]
    managers = ["North Region", "Central Region", "South Region", "Southwest Region"]
    properties = []
    for idx, name in enumerate(NAMES, start=1):
        market, submarket, rent_factor, demand_factor = MARKETS[(idx - 1) % len(MARKETS)]
        stage = stages[(idx + (idx // 4)) % len(stages)]
        housing_type = housing[(idx + 1) % len(housing)]
        units = RNG.choice([156, 184, 212, 248, 276, 318, 364])
        age = RNG.choice([2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024])
        strategy = {
            "Stabilized": "Protect occupancy and harvest rent growth",
            "Lease-up": "Accelerate absorption while limiting concession burn",
            "Turnaround": "Course-correct traffic, pricing, and exposure",
        }[stage]
        properties.append(
            {
                "property_id": f"MF{idx:03d}",
                "property_name": name,
                "market": market,
                "submarket": submarket,
                "asset_stage": stage,
                "housing_type": housing_type,
                "units": units,
                "year_built": age,
                "regional_manager": managers[idx % len(managers)],
                "rent_factor": rent_factor,
                "demand_factor": demand_factor,
                "strategy_lane": strategy,
            }
        )
    return properties


def build_weekly_metrics(properties):
    weekly_rows = []
    comp_rows = []
    start = date(2026, 1, 4)
    for prop in properties:
        units = int(prop["units"])
        stage = prop["asset_stage"]
        base_occ = {"Stabilized": 0.944, "Lease-up": 0.742, "Turnaround": 0.882}[stage]
        base_rent = RNG.randint(1420, 1830) * float(prop["rent_factor"])
        demand = float(prop["demand_factor"])
        concession_base = {"Stabilized": 0.006, "Lease-up": 0.035, "Turnaround": 0.022}[stage]
        for week_idx in range(16):
            week = start + timedelta(days=week_idx * 7)
            seasonal = math.sin((week_idx + 2) / 16 * math.pi) * 0.018
            shock = RNG.uniform(-0.018, 0.018)
            occupancy = clamp(base_occ + seasonal + shock + (week_idx * 0.0015 if stage == "Lease-up" else 0), 0.62, 0.985)
            leased_units = round(units * occupancy)
            available_units = units - leased_units
            notices = round(units * RNG.uniform(0.012, 0.028))
            traffic = round((available_units * RNG.uniform(2.0, 4.6) + RNG.uniform(18, 55)) * demand)
            tours = round(traffic * RNG.uniform(0.33, 0.52))
            apps = round(tours * RNG.uniform(0.25, 0.43))
            signed = round(apps * RNG.uniform(0.45, 0.72))
            renewals = round(notices * RNG.uniform(0.38, 0.68))
            asking_rent = base_rent * (1 + week_idx * RNG.uniform(0.0005, 0.0022))
            concessions = clamp(concession_base + (0.92 - occupancy) * 0.07 + RNG.uniform(-0.004, 0.008), 0, 0.085)
            effective_rent = asking_rent * (1 - concessions)
            days_vacant = clamp(11 + available_units / max(1, signed + renewals) * 2.1 + RNG.uniform(-3, 5), 6, 54)
            exposure_60 = round(units * RNG.uniform(0.045, 0.115) + notices * RNG.uniform(1.5, 3.3))
            budget_noi = units * base_rent * 0.63
            actual_noi = leased_units * effective_rent * 0.62 - concessions * units * asking_rent * 0.08
            weekly_rows.append(
                {
                    "week_start": week.isoformat(),
                    "property_id": prop["property_id"],
                    "property_name": prop["property_name"],
                    "market": prop["market"],
                    "asset_stage": stage,
                    "housing_type": prop["housing_type"],
                    "units": units,
                    "occupancy": round(occupancy, 4),
                    "available_units": available_units,
                    "notices": notices,
                    "traffic": traffic,
                    "tours": tours,
                    "applications": apps,
                    "signed_leases": signed,
                    "renewals": renewals,
                    "asking_rent": round(asking_rent, 0),
                    "effective_rent": round(effective_rent, 0),
                    "concession_pct": round(concessions, 4),
                    "avg_days_vacant": round(days_vacant, 1),
                    "exposure_next_60": exposure_60,
                    "budget_noi": round(budget_noi, 0),
                    "actual_noi": round(actual_noi, 0),
                }
            )
            comp_rent = asking_rent * RNG.uniform(0.965, 1.06)
            comp_occ = clamp(occupancy + RNG.uniform(-0.03, 0.035), 0.68, 0.985)
            comp_rows.append(
                {
                    "week_start": week.isoformat(),
                    "property_id": prop["property_id"],
                    "property_name": prop["property_name"],
                    "market": prop["market"],
                    "submarket": prop["submarket"],
                    "comp_effective_rent": round(comp_rent, 0),
                    "subject_effective_rent": round(effective_rent, 0),
                    "rent_position_vs_comp_pct": round((effective_rent - comp_rent) / comp_rent, 4),
                    "comp_occupancy": round(comp_occ, 4),
                    "submarket_traffic_index": round(clamp(100 * demand + RNG.uniform(-11, 12), 72, 128), 1),
                    "new_supply_units": round(RNG.uniform(80, 540) if stage != "Stabilized" else RNG.uniform(20, 260)),
                }
            )
    return weekly_rows, comp_rows


def latest_by_property(rows):
    latest = {}
    for row in rows:
        latest[row["property_id"]] = row
    return latest


def summarize_history(weekly_rows):
    history = defaultdict(list)
    for row in weekly_rows:
        history[row["property_id"]].append(row)
    return history


def build_outputs(properties, weekly_rows, comp_rows):
    by_property = latest_by_property(weekly_rows)
    comp_latest = latest_by_property(comp_rows)
    history = summarize_history(weekly_rows)
    pricing = []
    watchlist = []
    approvals = []
    actions = []

    for prop in properties:
        latest = by_property[prop["property_id"]]
        prior_four = history[prop["property_id"]][-4:]
        prev_four = history[prop["property_id"]][-8:-4]
        comp = comp_latest[prop["property_id"]]
        occ = float(latest["occupancy"])
        target_occ = {"Stabilized": 0.948, "Lease-up": 0.84, "Turnaround": 0.915}[prop["asset_stage"]]
        lease_velocity = sum(int(r["signed_leases"]) for r in prior_four) / 4
        prev_traffic = sum(int(r["traffic"]) for r in prev_four) / max(1, len(prev_four))
        recent_traffic = sum(int(r["traffic"]) for r in prior_four) / 4
        traffic_trend = (recent_traffic - prev_traffic) / max(prev_traffic, 1)
        noi_variance = (float(latest["actual_noi"]) - float(latest["budget_noi"])) / float(latest["budget_noi"])
        rent_position = float(comp["rent_position_vs_comp_pct"])
        concession = float(latest["concession_pct"])
        exposure = int(latest["exposure_next_60"])
        occupancy_gap = target_occ - occ
        pressure = rent_position * 0.40 + occupancy_gap * -0.34 + traffic_trend * 0.16 - concession * 0.42
        change_pct = clamp(pressure, -0.045, 0.052)
        if prop["asset_stage"] == "Lease-up" and occ < 0.82:
            change_pct = min(change_pct, 0.004)
        if exposure > int(prop["units"]) * 0.11:
            change_pct = min(change_pct, -0.008)
        current_rent = float(latest["asking_rent"])
        rec_rent = round(current_rent * (1 + change_pct), 0)
        risk = clamp(38 + occupancy_gap * 155 + exposure / int(prop["units"]) * 90 - traffic_trend * 30 + concession * 180, 10, 99)
        monthly_lift = (rec_rent - current_rent) * int(latest["available_units"]) * (1 - risk / 180)
        confidence = clamp(0.62 + abs(rent_position) * 1.3 + min(recent_traffic / 280, 0.15) - risk / 420, 0.44, 0.92)
        lane = "Approve" if confidence > 0.72 and risk < 58 else "Regional review" if risk < 76 else "Hold for pricing call"
        if change_pct < -0.018:
            rationale = "Reduce friction where exposure and velocity point to absorption risk."
        elif change_pct > 0.018:
            rationale = "Capture rent growth where occupancy and comp position support lift."
        else:
            rationale = "Hold near current rent and monitor conversion before the next pricing cycle."
        pricing.append(
            {
                "property_id": prop["property_id"],
                "property_name": prop["property_name"],
                "market": prop["market"],
                "asset_stage": prop["asset_stage"],
                "unit_type": RNG.choice(list(UNIT_MIX.keys())),
                "current_rent": round(current_rent, 0),
                "comp_rent": comp["comp_effective_rent"],
                "recommended_rent": rec_rent,
                "recommended_change_pct": round(change_pct, 4),
                "confidence": round(confidence, 3),
                "approval_lane": lane,
                "absorption_risk_score": round(risk, 1),
                "expected_monthly_noi_lift": round(monthly_lift, 0),
                "rationale": rationale,
            }
        )
        priority = clamp(occupancy_gap * 150 + max(-noi_variance, 0) * 130 + exposure / int(prop["units"]) * 80 - traffic_trend * 34 + concession * 120, 0, 100)
        if priority > 65:
            action = "Run regional pricing review with comps, concessions, and weekly traffic source checks."
        elif prop["asset_stage"] == "Lease-up":
            action = "Tune concessions and lead response by floor plan before the next lease-up review."
        elif noi_variance < -0.04:
            action = "Escalate NOI variance and isolate rent, vacancy, and concession drivers."
        else:
            action = "Keep in normal weekly review and watch exposure risk."
        watchlist.append(
            {
                "property_id": prop["property_id"],
                "property_name": prop["property_name"],
                "market": prop["market"],
                "asset_stage": prop["asset_stage"],
                "occupancy_gap_to_target": round(occupancy_gap, 4),
                "leasing_velocity_4wk": round(lease_velocity, 1),
                "traffic_trend_pct": round(traffic_trend, 4),
                "noi_variance_pct": round(noi_variance, 4),
                "exposure_next_60": exposure,
                "concession_pct": latest["concession_pct"],
                "priority_score": round(priority, 1),
                "corrective_action": action,
            }
        )
        approvals.append(
            {
                "property_id": prop["property_id"],
                "property_name": prop["property_name"],
                "requested_by": prop["regional_manager"],
                "approval_lane": lane,
                "decision_owner": "Revenue management" if lane == "Approve" else "Revenue and regional operations",
                "pricing_system_context": "AIRM style recommendation review",
                "reason_code": "Comp position" if abs(rent_position) > 0.025 else "Velocity and exposure",
            }
        )
        actions.append(
            {
                "property_id": prop["property_id"],
                "property_name": prop["property_name"],
                "action_type": "Pricing" if "pricing" in action.lower() else "Operations",
                "action": action,
                "owner": prop["regional_manager"],
                "expected_impact": round(max(monthly_lift, 0) * 3 + max(-noi_variance, 0) * float(latest["budget_noi"]), 0),
                "effort": RNG.choice(["Low", "Medium", "Medium", "High"]),
            }
        )

    pricing.sort(key=lambda r: (r["approval_lane"] != "Approve", -float(r["expected_monthly_noi_lift"])))
    watchlist.sort(key=lambda r: float(r["priority_score"]), reverse=True)
    actions.sort(key=lambda r: float(r["expected_impact"]), reverse=True)
    return pricing, watchlist, approvals, actions


def build_summary(properties, weekly_rows, pricing, watchlist):
    latest = list(latest_by_property(weekly_rows).values())
    total_units = sum(int(r["units"]) for r in latest)
    leased_units = sum(round(int(r["units"]) * float(r["occupancy"])) for r in latest)
    actual_noi = sum(float(r["actual_noi"]) for r in latest)
    budget_noi = sum(float(r["budget_noi"]) for r in latest)
    leaseup = sum(1 for p in properties if p["asset_stage"] == "Lease-up")
    approve_count = sum(1 for r in pricing if r["approval_lane"] == "Approve")
    review_count = sum(1 for r in pricing if r["approval_lane"] != "Approve")
    top_watch = watchlist[0]
    return {
        "portfolio": {
            "properties": len(properties),
            "units": total_units,
            "occupancy": round(leased_units / total_units, 4),
            "weekly_noi_variance_pct": round((actual_noi - budget_noi) / budget_noi, 4),
            "leaseup_assets": leaseup,
            "pricing_approvals": approve_count,
            "pricing_reviews": review_count,
            "watchlist_assets": sum(1 for r in watchlist if float(r["priority_score"]) >= 55),
            "top_watch_asset": top_watch["property_name"],
            "top_watch_reason": top_watch["corrective_action"],
        },
        "method": {
            "pricing_score": "Rent change responds to occupancy gap, traffic trend, comp rent position, concessions, and 60 day exposure.",
            "watchlist_score": "Priority rises with target occupancy gap, negative NOI variance, exposure, concessions, and falling traffic.",
        },
    }


def main():
    DATA.mkdir(exist_ok=True)
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    properties = build_properties()
    weekly_rows, comp_rows = build_weekly_metrics(properties)
    pricing, watchlist, approvals, actions = build_outputs(properties, weekly_rows, comp_rows)
    summary = build_summary(properties, weekly_rows, pricing, watchlist)

    property_fields = [
        "property_id",
        "property_name",
        "market",
        "submarket",
        "asset_stage",
        "housing_type",
        "units",
        "year_built",
        "regional_manager",
        "strategy_lane",
    ]
    write_csv(DATA / "properties.csv", [{k: v for k, v in row.items() if k in property_fields} for row in properties], property_fields)
    write_csv(DATA / "weekly_metrics.csv", weekly_rows, list(weekly_rows[0].keys()))
    write_csv(DATA / "market_comps.csv", comp_rows, list(comp_rows[0].keys()))
    write_csv(DATA / "pricing_recommendations.csv", pricing, list(pricing[0].keys()))
    write_csv(DATA / "pricing_approval_log.csv", approvals, list(approvals[0].keys()))
    write_csv(DATA / "recommended_actions.csv", actions, list(actions[0].keys()))
    write_csv(OUTPUTS / "forecast_watchlist.csv", watchlist, list(watchlist[0].keys()))
    write_csv(OUTPUTS / "pricing_priority_queue.csv", pricing, list(pricing[0].keys()))
    (OUTPUTS / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    print(f"Generated {len(properties)} properties, {len(weekly_rows)} weekly rows, and {len(pricing)} pricing recommendations.")
    print(f"Portfolio occupancy: {pct(summary['portfolio']['occupancy'])}%")
    print(f"Weekly NOI variance: {pct(summary['portfolio']['weekly_noi_variance_pct'])}%")
    print(f"Top watchlist asset: {summary['portfolio']['top_watch_asset']}")


if __name__ == "__main__":
    main()
