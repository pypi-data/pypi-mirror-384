"""Data module for PatX package."""

import numpy as np
from pathlib import Path
import pyarrow.parquet as pq

def get_data_path():
    """Get the path to the data directory."""
    return Path(__file__).parent

def load_remc_data(series=("H3K4me3", "H3K4me1")):
    """
    Load the REMC data as separate numpy arrays per series (multiple time series).
    Only the requested series are returned, defaulting to two: H3K4me3, H3K4me1.
    """
    data_path = get_data_path() / "E003.parquet"
    table = pq.read_table(data_path)
    column_names = table.column_names
    
    y = table.column('target').to_numpy()
    X_list = []
    series_names = []
    for s in series:
        cols = [c for c in column_names if c.startswith(f"{s}_")]
        if not cols:
            continue
        cols.sort(key=lambda x: int(x.split('_')[1]))
        X_series = np.column_stack([table.column(c).to_numpy() for c in cols])
        X_list.append(X_series)
        series_names.append(s)

    X_combined = np.concatenate(X_list, axis=1) if X_list else np.empty((len(y), 0))

    return {
        'X_list': X_list,
        'y': y,
        'X': X_combined,
        'series_names': series_names,
    }
