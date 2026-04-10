# Vietnam Population & Economy Dataset Analysis Report

**Data sources:**
- General Statistics Office (GSO) / National Statistics Office (NSO) of Vietnam
- JSON-stat tables: E02.01–E02.08 (population, provincial)
- SDMX archive: `extracted_database.json` from [gso-macro-monitor v1.2.0](https://github.com/thanhqtran/gso-macro-monitor/releases/tag/v1.2.0) (data through 2025-Q1)

**Analysis date:** 2026-04-10  
**Scripts:** `analyze.py` (population), `analyze_economic.py` (macroeconomy)

---

## Datasets

### Population (JSON-stat)

| File | Description | Dimensions | Period |
|------|-------------|-----------|--------|
| E02.02.json | National avg population by sex & residence | Items × Year × Sex/residence | 1990–2024 |
| E02.01.json | Area, population, density by province | 70 provinces × Year × Items | 2011–2024 |
| E02.08.json | Sex ratio by residence | Sex ratio type × Year × Residence | 2000–2024 |
| E02.03-07.json | Province avg population by sex & residence | 71 provinces × Category × Year | 1995–2024 |

### Macroeconomy (SDMX)

| Domain | Description | Frequency | Period |
|--------|-------------|-----------|--------|
| NAG | National Accounts – GDP, sectoral value-added | Annual / Quarterly | 2000–2024 |
| MET | Merchandise trade – exports, imports, balance | Monthly | 2010–2024 |
| CPI | Consumer Price Index – overall & components | Monthly | 2020-08–2025-03 |
| LMI | Labor Market – employment, unemployment, wages | Quarterly | 2011–2024 |

---

## Key Findings

### 1. National Population Trends (`01_national_population_trends.png`)

- Total population: **66.0M (1990) → 101.3M (2024)** (+53% over 34 years)
- Average annual growth: **1.29%/year**; declining from ~1.9% in early 1990s to ~1.0% by 2020s
- **Urban share** rose from 19.5% (1990) to **38.5% (2024)** — rapid urbanisation but still majority rural

### 2. Province Population & Density (`02–03`)

- **Densest (2024):** Ho Chi Minh City (4,555 p/km²) → Ha Noi, Hung Yen, Bac Ninh
- **Sparsest:** Lai Chau (55 p/km²); density gap extremes = ~83×
- **Top 5 populous:** HCMC, Hanoi, Thanh Hoa, Nghe An, Dong Nai — showing fastest absolute growth in recent decade

### 3. Sex Ratio (`04_sex_ratio_trends.png`)

- **Population sex ratio:** 96.7 (2000) → **99.6 (2024)** — converging toward parity
- **Birth sex ratio (SRB):** 107.3 (2000) → peak **114.8 (2018)** → 111.4 (2024)
  - Biological norm is ~105; Vietnam's SRB well above this, reflecting son preference and prenatal sex selection
  - Moderate improvement post-2018 following policy interventions

### 4. Province Urban/Rural Structure (`05–06`)

- **Most urbanised (2024):** Da Nang (87.8%), HCMC, Ha Noi, Binh Duong
- **Least urbanised:** Thai Binh (11.9%); most Mekong Delta & highland provinces remain agricultural
- National urban population growing in absolute terms; rural growth has plateaued

---

### 5. GDP Overview (`07_gdp_overview.png`)

- Nominal GDP: **441T VND (2000) → 11,512T VND (2024)** (~$476B USD at 2024 rates)
- Average **real GDP growth: 7.7%/year** (2005–2024)
- COVID impact: growth slowed to ~2.9% in 2020, then strong rebound (8.0% in 2022)
- **GDP per capita (2024):** ~113.6M VND (~$4,700) — lower-middle income transition underway

### 6. GDP Sectoral Composition (`08_gdp_sectors.png`)

- Structural transformation clearly visible (2004–2024, constant 2010 prices):
  - **Agriculture:** declining share (~12% → 11.4%)
  - **Industry:** expanded share, driven by manufacturing (~36% → 40%)
  - **Services:** dominant at **48.5% in 2024**, growing steadily
- Manufacturing-led export growth is Vietnam's primary engine, supported by FDI inflows

### 7. Merchandise Trade (`09_trade.png`)

- Vietnam is now a major trading nation:
  - **2024 exports: $403B**, **imports: $379B**, **trade surplus: $24B USD**
  - Trade total (~$782B) exceeds GDP ($476B) → extremely open economy (trade/GDP > 160%)
- Trade balance turned positive in 2012 and has been mostly in surplus since
- Monthly volatility reflects seasonal export patterns (electronics, textiles, seafood)

### 8. CPI Inflation (`10_cpi.png`)

- CPI index (2020=100): rose to **118.7 by March 2025** — cumulative 18.7% inflation in ~4.5 years
- **Average YoY inflation: 2.52%** (Aug 2020 – Mar 2025) — broadly within policy target
- Peak inflation (2022–2023): ~4–5% YoY, driven by housing/utilities and transport (global energy shock)
- Recent trend: inflation moderating to **3.1% YoY (March 2025)**
- Housing & Utilities and Transport show the largest price increases relative to 2020

### 9. Labor Market (`11_labor.png`)

- **Total employed (2024-Q4): 52.1M persons**
- **Unemployment rate (2024-Q4): 1.65%** — one of the lowest in Asia (reflects informal sector prevalence)
- COVID shock visible: employment fell sharply in 2021 (49.1M), recovered by 2022
- **Average monthly wage (2023-Q1): ~7.9M VND (~$316)** — wage data largely unavailable post-2023
- **Gender wage gap:** Males earn roughly 8–12% more than females per available data period
  - Gap has been narrow but persistent

### 10. Cross-Analysis: GDP Growth vs Population Growth (`12_gdp_vs_population.png`)

- Weak negative correlation: as population growth slows, GDP growth has generally remained high or risen
- Demographic dividend: working-age population share peaked in 2010s, supporting strong per-capita GDP gains
- Post-2020 slowdown in both metrics; Vietnam entering slower-growth demographic phase

---

## Charts Generated

| File | Content |
|------|---------|
| `output/01_national_population_trends.png` | Total population, growth rate, urban/rural structure (1990–2024) |
| `output/02_province_density.png` | Top/bottom 10 provinces by population density (2024) |
| `output/03_top5_province_population.png` | Population trend, top 5 provinces (2011–2024) |
| `output/04_sex_ratio_trends.png` | Population & birth sex ratio by residence (2000–2024) |
| `output/05_province_urban_share.png` | Most/least urbanised provinces (2024) |
| `output/06_national_urban_rural_trend.png` | National urban & rural population with urban share (1995–2024) |
| `output/07_gdp_overview.png` | Nominal GDP (T VND & B USD), real growth rate, per capita (2000–2024) |
| `output/08_gdp_sectors.png` | Sectoral GDP composition – agri/industry/services (2004–2024) |
| `output/09_trade.png` | Annual exports, imports, trade balance; monthly rolling trend (2010–2024) |
| `output/10_cpi.png` | Overall CPI & YoY inflation; component breakdown (2020–2025) |
| `output/11_labor.png` | Employment level, unemployment rate, wages, gender wage gap (2011–2024) |
| `output/12_gdp_vs_population.png` | GDP growth vs population growth scatter & time series (2005–2024) |

---

## How to Run

```bash
# Install dependencies
pip install matplotlib numpy

# Download extended economic data (one-time)
curl -L -o all_data_gso.json.zip \
  https://github.com/thanhqtran/gso-macro-monitor/releases/download/v1.2.0/all_data_gso_20250606.json.zip
unzip all_data_gso.json.zip

# Run full analysis (population + economy)
python3 analyze.py

# Run economic analysis only
python3 analyze_economic.py
```

Charts are written to `output/`.
