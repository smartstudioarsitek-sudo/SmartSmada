requirements.txt
streamlit
pandas
numpy
scipy
matplotlib
openpyxl
xlsxwriter

utils/__init__.py
# Init file for utils

utils/frequency.py
import numpy as np
import pandas as pd
from scipy import stats

def calculate_statistics(data):
    """Menghitung parameter statistik dasar untuk data hidrologi."""
    n = len(data)
    mean = np.mean(data)
    std = np.std(data, ddof=1) # Sample standard deviation
    skew = stats.skew(data, bias=False)
    kurt = stats.kurtosis(data, bias=False)
    return {"n": n, "mean": mean, "std": std, "skew": skew, "kurt": kurt}

def log_pearson_iii(data, return_periods):
    """
    Analisis Log Pearson Type III sesuai SNI 2415:2016.
    Menggunakan logaritma basis 10.
    """
    log_data = np.log10(data)
    stats_params = calculate_statistics(log_data)
    
    results = {}
    # K factor extraction could be improved with a lookup table, 
    # here using approximation via scipy's ppf which is mathematically accurate
    
    # Fit Pearson3 to the log data
    # Scipy pearson3 uses skew, loc (mean), scale (std)
    # Note: Scipy's skew definition might slightly differ, we pass the calculated sample skew
    
    for tr in return_periods:
        prob = 1.0 / tr
        # Calculate K factor (Frequency Factor)
        # We use the inverse survival function (isf) or ppf for the given probability
        # Log Pearson III follows Pearson III on log data
        
        # Standard deviate K for Pearson Type III
        k_val = stats.pearson3.ppf(1 - prob, skew=stats_params['skew'])
        
        log_qt = stats_params['mean'] + k_val * stats_params['std']
        qt = 10**log_qt
        results[tr] = qt
        
    return results, stats_params

def gumbel_method(data, return_periods):
    """Analisis Distribusi Gumbel (Tipe I Ekstrem)."""
    stats_params = calculate_statistics(data)
    results = {}
    
    # Gumbel parameters
    # Sn and Yn are approximations based on sample size n, 
    # For automation we use standard formula approximation or fixed regression
    n = stats_params['n']
    
    # Simplified approach using scipy fit for robustness
    # loc = mode, scale = measure of dispersion
    loc, scale = stats.gumbel_r.fit(data)
    
    for tr in return_periods:
        # Gumbel formula: Xt = u - alpha * ln(-ln(1 - 1/T))
        # Scipy uses: loc - scale * log(-log(cdf))?? No, gumbel_r is right skewed.
        # stats.gumbel_r.isf(1/tr) gives the value
        qt = stats.gumbel_r.isf(1.0/tr, loc=loc, scale=scale)
        results[tr] = qt
        
    return results, stats_params

def goodness_of_fit(data, dist_type='log_pearson3'):
    """
    Uji Kecocokan: Chi-Square dan Smirnov-Kolmogorov.
    Mengembalikan dictionary status (Diterima/Ditolak).
    """
    n = len(data)
    data_sorted = np.sort(data)
    
    # Prepare distribution for testing
    if dist_type == 'log_pearson3':
        log_data = np.log10(data)
        skew = stats.skew(log_data, bias=False)
        mean = np.mean(log_data)
        std = np.std(log_data, ddof=1)
        # Test performed on Log Data
        test_data = np.sort(log_data)
        dist_func = lambda x: stats.pearson3.cdf(x, skew=skew, loc=mean, scale=std)
    elif dist_type == 'gumbel':
        loc, scale = stats.gumbel_r.fit(data)
        test_data = data_sorted
        dist_func = lambda x: stats.gumbel_r.cdf(x, loc=loc, scale=scale)
    else:
        return {"status": "Error", "note": "Unknown distribution"}

    # 1. Smirnov-Kolmogorov Test
    d_stat, p_value_ks = stats.kstest(test_data, dist_func)
    # Critical value approximation for alpha=0.05
    d_critical = 1.36 / np.sqrt(n) 
    
    ks_result = "DITERIMA" if d_stat < d_critical else "DITOLAK"
    
    # 2. Chi-Square Test (Simplified binning)
    # Number of bins often k = 1 + 3.3 log n
    num_bins = int(1 + 3.3 * np.log10(n))
    if num_bins < 3: num_bins = 3
    
    # Create bins and calculate observed/expected frequencies
    # This is a simplification. For rigorous engineering, manual binning based on probability is used.
    # Here we use equal-width bins for automation stability
    obs_freq, bin_edges = np.histogram(test_data, bins=num_bins)
    
    # Calculate expected freq
    exp_freq =
    total_prob = 0
    for i in range(num_bins):
        lower_cdf = dist_func(bin_edges[i])
        upper_cdf = dist_func(bin_edges[i+1])
        prob = upper_cdf - lower_cdf
        exp_freq.append(prob * n)
        total_prob += prob
    
    # Normalize if total prob < 1 (due to tails)
    exp_freq = np.array(exp_freq)
    if np.sum(exp_freq) > 0:
        exp_freq = exp_freq * (n / np.sum(exp_freq))
    
    chi_stat, p_value_chi = stats.chisquare(obs_freq, f_exp=exp_freq)
    
    # Chi critical for alpha 0.05, df = k - 1 - estimated_params (let's say 2)
    df = max(1, num_bins - 1 - 2)
    chi_critical = stats.chi2.ppf(0.95, df)
    
    chi_result = "DITERIMA" if chi_stat < chi_critical else "DITOLAK"

    return {
        "KS_Stat": d_stat, "KS_Critical": d_critical, "KS_Result": ks_result,
        "Chi_Stat": chi_stat, "Chi_Critical": chi_critical, "Chi_Result": chi_result
    }

utils/hydrology.py
import numpy as np
import pandas as pd

def mononobe_intensity(R24, tc_hours):
    """
    Rumus Mononobe (Standar PU untuk data harian).
    I = (R24 / 24) * (24 / tc)^(2/3)
    """
    if tc_hours <= 0: return 0
    I = (R24 / 24.0) * ((24.0 / tc_hours) ** (2/3))
    return I

def nakayasu_hss(A, L, Ro, alpha=2.0):
    """
    Hidrograf Satuan Sintetik Nakayasu (SNI/KP-01).
    
    Parameters:
    A (float): Luas DAS (km2)
    L (float): Panjang Sungai Utama (km)
    Ro (float): Hujan satuan (mm), biasanya 1 mm
    alpha (float): Parameter karakteristik DAS (biasanya 2.0 - 3.0)
    
    Returns:
    pd.DataFrame: Time (jam) vs Debit (m3/s)
    dict: Parameter hasil hitungan (Tp, Tg, Qp, etc.)
    """
    # 1. Tenggang waktu dari permulaan hujan sampai puncak banjir (tg)
    if L > 15:
        tg = 0.4 + 0.058 * L
    else:
        tg = 0.21 * (L ** 0.7)
        
    # 2. Satuan durasi hujan (tr) - idealnya 0.5 * tg s/d 1 * tg
    tr = 0.5 * tg # Mengambil 0.5 tg sesuai kelaziman
    
    # 3. Waktu naik ke puncak banjir (Tp)
    tp = tg + 0.8 * tr
    
    # 4. Waktu penurunan debit sampai 30% dari debit puncak (T0.3)
    t03 = alpha * tg
    
    # 5. Debit Puncak (Qp)
    # Rumus: Qp = (C * A * Ro) / (3.6 * (0.3 * Tp + T0.3))
    # C = 1 (karena ini unit hydrograph murni dari hujan satuan 1 mm efektif)
    qp = (1.0 * A * Ro) / (3.6 * (0.3 * tp + t03))
    
    # Generate Coordinates
    # Time step for calculation
    dt = 0.1 # jam
    max_time = tp + t03 * 5 # Durasi yang cukup panjang sampai debit mendekati 0
    times = np.arange(0, max_time, dt)
    flows =
    
    for t in times:
        q = 0
        if t < tp:
            # Kurva Naik (Ascending)
            q = qp * ((t / tp) ** 2.4)
        elif t >= tp and t <= (tp + t03):
            # Kurva Turun 1
            q = qp * (0.3 ** ((t - tp) / t03))
        elif t > (tp + t03) and t <= (tp + t03 + 1.5 * t03):
            # Kurva Turun 2
            val = (t - tp + 0.5 * t03) / (1.5 * t03)
            q = qp * (0.3 ** val)
        elif t > (tp + t03 + 1.5 * t03):
            # Kurva Turun 3
            val = (t - tp + 1.5 * t03) / (2.0 * t03)
            q = qp * (0.3 ** val)
        
        flows.append(q)
        
    df_hss = pd.DataFrame({"Waktu (jam)": times, "Debit (m3/s)": flows})
    
    params = {
        "tg": tg, "tr": tr, "tp": tp, "t03": t03, "qp": qp
    }
    
    return df_hss, params

def rational_method_discharge(C, I, A):
    """
    Metode Rasional: Q = 0.278 * C * I * A
    Q (m3/s), I (mm/jam), A (km2)
    """
    return 0.278 * C * I * A

utils/drainage.py
import numpy as np

def check_channel_capacity_circular(diameter_m, slope, n, Q_design):
    """
    Cek Kapasitas Saluran Bulat (Pipa) dengan Syarat Freeboard.
    Sesuai Permen PUPR: Desain tidak boleh full capacity.
    Biasanya batas aman adalah 80% dari kedalaman diameter (h/D < 0.8).
    """
    # 1. Hitung Q Full (Manning)
    # A_full = pi * r^2
    # P_full = pi * D
    # R_full = D / 4
    
    A_full = np.pi * (diameter_m/2)**2
    R_full = diameter_m / 4.0
    V_full = (1/n) * (R_full**(2/3)) * (slope**0.5)
    Q_full = A_full * V_full
    
    # 2. Cek Rasio Q_design / Q_full
    # Secara pendekatan hidrolika, Q/Qfull pada h/D=0.8 adalah sekitar 90% (karena bentuk lingkaran).
    # Namun untuk keamanan PU, kita sering pakai ambang batas kapasitas.
    
    status = ""
    ratio = Q_design / Q_full
    
    # Kriteria Freeboard sederhana untuk pipa:
    # Jika Q_design < 80% Q_full -> Sangat Aman (Ada Freeboard besar)
    # Jika Q_design < 100% Q_full -> Kapasitas Cukup (Tapi tanpa freeboard ideal)
    # Jika Q_design > 100% Q_full -> Banjir
    
    if Q_design > Q_full:
        status = "BAHAYA (Banjir / Meluap)"
        is_safe = False
    elif Q_design > 0.85 * Q_full:
        status = "KRITIS (Kapasitas Penuh, Kurang Freeboard)"
        is_safe = True # Technically flows, but risky
    else:
        status = "AMAN (Memenuhi Kriteria Freeboard)"
        is_safe = True
        
    return {
        "Q_full": Q_full,
        "V_full": V_full,
        "Ratio": ratio * 100,
        "Status": status,
        "Is_Safe": is_safe
    }

def suggest_diameter(Q_design, slope, n):
    """Mencari diameter pipa yang memenuhi syarat freeboard."""
    d_candidates = [0.3, 0.4, 0.5, 0.6, 0.8, 1.0, 1.2, 1.5, 2.0]
    for d in d_candidates:
        res = check_channel_capacity_circular(d, slope, n, Q_design)
        if res and res < 85: # Target < 85% full
            return d, res
    return 2.5, check_channel_capacity_circular(2.5, slope, n, Q_design)

app.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from utils.frequency import log_pearson_iii, gumbel_method, goodness_of_fit
from utils.hydrology import nakayasu_hss, mononobe_intensity, rational_method_discharge
from utils.drainage import check_channel_capacity_circular, suggest_diameter

st.set_page_config(page_title="Smart Smada PU-Ready", layout="wide")

st.title("🌊 Smart Smada: Aplikasi Hidrologi Standar PU")
st.markdown("""
**Sesuai SNI 2415:2016 & Permen PUPR No. 12/2014**
Fitur: Analisis Frekuensi (LPIII), HSS Nakayasu, Drainase Mononobe.
""")

tabs = st.tabs()

# --- TAB 1: ANALISIS FREKUENSI ---
with tabs:
    st.header("Analisis Frekuensi Hujan Harian Maksimum")
    st.info("Upload data curah hujan harian maksimum tahunan (Series min. 10 tahun).")
    
    uploaded_file = st.file_uploader("Upload CSV (Kolom: 'Tahun', 'Hujan')", type="csv")
    
    if uploaded_file:
        df_rain = pd.read_csv(uploaded_file)
        st.write("Data Awal:", df_rain.head())
        
        col_rain = st.selectbox("Pilih Kolom Hujan", df_rain.columns)
        rain_data = df_rain[col_rain].values
        
        if len(rain_data) < 10:
            st.warning("Peringatan: SNI menyarankan data minimal 10 tahun untuk akurasi.")
            
        return_periods = 
        
        # Calculate Distributions
        lp3_res, lp3_stats = log_pearson_iii(rain_data, return_periods)
        gumbel_res, gumbel_stats = gumbel_method(rain_data, return_periods)
        
        # Goodness of Fit
        lp3_fit = goodness_of_fit(rain_data, 'log_pearson3')
        gumbel_fit = goodness_of_fit(rain_data, 'gumbel')
        
        # Display Results
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Log Pearson Tipe III (Prioritas SNI)")
            st.write(f"Mean: {lp3_stats['mean']:.4f}, Std: {lp3_stats['std']:.4f}, Skew: {lp3_stats['skew']:.4f}")
            st.table(pd.DataFrame(lp3_res.items(), columns=))
            
            st.write("**Uji Kecocokan:**")
            st.write(f"Chi-Square: {lp3_fit} (Stat: {lp3_fit:.2f} < Crit: {lp3_fit['Chi_Critical']:.2f})")
            st.write(f"Smirnov-Kolmogorov: {lp3_fit} (Stat: {lp3_fit:.4f} < Crit: {lp3_fit:.4f})")
            
        with col2:
            st.subheader("Gumbel (Pembanding)")
            st.table(pd.DataFrame(gumbel_res.items(), columns=))
            st.write("**Uji Kecocokan:**")
            st.write(f"Chi-Square: {gumbel_fit}")
            st.write(f"Smirnov-Kolmogorov: {gumbel_fit}")

        # Store R24 selected for next steps
        st.divider()
        st.subheader("Pilih Hujan Rencana untuk Desain")
        selected_tr = st.selectbox("Pilih Kala Ulang Desain (Tahun):", return_periods)
        r24_design = lp3_res[selected_tr]
        st.session_state['r24_design'] = r24_design
        st.success(f"Hujan Rencana R{selected_tr} = {r24_design:.2f} mm terpilih.")

# --- TAB 2: HIDROGRAF NAKAYASU ---
with tabs[1]:
    st.header("Hidrograf Satuan Sintetik (HSS) Nakayasu")
    st.markdown("Metode standar untuk perencanaan bendung dan sungai di Indonesia.")
    
    if 'r24_design' not in st.session_state:
        st.warning("Harap selesaikan Analisis Frekuensi di Tab 1 terlebih dahulu, atau masukkan R24 manual di bawah.")
        r24_input = st.number_input("Input Manual R24 (mm)", value=100.0)
    else:
        r24_input = st.number_input("R24 (dari Tab 1)", value=st.session_state['r24_design'])
        
    col_a, col_b = st.columns(2)
    with col_a:
        A_das = st.number_input("Luas DAS (km2)", value=50.0, min_value=0.1)
        L_river = st.number_input("Panjang Sungai Utama (km)", value=10.0, min_value=0.1)
    with col_b:
        alpha = st.number_input("Parameter Alpha (Standard Jawa=2.0)", value=2.0, min_value=1.5, max_value=3.5)
        koef_c = st.number_input("Koefisien Pengaliran (C) Rata-rata", value=0.6, min_value=0.1, max_value=1.0)
        
    if st.button("Hitung Hidrograf Banjir"):
        # 1. Hitung Hujan Efektif
        # R_eff = R24 * C (Metode sederhana Mononobe distribution applied to unit hydrograph basis)
        # Untuk simplifikasi di sini kita pakai Hujan Efektif Total yang didistribusikan
        # Tapi HSS Nakayasu butuh Rain Unit (1mm) dikalikan Rain Eff.
        
        r_eff_total = r24_input * koef_c
        
        # Generate Unit Hydrograph (1 mm)
        df_hss, params = nakayasu_hss(A_das, L_river, Ro=1.0, alpha=alpha)
        
        # Generate Flood Hydrograph (Direct Runoff)
        # Q_banjir = Ordinat HSS * R_eff_total
        # Note: Ini asumsi hujan merata sesaat (Block pulse). 
        # Untuk desain detail, perlu konvolusi hujan jam-jaman.
        
        df_hss = df_hss * r_eff_total
        
        st.subheader("Parameter Waktu")
        st.json(params)
        
        st.subheader(f"Debit Puncak Banjir (Qp): {df_hss.max():.2f} m3/s")
        
        # Plot
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(df_hss, df_hss, label="Hidrograf Banjir Rencana")
        ax.set_xlabel("Waktu (jam)")
        ax.set_ylabel("Debit (m3/s)")
        ax.grid(True, which='both', linestyle='--')
        ax.set_title(f"HSS Nakayasu (Alpha={alpha})")
        st.pyplot(fig)
        
        st.dataframe(df_hss)

# --- TAB 3: DESAIN DRAINASE ---
with tabs[2]:
    st.header("Desain Penampang Drainase (Metode Mononobe)")
    st.markdown("Perhitungan Intensitas dan Kapasitas Saluran sesuai Permen PUPR.")
    
    if 'r24_design' in st.session_state:
        st.info(f"Menggunakan data hujan R24 = {st.session_state['r24_design']:.2f} mm")
        r24_drain = st.session_state['r24_design']
    else:
        r24_drain = st.number_input("Masukkan Hujan Harian (R24) mm", value=120.0)
        
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        A_catchment_ha = st.number_input("Luas Tangkapan (Hektar)", value=10.0) # Konversi ke km2 nanti
        tc_menit = st.number_input("Waktu Konsentrasi (tc) menit", value=30.0)
        C_drain = st.number_input("Koefisien Runoff (C)", value=0.75) # Beton/Aspal
        
    with col_d2:
        slope = st.number_input("Kemiringan Saluran (S)", value=0.005, format="%.4f")
        n_manning = st.number_input("Kekasaran Manning (n)", value=0.013) # Beton
    
    if st.button("Hitung Dimensi Saluran"):
        # 1. Hitung Intensitas (Mononobe)
        tc_hours = tc_menit / 60.0
        I_mononobe = mononobe_intensity(r24_drain, tc_hours)
        
        # 2. Hitung Debit Desain (Rasional)
        # Q = 0.278 * C * I * A (km2)
        # A input ha -> km2 = ha / 100
        A_km2 = A_catchment_ha / 100.0
        Q_design = rational_method_discharge(C_drain, I_mononobe, A_km2)
        
        st.divider()
        st.metric("Intensitas Hujan (Mononobe)", f"{I_mononobe:.2f} mm/jam")
        st.metric("Debit Desain (Q)", f"{Q_design:.3f} m3/s")
        
        st.subheader("Cek Kapasitas Pipa / Gorong-gorong")
        
        # Suggest Diameter
        rec_d, res_check = suggest_diameter(Q_design, slope, n_manning)
        
        st.success(f"Rekomendasi Diameter Pipa: **{rec_d} meter**")
        st.write("Analisis Hidrolika Pipa Terpilih:")
        st.write(f"- Kapasitas Penuh (Qfull): {res_check['Q_full']:.3f} m3/s")
        st.write(f"- Kecepatan Penuh (Vfull): {res_check['V_full']:.2f} m/s")
        st.write(f"- Rasio Pengisian (Qdes/Qfull): {res_check:.1f}%")
        st.write(f"- Status: **{res_check}**")
        
        if res_check > 85:
            st.warning("Catatan: Rasio pengisian > 85%, mendekati kapasitas penuh. Pertimbangkan memperbesar dimensi untuk safety factor (freeboard).")
