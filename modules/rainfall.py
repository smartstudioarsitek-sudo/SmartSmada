# modules/rainfall.py
import pandas as pd
import numpy as np

from scipy.stats import pearson3

def log_pearson_3(data_series, return_periods=[2, 5, 10, 25, 50, 100]):
    """
    Menghitung Hujan Rencana Log Pearson III (SNI 2415:2016)
    """
    log_data = np.log10(data_series)
    mean = np.mean(log_data)
    std = np.std(log_data, ddof=1)
    skew = pd.Series(log_data).skew()
    
    results = {}
    for T in return_periods:
        # Sederhananya menggunakan K-table approximation atau scipy
        prob = 1 / T
        # Mencari nilai K berdasarkan skewness dan probabilitas
        # Catatan: Scipy pearson3 menggunakan parameter berbeda, 
        # Untuk implementasi PU yang presisi, disarankan menggunakan tabel K-faktor statis.
        k = pearson3.ppf(1 - prob, skew) 
        log_rt = mean + k * std
        results[T] = 10**log_rt
        
    return results

def mononobe_intensity(r24, tc_min):
    """
    Rumus Mononobe untuk Intensitas Hujan (Standard PU)
    """
    return (r24 / 24) * (24 / (tc_min / 60))**(2/3)


def rainfall_manual(
    rainfall_mm: list,
    dt_min: float
):
    """
    Membuat data hujan dari input manual (hyetograph).

    Parameters
    ----------
    rainfall_mm : list
        Curah hujan tiap time step (mm)
    dt_min : float
        Interval waktu (menit)

    Returns
    -------
    DataFrame
        time_min, rainfall_mm, cumulative_mm
    """
    time = np.arange(0, len(rainfall_mm) * dt_min, dt_min)
    cum = np.cumsum(rainfall_mm)

    df = pd.DataFrame({
        "time_min": time,
        "rainfall_mm": rainfall_mm,
        "cumulative_mm": cum
    })
    return df


def scs_dimensionless_curve(
    total_rainfall_mm: float,
    duration_hr: float,
    dt_min: float,
    curve_type: str = "type_II"
):
    """
    Membuat hujan berbasis kurva dimensi SCS.

    curve_type:
    - 'type_I'
    - 'type_IA'
    - 'type_II'
    - 'type_III'
    """

    # Distribusi relatif sederhana (bisa dikembangkan)
    scs_ratio = {
        "type_II": [0.02, 0.05, 0.15, 0.30, 0.28, 0.15, 0.05],
        "type_III": [0.01, 0.03, 0.10, 0.35, 0.30, 0.15, 0.06]
    }

    if curve_type not in scs_ratio:
        raise ValueError("Jenis kurva SCS tidak tersedia")

    ratio = np.array(scs_ratio[curve_type])
    ratio = ratio / ratio.sum()

    rainfall_step = ratio * total_rainfall_mm
    dt_curve = duration_hr * 60 / len(ratio)

    time = np.arange(0, duration_hr * 60, dt_curve)
    cum = np.cumsum(rainfall_step)

    df = pd.DataFrame({
        "time_min": time,
        "rainfall_mm": rainfall_step,
        "cumulative_mm": cum
    })
    return df


def import_rainfall_csv(
    filepath: str,
    dt_min: float
):
    """
    Import hujan dari file CSV (1 kolom hujan).

    CSV format:
    rainfall_mm
    """
    df = pd.read_csv(filepath)

    time = np.arange(0, len(df) * dt_min, dt_min)
    df["time_min"] = time
    df["cumulative_mm"] = df.iloc[:, 0].cumsum()

    df.columns = ["rainfall_mm", "time_min", "cumulative_mm"]
    return df


def rainfall_summary(df):
    """
    Ringkasan hujan
    """
    return {
        "total_rainfall_mm": df["rainfall_mm"].sum(),
        "max_intensity_mm_hr": df["rainfall_mm"].max() * 60 / (df["time_min"].diff().mean()),
        "duration_min": df["time_min"].max()
    }

