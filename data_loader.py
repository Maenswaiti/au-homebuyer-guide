import os
import pandas as pd
import geopandas as gpd

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "data", "processed")

def _path(name: str) -> str:
    return os.path.join(PROCESSED_DIR, name)

def _ensure_dir():
    os.makedirs(PROCESSED_DIR, exist_ok=True)

def load_sa2_geojson() -> gpd.GeoDataFrame:
    _ensure_dir()
    path = _path("sa2_boundaries_2021.geojson")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing {path}. Run scripts/fetch_full_data.py or use the button in the app.")
    gdf = gpd.read_file(path)
    if "SA2_CODE21" not in gdf.columns:
        for c in gdf.columns:
            if c.lower() in ("sa2_code21","sa2_code_2021","sa2_code"):
                gdf["SA2_CODE21"] = gdf[c]
                break
    gdf["SA2_CODE21"] = gdf["SA2_CODE21"].astype(str)
    return gdf[["SA2_CODE21","SA2_NAME21","geometry"]] if "SA2_NAME21" in gdf.columns else gdf

def load_abs_g37() -> pd.DataFrame:
    _ensure_dir()
    path = _path("abs_g37_ownership_sa2.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing {path}.")
    df = pd.read_csv(path, dtype={"sa2_code21":"string"})
    df["sa2_code21"] = df["sa2_code21"].astype(str)
    return df

def load_seifa_irsad() -> pd.DataFrame:
    _ensure_dir()
    path = _path("seifa_irsad_sa2.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing {path}.")
    df = pd.read_csv(path, dtype={"sa2_code21":"string"})
    df["sa2_code21"] = df["sa2_code21"].astype(str)
    return df

def load_medians_sales() -> pd.DataFrame:
    _ensure_dir()
    path = _path("medians_sales_sa2.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing {path}.")
    df = pd.read_csv(path, dtype={"sa2_code21":"string"})
    df["sa2_code21"] = df["sa2_code21"].astype(str)
    return df

def load_medians_rent() -> pd.DataFrame:
    _ensure_dir()
    path = _path("medians_rent_sa2.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing {path}.")
    df = pd.read_csv(path, dtype={"sa2_code21":"string"})
    df["sa2_code21"] = df["sa2_code21"].astype(str)
    return df

def load_vacancy() -> pd.DataFrame:
    _ensure_dir()
    path = _path("vacancy_sa2.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing {path}.")
    df = pd.read_csv(path, dtype={"sa2_code21":"string"})
    df["sa2_code21"] = df["sa2_code21"].astype(str)
    return df
