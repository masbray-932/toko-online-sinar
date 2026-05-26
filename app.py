import streamlit as st
import sqlite3
import hashlib
import random
import string
from modul.database import init_db, load_produk, DB_NAME
from modul.halaman_auth import render_login, render_register, render_lupa_password
from modul.halaman_toko import render_belanja, render_keranjang, render_riwayat
from modul.halaman_admin import render_admin

def hash_password_mandiri(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# 1. Jalankan Inisialisasi Database Utama
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

# ==============================================================================
# 🌟 STRUKTUR KEAMANAN BARU: TOKEN VALIDASI MUTAKHIR (ANTI-LINK COPAS BROWSER LAIN)
# ==============================================================================
# Buat kunci rahasia server yang acak setiap kali server berjalan
if "server_secret_seed" not in st.session_state:
    st.session_state["server_secret_seed"] = "".join(random.choices(string.ascii_letters + string.digits, k=16))

# Inisialisasi Session State Dasar
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

# PEMERIKSAAN SAKTI: Cek apakah token di URL cocok dengan token memori internal browser saat ini
url_user = st.query_params.get("user")
url_role = st.query_params.get("role")
url_token = st.query_params.get("token")

# Token internal dihitung dari gabungan username + secret seed server
if url_user and url_role and url_token:
    token_validasi_internal = hashlib.md5(f"{url_user}_{st.session_state['server_secret_seed']}".encode()).hexdigest()
    
    # Jika token di URL COCOK dengan memori internal, pertahankan login (Kasus: User pencet Refresh F5)
    if url_token == token_validasi_internal:
        st.session_state.login = True
        st.session_state.username = url_user
        st.session_state.role = url_role
    else:
        # Jika token TIDAK COCOK (Kasus: Orang lain copas link), paksa bersihkan URL dan tendang ke Login!
        st.query_params.clear()
        st.session_state.login = False
        st.session_state.username = ""
        st.session_state.role = ""

# ==============================================================================
# ALUR TAMPILAN HALAMAN
# ==============================================================================
if not st.session_state.login:
    if st.session_state.auth_page == "Login":
        render_login()
        
        # Jika login sukses dari fungsi render_login, rakit token rahasia dan tempel di URL
        if st.session_state.login:
            token_baru = hashlib.md5(f"{st.session_state.username}_{st.session_state['server_secret_seed']}".encode()).hexdigest()
            st.query_params["user"] = st.session_state.username
            st.query_params["role"] = st.session_state.role
            st.query_params["token"] = token_baru  # 👈 Tempel token pelindung di URL
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
        
    list_menu = ["Belanja", nama_menu_keranjang, "Riwayat Belanja", "💬 Chat Admin"]
    if st.session_state.role == "admin": 
        list_menu.append("Admin Panel")
        
    menu = st.sidebar.radio("Pilih Halaman", list_menu)
    
    # TOMBOL LOGOUT: Bersihkan parameter dan memori total
    if st.sidebar.button("Logout"):
        st.query_params.clear()
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
    elif menu == "💬 Chat Admin":
        from modul.halaman_toko import render_chat_admin
        render_chat_admin()
    elif menu == "Admin Panel" and st.session_state.role == "admin": 
        render_admin()
