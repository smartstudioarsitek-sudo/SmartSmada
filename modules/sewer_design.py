# modules/sewer_design.py
import numpy as np


# --------------------------------------------------
# 1. Debit rencana – Metode Rasional
# --------------------------------------------------
def rational_discharge(
    C: float,
    I_mm_hr: float,
    A_ha: float
):
    """
    Metode Rasional
    Q (m3/s) = 0.00278 * C * I * A

    C : koefisien limpasan
    I : intensitas hujan (mm/jam)
    A : luas DAS (ha)
    """
    if not (0 < C <= 1):
        raise ValueError("Koefisien C harus antara 0–1")

    Q = 0.00278 * C * I_mm_hr * A_ha
    return Q


# --------------------------------------------------
# 2. Intensitas hujan – IDF (bentuk umum PU)
# --------------------------------------------------
def rainfall_intensity_idf(
    A: float,
    B: float,
    C: float,
    tc_min: float
):
    """
    Persamaan IDF umum:
    I = A / (tc + B)^C

    tc : menit
    I  : mm/jam
    """
    if tc_min <= 0:
        raise ValueError("tc harus > 0")

    I = A / ((tc_min + B) ** C)
    return I


# --------------------------------------------------
# 3. Kecepatan & debit pipa – Manning
# --------------------------------------------------
def manning_pipe_full(
    diameter_m: float,
    slope: float,
    n: float
):
    """
    Aliran penuh pipa lingkaran (Manning)

    Output:
    Q (m3/s), V (m/s)
    """
    if slope <= 0:
        raise ValueError("Kemiringan harus > 0")

    area = np.pi * (diameter_m ** 2) / 4
    radius_h = diameter_m / 4

    V = (1 / n) * (radius_h ** (2 / 3)) * (slope ** 0.5)
    Q = V * area

    return Q, V


# --------------------------------------------------
# 4. Cek kapasitas pipa
# --------------------------------------------------
def check_pipe_capacity(
    Q_design: float,
    Q_pipe: float
):
    """
    Cek aman kapasitas pipa
    """
    return {
        "Q_design (m3/s)": Q_design,
        "Q_pipe (m3/s)": Q_pipe,
        "AMAN": Q_pipe >= Q_design
    }


# --------------------------------------------------
# 5. Estimasi diameter pipa minimum
# --------------------------------------------------
def estimate_pipe_diameter(
    Q_design: float,
    slope: float,
    n: float,
    d_min: float = 0.3,
    d_max: float = 3.0,
    step: float = 0.05
):
    """
    Estimasi diameter minimum pipa (trial & error)
    """

    d = d_min
    while d <= d_max:
        Q_pipe, V = manning_pipe_full(d, slope, n)
        if Q_pipe >= Q_design:
            return {
                "diameter_m": d,
                "Q_pipe (m3/s)": Q_pipe,
                "velocity (m/s)": V
            }
        d += step

    raise ValueError("Diameter maksimum tidak cukup")
