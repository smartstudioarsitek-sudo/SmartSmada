# modules/pond_routing.py
import numpy as np
import pandas as pd


# --------------------------------------------------
# Helper: interpolasi stage-storage-discharge
# --------------------------------------------------
def interp(x, x_table, y_table):
    return np.interp(x, x_table, y_table)


# --------------------------------------------------
# Routing kolam (Level Pool)
# --------------------------------------------------
def level_pool_routing(
    inflow_df: pd.DataFrame,
    stage_storage_df: pd.DataFrame,
    stage_discharge_df: pd.DataFrame,
    dt_min: float
):
    """
    Level Pool Routing (Modified Puls Method)

    inflow_df:
        time_min, inflow_cms

    stage_storage_df:
        stage_m, storage_m3

    stage_discharge_df:
        stage_m, outflow_cms
    """

    time = inflow_df["time_min"].values
    Qin = inflow_df["inflow_cms"].values

    stage_table = stage_storage_df["stage_m"].values
    storage_table = stage_storage_df["storage_m3"].values
    discharge_table = stage_discharge_df["outflow_cms"].values

    n = len(Qin)

    stage = np.zeros(n)
    storage = np.zeros(n)
    Qout = np.zeros(n)

    # kondisi awal
    stage[0] = stage_table[0]
    storage[0] = storage_table[0]
    Qout[0] = interp(stage[0], stage_table, discharge_table)

    dt_sec = dt_min * 60

    for i in range(1, n):
        S1 = storage[i - 1]
        Qout1 = Qout[i - 1]

        # Modified Puls
        RHS = (
            S1
            + 0.5 * dt_sec * (Qin[i - 1] + Qin[i])
            - 0.5 * dt_sec * Qout1
        )

        # cari storage baru (iterasi sederhana via interpolasi)
        storage[i] = RHS
        stage[i] = interp(storage[i], storage_table, stage_table)
        Qout[i] = interp(stage[i], stage_table, discharge_table)

    df = pd.DataFrame({
        "time_min": time,
        "inflow_cms": Qin,
        "outflow_cms": Qout,
        "stage_m": stage,
        "storage_m3": storage
    })

    return df
