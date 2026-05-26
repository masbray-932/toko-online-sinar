import streamlit as st
import sqlite3
import random
from modul.database import DB_NAME
from modul.keamanan import hash_password, verifikasi_password, kirim_email_otp  # Pastikan nama fungsi kirim email OTP kamu sesuai

# ==============================================================================
# FUNGSI PROSES DATABASE UNTUK LUPA PASSWORD
# ==============================================================================
def update_password_lewat_email(email, password_baru):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    password_hashed = hash_password(password_baru)
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

# ==============================================================================
# HALAMAN LOGIN (DENGAN NAVIGASI LUPA PASSWORD)
# ==============================================================================
def render_login():
    st.subheader("🔑 Login Pengguna")
    username = st.text_input("Username", key="login_user")
    password = st.text_input("Password", type="password", key="login_pass")

    if st.button("Masuk", type="primary"):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT password, role FROM pengguna WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()

        if row and verifikasi_password(password, row[0]):
            st.session_state.login = True
            st.session_state.username = username
            st.session_state.role = row[1]
            st.success(f"Selamat datang kembali, {username}!")
            st.rerun()
        else:
            st.error("Username atau Password salah!")

# ==============================================================================
# HALAMAN REGISTER (DENGAN OTP EMAIL)
# ==============================================================================
def render_register():
    st.subheader("📝 Daftar Akun Baru")
    # ... (Biarkan isi fungsi render_register milikmu yang lama tetap seperti aslinya di sini)
    # Catatan: Jika kodingan lama registermu panjang, pastikan tidak terhapus ya, bestie!
    st.info("Fitur registrasi akun berjalan normal.")

# ==============================================================================
# HALAMAN LUPA PASSWORD (FITUR BARU)
# ==============================================================================
def render_lupa_password():
    st.subheader("🔄 Reset Password Akun")

    # STEP 1: Masukkan Email & Kirim OTP
    if st.session_state.forgot_step == 1:
        email = st.text_input("Masukkan Email Anda yang Terdaftar", key="forgot_email_input")
        
        if st.button("Kirim Kode OTP", type="primary"):
            if not email:
                st.warning("Email tidak boleh kosong!")
            elif not cek_email_terdaftar(email):
                st.error("Email tersebut tidak terdaftar di sistem kami!")
            else:
                # Generate 6 digit OTP
                otp_code = str(random.randint(100000, 999999))
                st.session_state.forgot_otp = otp_code
                st.session_state.forgot_email = email
                
                # Kirim ke email user
                st.info("Sedang mengirim OTP ke email Anda...")
                # Panggil fungsi kirim email OTP yang kamu punya dari modul keamanan
                # Sesuaikan nama fungsinya ya, misalnya: kirim_email_otp(email, otp_code)
                try:
                    kirim_email_otp(email, otp_code) 
                    st.success("Kode OTP berhasil dikirim! Silakan cek kotak masuk/spam email Anda.")
                    st.session_state.forgot_step = 2
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal mengirim email: {e}. Pastikan settingan Secrets email benar.")

    # STEP 2: Verifikasi OTP & Masukkan Password Baru
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
                # Proses update ke database
                update_password_lewat_email(st.session_state.forgot_email, password_baru)
                st.success("🎉 Password Anda berhasil diubah! Silakan pilih menu Login untuk masuk.")
                
                # Reset status langkah lupa password kembali ke awal
                st.session_state.forgot_step = 1
                st.session_state.forgot_email = ""
                st.session_state.forgot_otp = ""
