"""
Vietnam Economy – Extra Visualizations (Charts 19–24)
全く新しいデータソースを使った追加チャート。

19: VN Stock Market Indices  (SPI: VN-Index, HNX, VN30)
20: USD/VND Exchange Rate    (EXR: monthly 2015-2025)
21: Industrial Production    (IND: AIP_ISIC4 components monthly)
22: GDP Expenditure Side     (NAG: C+G+I+NX as % of real GDP)
23: Balance of Payments      (BOP6: current account + FDI quarterly)
24: Long-run GDP per Capita  (NAG: NGDP_PA_XDC 1986-2024 w/ Doi Moi annotations)
"""

import json, os, math
from collections import defaultdict
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

BASE = os.path.dirname(__file__)
OUT  = os.path.join(BASE, "output")
os.makedirs(OUT, exist_ok=True)

# ── shared style ──────────────────────────────────────────────────────────────
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.grid":         True,
    "grid.alpha":        0.3,
    "grid.linestyle":    "--",
})

def savefig(name):
    path = os.path.join(OUT, name)
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")

def _safe(v):
    try:
        return float(str(v).replace(" ", ""))
    except Exception:
        return None

def _obs(series):
    return {o["@TIME_PERIOD"]: _safe(o["@OBS_VALUE"])
            for o in series.get("Obs", [])
            if _safe(o["@OBS_VALUE"]) is not None}

def _get(domain, indicator, freq=None):
    for s in domain:
        if not isinstance(s, dict):
            continue
        if s.get("@INDICATOR") == indicator:
            if freq is None or s.get("@FREQ") == freq:
                return s
    return None


# ── load database ─────────────────────────────────────────────────────────────
def load_db():
    path = os.path.join(BASE, "extracted_database.json")
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    # raw is list of groups; each group is a list of series dicts
    groups = {}
    for group in raw:
        if not isinstance(group, list):
            continue
        for s in group:
            if not isinstance(s, dict):
                continue
            dom = s.get("@DATA_DOMAIN")
            if dom:
                groups.setdefault(dom, []).append(s)
    return groups


# ── Chart 19: VN Stock Market Indices ────────────────────────────────────────
def chart19_stock_market(spi):
    """VN-Index, HNX-Index, VN30 monthly closing prices (2003-2025)."""
    vn_s  = _get(spi, "VNM_VN_EOP_IX")
    hnx_s = _get(spi, "VNM_HNX_EOP_IX")
    vn30_s= _get(spi, "VNM_VN30_EOP_IX")

    def monthly_xy(series):
        if series is None:
            return [], []
        d = _obs(series)
        pairs = sorted(d.items())
        xs = [p for p, _ in pairs]
        ys = [v for _, v in pairs]
        return xs, ys

    vn_x,  vn_y  = monthly_xy(vn_s)
    hnx_x, hnx_y = monthly_xy(hnx_s)
    v30_x, v30_y = monthly_xy(vn30_s)

    # Convert YYYY-MM strings to numeric for plotting
    def to_num(s):
        y, m = int(s[:4]), int(s[5:7])
        return y + (m - 0.5) / 12

    vn_xn  = [to_num(x) for x in vn_x]
    hnx_xn = [to_num(x) for x in hnx_x]
    v30_xn = [to_num(x) for x in v30_x]

    fig, axes = plt.subplots(2, 1, figsize=(13, 9),
                             gridspec_kw={"height_ratios": [3, 1.4]})
    fig.suptitle("Vietnam Stock Market Indices (Monthly Close, Base = 100)",
                 fontsize=14, fontweight="bold", y=1.01)

    ax = axes[0]
    ax.plot(vn_xn,  vn_y,  color="#1f77b4", lw=1.5, label="VN-Index (HOSE)")
    ax.plot(hnx_xn, hnx_y, color="#ff7f0e", lw=1.2, label="HNX-Index")
    ax.plot(v30_xn, v30_y, color="#2ca02c", lw=1.2, ls="--", label="VN30 (top-30 blue chips)")
    ax.set_ylabel("Index level (pts)")
    ax.legend(loc="upper left")

    # Annotate key events
    events = [
        (2007.5,  "Bull run\n2007"),
        (2008.6,  "GFC crash"),
        (2012.5,  "Recovery"),
        (2020.3,  "COVID\ncrash"),
        (2021.75, "Post-COVID\nboom"),
        (2022.4,  "Rate-hike\ncrash"),
    ]
    ylim_top = max(max(vn_y), max(hnx_y)) * 1.15
    ax.set_ylim(0, ylim_top)
    for xv, label in events:
        if xv < min(vn_xn) or xv > max(vn_xn):
            continue
        ax.axvline(xv, color="gray", lw=0.8, ls=":")
        ax.text(xv + 0.05, ylim_top * 0.92, label, fontsize=7.5,
                color="gray", va="top")

    # Bottom panel: YoY % change for VN-Index
    ax2 = axes[1]
    if len(vn_xn) > 12:
        yoy_x = vn_xn[12:]
        yoy_y = [(vn_y[i] / vn_y[i - 12] - 1) * 100
                 for i in range(12, len(vn_y))]
        colors_bar = ["#d62728" if v < 0 else "#2ca02c" for v in yoy_y]
        ax2.bar(yoy_x, yoy_y, width=0.07, color=colors_bar, alpha=0.7)
        ax2.axhline(0, color="black", lw=0.8)
        ax2.set_ylabel("VN-Index YoY %")
        ax2.yaxis.set_major_formatter(mticker.PercentFormatter())

    for ax_ in axes:
        ax_.set_xlim(min(vn_xn) - 0.2, max(vn_xn) + 0.2)
        ax_.xaxis.set_major_formatter(mticker.FuncFormatter(
            lambda v, _: str(int(v)) if v == int(v) else ""))
        ax_.xaxis.set_major_locator(mticker.MultipleLocator(2))

    plt.tight_layout()
    savefig("19_stock_market.png")


# ── Chart 20: USD/VND Exchange Rate ──────────────────────────────────────────
def chart20_exchange_rate(exr):
    """USD/VND monthly mid-rate and annual depreciation 2015-2025."""
    end_s = _get(exr, "ENDE_MID_XDC_USD_RATE")
    avg_s = _get(exr, "ENDA_MID_XDC_USD_RATE")

    def xy(s):
        if s is None:
            return [], []
        d = _obs(s)
        pairs = sorted(d.items())
        return [p for p, _ in pairs], [v for _, v in pairs]

    end_x, end_y = xy(end_s)
    avg_x, avg_y = xy(avg_s)

    def to_num(s):
        y, m = int(s[:4]), int(s[5:7])
        return y + (m - 0.5) / 12

    end_xn = [to_num(x) for x in end_x]
    avg_xn = [to_num(x) for x in avg_x]

    fig, axes = plt.subplots(2, 1, figsize=(13, 8),
                             gridspec_kw={"height_ratios": [3, 1.3]})
    fig.suptitle("USD/VND Exchange Rate (Monthly, VND per USD)",
                 fontsize=14, fontweight="bold")

    ax = axes[0]
    ax.plot(end_xn, end_y, color="#1f77b4", lw=1.5, label="End-of-period rate")
    ax.plot(avg_xn, avg_y, color="#ff7f0e", lw=1.2, ls="--", label="Period average")
    ax.set_ylabel("VND / 1 USD")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda v, _: f"{v:,.0f}"))
    ax.legend(loc="upper left")

    # Annotate key events
    key_events = [
        (2020.3,  "COVID\nshock"),
        (2022.5,  "Fed\nhike cycle"),
        (2023.1,  "VND\nstabilises"),
    ]
    ymin, ymax = ax.get_ylim()
    for xv, label in key_events:
        if xv < min(end_xn) or xv > max(end_xn):
            continue
        ax.axvline(xv, color="gray", lw=0.8, ls=":")
        ax.text(xv + 0.05, ymax * 0.98, label, fontsize=8,
                color="gray", va="top")

    # Bottom: annual depreciation %
    ax2 = axes[1]
    if len(avg_xn) > 12:
        dep_x = avg_xn[12:]
        dep_y = [(avg_y[i] / avg_y[i - 12] - 1) * 100
                 for i in range(12, len(avg_y))]
        colors_bar = ["#d62728" if v > 0 else "#2ca02c" for v in dep_y]
        ax2.bar(dep_x, dep_y, width=0.07, color=colors_bar, alpha=0.7)
        ax2.axhline(0, color="black", lw=0.8)
        ax2.set_ylabel("YoY depreciation %\n(+ = VND weaker)")
        ax2.yaxis.set_major_formatter(mticker.PercentFormatter())

    for ax_ in axes:
        ax_.set_xlim(min(end_xn) - 0.2, max(end_xn) + 0.5)
        ax_.xaxis.set_major_formatter(mticker.FuncFormatter(
            lambda v, _: str(int(v)) if v == int(v) else ""))
        ax_.xaxis.set_major_locator(mticker.MultipleLocator(1))

    plt.tight_layout()
    savefig("20_exchange_rate.png")


# ── Chart 21: Industrial Production Index ────────────────────────────────────
def chart21_industrial_production(ind):
    """Monthly industrial production index by ISIC4 sector 2017-2025."""
    series_map = {
        "Total Industry":  "AIP_ISIC4_IX",
        "Mining (B)":      "AIP_ISIC4_B_IX",
        "Manufacturing (C)": "AIP_ISIC4_C_IX",
        "Electricity (D)": "AIP_ISIC4_D_IX",
        "Water/Waste (E)": "AIP_ISIC4_E_IX",
    }
    colors = ["#1f77b4", "#8c564b", "#ff7f0e", "#2ca02c", "#9467bd"]

    def to_num(s):
        y, m = int(s[:4]), int(s[5:7])
        return y + (m - 0.5) / 12

    fig, axes = plt.subplots(2, 1, figsize=(13, 9),
                             gridspec_kw={"height_ratios": [3, 1.6]})
    fig.suptitle("Industrial Production Index by Sector (Monthly, ISIC4, 2017=100)",
                 fontsize=14, fontweight="bold")

    ax = axes[0]
    all_data = {}
    for (label, ind_code), color in zip(series_map.items(), colors):
        s = _get(ind, ind_code)
        if s is None:
            continue
        d = _obs(s)
        pairs = sorted(d.items())
        xs = [to_num(p) for p, _ in pairs]
        ys = [v for _, v in pairs]
        all_data[label] = (xs, ys)
        lw = 2.0 if "Total" in label else 1.2
        alpha = 1.0 if "Total" in label else 0.75
        ls = "-" if "Total" in label or "Manufacturing" in label else "--"
        ax.plot(xs, ys, color=color, lw=lw, ls=ls, alpha=alpha, label=label)

    ax.set_ylabel("Index (2017 = 100)")
    ax.legend(loc="upper left", fontsize=9)

    # Annotate COVID
    ax.axvspan(2020.0, 2021.75, color="gray", alpha=0.12, label="COVID disruption")
    ax.text(2020.3, ax.get_ylim()[1] * 0.95, "COVID\ndisruption",
            fontsize=8, color="gray", va="top")

    # Bottom: 12M rolling YoY of total industry
    ax2 = axes[1]
    if "Total Industry" in all_data:
        xs, ys = all_data["Total Industry"]
        if len(xs) > 12:
            yoy_x = xs[12:]
            yoy_y = [(ys[i] / ys[i - 12] - 1) * 100
                     for i in range(12, len(ys))]
            colors_bar = ["#d62728" if v < 0 else "#1f77b4" for v in yoy_y]
            ax2.bar(yoy_x, yoy_y, width=0.07, color=colors_bar, alpha=0.75)
            ax2.axhline(0, color="black", lw=0.8)
            ax2.set_ylabel("Total Industry\nYoY %")
            ax2.yaxis.set_major_formatter(mticker.PercentFormatter())

    for ax_ in axes:
        ax_.xaxis.set_major_formatter(mticker.FuncFormatter(
            lambda v, _: str(int(v)) if v == int(v) else ""))
        ax_.xaxis.set_major_locator(mticker.MultipleLocator(1))

    plt.tight_layout()
    savefig("21_industrial_production.png")


# ── Chart 22: GDP Expenditure Decomposition ──────────────────────────────────
def chart22_gdp_expenditure(nag):
    """Real GDP by expenditure: private C / government G / investment I / net exports NX."""
    gdp_s = _get(nag, "NGDP_R_XDC", freq="A")
    cp_s  = _get(nag, "NCP_R_XDC",  freq="A")   # private consumption
    cg_s  = _get(nag, "NCGG_R_XDC", freq="A")   # government consumption
    fi_s  = _get(nag, "NFI_R_XDC",  freq="A")   # gross fixed investment
    nx_s  = _get(nag, "NNXGS_R_XDC",freq="A")   # net exports of G&S

    if not all([gdp_s, cp_s, fi_s, nx_s]):
        print("  [chart22] missing series, skipping")
        return

    gdp = _obs(gdp_s)
    cp  = _obs(cp_s)
    cg  = _obs(cg_s) if cg_s else {}
    fi  = _obs(fi_s)
    nx  = _obs(nx_s)

    years = sorted(set(gdp) & set(cp) & set(fi) & set(nx))
    # NFI_R_XDC only available from 2010 (2010 constant prices); drop zero/missing years
    years = [y for y in years if y >= "2010" and fi.get(y, 0) > 0]

    def pct(d, years):
        return [d.get(y, 0) / gdp[y] * 100 if gdp.get(y) else 0 for y in years]

    cp_pct  = pct(cp, years)
    cg_pct  = pct(cg, years)
    fi_pct  = pct(fi, years)
    nx_pct  = pct(nx, years)
    xvals   = [int(y) for y in years]

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("GDP Expenditure Decomposition – Real, % of Real GDP (2010–2024)",
                 fontsize=14, fontweight="bold")

    # Left: stacked area
    ax = axes[0]
    bottom = np.zeros(len(years))
    components = [
        ("Private Consumption", cp_pct,  "#1f77b4"),
        ("Gov. Consumption",    cg_pct,  "#aec7e8"),
        ("Gross Fixed Invest.", fi_pct,  "#ff7f0e"),
    ]
    for label, vals, color in components:
        arr = np.array(vals)
        ax.fill_between(xvals, bottom, bottom + arr, alpha=0.8,
                        color=color, label=label)
        bottom += arr

    ax.set_ylabel("% of Real GDP")
    ax.set_title("Positive components (C + G + I)")
    ax.legend(loc="lower right", fontsize=9)
    ax.set_xlim(xvals[0], xvals[-1])
    ax.yaxis.set_major_formatter(mticker.PercentFormatter())

    # Right: NX + Investment rate time series
    ax2 = axes[1]
    ax2.plot(xvals, nx_pct, color="#d62728", lw=2, label="Net Exports (NX % GDP)")
    ax2.plot(xvals, fi_pct, color="#ff7f0e", lw=2, label="Gross Fixed Invest. % GDP")
    ax2.plot(xvals, cp_pct, color="#1f77b4", lw=1.5, ls="--", label="Private Cons. % GDP")
    ax2.axhline(0, color="black", lw=0.8)
    ax2.set_ylabel("% of Real GDP")
    ax2.set_title("Key ratios over time")
    ax2.legend(loc="center right", fontsize=9)
    ax2.set_xlim(xvals[0], xvals[-1])
    ax2.yaxis.set_major_formatter(mticker.PercentFormatter())

    for ax_ in axes:
        ax_.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
        ax_.xaxis.set_major_formatter(mticker.FuncFormatter(
            lambda v, _: str(int(v))))

    plt.tight_layout()
    savefig("22_gdp_expenditure.png")


# ── Chart 23: Balance of Payments ────────────────────────────────────────────
def chart23_balance_of_payments(bop6):
    """Current account, FDI inflows/outflows quarterly (2012-2021)."""
    ca_s   = _get(bop6, "VNM_BCA_BP6_USD")       # current account balance
    fdi_a_s= _get(bop6, "VNM_BFDA_BP6_USD")      # FDI assets (outward)
    fdi_l_s= _get(bop6, "VNM_BFDL_BP6_USD")      # FDI liabilities (inward FDI)
    xg_s   = _get(bop6, "VNM_BXG_BP6_USD")       # goods exports (BOP basis)
    mg_s   = _get(bop6, "VNM_BMG_BP6_USD")       # goods imports (BOP basis)

    def to_num(s):
        # "2012-Q1" -> 2012.125
        y, q = s.split("-Q")
        return int(y) + (int(q) - 0.5) / 4

    def xy_q(series):
        if series is None:
            return [], []
        d = _obs(series)
        pairs = sorted(d.items())
        xs = [to_num(p) for p, _ in pairs]
        ys = [v for _, v in pairs]
        return xs, ys

    ca_x,    ca_y    = xy_q(ca_s)
    fdia_x,  fdia_y  = xy_q(fdi_a_s)
    fdil_x,  fdil_y  = xy_q(fdi_l_s)
    xg_x,    xg_y    = xy_q(xg_s)
    mg_x,    mg_y    = xy_q(mg_s)

    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.suptitle("Balance of Payments – Quarterly (USD Millions, 2012–2021)",
                 fontsize=14, fontweight="bold")

    # Top-left: Current account balance
    ax = axes[0][0]
    colors_bar = ["#2ca02c" if v >= 0 else "#d62728" for v in ca_y]
    ax.bar(ca_x, ca_y, width=0.2, color=colors_bar, alpha=0.8)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_title("Current Account Balance (USD M)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda v, _: f"{v/1000:.1f}B"))

    # Top-right: Inward FDI (FDI liabilities)
    ax = axes[0][1]
    ax.bar(fdil_x, fdil_y, width=0.2, color="#ff7f0e", alpha=0.8,
           label="Inward FDI (liabilities)")
    if fdia_y:
        ax.bar(fdia_x, [-v for v in fdia_y], width=0.2, color="#1f77b4",
               alpha=0.6, label="Outward FDI (assets, neg.)")
    ax.axhline(0, color="black", lw=0.8)
    ax.set_title("FDI Flows (USD M)")
    ax.legend(fontsize=8)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda v, _: f"{v/1000:.1f}B"))

    # Bottom-left: Goods trade (BOP basis)
    ax = axes[1][0]
    if xg_y and mg_y:
        tb_y = [x + m for x, m in zip(xg_y, mg_y)]  # mg is negative in BOP
        ax.plot(xg_x, xg_y, color="#2ca02c", lw=1.5, label="Goods Exports")
        ax.plot(mg_x, [-v for v in mg_y], color="#d62728", lw=1.5,
                label="Goods Imports (abs)")
        ax.fill_between(xg_x, [0]*len(xg_x), tb_y, alpha=0.2,
                        color="#ff7f0e", label="Trade Balance")
        ax.axhline(0, color="black", lw=0.8)
        ax.set_title("Goods Trade (BOP basis, USD M)")
        ax.legend(fontsize=8)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(
            lambda v, _: f"{v/1000:.0f}B"))

    # Bottom-right: CA + FDI combined (sustainability check)
    ax = axes[1][1]
    if ca_y and fdil_y:
        common_x = sorted(set(ca_x) & set(fdil_x))
        ca_map   = dict(zip(ca_x, ca_y))
        fdi_map  = dict(zip(fdil_x, fdil_y))
        cx  = common_x
        cy  = [ca_map[x] for x in cx]
        fy  = [fdi_map[x] for x in cx]
        net = [c + f for c, f in zip(cy, fy)]
        ax.plot(cx, [v/1000 for v in cy], color="#1f77b4", lw=1.5,
                label="Current Account")
        ax.plot(cx, [v/1000 for v in fy], color="#ff7f0e", lw=1.5,
                label="Inward FDI")
        ax.fill_between(cx, [v/1000 for v in net], 0, alpha=0.2,
                        color="#2ca02c", label="CA + FDI net")
        ax.axhline(0, color="black", lw=0.8)
        ax.set_title("Current Account + Inward FDI (USD B)")
        ax.legend(fontsize=8)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(
            lambda v, _: f"{v:.1f}B"))

    for row in axes:
        for ax_ in row:
            ax_.xaxis.set_major_formatter(mticker.FuncFormatter(
                lambda v, _: str(int(v)) if abs(v - round(v)) < 0.01 else ""))
            ax_.xaxis.set_major_locator(mticker.MultipleLocator(1))

    plt.tight_layout()
    savefig("23_balance_of_payments.png")


# ── Chart 24: Long-run GDP per Capita since 2000 ─────────────────────────────
def chart24_longrun_gdp_percapita(nag):
    """Nominal & real GDP per capita 2000-2024 with era CAGR annotations.

    Computed as: NGDP_XDC (nominal, mult=9) / population from E02.02.
    NGDP_PA_XDC == NGDP_XDC in this dataset (population not embedded).
    """
    import json as _json

    # Load nominal GDP (mult=9 → multiply by 10^9 to get VND)
    ngdp_s = _get(nag, "NGDP_XDC", freq="A")
    rgdp_s = _get(nag, "NGDP_R_XDC", freq="A")   # real (constant 2010 prices)
    if ngdp_s is None:
        print("  [chart24] NGDP_XDC not found, skipping")
        return

    ngdp_raw = _obs(ngdp_s)  # values already in T VND (mult=9 → ×10^9, but
                              # raw values ~11.5M for 2024 → ×10^9 = 11.5×10^15 VND)
    rgdp_raw = _obs(rgdp_s) if rgdp_s else {}

    # Load population from E02.02.json (in thousands)
    e0202_path = os.path.join(BASE, "E02.02.json")
    pop_by_year = {}
    if os.path.exists(e0202_path):
        with open(e0202_path, encoding="utf-8") as f:
            content = f.read().rstrip("\x00").strip()
        ds = _json.loads(content)["dataset"]
        labels  = ds["dimension"]["Items"]["category"]["label"]
        yr_lbl  = ds["dimension"]["Year"]["category"]["label"]
        sr_lbl  = ds["dimension"]["Sex, residence"]["category"]["label"]
        items   = list(labels.values())
        years_e = list(yr_lbl.values())
        sr_list = list(sr_lbl.values())
        vals_e  = ds["value"]
        n_yr = len(years_e); n_sr = len(sr_list)
        # Find "Total" item and "Total" sex/residence
        total_item_idx = next((i for i, v in enumerate(items) if "Total" in v), 0)
        total_sr_idx   = next((i for i, v in enumerate(sr_list) if v == "Total"), 0)
        for yi, yr in enumerate(years_e):
            flat_idx = total_item_idx * n_yr * n_sr + yi * n_sr + total_sr_idx
            if flat_idx < len(vals_e) and vals_e[flat_idx] is not None:
                yr_clean = yr.replace("Prel. ", "").strip()
                pop_by_year[yr_clean] = vals_e[flat_idx]  # in thousands

    if not pop_by_year:
        print("  [chart24] population data not available, skipping")
        return

    # Compute per capita GDP in million VND per person
    # NGDP raw val × 10^9 VND / (pop_thousands × 1000 persons) = val × 10^6 VND/person
    # → divide by 1e6 to get million VND per person
    # per_capita_MVND = ngdp_raw_val × 10^9 / (pop_thousands × 1000) / 1e6
    #                 = ngdp_raw_val / pop_thousands × 1e3  (M VND/person? let's check)
    # 2024: 11,511,867 / 101,400 × 1e3 = 113.5 × 1e3 M VND → too big
    # Correct: ngdp_raw × 1e9 VND / (pop_th × 1e3) = ngdp_raw/pop_th × 1e6 VND/person
    #        / 1e6 = ngdp_raw/pop_th  M VND/person
    # 2024: 11,511,867 / 101,400 = 113.5 M VND/person ✓

    common_years = sorted(set(ngdp_raw) & set(pop_by_year))
    years_int = [int(y) for y in common_years]
    nom_pc    = [ngdp_raw[y] / pop_by_year[y] for y in common_years]  # M VND/person

    # Real per capita (same approach, skip base-year break 2009→2010)
    real_pc_map = {}
    if rgdp_raw and pop_by_year:
        for y in rgdp_raw:
            if y in pop_by_year:
                real_pc_map[y] = rgdp_raw[y] / pop_by_year[y]
    real_years = sorted(real_pc_map)
    real_vals  = [real_pc_map[y] for y in real_years]
    real_xvals = [int(y) for y in real_years]

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("Vietnam GDP per Capita (2000–2024)",
                 fontsize=14, fontweight="bold")

    # Left: nominal GDP per capita (M VND/person)
    ax = axes[0]
    ax.fill_between(years_int, nom_pc, alpha=0.25, color="#1f77b4")
    ax.plot(years_int, nom_pc, color="#1f77b4", lw=2, label="Nominal GDP per capita")
    ax.set_ylabel("Million VND / person")
    ax.set_title("Nominal GDP per Capita (M VND)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda v, _: f"{v:.0f}M"))

    # Secondary: approx USD (using 2024 rate ~25,000 VND/USD for scale)
    ax_r = ax.twinx()
    ax_r.set_ylim(ax.get_ylim()[0] / 25, ax.get_ylim()[1] / 25)
    ax_r.set_ylabel("Approx. USD (at 25,000 VND/USD)")
    ax_r.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda v, _: f"${v*1000:,.0f}"))
    ax_r.spines["right"].set_visible(True)

    annotations = [
        (2000, "Bilateral\ntrade with US", 0.12),
        (2007, "WTO\naccession",           0.28),
        (2020, "COVID-19",                 0.70),
    ]
    ymax = max(nom_pc) * 1.15
    ax.set_ylim(0, ymax)
    for xv, label, yfrac in annotations:
        if xv < years_int[0] or xv > years_int[-1]:
            continue
        ax.axvline(xv, color="gray", lw=0.8, ls=":")
        ax.text(xv + 0.3, ymax * yfrac, label, fontsize=7.5,
                color="#444", va="bottom")

    # Right: log-scale real per capita with CAGR eras
    ax2 = axes[1]
    ax2.semilogy(real_xvals, real_vals, color="#ff7f0e", lw=2,
                 marker="o", markersize=3, label="Real GDP/capita (const. 2010)")

    first_real_yr = real_xvals[0] if real_xvals else 2004
    eras = [
        (first_real_yr, 2007, "#2ca02c",  f"Pre-WTO\n{first_real_yr}–07"),
        (2007, 2019,          "#1f77b4",  "Post-WTO\n2007–19"),
        (2019, 2024,          "#d62728",  "COVID era\n2019–24"),
    ]
    for x0, x1, color, era_label in eras:
        if x0 < real_xvals[0] or x1 > real_xvals[-1]:
            continue
        v0 = real_pc_map.get(str(x0))
        v1 = real_pc_map.get(str(x1))
        if v0 and v1 and v0 > 0:
            cagr = (v1 / v0) ** (1 / (x1 - x0)) - 1
            mid  = (x0 + x1) / 2
            y_mid = (v0 * v1) ** 0.5   # geometric midpoint for log scale
            ax2.axvspan(x0, x1, alpha=0.10, color=color)
            ax2.text(mid, y_mid * 1.05,
                     f"{era_label}\nCAGR {cagr*100:.1f}%/yr",
                     fontsize=8, ha="center", color=color,
                     fontweight="bold", va="bottom")

    ax2.set_ylabel("M VND / person (log scale, const. 2010 prices)")
    ax2.set_title("Real GDP per Capita – Growth by Era (Log Scale)")

    for ax_ in [ax, ax2]:
        ax_.set_xlim(years_int[0] - 0.5, years_int[-1] + 0.5)
        ax_.xaxis.set_major_locator(mticker.MultipleLocator(5))

    plt.tight_layout()
    savefig("24_longrun_gdp_percapita.png")


# ── Entry point ───────────────────────────────────────────────────────────────
def run_extra_visualizations():
    print("\n[Charts 19–24] Extra Visualizations")
    groups = load_db()
    spi  = groups.get("SPI", [])
    exr  = groups.get("EXR", [])
    ind  = groups.get("IND", [])
    nag  = groups.get("NAG", [])
    bop6 = groups.get("BOP6", [])

    print("Chart 19: VN Stock Market Indices …")
    chart19_stock_market(spi)

    print("Chart 20: USD/VND Exchange Rate …")
    chart20_exchange_rate(exr)

    print("Chart 21: Industrial Production Index …")
    chart21_industrial_production(ind)

    print("Chart 22: GDP Expenditure Decomposition …")
    chart22_gdp_expenditure(nag)

    print("Chart 23: Balance of Payments …")
    chart23_balance_of_payments(bop6)

    print("Chart 24: Long-run GDP per Capita …")
    chart24_longrun_gdp_percapita(nag)


if __name__ == "__main__":
    run_extra_visualizations()
