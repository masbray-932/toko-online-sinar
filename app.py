import streamlit as st
import sqlite3
import hashlib # 🌟 Murni bawaan python, anti-bentrok/anti-eror
from modul.database import init_db, load_produk, DB_NAME
from modul.halaman_auth import render_login, render_register, render_lupa_password
from modul.halaman_toko import render_belanja, render_keranjang, render_riwayat
from modul.halaman_admin import render_admin

# 🌟 FUNGSI BAYANGAN: Membuat fungsi hash mandiri agar bebas dari impor modul keamanan
def hash_password_mandiri(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# 1. Jalankan Inisialisasi Database
init_db()

# 👑 BUAT AKUN ADMIN OTOMATIS (Aman, menggunakan fungsi hash mandiri)
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()
cursor.execute("SELECT username FROM pengguna WHERE username = 'admin'")
if not cursor.fetchone():
    password_admin_hashed = hash_password_mandiri("admin123") # 👈 Menggunakan fungsi mandiri
    cursor.execute("""
        INSERT INTO pengguna (username, password, email, role) 
        VALUES ('admin', ?, 'admin@toko.com', 'admin')
    """, (password_admin_hashed,))
    conn.commit()
conn.close()

# 2. Inisialisasi Session State
if "login" not in st.session_state: st.session_state.login = False
if "username" not in st.session_state: st.session_state.username = ""
if "role" not in st.session_state: st.session_state.role = ""
if "otp_step" not in st.session_state: st.session_state.otp_step = 1 
if "generated_otp" not in st.session_state: st.session_state.generated_otp = ""
if "temp_user_data" not in st.session_state: st.session_state.temp_user_data = {}

# State navigasi utama halaman login/register/lupa password
if "auth_page" not in st.session_state: st.session_state.auth_page = "Login"

if "produk" not in st.session_state:
    st.session_state.produk = load_produk()
if "keranjang" not in st.session_state:
    st.session_state.keranjang = []

# ==============================================================================
# ALUR TAMPILAN HALAMAN
# ==============================================================================
if not st.session_state.login:
    if st.session_state.auth_page == "Login":
        render_login()
    elif st.session_state.auth_page == "Register":
        render_register()
    elif st.session_state.auth_page == "Lupa Password":
        render_lupa_password()
else:
    st.sidebar.title("Navigation")
    st.sidebar.write(f"Logged in as: **{st.session_state.username}** ({st.session_state.role})")
    
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

    if menu == "Belanja": 
        render_belanja()
    elif menu == nama_menu_keranjang: 
        render_keranjang()
    elif menu == "Riwayat Belanja": 
        render_riwayat() 
    elif menu == "Admin Panel" and st.session_state.role == "admin": 
        render_admin()
