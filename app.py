"""
Hotel Business Intelligence Dashboard
--------------------------------------
Interactive Streamlit app answering three business questions:
  1. Which hotel type do customers book most often, and when?
  2. Does length of stay affect cancellation rate?
  3. Does lead time affect cancellation rate?

Run with:  streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from data_cleaning import load_raw, clean_hotel_data, get_cleaning_report

# ----------------------------------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="The Ledger — Hotel Booking Intelligence",
    page_icon="🗝️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------------
# DESIGN SYSTEM — "The Ledger": a boutique-hotel front-desk register aesthetic
# Palette: ink navy, warm brass, parchment ivory, sage (kept) / rust (cancelled)
# ----------------------------------------------------------------------------
INK = "#1B2A41"
INK_LIGHT = "#2C4160"
BRASS = "#C9A24B"
BRASS_LIGHT = "#E4C77A"
IVORY = "#FAF6EE"
PARCHMENT = "#F1EADC"
SAGE = "#6E8B6E"
RUST = "#B5533C"
INK_TEXT = "#25314A"

CUSTOM_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700;800&family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
}}

.stApp {{
    background-color: {IVORY};
}}

/* Header banner */
.ledger-header {{
    background: linear-gradient(120deg, {INK} 0%, {INK_LIGHT} 100%);
    padding: 2.2rem 2.5rem;
    border-radius: 14px;
    margin-bottom: 1.6rem;
    box-shadow: 0 6px 24px rgba(27,42,65,0.25);
    position: relative;
    overflow: hidden;
}}
.ledger-header::after {{
    content: "";
    position: absolute;
    top: -40%;
    right: -8%;
    width: 260px;
    height: 260px;
    border: 1.5px solid rgba(201,162,75,0.35);
    border-radius: 50%;
}}
.ledger-header h1 {{
    font-family: 'Playfair Display', serif;
    color: {IVORY};
    font-size: 2.3rem;
    margin: 0;
    letter-spacing: 0.5px;
}}
.ledger-header p {{
    color: {BRASS_LIGHT};
    font-size: 1.02rem;
    margin-top: 0.4rem;
    font-weight: 500;
    letter-spacing: 0.3px;
}}

/* Section labels styled like a hotel register / ledger entry */
.section-eyebrow {{
    font-family: 'Inter', sans-serif;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    font-size: 0.72rem;
    color: {BRASS};
    border-bottom: 1.5px solid {BRASS};
    display: inline-block;
    padding-bottom: 4px;
    margin-bottom: 0.3rem;
}}
.section-title {{
    font-family: 'Playfair Display', serif;
    font-size: 1.65rem;
    color: {INK};
    margin-top: 0.1rem;
    margin-bottom: 0.2rem;
}}
.section-sub {{
    color: #5B6B82;
    font-size: 0.95rem;
    margin-bottom: 1rem;
}}

/* KPI cards */
.kpi-card {{
    background: white;
    border-radius: 12px;
    padding: 1.1rem 1.3rem;
    border-left: 4px solid {BRASS};
    box-shadow: 0 2px 10px rgba(27,42,65,0.07);
}}
.kpi-label {{
    font-size: 0.78rem;
    color: #6B7A93;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    font-weight: 600;
}}
.kpi-value {{
    font-family: 'Playfair Display', serif;
    font-size: 1.9rem;
    color: {INK};
    font-weight: 700;
    margin-top: 0.1rem;
}}
.kpi-delta {{
    font-size: 0.82rem;
    color: {SAGE};
    font-weight: 600;
}}

/* Insight callout box */
.insight-box {{
    background: {PARCHMENT};
    border-left: 4px solid {SAGE};
    border-radius: 8px;
    padding: 0.9rem 1.2rem;
    margin: 0.8rem 0 1.4rem 0;
    color: {INK_TEXT};
    font-size: 0.95rem;
}}
.insight-box b {{ color: {INK}; }}

/* Sidebar */
section[data-testid="stSidebar"] {{
    background-color: {INK};
}}
section[data-testid="stSidebar"] * {{
    color: {IVORY} !important;
}}
section[data-testid="stSidebar"] .stSelectbox label, 
section[data-testid="stSidebar"] .stMultiSelect label,
section[data-testid="stSidebar"] .stSlider label {{
    color: {BRASS_LIGHT} !important;
    font-weight: 600;
}}

hr {{
    border-color: rgba(27,42,65,0.12);
}}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

PLOTLY_TEMPLATE = dict(
    layout=dict(
        font=dict(family="Inter, sans-serif", color=INK_TEXT, size=13),
        title_font=dict(family="Playfair Display, serif", size=18, color=INK),
        plot_bgcolor="white",
        paper_bgcolor="white",
        colorway=[INK_LIGHT, BRASS, SAGE, RUST, "#8C9DBE", "#D9C48F"],
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        margin=dict(t=60, l=10, r=10, b=10),
    )
)

# ----------------------------------------------------------------------------
# DATA LOADING (cached)
# ----------------------------------------------------------------------------
@st.cache_data(show_spinner="Loading and cleaning bookings data...")
def get_data():
    here = Path(__file__).parent
    clean_path = here / "hotel_bookings_clean.csv"
    if clean_path.exists():
        df = pd.read_csv(clean_path, parse_dates=["arrival_date"])
        raw_rows = 119390  # known raw row count for the report card
        return df, raw_rows
    else:
        raw = load_raw(here / "hotel_bookings_data.csv")
        df = clean_hotel_data(raw)
        return df, len(raw)


df, raw_row_count = get_data()

# ----------------------------------------------------------------------------
# HEADER
# ----------------------------------------------------------------------------
st.markdown(
    """
    <div class="ledger-header">
        <h1>🗝️ The Ledger — Hotel Booking Intelligence</h1>
        <p>Understanding what drives guests to book, and what drives them to cancel · 2017–2019</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------
# SIDEBAR FILTERS
# ----------------------------------------------------------------------------
st.sidebar.markdown("### 🏨 Filters")

hotel_options = ["All"] + sorted(df["hotel"].unique().tolist())
hotel_choice = st.sidebar.selectbox("Hotel type", hotel_options)

years = sorted(df["arrival_date_year"].unique().tolist())
year_choice = st.sidebar.multiselect("Arrival year", years, default=years)

segment_options = sorted(df["market_segment"].unique().tolist())
segment_choice = st.sidebar.multiselect("Market segment", segment_options, default=segment_options)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📋 About the data")
report = {
    "raw_rows": raw_row_count,
    "clean_rows": len(df),
}
st.sidebar.markdown(
    f"""
    <div style="font-size:0.85rem; line-height:1.6;">
    <b>Raw rows:</b> {report['raw_rows']:,}<br>
    <b>After cleaning:</b> {report['clean_rows']:,}<br>
    <b>Removed:</b> duplicates, zero-guest / zero-night bookings, invalid ADR<br>
    <b>Period:</b> 2017 – 2019
    </div>
    """,
    unsafe_allow_html=True,
)

# Apply filters
fdf = df.copy()
if hotel_choice != "All":
    fdf = fdf[fdf["hotel"] == hotel_choice]
if year_choice:
    fdf = fdf[fdf["arrival_date_year"].isin(year_choice)]
if segment_choice:
    fdf = fdf[fdf["market_segment"].isin(segment_choice)]

if fdf.empty:
    st.warning("No bookings match the selected filters. Try widening your selection.")
    st.stop()

# ----------------------------------------------------------------------------
# KPI ROW
# ----------------------------------------------------------------------------
total_bookings = len(fdf)
cancel_rate = fdf["is_canceled"].mean() * 100
avg_lead = fdf["lead_time"].mean()
avg_adr = fdf["adr"].mean()
avg_stay = fdf["total_stay_nights"].mean()

k1, k2, k3, k4, k5 = st.columns(5)
kpi_data = [
    (k1, "Total Bookings", f"{total_bookings:,}"),
    (k2, "Cancellation Rate", f"{cancel_rate:.1f}%"),
    (k3, "Avg. Lead Time", f"{avg_lead:.0f} days"),
    (k4, "Avg. Daily Rate", f"€{avg_adr:.0f}"),
    (k5, "Avg. Stay Length", f"{avg_stay:.1f} nights"),
]
for col, label, value in kpi_data:
    col.markdown(
        f"""<div class="kpi-card"><div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div></div>""",
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# TABS FOR THE THREE BUSINESS QUESTIONS
# ----------------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "🏨  Hotel Type & Seasonality",
    "🛏️  Stay Duration → Cancellations",
    "⏳  Lead Time → Cancellations",
    "📊  Explore Raw Data",
])

# =============================================================================
# TAB 1 — HOTEL TYPE & SEASONALITY
# =============================================================================
with tab1:
    st.markdown('<div class="section-eyebrow">Business Question 1</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Which hotel type do customers book most often?</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Booking share between City and Resort hotels, and how demand moves through the year.</div>', unsafe_allow_html=True)

    c1, c2 = st.columns([1, 1.6])

    with c1:
        hotel_share = fdf["hotel"].value_counts().reset_index()
        hotel_share.columns = ["hotel", "count"]
        fig_share = px.pie(
            hotel_share, names="hotel", values="count", hole=0.55,
            color="hotel", color_discrete_map={"City Hotel": INK_LIGHT, "Resort Hotel": BRASS},
        )
        fig_share.update_traces(textinfo="percent+label", textfont_size=13)
        fig_share.update_layout(**PLOTLY_TEMPLATE["layout"], title="Booking Share by Hotel Type", showlegend=False, height=380)
        st.plotly_chart(fig_share, use_container_width=True)

    with c2:
        monthly = (
            fdf.groupby(["hotel", "arrival_date_month", "arrival_month_num"])
            .size().reset_index(name="bookings")
            .sort_values("arrival_month_num")
        )
        fig_month = px.line(
            monthly, x="arrival_date_month", y="bookings", color="hotel", markers=True,
            color_discrete_map={"City Hotel": INK_LIGHT, "Resort Hotel": BRASS},
        )
        fig_month.update_layout(**PLOTLY_TEMPLATE["layout"], title="Monthly Booking Volume by Hotel Type", height=380,
                                 xaxis_title="", yaxis_title="Bookings")
        st.plotly_chart(fig_month, use_container_width=True)

    top_hotel = hotel_share.iloc[0]
    peak_month_row = fdf.groupby("arrival_date_month").size().idxmax()
    quiet_month_row = fdf.groupby("arrival_date_month").size().idxmin()
    st.markdown(
        f"""<div class="insight-box">
        💡 <b>{top_hotel['hotel']}</b> accounts for <b>{top_hotel['count']/total_bookings*100:.1f}%</b> of bookings in the current selection.
        Demand peaks in <b>{peak_month_row}</b> and is quietest in <b>{quiet_month_row}</b> —
        a pattern consistent with summer holiday travel and slower shoulder-season months.
        This suggests dynamic pricing and staffing should flex around the peak, while off-peak promotions
        could help lift the quieter months.
        </div>""",
        unsafe_allow_html=True,
    )

    # Weekday of arrival heatmap-style bar (bonus interactivity)
    seg_counts = fdf.groupby(["hotel", "market_segment"]).size().reset_index(name="bookings")
    fig_seg = px.bar(
        seg_counts, x="market_segment", y="bookings", color="hotel", barmode="group",
        color_discrete_map={"City Hotel": INK_LIGHT, "Resort Hotel": BRASS},
    )
    fig_seg.update_layout(**PLOTLY_TEMPLATE["layout"], title="Bookings by Market Segment", height=380, xaxis_title="", yaxis_title="Bookings")
    st.plotly_chart(fig_seg, use_container_width=True)

# =============================================================================
# TAB 2 — STAY DURATION vs CANCELLATION
# =============================================================================
with tab2:
    st.markdown('<div class="section-eyebrow">Business Question 2</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Does the length of stay affect cancellation rate?</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Cancellation rate by hotel type and by how many nights the guest booked.</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        cancel_by_hotel = fdf.groupby("hotel")["is_canceled"].mean().reset_index()
        cancel_by_hotel["is_canceled"] *= 100
        fig_ch = px.bar(
            cancel_by_hotel, x="hotel", y="is_canceled", color="hotel", text_auto=".1f",
            color_discrete_map={"City Hotel": INK_LIGHT, "Resort Hotel": BRASS},
        )
        fig_ch.update_traces(texttemplate="%{y:.1f}%", textposition="outside")
        fig_ch.update_layout(**PLOTLY_TEMPLATE["layout"], title="Cancellation Rate by Hotel Type", height=380,
                              yaxis_title="Cancellation Rate (%)", xaxis_title="", showlegend=False)
        st.plotly_chart(fig_ch, use_container_width=True)

    with c2:
        stay_cancel = (
            fdf.groupby(["hotel", "stay_length_bucket"], observed=True)["is_canceled"]
            .mean().reset_index()
        )
        stay_cancel["is_canceled"] *= 100
        order = ['1 night', '2-3 nights', '4-7 nights', '8-14 nights', '15+ nights']
        fig_stay = px.bar(
            stay_cancel, x="stay_length_bucket", y="is_canceled", color="hotel", barmode="group",
            category_orders={"stay_length_bucket": order},
            color_discrete_map={"City Hotel": INK_LIGHT, "Resort Hotel": BRASS},
        )
        fig_stay.update_layout(**PLOTLY_TEMPLATE["layout"], title="Cancellation Rate by Stay Length", height=380,
                                yaxis_title="Cancellation Rate (%)", xaxis_title="")
        st.plotly_chart(fig_stay, use_container_width=True)

    fig_line = px.line(
        fdf.groupby(["hotel", "total_stay_nights"])["is_canceled"].mean().reset_index().query("total_stay_nights <= 21"),
        x="total_stay_nights", y="is_canceled", color="hotel", markers=True,
        color_discrete_map={"City Hotel": INK_LIGHT, "Resort Hotel": BRASS},
    )
    fig_line.update_layout(**PLOTLY_TEMPLATE["layout"], title="Cancellation Rate vs. Exact Nights Booked (up to 21 nights)",
                            height=380, yaxis_title="Cancellation Rate", yaxis_tickformat=".0%", xaxis_title="Total Nights Booked")
    st.plotly_chart(fig_line, use_container_width=True)

    corr = fdf[["total_stay_nights", "is_canceled"]].corr().iloc[0, 1]
    trend_word = "rises" if corr > 0.02 else ("falls" if corr < -0.02 else "stays roughly flat")
    st.markdown(
        f"""<div class="insight-box">
        💡 Across the current selection, cancellation rate <b>{trend_word}</b> as stay length increases
        (correlation ≈ <b>{corr:.2f}</b>). Longer bookings tend to be planned further out and are more exposed to
        changing plans, which can make no-deposit cancellation terms and minimum-stay pricing worth revisiting
        for longer stays.
        </div>""",
        unsafe_allow_html=True,
    )

# =============================================================================
# TAB 3 — LEAD TIME vs CANCELLATION
# =============================================================================
with tab3:
    st.markdown('<div class="section-eyebrow">Business Question 3</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Does lead time affect cancellation rate?</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Lead time = days between booking and arrival. Longer lead times mean more time for plans to change.</div>', unsafe_allow_html=True)

    max_lead = int(fdf["lead_time"].quantile(0.98))
    lead_range = st.slider("Focus lead-time range (days)", 0, int(fdf["lead_time"].max()), (0, max_lead))
    ldf = fdf[(fdf["lead_time"] >= lead_range[0]) & (fdf["lead_time"] <= lead_range[1])]

    c1, c2 = st.columns(2)
    with c1:
        bucket_cancel = (
            ldf.groupby(["hotel", "lead_time_bucket"], observed=True)["is_canceled"]
            .mean().reset_index()
        )
        bucket_cancel["is_canceled"] *= 100
        order = ['0-7 days', '8-30 days', '31-90 days', '91-180 days', '181-365 days', '365+ days']
        fig_bucket = px.bar(
            bucket_cancel, x="lead_time_bucket", y="is_canceled", color="hotel", barmode="group",
            category_orders={"lead_time_bucket": order},
            color_discrete_map={"City Hotel": INK_LIGHT, "Resort Hotel": BRASS},
        )
        fig_bucket.update_layout(**PLOTLY_TEMPLATE["layout"], title="Cancellation Rate by Lead-Time Bucket", height=400,
                                  yaxis_title="Cancellation Rate (%)", xaxis_title="")
        st.plotly_chart(fig_bucket, use_container_width=True)

    with c2:
        smooth = (
            ldf.groupby(["hotel", "lead_time"])["is_canceled"].mean().reset_index()
        )
        fig_smooth = px.scatter(
            smooth, x="lead_time", y="is_canceled", color="hotel", trendline="lowess",
            color_discrete_map={"City Hotel": INK_LIGHT, "Resort Hotel": BRASS}, opacity=0.35,
        )
        fig_smooth.update_layout(**PLOTLY_TEMPLATE["layout"], title="Cancellation Rate vs. Lead Time (with trend)", height=400,
                                  yaxis_title="Cancellation Rate", yaxis_tickformat=".0%", xaxis_title="Lead Time (days)")
        st.plotly_chart(fig_smooth, use_container_width=True)

    lowest = bucket_cancel.loc[bucket_cancel["is_canceled"].idxmin()]
    highest = bucket_cancel.loc[bucket_cancel["is_canceled"].idxmax()]
    st.markdown(
        f"""<div class="insight-box">
        💡 Cancellation risk is lowest for <b>{lowest['lead_time_bucket']}</b> bookings
        (<b>{lowest['hotel']}</b>, {lowest['is_canceled']:.1f}%) and highest for
        <b>{highest['lead_time_bucket']}</b> bookings (<b>{highest['hotel']}</b>, {highest['is_canceled']:.1f}%).
        Bookings made far in advance carry more cancellation risk — a case for deposits, reminder emails,
        or flexible-reschedule options on long-lead-time reservations rather than rigid cancellation policies.
        </div>""",
        unsafe_allow_html=True,
    )

# =============================================================================
# TAB 4 — RAW DATA EXPLORER
# =============================================================================
with tab4:
    st.markdown('<div class="section-eyebrow">Appendix</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Explore the Cleaned Dataset</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-sub">{len(fdf):,} rows match your current filters (of {len(df):,} cleaned rows total).</div>', unsafe_allow_html=True)

    show_cols = st.multiselect(
        "Columns to display",
        options=fdf.columns.tolist(),
        default=["hotel", "arrival_date", "lead_time", "total_stay_nights", "adr", "is_canceled_label", "market_segment"],
    )
    st.dataframe(fdf[show_cols].head(500), use_container_width=True, height=440)

    csv = fdf.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download filtered data as CSV", csv, "filtered_hotel_bookings.csv", "text/csv")

# ----------------------------------------------------------------------------
# FOOTER
# ----------------------------------------------------------------------------
st.markdown("---")
st.markdown(
    """<div style="text-align:center; color:#8A97AA; font-size:0.82rem; padding: 0.5rem 0 1.5rem 0;">
    Built for the "Investigate Hotel Business using Data Visualization" project · Data: Hotel Bookings 2017–2019
    </div>""",
    unsafe_allow_html=True,
)
