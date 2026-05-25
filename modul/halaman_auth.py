import streamlit as st
import random
from modul.database import load_users, save_users
from modul.keamanan import hash_password, check_password, send_otp_email

def render_register():
    st.title("📝 Register Akun Baru")
    
    if st.session_state.otp_step == 1:
        reg_username = st.text_input("Username Baru", key="reg_user")
        reg_email = st.text_input("Email untuk OTP", key="reg_email", placeholder="contoh@gmail.com")
        reg_password = st.text_input("Password Baru", type="password", key="reg_pass")
        konfirmasi = st.text_input("Konfirmasi Password", type="password", key="reg_konf")

        if st.button("Kirim Kode OTP"):
            users = load_users()
            if not reg_username or not reg_email or not reg_password:
                st.error("Semua data tidak boleh kosong!")
            elif reg_username in users:
                st.error("Username sudah terdaftar!")
            elif reg_password != konfirmasi:
                st.error("Konfirmasi password tidak cocok!")
            elif "@" not in reg_email or "." not in reg_email:
                st.error("Format email tidak valid!")
            else:
                otp_code = str(random.randint(100000, 999999))
                st.info("Sedang mengirim OTP...")
                if send_otp_email(reg_email, otp_code):
                    st.session_state.generated_otp = otp_code
                    st.session_state.temp_user_data = {
                        "username": reg_username, "password": hash_password(reg_password), "role": "user"
                    }
                    st.session_state.otp_step = 2
                    st.rerun()

    elif st.session_state.otp_step == 2:
        st.warning("Kode OTP telah dikirim ke email.")
        input_otp = st.text_input("Masukkan 6 Digit Kode OTP", key="input_otp_user", max_chars=6)
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("Verifikasi & Daftar"):
                if input_otp == st.session_state.generated_otp:
                    users = load_users()
                    username_baru = st.session_state.temp_user_data["username"]
                    users[username_baru] = {
                        "password": st.session_state.temp_user_data["password"], "role": st.session_state.temp_user_data["role"]
                    }
                    save_users(users)
                    st.session_state.otp_step = 1
                    st.session_state.generated_otp = ""
                    st.session_state.temp_user_data = {}
                    st.success("Register berhasil! Silakan ke menu Login.")
                else:
                    st.error("Kode OTP salah!")
        with col_btn2:
            if st.button("Batal / Kembali"):
                st.session_state.otp_step = 1
                st.session_state.generated_otp = ""
                st.session_state.temp_user_data = {}
                st.rerun()

def render_login():
    st.session_state.otp_step = 1 
    st.title("🔐 Login Toko")
    login_username = st.text_input("Username", key="log_user")
    login_password = st.text_input("Password", type="password", key="log_pass")

    if st.button("Login"):
        users = load_users()
        if login_username in users:
            if check_password(login_password, users[login_username]["password"]):
                st.session_state.login = True
                st.session_state.username = login_username
                st.session_state.role = users[login_username]["role"]
                st.success("Login Berhasil!")
                st.rerun()
            else:
                st.error("Username atau password salah")
        else:
            st.error("Username atau password salah")