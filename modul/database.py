import streamlit as st  
import sqlite3
import json
import os
from datetime import datetime
from fpdf import FPDF  
from PIL import Image

DB_NAME = "toko_online.db"

# ==============================================================================
# FUNGSI INISIALISASI DATABASE UTAMA
# ==============================================================================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Pastikan tabel pengguna dibuat dengan benar
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pengguna (
            username TEXT PRIMARY KEY,
            password TEXT,
            email TEXT
        )
    """)
    
    # 2. FITUR AUTO-FIX Kolom Role
    try:
        cursor.execute("SELECT role FROM pengguna LIMIT 1")
    except sqlite3.OperationalError:
        print("Sistem mendeteksi pembaruan database, menyinkronkan kolom 'role'...")
        cursor.execute("ALTER TABLE pengguna ADD COLUMN role TEXT DEFAULT 'user'")
        conn.commit()

    # 3. Pastikan tabel produk otomatis terbuat
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produk (
            nama TEXT PRIMARY KEY,
            harga INTEGER,
            stok INTEGER,
            foto TEXT
        )
    """)

    # 4. Pastikan tabel transaksi sudah siap
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transaksi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            tanggal TEXT,
            items TEXT,
            total_bayar REAL,
            status TEXT DEFAULT 'Belum Bayar',
            bukti_transfer TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pesan_chat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pengirim TEXT,
            penerima TEXT,
            teks TEXT,
            tanggal TEXT
        )
    """)
    
    conn.commit()
    conn.close()

# ==============================================================================
# FUNGSI KELOLA PENGGUNA
# ==============================================================================
def load_users():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT username, password, email, role FROM pengguna")
    rows = cursor.fetchall()
    conn.close()
    return {row[0]: {"password": row[1], "email": row[2], "role": row[3]} for row in rows}

def save_users(users_dict):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    for username, data in users_dict.items():
        cursor.execute("""
            INSERT OR REPLACE INTO pengguna (username, password, email, role) 
            VALUES (?, ?, ?, ?)
        """, (username, data["password"], data.get("email", ""), data["role"]))
    conn.commit()
    conn.close()

# ==============================================================================
# FUNGSI KELOLA PRODUK GUDANG
# ==============================================================================
def load_produk():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT nama, harga, stok, foto FROM produk")
    rows = cursor.fetchall()
    conn.close()
    return [{"nama": row[0], "harga": row[1], "stok": row[2], "foto": row[3]} for row in rows]

def save_produk(list_produk):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 🌟 OPTIMASI: Kosongkan tabel produk lama agar sinkron total jika ada produk dihapus/diedit
    cursor.execute("DELETE FROM produk")
    
    for p in list_produk:
        cursor.execute("INSERT OR REPLACE INTO produk (nama, harga, stok, foto) VALUES (?, ?, ?, ?)", 
                       (p["nama"], p["harga"], p["stok"], p["foto"]))
    conn.commit()
    conn.close()

# ==============================================================================
# FUNGSI SIMPAN TRANSAKSI NOTA
# ==============================================================================
def save_transaksi(username, keranjang, total_bayar):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    items_json_string = json.dumps(keranjang)
    waktu_sekarang = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO transaksi (username, tanggal, items, total_bayar, bukti_transfer, status) 
        VALUES (?, ?, ?, ?, NULL, 'Belum Bayar')
    """, (username, waktu_sekarang, items_json_string, int(total_bayar)))
    conn.commit()
    conn.close()

# ==============================================================================
# FUNGSI MEMBUAT INVOICE PDF
# ==============================================================================
def buat_invoice_pdf(id_transaksi):
    """Fungsi untuk menghasilkan file PDF invoice berdasarkan ID Transaksi"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT username, tanggal, items, total_bayar, status FROM transaksi WHERE id = ?", (id_transaksi,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
        
    username, tanggal, items_json, total_bayar, status = row
    items = json.loads(items_json)
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Header Nota
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, text="TOKO ONLINE SINAR", ln=True, align="C")
    pdf.set_font("Arial", size=10)
    pdf.cell(190, 5, text="Invoice Resmi Pembelanjaan Online", ln=True, align="C")
    pdf.ln(10)
    
    # Informasi Transaksi
    pdf.set_font("Arial", "B", 11)
    pdf.cell(100, 7, text=f"ID Invoice: #TS-{id_transaksi}", ln=False)
    pdf.cell(90, 7, text=f"Tanggal: {tanggal}", ln=True, align="R")
    
    pdf.set_font("Arial", size=11)
    pdf.cell(100, 7, text=f"Pelanggan: {username}", ln=False)
    pdf.set_font("Arial", "B", 11)
    
    # Status warna teks
    if status in ["Lunas", "Diproses", "Lunas / Diproses"]:
        pdf.set_text_color(0, 128, 0)
    else:
        pdf.set_text_color(255, 0, 0)
        
    pdf.cell(90, 7, text=f"Status: {status.upper()}", ln=True, align="R")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)
    
    # Tabel Barang
    pdf.set_font("Arial", "B", 11)
    pdf.cell(90, 8, text="Nama Produk", border=1, ln=False)
    pdf.cell(35, 8, text="Harga Satuan", border=1, ln=False, align="C")
    pdf.cell(25, 8, text="Jumlah", border=1, ln=False, align="C")
    pdf.cell(40, 8, text="Subtotal", border=1, ln=True, align="C")
    
    pdf.set_font("Arial", size=11)
    for item in items:
        subtotal = item["harga"] * item["jumlah"]
        pdf.cell(90, 8, text=str(item["nama"]), border=1, ln=False)
        pdf.cell(35, 8, text=f"Rp {item['harga']:,}", border=1, ln=False, align="R")
        pdf.cell(25, 8, text=str(item["jumlah"]), border=1, ln=False, align="C")
        pdf.cell(40, 8, text=f"Rp {subtotal:,}", border=1, ln=True, align="R")
        
    pdf.set_font("Arial", "B", 11)
    pdf.cell(150, 10, text="TOTAL PEMBAYARAN : ", border=1, ln=False, align="R")
    pdf.cell(40, 10, text=f"Rp {int(total_bayar):,}", border=1, ln=True, align="R")
    pdf.ln(15)
    
    pdf.set_font("Arial", "I", 10)
    pdf.cell(190, 5, text="Terima kasih telah berbelanja di Toko Online Sinar!", ln=True, align="C")
    pdf.cell(190, 5, text="Nota ini sah dan dihasilkan secara otomatis oleh sistem.", ln=True, align="C")
    
    return pdf.output()

# ==============================================================================
# FUNGSI PROSES DAN KOMPRES FOTO PRODUK
# ==============================================================================
def proses_dan_simpan_foto(file_diunggah, nama_produk):
    """
    Fungsi otomatis untuk memotong (crop) tengah dan mengecilkan (resize)
    foto produk menjadi ukuran kotak 500x500 pixel agar hemat ruang storage.
    """
    if not os.path.exists("assets"):
        os.makedirs("assets")
        
    nama_file_aman = "".join(x for x in nama_produk.lower() if x.isalnum() or x in [" ", "_", "-"]).replace(" ", "_")
    jalur_simpan = f"assets/{nama_file_aman}.jpg"
    
    with Image.open(file_diunggah) as img:
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        lebar, tinggi = img.size
        ukuran_terkecil = min(lebar, tinggi)
        left = (lebar - ukuran_terkecil) / 2
        top = (tinggi - ukuran_terkecil) / 2
        right = (lebar + ukuran_terkecil) / 2
        bottom = (tinggi + ukuran_terkecil) / 2
        img_cropped = img.crop((left, top, right, bottom))
        
        img_resized = img_cropped.resize((500, 500), Image.Resampling.LANCZOS)
        img_resized.save(jalur_simpan, "JPEG", quality=85)
        
    return jalur_simpan
# ==============================================================================
# FUNGSI LIVE CHAT LOKAL (CUSTOMER & ADMIN)
# ==============================================================================
def ambil_chat_antara(user_a, user_b):
    """Mengambil riwayat chat antara dua pengguna secara berurutan waktu"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT pengirim, penerima, teks, tanggal 
        FROM pesan_chat 
        WHERE (pengirim = ? AND penerima = ?) OR (pengirim = ? AND penerima = ?)
        ORDER BY id ASC
    """, (user_a, user_b, user_b, user_a))
    rows = cursor.fetchall()
    conn.close()
    return [{"pengirim": r[0], "penerima": r[1], "teks": r[2], "tanggal": r[3]} for r in rows]

def simpan_chat(pengirim, penerima, teks):
    """Menyimpan pesan chat baru ke database"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    waktu_sekarang = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO pesan_chat (pengirim, penerima, teks, tanggal) 
        VALUES (?, ?, ?, ?)
    """, (pengirim, penerima, teks, waktu_sekarang))
    conn.commit()
    conn.close()
