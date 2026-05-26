# ==============================================================================
# 2. HALAMAN REGISTER (VERSI ANTI-SANGKUT & GARANSI MUNCUL 100%)
# ==============================================================================
def render_register():
    st.title("📝 Daftar Akun Baru")
    
    # SAFETY NET: Paksa inisialisasi state jika mendadak hilang atau eror di server
    if "otp_step" not in st.session_state or st.session_state.otp_step not in [1, 2]:
        st.session_state.otp_step = 1
        
    if "temp_user_data" not in st.session_state:
        st.session_state.temp_user_data = {}

    # --------------------------------------------------------------------------
    # STEP 1: Form Isi Data Pengguna (Ini yang harusnya muncul pertama kali)
    # --------------------------------------------------------------------------
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
                st.error("Email sudah terdaftar! Gunakan email lain.")
            else:
                # Generate OTP 6 digit
                otp_code = str(random.randint(100000, 999999))
                st.session_state.generated_otp = otp_code
                
                st.session_state.temp_user_data = {
                    "username": reg_username,
                    "email": reg_email,
                    "password": reg_password
                }
                
                st.info("Sedang mengirimkan kode OTP ke email Anda...")
                try:
                    keamanan.kirim_otp(reg_email, otp_code)
                    st.success("Kode OTP berhasil dikirim! Silakan cek kotak masuk email Anda.")
                    st.session_state.otp_step = 2
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal mengirim OTP: {e}. Periksa settingan Secrets email Anda.")
                    
    # --------------------------------------------------------------------------
    # STEP 2: Kolom Input Kode OTP Validasi
    # --------------------------------------------------------------------------
    elif st.session_state.otp_step == 2:
        st.write(f"Kode verifikasi telah dikirim ke: **{st.session_state.temp_user_data.get('email', '')}**")
        otp_input = st.text_input("Masukkan 6 Digit Kode OTP", key="reg_otp_input")
        
        if st.button("Verifikasi & Buat Akun", type="primary"):
            if otp_input == st.session_state.generated_otp:
                data_user = st.session_state.temp_user_data
                simpan_pengguna_baru(data_user["username"], data_user["password"], data_user["email"], role="user")
                
                st.success("🎉 Akun Anda berhasil dibuat! Silakan kembali ke Halaman Login.")
                
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
