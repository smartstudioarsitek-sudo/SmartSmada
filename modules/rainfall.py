# modules/rainfall.py
import pandas as pd
import numpy as np
from scipy.stats import pearson3

def log_pearson_3(data_series, return_periods=[2, 5, 10, 25, 50, 100]):
    """Menghitung Hujan Rencana Log Pearson III (SNI 2415:2016)"""
    # Pastikan data dalam format logaritmik
    log_data = np.log10(data_series)
    mean = np.mean(log_data)
    std = np.std(log_data, ddof=1)
    skew = pd.Series(log_data).skew()
    
    results = {}
    for T in return_periods:
        prob = 1 / T
        # Menggunakan scipy untuk mencari faktor K (Faktor Frekuensi)
        k = pearson3.ppf(1 - prob, skew) 
        log_rt = mean + k * std
        results[f"R{T}"] = 10**log_rt
    return results

def mononobe_intensity(r24, tc_min):
    """Rumus Mononobe untuk Intensitas Hujan (Standard PU)"""
    tc_hr = tc_min / 60
    # I = (R24/24) * (24/tc)^(2/3)
    return (r24 / 24) * (24 / tc_hr)**(2/3)

def rainfall_manual(rainfall_mm: list, dt_min: float):
    time = np.arange(0, len(rainfall_mm) * dt_min, dt_min)
    df = pd.DataFrame({
        "time_min": time,
        "rainfall_mm": rainfall_mm,
        "cumulative_mm": np.cumsum(rainfall_mm)
    })
    return df
