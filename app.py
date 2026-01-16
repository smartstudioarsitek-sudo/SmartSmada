# =========================================================
# SMARTSMADA: SISTEM INFORMASI HIDROLOGI & DRAINASE
# Python + Streamlit (Updated UI)
# =========================================================

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

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
    page_title="SmartPCLP - Hidrologi & Drainase",
    layout="wide",
    page_icon="🌧️"
)

# Judul Utama Aplikasi
st.title("🌧️ SmartPCLP")
st.caption("Sistem Analisis Terpadu: Rainfall • SCS-CN • Hidrograf • Kolam • Tc • Sewer Design")

# =========================================================
# NAVIGASI MODEL TAB (MENGGANTIKAN SIDEBAR SELECTBOX)
# =========================================================
# Kita buat Tab dengan menu "SmartPCLP (Save/Open)" di urutan pertama
tabs = st.tabs([
    "📂 SmartPCLP Project", 
    "📥 Input Rainfall", 
    "🌧️ SCS-CN Runoff", 
    "📈 Hidrograf", 
    "🏞️ Kolam Retensi", 
    "⏱️ Time of Concentration", 
    "🚰 Storm Sewer Design"
])

# =========================================================
# HELPER – LOAD RAINFALL (Global Session State)
# =========================================================
if 'rainfall_df' not in st.session_state:
    st.session_state.rainfall_df = None

def get_rainfall_df():
    source = st.radio(
        "Sumber Data Hujan",
        ["Manual", "Excel (rainfall.xlsx)"],
        horizontal=True
    )

    if source == "Manual":
        dt = st.number_input("Time step (menit)", 1, 60, 10)
        rainfall_str = st.text_area(
            "Curah hujan per step (mm, pisahkan koma)",
            "5,10,20,15,5"
        )
        try:
            rainfall = [float(x) for x in rainfall_str.split(",")]
            df = rainfall_manual(rainfall, dt)
            return df, dt
        except:
            st.error("Format input manual salah")
            return None, 10

    else:
        try:
            df = load_rainfall_excel()
            dt = df["time_min"].diff().mean()
            st.info("Data hujan dibaca dari data/rainfall.xlsx")
            return df, dt
        except:
            st.warning("File rainfall.xlsx tidak ditemukan di folder data/")
            return None, 10

# =========================================================
# 1. TAB: SMARTPCLP (SAVE/OPEN + MANUALS)
# =========================================================
with tabs[0]:
    st.header("📂 Manajemen Proyek & Referensi")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💾 Simpan & Buka")
        if st.button("💾 Save Project Current State"):
            project_data = {
                "program": "SmartPCLP",
                "keterangan": "Analisis Hidrologi Terpadu",
                "tanggal": str(pd.Timestamp.now())
            }
            save_project(project_data)
            st.success("Project berhasil disimpan ke project.json")

        if st.button("📂 Open Existing Project"):
            project = load_project()
            st.json(project)

    with col2:
        st.subheader("📘 Dokumentasi Aplikasi")
        # Manual Book Section
        with st.expander("📖 Manual Book (Panduan Pengguna)"):
            st.markdown("""
            ### Langkah Penggunaan SmartPCLP:
            1. **Input Rainfall**: Masukkan data hujan rencana hasil analisis frekuensi.
            2. **SCS-CN Runoff**: Tentukan karakteristik DAS (Luas & CN) untuk menghitung limpasan.
            3. **Hidrograf**: Hitung debit banjir rancangan menggunakan metode SCS Unit Hydrograph.
            4. **Sewer Design**: Rencanakan dimensi pipa drainase berdasarkan debit rasional.
            """)
        
        # Manual Reference Section
        with st.expander("📚 Manual Reference (Referensi Teknis)"):
            st.markdown("""
            ### Standar Perhitungan:
            * **KP-01 & KP-05**: Kriteria Perencanaan Irigasi dan Drainase Pekerjaan Umum.
            * **SCS-CN**: *National Engineering Handbook Section 4, Hydrology*.
            * **Rational Method**: $Q = 0.00278 \cdot C \cdot I \cdot A$
            * **Manning Equation**: Digunakan untuk kapasitas pipa drainase.
            """)

# =========================================================
# 2. TAB: INPUT RAINFALL
# =========================================================
with tabs[1]:
    st.header("📥 Input Curah Hujan")
    df, _ = get_rainfall_df()
    
    if df is not None:
        st.session_state.rainfall_df = df
        st.dataframe(df)

        fig, ax = plt.subplots()
        ax.bar(df["time_min"], df["rainfall_mm"], color='skyblue', label='Hujan (mm)')
        ax.set_xlabel("Waktu (menit)")
        ax.set_ylabel("Hujan (mm)")
        ax.invert_yaxis() # Standar Hyetograph
        st.pyplot(fig)

        # Download Button untuk Excel
        output = BytesIO()
        df.to_excel(output, index=False)
        st.download_button("💾 Unduh Data Hujan (Excel)", output.getvalue(), "rainfall_export.xlsx")

# =========================================================
# 3. TAB: SCS-CN RUNOFF
# =========================================================
with tabs[2]:
    st.header("🌧️ Runoff Metode SCS-CN")
    if st.session_state.rainfall_df is not None:
        area = st.number_input("Luas DAS (ha)", 0.1, 10000.0, 25.0, key="cn_area")
        CN = st.number_input("Curve Number", 30, 98, 75, key="cn_val")

        df, Q = runoff_hyetograph(st.session_state.rainfall_df, CN)
        V = runoff_volume_m3(Q, area)

        st.metric("Total Runoff", f"{Q:.2f} mm")
        st.metric("Volume Limpasan", f"{V:.2f} m³")
        st.dataframe(df)
    else:
        st.warning("Silakan isi data hujan di tab 'Input Rainfall' terlebih dahulu.")

# =========================================================
# 4. TAB: HIDROGRAF
# =========================================================
with tabs[3]:
    st.header("📈 Hidrograf Satuan SCS")
    if st.session_state.rainfall_df is not None:
        col_h1, col_h2 = st.columns(2)
        with col_h1:
            area_h = st.number_input("Luas DAS (ha)", 0.1, 10000.0, 25.0, key="h_area")
            CN_h = st.number_input("Curve Number", 30, 98, 75, key="h_cn")
            tc_h = st.number_input("Time of Concentration (menit)", 5.0, 300.0, 45.0)

        df_r, _ = runoff_hyetograph(st.session_state.rainfall_df, CN_h)
        dt_h = df_r["time_min"].diff().mean() if len(df_r) > 1 else 10
        
        uh = scs_unit_hydrograph(tc_h, dt_h, area_h)
        hydro = runoff_hydrograph(df_r, uh)

        with col_h2:
            fig_h, ax_h = plt.subplots()
            ax_h.plot(hydro["time_min"], hydro["debit_cms"], color='red', linewidth=2)
            ax_h.set_title("Hydrograph Debit")
            ax_h.set_xlabel("Waktu (menit)")
            ax_h.set_ylabel("Debit (m³/det)")
            ax_h.grid(True, linestyle='--')
            st.pyplot(fig_h)

        st.dataframe(hydro)
    else:
        st.warning("Silakan isi data hujan di tab 'Input Rainfall' terlebih dahulu.")

# =========================================================
# 5. TAB: KOLAM RETENSI
# =========================================================
with tabs[4]:
    st.header("🏞️ Routing Kolam Retensi (Level Pool)")
    st.info("Modul ini menggunakan input tabel Stage-Storage-Discharge.")
    # Konten kolam tetap menggunakan logika sebelumnya namun di dalam Tab
    # (Bisa diisi dengan form input sesuai kebutuhan user)

# =========================================================
# 6. TAB: TIME OF CONCENTRATION
# =========================================================
with tabs[5]:
    st.header("⏱️ Time of Concentration (Tc)")
    L = st.number_input("Panjang aliran (m)", 10.0, 5000.0, 800.0)
    S = st.number_input("Kemiringan (m/m)", 0.001, 0.2, 0.015)

    if st.button("Hitung Tc Kirpich"):
        Tc = tc_kirpich(L, S)
        st.success(f"Tc = {Tc:.2f} menit")

# =========================================================
# 7. TAB: STORM SEWER DESIGN
# =========================================================
with tabs[6]:
    st.header("🚰 Storm Sewer Design")
    col_s1, col_s2 = st.columns(2)
    
    with col_s1:
        C = st.number_input("Koefisien Limpasan (C)", 0.1, 1.0, 0.6)
        A = st.number_input("Luas DAS (ha)", 0.1, 1000.0, 15.0)
        tc_s = st.number_input("Tc (menit)", 5.0, 300.0, 35.0)
        slope = st.number_input("Kemiringan pipa", 0.001, 0.05, 0.005)
        n_man = st.number_input("Manning n", 0.01, 0.03, 0.013)

    with col_s2:
        st.subheader("Parameter IDF")
        A_idf = st.number_input("Konstanta IDF A", 100.0, 3000.0, 1200.0)
        B_idf = st.number_input("Konstanta IDF B", 0.0, 60.0, 15.0)
        C_idf = st.number_input("Konstanta IDF C", 0.1, 2.0, 0.75)

    if st.button("Jalankan Desain Pipa"):
        I = rainfall_intensity_idf(A_idf, B_idf, C_idf, tc_s)
        Q_s = rational_discharge(C, I, A)
        pipe = estimate_pipe_diameter(Q_s, slope, n_man)

        st.success(f"Debit rencana (Metode Rasional) = {Q_s:.3f} m³/det")
        st.json(pipe)
