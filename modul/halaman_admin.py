import streamlit as st  
import sqlite3
import json
import pandas as pd
from modul.database import DB_NAME, load_produk, save_produk, load_users, save_users, ambil_chat_antara, simpan_chat

def render_admin():
    st.title("👑 Panel Kendali Admin")
    
    # 🌟 KITA BUAT 3 TAB AGAR INTEGRASI LIVE CHAT MASUK DENGAN RAPI
    tab_dashboard, tab_kelola_stok, tab_chat_customer = st.tabs([
        "📊 Dashboard Analisis", 
        "📦 Kelola Stok Produk", 
        "💬 Chat Customer"
    ])
    
    # ==============================================================================
    # TAB 1: DASHBOARD ANALISIS & GRAFIK
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
                    use_container_width=True,
                    hide_index=True
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
            
            # File Uploader Gambar Asli Otomatis Terkoneksi Pillow
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
                        from modul.database import proses_dan_simpan_foto
                        
                        st.info("Sedang memproses dan mengecilkan ukuran fotomu...")
                        try:
                            jalur_foto_lokal = proses_dan_simpan_foto(foto_diunggah, nama_produk)
                            
                            produk_gudang.append({
                                "nama": nama_produk,
                                "harga": int(harga_produk),
                                "stok": int(stok_produk),
                                "foto": jalur_foto_lokal  
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
            df_asal = pd.DataFrame(st.session_state.produk)
            df_asal.insert(0, "Pilih", False)
            
            df_diedit = st.data_editor(
                df_asal,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "Pilih": st.column_config.CheckboxColumn("Pilih", help="Centang untuk memilih barang", default=False),
                    "nama": st.column_config.TextColumn("Nama Produk", disabled=True), 
                    "harga": st.column_config.NumberColumn("Harga (Rp)", min_value=0, format="Rp %d"),
                    "stok": st.column_config.NumberColumn("Stok Gudang", min_value=0),
                    "foto": st.column_config.TextColumn("Link Foto URL")
                }
            )
            
            col_save_edit, col_delete = st.columns([1, 1])
            
            with col_save_edit:
                if st.button("💾 Simpan Semua Perubahan Edit", type="primary", use_container_width=True):
                    produk_terupdate = df_diedit.drop(columns=["Pilih"]).to_dict(orient="records")
                    st.session_state.produk = produk_terupdate
                    save_produk(produk_terupdate)
                    st.success("🎉 Semua perubahan harga/stok berhasil disimpan!")
                    st.rerun()
                    
            with col_delete:
                item_dicentang = df_diedit[df_diedit["Pilih"] == True]
                label_hapus = f"🗑️ Hapus {len(item_dicentang)} Barang Terpilih" if not item_dicentang.empty else "🗑️ Hapus Barang Terpilih"
                
                if st.button(label_hapus, type="secondary", use_container_width=True, disabled=item_dicentang.empty):
                    nama_yang_dihapus = item_dicentang["nama"].tolist()
                    produk_tersisa = [p for p in st.session_state.produk if p["nama"] not in nama_yang_dihapus]
                    
                    st.session_state.produk = produk_tersisa
                    save_produk(produk_tersisa)
                    st.success(f"🔥 Berhasil menghapus {len(nama_yang_dihapus)} produk dari database!")
                    st.rerun()
        else:
            st.info("Belum ada produk di dalam gudang.")

    # ==============================================================================
    # 🌟 TAB 3: LIVE CHAT DENGAN CUSTOMER (VERSI DETEKTIF PELACAK DATA)
    # ==============================================================================
    with tab_chat_customer:
        st.subheader("💬 Pusat Bantuan & Chat Customer")
        
        # 🕵️‍♂️ KODE MATA-MATA DETEKTIF: Intip isi seluruh isi tabel database chat secara mentah
        st.write("🔍 **Isi Tabel Database Mentah (Mata-mata):**")
        try:
            conn = sqlite3.connect(DB_NAME)
            df_mentah = pd.read_sql_query("SELECT * FROM pesan_chat", conn)
            conn.close()
            if df_mentah.empty:
                st.warning("⚠️ Waduh! Di database server ini, tabel 'pesan_chat' beneran KOSONG MELONGPONG, Bestie! Data chat tidak pernah tersimpan.")
            else:
                st.dataframe(df_mentah, use_container_width=True) # Tampilkan tabel data asli jika ada
        except Exception as err:
            st.error(f"Gagal mengintip database: {err}")
            
        st.divider() # Batas akhir kode mata-mata
        
        # --- SISA KODE PENAMPIL CHAT YANG LAMA (BIARKAN DI BAWAHNYA) ---
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT pengirim FROM pesan_chat WHERE pengirim != 'admin'
                UNION
                SELECT DISTINCT penerima FROM pesan_chat WHERE penerima != 'admin'
            """)
            pilihan_customer = [row[0] for row in cursor.fetchall() if row[0]]
            conn.close()
        except Exception:
            pilihan_customer = []
            
        if not pilihan_customer:
            st.info("📭 Belum ada pesan chat masuk dari customer mana pun.")
        else:
            col_pilih, col_info = st.columns([2, 3])
            with col_pilih:
                st.write("📁 **Daftar Obrolan Aktif:**")
                customer_dipilih = st.radio("Customer aktif:", options=pilihan_customer, label_visibility="collapsed", key="admin_radio_chat_active")
                
            with col_info:
                st.write(f"💬 **Ruang Obrolan Bersama:** `{customer_dipilih}`")
                st.divider()
                riwayat_chat_admin = ambil_chat_antara("admin", customer_dipilih)
                
                wadah_chat_admin = st.container(height=300, border=True)
                with wadah_chat_admin:
                    if not riwayat_chat_admin:
                        st.info(f"Belum ada riwayat obrolan dengan {customer_dipilih}.")
                    else:
                        for chat in riwayat_chat_admin:
                            role_tampilan = "user" if chat["pengirim"] == "admin" else "assistant"
                            nama_label = "🤵 Anda (Admin)" if chat["pengirim"] == "admin" else f"👤 {chat['pengirim']}"
                            with st.chat_message(role_tampilan):
                                st.write(f"**{nama_label}** <small style='color:gray;'>({chat['tanggal']})</small>", unsafe_allow_html=True)
                                st.write(chat["teks"])
                
                balasan_admin = st.chat_input(f"Balas ke {customer_dipilih}...", key="input_balasan_admin_fix")
                if balasan_admin:
                    simpan_chat(pengirim="admin", penerima=customer_dipilih, teks=balasan_admin)
                    st.rerun()
