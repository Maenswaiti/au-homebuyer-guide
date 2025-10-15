import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium
from scripts.fetch_full_data import fetch_all_datasets

st.set_page_config(page_title="AU Homebuyer Guide", layout="wide")

st.title("🏡 Australian Homebuyer Guide")
st.write("Explore housing affordability, ownership, and vacancy by SA2 region.")

# --- Load datasets ---
st.write("Fetching SA2 boundaries...")

geo_path = "geometry/sa2_boundaries.geojson"
own_path = "data/ownership.csv"
seifa_path = "data/seifa.csv"
vac_path = "data/vacancy.csv"

try:
    geo = gpd.read_file(geo_path)
    own = pd.read_csv(own_path)
    seifa = pd.read_csv(seifa_path)
    vac = pd.read_csv(vac_path)
except Exception:
    st.warning("Missing or incomplete datasets, fetching from ABS API...")
    fetch_all_datasets()
    geo = gpd.read_file(geo_path)
    own = pd.read_csv(own_path)
    seifa = pd.read_csv(seifa_path)
    vac = pd.read_csv(vac_path)

# --- Prepare merge keys robustly ---
code_col = None
for c in geo.columns:
    if "sa2_code" in c.lower():
        code_col = c
        break
if not code_col:
    st.error(f"GeoJSON columns: {list(geo.columns)} — could not find SA2 code column.")
    st.stop()

name_col = None
for c in geo.columns:
    if "sa2_name" in c.lower():
        name_col = c
        break
if not name_col:
    st.error(f"GeoJSON columns: {list(geo.columns)} — could not find SA2 name column.")
    st.stop()

geo = geo.rename(columns={code_col: "SA2_CODE21", name_col: "SA2_NAME_2021"})
geo["SA2_CODE21"] = geo["SA2_CODE21"].astype(str)

own["sa2_code21"] = own.get("sa2_code21", pd.Series(dtype=str)).astype(str)
seifa["sa2_code21"] = seifa.get("sa2_code21", pd.Series(dtype=str)).astype(str)
vac["sa2_code21"] = vac.get("sa2_code21", pd.Series(dtype=str)).astype(str)

# --- Merge datasets ---
features = (
    geo[["SA2_CODE21", "SA2_NAME_2021", "geometry"]]
    .merge(own, left_on="SA2_CODE21", right_on="sa2_code21", how="left")
    .merge(seifa, left_on="SA2_CODE21", right_on="sa2_code21", how="left")
    .merge(vac, left_on="SA2_CODE21", right_on="sa2_code21", how="left")
)

gdf = gpd.GeoDataFrame(features, geometry="geometry")

# --- Sidebar controls ---
st.sidebar.header("Filters")
metric = st.sidebar.selectbox(
    "Choose a metric to visualize",
    [
        "ownership_pct",
        "vacancy_pct",
        "seifa_score",
    ],
    format_func=lambda x: {
        "ownership_pct": "🏠 Ownership %",
        "vacancy_pct": "🏢 Vacancy %",
        "seifa_score": "💰 SEIFA (Socioeconomic Index)"
    }[x]
)

# --- Map visualization ---
st.subheader("Map View")
st.caption("Click on an SA2 region for more details.")

map_center = [-25.0, 133.0]
m = folium.Map(location=map_center, zoom_start=4, tiles="cartodbpositron")

# Determine color metric
if metric not in gdf.columns:
    st.error(f"Selected metric '{metric}' not found in data columns: {list(gdf.columns)}")
    st.stop()

folium.Choropleth(
    geo_data=gdf,
    data=gdf,
    columns=["SA2_CODE21", metric],
    key_on="feature.properties.SA2_CODE21",
    fill_color="YlGnBu",
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name=metric.replace("_", " ").title(),
).add_to(m)

# Add tooltips
folium.GeoJsonTooltip(
    fields=["SA2_NAME_2021", metric],
    aliases=["Area:", f"{metric.replace('_', ' ').title()}: "],
).add_to(folium.GeoJson(gdf).add_to(m))

st_data = st_folium(m, width=1200, height=700)

# --- Data table ---
st.subheader("📊 Data Table")
st.dataframe(
    gdf[["SA2_NAME_2021", "ownership_pct", "vacancy_pct", "seifa_score"]].sort_values(
        by=metric, ascending=False
    ),
    use_container_width=True,
)

st.success("✅ Data successfully loaded and visualized!")
