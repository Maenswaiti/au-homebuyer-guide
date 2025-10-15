import numpy as np
import pandas as pd

def _norm(series: pd.Series) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce")
    lo, hi = s.quantile(0.02), s.quantile(0.98)
    s = (s.clip(lo, hi) - lo) / max(hi - lo, 1e-9)
    return s.fillna(0.0)

def score_suburb(df: pd.DataFrame, weights=None) -> pd.Series:
    if weights is None:
        weights = {
            "ownership_pct": 0.15,
            "irsad_rank":   -0.10,
            "median_price": -0.20,
            "median_rent":   0.10,
            "vacancy_pct":  -0.25,
            "growth_1y":     0.10,
            "yield_pct":     0.20,
        }
    d = df.copy()

    if "yield_pct" not in d.columns and {"median_rent","median_price"} <= set(d.columns):
        d["yield_pct"] = (pd.to_numeric(d["median_rent"], errors="coerce")*52) / pd.to_numeric(d["median_price"], errors="coerce").replace(0, np.nan) * 100

    if "growth_1y" not in d.columns:
        d["growth_1y"] = np.nan

    score = 0.0
    total_w = 0.0
    for k, w in weights.items():
        if k not in d.columns:
            continue
        v = _norm(d[k])
        if w < 0:
            v = 1.0 - v
        score += w * v
        total_w += abs(w)

    if total_w == 0:
        return pd.Series([50.0]*len(d), index=d.index)

    score = (score / total_w) * 100.0
    return score.clip(0, 100).fillna(0)
