"""
Vietnam Economy – Macroeconomic Analysis
Data source: GSO / NSO Vietnam SDMX archive (all_data_gso_20250606.json.zip)
  db[0]  NAG  Annual    National Accounts (GDP, sectoral value-added)
  db[1]  CPI  Monthly   Consumer Price Index
  db[7]  MET  Monthly   Merchandise trade (exports / imports)
  db[8]  EXR  Monthly   Exchange rate USD/VND
  db[10] LMI  Quarterly Labor Market Indicators
Charts written to output/07_*.png – 12_*.png
"""

import json
import os
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE, "extracted_database.json")
OUT = os.path.join(BASE, "output")
os.makedirs(OUT, exist_ok=True)


def savefig(name):
    path = os.path.join(OUT, name)
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")


# ---------------------------------------------------------------------------
# SDMX helpers
# ---------------------------------------------------------------------------

def _safe_float(val):
    """Convert SDMX obs value to float; return None for 'na' etc."""
    try:
        return float(str(val).replace(" ", ""))
    except (ValueError, TypeError):
        return None


def load_db():
    with open(DB_PATH) as f:
        return json.load(f)


def get_series(domain_list, indicator, freq=None):
    """Return the first matching series dict from a domain list."""
    for s in domain_list:
        if s.get("@INDICATOR") == indicator:
            if freq is None or s.get("@FREQ") == freq:
                return s
    return None


def obs_to_dict(series):
    """Return {time_period: float_value} from a series, skipping na."""
    result = {}
    for o in series.get("Obs", []):
        v = _safe_float(o["@OBS_VALUE"])
        if v is not None:
            result[o["@TIME_PERIOD"]] = v
    return result


def aggregate_monthly_to_annual(monthly_dict):
    """Sum monthly values by year."""
    annual = {}
    for period, val in monthly_dict.items():
        yr = period[:4]
        annual[yr] = annual.get(yr, 0.0) + val
    return annual


def quarterly_to_annual_avg(qdict):
    """Average quarterly values into annual."""
    sums = {}
    counts = {}
    for period, val in qdict.items():
        yr = period[:4]
        sums[yr] = sums.get(yr, 0.0) + val
        counts[yr] = counts.get(yr, 0) + 1
    return {yr: sums[yr] / counts[yr] for yr in sums}


def yoy_growth(value_dict):
    """Year-over-year percentage growth from a {year: value} dict."""
    yrs = sorted(value_dict.keys())
    growth = {}
    for i in range(1, len(yrs)):
        prev = value_dict[yrs[i - 1]]
        curr = value_dict[yrs[i]]
        if prev and prev != 0:
            growth[yrs[i]] = (curr / prev - 1) * 100
    return growth


# ---------------------------------------------------------------------------
# Analysis 1 – GDP overview
# ---------------------------------------------------------------------------

def analyze_gdp(db):
    print("\n[1/5] GDP Overview")
    nag = db[0]

    # nominal GDP (annual, billion VND)
    ngdp = obs_to_dict(get_series(nag, "NGDP_XDC", freq="A"))
    # real GDP (constant 2010 prices, billion VND)
    rgdp = obs_to_dict(get_series(nag, "NGDP_R_XDC", freq="A"))
    # real GDP growth = yoy from rgdp
    rgdp_growth = yoy_growth(rgdp)

    # USD exchange rate (annual avg from EXR monthly)
    exr = db[8]
    usd_series = get_series(exr, "ENDA_MID_XDC_USD_RATE")
    if usd_series:
        monthly_exr = obs_to_dict(usd_series)
        annual_exr = quarterly_to_annual_avg(monthly_exr)
    else:
        annual_exr = {}

    # GDP per capita: nominal GDP (billion VND) × 10^9 / population
    # We load population from E02.02 JSON-stat
    pop_data = _load_national_population()

    years_gdp = sorted(ngdp.keys())
    # GDP in trillion VND
    gdp_tvnd = {y: ngdp[y] / 1000 for y in years_gdp}
    # GDP in billion USD (convert via avg exchange rate or 25000 fallback)
    gdp_busd = {}
    for y in years_gdp:
        rate = annual_exr.get(y, 25000)
        gdp_busd[y] = ngdp[y] * 1e9 / rate / 1e9  # billion USD

    # GDP per capita in million VND
    gdp_pc_mvnd = {}
    for y in years_gdp:
        pop_millions = pop_data.get(y)
        if pop_millions:
            gdp_pc_mvnd[y] = ngdp[y] * 1e9 / (pop_millions * 1e6) / 1e6  # million VND

    fig, axes = plt.subplots(3, 1, figsize=(12, 14))
    fig.suptitle("Vietnam – GDP Overview (National Accounts)", fontsize=14, fontweight="bold")

    # GDP nominal
    ax = axes[0]
    yrs = sorted(gdp_tvnd.keys())
    vals_tvnd = [gdp_tvnd[y] for y in yrs]
    vals_busd = [gdp_busd.get(y, 0) for y in yrs]
    ax2 = ax.twinx()
    ax.bar(yrs, vals_tvnd, color="#1f77b4", alpha=0.6, label="GDP (T VND)")
    ax2.plot(yrs, vals_busd, "ro-", linewidth=2, markersize=4, label="GDP (B USD)")
    ax.set_title("Nominal GDP (Trillion VND & Billion USD)")
    ax.set_ylabel("Trillion VND", color="#1f77b4")
    ax2.set_ylabel("Billion USD", color="red")
    ax.set_xlabel("Year")
    ax.tick_params(axis='x', rotation=45)
    ax.grid(True, alpha=0.3, axis="y")
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

    # Real GDP growth
    ax = axes[1]
    yrs_g = sorted(rgdp_growth.keys())
    vals_g = [rgdp_growth[y] for y in yrs_g]
    colors = ["#d62728" if v < 0 else "#2ca02c" for v in vals_g]
    ax.bar(yrs_g, vals_g, color=colors, alpha=0.75)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.axhline(6, color="gray", linewidth=1, linestyle="--", label="6% reference")
    ax.set_title("Real GDP Growth Rate (%, constant 2010 prices)")
    ax.set_ylabel("%")
    ax.set_xlabel("Year")
    ax.grid(True, alpha=0.3, axis="y")
    ax.legend()
    ax.tick_params(axis='x', rotation=45)
    for i, (yr, v) in enumerate(zip(yrs_g, vals_g)):
        ax.text(yr, v + 0.1 if v >= 0 else v - 0.3, f"{v:.1f}", ha="center", fontsize=7)

    # GDP per capita
    ax = axes[2]
    if gdp_pc_mvnd:
        yrs_pc = sorted(gdp_pc_mvnd.keys())
        vals_pc = [gdp_pc_mvnd[y] for y in yrs_pc]
        ax.plot(yrs_pc, vals_pc, "g-o", linewidth=2, markersize=4)
        ax.fill_between(yrs_pc, vals_pc, alpha=0.2, color="green")
        ax.set_title("GDP per Capita (Million VND at current prices)")
        ax.set_ylabel("Million VND / person")
        ax.set_xlabel("Year")
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='x', rotation=45)

    plt.tight_layout()
    savefig("07_gdp_overview.png")

    latest_yr = sorted(ngdp.keys())[-1]
    print(f"  GDP 2024: {ngdp[latest_yr]/1000:.0f}T VND = ~${gdp_busd.get(latest_yr,0):.0f}B USD")
    print(f"  Avg real GDP growth: {sum(rgdp_growth.values())/len(rgdp_growth):.1f}%/yr")
    print(f"  GDP per capita 2024: {gdp_pc_mvnd.get(latest_yr, 0):.1f}M VND")

    return {"ngdp": ngdp, "gdp_tvnd": gdp_tvnd, "rgdp_growth": rgdp_growth, "gdp_pc_mvnd": gdp_pc_mvnd}


def _load_national_population():
    """Load national total population (million persons) from E02.02.json."""
    path = os.path.join(BASE, "E02.02.json")
    with open(path, encoding="utf-8") as f:
        content = f.read().rstrip("\x00").strip()
    ds = json.loads(content)["dataset"]
    dim = ds["dimension"]
    years = {v: k for k, v in dim["Year"]["category"]["label"].items()}
    items_idx = {v: int(k) for k, v in dim["Items"]["category"]["index"].items()}
    sex_idx = {v: int(k) for k, v in dim["Sex, residence"]["category"]["index"].items()}
    n_years = len(dim["Year"]["category"]["label"])
    n_sex = len(dim["Sex, residence"]["category"]["label"])
    values = ds["value"]
    pop = {}
    for yr_label, yr_str in dim["Year"]["category"]["label"].items():
        yi = int(yr_label)
        # item=0 (Total Thous. pers.), sex=0 (Total)
        idx = 0 * n_years * n_sex + yi * n_sex + 0
        v = values[idx]
        if v is not None:
            clean_yr = yr_str.replace("Prel. ", "").strip()
            pop[clean_yr] = v / 1000  # convert thous. -> millions
    return pop


# ---------------------------------------------------------------------------
# Analysis 2 – GDP Sectoral Composition
# ---------------------------------------------------------------------------

def analyze_gdp_sectors(db):
    print("\n[2/5] GDP Sectoral Composition")
    nag = db[0]

    # Aggregate ISIC4 sectors into 3 broad groups (2010 constant prices)
    sector_defs = {
        "Agriculture": ["NGDPVA_R_ISIC4_A_XDC"],
        "Industry": [
            "NGDPVA_R_ISIC4_B_XDC", "NGDPVA_R_ISIC4_C_XDC",
            "NGDPVA_R_ISIC4_D_XDC", "NGDPVA_R_ISIC4_E_XDC",
            "NGDPVA_R_ISIC4_F_XDC",
        ],
        "Services": [
            "NGDPVA_R_ISIC4_G_XDC", "NGDPVA_R_ISIC4_H_XDC",
            "NGDPVA_R_ISIC4_I_XDC", "NGDPVA_R_ISIC4_J_XDC",
            "NGDPVA_R_ISIC4_K_XDC", "NGDPVA_R_ISIC4_L_XDC",
            "NGDPVA_R_ISIC4_M_XDC", "NGDPVA_R_ISIC4_N_XDC",
            "NGDPVA_R_ISIC4_O_XDC", "NGDPVA_R_ISIC4_P_XDC",
            "NGDPVA_R_ISIC4_Q_XDC", "NGDPVA_R_ISIC4_R_XDC",
            "NGDPVA_R_ISIC4_S_XDC", "NGDPVA_R_ISIC4_T_XDC",
        ],
    }

    sector_data = {}
    for sec_name, indicators in sector_defs.items():
        combined = {}
        for ind in indicators:
            s = get_series(nag, ind, freq="A")
            if s:
                for yr, v in obs_to_dict(s).items():
                    combined[yr] = combined.get(yr, 0.0) + v
        sector_data[sec_name] = combined

    all_years = sorted(set(yr for d in sector_data.values() for yr in d))
    all_years = [y for y in all_years if all(y in sector_data[s] and sector_data[s][y] > 0
                                              for s in sector_data)]

    if not all_years:
        print("  No complete sector data found – skipping")
        return {}

    # Calculate shares
    totals = {y: sum(sector_data[s].get(y, 0) for s in sector_data) for y in all_years}
    shares = {s: [sector_data[s].get(y, 0) / totals[y] * 100
                  if totals.get(y) else 0 for y in all_years]
              for s in sector_data}

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    fig.suptitle("Vietnam – GDP Sectoral Composition (Constant 2010 prices)",
                 fontsize=13, fontweight="bold")

    colors = ["#2ca02c", "#1f77b4", "#ff7f0e"]

    # Stacked area: share
    ax = axes[0]
    ax.stackplot(all_years,
                 shares["Agriculture"], shares["Industry"], shares["Services"],
                 labels=["Agriculture", "Industry", "Services"],
                 colors=colors, alpha=0.8)
    ax.set_title("Sectoral Share of GDP (%)")
    ax.set_ylabel("%")
    ax.set_xlabel("Year")
    ax.set_ylim(0, 100)
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3, axis="y")
    ax.tick_params(axis="x", rotation=45)

    # Absolute values (trillion VND)
    ax = axes[1]
    vals_agri = [sector_data["Agriculture"].get(y, 0) / 1000 for y in all_years]
    vals_ind  = [sector_data["Industry"].get(y, 0) / 1000 for y in all_years]
    vals_svc  = [sector_data["Services"].get(y, 0) / 1000 for y in all_years]
    ax.stackplot(all_years, vals_agri, vals_ind, vals_svc,
                 labels=["Agriculture", "Industry", "Services"],
                 colors=colors, alpha=0.8)
    ax.set_title("Sectoral GDP (Trillion VND)")
    ax.set_ylabel("Trillion VND")
    ax.set_xlabel("Year")
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3, axis="y")
    ax.tick_params(axis="x", rotation=45)

    plt.tight_layout()
    savefig("08_gdp_sectors.png")

    latest = all_years[-1]
    print(f"  Sector shares {latest}: Agri={shares['Agriculture'][-1]:.1f}%, "
          f"Industry={shares['Industry'][-1]:.1f}%, Services={shares['Services'][-1]:.1f}%")
    print(f"  Manufacturing GDP {latest}: {sector_data.get('Industry',{}).get(latest,0)/1000:.0f}T VND")

    return {"sector_data": sector_data, "shares": shares, "years": all_years}


# ---------------------------------------------------------------------------
# Analysis 3 – Merchandise Trade
# ---------------------------------------------------------------------------

def analyze_trade(db):
    print("\n[3/5] Merchandise Trade")
    met = db[7]

    ex_m  = obs_to_dict(get_series(met, "TXG_FOB_USD"))   # monthly exports (M USD)
    im_m  = obs_to_dict(get_series(met, "TMG_CIF_USD"))   # monthly imports (M USD)
    tb_m  = obs_to_dict(get_series(met, "TB_USD"))        # monthly trade balance

    ex_a  = aggregate_monthly_to_annual(ex_m)  # annual exports (M USD)
    im_a  = aggregate_monthly_to_annual(im_m)
    tb_a  = {yr: ex_a.get(yr, 0) - im_a.get(yr, 0) for yr in ex_a}

    # Filter years with 12 months of data
    from collections import Counter
    months_ex = Counter(p[:4] for p in ex_m)
    full_years = sorted(yr for yr, cnt in months_ex.items() if cnt == 12)
    ex_a  = {y: ex_a[y] for y in full_years}
    im_a  = {y: im_a[y] for y in full_years}
    tb_a  = {y: tb_a[y] for y in full_years}

    yrs = full_years

    fig, axes = plt.subplots(2, 1, figsize=(13, 10))
    fig.suptitle("Vietnam – Merchandise Trade (E02-GSO MET)", fontsize=13, fontweight="bold")

    # Annual trade
    ax = axes[0]
    x = range(len(yrs))
    w = 0.35
    bars1 = ax.bar([i - w/2 for i in x], [ex_a[y]/1000 for y in yrs],
                   w, label="Exports (FOB)", color="#1f77b4", alpha=0.8)
    bars2 = ax.bar([i + w/2 for i in x], [im_a[y]/1000 for y in yrs],
                   w, label="Imports (CIF)", color="#d62728", alpha=0.8)
    ax2 = ax.twinx()
    ax2.plot(x, [tb_a[y]/1000 for y in yrs], "go-", linewidth=2,
             markersize=5, label="Trade Balance")
    ax2.axhline(0, color="gray", linestyle=":", linewidth=1)
    ax.set_title("Annual Exports, Imports & Trade Balance (Billion USD)")
    ax.set_xticks(list(x))
    ax.set_xticklabels(yrs, rotation=45)
    ax.set_ylabel("Billion USD")
    ax2.set_ylabel("Trade Balance (B USD)", color="green")
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc="upper left")
    ax.grid(True, alpha=0.3, axis="y")

    # Monthly trade balance trend (rolling 12m sum)
    ax = axes[1]
    sorted_months = sorted(tb_m.keys())
    months = sorted_months
    tb_vals = [tb_m[m] / 1000 for m in months]  # billion USD
    # rolling 12-month sum
    window = 12
    rolling = [sum(tb_vals[max(0, i-window+1):i+1]) for i in range(len(tb_vals))]
    month_labels = [m for m in months]
    ax.bar(range(len(months)), tb_vals,
           color=["#d62728" if v < 0 else "#2ca02c" for v in tb_vals], alpha=0.5, label="Monthly")
    ax.plot(range(len(months)), rolling, "b-", linewidth=2, label="12m rolling sum")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_title("Monthly Trade Balance & 12-Month Rolling Sum (Billion USD)")
    ax.set_ylabel("Billion USD")
    ax.set_xlabel("Month")
    # x-axis: show every 12th label
    tick_positions = list(range(0, len(months), 12))
    ax.set_xticks(tick_positions)
    ax.set_xticklabels([months[i][:4] for i in tick_positions], rotation=45)
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()
    savefig("09_trade.png")

    latest = yrs[-1]
    print(f"  Trade 2024: Export=${ex_a[latest]/1000:.0f}B, Import=${im_a[latest]/1000:.0f}B, "
          f"Balance=${tb_a[latest]/1000:.0f}B USD")

    return {"ex_annual": ex_a, "im_annual": im_a, "tb_annual": tb_a}


# ---------------------------------------------------------------------------
# Analysis 4 – CPI Inflation
# ---------------------------------------------------------------------------

def analyze_cpi(db):
    print("\n[4/5] CPI & Inflation")
    cpi_domain = db[1]

    # Overall CPI index (2020=100 base)
    cpi_idx = obs_to_dict(get_series(cpi_domain, "PCPI_IX"))
    # YoY change (%)
    cpi_yoy = obs_to_dict(get_series(cpi_domain, "PCPICO_PC_PP_PT"))

    # Component indices
    components = {
        "Food & Non-Alc. Bev.": "PCPI_CP_01_IX",
        "Housing & Utilities":   "PCPI_CP_04_IX",
        "Transport":             "PCPI_CP_07_IX",
        "Healthcare":            "PCPI_CP_06_IX",
        "Education":             "PCPI_CP_10_IX",
        "Clothing":              "PCPI_CP_03_IX",
    }
    comp_data = {}
    for name, ind in components.items():
        s = get_series(cpi_domain, ind)
        if s:
            comp_data[name] = obs_to_dict(s)

    months = sorted(cpi_idx.keys())

    fig, axes = plt.subplots(2, 1, figsize=(13, 10))
    fig.suptitle("Vietnam – Consumer Price Index (CPI)", fontsize=13, fontweight="bold")

    # Overall CPI + YoY
    ax = axes[0]
    ax2 = ax.twinx()
    ax.plot(range(len(months)), [cpi_idx[m] for m in months],
            "b-", linewidth=2, label="CPI Index (2020=100)")
    yoy_months = sorted(cpi_yoy.keys())
    yoy_x = [months.index(m) for m in yoy_months if m in months]
    yoy_y = [cpi_yoy[m] for m in yoy_months if m in months]
    ax2.bar(yoy_x, yoy_y,
            color=["#d62728" if v > 4 else "#ff7f0e" if v > 2 else "#2ca02c" for v in yoy_y],
            alpha=0.5, label="YoY change (%)")
    ax2.axhline(0, color="gray", linewidth=0.8)
    ax2.axhline(4, color="red", linestyle=":", linewidth=1, label="4% target")
    ax.set_title("Overall CPI Index & Year-on-Year Inflation")
    ax.set_ylabel("CPI Index (2020 = 100)")
    ax2.set_ylabel("YoY Change (%)", color="#d62728")
    tick_pos = list(range(0, len(months), 6))
    ax.set_xticks(tick_pos)
    ax.set_xticklabels([months[i] for i in tick_pos], rotation=45)
    ax.grid(True, alpha=0.3)
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=8)

    # Component comparison
    ax = axes[1]
    colors_cycle = plt.cm.tab10.colors
    for i, (name, data) in enumerate(comp_data.items()):
        comp_months = sorted(data.keys())
        comp_x = [months.index(m) for m in comp_months if m in months]
        comp_y = [data[m] for m in comp_months if m in months]
        ax.plot(comp_x, comp_y, linewidth=1.5, color=colors_cycle[i], label=name)
    ax.plot(range(len(months)), [cpi_idx[m] for m in months],
            "k-", linewidth=2.5, label="Overall CPI")
    ax.set_title("CPI by Component (2020 = 100)")
    ax.set_ylabel("Index (2020 = 100)")
    ax.set_xlabel("Month")
    ax.set_xticks(tick_pos)
    ax.set_xticklabels([months[i] for i in tick_pos], rotation=45)
    ax.legend(fontsize=8, ncol=2)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    savefig("10_cpi.png")

    latest_m = months[-1]
    latest_yoy = cpi_yoy.get(latest_m)
    print(f"  CPI index {latest_m}: {cpi_idx[latest_m]:.1f} (2020=100)")
    if latest_yoy:
        print(f"  YoY inflation {latest_m}: {latest_yoy:.2f}%")
    avg_yoy = sum(cpi_yoy.values()) / len(cpi_yoy) if cpi_yoy else 0
    print(f"  Avg YoY inflation (period): {avg_yoy:.2f}%")

    return {"cpi_idx": cpi_idx, "cpi_yoy": cpi_yoy}


# ---------------------------------------------------------------------------
# Analysis 5 – Labor Market
# ---------------------------------------------------------------------------

def analyze_labor(db):
    print("\n[5/5] Labor Market")
    lmi = db[10]

    employed  = obs_to_dict(get_series(lmi, "LE_PE_NUM"))      # thousand persons
    unemp_pt  = obs_to_dict(get_series(lmi, "LEU_PT"))         # unemployment rate %
    wage_m    = obs_to_dict(get_series(lmi, "LME_AVG_XDC"))    # avg monthly wage (thousand VND)
    wage_f    = obs_to_dict(get_series(lmi, "LMEF_AVG_XDC"))
    wage_male = obs_to_dict(get_series(lmi, "LMEM_AVG_XDC"))

    # Annual averages
    emp_a   = quarterly_to_annual_avg(employed)
    unemp_a = quarterly_to_annual_avg(unemp_pt)
    wage_a  = quarterly_to_annual_avg(wage_m)
    wage_f_a   = quarterly_to_annual_avg(wage_f)
    wage_m_a   = quarterly_to_annual_avg(wage_male)

    quarters_emp   = sorted(employed.keys())
    quarters_unemp = sorted(unemp_pt.keys())
    quarters_wage  = sorted(wage_m.keys())

    fig, axes = plt.subplots(3, 1, figsize=(13, 14))
    fig.suptitle("Vietnam – Labor Market Indicators", fontsize=13, fontweight="bold")

    # Employment
    ax = axes[0]
    ax2 = ax.twinx()
    ax.plot(quarters_emp, [employed[q] / 1000 for q in quarters_emp],
            "b-o", linewidth=2, markersize=3, label="Employed (M persons)")
    ax2.plot(quarters_unemp, [unemp_pt.get(q, None) for q in quarters_unemp],
             "r-s", linewidth=2, markersize=3, label="Unemployment rate (%)")
    ax.set_title("Employment Level & Unemployment Rate (Quarterly)")
    ax.set_ylabel("Employed (Million persons)", color="blue")
    ax2.set_ylabel("Unemployment rate (%)", color="red")
    tick_qs = [q for q in quarters_emp if q.endswith("Q1")]
    ax.set_xticks([quarters_emp.index(q) for q in tick_qs if q in quarters_emp])
    ax.set_xticklabels([q[:4] for q in tick_qs if q in quarters_emp], rotation=45)
    ax.grid(True, alpha=0.3)
    lines1, l1 = ax.get_legend_handles_labels()
    lines2, l2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, l1 + l2, loc="lower right")

    # Wage trend
    ax = axes[1]
    if wage_m:
        ax.plot(quarters_wage, [wage_m.get(q, None) for q in quarters_wage],
                "g-o", linewidth=2, markersize=3, label="Overall")
        if wage_f:
            ax.plot([q for q in quarters_wage if q in wage_f],
                    [wage_f[q] for q in quarters_wage if q in wage_f],
                    "r--s", linewidth=1.5, markersize=3, label="Female")
        if wage_male:
            ax.plot([q for q in quarters_wage if q in wage_male],
                    [wage_male[q] for q in quarters_wage if q in wage_male],
                    "b--^", linewidth=1.5, markersize=3, label="Male")
        ax.set_title("Average Monthly Wage (Thousand VND)")
        ax.set_ylabel("Thousand VND / month")
        tick_qs_w = [q for q in quarters_wage if q.endswith("Q1")]
        ax.set_xticks([quarters_wage.index(q) for q in tick_qs_w if q in quarters_wage])
        ax.set_xticklabels([q[:4] for q in tick_qs_w if q in quarters_wage], rotation=45)
        ax.legend()
        ax.grid(True, alpha=0.3)
    else:
        ax.text(0.5, 0.5, "No wage data available", ha="center", va="center",
                transform=ax.transAxes)

    # Gender wage gap (annual)
    ax = axes[2]
    common_yrs = sorted(set(wage_f_a.keys()) & set(wage_m_a.keys()))
    if common_yrs:
        gap = [wage_m_a[y] / wage_f_a[y] * 100 - 100 for y in common_yrs]
        ax.bar(common_yrs, gap, color="#9467bd", alpha=0.75)
        ax.axhline(0, color="black", linewidth=0.8)
        ax.set_title("Gender Wage Gap: Male Premium over Female (%, annual avg)")
        ax.set_ylabel("Male wage premium (%)")
        ax.set_xlabel("Year")
        ax.tick_params(axis='x', rotation=45)
        ax.grid(True, alpha=0.3, axis="y")
        for i, (yr, v) in enumerate(zip(common_yrs, gap)):
            ax.text(yr, v + 0.1, f"{v:.1f}%", ha="center", fontsize=8)
    else:
        ax.text(0.5, 0.5, "Insufficient wage data for gender gap", ha="center", va="center",
                transform=ax.transAxes)

    plt.tight_layout()
    savefig("11_labor.png")

    latest_q = sorted(employed.keys())[-1]
    print(f"  Employment {latest_q}: {employed[latest_q]/1000:.2f}M persons")
    latest_u = sorted(unemp_pt.keys())[-1]
    print(f"  Unemployment rate {latest_u}: {unemp_pt[latest_u]:.2f}%")
    if wage_m:
        latest_w = sorted(wage_m.keys())[-1]
        wv = wage_m.get(latest_w)
        if wv:
            print(f"  Avg monthly wage {latest_w}: {wv:.0f}K VND = ${wv/25:.0f}")

    return {"emp_annual": emp_a, "unemp_annual": unemp_a}


# ---------------------------------------------------------------------------
# Analysis 6 – Cross-analysis: GDP growth vs Population growth
# ---------------------------------------------------------------------------

def analyze_cross(gdp_result, e0202_result):
    print("\n[+] Cross-analysis: GDP growth vs Population growth")

    rgdp_growth = gdp_result["rgdp_growth"]
    pop_growth  = e0202_result["growth"]
    pop_years   = e0202_result["years"]

    pop_growth_dict = {str(y): g for y, g in zip(pop_years, pop_growth)}

    common = sorted(set(rgdp_growth.keys()) & set(pop_growth_dict.keys()))
    gdp_g  = [rgdp_growth[y] for y in common]
    pop_g  = [pop_growth_dict[y] for y in common]

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    fig.suptitle("Vietnam – GDP Growth vs Population Growth", fontsize=13, fontweight="bold")

    ax = axes[0]
    ax.scatter(pop_g, gdp_g, c=range(len(common)), cmap="viridis", s=60, zorder=3)
    for i, yr in enumerate(common):
        ax.annotate(yr, (pop_g[i], gdp_g[i]), fontsize=7,
                    xytext=(3, 3), textcoords="offset points")
    # trend line
    if len(pop_g) > 2:
        z = np.polyfit(pop_g, gdp_g, 1)
        p = np.poly1d(z)
        xr = np.linspace(min(pop_g), max(pop_g), 100)
        ax.plot(xr, p(xr), "r--", linewidth=1.5, label=f"Trend (slope={z[0]:.1f})")
    ax.set_xlabel("Population Growth Rate (%)")
    ax.set_ylabel("Real GDP Growth Rate (%)")
    ax.set_title("GDP Growth vs Population Growth (annual)")
    ax.grid(True, alpha=0.3)
    ax.legend()

    ax = axes[1]
    ax2 = ax.twinx()
    ax.plot([int(y) for y in common], gdp_g, "b-o", markersize=4,
            linewidth=2, label="Real GDP growth (%)")
    ax2.plot([int(y) for y in common], pop_g, "r--s", markersize=4,
             linewidth=1.5, label="Population growth (%)")
    ax.set_title("GDP Growth & Population Growth Over Time")
    ax.set_xlabel("Year")
    ax.set_ylabel("Real GDP growth (%)", color="blue")
    ax2.set_ylabel("Population growth (%)", color="red")
    ax.grid(True, alpha=0.3)
    lines1, l1 = ax.get_legend_handles_labels()
    lines2, l2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, l1 + l2, loc="upper right")

    plt.tight_layout()
    savefig("12_gdp_vs_population.png")
    print(f"  Common years for cross-analysis: {common[0]}–{common[-1]}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_economic_analysis(e0202_result=None):
    print("\n" + "=" * 60)
    print("ECONOMIC ANALYSIS (SDMX / NSO archive)")
    print("=" * 60)

    db = load_db()

    gdp_result     = analyze_gdp(db)
    sector_result  = analyze_gdp_sectors(db)
    trade_result   = analyze_trade(db)
    cpi_result     = analyze_cpi(db)
    labor_result   = analyze_labor(db)

    if e0202_result:
        analyze_cross(gdp_result, e0202_result)

    return {
        "gdp":    gdp_result,
        "sector": sector_result,
        "trade":  trade_result,
        "cpi":    cpi_result,
        "labor":  labor_result,
    }


if __name__ == "__main__":
    run_economic_analysis()
