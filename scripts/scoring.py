import numpy as np
import pandas as pd

def normalize(series):
    if series.empty or series.isna().all():
        return pd.Series([0] * len(series))
    return (series - series.min()) / (series.max() - series.min() + 1e-6)

def score_suburb(df):
    """Weighted score: higher ownership, higher SEIFA, lower vacancy."""
    score = (
        0.4 * normalize(df["ownership_pct"]) +
        0.4 * normalize(df["irsad_rank"]) +
        0.2 * (1 - normalize(df["vacancy_rate"]))
    ) * 100
    return np.round(score, 1)
