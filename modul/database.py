import streamlit as st  # 🌟 TAMBAHAN: Wajib di-import agar st.info bisa berjalan
import sqlite3
import json
from datetime import datetime

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
        st.info("Sistem mendeteksi pembaruan database, menyinkronkan kolom 'role'...")
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
    conn.commit()
    
    # 🌟 KEAJAIBAN DI SINI: Impor ditaruh di dalam agar tidak memicu Circular Import
    cursor.execute("SELECT username FROM pengguna WHERE username = 'admin'")
    if not cursor.fetchone():
        from modul.keamanan import hash_password # 👈 Pindah ke sini, aman 100%!
        password_admin_hashed = hash_password("admin123")
        cursor.execute("""
            INSERT INTO pengguna (username, password, email, role) 
            VALUES ('admin', ?, 'admin@toko.com', 'admin')
        """, (password_admin_hashed,))
        conn.commit()
        
    conn.close()

# ==============================================================================
# FUNGSI KELOLA PENGGUNA (SINKRON DENGAN TABEL 'PENGGUNA')
# ==============================================================================
def load_users():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # PERBAIKAN: Diselaraskan menembak tabel 'pengguna', bukan 'users'
    cursor.execute("SELECT username, password, role FROM pengguna")
    rows = cursor.fetchall()
    conn.close()
    return {row[0]: {"password": row[1], "role": row[2]} for row in rows}

def save_users(users_dict):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    for username, data in users_dict.items():
        # PERBAIKAN: Diselaraskan memasukkan data ke tabel 'pengguna', bukan 'users'
        cursor.execute("INSERT OR REPLACE INTO pengguna (username, password, role) VALUES (?, ?, ?)", 
                       (username, data["password"], data["role"]))
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
