import streamlit as st
from modul.database import init_db, load_produk
from modul.halaman_auth import render_login, render_register, render_lupa_password
from modul.halaman_toko import render_belanja, render_keranjang, render_riwayat
from modul.halaman_admin import render_admin

init_db()

if "login" not in st.session_state: st.session_state.login = False
if "username" not in st.session_state: st.session_state.username = ""
if "role" not in st.session_state: st.session_state.role = ""
if "otp_step" not in st.session_state: st.session_state.otp_step = 1 
if "generated_otp" not in st.session_state: st.session_state.generated_otp = ""
if "temp_user_data" not in st.session_state: st.session_state.temp_user_data = {}

# State untuk melacak halaman auth mana yang sedang aktif di halaman utama
if "auth_page" not in st.session_state: st.session_state.auth_page = "Login"

if "produk" not in st.session_state:
    st.session_state.produk = load_produk()
if "keranjang" not in st.session_state:
    st.session_state.keranjang = []

# ==============================================================================
# ALUR NAVIGASI UTAMA
# ==============================================================================
if not st.session_state.login:
    # Jika belum login, sidebar dikosongkan total (Navigasi pindah ke halaman utama)
    if st.session_state.auth_page == "Login":
        render_login()
    elif st.session_state.auth_page == "Register":
        render_register()
    elif st.session_state.auth_page == "Lupa Password":
        render_lupa_password()
else:
    # Jika sudah login, judul Navigation dan menu baru dimunculkan di sidebar
    st.sidebar.title("Navigation")
    st.sidebar.write(f"Logged in as: **{st.session_state.username}** ({st.session_state.role})")
    
    # Hitung badge total item di keranjang secara real-time
    total_item = sum(item["jumlah"] for item in st.session_state.keranjang)
    if total_item > 0:
        nama_menu_keranjang = f"Keranjang & Checkout ( {total_item} )"
    else:
        nama_menu_keranjang = "Keranjang & Checkout"
        
    list_menu = ["Belanja", nama_menu_keranjang, "Riwayat Belanja"]
    if st.session_state.role == "admin": 
        list_menu.append("Admin Panel")
        
    menu = st.sidebar.radio("Pilih Halaman", list_menu)
    
    if st.sidebar.button("Logout"):
        st.session_state.login = False
        st.session_state.username = ""
        st.session_state.role = ""
        st.session_state.keranjang = [] 
        st.rerun()

    # Logika penampilan halaman setelah login
    if menu == "Belanja": 
        render_belanja()
    elif menu == nama_menu_keranjang: 
        render_keranjang()
    elif menu == "Riwayat Belanja": 
        render_riwayat() 
    elif menu == "Admin Panel" and st.session_state.role == "admin": 
        render_admin()
