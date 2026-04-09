# Vietnam Population Dataset Analysis Report

**Data source:** General Statistics Office of Vietnam  
**Analysis date:** 2026-04-09  
**Script:** `analyze.py`

---

## Datasets

| File | Description | Dimensions | Period |
|------|-------------|-----------|--------|
| E02.02.json | National avg population by sex & residence | Items × Year × Sex/residence | 1990–2024 |
| E02.01.json | Area, population, density by province | 70 provinces × Year × Items | 2011–2024 |
| E02.08.json | Sex ratio by residence | Sex ratio type × Year × Residence | 2000–2024 |
| E02.03-07.json | Province avg population by sex & residence | 71 provinces × Category × Year | 1995–2024 |

---

## Key Findings

### 1. National Population Trends (`01_national_population_trends.png`)

- Total population grew from **66.0 million (1990)** to **101.3 million (2024)** — a 53% increase over 34 years.
- Average annual growth rate: **1.29%/year**; decelerating from ~1.9% in the early 1990s to ~1.0% by the 2020s.
- A notable growth spike in 1999 (+9.2%) is visible, likely due to a methodological revision or census adjustment.
- **Urban population share** rose from 19.5% (1990) to 38.5% (2024), reflecting sustained urbanisation, though Vietnam remains predominantly rural.

### 2. Province Population & Density (`02_province_density.png`, `03_top5_province_population.png`)

- **Most densely populated province (2024):** Ho Chi Minh City (4,555 persons/km²)
- Other high-density provinces: Ha Noi, Hung Yen, Bac Ninh — all in major metropolitan or industrialised corridors
- **Least densely populated:** Lai Chau (55 persons/km²), followed by other Northern highland provinces (Dien Bien, Son La)
- The density gap between extremes is ~83×, reflecting large urban–rural and highland–lowland disparities.
- Among the top 5 most populous provinces, **Ho Chi Minh City** and **Ha Noi** showed the fastest absolute growth over the 2011–2024 period.

### 3. Sex Ratio Trends (`04_sex_ratio_trends.png`)

**Population sex ratio** (males per 100 females):
- Rose steadily from **96.7 (2000)** to **99.6 (2024)**, converging toward parity.
- Rural areas consistently show a higher ratio than urban areas, suggesting female out-migration to cities.

**Sex ratio at birth (SRB)** (male births per 100 female births):
- Climbed from **107.3 (2000)** to a peak of **114.8 (2018)**, far above the biological norm of ~105.
- Slight decline since 2018, reaching **111.4 (2024)**, indicating some policy impact (Law on Gender Equality, awareness campaigns).
- Urban SRB is generally higher than rural, suggesting son preference is amplified by access to prenatal sex selection.

### 4. Province Urban/Rural Structure (`05_province_urban_share.png`, `06_national_urban_rural_trend.png`)

- **Most urbanised province (2024):** Da Nang (87.8%)
- Other highly urbanised: Ho Chi Minh City, Ha Noi, Binh Duong (industrial satellite)
- **Least urbanised:** Thai Binh (11.9%), followed by other agricultural delta and highland provinces
- National urban population trend (E02.03-07) confirms the steady rise in urban residents in absolute terms, while rural population has grown more slowly and begun to plateau.

---

## Charts Generated

| File | Content |
|------|---------|
| `output/01_national_population_trends.png` | Total population, growth rate, urban/rural structure (1990–2024) |
| `output/02_province_density.png` | Top/bottom 10 provinces by population density (2024) |
| `output/03_top5_province_population.png` | Population trend for 5 most populous provinces (2011–2024) |
| `output/04_sex_ratio_trends.png` | Population & birth sex ratio by residence (2000–2024) |
| `output/05_province_urban_share.png` | Most/least urbanised provinces (2024) |
| `output/06_national_urban_rural_trend.png` | National urban & rural population with urban share (1995–2024) |

---

## How to Run

```bash
pip install matplotlib numpy
python3 analyze.py
```

Charts are written to `output/`.
