"""
Vietnam Economy – Extended Visualizations (Charts 13–18)
追加チャートモジュール。analyze.py から呼び出される。
"""

import json, os, math
from collections import defaultdict
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import numpy as np

BASE = os.path.dirname(__file__)
OUT  = os.path.join(BASE, "output")
os.makedirs(OUT, exist_ok=True)

def savefig(name):
    path = os.path.join(OUT, name)
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")

def _safe(v):
    try:
        return float(str(v).replace(" ", ""))
    except:
        return None

def _obs(series):
    return {o["@TIME_PERIOD"]: _safe(o["@OBS_VALUE"])
            for o in series.get("Obs", [])
            if _safe(o["@OBS_VALUE"]) is not None}

def _get(domain, indicator, freq=None):
    for s in domain:
        if s.get("@INDICATOR") == indicator:
            if freq is None or s.get("@FREQ") == freq:
                return s
    return None

def _annual_sum(monthly_dict):
    d = defaultdict(float)
    for p, v in monthly_dict.items():
        d[p[:4]] += v
    return dict(d)

def _annual_avg(qdict):
    s, c = defaultdict(float), defaultdict(int)
    for p, v in qdict.items():
        s[p[:4]] += v; c[p[:4]] += 1
    return {y: s[y]/c[y] for y in s}

# ─────────────────────────────────────────────────────────────────────────────
# Chart 13 – Annotated GDP Growth Timeline
# ─────────────────────────────────────────────────────────────────────────────
def chart13_gdp_annotated(db):
    """GDP成長率タイムライン（歴史的イベント注記付き）.
    NOTE: NGDP_R_XDC series has a base-year break between 2009 (1994 prices)
    and 2010 (2010 prices). The 2009→2010 transition is excluded from growth
    calculation; a divider line marks the base-year change.
    """
    print("\n[13] Annotated GDP growth timeline")
    nag = db[0]
    rgdp = _obs(_get(nag, "NGDP_R_XDC", freq="A"))
    yrs  = sorted(rgdp)

    # Compute YoY growth, EXCLUDING the base-year break (2009→2010)
    growth = {}
    for i in range(1, len(yrs)):
        if yrs[i-1] == "2009" and yrs[i] == "2010":
            continue   # skip structural break
        p, c = rgdp[yrs[i-1]], rgdp[yrs[i]]
        if p:
            growth[yrs[i]] = (c / p - 1) * 100

    gyrs  = sorted(growth)
    gvals = [growth[y] for y in gyrs]

    # Historical events (year → label, position)
    events = {
        "2007": ("WTO\nAccession", "top"),
        "2008": ("Global\nFinancial\nCrisis", "bottom"),
        "2011": ("Monetary\nTightening", "bottom"),
        "2016": ("El Niño\nDrought", "bottom"),
        "2020": ("COVID-19", "bottom"),
        "2021": ("Delta\nVariant", "bottom"),
        "2022": ("Strong\nRecovery", "top"),
    }

    fig, ax = plt.subplots(figsize=(16, 7))
    bar_colors = ["#d62728" if v < 5 else "#1f77b4" for v in gvals]
    ax.bar(gyrs, gvals, color=bar_colors, alpha=0.75, zorder=2, width=0.7)
    ax.plot(gyrs, gvals, "ko-", linewidth=1.5, markersize=4, zorder=3)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.axhline(6, color="#2ca02c", linewidth=1.3, linestyle="--", alpha=0.8, label="6% level")
    ax.fill_between(gyrs, 6, [max(v, 6) for v in gvals],
                    alpha=0.10, color="#2ca02c", label="≥6% zone")
    ax.fill_between(gyrs, [min(v, 5) for v in gvals], 5,
                    alpha=0.10, color="#d62728", label="<5% zone")

    # Event annotations
    for yr, (label, pos) in events.items():
        if yr not in growth:
            continue
        v = growth[yr]
        dy = 3.0 if pos == "top" else -3.5
        ax.annotate(label,
                    xy=(yr, v), xytext=(yr, v + dy),
                    ha="center", va="bottom" if pos == "top" else "top",
                    fontsize=7.5,
                    arrowprops=dict(arrowstyle="-|>", color="#666", lw=0.9, mutation_scale=8),
                    bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#bbb", alpha=0.9))

    # Value labels
    for yr, v in zip(gyrs, gvals):
        ax.text(yr, v + (0.15 if v >= 0 else -0.3),
                f"{v:.1f}%", ha="center",
                va="bottom" if v >= 0 else "top",
                fontsize=7, fontweight="bold")

    # Shaded eras
    ax.axvspan("2007", "2009", alpha=0.06, color="red")
    ax.axvspan("2020", "2021", alpha=0.08, color="gray")

    # Base-year break marker between 2009 and 2011 data
    ax.axvline(x="2010", color="purple", linewidth=1.5, linestyle=":", alpha=0.7)
    ax.text("2010", ax.get_ylim()[1] * 0.92,
            "Base-year\nchange\n(1994→2010 prices)",
            ha="center", va="top", fontsize=7, color="purple",
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="purple", alpha=0.8))

    ax.set_title("Vietnam – Real GDP Growth Rate & Historical Events (2005–2024)",
                 fontsize=13, fontweight="bold", pad=12)
    ax.set_ylabel("Real GDP Growth Rate (%)", fontsize=11)
    ax.set_xlabel("Year", fontsize=11)
    ax.set_ylim(min(gvals) - 2.5, max(gvals) + 5.5)
    ax.tick_params(axis="x", rotation=45)
    ax.grid(True, alpha=0.3, axis="y", zorder=0)
    ax.legend(fontsize=9, loc="upper left")

    plt.tight_layout()
    savefig("13_gdp_growth_annotated.png")

    valid = [v for v in gvals if v < 20]   # exclude break artefacts
    print(f"  Avg growth (excl. break): {sum(valid)/len(valid):.1f}%"
          f"  Min: {min(valid):.1f}%  Max: {max(valid):.1f}%")

# ─────────────────────────────────────────────────────────────────────────────
# Chart 14 – Export Commodity Structure
# ─────────────────────────────────────────────────────────────────────────────
def chart14_export_structure(db):
    """輸出品目構成：積み上げ棒（年次推移）＋最新年パイチャート."""
    print("\n[14] Export commodity structure")
    met = db[7]

    # Non-overlapping top-level export categories (HS codes)
    CATS = {
        "Electronics &\nElec. Equipment (HS85)":   "TXG_H5_85_FOB_USD",
        "Machinery &\nTransport (HS84T86)":         "TXG_H5_84T86_FOB_USD",
        "Apparel &\nTextiles (HS61-63)":            "TXG_H5_63_61_FOB_USD",
        "Footwear (HS64)":                           "TXG_H5_64_FOB_USD",
        "Wood & Wood\nProducts (HS44)":              "TXG_H5_44_FOB_USD",
        "Seafood (HS03)":                            "TXG_H5_03_FOB_USD",
        "Rubber (HS40)":                             "TXG_H5_40_FOB_USD",
        "Coffee &\nPepper (HS09)":                  "TXG_H5_0901_FOB_USD",
        "Rice (HS10)":                               "TXG_H5_1006_FOB_USD",
        "Plastic &\nChemicals (HS39)":               "TXG_H5_39_FOB_USD",
    }
    CAT_COLORS = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
        "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
    ]

    # Build annual totals per category (million USD)
    from collections import Counter
    cat_annual = {}
    for label, ind in CATS.items():
        s = _get(met, ind)
        if s:
            monthly = _obs(s)
            annual  = _annual_sum(monthly)
            # keep only fully-observed years (12 months)
            month_cnt = Counter(p[:4] for p in monthly)
            cat_annual[label] = {y: v for y, v in annual.items() if month_cnt[y] == 12}

    # Total exports (for "Other" calculation)
    total_s  = _get(met, "TXG_FOB_USD")
    total_monthly = _obs(total_s) if total_s else {}
    total_annual  = _annual_sum(total_monthly)
    month_cnt_tot = Counter(p[:4] for p in total_monthly)
    total_annual  = {y: v for y, v in total_annual.items() if month_cnt_tot[y] == 12}

    years = sorted(set(total_annual) & set(list(cat_annual.values())[0]))

    # "Other" = total − sum of named categories
    other_annual = {}
    for y in years:
        cat_sum = sum(cat_annual[lbl].get(y, 0) for lbl in CATS)
        other_annual[y] = max(total_annual.get(y, 0) - cat_sum, 0)

    # ── Plot ────────────────────────────────────────────────────────────────
    fig = plt.figure(figsize=(18, 8))
    gs  = fig.add_gridspec(1, 3, width_ratios=[2.5, 0.05, 1])
    ax_bar = fig.add_subplot(gs[0])
    ax_pie = fig.add_subplot(gs[2])
    fig.suptitle("Vietnam – Export Commodity Structure (Merchandise Trade)",
                 fontsize=13, fontweight="bold")

    labels_plot = list(CATS.keys()) + ["Other"]
    colors_plot = CAT_COLORS + ["#aaaaaa"]

    # Stacked bar
    bottoms = [0.0] * len(years)
    for i, (label, color) in enumerate(zip(labels_plot, colors_plot)):
        vals = ([(cat_annual[label].get(y, 0) / 1000) for y in years]
                if label != "Other"
                else [other_annual.get(y, 0) / 1000 for y in years])
        ax_bar.bar(years, vals, bottom=bottoms, color=color,
                   alpha=0.85, label=label.replace("\n", " "), width=0.7)
        bottoms = [b + v for b, v in zip(bottoms, vals)]

    ax_bar.set_title("Annual Export by Category (Billion USD)")
    ax_bar.set_ylabel("Billion USD")
    ax_bar.set_xlabel("Year")
    ax_bar.tick_params(axis="x", rotation=45)
    ax_bar.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:.0f}B"))
    ax_bar.grid(True, alpha=0.3, axis="y")
    ax_bar.legend(fontsize=7, loc="upper left", ncol=2)

    # Pie chart for latest year
    latest = years[-1]
    pie_vals  = []
    pie_lbls  = []
    pie_cols  = []
    for label, color in zip(labels_plot, colors_plot):
        v = (cat_annual[label].get(latest, 0)
             if label != "Other"
             else other_annual.get(latest, 0))
        if v > 0:
            pie_vals.append(v)
            pie_lbls.append(label.replace("\n", " "))
            pie_cols.append(color)

    total_pie = sum(pie_vals)
    wedges, texts, autotexts = ax_pie.pie(
        pie_vals,
        labels=None,
        colors=pie_cols,
        autopct=lambda p: f"{p:.1f}%" if p > 3 else "",
        startangle=140,
        pctdistance=0.75,
        wedgeprops=dict(linewidth=0.5, edgecolor="white"),
    )
    for at in autotexts:
        at.set_fontsize(7)
    ax_pie.set_title(f"Export Mix\n{latest}\n(Total=${total_pie/1000:.0f}B)",
                     fontsize=10, fontweight="bold")
    ax_pie.legend(wedges, [l.replace("\n"," ") for l in pie_lbls],
                  fontsize=6.5, loc="lower center",
                  bbox_to_anchor=(0.5, -0.35), ncol=2)

    plt.tight_layout()
    savefig("14_export_structure.png")

    # Summary
    top = sorted([(lbl, cat_annual[lbl].get(latest,0)) for lbl in CATS],
                 key=lambda x: -x[1])
    print(f"  Top export {latest}: {top[0][0].split(chr(10))[0]} = ${top[0][1]/1000:.0f}B "
          f"({top[0][1]/total_annual.get(latest,1)*100:.0f}% of total)")

# ─────────────────────────────────────────────────────────────────────────────
# Chart 15 – Labor Market: Gender Comparison
# ─────────────────────────────────────────────────────────────────────────────
def chart15_labor_gender(db):
    """労働市場の男女比較：労働力・失業・賃金格差."""
    print("\n[15] Labor market gender comparison")
    lmi = db[10]

    # Labor force
    lf_m  = _obs(_get(lmi, "LLFM_PE_NUM"))   # male   (thousand)
    lf_f  = _obs(_get(lmi, "LLFF_PE_NUM"))   # female
    lf    = _obs(_get(lmi, "LLF_PE_NUM"))    # total
    # Unemployment
    lu_m  = _obs(_get(lmi, "LUM_PE_NUM"))
    lu_f  = _obs(_get(lmi, "LUF_PE_NUM"))
    lu    = _obs(_get(lmi, "LU_PE_NUM"))
    # Wages (Q, thousand VND)
    wm    = _obs(_get(lmi, "LMEM_AVG_XDC"))
    wf    = _obs(_get(lmi, "LMEF_AVG_XDC"))
    w     = _obs(_get(lmi, "LME_AVG_XDC"))

    # Annual averages
    lf_m_a  = _annual_avg(lf_m)
    lf_f_a  = _annual_avg(lf_f)
    lu_m_a  = _annual_avg(lu_m)
    lu_f_a  = _annual_avg(lu_f)
    wm_a    = _annual_avg(wm)
    wf_a    = _annual_avg(wf)
    w_a     = _annual_avg(w)

    fig, axes = plt.subplots(1, 3, figsize=(18, 7))
    fig.suptitle("Vietnam – Labor Market: Male vs Female Comparison",
                 fontsize=13, fontweight="bold")

    # ── Panel 1: Labor force by gender (stacked area) ────────────────────
    ax = axes[0]
    yrs = sorted(set(lf_m_a) & set(lf_f_a))
    m_vals = [lf_m_a[y] / 1000 for y in yrs]
    f_vals = [lf_f_a[y] / 1000 for y in yrs]
    ax.stackplot(yrs, m_vals, f_vals,
                 labels=["Male", "Female"],
                 colors=["#1f77b4", "#e377c2"], alpha=0.8)
    # Participation ratio line
    ax2 = ax.twinx()
    ratio = [lf_f_a.get(y, 0) / lf_m_a.get(y, 1) * 100 for y in yrs]
    ax2.plot(yrs, ratio, "k--", linewidth=1.5, label="Female/Male ratio (%)")
    ax2.set_ylim(70, 100)
    ax2.set_ylabel("Female/Male ratio (%)", fontsize=9)
    ax.set_title("Labor Force by Gender (Million persons)")
    ax.set_ylabel("Million persons")
    ax.set_xlabel("Year")
    ax.tick_params(axis="x", rotation=45)
    ax.grid(True, alpha=0.3, axis="y")
    lines1, l1 = ax.get_legend_handles_labels()
    lines2, l2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, l1 + l2, fontsize=8, loc="upper left")

    # ── Panel 2: Unemployment comparison ─────────────────────────────────
    ax = axes[1]
    # quarterly data plotted directly
    q_all = sorted(set(lu_m) & set(lu_f))
    um_q  = [lu_m.get(q, None) for q in q_all]
    uf_q  = [lu_f.get(q, None) for q in q_all]
    ur_m  = [m / (lf_m.get(q, 1) or 1) * 100 if m else None for m, q in zip(um_q, q_all)]
    ur_f  = [f / (lf_f.get(q, 1) or 1) * 100 if f else None for f, q in zip(uf_q, q_all)]
    xs    = range(len(q_all))
    ax.plot(xs, ur_m, "b-", linewidth=1.8, label="Male unemployment rate")
    ax.plot(xs, ur_f, "r-", linewidth=1.8, label="Female unemployment rate")
    ax.fill_between(xs,
                    [m or 0 for m in ur_m],
                    [f or 0 for f in ur_f],
                    alpha=0.15, color="purple",
                    label="Gender gap")
    tick_pos = [i for i, q in enumerate(q_all) if q.endswith("Q1")]
    ax.set_xticks(tick_pos)
    ax.set_xticklabels([q_all[i][:4] for i in tick_pos], rotation=45)
    ax.set_title("Unemployment Rate by Gender (Quarterly)")
    ax.set_ylabel("Unemployment rate (%)")
    ax.set_xlabel("Quarter")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # ── Panel 3: Wage gap over time ───────────────────────────────────────
    ax = axes[2]
    common_w = sorted(set(wm_a) & set(wf_a))
    if common_w:
        gap_pct  = [(wm_a[y] / wf_a[y] - 1) * 100 for y in common_w]
        wm_vals  = [wm_a[y] / 1000 for y in common_w]  # million VND
        wf_vals  = [wf_a[y] / 1000 for y in common_w]

        ax2 = ax.twinx()
        ax.plot(common_w, wm_vals, "b-o", linewidth=2, markersize=5, label="Male wage")
        ax.plot(common_w, wf_vals, "r-o", linewidth=2, markersize=5, label="Female wage")
        ax.fill_between(common_w, wf_vals, wm_vals, alpha=0.15, color="purple",
                        label="Wage gap")
        ax2.bar(common_w, gap_pct, alpha=0.3, color="purple", label="Gap % (M over F)")
        ax.set_title("Average Monthly Wage by Gender\n(Million VND/month, annual avg)")
        ax.set_ylabel("Million VND / month")
        ax2.set_ylabel("Male premium (%)", color="purple")
        ax.set_xlabel("Year")
        ax.tick_params(axis="x", rotation=45)
        ax.grid(True, alpha=0.3)
        lines1, l1 = ax.get_legend_handles_labels()
        lines2, l2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, l1 + l2, fontsize=8, loc="upper left")
    else:
        ax.text(0.5, 0.5, "Insufficient wage data", ha="center", va="center",
                transform=ax.transAxes, fontsize=11)

    plt.tight_layout()
    savefig("15_labor_gender.png")

    latest_lf = sorted(set(lf_m_a) & set(lf_f_a))[-1]
    ratio_latest = lf_f_a[latest_lf] / lf_m_a[latest_lf] * 100
    print(f"  {latest_lf}: Male LF={lf_m_a[latest_lf]/1000:.2f}M, "
          f"Female LF={lf_f_a[latest_lf]/1000:.2f}M, F/M={ratio_latest:.1f}%")

# ─────────────────────────────────────────────────────────────────────────────
# Chart 16 – CPI Component Heatmap
# ─────────────────────────────────────────────────────────────────────────────
def chart16_cpi_heatmap(db):
    """CPIヒートマップ：品目×月のYoY変化率を色で表示."""
    print("\n[16] CPI component heatmap")
    cpi_d = db[1]

    COMPONENTS = {
        "Food & Non-Alc. Bev. (33.6%)": "PCPI_CP_01_IX",
        "Housing & Utilities (18.8%)":   "PCPI_CP_04_IX",
        "Transport (9.7%)":              "PCPI_CP_07_IX",
        "Education (6.2%)":              "PCPI_CP_10_IX",
        "Healthcare (5.4%)":             "PCPI_CP_06_IX",
        "Restaurant & Hotel (4.6%)":     "PCPI_CP_09_IX",
        "Clothing (5.7%)":               "PCPI_CP_03_IX",
        "Comm. & Recreation (3.1%)":     "PCPI_CP_08_IX",
        "Overall CPI":                   "PCPI_IX",
    }

    # Build YoY% matrix: component × month
    comp_yoy = {}
    all_months = None
    for label, ind in COMPONENTS.items():
        s = _get(cpi_d, ind)
        if not s:
            continue
        idx = _obs(s)
        months = sorted(idx)
        yoy = {}
        for i in range(12, len(months)):
            curr, prev = months[i], months[i-12]
            if idx.get(prev, 0):
                yoy[curr] = (idx[curr] / idx[prev] - 1) * 100
        comp_yoy[label] = yoy
        if all_months is None:
            all_months = sorted(yoy)

    if not all_months:
        print("  No CPI data – skipping")
        return

    # Restrict to months present in ALL components
    all_months = sorted(set(all_months).intersection(*[set(v) for v in comp_yoy.values()]))

    row_labels = list(COMPONENTS.keys())
    matrix = np.array([[comp_yoy[lbl].get(m, np.nan) for m in all_months]
                       for lbl in row_labels if lbl in comp_yoy])
    row_labels = [lbl for lbl in row_labels if lbl in comp_yoy]

    fig, axes = plt.subplots(2, 1, figsize=(18, 11),
                              gridspec_kw={"height_ratios": [3, 1]})
    fig.suptitle("Vietnam – CPI Inflation Heatmap by Component (YoY %)",
                 fontsize=13, fontweight="bold")

    # ── Heatmap ───────────────────────────────────────────────────────────
    ax = axes[0]
    vmax = max(abs(np.nanmax(matrix)), abs(np.nanmin(matrix)))
    vmax = min(vmax, 10)
    im = ax.imshow(matrix, aspect="auto", cmap="RdYlGn_r",
                   vmin=-vmax, vmax=vmax, interpolation="nearest")

    # x-axis: every 3rd month labelled
    step = 3
    xticks = list(range(0, len(all_months), step))
    ax.set_xticks(xticks)
    ax.set_xticklabels([all_months[i] for i in xticks], rotation=45,
                       ha="right", fontsize=7.5)

    ax.set_yticks(range(len(row_labels)))
    ax.set_yticklabels(row_labels, fontsize=9)

    # Cell annotations for integer values
    for ri in range(matrix.shape[0]):
        for ci in range(matrix.shape[1]):
            v = matrix[ri, ci]
            if not np.isnan(v) and ci % 3 == 0:
                ax.text(ci, ri, f"{v:.1f}", ha="center", va="center",
                        fontsize=6,
                        color="white" if abs(v) > vmax * 0.65 else "black")

    plt.colorbar(im, ax=ax, orientation="vertical",
                 label="YoY Change (%)", shrink=0.8)
    ax.set_title("YoY Change Rate (%) — Red = higher inflation, Green = lower",
                 fontsize=10)

    # ── Overall CPI YoY line ──────────────────────────────────────────────
    ax2 = axes[1]
    overall_label = "Overall CPI"
    if overall_label in comp_yoy:
        ov_yoy = comp_yoy[overall_label]
        xs  = range(len(all_months))
        ys  = [ov_yoy.get(m, None) for m in all_months]
        valid_xs = [x for x, y in zip(xs, ys) if y is not None]
        valid_ys = [y for y in ys if y is not None]
        ax2.plot(valid_xs, valid_ys, "b-o", linewidth=2, markersize=3, label="Overall YoY%")
        ax2.axhline(4, color="red", linestyle="--", linewidth=1, label="4% target")
        ax2.axhline(0, color="gray", linewidth=0.8)
        ax2.fill_between(valid_xs, valid_ys, 4,
                         where=[y > 4 for y in valid_ys],
                         alpha=0.2, color="red", label="Above target")
        ax2.fill_between(valid_xs, valid_ys, 4,
                         where=[y <= 4 for y in valid_ys],
                         alpha=0.1, color="green", label="Within target")
        ax2.set_xlim(-0.5, len(all_months) - 0.5)
        ax2.set_xticks(list(range(0, len(all_months), step)))
        ax2.set_xticklabels([all_months[i] for i in range(0, len(all_months), step)],
                             rotation=45, ha="right", fontsize=7.5)
        ax2.set_title("Overall CPI Year-on-Year (%)")
        ax2.set_ylabel("YoY %")
        ax2.legend(fontsize=8, loc="upper left")
        ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    savefig("16_cpi_heatmap.png")

    latest_m = all_months[-1]
    for lbl in row_labels:
        v = comp_yoy[lbl].get(latest_m, None)
        if v is not None:
            print(f"  {latest_m} {lbl.split('(')[0].strip()}: {v:+.2f}%")

# ─────────────────────────────────────────────────────────────────────────────
# Chart 17 – Province Bubble Chart  (density × urbanization × population)
# ─────────────────────────────────────────────────────────────────────────────
def chart17_province_bubble(e0201_records, e030307_records):
    """省別バブルチャート：X=人口密度, Y=都市化率, バブル=人口規模, 色=地域."""
    print("\n[17] Province bubble chart")

    # Region classification
    REGIONS = {
        "Red River Delta":          "#1f77b4",
        "North East":               "#aec7e8",
        "North West":               "#c5b0d5",
        "Northern Midlands and Mountain Areas": "#c5b0d5",
        "North Central and Central Coastal Areas": "#ff7f0e",
        "Central Highlands":        "#8c564b",
        "South East":               "#d62728",
        "Mekong River Delta":       "#2ca02c",
    }
    AGGREGATES = set(REGIONS) | {" WHOLE COUNTRY"}

    def clean_yr(y): return y.replace("Prel. ", "").strip()

    # ── Pull density + population from E02.01 (latest year) ──────────────
    years01 = sorted({r["Year"] for r in e0201_records}, key=clean_yr)
    latest01 = years01[-1]

    density = {}
    pop     = {}
    for r in e0201_records:
        prov = r["Cities, provincies"]
        if prov in AGGREGATES or r["Year"] != latest01:
            continue
        if r["Items"] == "Population density (Person/km2)" and r["value"]:
            density[prov] = r["value"]
        if r["Items"] == "Average population (Thous. pers.)" and r["value"]:
            pop[prov] = r["value"]

    # ── Pull urban share from E02.03-07 (latest year) ────────────────────
    years03 = sorted({r["Year"] for r in e030307_records}, key=clean_yr)
    latest03 = years03[-1]

    urban_share = {}
    for prov in density:
        total = next((r["value"] for r in e030307_records
                      if r["Cities, provincies"] == prov
                      and r["Year"] == latest03
                      and r["Average population"] == "Total"), None)
        urban = next((r["value"] for r in e030307_records
                      if r["Cities, provincies"] == prov
                      and r["Year"] == latest03
                      and r["Average population"] == "Urban"), None)
        if total and urban and total > 0:
            urban_share[prov] = urban / total * 100

    # Province → region mapping
    prov_region = {}
    current_region = None
    for r in e0201_records:
        prov = r["Cities, provincies"]
        if prov in REGIONS:
            current_region = prov
        elif prov not in AGGREGATES and current_region:
            prov_region[prov] = current_region

    provs = sorted(set(density) & set(urban_share) & set(pop))

    fig, ax = plt.subplots(figsize=(16, 11))

    legend_handles = {}
    for prov in provs:
        d  = density.get(prov, 0)
        u  = urban_share.get(prov, 0)
        p  = pop.get(prov, 0)            # thousand persons
        region = prov_region.get(prov, "Unknown")
        color  = REGIONS.get(region, "#999999")
        size   = (p / 500) ** 1.7 * 30   # non-linear scaling for bubble

        ax.scatter(d, u, s=max(size, 20), color=color, alpha=0.65,
                   edgecolors="white", linewidths=0.5, zorder=3)

        # Label notable provinces
        notable = {
            "Ho Chi Minh city", "Ha Noi", "Da Nang", "Binh Duong",
            "Can Tho", "Hai Phong", "Nghe An", "Thanh Hoa",
            "Long An", "Dong Nai", "Bac Ninh", "Hung Yen",
        }
        if prov in notable:
            ax.annotate(prov, (d, u), xytext=(5, 3),
                        textcoords="offset points",
                        fontsize=7.5, fontweight="bold",
                        bbox=dict(boxstyle="round,pad=0.15", fc="white",
                                  ec="none", alpha=0.7))
        if region not in legend_handles:
            legend_handles[region] = mpatches.Patch(color=color, label=region)

    # Reference lines
    nat_density = sum(density.values()) / len(density) if density else 0
    nat_urban   = sum(urban_share.values()) / len(urban_share) if urban_share else 0
    ax.axhline(nat_urban,   color="gray", linestyle="--", linewidth=1,
               alpha=0.7, label=f"Avg urban share ({nat_urban:.0f}%)")
    ax.axvline(nat_density, color="gray", linestyle=":",  linewidth=1,
               alpha=0.7, label=f"Avg density ({nat_density:.0f} p/km²)")

    # Quadrant labels
    ax.text(0.97, 0.97, "High density\nHigh urbanisation",
            transform=ax.transAxes, ha="right", va="top",
            fontsize=8, color="gray", alpha=0.6)
    ax.text(0.03, 0.97, "Low density\nHigh urbanisation",
            transform=ax.transAxes, ha="left",  va="top",
            fontsize=8, color="gray", alpha=0.6)
    ax.text(0.97, 0.03, "High density\nLow urbanisation",
            transform=ax.transAxes, ha="right", va="bottom",
            fontsize=8, color="gray", alpha=0.6)
    ax.text(0.03, 0.03, "Low density\nLow urbanisation",
            transform=ax.transAxes, ha="left",  va="bottom",
            fontsize=8, color="gray", alpha=0.6)

    ax.set_xscale("log")
    ax.set_title(
        f"Vietnam Provinces – Population Density vs Urbanisation Rate\n"
        f"(bubble size ∝ population, {clean_yr(latest01)} data)",
        fontsize=13, fontweight="bold")
    ax.set_xlabel("Population Density (persons/km²) — log scale", fontsize=11)
    ax.set_ylabel("Urban Population Share (%)", fontsize=11)
    ax.set_ylim(-5, 105)
    ax.grid(True, alpha=0.25)

    # Bubble size legend
    for sz_pop, lbl in [(500, "0.5M"), (2000, "2M"), (5000, "5M"), (10000, "10M")]:
        sz = (sz_pop / 500) ** 1.7 * 30
        ax.scatter([], [], s=sz, color="gray", alpha=0.5, label=f"Pop {lbl}")

    ax.legend(handles=list(legend_handles.values()) +
              [mpatches.Patch(color="white", label="── Bubble size = population ──")],
              fontsize=8, loc="upper left", ncol=2,
              framealpha=0.9)

    plt.tight_layout()
    savefig("17_province_bubble.png")
    print(f"  Plotted {len(provs)} provinces  |  "
          f"Latest density year: {clean_yr(latest01)}  |  "
          f"Latest urban year: {clean_yr(latest03)}")

# ─────────────────────────────────────────────────────────────────────────────
# Chart 18 – Economic Summary Dashboard  (1-page overview)
# ─────────────────────────────────────────────────────────────────────────────
def chart18_dashboard(db, e0202_result):
    """全指標を1枚にまとめた経済サマリーダッシュボード."""
    print("\n[18] Economic summary dashboard")

    nag  = db[0]
    met  = db[7]
    cpi_d = db[1]
    lmi  = db[10]

    # ── Data prep ──────────────────────────────────────────────────────────
    # GDP nominal (trillion VND, annual)
    ngdp_d = _obs(_get(nag, "NGDP_XDC", freq="A"))
    gdp_yrs = sorted(ngdp_d)
    gdp_vals = [ngdp_d[y] / 1000 for y in gdp_yrs]

    # Real GDP growth
    rgdp_d = _obs(_get(nag, "NGDP_R_XDC", freq="A"))
    rgdp_yrs = sorted(rgdp_d)
    rgdp_growth = {}
    for i in range(1, len(rgdp_yrs)):
        if rgdp_yrs[i-1] == "2009": continue
        p, c = rgdp_d[rgdp_yrs[i-1]], rgdp_d[rgdp_yrs[i]]
        if p: rgdp_growth[rgdp_yrs[i]] = (c/p - 1)*100
    gg_yrs = sorted(rgdp_growth)
    gg_vals = [rgdp_growth[y] for y in gg_yrs]

    # Trade balance (annual, billion USD)
    from collections import Counter
    ex_m = _obs(_get(met, "TXG_FOB_USD"))
    im_m = _obs(_get(met, "TMG_CIF_USD"))
    ex_a = _annual_sum(ex_m)
    im_a = _annual_sum(im_m)
    cnt  = Counter(p[:4] for p in ex_m)
    full = [y for y in cnt if cnt[y] == 12]
    ex_a = {y: ex_a[y]/1000 for y in full}
    im_a = {y: im_a[y]/1000 for y in full}
    tb_a = {y: ex_a[y] - im_a[y] for y in full}
    tr_yrs = sorted(full)

    # CPI YoY
    cpi_yoy_d = _obs(_get(cpi_d, "PCPICO_PC_PP_PT"))
    cpi_months = sorted(cpi_yoy_d)
    cpi_vals   = [cpi_yoy_d[m] for m in cpi_months]

    # Employment (quarterly → annual Q4)
    emp_d  = _obs(_get(lmi, "LE_PE_NUM"))
    emp_q4 = {q[:4]: v for q, v in emp_d.items() if q.endswith("Q4")}
    uemp_d = _obs(_get(lmi, "LEU_PT"))
    uemp_q4 = {q[:4]: v for q, v in uemp_d.items() if q.endswith("Q4")}

    # Population (from e0202)
    pop_yrs_int  = e0202_result["years"]
    pop_vals_mil = [v/1000 for v in e0202_result["total_pop_thous"]]
    urban_pct    = e0202_result["urban_struct"]

    # ── Figure layout: 3×2 grid ───────────────────────────────────────────
    fig, axes = plt.subplots(3, 2, figsize=(16, 14))
    fig.patch.set_facecolor("#f8f8f8")
    fig.suptitle(
        "Vietnam Economic & Demographic Dashboard\n"
        "Data: GSO/NSO Vietnam  •  Population: 1990–2024  •  Economy: 2000–2024",
        fontsize=14, fontweight="bold", y=0.98)

    # ── [0,0] GDP Nominal + Growth dual axis ─────────────────────────────
    ax = axes[0, 0]
    ax.set_facecolor("#fafafa")
    ax2 = ax.twinx()
    ax.fill_between(gdp_yrs, gdp_vals, alpha=0.25, color="#1f77b4")
    ax.plot(gdp_yrs, gdp_vals, "b-o", linewidth=2, markersize=4, label="GDP (T VND)")
    ax2.bar(gg_yrs, gg_vals,
            color=["#d62728" if v < 5 else "#2ca02c" for v in gg_vals],
            alpha=0.4, width=0.6, label="Real growth %")
    ax.set_title("GDP Nominal & Real Growth Rate", fontsize=11, fontweight="bold")
    ax.set_ylabel("Trillion VND", color="#1f77b4", fontsize=9)
    ax2.set_ylabel("Growth %", color="#555", fontsize=9)
    ax.tick_params(axis="x", rotation=45, labelsize=8)
    ax.grid(True, alpha=0.25)
    ax.set_xlabel("")

    # ── [0,1] Trade: Exports, Imports, Balance ────────────────────────────
    ax = axes[0, 1]
    ax.set_facecolor("#fafafa")
    ax.fill_between(tr_yrs, [ex_a[y] for y in tr_yrs], alpha=0.15, color="#1f77b4")
    ax.fill_between(tr_yrs, [im_a[y] for y in tr_yrs], alpha=0.15, color="#d62728")
    ax.plot(tr_yrs, [ex_a[y] for y in tr_yrs], "b-o", linewidth=2,
            markersize=4, label="Exports")
    ax.plot(tr_yrs, [im_a[y] for y in tr_yrs], "r-o", linewidth=2,
            markersize=4, label="Imports")
    ax2 = ax.twinx()
    tb_col = ["#2ca02c" if tb_a[y] >= 0 else "#d62728" for y in tr_yrs]
    ax2.bar(tr_yrs, [tb_a[y] for y in tr_yrs], color=tb_col, alpha=0.5,
            width=0.6, label="Balance")
    ax2.axhline(0, color="gray", linewidth=0.8)
    ax.set_title("Merchandise Trade (Billion USD)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Billion USD", fontsize=9)
    ax2.set_ylabel("Trade Balance (B USD)", color="#2ca02c", fontsize=9)
    ax.legend(fontsize=8, loc="upper left")
    ax.tick_params(axis="x", rotation=45, labelsize=8)
    ax.grid(True, alpha=0.25)

    # ── [1,0] CPI Inflation ───────────────────────────────────────────────
    ax = axes[1, 0]
    ax.set_facecolor("#fafafa")
    xs = range(len(cpi_months))
    ax.bar(xs, cpi_vals,
           color=["#d62728" if v > 4 else "#ff7f0e" if v > 2 else "#2ca02c"
                  for v in cpi_vals],
           alpha=0.7, width=1.0)
    ax.axhline(4, color="red", linestyle="--", linewidth=1.2,
               label="4% ceiling")
    ax.axhline(0, color="gray", linewidth=0.7)
    tick_xs = [i for i, m in enumerate(cpi_months) if m[5:] == "01"]
    ax.set_xticks(tick_xs)
    ax.set_xticklabels([cpi_months[i][:4] for i in tick_xs], rotation=45, fontsize=8)
    ax.set_title("CPI Inflation YoY % (Monthly)", fontsize=11, fontweight="bold")
    ax.set_ylabel("YoY %", fontsize=9)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.25, axis="y")

    # ── [1,1] Employment & Unemployment rate ──────────────────────────────
    ax = axes[1, 1]
    ax.set_facecolor("#fafafa")
    emp_yrs  = sorted(emp_q4)
    uemp_yrs = sorted(uemp_q4)
    ax2 = ax.twinx()
    ax.fill_between(emp_yrs, [emp_q4[y]/1000 for y in emp_yrs],
                    alpha=0.15, color="#1f77b4")
    ax.plot(emp_yrs, [emp_q4[y]/1000 for y in emp_yrs], "b-o",
            linewidth=2, markersize=4, label="Employed (M)")
    ax2.plot(uemp_yrs, [uemp_q4[y] for y in uemp_yrs], "r-s",
             linewidth=2, markersize=4, label="Unemployment %")
    ax.set_title("Employment & Unemployment Rate (Q4)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Employed (Million)", color="#1f77b4", fontsize=9)
    ax2.set_ylabel("Unemployment %", color="red", fontsize=9)
    ax.tick_params(axis="x", rotation=45, labelsize=8)
    ax.grid(True, alpha=0.25)
    lines1, l1 = ax.get_legend_handles_labels()
    lines2, l2 = ax2.get_legend_handles_labels()
    ax.legend(lines1+lines2, l1+l2, fontsize=8, loc="upper right")

    # ── [2,0] Population & Urban share ───────────────────────────────────
    ax = axes[2, 0]
    ax.set_facecolor("#fafafa")
    ax2 = ax.twinx()
    ax.fill_between(pop_yrs_int, pop_vals_mil, alpha=0.2, color="#9467bd")
    ax.plot(pop_yrs_int, pop_vals_mil, color="#9467bd", linewidth=2,
            marker="o", markersize=3, label="Population (M)")
    ax2.stackplot(pop_yrs_int, urban_pct, [100-u for u in urban_pct],
                  labels=["Urban %", "Rural %"],
                  colors=["#ff7f0e", "#2ca02c"], alpha=0.35)
    ax2.set_ylim(0, 105)
    ax.set_title("Population & Urban/Rural Split", fontsize=11, fontweight="bold")
    ax.set_ylabel("Population (Million)", color="#9467bd", fontsize=9)
    ax2.set_ylabel("Urban / Rural share (%)", fontsize=9)
    ax.tick_params(axis="x", rotation=45, labelsize=8)
    ax.grid(True, alpha=0.25)
    lines1, l1 = ax.get_legend_handles_labels()
    lines2, l2 = ax2.get_legend_handles_labels()
    ax.legend(lines1+lines2, l1+l2, fontsize=8, loc="upper left")

    # ── [2,1] Key Metrics Text Box ────────────────────────────────────────
    ax = axes[2, 1]
    ax.set_facecolor("#eef2f7")
    ax.axis("off")

    latest_gdp  = gdp_yrs[-1]
    latest_gdp_v = ngdp_d[latest_gdp]
    latest_growth = gg_vals[-1] if gg_vals else 0
    latest_ex   = ex_a.get(tr_yrs[-1], 0)
    latest_tb   = tb_a.get(tr_yrs[-1], 0)
    latest_cpi  = cpi_vals[-1] if cpi_vals else 0
    latest_emp  = emp_q4.get(sorted(emp_q4)[-1], 0) / 1000
    latest_uemp = uemp_q4.get(sorted(uemp_q4)[-1], 0)
    latest_pop  = pop_vals_mil[-1]
    latest_urban = urban_pct[-1]

    metrics = [
        ("GDP (2024)",             f"{latest_gdp_v/1000:.0f}T VND   ~${latest_gdp_v/25000:.0f}B"),
        ("Real GDP Growth",         f"{latest_growth:.1f}%/year"),
        ("Exports (2024)",          f"${latest_ex:.0f}B USD"),
        ("Trade Balance (2024)",    f"${latest_tb:+.0f}B USD"),
        ("CPI Inflation (Mar 2025)",f"{latest_cpi:.2f}% YoY"),
        ("Employment (2024-Q4)",    f"{latest_emp:.1f}M persons"),
        ("Unemployment (2024-Q4)", f"{latest_uemp:.2f}%"),
        ("Population (2024)",       f"{latest_pop:.1f}M persons"),
        ("Urban share (2024)",      f"{latest_urban:.1f}%"),
    ]

    ax.text(0.5, 0.97, "Key Indicators at a Glance",
            transform=ax.transAxes, ha="center", va="top",
            fontsize=12, fontweight="bold", color="#1a1a2e")

    for i, (label, value) in enumerate(metrics):
        y_pos = 0.87 - i * 0.095
        ax.text(0.08, y_pos, f"▸ {label}:",
                transform=ax.transAxes, ha="left", va="center",
                fontsize=9.5, color="#444")
        ax.text(0.92, y_pos, value,
                transform=ax.transAxes, ha="right", va="center",
                fontsize=9.5, fontweight="bold", color="#1a1a2e")
        ax.plot([0.05, 0.95], [y_pos - 0.038, y_pos - 0.038],
                transform=ax.transAxes, color="#cccccc",
                linewidth=0.5, clip_on=False)

    plt.tight_layout(rect=[0, 0, 1, 0.97])
    savefig("18_dashboard.png")
    print(f"  Dashboard: GDP={latest_gdp_v/1000:.0f}T VND | "
          f"Growth={latest_growth:.1f}% | Exports=${latest_ex:.0f}B | "
          f"CPI={latest_cpi:.1f}% | Unemployment={latest_uemp:.2f}%")


# ─────────────────────────────────────────────────────────────────────────────
# Entry point: run_extended_visualizations()
# ─────────────────────────────────────────────────────────────────────────────
def run_extended_visualizations(e0202_result, e0201_records, e030307_records):
    print("\n" + "=" * 60)
    print("EXTENDED VISUALIZATIONS (Charts 13–18)")
    print("=" * 60)

    db_path = os.path.join(BASE, "extracted_database.json")
    with open(db_path) as f:
        db = json.load(f)

    chart13_gdp_annotated(db)
    chart14_export_structure(db)
    chart15_labor_gender(db)
    chart16_cpi_heatmap(db)
    chart17_province_bubble(e0201_records, e030307_records)
    chart18_dashboard(db, e0202_result)
