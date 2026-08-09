"""
data_cleaning.py
-----------------
Shared cleaning pipeline for the Hotel Booking Business project.
Used by both the EDA notebook and the Streamlit dashboard so that
every chart in the project is built on exactly the same cleaned data.
"""

import pandas as pd
import numpy as np


def load_raw(path: str) -> pd.DataFrame:
    """Load the raw hotel bookings CSV."""
    return pd.read_csv(path)


def clean_hotel_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Full cleaning pipeline for the hotel bookings dataset.

    Steps (each justified in the EDA notebook, Stage 1.2):
      1. Drop exact duplicate rows.
      2. Fill missing 'children' with 0 (no children recorded -> assume none).
      3. Fill missing 'city' with 'Unknown' (guest did not supply origin).
      4. Fill missing 'agent' / 'company' with 0 (no agent/company = booked
         directly, not missing data).
      5. Recode 'Undefined' meal as 'No Meal' (both mean no meal package).
      6. Remove bookings with adr < 0 (data entry error) and cap extreme
         adr outliers at the 99.5th percentile (keep the row, cap the value)
         so a handful of luxury/erroneous rows don't distort every chart.
      7. Remove bookings with zero total guests (adults+children+babies==0)
         - these cannot be real stays.
      8. Add helper columns used throughout the analysis:
         total_stay_nights, total_guests, arrival_date, is_canceled_label.
    """
    df = df.copy()

    # 1. Duplicates
    df = df.drop_duplicates()

    # 2-4. Missing values
    df['children'] = df['children'].fillna(0)
    df['city'] = df['city'].fillna('Unknown')
    df['agent'] = df['agent'].fillna(0)
    df['company'] = df['company'].fillna(0)

    # 5. Meal recode
    df['meal'] = df['meal'].replace({'Undefined': 'No Meal'})

    # 6. ADR anomalies
    df = df[df['adr'] >= 0]
    adr_cap = df['adr'].quantile(0.995)
    df['adr'] = df['adr'].clip(upper=adr_cap)

    # 7. Zero-guest bookings
    total_guests = df['adults'] + df['children'] + df['babies']
    df = df[total_guests > 0]

    # 8. Helper columns
    df['total_stay_nights'] = df['stays_in_weekend_nights'] + df['stays_in_weekdays_nights']
    df = df[df['total_stay_nights'] > 0]  # a stay of 0 nights is not a real stay
    df['total_guests'] = df['adults'] + df['children'] + df['babies']

    month_map = {
        'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6,
        'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12
    }
    df['arrival_month_num'] = df['arrival_date_month'].map(month_map)
    df['arrival_date'] = pd.to_datetime(
        dict(year=df['arrival_date_year'], month=df['arrival_month_num'], day=df['arrival_date_day_of_month']),
        errors='coerce'
    )

    df['is_canceled_label'] = df['is_canceled'].map({0: 'Not Cancelled', 1: 'Cancelled'})

    # Lead time bucket for the lead-time analysis
    bins = [-1, 7, 30, 90, 180, 365, 10000]
    labels = ['0-7 days', '8-30 days', '31-90 days', '91-180 days', '181-365 days', '365+ days']
    df['lead_time_bucket'] = pd.cut(df['lead_time'], bins=bins, labels=labels)

    # Stay length bucket for the stay-duration analysis
    stay_bins = [-1, 1, 3, 7, 14, 1000]
    stay_labels = ['1 night', '2-3 nights', '4-7 nights', '8-14 nights', '15+ nights']
    df['stay_length_bucket'] = pd.cut(df['total_stay_nights'], bins=stay_bins, labels=stay_labels)

    df = df.reset_index(drop=True)
    return df


def get_cleaning_report(raw: pd.DataFrame, clean: pd.DataFrame) -> dict:
    """Small summary dict used to show a 'what changed' box in the dashboard."""
    return {
        'raw_rows': len(raw),
        'clean_rows': len(clean),
        'rows_removed': len(raw) - len(clean),
        'duplicates_removed': int(raw.duplicated().sum()),
        'missing_filled': {
            'children': int(raw['children'].isnull().sum()),
            'city': int(raw['city'].isnull().sum()),
            'agent': int(raw['agent'].isnull().sum()),
            'company': int(raw['company'].isnull().sum()),
        },
    }


if __name__ == '__main__':
    raw = load_raw('data/hotel_bookings_data.csv')
    clean = clean_hotel_data(raw)
    report = get_cleaning_report(raw, clean)
    print(report)
    clean.to_csv('data/hotel_bookings_clean.csv', index=False)
    print(f"Saved cleaned data: {clean.shape}")
