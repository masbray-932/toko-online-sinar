import smtplib
from email.mime.text import MIMEText
import streamlit as st

def kirim_otp(email_tujuan, kode_otp):
    """
    Fungsi universal untuk mengirim kode OTP ke email pengguna
    menggunakan data kredensial dari Streamlit Secrets.
    """
    # Ambil konfigurasi email pengirim dari st.secrets
    pengirim = st.secrets["SENDER_EMAIL"]
    password = st.secrets["SENDER_PASSWORD"]
    
    # Atur struktur pesan email
    subjek = "🔐 Kode Verifikasi Toko Sinar"
    isi_pesan = f"""
    Halo, Bestie!
    
    Berikut adalah kode verifikasi OTP rahasia kamu:
    👉 {kode_otp}
    
    Jangan bagikan kode ini kepada siapa pun ya! Kode ini digunakan untuk 
    proses registrasi atau reset password akun tokomu.
    
    Happy Shopping,
    Toko Online Sinar
    """
    
    msg = MIMEText(isi_pesan)
    msg['Subject'] = subjek
    msg['From'] = pengirim
    msg['To'] = email_tujuan
    
    # Proses pengiriman menggunakan server SMTP Gmail
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(pengirim, password)
        server.sendmail(pengirim, email_tujuan, msg.as_string())
