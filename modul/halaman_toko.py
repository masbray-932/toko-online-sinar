import streamlit as st
import os
import json
import sqlite3
import requests
import base64
import time
from datetime import datetime
from modul.database import DB_NAME, save_produk, save_transaksi, buat_invoice_pdf

# ==============================================================================
# 1. FUNGSI INTEGRASI API MIDTRANS (VERSI SANDBOX OPTIMIZED)
# ==============================================================================
def buat_link_midtrans(order_id, total_harga, username):
    url = "https://app.sandbox.midtrans.com/snap/v1/transactions"
    server_key = st.secrets["midtrans"]["SERVER_KEY"].strip()
    
    auth_string = f"{server_key}:"
    auth_encoded = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Basic {auth_encoded}"
    }
    
    unique_order_id = f"NOTA-{order_id}-{int(time.time())}"
    
    payload = {
        "transaction_details": {"order_id": unique_order_id, "gross_amount": int(total_harga)},
        "customer_details": {"first_name": username},
        "expiry": {"duration": 15, "unit": "minutes"}
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        if "error_messages" in data:
            st.error(f"Ditolak Midtrans: {data['error_messages']}")
            return None
        return data.get("redirect_url")
    except Exception as e:
        st.error(f"Gagal terhubung ke Midtrans: {e}")
        return None

# ==============================================================================
# 3. HALAMAN KATALOG BELANJA
# ==============================================================================
def render_belanja():
    st.title("🛒 Toko Online Sinar")
    search_query = st.text_input("🔍 Cari produk...", placeholder="Ketik nama produk di sini...")
    produk_ditampilkan = [p for p in st.session_state.produk if search_query.lower() in p["nama"].lower()] if search_query else st.session_state.produk

    if not produk_ditampilkan:
        st.info("Produk tidak ditemukan.")
        return
    
    for item in produk_ditampilkan:
        jumlah_di_keranjang = sum(k["jumlah"] for k in st.session_state.keranjang if k["nama"] == item["nama"])
        stok_tampilan = item["stok"] - jumlah_di_keranjang

        url_foto = item.get("foto", "")
        foto_tampilan = url_foto if url_foto.startswith("http") or os.path.exists(url_foto) else "https://via.placeholder.com/150?text=No+Image"

        col_foto, col_detail = st.columns([1, 2])
        with col_foto:
            st.image(foto_tampilan, width=200)
        with col_detail:
            st.write(f"### {item['nama']}")
            st.write(f"Harga: **Rp {item['harga']:,}** | Stok Total: {item['stok']} *(Tersedia: {stok_tampilan} pcs)*")
            clean_key = "".join(x for x in item["nama"] if x.isalnum())

            if stok_tampilan > 0:
                qty_dipilih = st.number_input("Jumlah", min_value=1, max_value=int(stok_tampilan), value=1, step=1, key=f"qty_{clean_key}")
                if st.button(f"🛒 Masukkan ({qty_dipilih} Pcs)", key=f"beli_{clean_key}", type="primary"):
                    ada = False
                    for k_item in st.session_state.keranjang:
                        if k_item["nama"] == item["nama"]:
                            k_item["jumlah"] += int(qty_dipilih)
                            ada = True
                            break
                    if not ada:
                        st.session_state.keranjang.append({"nama": item["nama"], "harga": item["harga"], "jumlah": int(qty_dipilih)})
                    st.toast(f"✅ {qty_dipilih} Pcs {item['nama']} berhasil dimasukkan!")
                    st.rerun()
            else:
                st.warning("🔒 Stok Habis")
        st.divider()

# ==============================================================================
# 4. HALAMAN KERANJANG & CHECKOUT
# ==============================================================================
def render_keranjang():
    st.title("🛍️ Keranjang Belanja Anda")
    if not st.session_state.keranjang:
        st.info("Keranjang Anda masih kosong.")
        return

    total = 0
    for item in st.session_state.keranjang:
        total += (item["harga"] * item["jumlah"])

    st.write(f"### Total Harga Barang: Rp {total:,}")
    
    st.write("---")
    st.write("### 🚚 Informasi Pengiriman")
    alamat_kirim = st.text_area("📍 Alamat Lengkap Pengiriman", placeholder="Contoh: Jl. Sinar No. 1, Jakarta...")
    
    opsi_kurir = {
        "J&T Express (Regular) — Rp 15,000": {"nama": "J&T Express", "ongkir": 15000},
        "GoSend Sameday — Rp 20,000": {"nama": "GoSend Sameday", "ongkir": 20000},
        "GoSend Instant — Rp 35,000": {"nama": "GoSend Instant", "ongkir": 35000},
        "Ambil di Toko — Rp 0": {"nama": "Ambil di Toko", "ongkir": 0}
    }
    
    pilihan = st.selectbox("📦 Pilih Jasa Pengiriman", options=list(opsi_kurir.keys()))
    data_kurir = opsi_kurir[pilihan]
    
    total_akhir = total - (total * 0.1 if total >= 200000 else 0) + data_kurir["ongkir"]
    st.write(f"## Total Akhir Pembayaran: Rp {int(total_akhir):,}")

    if st.button("Selesaikan Pembayaran (Checkout)", type="primary"):
        if not alamat_kirim:
            st.error("Alamat wajib diisi!")
            return
            
        save_produk(st.session_state.produk)
        save_transaksi(st.session_state.username, st.session_state.keranjang, total_akhir)
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT max(id) FROM transaksi WHERE username = ?", (st.session_state.username,))
        id_nota = cursor.fetchone()[0]
        cursor.execute("UPDATE transaksi SET kurir = ? WHERE id = ?", (f"{data_kurir['nama']} | {alamat_kirim}", id_nota))
        conn.commit()
        conn.close()
        
        link = buat_link_midtrans(id_nota, total_akhir, st.session_state.username)
        if link:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("UPDATE transaksi SET bukti_transfer = ? WHERE id = ?", (link, id_nota))
            conn.commit()
            conn.close()
            st.session_state.keranjang = []
            st.success("Checkout Berhasil!")
            st.link_button("💳 BAYAR SEKARANG", link, type="primary", use_container_width=True)
        else:
            st.error("Gagal membuat link pembayaran.")

# ==============================================================================
# 5. HALAMAN RIWAYAT BELANJA
# ==============================================================================
def render_riwayat():
    st.title("📜 Riwayat Belanja Kamu")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, total_bayar, tanggal, status, kurir, no_resi FROM transaksi WHERE username = ? ORDER BY id DESC", (st.session_state.username,))
    for trx in cursor.fetchall():
        id_trx, total, tgl, status, kurir, resi = trx
        with st.expander(f"📦 Nota #{id_trx} - {status}"):
            st.write(f"📅 {tgl} | 💰 Rp {int(total):,}")
            st.info(f"🚚 {kurir} | 🔢 Resi: {resi}")
            if status == "Belum Bayar":
                conn2 = sqlite3.connect(DB_NAME)
                link = conn2.execute("SELECT bukti_transfer FROM transaksi WHERE id=?", (id_trx,)).fetchone()[0]
                conn2.close()
                st.link_button("💳 Lanjutkan Pembayaran", link, use_container_width=True)
    conn.close()
