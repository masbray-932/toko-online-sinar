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
    # TAB 1: DASHBOARD ANALISIS & GRAFIK (VERSI AMAN DARI OPERATIONAL ERROR)
    # ==============================================================================
    with tab_dashboard:
        st.subheader("📈 Analisis Performa Penjualan")
        
        try:
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
        except Exception as e:
            # Jika tabel transaksi belum siap, tampilkan pesan ramah alih-alih layar merah eror
            st.warning("⚠️ Sistem dashboard belum bisa memuat data harian. Selesaikan 1 transaksi QRIS terlebih dahulu untuk memicu pembuatan data.")

    # ==============================================================================
    # TAB 2: KELOLA STOK PRODUK (INTEGRASI FITUR MANAJEMEN STOK LAMA)
    # ==============================================================================
    with tab_kelola_stok:
        st.subheader("📦 Manajemen Stok Gudang")
        
        # Form Tambah/Update Produk Sederhana bawaan agar file admin kamu langsung bisa dipakai penuh
        st.write("### 🆕 Tambah / Update Produk Baru")
        nama_produk = st.text_input("Nama Produk", key="admin_nama_produk")
        harga_produk = st.number_input("Harga Produk (Rp)", min_value=0, step=1000, key="admin_harga_produk")
        stok_produk = st.number_input("Jumlah Stok", min_value=0, step=1, key="admin_stok_produk")
        foto_produk = st.text_input("Link Foto Produk", placeholder="https://...", key="admin_foto_produk")
        
        if st.button("Simpan ke Gudang", type="primary"):
            if not nama_produk:
                st.error("Nama produk wajib diisi!")
            else:
                # Muat data produk yang ada di session state saat ini
                produk_gudang = list(st.session_state.produk)
                
                # Cek apakah produk sudah ada (jika ada, tinggal diupdate stok & harganya)
                terupdate = False
                for p in produk_gudang:
                    if p["nama"].lower() == nama_produk.lower():
                        p["harga"] = int(harga_produk)
                        p["stok"] = int(stok_produk)
                        if foto_produk:
                            p["foto"] = foto_produk
                        terupdate = True
                        break
                
                # Jika produk baru, masukkan ke daftar list
                if not terupdate:
                    produk_gudang.append({
                        "nama": nama_produk,
                        "harga": int(harga_produk),
                        "stok": int(stok_produk),
                        "foto": foto_produk if foto_produk else "https://via.placeholder.com/150?text=No+Image"
                    })
                
                # Simpan perubahan secara permanen ke database lokal via modul.database
                st.session_state.produk = produk_gudang
                save_produk(produk_gudang)
                st.success(f"Berhasil menyimpan data produk: {nama_produk}!")
                st.rerun()
                
        st.divider()
        st.write("### 📋 Daftar Semua Produk Saat Ini")
        if st.session_state.produk:
            df_stok = pd.DataFrame(st.session_state.produk)
            st.dataframe(df_stok[['nama', 'harga', 'stok']], use_container_width=True)
        else:
            st.info("Belum ada produk di dalam gudang.")
