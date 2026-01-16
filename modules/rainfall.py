# modules/rainfall.py
import pandas as pd
import numpy as np


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
