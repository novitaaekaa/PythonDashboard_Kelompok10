import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import numpy as np
from datetime import datetime
import os


# -------------------------------
# Page Configuration
# -------------------------------
st.set_page_config(
    page_title="Dashboard Kemiskinan Indonesia 2024",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk styling yang lebih menarik
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .stButton > button {
        background: linear-gradient(90deg, #74b9ff 0%, #0984e3 100%);
        color: white;
        border: none;
        border-radius: 20px;
        padding: 0.5rem 2rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    
    .chart-container {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
    }
    
    .data-status {
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
        font-weight: bold;
    }
    
    .status-success {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    
    .status-error {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------
# Direct Data Loading Function
# -------------------------------
@st.cache_data
def load_data_direct():
    """Load data langsung dari file Excel dengan path yang telah ditentukan"""
    
    # Gunakan path relatif atau path absolut
    file_path = 'data_python.xlsx'  # Path absolut yang sudah ditentukan
    
    try:
        # Load semua sheets dari file Excel
        data_provinsi = pd.read_excel(file_path, sheet_name="DATA_PROVINSI")
        data_kabkota = pd.read_excel(file_path, sheet_name="KEMISKINAN_KABKOTA") 
        data_tpak = pd.read_excel(file_path, sheet_name="TPAK_JENISKELAMIN")
        
        # Validasi data
        if data_provinsi.empty:
            return None, None, None, "Data provinsi kosong!"
            
        success_msg = f"✅ Data berhasil dimuat dari: {file_path}"
        return data_provinsi, data_kabkota, data_tpak, success_msg
        
    except FileNotFoundError:
        return None, None, None, f"❌ File tidak ditemukan di: {file_path}"
    except ValueError as e:
        return None, None, None, f"❌ Error sheet Excel: {str(e)}"
    except Exception as e:
        return None, None, None, f"❌ Error loading data: {str(e)}"

# -------------------------------
# Load Data
# -------------------------------

# Load data
data_provinsi, data_kabkota, data_tpak, message = load_data_direct()


# -------------------------------
# Main Dashboard (hanya jika data berhasil dimuat)
# -------------------------------
if data_provinsi is not None and not data_provinsi.empty:
    
    # -------------------------------
    # Header Dashboard
    # -------------------------------
    st.markdown("""
    <div class="main-header">
        <h1> Dashboard Kemiskinan Indonesia 2024</h1>
        <p>Analisis Komprehensif Data Kemiskinan dan Ketenagakerjaan</p>
        <p><strong>Data ter-update:</strong> """ + datetime.now().strftime("%d %B %Y") + """</p>
    </div>
    """, unsafe_allow_html=True)
    
    # -------------------------------
    # Sidebar Controls
    # -------------------------------
    with st.sidebar:
        st.markdown("### 🎛️ Kontrol Dashboard")
        
        # Enhanced filters (tanpa statistik cepat)
        st.markdown("#### 🔍 Filter Data")
        
        # Detect available columns dynamically
        available_columns = [col for col in data_provinsi.columns if col not in ['PROVINSI']]
        
        if available_columns:
            box_filter = st.selectbox(
                "Pilih Variabel untuk Boxplot", 
                options=available_columns,
                help="Pilih variabel untuk analisis distribusi data"
            )
        else:
            box_filter = None
        
        sort_order = st.radio(
            "Urutkan Bar Chart", 
            options=["Descending", "Ascending"],
            help="Pilih urutan data TPT"
        )
        
        # Province filter
        selected_provinces = st.multiselect(
            "Filter Provinsi Spesifik",
            options=data_provinsi["PROVINSI"].tolist(),
            default=data_provinsi["PROVINSI"].tolist(),
            help="Pilih provinsi untuk analisis detail"
        )
        
        # Data range slider
        if "PENDUDUK_MISKIN" in data_provinsi.columns:
            poverty_range = st.slider(
                "Range Penduduk Miskin (Ribu)",
                min_value=int(data_provinsi["PENDUDUK_MISKIN"].min()),
                max_value=int(data_provinsi["PENDUDUK_MISKIN"].max()),
                value=(int(data_provinsi["PENDUDUK_MISKIN"].min()), 
                       int(data_provinsi["PENDUDUK_MISKIN"].max())),
                help="Filter data berdasarkan jumlah penduduk miskin"
            )
        else:
            # Default values jika kolom tidak ada
            poverty_range = (0, 1000)

    # Filter data berdasarkan selection
    if selected_provinces:
        if "PENDUDUK_MISKIN" in data_provinsi.columns:
            filtered_data = data_provinsi[
                (data_provinsi["PROVINSI"].isin(selected_provinces)) &
                (data_provinsi["PENDUDUK_MISKIN"] >= poverty_range[0]) &
                (data_provinsi["PENDUDUK_MISKIN"] <= poverty_range[1])
            ]
        else:
            filtered_data = data_provinsi[data_provinsi["PROVINSI"].isin(selected_provinces)]
    else:
        filtered_data = data_provinsi

    # -------------------------------
    # Interactive Metrics Dashboard
    # -------------------------------
    st.markdown("### 📊 Ringkasan Eksekutif")

    if not filtered_data.empty:
        col1, col2, col3 = st.columns(3)

        with col1:
            if "PENDUDUK_MISKIN" in filtered_data.columns:
                total_poverty = filtered_data["PENDUDUK_MISKIN"].sum()
                st.metric(
                    "Total Penduduk Miskin", 
                    f"{total_poverty:,.0f}K"
                )
            else:
                st.metric("Total Penduduk Miskin", "N/A")

        with col2:
            if "PENDUDUK_MISKIN" in filtered_data.columns:
                avg_poverty_filtered = filtered_data["PENDUDUK_MISKIN"].mean()
                st.metric(
                    "Rata-rata Kemiskinan", 
                    f"{avg_poverty_filtered:.1f}K"
                )
            else:
                st.metric("Rata-rata Kemiskinan", "N/A")

        with col3:
            if "TPT (%)" in filtered_data.columns:
                avg_tpt = filtered_data["TPT (%)"].mean()
                st.metric(
                    "Rata-rata TPT", 
                    f"{avg_tpt:.2f}%"
                )
            else:
                st.metric("Rata-rata TPT", "N/A")

    # -------------------------------
    # Visualizations
    # -------------------------------
    st.markdown("### 🗺️ Visualisasi Data Kemiskinan Indonesia")

    # PENTING: Pastikan ini dalam try-except untuk menangkap error
    try:
        # Tabs untuk berbagai view - SEMUA HARUS DALAM SATU BARIS
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "🗺️ Pemetaan Kemiskinan", 
            "📊 Tingkat Pengangguran Terbuka (%)", 
            "👥 Analisis TPAK", 
            "💰 Kemiskinan", 
            "📈 Boxplot",
            "🎓 Angka Partisipasi Sekolah"
        ])

        # TAB 1: Pemetaan Kemiskinan
        with tab1:
            st.markdown("### 🗺️ Peta Kemiskinan Indonesia (Tingkat Provinsi)")
            
            try:
                if data_provinsi is not None and not data_provinsi.empty:
                    # Cek ketersediaan kolom koordinat
                    lat_col = None
                    lon_col = None
                    poverty_col = None
                    
                    # Cari kolom latitude
                    for col in data_provinsi.columns:
                        if 'LATITUDE' in col.upper() or 'LAT' in col.upper():
                            lat_col = col
                            break
                    
                    # Cari kolom longitude  
                    for col in data_provinsi.columns:
                        if 'LONGITUDE' in col.upper() or 'LON' in col.upper() or 'LONG' in col.upper():
                            lon_col = col
                            break
                    
                    # Cari kolom kemiskinan
                    for col in data_provinsi.columns:
                        if 'PENDUDUK_MISKIN' in col.upper() or 'MISKIN' in col.upper() or 'KEMISKINAN' in col.upper():
                            poverty_col = col
                            break
                    
                    if lat_col and lon_col and poverty_col:
                        # Konversi data ke numeric dan bersihkan
                        map_data = filtered_data.copy()
                        map_data[lat_col] = pd.to_numeric(map_data[lat_col], errors='coerce')
                        map_data[lon_col] = pd.to_numeric(map_data[lon_col], errors='coerce')
                        map_data[poverty_col] = pd.to_numeric(map_data[poverty_col], errors='coerce')
                        
                        # Hapus data yang tidak lengkap
                        map_data = map_data.dropna(subset=[lat_col, lon_col, poverty_col])
                        
                        if not map_data.empty:
                            # === MEMBUAT PETA DENGAN SCATTER_MAPBOX ===
                            fig_map = px.scatter_mapbox(
                                map_data,
                                lat=lat_col,
                                lon=lon_col,
                                size=poverty_col,
                                color=poverty_col,
                                hover_name="PROVINSI",
                                hover_data={
                                    poverty_col: ':.1f',
                                    'TPT (%)': ':.2f' if 'TPT (%)' in map_data.columns else False,
                                    lat_col: False,
                                    lon_col: False
                                },
                                color_continuous_scale=[
                                    [0, '#74b9ff'],      # Biru untuk rendah
                                    [0.25, '#00b894'],   # Hijau untuk sedang-rendah
                                    [0.5, '#fdcb6e'],    # Kuning untuk sedang
                                    [0.75, '#e17055'],   # Orange untuk tinggi
                                    [1, '#d63031']       # Merah untuk sangat tinggi
                                ],
                                size_max=60,
                                zoom=4,
                                mapbox_style="open-street-map",
                                title=f'Peta Kemiskinan Indonesia - {len(map_data)} Provinsi',
                                labels={
                                    poverty_col: 'Penduduk Miskin (Ribu)',
                                    lat_col: 'Lintang',
                                    lon_col: 'Bujur'
                                },
                                center=dict(lat=-2.5, lon=118)  # Pusat Indonesia
                            )
                            
                            # PERBAIKAN UTAMA: Update layout untuk peta yang lebih baik dengan PROPER colorbar
                            fig_map.update_layout(
                                height=600,
                                margin=dict(r=0, t=50, l=0, b=0),
                                # FIXED: Gunakan struktur yang benar untuk colorbar
                                coloraxis_colorbar=dict(
                                    title=dict(
                                        text="Penduduk Miskin<br>(Ribu)",
                                        side="right"  # Gunakan "side" bukan "titleside"
                                    ),
                                    len=0.7,
                                    thickness=15,
                                    x=1.02,  # Posisi colorbar
                                    xanchor="left"
                                ),
                                title=dict(
                                    text=f'Peta Kemiskinan Indonesia - {len(map_data)} Provinsi',
                                    x=0.5,
                                    font=dict(size=18, color='darkblue'),
                                    pad=dict(t=20)
                                )
                            )
                            
                            # Update traces untuk hover yang lebih baik
                            fig_map.update_traces(
                                hovertemplate='<b>%{hovertext}</b><br>' +
                                             'Penduduk Miskin: %{marker.size:.1f} ribu<br>' +
                                             ('<br>TPT: %{customdata[0]:.2f}%' if 'TPT (%)' in map_data.columns else '') +
                                             '<extra></extra>',
                                hovertext=map_data['PROVINSI'],
                                customdata=map_data[['TPT (%)']].values if 'TPT (%)' in map_data.columns else None
                            )
                            
                            st.plotly_chart(fig_map, use_container_width=True)
                            
                        else:
                            st.warning("⚠️ Tidak ada data yang valid untuk ditampilkan")
                    
                    else:
                        st.error("❌ Kolom koordinat atau kemiskinan tidak ditemukan")
                        with st.expander("📋 Informasi Kolom yang Dibutuhkan"):
                            st.write("**Kolom yang tersedia dalam data:**", ', '.join(list(data_provinsi.columns)))
                
                else:
                    st.warning("❌ Data provinsi tidak tersedia")
                    
            except Exception as e:
                st.error(f"❌ Error di Tab 1: {str(e)}")

        # TAB 2: TPT
        with tab2:
            st.markdown("### 📊 Tingkat Pengangguran Terbuka (%)")
            
            try:
                if "TPT (%)" in filtered_data.columns:
                    sorted_data = filtered_data.sort_values("TPT (%)", ascending=(sort_order == "Ascending"))
                    fig_tpt = px.bar(
                        sorted_data.head(10),
                        x="TPT (%)",
                        y="PROVINSI",
                        orientation='h',
                        title="Top 10 Provinsi - Tingkat Pengangguran Terbuka (%)",
                        color="TPT (%)",
                        color_continuous_scale="Reds"
                    )
                    fig_tpt.update_layout(height=500)
                    st.plotly_chart(fig_tpt, use_container_width=True)
                else:
                    st.warning("Kolom 'TPT (%)' tidak ditemukan")
            except Exception as e:
                st.error(f"❌ Error di Tab 2: {str(e)}")

        # TAB 3: TPAK
        with tab3:
            st.markdown("### 👥 Analisis TPAK Berdasarkan Jenis Kelamin")
            
            try:
                if data_tpak is not None and not data_tpak.empty:
                    # Debug info
                    with st.expander("🔍 Debug: Struktur Data TPAK"):
                        st.write("**Kolom dalam data TPAK:**", list(data_tpak.columns))
                        st.dataframe(data_tpak.head())
                
                    # Cek kolom yang dibutuhkan
                    required_cols = ['PROVINSI', 'LAKI-LAKI', 'PEREMPUAN']
                    missing_cols = [col for col in required_cols if col not in data_tpak.columns]
                
                    if not missing_cols:
                        # Pastikan data numerik
                        data_tpak_copy = data_tpak.copy()
                        data_tpak_copy['LAKI-LAKI'] = pd.to_numeric(data_tpak_copy['LAKI-LAKI'], errors='coerce')
                        data_tpak_copy['PEREMPUAN'] = pd.to_numeric(data_tpak_copy['PEREMPUAN'], errors='coerce')
                    
                        # Remove rows with NaN values
                        data_tpak_clean = data_tpak_copy.dropna(subset=['LAKI-LAKI', 'PEREMPUAN'])
                    
                        if not data_tpak_clean.empty:
                            # Line chart perbandingan TPAK
                            fig_tpak_line = px.line(
                                data_tpak_clean,
                                x="PROVINSI",
                                y=["LAKI-LAKI", "PEREMPUAN"],
                                title="Perbandingan TPAK Laki-laki vs Perempuan per Provinsi",
                                labels={'value': 'TPAK (%)', 'PROVINSI': 'Provinsi', 'variable': 'Jenis Kelamin'},
                                color_discrete_map={'LAKI-LAKI': '#3498db', 'PEREMPUAN': '#e74c3c'},
                                height=600,
                                markers=True
                            )
                            fig_tpak_line.update_layout(
                                xaxis_tickangle=-45,
                                xaxis_title="Provinsi",
                                yaxis_title="TPAK (%)",
                                legend_title="Jenis Kelamin"
                            )
                            fig_tpak_line.update_traces(mode='lines+markers', line=dict(width=3), marker=dict(size=8))
                            st.plotly_chart(fig_tpak_line, use_container_width=True)
                        else:
                            st.error("Data TPAK tidak valid - semua nilai kosong atau non-numerik")
                    
                    else:
                        st.error(f"Kolom yang dibutuhkan tidak ditemukan: {missing_cols}")
                        st.write("**Kolom yang tersedia:**", list(data_tpak.columns))
                else:
                    st.warning("Data TPAK tidak tersedia")
            except Exception as e:
                st.error(f"❌ Error di Tab 3: {str(e)}")

        # TAB 4: Kemiskinan  
        with tab4:
            st.markdown("### 💰 Kemiskinan")
            
            try:
                # Poverty bar chart dengan pengecekan kolom
                poverty_col = None
                possible_poverty_cols = ['PENDUDUK_MISKIN', 'MISKIN', 'POVERTY']
                for col in possible_poverty_cols:
                    if col in filtered_data.columns:
                        poverty_col = col
                        break
            
                if poverty_col:
                    # Gunakan sort_order yang sama seperti di tab2
                    sorted_poverty_data = filtered_data.sort_values(poverty_col, ascending=(sort_order == "Ascending"))
                
                    fig_poverty = px.bar(
                        sorted_poverty_data.head(10),
                        x=poverty_col,
                        y="PROVINSI",
                        orientation='h',
                        title=f"Top 10 Provinsi - {poverty_col}",
                        color=poverty_col,
                        color_continuous_scale="Blues"
                    )
                    fig_poverty.update_layout(height=500)
                    st.plotly_chart(fig_poverty, use_container_width=True)
                
                    # Detail kabupaten/kota jika data tersedia
                    if data_kabkota is not None and not data_kabkota.empty:
                        st.markdown("#### 🏘️ Detail Kabupaten/Kota")
                    
                        # Interactive kabupaten/kota selector
                        prov_col = None
                        for col in data_kabkota.columns:
                            if 'PROVINSI' in col.upper() or 'PROV' in col.upper():
                                prov_col = col
                                break
                    
                        if prov_col:
                            available_provinces = data_kabkota[prov_col].unique()
                            selected_prov_detail = st.selectbox(
                                "Pilih Provinsi untuk Detail Kabupaten/Kota",
                                options=available_provinces,
                                key="prov_detail_selector"  # Tambahkan key unik
                            )
                        
                            # Filter kabkota data
                            kabkota_filtered = data_kabkota[data_kabkota[prov_col] == selected_prov_detail]
                        
                            if not kabkota_filtered.empty:
                                # Identify the correct columns
                                kab_col = None
                                kabkota_poverty_col = None
                            
                                for col in data_kabkota.columns:
                                    if 'KAB' in col.upper() or 'KOTA' in col.upper():
                                        kab_col = col
                                    if 'MISKIN' in col.upper() or 'KEMISKINAN' in col.upper():
                                        kabkota_poverty_col = col
                            
                                if kab_col and kabkota_poverty_col:
                                    fig_kabkota = px.bar(
                                        kabkota_filtered.head(15),
                                        x=kab_col,
                                        y=kabkota_poverty_col,
                                        color=kabkota_poverty_col,
                                        title=f"Tingkat Kemiskinan di Kabupaten/Kota - {selected_prov_detail}",
                                        color_continuous_scale="Reds",
                                        text=kabkota_poverty_col
                                    )
                                    fig_kabkota.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                                    fig_kabkota.update_layout(xaxis_tickangle=-45, height=400)
                                    st.plotly_chart(fig_kabkota, use_container_width=True)
                                else:
                                    st.warning("Kolom kabupaten/kota atau kemiskinan tidak ditemukan")
                            else:
                                st.warning(f"Tidak ada data kabupaten/kota untuk {selected_prov_detail}")
                        else:
                            st.warning("Data kabupaten/kota tidak memiliki kolom PROVINSI")
                    else:
                        st.info("Data detail kabupaten/kota tidak tersedia")
                else:
                    st.warning("Kolom penduduk miskin tidak ditemukan")
            except Exception as e:
                st.error(f"❌ Error di Tab 4: {str(e)}")
                
        # TAB 5: Boxplot
        with tab5:
            st.markdown("### 📊 Boxplot")
            
            try:
                if box_filter:
                    fig_box = px.box(
                        filtered_data,
                        y=box_filter,
                        title=f"Distribusi Data: {box_filter}",
                        color_discrete_sequence=["#74b9ff"]
                    )
                    fig_box.update_layout(height=400)
                    st.plotly_chart(fig_box, use_container_width=True)
                else:
                    st.info("Pilih variabel untuk menampilkan boxplot dari sidebar")
            except Exception as e:
                st.error(f"❌ Error di Tab 5: {str(e)}")

        # TAB 6: APS
        with tab6:
            st.markdown("### 🎓 Angka Partisipasi Sekolah")
            
            try:
                # Interactive provinsi selector
                available_provinces_aps = sorted(filtered_data["PROVINSI"].unique())
                selected_prov_aps = st.selectbox(
                    "Pilih Provinsi untuk Detail Angka Partisipasi Sekolah",
                    options=available_provinces_aps,
                    key="aps_selector"  # Tambahkan key unik
                )
            
                if selected_prov_aps:
                    # Filter data berdasarkan provinsi yang dipilih
                    aps_data = filtered_data[filtered_data["PROVINSI"] == selected_prov_aps]
                
                    if not aps_data.empty:
                        # Ambil data dari provinsi yang dipilih
                        selected_province = aps_data.iloc[0]
                    
                        # Ambil nilai dari kolom yang sesuai
                        aps_categories = []
                        aps_values = []
                    
                        # Cari kolom yang mengandung kata kunci APS atau rentang usia
                        for col in filtered_data.columns:
                            if any(keyword in col.upper() for keyword in ['7-12', '13-15', '16-18', '19-23', 'APS']):
                                if col in selected_province.index and pd.notna(selected_province[col]):
                                    aps_categories.append(col)
                                    aps_values.append(float(selected_province[col]))
                    
                        if aps_categories and aps_values:
                            # Buat DataFrame untuk pie chart
                            aps_df = pd.DataFrame({
                                'Kategori': aps_categories,
                                'Nilai': aps_values
                            })
                        
                            # Pie chart
                            fig_pie = px.pie(
                                aps_df,
                                values='Nilai',
                                names='Kategori',
                                title=f"Angka Partisipasi Sekolah - {selected_province['PROVINSI']}",
                                color_discrete_sequence=px.colors.qualitative.Set3
                            )
                            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                            fig_pie.update_layout(height=500)
                            st.plotly_chart(fig_pie, use_container_width=True)
                        else:
                            st.warning("Data APS tidak ditemukan untuk provinsi yang dipilih. Pastikan kolom APS tersedia dengan format yang benar.")
                    else:
                        st.warning(f"Provinsi '{selected_prov_aps}' tidak ditemukan")
                else:
                    st.info("Pilih provinsi untuk melihat data Angka Partisipasi Sekolah")
            except Exception as e:
                st.error(f"❌ Error di Tab 6: {str(e)}")

    except Exception as e:
        st.error(f"❌ Error dalam definisi tabs: {str(e)}")
        st.info("Silakan refresh halaman atau periksa console untuk detail error")

else:
    # Tampilkan pesan error jika data tidak berhasil dimuat
    st.error("❌ Data tidak dapat dimuat!")
    st.markdown(f"**Error message:** {message}")

# -------------------------------
# Footer
# -------------------------------
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
    <p>Dashboard Kemiskinan Indonesia 2024 | Dibuat oleh Kelompok 10</p>
    <p>Ana Rovidhoh (M0722010) | Bernadeta Chrisma Damai S (M0722025) | Novita Eka Permatasari (M0722060)</p>
    <p>Data source: BPS Indonesia | Last updated: """ + datetime.now().strftime("%d %B %Y, %H:%M") + """</p>
    </div>
    """, 
    unsafe_allow_html=True
)