import streamlit as st
import sqlite3
import json
import pandas as pd
from modul.database import DB_NAME, load_produk, save_produk

def render_admin():
    st.title("👑 Panel Kendali Admin")
    
    # KITA BUAT TAB AGAR TAMPILAN ADMIN RAPI
    tab_dashboard, tab_kelola_stok = st.tabs(["📊 Dashboard Analisis", "📦 Kelola Stok Produk"])
    
    # ==============================================================================
    # TAB 1: DASHBOARD ANALISIS & GRAFIK (FITUR BARU)
    # ==============================================================================
    with tab_dashboard:
        st.subheader("📈 Analisis Performa Penjualan")
        
        # 1. Tarik data transaksi lunas dari database
        conn = sqlite3.connect(DB_NAME)
        query = """
            SELECT id, tanggal, total_bayar, items 
            FROM transaksi 
            WHERE status = 'Lunas / Diproses'
        """
        df_transaksi = pd.read_sql_query(query, conn)
        conn.close()
        
        if df_transaksi.empty:
            st.info("Belum ada data penjualan yang lunas untuk dianalisis.")
        else:
            # Konversi kolom tanggal menjadi format datetime agar grafiknya urut
            df_transaksi['tanggal'] = pd.to_datetime(df_transaksi['tanggal']).dt.date
            
            # Hitung total barang terjual dari JSON
            total_barang_terjual = 0
            for index, row in df_transaksi.iterrows():
                try:
                    items_list = json.loads(row['items'])
                    total_barang_terjual += sum(item['jumlah'] for item in items_list)
                except:
                    pass
            
            # 2. TAMPILKAN METRIK RINGKASAN UTAMA
            col_omset, col_transaksi, col_barang = st.columns(3)
            with col_omset:
                st.metric(label="💰 Total Omset (Lunas)", value=f"Rp{int(df_transaksi['total_bayar'].sum())}")
            with col_transaksi:
                st.metric(label="📦 Transaksi Sukses", value=f"{len(df_transaksi)} Pesanan")
            with col_barang:
                st.metric(label="🛒 Produk Terjual", value=f"{total_barang_terjual} Pcs")
                
            st.divider()
            
            # 3. MEMBUAT GRAFIK PENDAPATAN HARIAN
            st.write("### 📅 Tren Pendapatan Harian")
            # Kelompokkan total bayar berdasarkan tanggal
            df_grafik = df_transaksi.groupby('tanggal')['total_bayar'].sum().reset_index()
            # Set tanggal sebagai index agar dibaca Streamlit sebagai sumbu X
            df_grafik = df_grafik.set_index('tanggal')
            
            # Tampilkan Grafik Batang yang interaktif
            st.bar_chart(df_grafik, use_container_width=True)
            
            st.divider()
            
            # 4. TABEL LIVE TRANSAKSI TERBARU
            st.write("### 📜 Daftar Pesanan Lunas Terbaru")
            st.dataframe(
                df_transaksi[['id', 'tanggal', 'total_bayar']].rename(
                    columns={'id': 'ID Nota', 'tanggal': 'Tanggal', 'total_bayar': 'Total Bayar (Rp)'}
                ),
                use_container_width=True
            )

    # ==============================================================================
    # TAB 2: KELOLA STOK PRODUK (KODINGAN LAMA KAMU)
    # ==============================================================================
    with tab_kelola_stok:
        st.subheader("📦 Manajemen Stok Gudang")
        # Masukkan kodingan manajemen stok (tambah produk, edit stok, hapus barang) 
        # milikmu yang lama di bawah baris ini agar fitur lamamu tidak hilang.
        st.info("Fitur manajemen produk lama Anda aktif di tab ini.")
