# modules/tc_calc.py
import numpy as np


# --------------------------------------------------
# 1. Kirpich (alami / saluran kecil)
# --------------------------------------------------
def tc_kirpich(
    L_m: float,
    S: float
):
    """
    Kirpich Formula
    Tc (menit) = 0.01947 * L^0.77 * S^-0.385

    L : panjang aliran (m)
    S : kemiringan saluran (m/m)
    """
    if S <= 0:
        raise ValueError("Kemiringan (S) harus > 0")

    Tc = 0.01947 * (L_m ** 0.77) * (S ** -0.385)
    return Tc


# --------------------------------------------------
# 2. Kerby (aliran lembar / overland flow)
# --------------------------------------------------
def tc_kerby(
    L_m: float,
    n: float,
    S: float
):
    """
    Kerby Formula
    Tc (menit) = 0.828 * (L * n)^0.467 / S^0.235

    L : panjang aliran (m)
    n : koefisien kekasaran (0.02 – 0.8)
    S : kemiringan lahan (m/m)
    """
    if S <= 0:
        raise ValueError("Kemiringan (S) harus > 0")

    Tc = 0.828 * ((L_m * n) ** 0.467) / (S ** 0.235)
    return Tc


# --------------------------------------------------
# 3. NRCS / TR-55 (sheet + shallow + channel)
# --------------------------------------------------
def tc_tr55(
    L_sheet: float,
    n_sheet: float,
    S_sheet: float,
    L_channel: float,
    V_channel: float
):
    """
    TR-55 Time of Concentration (menit)

    Sheet flow:
    Ts = 0.007 * (n * L)^0.8 / (P2^0.5 * S^0.4)
    (P2 = 50 mm hujan 2-thn → disederhanakan)

    Channel flow:
    Tc = L / V
    """

    if S_sheet <= 0 or V_channel <= 0:
        raise ValueError("Kemiringan & kecepatan harus > 0")

    # Sheet flow (menit)
    P2 = 50  # mm (standar TR-55)
    Ts = (
        0.007
        * ((n_sheet * L_sheet) ** 0.8)
        / ((P2 ** 0.5) * (S_sheet ** 0.4))
    )

    # Channel flow (menit)
    Tc_channel = (L_channel / V_channel) / 60

    return Ts + Tc_channel


# --------------------------------------------------
# 4. FAA Formula (bandara / permukaan keras)
# --------------------------------------------------
def tc_faa(
    L_m: float,
    S: float
):
    """
    FAA Formula
    Tc (menit) = 1.8 * (1.1 - C) * L^0.5 / S^0.333

    (C disederhanakan = 0.9 untuk perkerasan)
    """
    C = 0.9
    if S <= 0:
        raise ValueError("Kemiringan (S) harus > 0")

    Tc = 1.8 * (1.1 - C) * (L_m ** 0.5) / (S ** 0.333)
    return Tc


# --------------------------------------------------
# 5. Ringkasan otomatis
# --------------------------------------------------
def tc_summary(**kwargs):
    """
    Hitung beberapa metode sekaligus
    """
    result = {}

    if {"L_m", "S"} <= kwargs.keys():
        result["Kirpich"] = tc_kirpich(kwargs["L_m"], kwargs["S"])

    if {"L_m", "n", "S"} <= kwargs.keys():
        result["Kerby"] = tc_kerby(kwargs["L_m"], kwargs["n"], kwargs["S"])

    return result
