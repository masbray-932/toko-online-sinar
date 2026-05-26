import streamlit as st
import sqlite3
import hashlib
from streamlit_cookies_controller import CookieController # 🌟 TAMBAHAN: Pengendali Cookies
from modul.database import init_db, load_produk, DB_NAME
from modul.halaman_auth import render_login, render_register, render_lupa_password
from modul.halaman_toko import render_belanja, render_keranjang, render_riwayat
from modul.halaman_admin import render_admin

# Inisialisasi pengontrol cookies browser
controller = CookieController()

def hash_password_mandiri(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# 1. Jalankan Inisialisasi Database
init_db()

# 👑 BUAT AKUN ADMIN OTOMATIS
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()
cursor.execute("SELECT username FROM pengguna WHERE username = 'admin'")
if not cursor.fetchone():
    password_admin_hashed = hash_password_mandiri("admin123")
    cursor.execute("""
        INSERT INTO pengguna (username, password, email, role) 
        VALUES ('admin', ?, 'admin@toko.com', 'admin')
    """, (password_admin_hashed,))
    conn.commit()
conn.close()

# 2. Inisialisasi Session State Dasar (Jika Belum Ada)
if "login" not in st.session_state: st.session_state.login = False
if "username" not in st.session_state: st.session_state.username = ""
if "role" not in st.session_state: st.session_state.role = ""
if "otp_step" not in st.session_state: st.session_state.otp_step = 1 
if "generated_otp" not in st.session_state: st.session_state.generated_otp = ""
if "temp_user_data" not in st.session_state: st.session_state.temp_user_data = {}
if "auth_page" not in st.session_state: st.session_state.auth_page = "Login"

if "produk" not in st.session_state:
    st.session_state.produk = load_produk()
if "keranjang" not in st.session_state:
    st.session_state.keranjang = []

# ==============================================================================
# 🌟 KEAJAIBAN ANTI-LOGOUT: Baca Cookies Saat Browser Di-refresh
# ==============================================================================
# Mengambil cookies jika sebelumnya user sudah sukses login
saved_username = controller.get("saved_username")
saved_role = controller.get("saved_role")

if saved_username and saved_role and not st.session_state.login:
    # Kembalikan status login yang sempat hilang akibat refresh browser
    st.session_state.login = True
    st.session_state.username = saved_username
    st.session_state.role = saved_role

# ==============================================================================
# ALUR TAMPILAN HALAMAN
# ==============================================================================
if not st.session_state.login:
    if st.session_state.auth_page == "Login":
        # Jalankan fungsi login
        render_login()
        
        # SENSOR PINTAR: Jika user baru saja sukses klik 'Masuk' di render_login
        if st.session_state.login:
            # Tanam cookies ke browser agar awet saat di-refresh (bertahan 1 hari)
            controller.set("saved_username", st.session_state.username)
            controller.set("saved_role", st.session_state.role)
            st.rerun()
            
    elif st.session_state.auth_page == "Register":
        render_register()
    elif st.session_state.auth_page == "Lupa Password":
        render_lupa_password()
else:
    st.sidebar.title("Navigation")
    st.sidebar.write(f"Logged in as: **{st.session_state.username}** ({st.session_state.role})")
    
    total_item = sum(item["jumlah"] for item in st.session_state.keranjang)
    nama_menu_keranjang = f"Keranjang & Checkout ( {total_item} )" if total_item > 0 else "Keranjang & Checkout"
        
    list_menu = ["Belanja", nama_menu_keranjang, "Riwayat Belanja"]
    if st.session_state.role == "admin": 
        list_menu.append("Admin Panel")
        
    menu = st.sidebar.radio("Pilih Halaman", list_menu)
    
    # 🌟 TOMBOL LOGOUT: Hapus cookies total saat user sengaja klik Logout
    if st.sidebar.button("Logout"):
        controller.remove("saved_username")
        controller.remove("saved_role")
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
