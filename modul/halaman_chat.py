import streamlit as st
from modul.database import ambil_chat_antara, simpan_chat

# ==============================================================================
# 💬 HALAMAN LIVE CHAT CUSTOMER KE ADMIN (TERPISAH & ANTI-CIRCULAR IMPORT)
# ==============================================================================
def render_chat_admin():
    st.title("💬 Hubungi Admin Toko")
    st.caption("Punya pertanyaan seputar produk atau pesanan? Chat admin di sini ya!")
    
    user_sekarang = st.session_state.username
    
    # Ambil semua riwayat chat antara customer ini dengan user 'admin'
    riwayat_chat = ambil_chat_antara(user_sekarang, "admin")
    
    # Wadah container khusus chat agar bisa discroll dengan rapi
    wadah_chat = st.container(height=400, border=True)
    with wadah_chat:
        if not riwayat_chat:
            st.info("Belum ada obrolan. Silakan sapa admin terlebih dahulu!")
        else:
            for chat in riwayat_chat:
                # Tentukan posisi balon chat: kanan jika dikirim sendiri, kiri jika dari admin
                role_tampilan = "user" if chat["pengirim"] == user_sekarang else "assistant"
                nama_label = "Kamu" if chat["pengirim"] == user_sekarang else "🤵 Admin Sinar"
                
                with st.chat_message(role_tampilan):
                    st.write(f"**{nama_label}** <small style='color:gray;'>({chat['tanggal']})</small>", unsafe_allow_html=True)
                    st.write(chat["teks"])
                    
    # Kotak input pesan di bagian paling bawah halaman
    pesan_baru = st.chat_input("Ketik pesan kamu ke admin di sini...", key="input_chat_customer_baru")
    if pesan_baru:
        simpan_chat(pengirim=user_sekarang, penerima="admin", teks=pesan_baru)
        st.rerun()
