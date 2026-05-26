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
    # TAB 1: DASHBOARD ANALISIS & GRAFIK (SUDAH AMAN & BEBAS EROR)
    # ==============================================================================
    with tab_dashboard:
        st.subheader("📈 Analisis Performa Penjualan")
        
        try:
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
                df_transaksi['tanggal'] = pd.to_datetime(df_transaksi['tanggal']).dt.date
                
                total_barang_terjual = 0
                for index, row in df_transaksi.iterrows():
                    try:
                        items_list = json.loads(row['items'])
                        total_barang_terjual += sum(item['jumlah'] for item in items_list)
                    except:
                        pass
                
                col_omset, col_transaksi, col_barang = st.columns(3)
                with col_omset:
                    st.metric(label="💰 Total Omset (Lunas)", value=f"Rp{int(df_transaksi['total_bayar'].sum()):,}")
                with col_transaksi:
                    st.metric(label="📦 Transaksi Sukses", value=f"{len(df_transaksi)} Pesanan")
                with col_barang:
                    st.metric(label="🛒 Produk Terjual", value=f"{total_barang_terjual} Pcs")
                    
                st.divider()
                
                st.write("### 📅 Tren Pendapatan Harian")
                df_grafik = df_transaksi.groupby('tanggal')['total_bayar'].sum().reset_index()
                df_grafik = df_grafik.set_index('tanggal')
                st.bar_chart(df_grafik, use_container_width=True)
                
                st.divider()
                
                st.write("### 📜 Daftar Pesanan Lunas Terbaru")
                st.dataframe(
                    df_transaksi[['id', 'tanggal', 'total_bayar']].rename(
                        columns={'id': 'ID Nota', 'tanggal': 'Tanggal', 'total_bayar': 'Total Bayar (Rp)'}
                    ),
                    use_container_width=True
                )
        except Exception as e:
            st.warning("⚠️ Sistem dashboard belum bisa memuat data harian. Selesaikan 1 transaksi QRIS terlebih dahulu untuk memicu pembuatan data.")

    # ==============================================================================
    # TAB 2: KELOLA STOK PRODUK (VERSI AUTO-RESIZE & FILE UPLOADER)
    # ==============================================================================
    with tab_kelola_stok:
        st.subheader("📦 Manajemen Stok Gudang")
        
        # 1. FORM UTK TAMBAH PRODUK BARU
        with st.expander("🆕 Tambah Produk Baru Ke Gudang"):
            nama_produk = st.text_input("Nama Produk Baru", key="admin_nama_produk")
            harga_produk = st.number_input("Harga Produk (Rp)", min_value=0, step=1000, key="admin_harga_produk")
            stok_produk = st.number_input("Jumlah Stok Awal", min_value=0, step=1, key="admin_stok_produk")
            
            # 🌟 PERBAIKAN: Ubah ketikan teks URL menjadi File Uploader Gambar asli!
            foto_diunggah = st.file_uploader("Unggah Foto Produk (Bebas dari HP / Laptop)", type=["jpg", "jpeg", "png"], key="admin_file_foto")
            
            if st.button("Simpan Produk", type="primary"):
                if not nama_produk:
                    st.error("Nama produk wajib diisi!")
                elif not foto_diunggah:
                    st.error("Silakan unggah foto produk terlebih dahulu!")
                else:
                    produk_gudang = list(st.session_state.produk)
                    
                    # Cek duplikasi nama
                    if any(p["nama"].lower() == nama_produk.lower() for p in produk_gudang):
                        st.error("Produk dengan nama tersebut sudah ada!")
                    else:
                        # Panggil fungsi kompresi gambar otomatis kita dari database.py
                        from modul.database import proses_dan_simpan_foto
                        
                        st.info("Sedang memproses dan mengecilkan ukuran fotomu...")
                        try:
                            # Jalankan fungsi Pillow dan dapatkan jalur path lokalnya
                            jalur_foto_lokal = proses_dan_simpan_foto(foto_diunggah, nama_produk)
                            
                            # Masukkan data baru ke list produk
                            produk_gudang.append({
                                "nama": nama_produk,
                                "harga": int(harga_produk),
                                "stok": int(stok_produk),
                                "foto": jalur_foto_lokal  # Hasilnya otomatis jadi 'assets/nama_barang.jpg'
                            })
                            st.session_state.produk = produk_gudang
                            save_produk(produk_gudang)
                            st.success(f"🎉 Sukses! {nama_produk} berhasil ditambah dengan foto otomatis.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Gagal memproses gambar: {e}")

        st.divider()
        st.write("### 📋 Daftar Semua Produk")
        st.caption("💡 Centang kotak **'Pilih'** di bawah untuk melakukan aksi hapus, atau kamu bisa edit langsung isi kolom Harga & Stok di tabel!")
        
        if st.session_state.produk:
            # Ubah list produk menjadi DataFrame pandas
            df_asal = pd.DataFrame(st.session_state.produk)
            
            # Sisipkan kolom Checkbox tiruan bernama 'Pilih' di urutan paling kiri
            df_asal.insert(0, "Pilih", False)
            
            # TAMPILKAN TABEL EDITOR INTERAKTIF DENGAN CHECKBOX
            df_diedit = st.data_editor(
                df_asal,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "Pilih": st.column_config.CheckboxColumn("Pilih", help="Centang untuk memilih barang", default=False),
                    "nama": st.column_config.TextColumn("Nama Produk", disabled=True), # Nama barang dikunci biar ga rusak
                    "harga": st.column_config.NumberColumn("Harga (Rp)", min_value=0, format="Rp %d"),
                    "stok": st.column_config.NumberColumn("Stok Gudang", min_value=0),
                    "foto": st.column_config.TextColumn("Link Foto URL")
                }
            )
            
            # BUAT DUA TOMBOL AKSI DI BAWAH TABEL
            col_save_edit, col_delete = st.columns([1, 1])
            
            with col_save_edit:
                # AKSI 1: SIMPAN PERUBAHAN EDIT LANGSUNG DARI TABEL
                if st.button("💾 Simpan Semua Perubahan Edit", type="primary", use_container_width=True):
                    # Kembalikan DataFrame yang diedit menjadi format list-dict produk (buang kolom 'Pilih')
                    produk_terupdate = df_diedit.drop(columns=["Pilih"]).to_dict(orient="records")
                    st.session_state.produk = produk_terupdate
                    save_produk(produk_terupdate)
                    st.success("🎉 Semua perubahan harga/stok berhasil disimpan!")
                    st.rerun()
                    
            with col_delete:
                # AKSI 2: HAPUS MASAL PRODUK YANG DICENTANG CHKBOX-NYA
                # Filter baris mana saja yang kolom 'Pilih'-nya bernilai True
                item_dicentang = df_diedit[df_diedit["Pilih"] == True]
                
                label_hapus = f"🗑️ Hapus {len(item_dicentang)} Barang Terpilih" if not item_dicentang.empty else "🗑️ Hapus Barang Terpilih"
                
                if st.button(label_hapus, type="secondary", use_container_width=True, disabled=item_dicentang.empty):
                    nama_yang_dihapus = item_dicentang["nama"].tolist()
                    
                    # Filter dan sisakan produk yang namanya tidak ada di daftar hapus
                    produk_tersisa = [p for p in st.session_state.produk if p["nama"] not in nama_yang_dihapus]
                    
                    st.session_state.produk = produk_tersisa
                    save_produk(produk_tersisa)
                    st.success(f"🔥 Berhasil menghapus {len(nama_yang_dihapus)} produk dari database!")
                    st.rerun()
        else:
            st.info("Belum ada produk di dalam gudang.")
