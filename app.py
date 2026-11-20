import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

st.set_page_config(
    page_title="India Live Rainfall Monitor",
    page_icon="🌧️",
    layout="wide",
)

st.markdown("""
<style>
    .main {background-color: #f5f8fc;}
    .block-container {padding-top: 1.4rem; padding-bottom: 2rem;}
    div[data-testid="stMetric"] {
        background: white; border: 1px solid #e3eaf2;
        padding: 15px; border-radius: 12px;
    }
    .small-note {color: #64748b; font-size: 0.88rem;}
</style>
""", unsafe_allow_html=True)

DATA_FILE = Path(__file__).parent / "precipitation-ind-csv-1.csv"
API_URL = "https://api.open-meteo.com/v1/forecast"

# Representative city locations across India. These are model forecast points,
# not a complete gridded rainfall map or official rain-gauge network.
CITIES = [
    ("Delhi", "Delhi", 28.6139, 77.2090),
    ("Chandigarh", "Chandigarh", 30.7333, 76.7794),
    ("Shimla", "Himachal Pradesh", 31.1048, 77.1734),
    ("Dehradun", "Uttarakhand", 30.3165, 78.0322),
    ("Srinagar", "Jammu & Kashmir", 34.0837, 74.7973),
    ("Jaipur", "Rajasthan", 26.9124, 75.7873),
    ("Lucknow", "Uttar Pradesh", 26.8467, 80.9462),
    ("Patna", "Bihar", 25.5941, 85.1376),
    ("Ranchi", "Jharkhand", 23.3441, 85.3096),
    ("Kolkata", "West Bengal", 22.5726, 88.3639),
    ("Gangtok", "Sikkim", 27.3389, 88.6065),
    ("Guwahati", "Assam", 26.1445, 91.7362),
    ("Shillong", "Meghalaya", 25.5788, 91.8933),
    ("Agartala", "Tripura", 23.8315, 91.2868),
    ("Aizawl", "Mizoram", 23.7271, 92.7176),
    ("Imphal", "Manipur", 24.8170, 93.9368),
    ("Kohima", "Nagaland", 25.6751, 94.1086),
    ("Itanagar", "Arunachal Pradesh", 27.0844, 93.6053),
    ("Bhopal", "Madhya Pradesh", 23.2599, 77.4126),
    ("Raipur", "Chhattisgarh", 21.2514, 81.6296),
    ("Gandhinagar", "Gujarat", 23.2156, 72.6369),
    ("Mumbai", "Maharashtra", 19.0760, 72.8777),
    ("Panaji", "Goa", 15.4909, 73.8278),
    ("Bengaluru", "Karnataka", 12.9716, 77.5946),
    ("Chennai", "Tamil Nadu", 13.0827, 80.2707),
    ("Hyderabad", "Telangana", 17.3850, 78.4867),
    ("Amaravati", "Andhra Pradesh", 16.5062, 80.6480),
    ("Thiruvananthapuram", "Kerala", 8.5241, 76.9366),
]

@st.cache_data(show_spinner=False)
def load_historical():
    if not DATA_FILE.exists():
        return None, f"Dataset file not found: {DATA_FILE.name}"
    try:
        data = pd.read_csv(DATA_FILE)
        required = {"date", "station", "value"}
        if not required.issubset(data.columns):
            return None, "CSV must contain date, station and value columns."
        data["date"] = pd.to_datetime(data["date"], errors="coerce")
        data["value"] = pd.to_numeric(data["value"], errors="coerce")
        data = data.dropna(subset=["date", "station", "value"]).copy()
        data["year"] = data["date"].dt.year
        data["month"] = data["date"].dt.month
        data["month_name"] = data["date"].dt.strftime("%b")
        return data, None
    except Exception as exc:
        return None, str(exc)

def fetch_city_weather(city):
    name, state, lat, lon = city
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,precipitation,rain,showers,weather_code,wind_speed_10m",
        "hourly": "precipitation,precipitation_probability",
        "forecast_days": 1,
        "timezone": "Asia/Kolkata",
    }
    response = requests.get(API_URL, params=params, timeout=18)
    response.raise_for_status()
    payload = response.json()
    current = payload.get("current", {})
    hourly = payload.get("hourly", {})
    times = hourly.get("time", [])
    precip = hourly.get("precipitation", [])
    prob = hourly.get("precipitation_probability", [])
    now = current.get("time")
    upcoming = []
    for i, t in enumerate(times):
        if now and t >= now:
            upcoming.append((t, precip[i] if i < len(precip) else None,
                             prob[i] if i < len(prob) else None))
    next_rain = next((x for x in upcoming if x[1] is not None and x[1] > 0), None)
    return {
        "City": name, "State/UT": state, "Latitude": lat, "Longitude": lon,
        "Temperature (°C)": current.get("temperature_2m"),
        "Humidity (%)": current.get("relative_humidity_2m"),
        "Current precipitation (mm)": current.get("precipitation"),
        "Rain (mm)": current.get("rain"),
        "Wind (km/h)": current.get("wind_speed_10m"),
        "Weather code": current.get("weather_code"),
        "Next-hour precipitation (mm)": upcoming[0][1] if upcoming else None,
        "Next-hour rain probability (%)": upcoming[0][2] if upcoming else None,
        "Next forecast rain": next_rain[0] if next_rain else "No rain predicted in available hours",
        "Updated at (India time)": now,
    }

def fetch_all_cities():
    results, errors = [], []
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(fetch_city_weather, city): city for city in CITIES}
        for future in as_completed(futures):
            city = futures[future]
            try:
                results.append(future.result())
            except Exception as exc:
                errors.append(f"{city[0]}: {exc}")
    frame = pd.DataFrame(results)
    if not frame.empty:
        frame = frame.sort_values("City").reset_index(drop=True)
    return frame, errors

# Header
st.title("🌧️ India Live Rainfall Monitor")
st.markdown("**Live model-based weather conditions + historical precipitation analysis**")
st.caption("Coverage: 28 representative city locations across India | Manual refresh")

st.info(
    "Live-data note: current conditions and forecasts are supplied by Open-Meteo weather models "
    "for representative city coordinates. This is not a live radar image, official IMD warning, "
    "or a complete observation map of every location in India."
)

# Manual refresh only: retain last successful result until user presses the button.
if "live_weather" not in st.session_state:
    st.session_state.live_weather = pd.DataFrame()
if "live_errors" not in st.session_state:
    st.session_state.live_errors = []
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = None

top_left, top_right = st.columns([1, 3])
with top_left:
    refresh_clicked = st.button("🔄 Refresh live weather", type="primary", use_container_width=True)
with top_right:
    if st.session_state.last_refresh:
        st.caption(f"Last successful refresh: {st.session_state.last_refresh}")
    else:
        st.caption("Press Refresh live weather to retrieve the latest available model conditions.")

if refresh_clicked:
    with st.spinner("Fetching weather for representative locations across India..."):
        live, errors = fetch_all_cities()
        if not live.empty:
            st.session_state.live_weather = live
            st.session_state.live_errors = errors
            st.session_state.last_refresh = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%d %b %Y, %I:%M:%S %p IST")
        else:
            st.error("Live weather could not be retrieved. Check your internet connection and try again.")
            st.session_state.live_errors = errors

live = st.session_state.live_weather

st.subheader("🇮🇳 Live weather snapshot")
if live.empty:
    st.warning("No live data loaded yet. Click **Refresh live weather** above.")
else:
    valid_rain = pd.to_numeric(live["Current precipitation (mm)"], errors="coerce").dropna()
    wet_cities = int((valid_rain > 0).sum())
    mean_temp = pd.to_numeric(live["Temperature (°C)"], errors="coerce").mean()
    max_rain_row = live.loc[pd.to_numeric(live["Current precipitation (mm)"], errors="coerce").fillna(-1).idxmax()]
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Locations reporting rain", f"{wet_cities} / {len(live)}")
    k2.metric("Average city temperature", f"{mean_temp:.1f} °C" if pd.notna(mean_temp) else "N/A")
    k3.metric("Highest current precipitation", f"{max(valid_rain):.1f} mm" if len(valid_rain) else "N/A")
    k4.metric("Locations covered", f"{len(live)}")

    st.subheader("Current precipitation by city")
    map_data = live.copy()
    map_data["Current precipitation (mm)"] = pd.to_numeric(map_data["Current precipitation (mm)"], errors="coerce")
    fig_map = px.scatter_geo(
        map_data, lat="Latitude", lon="Longitude",
        color="Current precipitation (mm)", size="Current precipitation (mm)",
        hover_name="City",
        hover_data={"State/UT": True, "Temperature (°C)": True, "Humidity (%)": True,
                    "Current precipitation (mm)": ":.2f", "Latitude": False, "Longitude": False},
        scope="asia", projection="natural earth",
        color_continuous_scale="Blues", size_max=22,
        title="Modelled current precipitation at selected Indian city locations"
    )
    fig_map.update_geos(
        lonaxis_range=[67, 98], lataxis_range=[6, 38],
        showcountries=True, countrycolor="#94a3b8",
        showland=True, landcolor="#f1f5f9",
        showocean=True, oceancolor="#eaf3fb"
    )
    fig_map.update_layout(height=520, margin=dict(l=0, r=0, t=55, b=0))
    st.plotly_chart(fig_map, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Temperature by location")
        temp_fig = px.bar(
            live.sort_values("Temperature (°C)"),
            x="Temperature (°C)", y="City", orientation="h", color="Temperature (°C)",
            color_continuous_scale="RdYlBu_r", template="plotly_white"
        )
        temp_fig.update_layout(height=600, margin=dict(l=0, r=0, t=20, b=0))
        st.plotly_chart(temp_fig, use_container_width=True)
    with col2:
        st.subheader("Next-hour precipitation probability")
        prob = live.copy()
        prob["Next-hour rain probability (%)"] = pd.to_numeric(prob["Next-hour rain probability (%)"], errors="coerce")
        prob_fig = px.bar(
            prob.sort_values("Next-hour rain probability (%)"),
            x="Next-hour rain probability (%)", y="City", orientation="h",
            color="Next-hour rain probability (%)", color_continuous_scale="Blues",
            template="plotly_white"
        )
        prob_fig.update_layout(height=600, margin=dict(l=0, r=0, t=20, b=0))
        st.plotly_chart(prob_fig, use_container_width=True)

    st.subheader("Live location details")
    display_cols = ["City", "State/UT", "Current precipitation (mm)", "Rain (mm)",
                    "Temperature (°C)", "Humidity (%)", "Wind (km/h)",
                    "Next-hour precipitation (mm)", "Next-hour rain probability (%)",
                    "Updated at (India time)"]
    st.dataframe(live[display_cols], use_container_width=True, hide_index=True)
    csv_live = live.to_csv(index=False).encode("utf-8")
    st.download_button("Download live snapshot CSV", csv_live, "india_live_weather_snapshot.csv", "text/csv")

    if st.session_state.live_errors:
        with st.expander(f"Locations that could not be fetched ({len(st.session_state.live_errors)})"):
            st.write("\n".join(st.session_state.live_errors))

st.divider()
st.header("📊 Historical precipitation analysis")
st.caption("Source: your uploaded precipitation-ind-csv-1.csv | 2010–2011 monthly observation dates")

hist, hist_error = load_historical()
if hist_error:
    st.error(hist_error)
elif hist is not None:
    st.warning(
        "Historical dataset values are displayed in their original source scale. "
        "The CSV does not identify a physical measurement unit in its supplied columns; "
        "do not interpret station-value sums as India's total area rainfall."
    )
    years = sorted(hist["year"].dropna().unique().tolist())
    chosen_years = st.multiselect("Historical year filter", years, default=years, key="hist_years")
    h = hist[hist["year"].isin(chosen_years)].copy()
    h1, h2, h3, h4 = st.columns(4)
    h1.metric("Historical records", f"{len(h):,}")
    h2.metric("Weather stations", f"{h['station'].nunique():,}")
    h3.metric("Average recorded value", f"{h['value'].mean():,.2f}")
    h4.metric("Maximum recorded value", f"{h['value'].max():,.0f}")

    monthly = h.groupby("date", as_index=False).agg(
        average_value=("value", "mean"), station_value_sum=("value", "sum")
    ).sort_values("date")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Monthly average recorded value")
        f = px.line(monthly, x="date", y="average_value", markers=True,
                    labels={"date": "Month", "average_value": "Average source value"},
                    template="plotly_white")
        st.plotly_chart(f, use_container_width=True)
    with c2:
        st.subheader("Year-wise average comparison")
        yearly = h.groupby("year", as_index=False)["value"].mean()
        f = px.bar(yearly, x="year", y="value", text_auto=".2f",
                   labels={"year": "Year", "value": "Average source value"},
                   template="plotly_white")
        st.plotly_chart(f, use_container_width=True)

    st.subheader("Top 10 historical stations by sum of recorded values")
    top = h.groupby("station", as_index=False)["value"].sum().nlargest(10, "value")
    f = px.bar(top.sort_values("value"), x="value", y="station", orientation="h",
               labels={"value": "Sum of source values", "station": "Station ID"},
               template="plotly_white")
    st.plotly_chart(f, use_container_width=True)

    with st.expander("View historical source data"):
        st.dataframe(h, use_container_width=True, hide_index=True)
        st.download_button("Download filtered historical data", h.to_csv(index=False).encode("utf-8"),
                           "historical_precipitation_filtered.csv", "text/csv")

st.divider()
st.markdown("""
**Data sources & attribution**
- Historical observations: user-provided `precipitation-ind-csv-1.csv`.
- Live model weather: [Open-Meteo Forecast API](https://open-meteo.com/en/docs).
- Open-Meteo current conditions are model-based and may differ from local rain-gauge readings.
- This dashboard is an educational monitoring project, not an official emergency alert service.
""")
