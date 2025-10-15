import streamlit as st
import pandas as pd
import geopandas as gpd
import numpy as np
import plotly.express as px
import json
import os

from scripts.fetch_full_data import fetch_sa2_boundaries, fetch_all_datasets
from scripts.data_loader import load_all_data
from scripts.scoring import score_suburb

st.set_page_config(page_title="🏠 AU Homebuyer Guide — Production", layout="wide")

st.title("🏠 AU Homebuyer Guide — Production")
st.caption("The complete data-driven guide to buying a home in Australia — affordability, livability, and growth insights across all suburbs.")

# ================================
# 🔹 Setup and data paths
# ================================
DATA_PATH = "data"
GEO_PATH = "geometry/sa2_2021_simplified.geojson"

os.makedirs(DATA_PATH, exist_ok=True)
os.makedirs("geometry", exist_ok=True)

# ================================
# 🔹 Ensure GeoJSON exists
# ================================
if not os.path.exists(GEO_PATH):
    st.warning("Downloading SA2 boundaries from ABS (first-time setup)...")
    try:
        fetch_sa2_boundaries()
        st.success("✅ SA2 boundaries downloaded successfully.")
    except Exception as e:
        st.error(f"Failed to download SA2 boundaries: {e}")

# ================================
# 🔹 Ensure data CSVs exist
# ================================
required_files = [
    "ownership.csv",
    "seifa.csv",
    "vacancy.csv",
    "vic_medians.csv"
]
missing = [f for f in required_files if not os.path.exists(os.path.join(DATA_PATH, f))]

if missing:
    st.warning(f"Missing datasets detected: {', '.join(missing)} — fetching now...")
    try:
        fetch_all_datasets()
        st.success("✅ All datasets successfully fetched.")
    except Exception as e:
        st.error(f"Failed to fetch datasets: {e}")

# ================================
# 🔹 Load data
# ================================
try:
    geo, own, seifa, vac, med = load_all_data()
except Exception as e:
    st.error(f"❌ Failed to load data: {e}")
    st.stop()

# ================================
# 🔹 Data cleanup
# ================================
for df, cols in [(own, ["sa2_code21"]), (seifa, ["sa2_code21"]), (vac, ["sa2_code21"]), (med, ["postcode"])]:
    for c in cols:
        if c in df.columns:
            df[c] = df[c].astype(str)

if "SA2_CODE21" not in geo.columns:
    st.error("GeoJSON missing expected column 'SA2_CODE21'. Please check the file integrity.")
    st.stop()

# ================================
# 🔹 Merge features
# ================================
features = (
    geo[["SA2_CODE21", "SA2_NAME21", "geometry"]]
    .merge(own[["sa2_code21", "ownership_pct"]], left_on="SA2_CODE21", right_on="sa2_code21", how="left")
    .merge(seifa[["sa2_code21", "irsad_rank"]], left_on="SA2_CODE21", right_on="sa2_code21", how="left")
    .merge(vac[["sa2_code21", "vacancy_rate"]], left_on="SA2_CODE21", right_on="sa2_code21", how="left")
)

features["score"] = score_suburb(features)

# ================================
# 🔹 Sidebar filters
# ================================
st.sidebar.header("Filter Suburbs")

min_rank, max_rank = st.sidebar.slider(
    "SEIFA (Socioeconomic Rank Range)",
    1, 100, (20, 80)
)

max_vacancy = st.sidebar.slider(
    "Max Vacancy Rate (%)",
    0.0, 10.0, 4.0
)

filtered = features[
    (features["irsad_rank"].between(min_rank, max_rank, inclusive="both")) &
    (features["vacancy_rate"] <= max_vacancy)
]

# ================================
# 🔹 Visualization
# ================================
st.subheader("🏡 Suburb Attractiveness Map")

if not filtered.empty:
    fig = px.choropleth_mapbox(
        filtered,
        geojson=json.loads(filtered.to_json()),
        locations="SA2_CODE21",
        color="score",
        hover_name="SA2_NAME21",
        hover_data=["ownership_pct", "irsad_rank", "vacancy_rate"],
        mapbox_style="carto-positron",
        center={"lat": -25.0, "lon": 134.0},
        zoom=3.5,
        opacity=0.6,
        color_continuous_scale="YlGnBu",
        title="Overall Suburb Score"
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No suburbs match the selected criteria.")

# ================================
# 🔹 Data table
# ================================
st.subheader("📊 Detailed Suburb Data")
st.dataframe(
    filtered[["SA2_NAME21", "ownership_pct", "irsad_rank", "vacancy_rate", "score"]]
    .sort_values("score", ascending=False)
    .reset_index(drop=True)
)
