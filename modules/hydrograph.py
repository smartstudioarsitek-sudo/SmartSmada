# modules/hydrograph.py (Update)
import numpy as np
import pandas as pd

def hss_nakayasu(area_ha, L_km, tg_hour=None, alpha=2.0, tr_hour=None, dt_min=10):
    """Implementasi Hidrograf Satuan Sintetik Nakayasu (Standard SNI)"""
    area_km2 = area_ha / 100
    
    # 1. Menghitung Time Lag (tg) - Pendekatan L
    if tg_hour is None:
        tg = 0.21 * (L_km**0.7) if L_km < 15 else 0.4 + 0.058 * L_km
    else:
        tg = tg_hour

    tr = 0.75 * tg if tr_hour is None else tr_hour 
    tp = tg + 0.8 * tr                            
    t03 = alpha * tg                              
    
    # Debit Puncak (Qp) per 1 mm hujan
    qp = (area_km2) / (3.6 * (0.3 * tp + t03))
    
    # Simulasi kurva (4 segmen)
    t_max = tp + 10 * t03 
    time = np.arange(0, t_max * 60, dt_min) / 60
    q = []

    for t in time:
        if t <= tp:
            val = qp * (t / tp)**2.4 # Kurva Naik
        elif t <= tp + t03:
            val = qp * 0.3**((t - tp) / t03) # Turun 1
        elif t <= tp + t03 + 1.5 * t03:
            val = qp * 0.3**((t - tp + 0.5 * t03) / (1.5 * t03)) # Turun 2
        else:
            val = qp * 0.3**((t - tp + 1.5 * t03) / (2 * t03)) # Turun 3
        q.append(max(val, 0))

    return pd.DataFrame({"time_min": time * 60, "uh_cms_per_mm": q})
