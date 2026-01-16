# app.py (Struktur Baru)
import streamlit as st
from modules.rainfall import log_pearson_3, mononobe_intensity, rainfall_manual
from modules.hydrograph import hss_nakayasu
from modules.sewer_design import rainfall_intensity_idf, rational_discharge, estimate_pipe_diameter, check_pipe_capacity_pu
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Smart Smada - PU Standard", layout="wide")

menu = st.sidebar.selectbox(
    "Tahapan Perencanaan (Standard PU)",
    ["1. Analisis Frekuensi (SNI)", "2. HSS Nakayasu", "3. Drainase (Mononobe)"]
)

# --- MENU 1: ANALISIS FREKUENSI ---
if menu == "1. Analisis Frekuensi (SNI)":
    st.header("📊 Analisis Frekuensi Log Pearson III")
    uploaded_file = st.file_uploader("Upload Data Hujan Harian (Excel/CSV)", type=['csv', 'xlsx'])
    
    if uploaded_file:
        data = pd.read_csv(uploaded_file) # Contoh sederhana
        st.write("Data Historis:", data.head())
        if st.button("Hitung Hujan Rencana"):
            results = log_pearson_3(data.iloc[:, 0]) # Kolom pertama data hujan
            st.table(pd.DataFrame(results.items(), columns=["Kala Ulang", "Hujan Rencana (mm)"]))

# --- MENU 2: NAKAYASU ---
elif menu == "2. HSS Nakayasu":
    st.header("📈 Hidrograf Satuan Sintetik Nakayasu")
    col1, col2 = st.columns(2)
    with col1:
        area = st.number_input("Luas DAS (ha)", value=50.0)
        L = st.number_input("Panjang Sungai (km)", value=2.5)
        alpha = st.slider("Parameter Alpha (Saran PU: 1.5-3.0)", 1.5, 3.0, 2.0)
    
    uh_df = hss_nakayasu(area, L, alpha=alpha)
    fig, ax = plt.subplots()
    ax.plot(uh_df["time_min"], uh_df["uh_cms_per_mm"])
    ax.set_title("Unit Hidrograf Nakayasu")
    st.pyplot(fig)

# --- MENU 3: DRAINASE ---
elif menu == "3. Drainase (Mononobe)":
    st.header("🚰 Desain Saluran Drainase")
    r24 = st.number_input("Hujan Harian Maksimum (R24) - mm", value=120.0)
    tc = st.number_input("Waktu Konsentrasi (tc) - menit", value=30.0)
    
    I = mononobe_intensity(r24, tc)
    st.info(f"Intensitas Hujan (Mononobe): {I:.2f} mm/jam")
    
    q_design = rational_discharge(0.6, I, 15.0) # Contoh C=0.6, A=15ha
    st.success(f"Debit Banjir Rencana: {q_design:.3f} m3/det")
    
    # Cek Kapasitas Pipa
    st.subheader("Pengecekan Kapasitas")
    q_pipe = st.number_input("Kapasitas Pipa Full (m3/det)", value=1.0)
    hasil = check_pipe_capacity_pu(q_design, q_pipe)
    st.subheader(hasil["status"])
