# modules/hydrograph.py
import numpy as np
import pandas as pd


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
