import os
import geopandas as gpd
import pandas as pd

GEO_PATH = "geometry/sa2_2021_simplified.geojson"
DATA_PATH = "data"

def load_sa2_geojson():
    if not os.path.exists(GEO_PATH):
        raise FileNotFoundError(f"Missing geometry file: {GEO_PATH}")
    return gpd.read_file(GEO_PATH)

def load_ownership():
    p = os.path.join(DATA_PATH, "ownership.csv")
    if os.path.exists(p):
        return pd.read_csv(p, dtype={"sa2_code21": str})
    return pd.DataFrame(columns=["sa2_code21", "ownership_pct"])

def load_seifa():
    p = os.path.join(DATA_PATH, "seifa.csv")
    if os.path.exists(p):
        return pd.read_csv(p, dtype={"sa2_code21": str})
    return pd.DataFrame(columns=["sa2_code21", "irsad_rank"])

def load_vacancy():
    p = os.path.join(DATA_PATH, "vacancy.csv")
    if os.path.exists(p):
        return pd.read_csv(p, dtype={"sa2_code21": str})
    return pd.DataFrame(columns=["sa2_code21", "vacancy_rate"])

def load_vic_medians():
    p = os.path.join(DATA_PATH, "vic_medians.csv")
    if os.path.exists(p):
        return pd.read_csv(p, dtype={"postcode": str})
    return pd.DataFrame(columns=["postcode", "median_price"])

def load_all_data():
    geo = load_sa2_geojson()
    own = load_ownership()
    seifa = load_seifa()
    vac = load_vacancy()
    med = load_vic_medians()
    return geo, own, seifa, vac, med
