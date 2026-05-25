import bcrypt
import smtplib
import random
import streamlit as st
from email.mime.text import MIMEText

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = st.secrets["email_konfigurasi"]["SENDER_EMAIL"]
SENDER_PASSWORD = st.secrets["email_konfigurasi"]["SENDER_PASSWORD"]

def hash_password(password):
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode('utf-8')

def check_password(password_input, password_database):
    return bcrypt.checkpw(password_input.encode('utf-8'), password_database.encode('utf-8'))

def send_otp_email(target_email, otp_code):
    msg = MIMEText(f"Kode OTP Registrasi Anda adalah: {otp_code}\nJangan bagikan kode ini kepada siapapun.")
    msg['Subject'] = 'Kode Verifikasi OTP Toko Saya'
    msg['From'] = SENDER_EMAIL
    msg['To'] = target_email

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, target_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.error(f"Gagal mengirim email: {e}")
        return False