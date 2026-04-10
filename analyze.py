"""
Vietnam Economy Dataset Analysis
Datasets:
  E02.01  - Area, population, density by province (70 provinces × 14 years)
  E02.02  - National avg population by sex & residence (1990-2024)
  E02.03-07 - Province avg population by sex & residence (71 provinces × 30 years)
  E02.08  - Sex ratio by residence (2000-2024)
"""

import json
import os
import itertools
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

# ---------------------------------------------------------------------------
# JSON-stat parser
# ---------------------------------------------------------------------------

def load_jsonstat(path):
    """Return the 'dataset' dict from a JSON-stat file (handles trailing null bytes)."""
    with open(path, encoding="utf-8") as f:
        content = f.read().rstrip("\x00").strip()
    raw = json.loads(content)
    return raw["dataset"]


def to_table(ds):
    """
    Convert a JSON-stat dataset to a flat list of dicts.
    Handles both top-level size/id and dimension-embedded size/id.
    """
    dim_keys = ds["dimension"].get("id") or ds.get("id") or []
    sizes    = ds["dimension"].get("size") or ds.get("size") or []

    dims = []
    for key in dim_keys:
        cat = ds["dimension"][key]["category"]
        labels = [cat["label"][str(i)] for i in range(len(cat["label"]))]
        dims.append(labels)

    values = ds["value"]
    records = []
    for idx, combo in enumerate(itertools.product(*dims)):
        v = values[idx]
        row = dict(zip(dim_keys, combo))
        row["value"] = v
        records.append(row)
    return records


def pivot(records, row_key, col_key, val_key="value"):
    """Simple pivot: {row_val: {col_val: value}}."""
    table = {}
    for r in records:
        rk = r[row_key]
        ck = r[col_key]
        table.setdefault(rk, {})[ck] = r[val_key]
    return table


# ---------------------------------------------------------------------------
# Output directory
# ---------------------------------------------------------------------------
OUT = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUT, exist_ok=True)


def savefig(name):
    path = os.path.join(OUT, name)
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")


# ---------------------------------------------------------------------------
# Helper: clean year label (e.g. "Prel. 2024" -> "2024")
# ---------------------------------------------------------------------------
def clean_year(y):
    return y.replace("Prel. ", "").strip()


# ---------------------------------------------------------------------------
# Analysis 1 – E02.02: National population trends
# ---------------------------------------------------------------------------

def analyze_e0202():
    print("\n[1/4] E02.02 – National population trends")
    ds = load_jsonstat(os.path.join(os.path.dirname(__file__), "E02.02.json"))
    records = to_table(ds)

    years_raw = sorted(set(r["Year"] for r in records), key=clean_year)
    years_int = [int(clean_year(y)) for y in years_raw]

    # ── 1a  Total population ────────────────────────────────────────────────
    total_pop = [
        next(r["value"] for r in records
             if r["Items"] == "Total - Thous. pers."
             and r["Year"] == y
             and r["Sex, residence"] == "Total")
        for y in years_raw
    ]

    # ── 1b  Growth rate ─────────────────────────────────────────────────────
    growth = [
        next(r["value"] for r in records
             if r["Items"] == "Growth rate -%"
             and r["Year"] == y
             and r["Sex, residence"] == "Total")
        for y in years_raw
    ]

    # ── 1c  Urban / Rural structure ─────────────────────────────────────────
    urban_struct = [
        next(r["value"] for r in records
             if r["Items"] == "Structure -%"
             and r["Year"] == y
             and r["Sex, residence"] == "Urban")
        for y in years_raw
    ]
    rural_struct = [100 - u for u in urban_struct]

    # ── Plot ────────────────────────────────────────────────────────────────
    fig, axes = plt.subplots(3, 1, figsize=(12, 13))
    fig.suptitle("Vietnam – National Population Overview (E02.02)", fontsize=14, fontweight="bold")

    # Total population
    ax = axes[0]
    ax.plot(years_int, [v / 1000 for v in total_pop], color="#1f77b4", linewidth=2, marker="o", markersize=3)
    ax.set_title("Total Average Population (Million persons)")
    ax.set_ylabel("Million persons")
    ax.set_xlabel("Year")
    ax.grid(True, alpha=0.3)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.1f}"))

    # Growth rate
    ax = axes[1]
    ax.bar(years_int, growth, color=["#d62728" if g < 0 else "#2ca02c" for g in growth], alpha=0.75)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_title("Population Growth Rate (%)")
    ax.set_ylabel("%")
    ax.set_xlabel("Year")
    ax.grid(True, alpha=0.3, axis="y")

    # Urban/rural structure
    ax = axes[2]
    ax.stackplot(years_int, urban_struct, rural_struct,
                 labels=["Urban", "Rural"],
                 colors=["#ff7f0e", "#9467bd"], alpha=0.8)
    ax.set_title("Urban / Rural Population Structure (%)")
    ax.set_ylabel("%")
    ax.set_xlabel("Year")
    ax.set_ylim(0, 100)
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()
    savefig("01_national_population_trends.png")

    # ── Summary stats ────────────────────────────────────────────────────────
    print(f"  Population 1990: {total_pop[0]/1000:.2f}M  →  2024: {total_pop[-1]/1000:.2f}M")
    print(f"  Urban share 1990: {urban_struct[0]:.1f}%  →  2024: {urban_struct[-1]:.1f}%")
    print(f"  Avg growth rate: {sum(growth)/len(growth):.2f}%/yr")

    return {
        "years": years_int,
        "total_pop_thous": total_pop,
        "growth": growth,
        "urban_struct": urban_struct,
    }


# ---------------------------------------------------------------------------
# Analysis 2 – E02.01: Province-level population & density
# ---------------------------------------------------------------------------

def analyze_e0201():
    print("\n[2/4] E02.01 – Province-level population & density")
    ds = load_jsonstat(os.path.join(os.path.dirname(__file__), "E02.01.json"))
    records = to_table(ds)

    # Latest year available
    years_raw = sorted(set(r["Year"] for r in records), key=clean_year)
    latest = years_raw[-1]

    # Filter out aggregate regions (only proper provinces/cities)
    aggregate_regions = {
        " WHOLE COUNTRY", "Red River Delta", "Northern Midlands and Mountain Areas",
        "North Central and Central Coastal Areas", "Central Highlands",
        "South East", "Mekong River Delta", "North East", "North West",
    }

    provinces = sorted(set(r["Cities, provincies"] for r in records
                           if r["Cities, provincies"] not in aggregate_regions))

    def get_val(prov, year, item):
        for r in records:
            if r["Cities, provincies"] == prov and r["Year"] == year and r["Items"] == item:
                return r["value"]
        return None

    density_latest = {}
    pop_latest = {}
    for p in provinces:
        d = get_val(p, latest, "Population density (Person/km2)")
        pop = get_val(p, latest, "Average population (Thous. pers.)")
        if d is not None:
            density_latest[p] = d
        if pop is not None:
            pop_latest[p] = pop

    # Top/bottom 10 by density
    sorted_density = sorted(density_latest.items(), key=lambda x: x[1], reverse=True)
    top10   = sorted_density[:10]
    bot10   = sorted_density[-10:]

    # ── Plot 2a: Top/Bottom 10 density ──────────────────────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    fig.suptitle(f"Vietnam Province Population Density – {clean_year(latest)} (E02.01)",
                 fontsize=13, fontweight="bold")

    for ax, data, title, color in [
        (axes[0], top10,  "Top 10 Most Dense Provinces",   "#d62728"),
        (axes[1], bot10[::-1], "Bottom 10 Least Dense Provinces", "#1f77b4"),
    ]:
        names  = [d[0] for d in data]
        values = [d[1] for d in data]
        bars = ax.barh(names, values, color=color, alpha=0.75)
        ax.set_title(title)
        ax.set_xlabel("Persons/km²")
        ax.grid(True, alpha=0.3, axis="x")
        for bar, val in zip(bars, values):
            ax.text(bar.get_width() + max(values) * 0.01, bar.get_y() + bar.get_height() / 2,
                    f"{val:,.0f}", va="center", fontsize=8)
    plt.tight_layout()
    savefig("02_province_density.png")

    # ── Plot 2b: Population change over time for top 5 populous provinces ───
    top5_pop = sorted(pop_latest.items(), key=lambda x: x[1], reverse=True)[:5]
    top5_names = [p[0] for p in top5_pop]

    fig, ax = plt.subplots(figsize=(12, 6))
    colors_cycle = plt.cm.tab10.colors
    for i, prov in enumerate(top5_names):
        pops = []
        yrs = []
        for yr in years_raw:
            v = get_val(prov, yr, "Average population (Thous. pers.)")
            if v is not None:
                pops.append(v / 1000)
                yrs.append(int(clean_year(yr)))
        ax.plot(yrs, pops, marker="o", markersize=4, linewidth=2,
                color=colors_cycle[i], label=prov)

    ax.set_title("Population Trend – Top 5 Most Populous Provinces (E02.01)")
    ax.set_ylabel("Million persons")
    ax.set_xlabel("Year")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    savefig("03_top5_province_population.png")

    print(f"  Latest year: {clean_year(latest)}")
    print(f"  Highest density: {sorted_density[0][0]} ({sorted_density[0][1]:,.0f} p/km²)")
    print(f"  Lowest density:  {sorted_density[-1][0]} ({sorted_density[-1][1]:,.0f} p/km²)")
    print(f"  Largest province by pop: {top5_pop[0][0]} ({top5_pop[0][1]/1000:.2f}M)")

    return {"sorted_density": sorted_density, "top5_pop": top5_names}


# ---------------------------------------------------------------------------
# Analysis 3 – E02.08: Sex ratio trends
# ---------------------------------------------------------------------------

def analyze_e0208():
    print("\n[3/4] E02.08 – Sex ratio trends")
    ds = load_jsonstat(os.path.join(os.path.dirname(__file__), "E02.08.json"))
    records = to_table(ds)

    years_raw = sorted(set(r["Year"] for r in records), key=clean_year)
    years_int = [int(clean_year(y)) for y in years_raw]

    def series(sr_label, res_label):
        return [
            next((r["value"] for r in records
                  if r["Sex ratio"] == sr_label
                  and r["Year"] == y
                  and r["Residence"] == res_label), None)
            for y in years_raw
        ]

    pop_total  = series("Sex ratio of population (Males per 100 females)", "Total")
    pop_urban  = series("Sex ratio of population (Males per 100 females)", "Urban")
    pop_rural  = series("Sex ratio of population (Males per 100 females)", "Rural")
    birth_total = series("Sex ratio at birth (Males births per 100 female births)", "Total")
    birth_urban = series("Sex ratio at birth (Males births per 100 female births)", "Urban")
    birth_rural = series("Sex ratio at birth (Males births per 100 female births)", "Rural")

    fig, axes = plt.subplots(2, 1, figsize=(12, 10))
    fig.suptitle("Vietnam – Sex Ratio Trends (E02.08)", fontsize=13, fontweight="bold")

    ax = axes[0]
    ax.plot(years_int, pop_total, "b-o",  markersize=4, label="Total",   linewidth=2)
    ax.plot(years_int, pop_urban, "r--s", markersize=4, label="Urban",   linewidth=1.5)
    ax.plot(years_int, pop_rural, "g--^", markersize=4, label="Rural",   linewidth=1.5)
    ax.axhline(100, color="gray", linestyle=":", linewidth=1, label="Equal (100)")
    ax.set_title("Population Sex Ratio (Males per 100 Females)")
    ax.set_ylabel("Males per 100 Females")
    ax.set_xlabel("Year")
    ax.legend()
    ax.grid(True, alpha=0.3)

    ax = axes[1]
    ax.plot(years_int, birth_total, "b-o",  markersize=4, label="Total", linewidth=2)
    ax.plot(years_int, birth_urban, "r--s", markersize=4, label="Urban", linewidth=1.5)
    ax.plot(years_int, birth_rural, "g--^", markersize=4, label="Rural", linewidth=1.5)
    ax.axhline(105, color="gray", linestyle=":", linewidth=1, label="Biological norm (~105)")
    ax.set_title("Sex Ratio at Birth (Male Births per 100 Female Births)")
    ax.set_ylabel("Males per 100 Females")
    ax.set_xlabel("Year")
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    savefig("04_sex_ratio_trends.png")

    print(f"  Population sex ratio 2000: {pop_total[0]:.1f}  →  2024: {pop_total[-1]:.1f}")
    print(f"  Birth sex ratio 2000: {birth_total[0]:.1f}  →  2024: {birth_total[-1]:.1f}")
    print(f"  Birth SRB peak: {max(birth_total):.1f} ({years_int[birth_total.index(max(birth_total))]})")

    return {"years": years_int, "pop_total": pop_total, "birth_total": birth_total}


# ---------------------------------------------------------------------------
# Analysis 4 – E02.03-07: Province population by sex & residence
# ---------------------------------------------------------------------------

def analyze_e030307():
    print("\n[4/4] E02.03-07 – Province population by sex & residence")
    ds = load_jsonstat(os.path.join(os.path.dirname(__file__), "E02.03-07.json"))
    records = to_table(ds)

    # Latest common year with data
    years_raw = sorted(set(r["Year"] for r in records), key=clean_year)
    latest = years_raw[-1]

    aggregate_regions = {
        " WHOLE COUNTRY", "Red River Delta", "Northern Midlands and Mountain Areas",
        "North Central and Central Coastal Areas", "Central Highlands",
        "South East", "Mekong River Delta", "North East", "North West",
    }
    provinces = sorted(set(r["Cities, provincies"] for r in records
                           if r["Cities, provincies"] not in aggregate_regions))

    # Urban share per province in the latest year
    def get_val(prov, year, cat):
        for r in records:
            if (r["Cities, provincies"] == prov
                    and r["Year"] == year
                    and r["Average population"] == cat):
                return r["value"]
        return None

    urban_share = {}
    for p in provinces:
        total = get_val(p, latest, "Total")
        urban = get_val(p, latest, "Urban")
        if total and urban and total > 0:
            urban_share[p] = urban / total * 100

    sorted_urban = sorted(urban_share.items(), key=lambda x: x[1], reverse=True)
    top10u  = sorted_urban[:10]
    bot10u  = sorted_urban[-10:]

    # ── Plot 4a: Urban share top/bottom ─────────────────────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    fig.suptitle(f"Vietnam Province Urban Population Share – {clean_year(latest)} (E02.03-07)",
                 fontsize=13, fontweight="bold")

    for ax, data, title, color in [
        (axes[0], top10u,        "Top 10 Most Urbanised",       "#ff7f0e"),
        (axes[1], bot10u[::-1],  "Top 10 Least Urbanised",      "#9467bd"),
    ]:
        names  = [d[0] for d in data]
        values = [d[1] for d in data]
        bars = ax.barh(names, values, color=color, alpha=0.75)
        ax.set_title(title)
        ax.set_xlabel("Urban population share (%)")
        ax.set_xlim(0, 100)
        ax.grid(True, alpha=0.3, axis="x")
        for bar, val in zip(bars, values):
            ax.text(min(val + 2, 95), bar.get_y() + bar.get_height() / 2,
                    f"{val:.1f}%", va="center", fontsize=8)
    plt.tight_layout()
    savefig("05_province_urban_share.png")

    # ── Plot 4b: National urban/rural trend using whole-country row ──────────
    nat_records_urban = [(r["Year"], r["value"]) for r in records
                         if r["Cities, provincies"] == " WHOLE COUNTRY"
                         and r["Average population"] == "Urban"]
    nat_records_rural = [(r["Year"], r["value"]) for r in records
                         if r["Cities, provincies"] == " WHOLE COUNTRY"
                         and r["Average population"] == "Rural"]
    nat_records_total = [(r["Year"], r["value"]) for r in records
                         if r["Cities, provincies"] == " WHOLE COUNTRY"
                         and r["Average population"] == "Total"]

    def sort_by_year(lst):
        return sorted(lst, key=lambda x: clean_year(x[0]))

    nat_urban = sort_by_year(nat_records_urban)
    nat_rural = sort_by_year(nat_records_rural)
    nat_total = sort_by_year(nat_records_total)

    # Filter out entries with None values
    combined = [(int(clean_year(t[0])), t[1], u[1], r[1])
                for t, u, r in zip(nat_total, nat_urban, nat_rural)
                if t[1] is not None and u[1] is not None and r[1] is not None]
    yrs    = [x[0] for x in combined]
    t_vals = [x[1] for x in combined]
    u_vals = [x[2] for x in combined]
    r_vals = [x[3] for x in combined]
    u_pct  = [u / t * 100 for u, t in zip(u_vals, t_vals)]

    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax2 = ax1.twinx()
    ax1.stackplot(yrs,
                  [v / 1000 for v in u_vals],
                  [v / 1000 for v in r_vals],
                  labels=["Urban", "Rural"],
                  colors=["#ff7f0e", "#9467bd"], alpha=0.7)
    ax2.plot(yrs, u_pct, "k--", linewidth=2, label="Urban share (%)")
    ax1.set_title("Vietnam – Urban & Rural Population Trend, All Provinces (E02.03-07)")
    ax1.set_ylabel("Million persons")
    ax2.set_ylabel("Urban share (%)")
    ax1.set_xlabel("Year")
    ax1.legend(loc="upper left")
    ax2.legend(loc="upper center")
    ax2.set_ylim(0, 100)
    ax1.grid(True, alpha=0.3)
    plt.tight_layout()
    savefig("06_national_urban_rural_trend.png")

    print(f"  Latest year: {clean_year(latest)}")
    print(f"  Most urbanised: {sorted_urban[0][0]} ({sorted_urban[0][1]:.1f}%)")
    print(f"  Least urbanised: {sorted_urban[-1][0]} ({sorted_urban[-1][1]:.1f}%)")

    return {"sorted_urban": sorted_urban}


# ---------------------------------------------------------------------------
# Summary table print
# ---------------------------------------------------------------------------

def print_summary(e0202, e0201, e0208, e030307):
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Population (1990 → latest): "
          f"{e0202['total_pop_thous'][0]/1000:.2f}M → "
          f"{e0202['total_pop_thous'][-1]/1000:.2f}M")
    print(f"Urban share (1990 → latest): "
          f"{e0202['urban_struct'][0]:.1f}% → "
          f"{e0202['urban_struct'][-1]:.1f}%")
    print(f"Avg annual growth: {sum(e0202['growth'])/len(e0202['growth']):.2f}%")
    print(f"Densest province: {e0201['sorted_density'][0][0]}")
    print(f"Most urbanised province: {e030307['sorted_urban'][0][0]}")
    print(f"Birth sex ratio peak: "
          f"{max(e0208['birth_total']):.1f} "
          f"({e0208['years'][e0208['birth_total'].index(max(e0208['birth_total']))]})")
    print("=" * 60)
    print(f"Charts saved to: {OUT}/")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Vietnam Economy Dataset Analysis")
    print("=" * 60)

    e0202    = analyze_e0202()
    e0201    = analyze_e0201()
    e0208    = analyze_e0208()
    e030307  = analyze_e030307()

    print_summary(e0202, e0201, e0208, e030307)

    # ── Extended economic analysis (SDMX archive) ──────────────────────────
    db_path = os.path.join(os.path.dirname(__file__), "extracted_database.json")
    if os.path.exists(db_path):
        from analyze_economic import run_economic_analysis
        run_economic_analysis(e0202_result=e0202)
    else:
        print("\n[SKIP] extracted_database.json not found – run: "
              "curl -L -o all_data_gso.json.zip <url> && unzip all_data_gso.json.zip")
