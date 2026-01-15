import streamlit as st
import pandas as pd
import requests
import os
from PIL import Image
from pyzbar.pyzbar import decode

# Konfigurasi Tampilan
st.set_page_config(page_title="My Library Clone", page_icon="📚", layout="centered")

DATA_FILE = "books_data.csv"

# Fungsi Database Sederhana
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=["ID", "Judul", "Penulis", "Cover", "Status"])

def save_to_db(book_id, title, author, cover):
    df = load_data()
    if book_id not in df['ID'].values:
        new_row = pd.DataFrame([[book_id, title, author, cover, "Belum Dibaca"]], 
                             columns=["ID", "Judul", "Penulis", "Cover", "Status"])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(DATA_FILE, index=False)
        return True
    return False

# Fungsi Cari Buku lewat Google Books
def get_book_details(query, is_isbn=False):
    prefix = "isbn:" if is_isbn else ""
    url = f"https://www.googleapis.com/books/v1/volumes?q={prefix}{query}"
    res = requests.get(url).json()
    if 'items' in res:
        info = res['items'][0]['volumeInfo']
        return {
            "id": res['items'][0]['id'],
            "title": info.get('title', 'Tanpa Judul'),
            "author": ", ".join(info.get('authors', ['Anonim'])),
            "cover": info.get('imageLinks', {}).get('thumbnail', 'https://via.placeholder.com/150')
        }
    return None

# ANTARMUKA APLIKASI (UI)
st.title("📚 My Library")

tab1, tab2 = st.tabs(["🏠 Koleksi Saya", "➕ Tambah Buku"])

with tab1:
    df = load_data()
    if df.empty:
        st.info("Koleksi kosong. Klik tab 'Tambah Buku' untuk memulai!")
    else:
        search = st.text_input("Cari di koleksi...")
        filtered_df = df[df['Judul'].str.contains(search, case=False)]
        
        for idx, row in filtered_df.iterrows():
            with st.container():
                c1, c2 = st.columns([1, 3])
                c1.image(row['Cover'])
                c2.subheader(row['Judul'])
                c2.write(f"Penulis: {row['Penulis']}")
                status = c2.selectbox("Status", ["Belum Dibaca", "Sedang Dibaca", "Selesai"], key=f"stat_{row['ID']}")
                if c2.button("Hapus", key=f"del_{row['ID']}"):
                    df.drop(idx).to_csv(DATA_FILE, index=False)
                    st.rerun()
                st.divider()

with tab2:
    st.subheader("Gunakan Kamera untuk Scan Barcode (ISBN)")
    img_file = st.camera_input("Scan Barcode")
    
    if img_file:
        barcodes = decode(Image.open(img_file))
        if barcodes:
            isbn = barcodes[0].data.decode('utf-8')
            st.success(f"Barcode ditemukan: {isbn}")
            book = get_book_details(isbn, is_isbn=True)
            if book:
                st.image(book['cover'], width=100)
                st.write(f"**{book['title']}** - {book['author']}")
                if st.button("Simpan ke Koleksi"):
                    if save_to_db(book['id'], book['title'], book['author'], book['cover']):
                        st.success("Tersimpan!")
                    else:
                        st.warning("Buku sudah ada.")
        else:
            st.warning("Barcode tidak terdeteksi, pastikan cahaya cukup.")

    st.divider()
    st.subheader("Atau Cari Manual")
    manual_search = st.text_input("Ketik Judul Buku...")
    if manual_search:
        book = get_book_details(manual_search)
        if book:
            st.image(book['cover'], width=100)
            st.write(f"**{book['title']}**")
            if st.button("Simpan Buku Ini"):
                save_to_db(book['id'], book['title'], book['author'], book['cover'])
                st.success("Berhasil disimpan!")
