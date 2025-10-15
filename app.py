import os
import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import json

from scripts.fetch_full_data import fetch_all_datasets, fetch_sa2_boundaries
from scripts.data_loader import load_all_data
from scripts.scoring import score_suburb

st.set_page_config(page_title="AU Homebuyer Guide", layout="wide")

st.title("🏠 AU Homebuyer Guide — Production")

# Ensure geometry file
geo_file = "geometry/sa2_2021_simplified.geojson"
if not os.path.exists(geo_file):
    st.warning("Downloading SA2 boundaries...")
    try:
        fetch_sa2_boundaries()
    except Exception as e:
        st.error(f"Failed to fetch boundaries: {e}")

# Ensure datasets
required = ["ownership.csv"]
missing = [f for f in required if not os.path.exists(os.path.join("data", f))]
if missing:
    st.warning(f"Missing datasets: {missing} — fetching from ABS API...")
    try:
        fetch_all_datasets()
    except Exception as e:
        st.error(f"Failed to fetch datasets: {e}")

# Load data
try:
    geo, own, seifa, vac, med = load_all_data()
except Exception as e:
    st.error(f"Load data failed: {e}")
    st.stop()

# Prepare merge keys
# Prepare merge keys (robust handling)
code_col = None
for c in geo.columns:
    if "SA2_CODE" in c:
        code_col = c
        break
if not code_col:
    st.error(f"GeoJSON columns: {list(geo.columns)} — could not find SA2 code column.")
    st.stop()

geo = geo.rename(columns={code_col: "SA2_CODE21"})
geo["SA2_CODE21"] = geo["SA2_CODE21"].astype(str)

own["sa2_code21"] = own.get("sa2_code21", pd.Series(dtype=str)).astype(str)
seifa["sa2_code21"] = seifa.get("sa2_code21", pd.Series(dtype=str)).astype(str)
vac["sa2_code21"] = vac.get("sa2_code21", pd.Series(dtype=str)).astype(str)

# Merge
features = (
    geo[["SA2_CODE21", "SA2_NAME_2021", "geometry"]]
    .merge(own, left_on="SA2_CODE21", right_on="sa2_code21", how="left")
    .merge(seifa, left_on="SA2_CODE21", right_on="sa2_code21", how="left")
    .merge(vac, left_on="SA2_CODE21", right_on="sa2_code21", how="left")
)

features["score"] = score_suburb(features)

# Sidebar
st.sidebar.header("Filters")
min_rank, max_rank = st.sidebar.slider("IRSAD Rank Range", 1, 100, (20, 80))
max_vac = st.sidebar.slider("Max Vacancy (%)", 0.0, 10.0, 4.0)

df = features[
    (features["irsad_rank"].between(min_rank, max_rank, inclusive="both")) &
    (features.get("vacancy_rate", 0) <= max_vac)
]

# Map
st.subheader("Suburb Scores Map")
if not df.empty:
    fig = px.choropleth_mapbox(
        df,
        geojson=json.loads(df.to_json()),
        locations="SA2_CODE21",
        color="score",
        hover_name="SA2_NAME_2021",
        hover_data=["ownership_pct", "irsad_rank", "vacancy_rate"],
        mapbox_style="carto-positron",
        center={"lat": -25, "lon": 134},
        zoom=3.5,
        opacity=0.6,
        color_continuous_scale="YlGnBu"
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No suburbs match filters.")

# Table
st.subheader("Detailed Data")
st.dataframe(
    df[["SA2_NAME_2021", "ownership_pct", "irsad_rank", "vacancy_rate", "score"]]
    .sort_values("score", ascending=False)
    .reset_index(drop=True)
)
