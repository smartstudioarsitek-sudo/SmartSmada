# =========================================================
# SMARTPCLP: SISTEM INFORMASI HIDROLOGI & DRAINASE
# Python + Streamlit (Fixed Sidebar Navigation)
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
    page_icon="🌊",
    initial_sidebar_state="expanded" # Sidebar selalu terbuka saat awal
)

# Gaya CSS untuk membuat Radio Button di Sidebar terlihat seperti Tab/Menu Fix
st.markdown("""
    <style>
    [data-testid="stSidebarNav"] {display: none;}
    .stRadio [role="radiogroup"] {
        flex-direction: column;
    }
    </style>
    """, unsafe_allow_html=True)

# =========================================================
# SIDEBAR – NAVIGASI FIX (BUKAN POP-UP)
# =========================================================
with st.sidebar:
    st.title("📂 SmartPCLP")
    st.info("Sistem Analisis Terpadu")
    
    # Navigasi menggunakan Radio Button agar pilihan selalu terlihat (FIX)
    menu = st.radio(
        "Main Navigation",
        [
            "🏠 SmartPCLP Project (Save/Open)",
            "📥 Input Rainfall",
            "🌧️ SCS-CN Runoff",
            "📈 Hidrograf",
            "🏞️ Kolam Retensi",
            "⏱️ Time of Concentration",
            "🚰 Storm Sewer Design"
        ],
        index=0 # Default ke menu pertama (Save/Open)
    )
    
    st.divider()
    st.caption("Developed for Civil Engineering Standards")

# =========================================================
# SESSION STATE (Global Data)
# =========================================================
if 'rainfall_df' not in st.session_state:
    st.session_state.rainfall_df = None

# =========================================================
# 1. PAGE: SMARTPCLP PROJECT (SAVE/OPEN + MANUAL)
# =========================================================
if menu == "🏠 SmartPCLP Project (Save/Open)":
    st.title("🏠 SmartPCLP Project Manager")
    
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        st.subheader("💾 Data Management")
        if st.button("💾 Save Current Project"):
            project_data = {
                "program": "SmartPCLP",
                "status": "Final Calculation",
                "timestamp": str(pd.Timestamp.now())
            }
            save_project(project_data)
            st.success("Data berhasil disimpan ke sistem.")

        if st.button("📂 Load Existing Project"):
            try:
                project = load_project()
                st.json(project)
            except:
                st.error("Gagal memuat data. Pastikan file project.json tersedia.")

    with col2:
        st.subheader("📖 Manuals & Documentation")
        
        # Manual Book Section
        with st.expander("📕 Manual Book (Panduan Langkah Demi Langkah)", expanded=True):
            st.markdown("""
            **Urutan Penggunaan Aplikasi:**
            1. **Input Rainfall**: Masukkan data hujan manual atau dari Excel.
            2. **SCS-CN Runoff**: Masukkan luas DAS dan nilai CN untuk mendapatkan limpasan efektif.
            3. **Hidrograf**: Hitung debit banjir rancangan ($Q_{peak}$).
            4. **Sewer Design**: Rencanakan dimensi saluran/pipa berdasarkan debit rencana.
            """)
        
        # Manual Reference Section
        with st.expander("📚 Manual Reference (Teori & Standar Teknis)"):
            st.markdown("""
            **Metodologi & Standar:**
            * **Metode Rasional**: Digunakan untuk luas DAS < 50 Ha.
              $$Q = 0.00278 \cdot C \cdot I \cdot A$$
            * **SCS-CN**: Digunakan untuk menghitung hujan efektif berdasarkan karakteristik tanah dan tata guna lahan.
            * **Manning Formula**: Standar kapasitas saluran terbuka dan pipa.
            * **Referensi**: KP-01 (Irigasi) & KP-05 (Drainase).
            """)

# =========================================================
# 2. PAGE: INPUT RAINFALL
# =========================================================
elif menu == "📥 Input Rainfall":
    st.header("📥 Analisis Curah Hujan")
    
    source = st.radio("Metode Input", ["Manual Input", "Import Excel"], horizontal=True)
    
    if source == "Manual Input":
        dt = st.number_input("Interval Waktu (menit)", 1, 60, 10)
        rainfall_input = st.text_area("Masukkan Data Hujan (mm, dipisah koma)", "5, 12, 25, 18, 7")
        if st.button("Generate Hyetograph"):
            data = [float(x) for x in rainfall_input.split(",")]
            st.session_state.rainfall_df = rainfall_manual(data, dt)
            st.success("Hyetograph berhasil dibuat.")

    if st.session_state.rainfall_df is not None:
        df = st.session_state.rainfall_df
        st.dataframe(df)
        
        # Visualisasi Inverted Bar (Standar Hidrologi)
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.bar(df["time_min"], df["rainfall_mm"], color='dodgerblue', width=dt*0.8)
        ax.set_ylabel("Hujan (mm)")
        ax.set_xlabel("Waktu (menit)")
        ax.invert_yaxis()
        st.pyplot(fig)

# =========================================================
# 3. PAGE: SCS-CN RUNOFF
# =========================================================
elif menu == "🌧️ SCS-CN Runoff":
    st.header("🌧️ Perhitungan Runoff (SCS-CN)")
    if st.session_state.rainfall_df is not None:
        c1, c2 = st.columns(2)
        with c1:
            area = st.number_input("Luas Catchment (ha)", 0.1, 5000.0, 10.0)
        with c2:
            cn_val = st.number_input("Curve Number (CN)", 30, 98, 80)
        
        df_runoff, q_total = runoff_hyetograph(st.session_state.rainfall_df, cn_val)
        v_runoff = runoff_volume_m3(q_total, area)
        
        st.metric("Total Runoff (mm)", f"{q_total:.2f}")
        st.metric("Volume Runoff (m³)", f"{v_runoff:.2f}")
        st.dataframe(df_runoff)
    else:
        st.warning("Silakan input data hujan terlebih dahulu.")

# (Bagian Menu Lainnya tetap mengikuti struktur di atas...)
