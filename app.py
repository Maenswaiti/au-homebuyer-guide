import streamlit as st
import pandas as pd
import numpy as np
import geopandas as gpd
import plotly.express as px
import json
import os

from scripts.fetch_full_data import (
    fetch_sa2_boundaries,
    fetch_all_datasets
)
from scripts.data_loader import load_all_data
from scripts.scoring import score_suburb

st.set_page_config(page_title="🏠 AU Homebuyer Guide — Production", layout="wide")

st.title("🏠 AU Homebuyer Guide — Production")
st.caption("Explore affordability, lifestyle, and investment insights across all Australian suburbs")

# ================================
# 🔹 Fetch or load data
# ================================
DATA_PATH = "data"
GEO_PATH = "geometry/sa2_2021_simplified.geojson"

if not os.path.exists(DATA_PATH):
    os.makedirs(DATA_PATH, exist_ok=True)

missing = []
if not os.path.exists(GEO_PATH):
    missing.append("SA2 boundaries")

required_files = [
    "ownership.csv",
    "seifa.csv",
    "vacancy.csv",
    "vic_medians.csv"
]

for f in required_files:
    if not os.path.exists(os.path.join(DATA_PATH, f)):
        missing.append(f)

if missing:
    st.warning(f"Missing data detected: {', '.join(missing)}. Attempting to fetch...")
    try:
        if "SA2 boundaries" in missing:
            fetch_sa2_boundaries()
        fetch_all_datasets()
        st.success("Data successfully fetched.")
    except Exception as e:
        st.error(f"Data fetch failed: {e}")

# ================================
# 🔹 Load data
# ================================
geo, own, seifa, vac, med = load_all_data()

# Ensure data types align
geo["SA2_CODE21"] = geo["SA2_CODE21"].astype(str)
own["sa2_code21"] = own["sa2_code21"].astype(str)
seifa["sa2_code21"] = seifa["sa2_code21"].astype(str)
vac["sa2_code21"] = vac["sa2_code21"].astype(str)
med["postcode"] = med["postcode"].astype(str)

# ================================
# 🔹 Merge features
# ================================
features = (
    geo[["SA2_CODE21", "SA2_NAME21", "geometry"]]
    .merge(own[["sa2_code21", "ownership_pct"]], left_on="SA2_CODE21", right_on="sa2_code21", how="left")
    .merge(seifa[["sa2_code21", "irsad_rank"]], left_on="SA2_CODE21", right_on="sa2_code21", how="left")
    .merge(vac[["sa2_code21", "vacancy_rate"]], left_on="SA2_CODE21", right_on="sa2_code21", how="left")
)

# ================================
# 🔹 Apply scoring
# ================================
features["score"] = score_suburb(features)

# ================================
# 🔹 UI Filters
# ================================
st.sidebar.header("Filters")
min_rank, max_rank = st.sidebar.slider("SEIFA (Socioeconomic Rank)", 1, 100, (20, 80))
max_vacancy = st.sidebar.slider("Max Vacancy Rate (%)", 0.0, 10.0, 4.0)

filtered = features[
    (features["irsad_rank"].between(min_rank, max_rank))
    & (features["vacancy_rate"] <= max_vacancy)
]

# ================================
# 🔹 Visualization
# ================================
st.subheader("Australian Suburb Insights")

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
        title="Suburb Attractiveness Score"
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No suburbs match your filter criteria.")

# ================================
# 🔹 Data Table
# ================================
st.subheader("Detailed Data Table")
st.dataframe(filtered[["SA2_NAME21", "ownership_pct", "irsad_rank", "vacancy_rate", "score"]])
