import streamlit as st
import os
import json
import sqlite3
from modul.database import DB_NAME, save_produk

def render_belanja():
    st.title("🛒 Toko Online Saya")
    search_query = st.text_input("🔍 Cari produk...", placeholder="Ketik nama produk di sini...")
    
    produk_ditampilkan = [p for p in st.session_state.produk if search_query.lower() in p["nama"].lower()] if search_query else st.session_state.produk

    if not produk_ditampilkan:
        st.info("Produk tidak ditemukan.")
    
    for item in produk_ditampilkan:
        jumlah_di_keranjang = sum(k["jumlah"] for k in st.session_state.keranjang if k["nama"] == item["nama"])
        stok_tampilan = item["stok"] - jumlah_di_keranjang

        col_foto, col_detail = st.columns([1, 2])
        with col_foto:
            st.image(item["foto"] if item.get("foto") and os.path.exists(item["foto"]) else "https://via.placeholder.com/150?text=No+Image", use_container_width=True)

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
            
            from modul.database import save_transaksi
            save_produk(st.session_state.produk)
            save_transaksi(st.session_state.username, st.session_state.keranjang, total_akhir)
            st.session_state.keranjang = []
            st.success("Checkout Berhasil! Silakan cek menu 'Riwayat Belanja' untuk instruksi pembayaran.")
            st.balloons()
            st.rerun()

def render_riwayat():
    st.title("📜 Riwayat Belanja & Pembayaran")
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, tanggal, items, total_bayar, status, bukti_transfer 
        FROM transaksi WHERE username = ? ORDER BY id DESC
    """, (st.session_state.username,))
    daftar_transaksi = cursor.fetchall()
    conn.close()

    if not daftar_transaksi:
        st.info("Kamu belum pernah melakukan transaksi apa pun.")
        return

    for nota in daftar_transaksi:
        nota_id, tanggal, items_json, total_bayar, status, bukti_foto = nota
        status_tampilan = f"🔴 {status}" if status == "Belum Bayar" else f"🟡 {status}" if status == "Menunggu Verifikasi" else f"🟢 {status}"

        with st.expander(f"Nota #{nota_id} - {tanggal} | {status_tampilan}"):
            st.write("### Detail Barang:")
            list_items = json.loads(items_json)
            for item in list_items:
                st.write(f"- {item['nama']} x {item['jumlah']} : **Rp{item['harga'] * item['jumlah']}**")
            st.write(f"### Total Tagihan: **Rp{total_bayar}**")
            st.divider()

            if status == "Belum Bayar":
                st.info("**Transfer Ke Rekening:**\n* **Bank BCA:** 123-456-7890 (a.n Toko Bestie)\n* **Dana/Gopay:** 0812-3456-7890")
                upload_bukti = st.file_uploader(f"Unggah Struk Transfer Nota #{nota_id}", type=["jpg", "jpeg", "png"], key=f"up_{nota_id}")
                
                if st.button(f"Konfirmasi Pembayaran #{nota_id}", key=f"btn_{nota_id}", type="primary"):
                    if upload_bukti is not None:
                        if not os.path.exists("bukti_bayar"):
                            os.makedirs("bukti_bayar")
                        ext = upload_bukti.name.split(".")[-1]
                        path_simpan_bukti = f"bukti_bayar/nota_{nota_id}.{ext}"
                        with open(path_simpan_bukti, "wb") as f:
                            f.write(upload_bukti.getbuffer())
                        
                        conn = sqlite3.connect(DB_NAME)
                        cursor = conn.cursor()
                        cursor.execute("UPDATE transaksi SET status = 'Menunggu Verifikasi', bukti_transfer = ? WHERE id = ?", (path_simpan_bukti, nota_id))
                        conn.commit()
                        conn.close()
                        st.success("Bukti transfer terkirim!")
                        st.rerun()
                    else:
                        st.error("Silakan unggah foto struk terlebih dahulu!")
            elif status == "Menunggu Verifikasi":
                st.warning("Sedang diverifikasi oleh admin.")
                if bukti_foto and os.path.exists(bukti_foto):
                    st.image(bukti_foto, width=250)
            elif status == "Lunas / Diproses":
                st.success("🎉 Pembayaran Sah! Barang dikemas.")