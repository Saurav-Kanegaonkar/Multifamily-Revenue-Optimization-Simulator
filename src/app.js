const paths = {
  properties: "data/properties.csv",
  weekly: "data/weekly_metrics.csv",
  pricing: "data/pricing_recommendations.csv",
  watchlist: "analysis/outputs/forecast_watchlist.csv",
  summary: "analysis/outputs/summary.json"
};

const currency = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0
});

const number = new Intl.NumberFormat("en-US");

function parseCsv(text) {
  const rows = [];
  const lines = text.trim().split(/\r?\n/);
  const headers = lines.shift().split(",");
  for (const line of lines) {
    const values = [];
    let current = "";
    let quoted = false;
    for (let i = 0; i < line.length; i += 1) {
      const char = line[i];
      if (char === '"') {
        quoted = !quoted;
      } else if (char === "," && !quoted) {
        values.push(current);
        current = "";
      } else {
        current += char;
      }
    }
    values.push(current);
    rows.push(Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ""])));
  }
  return rows;
}

async function loadCsv(path) {
  const response = await fetch(path);
  return parseCsv(await response.text());
}

function pct(value, digits = 1) {
  return `${(Number(value) * 100).toFixed(digits)}%`;
}

function latestWeekly(rows) {
  return Object.values(
    rows.reduce((acc, row) => {
      acc[row.property_id] = row;
      return acc;
    }, {})
  );
}

function groupBy(rows, key) {
  return rows.reduce((acc, row) => {
    const value = row[key];
    acc[value] = acc[value] || [];
    acc[value].push(row);
    return acc;
  }, {});
}

function mean(rows, key) {
  return rows.reduce((sum, row) => sum + Number(row[key]), 0) / Math.max(rows.length, 1);
}

function laneClass(lane) {
  if (lane === "Approve") return "good";
  if (lane === "Regional review") return "warn";
  return "risk";
}

function renderMetrics(summary) {
  const portfolio = summary.portfolio;
  const metrics = [
    ["Assets", portfolio.properties, `${number.format(portfolio.units)} units`],
    ["Occupancy", pct(portfolio.occupancy), `${portfolio.leaseup_assets} lease-up assets`],
    ["NOI variance", pct(portfolio.weekly_noi_variance_pct), "latest weekly run rate"],
    ["Review queue", portfolio.pricing_reviews, `${portfolio.pricing_approvals} auto-approve candidates`]
  ];

  document.querySelector("#metricGrid").innerHTML = metrics.map(([label, value, detail]) => `
    <article>
      <span>${label}</span>
      <strong>${value}</strong>
      <small>${detail}</small>
    </article>
  `).join("");
  document.querySelector("#reviewCount").textContent = `${portfolio.pricing_reviews} reviews`;
}

function renderMarkets(weeklyRows) {
  const latest = latestWeekly(weeklyRows);
  const markets = Object.entries(groupBy(latest, "market")).map(([market, rows]) => {
    const units = rows.reduce((sum, row) => sum + Number(row.units), 0);
    const leased = rows.reduce((sum, row) => sum + Number(row.units) * Number(row.occupancy), 0);
    const noi = rows.reduce((sum, row) => sum + Number(row.actual_noi), 0);
    const budget = rows.reduce((sum, row) => sum + Number(row.budget_noi), 0);
    return { market, rows, units, occupancy: leased / units, variance: (noi - budget) / budget };
  }).sort((a, b) => a.variance - b.variance);

  document.querySelector("#marketList").innerHTML = markets.map((market) => `
    <div class="market-row">
      <div>
        <strong>${market.market}</strong>
        <span>${market.rows.length} assets, ${number.format(market.units)} units</span>
      </div>
      <div class="market-metrics">
        <b>${pct(market.occupancy)}</b>
        <em class="${market.variance < -0.04 ? "risk-text" : "good-text"}">${pct(market.variance)}</em>
      </div>
    </div>
  `).join("");
}

function renderAssets(properties, weeklyRows) {
  const latest = latestWeekly(weeklyRows);
  const byId = Object.fromEntries(latest.map((row) => [row.property_id, row]));
  document.querySelector("#assetGrid").innerHTML = properties.map((property) => {
    const row = byId[property.property_id];
    const variance = (Number(row.actual_noi) - Number(row.budget_noi)) / Number(row.budget_noi);
    return `
      <article>
        <div>
          <span>${property.asset_stage}</span>
          <strong>${property.property_name}</strong>
          <small>${property.market} / ${property.housing_type}</small>
        </div>
        <div class="asset-stats">
          <b>${pct(row.occupancy)}</b>
          <em>${pct(variance)}</em>
        </div>
      </article>
    `;
  }).join("");
}

function renderPricing(pricingRows, filter = "all") {
  const rows = pricingRows
    .filter((row) => filter === "all" || row.approval_lane === filter)
    .sort((a, b) => Number(b.absorption_risk_score) - Number(a.absorption_risk_score));
  document.querySelector("#pricingRows").innerHTML = rows.map((row) => `
    <tr>
      <td><strong>${row.property_name}</strong><small>${row.asset_stage} / ${row.unit_type}</small></td>
      <td>${row.market}</td>
      <td>${currency.format(row.current_rent)}</td>
      <td>${currency.format(row.recommended_rent)}</td>
      <td class="${Number(row.recommended_change_pct) < 0 ? "risk-text" : "good-text"}">${pct(row.recommended_change_pct)}</td>
      <td>${Number(row.absorption_risk_score).toFixed(1)}</td>
      <td><span class="pill ${laneClass(row.approval_lane)}">${row.approval_lane}</span></td>
      <td>${row.rationale}</td>
    </tr>
  `).join("");
}

function renderWatchlist(rows) {
  const top = rows.slice(0, 7);
  document.querySelector("#watchlistCards").innerHTML = top.map((row, index) => `
    <article>
      <div class="rank">${index + 1}</div>
      <div>
        <strong>${row.property_name}</strong>
        <span>${row.market} / ${row.asset_stage}</span>
        <p>${row.corrective_action}</p>
      </div>
      <div class="score">${Number(row.priority_score).toFixed(1)}</div>
    </article>
  `).join("");

  document.querySelector("#varianceBars").innerHTML = top.map((row) => {
    const width = Math.min(100, Math.abs(Number(row.noi_variance_pct)) * 850);
    return `
      <div class="bar-row">
        <div>
          <strong>${row.property_name}</strong>
          <span>${pct(row.traffic_trend_pct)} traffic trend, ${row.exposure_next_60} exposed units</span>
        </div>
        <div class="bar-track"><i style="width:${width}%"></i></div>
        <b>${pct(row.noi_variance_pct)}</b>
      </div>
    `;
  }).join("");
}

function setupTabs() {
  document.querySelectorAll(".tabs button").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll(".tabs button").forEach((item) => item.classList.remove("active"));
      document.querySelectorAll(".view").forEach((view) => view.classList.remove("active"));
      button.classList.add("active");
      document.querySelector(`#${button.dataset.view}View`).classList.add("active");
    });
  });
}

async function init() {
  const [properties, weekly, pricing, watchlist, summaryResponse] = await Promise.all([
    loadCsv(paths.properties),
    loadCsv(paths.weekly),
    loadCsv(paths.pricing),
    loadCsv(paths.watchlist),
    fetch(paths.summary)
  ]);
  const summary = await summaryResponse.json();

  renderMetrics(summary);
  renderMarkets(weekly);
  renderAssets(properties, weekly);
  renderPricing(pricing);
  renderWatchlist(watchlist);
  setupTabs();

  document.querySelector("#laneFilter").addEventListener("change", (event) => {
    renderPricing(pricing, event.target.value);
  });
}

init();
