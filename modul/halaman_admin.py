import streamlit as st
import os
import sqlite3
from modul.database import DB_NAME, save_produk, load_produk

def render_admin():
    st.title("⚙️ Admin Dashboard")
    tab1, tab2, tab3 = st.tabs(["➕ Tambah Produk", "✏️ Edit Stok", "❌ Hapus Produk"])
    
    with tab1:
        st.subheader("Tambah Produk Baru")
        new_nama = st.text_input("Nama Produk")
        new_harga = st.number_input("Harga (Rp)", min_value=0, step=1000)
        new_stok = st.number_input("Jumlah Stok Awal", min_value=0, step=1)
        uploaded_file = st.file_uploader("Upload Foto Produk", type=["jpg", "jpeg", "png"])
        
        if st.button("Simpan Produk Baru"):
            if new_nama:
                saved_image_path = None
                if uploaded_file is not None:
                    file_extension = uploaded_file.name.split(".")[-1]
                    clean_nama = "".join(x for x in new_nama if x.isalnum())
                    saved_image_path = f"img/{clean_nama}.{file_extension}"
                    with open(saved_image_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                
                st.session_state.produk.append({
                    "nama": new_nama, "harga": int(new_harga), "stok": int(new_stok), "foto": saved_image_path
                })
                save_produk(st.session_state.produk)
                st.success(f"Produk {new_nama} berhasil disimpan!")
                st.rerun()

    with tab2:
        st.subheader("Ubah Stok Produk")
        list_nama_produk = [p["nama"] for p in st.session_state.produk]
        if list_nama_produk:
            pilih_produk = st.selectbox("Pilih produk yang mau diedit", list_nama_produk)
            stok_sekarang = next((p["stok"] for p in st.session_state.produk if p["nama"] == pilih_produk), 0)
            stok_baru = st.number_input("Set Stok Baru", min_value=0, value=stok_sekarang, step=1)
            
            if st.button("Update Stok"):
                for p in st.session_state.produk:
                    if p["nama"] == pilih_produk:
                        p["stok"] = int(stok_baru)
                save_produk(st.session_state.produk)
                st.success(f"Stok {pilih_produk} diubah menjadi {stok_baru}!")
                st.rerun()

    with tab3:
        st.subheader("Hapus Produk dari Toko")
        list_hapus_produk = [p["nama"] for p in st.session_state.produk]
        if list_hapus_produk:
            pilih_hapus = st.selectbox("Pilih produk yang mau dihapus", list_hapus_produk)
            if st.button("Hapus Produk"):
                for p in st.session_state.produk:
                    if p["nama"] == pilih_hapus and p.get("foto") and os.path.exists(p["foto"]):
                        try: os.remove(p["foto"])
                        except: pass
                
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM produk WHERE nama = ?", (pilih_hapus,))
                conn.commit()
                conn.close()
                
                st.session_state.produk = load_produk()
                st.warning(f"Produk {pilih_hapus} berhasil dihapus permanen!")
                st.rerun()