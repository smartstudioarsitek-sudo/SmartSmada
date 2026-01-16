# modules/sewer_design.py (Update)

def check_pipe_capacity_pu(Q_design, Q_pipe_full):
    """Evaluasi Kapasitas dengan kriteria Freeboard (80%)"""
    ratio = Q_design / Q_pipe_full
    
    if ratio <= 0.8:
        status = "✅ AMAN (Memenuhi Freeboard)"
    elif ratio <= 1.0:
        status = "⚠️ KRITIS (Tanpa Freeboard)"
    else:
        status = "❌ TIDAK AMAN (Banjir)"
        
    return {"ratio": round(ratio, 2), "status": status}
