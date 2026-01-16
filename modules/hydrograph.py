# modules/hydrograph.py
import numpy as np
import pandas as pd


def hss_nakayasu(area_ha, L_km, tg_hour=None, alpha=2.0, tr_hour=None, dt_min=10):
    """
    Implementasi Hidrograf Satuan Sintetik Nakayasu (Standar SNI)
    """
    area_km2 = area_ha / 100
    
    # 1. Menghitung Time Lag (tg) jika tidak diinput
    if tg_hour is None:
        if L_km < 15:
            tg = 0.21 * (L_km**0.7)
        else:
            tg = 0.4 + 0.058 * L_km
    else:
        tg = tg_hour

    # 2. Parameter Waktu
    tr = 0.75 * tg if tr_hour is None else tr_hour # Durasi hujan efektif
    tp = tg + 0.8 * tr                            # Time to peak
    t03 = alpha * tg                              # Time to 0.3 peak
    
    # 3. Debit Puncak (Qp) per 1 mm hujan
    qp = (area_km2) / (3.6 * (0.3 * tp + t03))
    
    # 4. Membuat Kurva
    t_max = tp + 10 * t03 # Simulasi sampai 10x waktu turun
    time = np.arange(0, t_max * 60, dt_min) / 60
    q = []

    for t in time:
        if t <= tp:
            # Kurva Naik
            val = qp * (t / tp)**2.4
        elif t <= tp + t03:
            # Kurva Turun 1
            val = qp * 0.3**((t - tp) / t03)
        elif t <= tp + t03 + 1.5 * t03:
            # Kurva Turun 2
            val = qp * 0.3**((t - tp + 0.5 * t03) / (1.5 * t03))
        else:
            # Kurva Turun 3
            val = qp * 0.3**((t - tp + 1.5 * t03) / (2 * t03))
        q.append(max(val, 0))

    return pd.DataFrame({"time_min": time * 60, "uh_cms_per_mm": q})


def scs_unit_hydrograph(
    tc_min: float,
    dt_min: float,
    area_ha: float
):
    """
    Membuat SCS Unit Hydrograph (UH)

    Parameter:
    tc_min : time of concentration (menit)
    dt_min : time step (menit)
    area_ha : luas DAS (ha)

    Output:
    DataFrame time_min, uh_cms_per_mm
    """

    # Parameter standar SCS
    tp = 0.6 * tc_min        # time to peak (menit)
    tb = 2.67 * tp           # base time (menit)

    time = np.arange(0, tb + dt_min, dt_min)

    uh = np.zeros_like(time, dtype=float)

    for i, t in enumerate(time):
        if t <= tp:
            uh[i] = t / tp
        elif tp < t <= tb:
            uh[i] = (tb - t) / (tb - tp)
        else:
            uh[i] = 0

    uh = uh / uh.sum()       # normalisasi unit depth

    # Konversi ke debit (m3/s per mm hujan)
    area_m2 = area_ha * 10_000
    uh_cms = uh * area_m2 / 1000 / (dt_min * 60)

    df = pd.DataFrame({
        "time_min": time,
        "uh_cms_per_mm": uh_cms
    })

    return df


def runoff_hydrograph(
    runoff_df: pd.DataFrame,
    uh_df: pd.DataFrame
):
    """
    Konvolusi limpasan efektif dengan Unit Hydrograph
    """

    runoff = runoff_df["runoff_mm"].values
    uh = uh_df["uh_cms_per_mm"].values

    q = np.convolve(runoff, uh)

    dt_min = runoff_df["time_min"].diff().mean()
    time = np.arange(0, len(q) * dt_min, dt_min)

    df = pd.DataFrame({
        "time_min": time,
        "debit_cms": q
    })

    return df


def santa_barbara_routing(
    runoff_df: pd.DataFrame,
    tc_min: float
):
    """
    Santa Barbara Urban Hydrograph Method
    """

    dt_min = runoff_df["time_min"].diff().mean()
    dt_hr = dt_min / 60

    K = dt_min / (2 * tc_min + dt_min)

    Q = np.zeros(len(runoff_df))

    for i in range(1, len(runoff_df)):
        R1 = runoff_df.loc[i - 1, "runoff_mm"]
        R2 = runoff_df.loc[i, "runoff_mm"]
        Q1 = Q[i - 1]

        Q[i] = Q1 + K * (R1 + R2 - 2 * Q1)

    runoff_df["debit_relative"] = Q
    return runoff_df


