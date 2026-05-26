import streamlit as st
from modul.database import ambil_chat_antara, simpan_chat

# 🌟 BALON CHAT DIBUNGKUS FRAGMENT BIAR REFRESH REALTIME PER 3 DETIK
@st.fragment(run_every=3)
def tampilkan_balon_chat_customer(user_sekarang):
    riwayat_chat = ambil_chat_antara(user_sekarang, "admin")
    
    # Wadah utama pembatas scroll
    wadah_chat = st.container(height=450, border=True)
    with wadah_chat:
        if not riwayat_chat:
            st.info("👋 Belum ada obrolan. Silakan sapa admin terlebih dahulu!")
        else:
            for chat in riwayat_chat:
                # Tentukan posisi & warna balon chat
                role_tampilan = "user" if chat["pengirim"] == user_sekarang else "assistant"
                nama_label = "Kamu" if chat["pengirim"] == user_sekarang else "🤵 Admin Sinar"
                
                # 🌟 FIX BUG: Semua st.write WAJIB masuk ke dalam identasi blok "with st.chat_message"
                with st.chat_message(role_tampilan):
                    st.markdown(f"**{nama_label}** <small style='color:gray;'>({chat['tanggal']})</small>", unsafe_allow_html=True)
                    st.write(chat["teks"])

# ==============================================================================
# HALAMAN UTAMA CHAT CUSTOMER
# ==============================================================================
def render_chat_admin():
    st.title("💬 Hubungi Admin Toko")
    st.caption("🔄 *Otomatis memuat pesan baru setiap 3 detik...*")
    
    user_sekarang = st.session_state.get("username", "guest")
    
    # 1. Tampilkan riwayat chat dari fragment pintar
    tampilkan_balon_chat_customer(user_sekarang)
                    
    # 2. Kotak input ditaruh di paling bawah halaman agar tidak mengganggu ketikan keyboard
    pesan_baru = st.chat_input("Ketik pesan kamu ke admin di sini...", key="input_chat_customer_realtime_v2")
    if pesan_baru:
        simpan_chat(pengirim=user_sekarang, penerima="admin", teks=pesan_baru)
        st.rerun()
