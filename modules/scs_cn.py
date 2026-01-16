# modules/scs_cn.py
import numpy as np
import pandas as pd


def scs_parameters(
    curve_number: float,
    ia_factor: float = 0.2
):
    """
    Hitung parameter SCS

    S = (25400 / CN) - 254
    Ia = Ia_factor * S
    """
    if not 30 <= curve_number <= 98:
        raise ValueError("Curve Number harus antara 30 – 98")

    S = (25400 / curve_number) - 254
    Ia = ia_factor * S

    return S, Ia


def runoff_total(
    total_rainfall_mm: float,
    curve_number: float,
    ia_factor: float = 0.2
):
    """
    Limpasan total (mm) - SCS CN klasik
    """
    S, Ia = scs_parameters(curve_number, ia_factor)

    if total_rainfall_mm <= Ia:
        return 0.0

    Q = ((total_rainfall_mm - Ia) ** 2) / (
        total_rainfall_mm - Ia + S
    )
    return Q


def runoff_hyetograph(
    rainfall_df: pd.DataFrame,
    curve_number: float,
    ia_factor: float = 0.2
):
    """
    Distribusi limpasan per time step
    """
    P_total = rainfall_df["rainfall_mm"].sum()
    Q_total = runoff_total(P_total, curve_number, ia_factor)

    if Q_total == 0:
        rainfall_df["runoff_mm"] = 0.0
        return rainfall_df, 0.0

    ratio = rainfall_df["rainfall_mm"] / P_total
    rainfall_df["runoff_mm"] = ratio * Q_total

    return rainfall_df, Q_total


def runoff_volume_m3(
    runoff_mm: float,
    area_ha: float
):
    """
    Konversi runoff (mm) → volume (m3)
    """
    area_m2 = area_ha * 10_000
    return runoff_mm / 1000 * area_m2
