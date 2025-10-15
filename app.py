import streamlit as st
import pandas as pd
import geopandas as gpd
import pydeck as pdk
import plotly.express as px

import data_loader as dl
import scoring

st.set_page_config(page_title="AU Homebuyer Guide", page_icon="🏠", layout="wide")
st.title("🏠 AU Homebuyer Guide — Production")

missing = []
need = {
    "SA2 boundaries": ("sa2_boundaries_2021.geojson", dl.load_sa2_geojson),
    "ABS G37 (ownership)": ("abs_g37_ownership_sa2.csv", dl.load_abs_g37),
    "SEIFA IRSAD": ("seifa_irsad_sa2.csv", dl.load_seifa_irsad),
}

# optional
optional = {
    "Median sale price": ("medians_sales_sa2.csv", dl.load_medians_sales),
    "Median rent": ("medians_rent_sa2.csv", dl.load_medians_rent),
    "Vacancy": ("vacancy_sa2.csv", dl.load_vacancy),
}

for label, (_, loader) in {**need, **optional}.items():
    try:
        _ = loader()
    except Exception:
        missing.append(label)

if missing:
    with st.warning(f"Missing datasets: {', '.join(missing)}"):
        st.write("Click to fetch what can be fetched automatically.")
        if st.button("📥 Fetch / Refresh datasets now"):
            with st.status("Fetching…", expanded=True) as s:
                from scripts.fetch_full_data import fetch_sa2_boundaries, fetch_abs_g37_owner, fetch_seifa_irsad, build_state_medians, build_vacancy
                if "SA2 boundaries" in missing: fetch_sa2_boundaries()
                if "ABS G37 (ownership)" in missing: fetch_abs_g37_owner()
                if "SEIFA IRSAD" in missing: fetch_seifa_irsad()
                if "Median sale price" in missing or "Median rent" in missing: build_state_medians()
                if "Vacancy" in missing: build_vacancy()
                s.update(label="Done. Reloading…", state="complete")
            st.rerun()

geo = dl.load_sa2_geojson()
own = dl.load_abs_g37()
seifa = dl.load_seifa_irsad()

# optional
try:
    med_sale = dl.load_medians_sales()
except Exception:
    med_sale = None

try:
    med_rent = dl.load_medians_rent()
except Exception:
    med_rent = None

try:
    vac = dl.load_vacancy()
except Exception:
    vac = None

features = geo[["SA2_CODE21","SA2_NAME21","geometry"]].copy()
features["SA2_CODE21"] = features["SA2_CODE21"].astype(str)

features = features.merge(own[["sa2_code21","ownership_pct"]], left_on="SA2_CODE21", right_on="sa2_code21", how="left").drop(columns=["sa2_code21"])
features = features.merge(seifa[["sa2_code21","irsad_rank","irsad_score"]], left_on="SA2_CODE21", right_on="sa2_code21", how="left").drop(columns=["sa2_code21"])

if med_sale is not None:
    features = features.merge(med_sale[["sa2_code21","median_price"]], left_on="SA2_CODE21", right_on="sa2_code21", how="left").drop(columns=["sa2_code21"])
if med_rent is not None:
    features = features.merge(med_rent[["sa2_code21","median_rent"]], left_on="SA2_CODE21", right_on="sa2_code21", how="left").drop(columns=["sa2_code21"])
if vac is not None:
    features = features.merge(vac[["sa2_code21","vacancy_pct"]], left_on="SA2_CODE21", right_on="sa2_code21", how="left").drop(columns=["sa2_code21"])

# derive yield
if "median_price" in features.columns and "median_rent" in features.columns:
    features["yield_pct"] = (pd.to_numeric(features["median_rent"], errors="coerce")*52) / pd.to_numeric(features["median_price"], errors="coerce").replace(0, pd.NA) * 100

# composite score
features["score"] = scoring.score_suburb(features)

with st.sidebar:
    st.header("Filters")
    state_query = st.text_input("State filter (e.g. VIC, NSW, QLD)", "").strip().upper()
    max_price = st.number_input("Max budget (median price, AUD)", min_value=0, value=1_200_000, step=50_000)
    min_yield = st.slider("Min gross rental yield (%)", 0.0, 12.0, 3.5, 0.1)
    max_vacancy = st.slider("Max vacancy (%)", 0.0, 10.0, 3.0, 0.1)
    preset = st.selectbox("Scoring preset", ["Balanced", "Investor (yield focus)", "Owner-occupier (liveability)"])

def weights_from_preset(preset: str):
    if preset == "Investor (yield focus)":
        return {"ownership_pct": 0.10,"irsad_rank":-0.05,"median_price":-0.10,"median_rent":0.10,"vacancy_pct":-0.35,"growth_1y":0.10,"yield_pct":0.30}
    if preset == "Owner-occupier (liveability)":
        return {"ownership_pct": 0.25,"irsad_rank":-0.20,"median_price":-0.15,"median_rent":0.00,"vacancy_pct":-0.15,"growth_1y":0.10,"yield_pct":0.15}
    return None

w = weights_from_preset(preset)
if w is not None:
    features["score"] = scoring.score_suburb(features, weights=w)

df = features.copy()
if state_query:
    df = df[df["SA2_NAME21"].str.upper().str.contains(state_query)]
if "median_price" in df.columns:
    df = df[(df["median_price"].isna()) | (df["median_price"] <= max_price)]
if "yield_pct" in df.columns:
    df = df[(df["yield_pct"].isna()) | (df["yield_pct"] >= min_yield)]
if "vacancy_pct" in df.columns:
    df = df[(df["vacancy_pct"].isna()) | (df["vacancy_pct"] <= max_vacancy)]

st.subheader("Top suburbs (SA2)")
cols = ["SA2_NAME21","score","ownership_pct","irsad_rank","median_price","median_rent","yield_pct","vacancy_pct"]
present_cols = [c for c in cols if c in df.columns]
ranked = df.drop(columns="geometry")[present_cols].sort_values("score", ascending=False).head(200)
st.dataframe(ranked, use_container_width=True)

st.subheader("Map")
df_map = df[["SA2_CODE21","SA2_NAME21","score","geometry"]].dropna(subset=["geometry"]).copy()
gjson = gpd.GeoSeries(df_map.set_geometry("geometry").geometry).to_json()

layer = pdk.Layer(
    "GeoJsonLayer",
    data=gjson,
    pickable=True,
    stroked=False,
    filled=True,
    extruded=False,
    get_fill_color=[
        "255*(1 - (properties.score/100))",
        "255*(properties.score/100)",
        "80"
    ],
    get_line_color=[200,200,200],
)

view_state = pdk.ViewState(latitude=-25.0, longitude=133.0, zoom=3.5, pitch=0)
r = pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip={"text": "{SA2_NAME21}\nScore: {score}"})
st.pydeck_chart(r)

st.caption("Sources: ABS 2021, Digital Atlas, state open data portals. Vacancy/rent sources depend on your configuration.")
