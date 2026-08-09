# Investigate Hotel Business using Data Visualization

Everything for the project brief, plus an interactive Streamlit dashboard on top.

## What's in here

```
├── Hotel_Business_EDA.ipynb     ← the assignment notebook (Stages 0–3), fully executed
├── Hotel_Business_EDA.html      ← exported HTML version (submission-ready)
├── data_cleaning.py             ← shared cleaning pipeline (used by notebook + dashboard)
├── data/
│   ├── hotel_bookings_data.csv  ← raw dataset (119,390 rows)
│   └── hotel_bookings_clean.csv ← cleaned dataset (85,377 rows) produced by data_cleaning.py
├── dashboard/
│   ├── app.py                   ← Streamlit dashboard
│   ├── data_cleaning.py         ← copy of the cleaning module (self-contained folder)
│   └── hotel_bookings_clean.csv ← pre-cleaned data so the dashboard loads instantly
└── requirements.txt
```

## Quick start

Install dependencies:

```bash
pip install -r requirements.txt
```

### Run the dashboard

```bash
cd dashboard
streamlit run app.py
```

It opens at `http://localhost:8501`. Use the sidebar to filter by hotel type, arrival year, and
market segment — every chart and KPI updates live. Four tabs cover the three business questions
plus a raw-data explorer with CSV export.

### Re-run the EDA notebook

```bash
jupyter notebook Hotel_Business_EDA.ipynb
```

Or, to re-run headlessly and regenerate the HTML export:

```bash
jupyter nbconvert --to notebook --execute --inplace Hotel_Business_EDA.ipynb
jupyter nbconvert --to html Hotel_Business_EDA.ipynb
```

### Regenerate the cleaned dataset

```bash
python data_cleaning.py
```

Reads `data/hotel_bookings_data.csv`, applies the cleaning pipeline, and writes
`data/hotel_bookings_clean.csv`.

## Cleaning decisions (summary)

| Issue | Action | Why |
|---|---|---|
| 33,261 duplicate rows | Dropped | Identical across all 29 columns — re-submitted records |
| Missing `children` (4) | Filled with 0 | Adults/babies present; most plausible value |
| Missing `city` (488) | Filled with `'Unknown'` | Guest didn't supply origin; keep the rest of the row |
| Missing `agent`/`company` | Filled with 0 | Missing = booked directly, not missing data |
| `meal = 'Undefined'` | Recoded to `'No Meal'` | Both describe no meal package attached |
| Negative `adr` | Dropped | Data-entry error, a rate can't be negative |
| Extreme `adr` outliers | Capped at 99.5th percentile | Keep the row, stop it from skewing every average |
| Zero-guest / zero-night bookings | Dropped | Not real stays |

## The three business questions

1. **Hotel type popularity & seasonality** — City Hotel takes the larger share of bookings; both
   hotel types peak in July–August and dip in winter.
2. **Stay duration → cancellation** — cancellation rate rises as booked stay length increases.
3. **Lead time → cancellation** — cancellation rate rises steadily with lead time; last-minute
   bookings rarely cancel, far-ahead bookings cancel far more often.

Full charts, captions, and business recommendations for each question are in the notebook (Stage 2–3)
and interactively explorable in the dashboard.
