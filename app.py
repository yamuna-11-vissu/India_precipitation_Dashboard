import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="India Precipitation Analysis",
    page_icon="🌧️",
    layout="wide",
)

DATA_FILE = Path(__file__).parent / "precipitation-ind-csv-1.csv"

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_FILE)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["date", "value", "station"]).copy()
    df["year"] = df["date"].dt.year.astype(int)
    df["month"] = df["date"].dt.month
    df["month_name"] = df["date"].dt.strftime("%b")
    df["year_month"] = df["date"].dt.strftime("%Y-%m")
    return df

try:
    df = load_data()
except Exception as exc:
    st.error(f"Could not load the dataset: {exc}")
    st.info("Check that precipitation-ind-csv-1.csv is in the same GitHub folder as app.py.")
    st.stop()

st.title("🌧️ India Precipitation Analysis Dashboard")
st.caption("Exploratory analysis of monthly TPCP observations from Indian weather stations | January 2010 – June 2011")
st.warning(
    "Interpretation note: the dataset does not specify the measurement unit in the supplied columns. "
    "Values below are shown as dataset values, not labelled as millimetres. "
    "Summing station observations is not the same as calculating national-area rainfall."
)

# Sidebar filters
st.sidebar.header("Dashboard Filters")
years = sorted(df["year"].dropna().unique().tolist())
selected_years = st.sidebar.multiselect("Select year(s)", years, default=years)
stations = sorted(df["station"].dropna().unique().tolist())
selected_stations = st.sidebar.multiselect("Select station(s)", stations, default=stations)

filtered = df[df["year"].isin(selected_years)]
if selected_stations:
    filtered = filtered[filtered["station"].isin(selected_stations)]
else:
    filtered = filtered.iloc[0:0]

if filtered.empty:
    st.warning("No records match the selected filters. Choose at least one year and one station.")
    st.stop()

# KPI cards
total_value = filtered["value"].sum()
average_value = filtered["value"].mean()
max_value = filtered["value"].max()
station_count = filtered["station"].nunique()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total recorded value", f"{total_value:,.0f}")
c2.metric("Average recorded value", f"{average_value:,.2f}")
c3.metric("Maximum recorded value", f"{max_value:,.0f}")
c4.metric("Stations selected", f"{station_count:,}")

st.divider()

# Monthly trend - average across station observations per month
monthly = (
    filtered.groupby(["date"], as_index=False)
    .agg(mean_value=("value", "mean"), sum_station_values=("value", "sum"), observations=("value", "size"))
    .sort_values("date")
)
left, right = st.columns((1.5, 1))
with left:
    st.subheader("Monthly average precipitation value")
    fig = px.line(
        monthly, x="date", y="mean_value", markers=True,
        labels={"date": "Month", "mean_value": "Average dataset value"},
        template="plotly_white"
    )
    fig.update_layout(margin=dict(l=10, r=10, t=25, b=10))
    st.plotly_chart(fig, use_container_width=True)
with right:
    st.subheader("Year-wise comparison")
    yearly = (
        filtered.groupby("year", as_index=False)
        .agg(mean_value=("value", "mean"), total_station_values=("value", "sum"))
    )
    fig_year = px.bar(
        yearly, x="year", y="mean_value", text_auto=".2f",
        labels={"year": "Year", "mean_value": "Average dataset value"},
        template="plotly_white"
    )
    fig_year.update_layout(margin=dict(l=10, r=10, t=25, b=10))
    st.plotly_chart(fig_year, use_container_width=True)

st.divider()
left, right = st.columns(2)
with left:
    st.subheader("Top 10 stations by recorded-value sum")
    top_stations = (
        filtered.groupby("station", as_index=False)["value"].sum()
        .sort_values("value", ascending=False).head(10)
    )
    fig_top = px.bar(
        top_stations.sort_values("value"), x="value", y="station", orientation="h",
        labels={"value": "Sum of recorded values", "station": "Weather station"},
        template="plotly_white"
    )
    fig_top.update_layout(margin=dict(l=10, r=10, t=25, b=10))
    st.plotly_chart(fig_top, use_container_width=True)
with right:
    st.subheader("Positive vs zero observations")
    rain_counts = pd.DataFrame({
        "Observation": ["Positive value", "Zero value"],
        "Records": [(filtered["value"] > 0).sum(), (filtered["value"] == 0).sum()]
    })
    fig_zero = px.pie(
        rain_counts, names="Observation", values="Records", hole=0.48,
        template="plotly_white"
    )
    fig_zero.update_layout(margin=dict(l=10, r=10, t=25, b=10))
    st.plotly_chart(fig_zero, use_container_width=True)

st.divider()
st.subheader("Monthly heatmap – selected stations")
heat = filtered.pivot_table(index="station", columns="year_month", values="value", aggfunc="mean")
# Keep the 20 stations with the highest average value so the heatmap remains readable.
if len(heat) > 20:
    keep = heat.mean(axis=1).nlargest(20).index
    heat = heat.loc[keep]
fig_heat = px.imshow(
    heat, aspect="auto", color_continuous_scale="Blues",
    labels=dict(x="Year-month", y="Weather station", color="Average value"),
    template="plotly_white"
)
fig_heat.update_layout(margin=dict(l=10, r=10, t=25, b=10))
st.plotly_chart(fig_heat, use_container_width=True)

# Insights and table
st.subheader("Key observations")
peak_month = monthly.loc[monthly["mean_value"].idxmax()]
low_month = monthly.loc[monthly["mean_value"].idxmin()]
i1, i2, i3 = st.columns(3)
i1.info(f"Highest monthly average: **{peak_month['date']:%B %Y}** ({peak_month['mean_value']:.2f})")
i2.info(f"Lowest monthly average: **{low_month['date']:%B %Y}** ({low_month['mean_value']:.2f})")
i3.info(f"Records after filters: **{len(filtered):,}**")

with st.expander("View filtered data"):
    st.dataframe(filtered, use_container_width=True, hide_index=True)
    csv = filtered.to_csv(index=False).encode("utf-8")
    st.download_button("Download filtered data as CSV", csv, "filtered_precipitation_data.csv", "text/csv")

st.caption("Source: precipitation-ind-csv-1.csv supplied for this project. TPCP is retained as provided in the source data.")
