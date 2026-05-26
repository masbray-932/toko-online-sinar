import streamlit as st
import time
from modul.database import ambil_chat_antara, simpan_chat

# 🌟 BIKIN FRAGMENT KHUSUS UNTUK AUTO-REFRESH DAFTAR BALON CHAT
@st.fragment(run_every=3)
def tampilkan_balon_chat_customer(user_sekarang):
    riwayat_chat = ambil_chat_antara(user_sekarang, "admin")
    
    wadah_chat = st.container(height=380, border=True)
    with wadah_chat:
        if not riwayat_chat:
            st.info("👋 Belum ada obrolan. Silakan sapa admin terlebih dahulu!")
        else:
            for chat in riwayat_chat:
                role_tampilan = "user" if chat["pengirim"] == user_sekarang else "assistant"
                nama_label = "Kamu" if chat["pengirim"] == user_sekarang else "🤵 Admin Sinar"
                
                with st.chat_message(role_tampilan):
                    st.write(f"**{nama_label}** <small style='color:gray;'>({chat['tanggal']})</small>", unsafe_allow_html=True)
                    st.write(chat["teks"])

# ==============================================================================
# FUNCTION UTAMA UTK DI-RENDER
# ==============================================================================
def render_chat_admin():
    st.title("💬 Hubungi Admin Toko")
    st.caption("🔄 *Halaman ini otomatis memuat pesan baru setiap 3 detik*")
    
    user_sekarang = st.session_state.get("username", "guest")
    
    # 1. Panggil fungsi fragment balon chat agar dia melakukan putaran refresh mandiri
    tampilkan_balon_chat_customer(user_sekarang)
                    
    # 2. Kotak input ditaruh di luar fragment agar tidak nge-reset saat user sedang mengetik
    pesan_baru = st.chat_input("Ketik pesan kamu ke admin di sini...", key="input_chat_customer_realtime")
    if pesan_baru:
        simpan_chat(pengirim=user_sekarang, penerima="admin", teks=pesan_baru)
        st.rerun()
        
    # 2. Ambil semua riwayat chat terbaru antara customer ini dengan user 'admin'
    riwayat_chat = ambil_chat_antara(user_sekarang, "admin")
    
    # Wadah container khusus chat agar bisa discroll dengan rapi
    wadah_chat = st.container(height=400, border=True)
    with wadah_chat:
        if not riwayat_chat:
            st.info("👋 Belum ada obrolan. Silakan sapa admin terlebih dahulu!")
        else:
            for chat in riwayat_chat:
                # Tentukan posisi balon chat: kanan (user) / kiri (assistant)
                role_tampilan = "user" if chat["pengirim"] == user_sekarang else "assistant"
                nama_label = "Kamu" if chat["pengirim"] == user_sekarang else "🤵 Admin Sinar"
                
                with st.chat_message(role_tampilan):
                    st.write(f"**{nama_label}** <small style='color:gray;'>({chat['tanggal']})</small>", unsafe_allow_html=True)
                    st.write(chat["teks"])
