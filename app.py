# =========================================================
# APP HIDROLOGI & DRAINASE
# Python + Streamlit
# =========================================================



import streamlit as st
import pandas as pd
import json
import os
import matplotlib.pyplot as plt

# -----------------------------
# IMPORT MODULE ENGINE
# -----------------------------
from modules.rainfall import rainfall_manual
from modules.scs_cn import runoff_hyetograph, runoff_volume_m3
from modules.hydrograph import scs_unit_hydrograph, runoff_hydrograph
from modules.pond_routing import level_pool_routing
from modules.tc_calc import tc_kirpich
from modules.sewer_design import (
    rainfall_intensity_idf,
    rational_discharge,
    estimate_pipe_diameter
)

# -----------------------------
# IMPORT DATA HANDLER
# -----------------------------
from data import (
    load_rainfall_excel,
    save_rainfall_excel,
    save_project,
    load_project
)

# =========================================================
# KONFIGURASI APP
# =========================================================
st.set_page_config(
    page_title="Aplikasi Hidrologi & Drainase",
    layout="wide"
)

st.title("🌧️ Aplikasi Hidrologi & Drainase")
st.caption("Rainfall • SCS-CN • Hidrograf • Kolam • Tc • Sewer Design")

DATA_DIR = "data"

# =========================================================
# SIDEBAR – MENU
# =========================================================
menu = st.sidebar.selectbox(
    "Menu Utama",
    [
        "Input Rainfall",
        "SCS-CN Runoff",
        "Hidrograf",
        "Kolam Retensi",
        "Time of Concentration",
        "Storm Sewer Design",
        "Save / Open Project"
    ]
)

# =========================================================
# HELPER – LOAD RAINFALL
# =========================================================
def get_rainfall_df():
    source = st.radio(
        "Sumber Data Hujan",
        ["Manual", "Excel (rainfall.xlsx)"]
    )

    if source == "Manual":
        dt = st.number_input("Time step (menit)", 1, 60, 10)
        rainfall_str = st.text_area(
            "Curah hujan per step (mm, pisahkan koma)",
            "5,10,20,15,5"
        )
        rainfall = [float(x) for x in rainfall_str.split(",")]

        df = rainfall_manual(rainfall, dt)
        return df, dt

    else:
        df = load_rainfall_excel()
        dt = df["time_min"].diff().mean()
        st.info("Data hujan dibaca dari data/rainfall.xlsx")
        return df, dt


# =========================================================
# 1. INPUT RAINFALL
# =========================================================
if menu == "Input Rainfall":
    st.header("📥 Input Curah Hujan")

    df, _ = get_rainfall_df()
    st.dataframe(df)

    fig, ax = plt.subplots()
    ax.bar(df["time_min"], df["rainfall_mm"])
    ax.set_xlabel("Waktu (menit)")
    ax.set_ylabel("Hujan (mm)")
    st.pyplot(fig)

    if st.button("💾 Simpan ke rainfall.xlsx"):
        save_rainfall_excel(df)
        st.success("Data hujan berhasil disimpan")

# =========================================================
# 2. SCS-CN RUNOFF
# =========================================================
elif menu == "SCS-CN Runoff":
    st.header("🌧️ Runoff Metode SCS-CN")

    area = st.number_input("Luas DAS (ha)", 0.1, 10000.0, 25.0)
    CN = st.number_input("Curve Number", 30, 98, 75)

    df, _ = get_rainfall_df()
    df, Q = runoff_hyetograph(df, CN)
    V = runoff_volume_m3(Q, area)

    st.success(f"Runoff Total = {Q:.2f} mm")
    st.info(f"Volume Limpasan = {V:.2f} m³")

    st.dataframe(df)

# =========================================================
# 3. HIDROGRAF
# =========================================================
elif menu == "Hidrograf":
    st.header("📈 Hidrograf SCS")

    area = st.number_input("Luas DAS (ha)", 0.1, 10000.0, 25.0)
    CN = st.number_input("Curve Number", 30, 98, 75)
    tc = st.number_input("Time of Concentration (menit)", 5.0, 300.0, 45.0)

    df, dt = get_rainfall_df()
    df, _ = runoff_hyetograph(df, CN)

    uh = scs_unit_hydrograph(tc, dt, area)
    hydro = runoff_hydrograph(df, uh)

    fig, ax = plt.subplots()
    ax.plot(hydro["time_min"], hydro["debit_cms"])
    ax.set_xlabel("Waktu (menit)")
    ax.set_ylabel("Debit (m³/det)")
    st.pyplot(fig)

    st.dataframe(hydro)

# =========================================================
# 4. KOLAM RETENSI
# =========================================================
elif menu == "Kolam Retensi":
    st.header("🏞️ Routing Kolam Retensi (Level Pool)")

    inflow = pd.DataFrame({
        "time_min": [0,10,20,30,40,50],
        "inflow_cms": [0,5,15,10,4,0]
    })

    stage_storage = pd.DataFrame({
        "stage_m": [0,1,2,3],
        "storage_m3": [0,500,1500,3000]
    })

    stage_discharge = pd.DataFrame({
        "stage_m": [0,1,2,3],
        "outflow_cms": [0,1,4,10]
    })

    if st.button("Hitung Routing Kolam"):
        result = level_pool_routing(
            inflow,
            stage_storage,
            stage_discharge,
            dt_min=10
        )
        st.dataframe(result)

# =========================================================
# 5. TIME OF CONCENTRATION
# =========================================================
elif menu == "Time of Concentration":
    st.header("⏱️ Time of Concentration (Kirpich)")

    L = st.number_input("Panjang aliran (m)", 10.0, 5000.0, 800.0)
    S = st.number_input("Kemiringan (m/m)", 0.001, 0.2, 0.015)

    if st.button("Hitung Tc"):
        Tc = tc_kirpich(L, S)
        st.success(f"Tc = {Tc:.2f} menit")

# =========================================================
# 6. STORM SEWER DESIGN
# =========================================================
elif menu == "Storm Sewer Design":
    st.header("🚰 Storm Sewer Design")

    C = st.number_input("Koefisien Limpasan (C)", 0.1, 1.0, 0.6)
    A = st.number_input("Luas DAS (ha)", 0.1, 1000.0, 15.0)
    tc = st.number_input("Tc (menit)", 5.0, 300.0, 35.0)

    A_idf = st.number_input("Konstanta IDF A", 100.0, 3000.0, 1200.0)
    B_idf = st.number_input("Konstanta IDF B", 0.0, 60.0, 15.0)
    C_idf = st.number_input("Konstanta IDF C", 0.1, 2.0, 0.75)

    slope = st.number_input("Kemiringan pipa", 0.001, 0.05, 0.005)
    n = st.number_input("Manning n", 0.01, 0.03, 0.013)

    if st.button("Desain Pipa"):
        I = rainfall_intensity_idf(A_idf, B_idf, C_idf, tc)
        Q = rational_discharge(C, I, A)
        pipe = estimate_pipe_diameter(Q, slope, n)

        st.success(f"Debit rencana = {Q:.3f} m³/det")
        st.json(pipe)

# =========================================================
# 7. SAVE / OPEN PROJECT
# =========================================================
elif menu == "Save / Open Project":
    st.header("💾 Save / Open Project")

    if st.button("💾 Save Project"):
        project_data = {
            "keterangan": "Project Hidrologi",
            "tanggal": str(pd.Timestamp.now())
        }
        save_project(project_data)
        st.success("Project berhasil disimpan")

    if st.button("📂 Open Project"):
        project = load_project()
        st.json(project)

# app.py (Penyesuaian Menu)
menu = st.sidebar.selectbox(
    "Menu Utama",
    [
        "1. Analisis Frekuensi (SNI)",  # Baru
        "2. Hujan Rencana & IDF",       # Baru (Mononobe)
        "3. HSS Nakayasu",              # Baru
        "4. Storm Sewer Design",
        "5. Save / Open Project"
    ]
)

# Contoh Implementasi Menu Nakayasu
if menu == "3. HSS Nakayasu":
    st.header("📈 Hidrograf Satuan Sintetik Nakayasu")
    col1, col2 = st.columns(2)
    with col1:
        area = st.number_input("Luas DAS (ha)", 0.1, 1000.0, 50.0)
        L = st.number_input("Panjang Sungai Utama (km)", 0.1, 100.0, 2.5)
    with col2:
        alpha = st.slider("Parameter Alpha (Saran PU: 1.5 - 3.0)", 1.5, 3.0, 2.0)
        rt = st.number_input("Hujan Efektif (mm)", 1.0, 500.0, 100.0)

    uh_df = hss_nakayasu(area, L, alpha=alpha)
    # Konvolusi dengan hujan rencana
    uh_df["debit_banjir_cms"] = uh_df["uh_cms_per_mm"] * rt
    
    st.line_chart(uh_df, x="time_min", y="debit_banjir_cms")
    st.dataframe(uh_df)
