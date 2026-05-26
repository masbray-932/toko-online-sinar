import streamlit as st
import sqlite3
import random
from modul.database import DB_NAME
import modul.keamanan as keamanan 

# ==============================================================================
# FUNGSI PROSES DATABASE UNTUK LUPA PASSWORD
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

# ==============================================================================
# HALAMAN LOGIN (TOMBOL DI HALAMAN UTAMA)
# ==============================================================================
def render_login():
    st.title("🔑 Login Pengguna")
    username = st.text_input("Username", key="login_user")
    password = st.text_input("Password", type="password", key="login_pass")

    # Tombol Masuk Utama
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
            
    st.write("") # Jeda spasial kecil
    
    # KEAJAIBAN TATA LETAK: Kita buat 2 kolom tepat di bawah tombol Masuk
    col_lupa, col_reg = st.columns([1, 1])
    
    with col_lupa:
        # Meniru gaya text link dengan st.button biasa (tanpa border tebal pakai bantuan type)
        if st.button("❓ Lupa Password", key="btn_to_forgot"):
            st.session_state.auth_page = "Lupa Password"
            st.rerun()
            
    with col_reg:
        # Diposisikan di sebelah kanan halaman
        if st.button("📝 Register Akun Baru", key="btn_to_register"):
            st.session_state.auth_page = "Register"
            st.rerun()

# ==============================================================================
# HALAMAN REGISTER (DENGAN EMAIL OTP)
# ==============================================================================
def render_register():
    st.title("📝 Daftar Akun Baru")
    
    # ... (Isi logika form register asli/lama kamu taruh di sini, jangan sampai hilang)
    st.info("Form registrasi akun Anda tampil di sini.")
    
    st.divider()
    # Tombol untuk kembali ke halaman utama login
    if st.button("⬅️ Kembali ke Halaman Login", key="reg_back_login"):
        st.session_state.auth_page = "Login"
        st.rerun()

# ==============================================================================
# HALAMAN LUPA PASSWORD
# ==============================================================================
def render_lupa_password():
    st.title("🔄 Reset Password Akun")

    # STEP 1: Masukkan Email & Kirim OTP
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
                    st.success("Kode OTP berhasil dikirim! Silakan cek email Anda.")
                    st.session_state.forgot_step = 2
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal mengirim email: {e}.")

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
                update_password_lewat_email(st.session_state.forgot_email, password_baru)
                st.success("🎉 Password berhasil diubah!")
                
                # Kembalikan state ke mode login bersih
                st.session_state.forgot_step = 1
                st.session_state.forgot_email = ""
                st.session_state.forgot_otp = ""
                st.session_state.auth_page = "Login"
                st.rerun()
                
    st.divider()
    # Tombol darurat kalau pengguna tiba-tiba ingat passwordnya lagi
    if st.button("⬅️ Batalkan, Kembali ke Login", key="forgot_back_login"):
        st.session_state.forgot_step = 1
        st.session_state.auth_page = "Login"
        st.rerun()
