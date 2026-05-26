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
    # 🌟 KEMBALIKAN KE SANDBOX karena akunmu terdaftar di sistem uji coba
    url = "https://app.sandbox.midtrans.com/snap/v1/transactions"
    
    server_key = st.secrets["midtrans"]["SERVER_KEY"]
    server_key = server_key.strip() # Bersihkan spasi gaib
    
    # Proses Enkripsi Basic Auth yang presisi
    auth_string = f"{server_key}:"
    auth_encoded = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Basic {auth_encoded}"
    }
    
    unique_order_id = f"NOTA-{order_id}-{int(time.time())}"
    
    payload = {
        "transaction_details": {
            "order_id": unique_order_id,
            "gross_amount": int(total_harga)
        },
        "customer_details": {
            "first_name": username
        },
        "expiry": {
            "duration": 15,
            "unit": "minutes"
        }
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
# 2. FUNGSI CEK STATUS PEMBAYARAN MIDTRANS
# ==============================================================================
def cek_status_midtrans(order_id):
    # 🌟 KEMBALIKAN KE API SANDBOX
    url = f"https://api.sandbox.midtrans.com/v2/NOTA-{order_id}/status"
    server_key = st.secrets["midtrans"]["SERVER_KEY"]
    server_key = server_key.strip()
    
    auth_string = f"{server_key}:"
    auth_encoded = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Basic {auth_encoded}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        return data.get("transaction_status")
    except:
        return None

# ==============================================================================
# 3. HALAMAN KATALOG BELANJA (VERSI INTERAKTIF QUANTITY COUNTER)
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

        # Pemilihan gambar (Lokal vs Internet)
        url_foto = item.get("foto", "")
        if url_foto.startswith("http://") or url_foto.startswith("https://"):
            foto_tampilan = url_foto
        elif url_foto and os.path.exists(url_foto):
            foto_tampilan = url_foto
        else:
            foto_tampilan = "https://via.placeholder.com/150?text=No+Image"

        col_foto, col_detail = st.columns([1, 2])
        with col_foto:
            st.image(foto_tampilan, width=200)

        with col_detail:
            st.write(f"### {item['nama']}")
            st.write(f"Harga: **Rp {item['harga']:,}** | Stok Total: {item['stok']} *(Tersedia: {stok_tampilan} pcs)*")
            clean_key = "".join(x for x in item["nama"] if x.isalnum())

            if stok_tampilan > 0:
                col_counter, col_tombol = st.columns([1, 2])
                
                with col_counter:
                    qty_dipilih = st.number_input(
                        "Jumlah",
                        min_value=1,
                        max_value=int(stok_tampilan),
                        value=1,
                        step=1,
                        key=f"qty_{clean_key}"
                    )
                
                with col_tombol:
                    st.write("") 
                    st.write("") 
                    if st.button(f"🛒 Masukkan ({qty_dipilih} Pcs)", key=f"beli_{clean_key}", type="primary"):
                        ada_di_keranjang = False
                        for k_item in st.session_state.keranjang:
                            if k_item["nama"] == item["nama"]:
                                k_item["jumlah"] += int(qty_dipilih)
                                ada_di_keranjang = True
                                break
                        
                        if not ada_di_keranjang:
                            st.session_state.keranjang.append({
                                "nama": item["nama"], 
                                "harga": item["harga"], 
                                "jumlah": int(qty_dipilih)
                            })
                        st.toast(f"✅ {qty_dipilih} Pcs {item['nama']} berhasil dimasukkan ke keranjang!")
                        st.rerun()
            else:
                st.warning("🔒 Maaf, Stok Produk Habis / Sudah Penuh di Keranjang")
        st.divider()

# ==============================================================================
# 4. HALAMAN KERANJANG & CHECKOUT
# ==============================================================================
def render_keranjang():
    st.title("🛍️ Keranjang Belanja Anda")

    if len(st.session_state.keranjang) == 0:
        st.info("Keranjang Anda masih kosong.")
        return

    total = 0
    col_h1, col_h2, col_h3, col_h4 = st.columns([3, 1, 1, 2])
    col_h1.write("**Nama Barang**")
    col_h2.write("**Aksi**")
    col_h3.write("**Qty**")
    col_h4.write("**Subtotal**")
    st.divider()

    for index, item in enumerate(list(st.session_state.keranjang)):
        col1, col2, col3, col4 = st.columns([3, 1, 1, 2])
        stok_asli_gudang = next((p["stok"] for p in st.session_state.produk if p["nama"] == item["nama"]), 0)

        with col1:
            st.write(item["nama"])
            st.caption(f"Harga: Rp {item['harga']:,}")
        with col2:
            if st.button("➖", key=f"minus_{index}"):
                if item["jumlah"] > 1:
                    item["jumlah"] -= 1
                else:
                    st.session_state.keranjang.pop(index)
                st.rerun()
        with col3:
            st.write(f"**{item['jumlah']}**")

        subtotal = item["harga"] * item["jumlah"]
        total += subtotal

        with col4:
            st.write(f"Rp {subtotal:,}")
            if st.button("➕", key=f"plus_{index}"):
                if item["jumlah"] < stok_asli_gudang:
                    item["jumlah"] += 1
                    st.rerun()
                else:
                    st.error("Stok gudang tidak mencukupi!")
        st.divider()

    diskon = total * 0.1 if total >= 200000 else 0
    total_akhir = total - diskon

    st.write(f"### Total Kotor: Rp {total:,}")
    if diskon > 0:
        st.write(f"### 🔥 Diskon Promo (10%): -Rp {int(diskon):,}")
    st.write(f"## Total Akhir: Rp {int(total_akhir):,}")

    if st.button("Selesaikan Pembayaran (Checkout)", type="primary"):
        gagal_checkout = False
        for k_item in st.session_state.keranjang:
            for p in st.session_state.produk:
                if p["nama"] == k_item["nama"] and p["stok"] < k_item["jumlah"]:
                    gagal_checkout = True
                    st.error(f"Maaf, stok {p['nama']} tiba-tiba habis.")
        
        if not gagal_checkout:
            for k_item in st.session_state.keranjang:
                for p in st.session_state.produk:
                    if p["nama"] == k_item["nama"]:
                        p["stok"] -= k_item["jumlah"]
            
            save_produk(st.session_state.produk)
            save_transaksi(st.session_state.username, st.session_state.keranjang, total_akhir)
            
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT max(id) FROM transaksi WHERE username = ?", (st.session_state.username,))
            id_nota_terakhir = cursor.fetchone()[0]
            conn.close()
            
            st.info("Menghubungkan ke gerbang pembayaran Midtrans...")
            link_pembayaran = buat_link_midtrans(id_nota_terakhir, total_akhir, st.session_state.username)
            
            if link_pembayaran:
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("UPDATE transaksi SET bukti_transfer = ? WHERE id = ?", (link_pembayaran, id_nota_terakhir))
                conn.commit()
                conn.close()
                
                st.session_state.keranjang = []
                st.success("Checkout Berhasil! Link Pembayaran Otomatis telah dibuat.")
                st.balloons()
                st.rerun()
            else:
                st.error("Gagal membuat link pembayaran, silakan hubungi admin.")

# ==============================================================================
# 5. HALAMAN RIWAYAT BELANJA (SINKRON DATA JSON + LOGISTIK)
# ==============================================================================
def render_riwayat():
    st.title("📜 Riwayat Belanja Kamu")
    username = st.session_state.get("username")
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, total_bayar, tanggal, status, kurir, no_resi 
        FROM transaksi 
        WHERE username = ? 
        ORDER BY id DESC
    """, (username,))
    daftar_transaksi = cursor.fetchall()
    conn.close()
    
    if not daftar_transaksi:
        st.info("🛒 Kamu belum pernah melakukan transaksi apa pun.")
        return
        
    for trx in daftar_transaksi:
        trx_id, total_bayar, tanggal, status, kurir, no_resi = trx
        
        if status == "Belum Bayar":
            status_badge = "🔴 **Belum Bayar**"
        elif status in ["Diproses", "Lunas", "Lunas / Diproses"]:
            status_badge = "🟡 **Sedang Dipacking**"
        elif status == "Siap di-Jemput":
            status_badge = "🔵 **Siap di-Jemput Kurir**"
        elif status == "Dikirim":
            status_badge = "🚚 **Dalam Pengiriman**"
        else:
            status_badge = "🟢 **Selesai**"
            
        with st.expander(f"📦 Nota #{trx_id} — {tanggal} — ({status})"):
            st.write(f"📅 **Tanggal Transaksi:** {tanggal}")
            st.write(f"💰 **Total Belanja:** Rp {int(total_bayar):,}")
            st.write(f"📌 **Status Pesanan:** {status_badge}")
            
            if status in ["Siap di-Jemput", "Dikirim", "Selesai"]:
                st.info(f"🚚 **Informasi Ekspedisi:**\n- Jasa Pengiriman: `{kurir}`\n- Nomor Resi: `{no_resi}`")
            
            st.write("🛍️ **Daftar Produk yang Dibeli:**")
            
            try:
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("SELECT items FROM transaksi WHERE id = ?", (trx_id,))
                items_json = cursor.fetchone()[0]
                conn.close()
                
                items_list = json.loads(items_json)
                for item in items_list:
                    subtotal_item = item["harga"] * item["jumlah"]
                    st.write(f"- {item['nama']} (x{item['jumlah']}) — Rp {subtotal_item:,}")
            except Exception as e:
                st.write("⚠️ Gagal memuat daftar produk.")
                
            if status == "Dikirim":
                if st.button(f"✅ Konfirmasi Barang Diterima (#{trx_id})", key=f"btn_selesai_{trx_id}"):
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("UPDATE transaksi SET status = 'Selesai' WHERE id = ?", (trx_id,))
                    conn.commit()
                    conn.close()
                    st.success("Terima kasih sudah berbelanja di Toko Sinar! ❤️")
                    st.rerun()
