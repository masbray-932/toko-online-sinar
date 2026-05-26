import streamlit as st
import os
import json
import sqlite3
import requests
import base64
import time

# ==============================================================================
# WAJIB ADA: Import fungsi database agar dikenali oleh halaman_toko.py
# ==============================================================================
from modul.database import DB_NAME, save_produk, save_transaksi, buat_invoice_pdf

# ==============================================================================
# 1. FUNGSI INTEGRASI API MIDTRANS SANDBOX (VERSI UTUH & SEMPURNA)
# ==============================================================================
def buat_link_midtrans(order_id, total_harga, username):
    url = "https://app.sandbox.midtrans.com/snap/v1/transactions"
    
    server_key = st.secrets["midtrans"]["SERVER_KEY"]
    
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
# 2. FUNGSI CEK STATUS PEMBAYARAN MIDTRANS (VERSI SEHAT)
# ==============================================================================
def cek_status_midtrans(order_id):
    url = f"https://api.sandbox.midtrans.com/v2/NOTA-{order_id}/status"
    server_key = st.secrets["midtrans"]["SERVER_KEY"]
    
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

        col_foto, col_detail = st.columns([1, 2])
        with col_foto:
            st.image(item["foto"] if item.get("foto") and os.path.exists(item["foto"]) else "https://via.placeholder.com/150?text=No+Image", width=200)

        with col_detail:
            st.write(f"### {item['nama']}")
            st.write(f"Harga: **Rp{item['harga']}** | Stok: {item['stok']} *(Tersedia: {stok_tampilan})*")
            clean_key = "".join(x for x in item["nama"] if x.isalnum())

            if stok_tampilan > 0:
                if st.button(f"Tambah ke Keranjang ({item['nama']})", key=f"beli_{clean_key}"):
                    ada_di_keranjang = False
                    for k_item in st.session_state.keranjang:
                        if k_item["nama"] == item["nama"]:
                            k_item["jumlah"] += 1
                            ada_di_keranjang = True
                            break
                    if not ada_di_keranjang:
                        st.session_state.keranjang.append({"nama": item["nama"], "harga": item["harga"], "jumlah": 1})
                    st.toast(f"{item['nama']} dimasukkan ke keranjang!")
                    st.rerun()
            else:
                st.warning("Stok Penuh/Habis")
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
            st.caption(f"Harga: Rp{item['harga']}")
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
            st.write(f"Rp{subtotal}")
            if st.button("➕", key=f"plus_{index}"):
                if item["jumlah"] < stok_asli_gudang:
                    item["jumlah"] += 1
                    st.rerun()
                else:
                    st.error("Stok gudang tidak mencukupi!")
        st.divider()

    diskon = total * 0.1 if total >= 200000 else 0
    total_akhir = total - diskon

    st.write(f"### Total Kotor: Rp{total}")
    if diskon > 0:
        st.write(f"### 🔥 Diskon Promo (10%): -Rp{int(diskon)}")
    st.write(f"## Total Akhir: Rp{int(total_akhir)}")

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
# 5. HALAMAN RIWAYAT BELANJA (UTUH + RE-INTEGRASI NOTA PDF)
# ==============================================================================
def render_riwayat():
    st.title("🛍️ Riwayat Belanja Kamu")
    
    # KITA AMBIL DATA TRANSAKSI UTK USER YANG SEDANG LOGIN
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, tanggal, items, total_bayar, status, bukti_transfer 
        FROM transaksi 
        WHERE username = ? 
        ORDER BY id DESC
    """, (st.session_state.username,))
    daftar_transaksi = cursor.fetchall()
    conn.close()

    if not daftar_transaksi:
        st.info("Kamu belum pernah melakukan transaksi apa pun.")
        return

    for nota in daftar_transaksi:
        nota_id, tanggal, items_json, total_bayar, status, link_midtrans = nota
        status_tampilan = f"🔴 {status}" if status == "Belum Bayar" else f"🟢 {status}"

        with st.expander(f"Nota #{nota_id} - {tanggal} | {status_tampilan}"):
            st.write("### Detail Barang:")
            list_items = json.loads(items_json)
            for item in list_items:
                st.write(f"- {item['nama']} x {item['jumlah']} : **Rp{item['harga'] * item['jumlah']}**")
            st.write(f"### Total Tagihan: **Rp{int(total_bayar)}**")
            st.divider()

            # JALANKAN LOGIKA TOMBOL UNDUH PDF DI DALAM NOTA
            try:
                pdf_bytes = buat_invoice_pdf(nota_id)
                if pdf_bytes:
                    st.download_button(
                        label="📄 Unduh Nota PDF Resmi",
                        data=bytes(pdf_bytes),
                        file_name=f"Invoice_TokoSinar_TS-{nota_id}.pdf",
                        mime="application/pdf",
                        key=f"dl_pdf_{nota_id}" # Menggunakan ID Nota agar key selalu unik
                    )
            except Exception as e:
                st.caption(f"Gagal memuat sistem cetak PDF: {e}")

            st.write("") # Pembatas ruang kosong kecil

            if status == "Belum Bayar":
                st.warning("Silakan selesaikan pembayaran otomatis Anda melalui tombol di bawah:")
                
                if link_midtrans:
                    st.link_button("💳 Bayar Otomatis Sekarang", url=link_midtrans, type="primary")
                
                st.write("")
                if st.button("🔄 Cek Status Pembayaran", key=f"cek_{nota_id}"):
                    status_terbaru = cek_status_midtrans(nota_id)
                    
                    if status_terbaru in ["settlement", "capture"]:
                        conn = sqlite3.connect(DB_NAME)
                        cursor = conn.cursor()
                        cursor.execute("UPDATE transaksi SET status = 'Lunas / Diproses' WHERE id = ?", (nota_id,))
                        conn.commit()
                        conn.close()
                        st.success("🎉 Pembayaran Anda berhasil terverifikasi otomatis oleh sistem! Pesanan diproses.")
                        st.rerun()
                    else:
                        st.error("Sistem belum mendeteksi adanya pembayaran. Silakan bayar terlebih dahulu di Simulator.")
                        
            elif status in ["Lunas", "Diproses", "Lunas / Diproses"]:
                st.success("🎉 Pembayaran SAH & LUNAS! Barang Anda sedang dikemas oleh admin.")
