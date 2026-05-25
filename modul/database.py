import sqlite3
import json
from datetime import datetime
from modul.keamanan import hash_password

DB_NAME = "toko_online.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY, password TEXT NOT NULL, role TEXT NOT NULL
    )""")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS produk (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT NOT NULL UNIQUE,
        harga INTEGER NOT NULL, stok INTEGER NOT NULL, foto TEXT
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transaksi (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL,
        tanggal TEXT NOT NULL, items TEXT NOT NULL, total_bayar INTEGER NOT NULL,
        bukti_transfer TEXT, status TEXT DEFAULT 'Belum Bayar'
    )""")
    
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO users VALUES (?, ?, ?)", ("admin", hash_password("123"), "admin"))
        
    cursor.execute("SELECT COUNT(*) FROM produk")
    if cursor.fetchone()[0] == 0:
        produk_default = [("Kaos", 50000, 10, None), ("Celana", 100000, 5, None), ("Sepatu", 250000, 3, None)]
        cursor.executemany("INSERT INTO produk (nama, harga, stok, foto) VALUES (?, ?, ?, ?)", produk_default)
        
    conn.commit()
    conn.close()

def load_users():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT username, password, role FROM users")
    rows = cursor.fetchall()
    conn.close()
    return {row[0]: {"password": row[1], "role": row[2]} for row in rows}

def save_users(users_dict):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    for username, data in users_dict.items():
        cursor.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?)", (username, data["password"], data["role"]))
    conn.commit()
    conn.close()

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
        cursor.execute("INSERT OR REPLACE INTO produk (nama, harga, stok, foto) VALUES (?, ?, ?, ?)", (p["nama"], p["harga"], p["stok"], p["foto"]))
    conn.commit()
    conn.close()

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