import streamlit as st
import pandas as pd
import requests
import datetime
import time
import pydeck as pdk

# ------------------ PAGE ------------------
st.set_page_config(page_title="AQI Dashboard", layout="wide")
st.title("🌍 Air Quality Monitoring Dashboard")

# ------------------ API SETTINGS ------------------
waqi_token = "44192d58f58d96613ec4baa6fc99637b2d33956f"

# OpenWeather
owm_api_key = "aa342999f962c6f8d9b71a89ae8661a8"

# ------------------ CITY SELECTION ------------------
cities = {
    "Hyderabad": (17.385, 78.486),
    "Delhi": (28.6139, 77.2090),
    "Mumbai": (19.0760, 72.8777),
    "Bangalore": (12.9716, 77.5946),
    "Chennai": (13.0827, 80.2707),
    "Kolkata": (22.5726, 88.3639),
}

selected_city = st.selectbox("Select City", list(cities.keys()))
lat, lon = cities[selected_city]

# ------------------ LIVE DATA ------------------
url = f"https://api.waqi.info/feed/geo:{lat};{lon}/?token={waqi_token}"
res = requests.get(url)
data = res.json()

pm25 = pm10 = no2 = so2 = co = o3 = 0

if data["status"] == "ok":
    iaqi = data["data"]["iaqi"]
    pm25 = iaqi.get("pm25", {}).get("v", 0)
    pm10 = iaqi.get("pm10", {}).get("v", 0)
    no2 = iaqi.get("no2", {}).get("v", 0)
    so2 = iaqi.get("so2", {}).get("v", 0)
    co = iaqi.get("co", {}).get("v", 0)
    o3 = iaqi.get("o3", {}).get("v", 0)

# ------------------ METRICS ------------------
col1, col2, col3 = st.columns(3)
col1.metric("PM2.5", pm25)
col2.metric("PM10", pm10)
col3.metric("NO2", no2)

# ------------------ BAR CHART ------------------
st.subheader("📊 Pollutant Distribution")

pollutants = {
    "PM2.5": pm25,
    "PM10": pm10,
    "NO2": no2,
    "SO2": so2,
    "CO": co,
    "O3": o3
}

df_poll = pd.DataFrame(list(pollutants.items()), columns=["Pollutant", "Value"])
st.bar_chart(df_poll.set_index("Pollutant"))

# ------------------ MAP ------------------
st.subheader("🗺️ Air Quality Map")

def get_color(aqi):
    if aqi <= 50:
        return [0, 255, 0]
    elif aqi <= 100:
        return [255, 255, 0]
    elif aqi <= 200:
        return [255, 165, 0]
    else:
        return [255, 0, 0]

df_map = pd.DataFrame([{
    "lat": lat,
    "lon": lon,
    "aqi": pm25,
    "color": get_color(pm25)
}])

layer = pdk.Layer(
    "ScatterplotLayer",
    data=df_map,
    get_position='[lon, lat]',
    get_color='color',
    get_radius=80000,
)

view_state = pdk.ViewState(
    latitude=lat,
    longitude=lon,
    zoom=8,
)

st.pydeck_chart(pdk.Deck(
    layers=[layer],
    initial_view_state=view_state
))

# ------------------ 24H TREND ------------------
st.subheader("📈 24-Hour Trend")

end = int(time.time())
start = end - 24 * 3600

hist_url = (
    f"http://api.openweathermap.org/data/2.5/air_pollution/history"
    f"?lat={lat}&lon={lon}&start={start}&end={end}&appid={owm_api_key}"
)

resp_hist = requests.get(hist_url)

if resp_hist.status_code == 200:
    hist = resp_hist.json()

    times = [datetime.datetime.fromtimestamp(x['dt']) for x in hist['list']]
    pm25_hist = [x['components']['pm2_5'] for x in hist['list']]
    pm10_hist = [x['components']['pm10'] for x in hist['list']]

    df_hist = pd.DataFrame({
        "PM2.5": pm25_hist,
        "PM10": pm10_hist
    }, index=times)

    st.line_chart(df_hist)

# ------------------ AUTO REFRESH ------------------
time.sleep(30)
st.rerun()
