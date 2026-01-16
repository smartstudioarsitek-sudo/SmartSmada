# modules/pond_routing.py
import numpy as np
import pandas as pd

def level_pool_routing(inflow_df, stage_storage_df, stage_discharge_df, dt_min):
    dt_sec = dt_min * 60
    time = inflow_df["time_min"].values
    Qin = inflow_df["inflow_cms"].values
    
    stg_table = stage_storage_df["stage_m"].values
    str_table = stage_storage_df["storage_m3"].values
    dis_table = stage_discharge_df["outflow_cms"].values

    # Buat tabel indikator routing: (2S/dt + O) vs O
    indicator_table = (2 * str_table / dt_sec) + dis_table
    
    n = len(Qin)
    Qout = np.zeros(n)
    storage = np.zeros(n)
    stage = np.zeros(n)

    # Kondisi Awal (Asumsi kolam kosong di awal atau sesuai stage[0])
    stage[0] = stg_table[0]
    storage[0] = str_table[0]
    Qout[0] = dis_table[0]

    for i in range(1, n):
        # Hitung Nilai RHS (Right Hand Side)
        rhs = (Qin[i-1] + Qin[i]) + ((2 * storage[i-1] / dt_sec) - Qout[i-1])
        
        # Cari Qout[i] dengan interpolasi dari indikator_table
        Qout[i] = np.interp(rhs, indicator_table, dis_table)
        
        # Hitung Storage baru
        storage[i] = storage[i-1] + (Qin[i-1] + Qin[i] - Qout[i-1] - Qout[i]) * (dt_sec / 2)
        stage[i] = np.interp(storage[i], str_table, stg_table)

    return pd.DataFrame({
        "time_min": time, "inflow_cms": Qin, "outflow_cms": Qout,
        "stage_m": stage, "storage_m3": storage
    })
