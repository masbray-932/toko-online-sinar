import streamlit as st
import sqlite3
import random
from modul.database import DB_NAME
import modul.keamanan as keamanan 

# ==============================================================================
# FUNGSI PROSES DATABASE
# ==============================================================================
def update_password_lewat_email(email, password_baru):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    password_hashed = keamanan.hash_password(password_baru)
    cursor.execute("UPDATE pengguna SET password = ? WHERE email = ?", (password_hashed, email))
    conn.commit()
    conn.close()

def cek_email_terdaftar(email):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM pengguna WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    return user is not None

def cek_username_terdaftar(username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM pengguna WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user is not None

def simpan_pengguna_baru(username, password_polos, email, role="user"):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    password_hashed = keamanan.hash_password(password_polos)
    cursor.execute("""
        INSERT INTO pengguna (username, password, email, role) 
        VALUES (?, ?, ?, ?)
    """, (username, password_hashed, email, role))
    conn.commit()
    conn.close()

# ==============================================================================
# 1. HALAMAN LOGIN
# ==============================================================================
def render_login():
    st.title("🔑 Login Pengguna")
    username = st.text_input("Username", key="utama_login_user")
    password = st.text_input("Password", type="password", key="utama_login_pass")

    if st.button("Masuk", type="primary"):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT password, role FROM pengguna WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()

        if row and keamanan.verifikasi_password(password, row[0]):
            st.session_state.login = True
            st.session_state.username = username
            st.session_state.role = row[1]
            st.success(f"Selamat datang kembali, {username}!")
            st.rerun()
        else:
            st.error("Username atau Password salah!")
            
    st.write("") 
    col_lupa, col_reg = st.columns([1, 1])
    with col_lupa:
        if st.button("❓ Lupa Password", key="btn_to_forgot"):
            st.session_state.auth_page = "Lupa Password"
            st.rerun()
    with col_reg:
        if st.button("📝 Register Akun Baru", key="btn_to_register"):
            st.session_state.auth_page = "Register"
            st.rerun()

# ==============================================================================
# 2. HALAMAN REGISTER (DENGAN EMAIL OTP PULIH TOTAL)
# ==============================================================================
def render_register():
    st.title("📝 Daftar Akun Baru")
    
    # STEP 1: Isi Formulir Pendaftaran
    if st.session_state.otp_step == 1:
        reg_username = st.text_input("Buat Username", key="reg_user")
        reg_email = st.text_input("Masukkan Email Aktif", key="reg_email")
        reg_password = st.text_input("Buat Password", type="password", key="reg_pass")
        reg_confirm = st.text_input("Ulangi Password", type="password", key="reg_confirm")
        
        if st.button("Kirim OTP Registrasi", type="primary"):
            if not reg_username or not reg_email or not reg_password:
                st.warning("Semua kolom formulir wajib diisi!")
            elif reg_password != reg_confirm:
                st.error("Konfirmasi password tidak cocok!")
            elif cek_username_terdaftar(reg_username):
                st.error("Username sudah digunakan! Silakan cari nama lain.")
            elif cek_email_terdaftar(reg_email):
                st.error("Email sudah terdaftar! Gunakan email lain atau pilih Lupa Password.")
            else:
                # Generate OTP 6 digit
                otp_code = str(random.randint(100000, 999999))
                st.session_state.generated_otp = otp_code
                
                # Simpan data sementara ke session state
                st.session_state.temp_user_data = {
                    "username": reg_username,
                    "email": reg_email,
                    "password": reg_password
                }
                
                st.info("Sedang mengirimkan kode OTP ke email Anda...")
                try:
                    keamanan.kirim_otp(reg_email, otp_code)
                    st.success("Kode OTP berhasil dikirim! Silakan periksa kotak masuk/spam email Anda.")
                    st.session_state.otp_step = 2
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal mengirim OTP: {e}. Periksa konfigurasi Secrets email Anda.")
                    
    # STEP 2: Masukkan Kode OTP Validasi
    elif st.session_state.otp_step == 2:
        st.write(f"Kode verifikasi telah dikirim ke: **{st.session_state.temp_user_data['email']}**")
        otp_input = st.text_input("Masukkan 6 Digit Kode OTP", key="reg_otp_input")
        
        if st.button("Verifikasi & Buat Akun", type="primary"):
            if otp_input == st.session_state.generated_otp:
                # Ambil data dari penyimpanan sementara dan masukkan ke database SQLite
                data_user = st.session_state.temp_user_data
                simpan_pengguna_baru(data_user["username"], data_user["password"], data_user["email"], role="user")
                
                st.success("🎉 Akun Anda berhasil dibuat! Silakan kembali ke Halaman Login.")
                
                # Bersihkan data state registrasi
                st.session_state.otp_step = 1
                st.session_state.generated_otp = ""
                st.session_state.temp_user_data = {}
                st.session_state.auth_page = "Login"
                st.rerun()
            else:
                st.error("Kode OTP salah! Silakan periksa kembali email Anda.")
                
        if st.button("🔄 Kirim Ulang OTP / Perbaiki Data", key="reg_resend_otp"):
            st.session_state.otp_step = 1
            st.rerun()

    st.divider()
    if st.button("⬅️ Kembali ke Halaman Login", key="reg_back_login"):
        st.session_state.otp_step = 1
        st.session_state.auth_page = "Login"
        st.rerun()

# ==============================================================================
# 3. HALAMAN LUPA PASSWORD
# ==============================================================================
def render_lupa_password():
    st.title("🔄 Reset Password Akun")

    if st.session_state.forgot_step == 1:
        email = st.text_input("Masukkan Email Anda yang Terdaftar", key="forgot_email_input")
        
        if st.button("Kirim Kode OTP", type="primary"):
            if not email:
                st.warning("Email tidak boleh kosong!")
            elif not cek_email_terdaftar(email):
                st.error("Email tersebut tidak terdaftar di sistem kami!")
            else:
                otp_code = str(random.randint(100000, 999999))
                st.session_state.forgot_otp = otp_code
                st.session_state.forgot_email = email
                
                st.info("Sedang mengirim OTP ke email Anda...")
                try:
                    keamanan.kirim_otp(email, otp_code) 
                    st.success("Kode OTP berhasil dikirim! Silakan cek kotak masuk email Anda.")
                    st.session_state.forgot_step = 2
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal mengirim email: {e}.")

    elif st.session_state.forgot_step == 2:
        st.write(f"Kode OTP telah dikirim ke: **{st.session_state.forgot_email}**")
        otp_input = st.text_input("Masukkan 6 Digit Kode OTP", key="forgot_otp_input")
        password_baru = st.text_input("Masukkan Password Baru Anda", type="password", key="forgot_new_pass")
        konfirmasi_pass = st.text_input("Ulangi Password Baru", type="password", key="forgot_confirm_pass")

        if st.button("Reset Password Sekarang", type="primary"):
            if otp_input != st.session_state.forgot_otp:
                st.error("Kode OTP salah atau tidak cocok!")
            elif not password_baru:
                st.warning("Password baru tidak boleh kosong!")
            elif password_baru != konfirmasi_pass:
                st.error("Konfirmasi password tidak cocok!")
            else:
                update_password_lewat_email(st.session_state.forgot_email, password_baru)
                st.success("🎉 Password berhasil diubah! Silakan login.")
                
                st.session_state.forgot_step = 1
                st.session_state.forgot_email = ""
                st.session_state.forgot_otp = ""
                st.session_state.auth_page = "Login"
                st.rerun()
                
    st.divider()
    if st.button("⬅️ Batalkan, Kembali ke Login", key="forgot_back_login"):
        st.session_state.forgot_step = 1
        st.session_state.auth_page = "Login"
        st.rerun()
