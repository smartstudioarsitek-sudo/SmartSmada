# modules/watershed.py
import numpy as np


class Watershed:
    """
    Kelas DAS / Catchment
    """

    def __init__(
        self,
        area_ha: float,
        impervious_percent: float,
        tc_min: float,
        abstraction_pervious_mm: float = 0.0,
        abstraction_impervious_mm: float = 0.0
    ):
        self.area_ha = area_ha
        self.impervious_percent = impervious_percent
        self.tc_min = tc_min
        self.abstraction_pervious_mm = abstraction_pervious_mm
        self.abstraction_impervious_mm = abstraction_impervious_mm

        self.area_m2 = area_ha * 10_000
        self.area_impervious_m2 = self.area_m2 * impervious_percent / 100
        self.area_pervious_m2 = self.area_m2 - self.area_impervious_m2

    # --------------------------------------------------
    def summary(self):
        return {
            "Luas DAS (ha)": self.area_ha,
            "Luas Impervious (m2)": self.area_impervious_m2,
            "Luas Pervious (m2)": self.area_pervious_m2,
            "Tc (menit)": self.tc_min
        }

    # --------------------------------------------------
    def horton_infiltration(
        self,
        f0: float,
        fc: float,
        k: float,
        rainfall_df
    ):
        """
        Horton Infiltration Method

        f(t) = fc + (f0 - fc) * exp(-k * t)

        Parameters
        ----------
        f0 : mm/hr
        fc : mm/hr
        k  : 1/hr
        rainfall_df : DataFrame dari rainfall.py
        """

        dt_hr = rainfall_df["time_min"].diff().mean() / 60
        time_hr = rainfall_df["time_min"] / 60

        infiltration_rate = fc + (f0 - fc) * np.exp(-k * time_hr)
        infiltration = infiltration_rate * dt_hr

        rainfall_df["infiltration_mm"] = infiltration
        rainfall_df["excess_rain_mm"] = (
            rainfall_df["rainfall_mm"] - infiltration
        ).clip(lower=0)

        return rainfall_df

    # --------------------------------------------------
    def scs_cn_runoff(
        self,
        rainfall_df,
        curve_number: float,
        ia_factor: float = 0.2
    ):
        """
        SCS Curve Number Method
        """

        P = rainfall_df["rainfall_mm"].sum()
        S = (25400 / curve_number) - 254
        Ia = ia_factor * S

        if P <= Ia:
            Q = 0
        else:
            Q = ((P - Ia) ** 2) / (P - Ia + S)

        rainfall_df["runoff_mm"] = Q / len(rainfall_df)

        return rainfall_df, Q

    # --------------------------------------------------
    def runoff_volume(self, runoff_mm: float):
        """
        Menghitung volume limpasan (m3)
        """
        return runoff_mm / 1000 * self.area_m2
