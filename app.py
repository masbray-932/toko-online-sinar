import streamlit as st
from modul.database import init_db, load_produk
from modul.halaman_auth import render_login, render_register
from modul.halaman_toko import render_belanja, render_keranjang, render_riwayat
from modul.halaman_admin import render_admin

init_db()

if "login" not in st.session_state: st.session_state.login = False
if "username" not in st.session_state: st.session_state.username = ""
if "role" not in st.session_state: st.session_state.role = ""
if "otp_step" not in st.session_state: st.session_state.otp_step = 1 
if "generated_otp" not in st.session_state: st.session_state.generated_otp = ""
if "temp_user_data" not in st.session_state: st.session_state.temp_user_data = {}
if "forgot_step" not in st.session_state: st.session_state.forgot_step = 1
if "forgot_email" not in st.session_state: st.session_state.forgot_email = ""
if "forgot_otp" not in st.session_state: st.session_state.forgot_otp = ""

if "produk" not in st.session_state:
    st.session_state.produk = load_produk()
if "keranjang" not in st.session_state:
    st.session_state.keranjang = []

st.sidebar.title("Navigation")

if not st.session_state.login:
    menu = st.sidebar.selectbox("Menu Auth", ["Login", "Register"])
    if menu == "Register": render_register()
    elif menu == "Login": render_login()
else:
    st.sidebar.write(f"Logged in as: **{st.session_state.username}** ({st.session_state.role})")
    
    # ==========================================================================
    # LOGIKA BARU: HITUNG BADGE TOTAL ITEM DI KERANJANG SECARA REAL-TIME
    # ==========================================================================
    total_item = sum(item["jumlah"] for item in st.session_state.keranjang)
    
    if total_item > 0:
        nama_menu_keranjang = f"Keranjang & Checkout ( {total_item} )"
    else:
        nama_menu_keranjang = "Keranjang & Checkout"
    # ==========================================================================
    
    # Masukkan variabel nama_menu_keranjang ke dalam list navigasi
    list_menu = ["Belanja", nama_menu_keranjang, "Riwayat Belanja"]
    if st.session_state.role == "admin": list_menu.append("Admin Panel")
        
    menu = st.sidebar.radio("Pilih Halaman", list_menu)
    
    if st.sidebar.button("Logout"):
        st.session_state.login = False
        st.session_state.username = ""
        st.session_state.role = ""
        st.session_state.keranjang = [] 
        st.rerun()

    # Pengecekan halaman diselaraskan dengan variabel menu dinamis tadi
    if menu == "Belanja": 
        render_belanja()
    elif menu == nama_menu_keranjang: # 👈 Menggunakan variabel agar tidak pecah/eror
        render_keranjang()
    elif menu == "Riwayat Belanja": 
        render_riwayat() 
    elif menu == "Admin Panel" and st.session_state.role == "admin": 
        render_admin()
