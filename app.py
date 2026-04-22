import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Database file
DB_FILE = "data_pengeluaran.csv"

def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["Tanggal", "PIC", "Keperluan", "Dana_Awal", "Total_Belanja", "Sisa", "Status"])

st.set_page_config(page_title="HC-GA Operasional", layout="wide")
st.title("💰 Sistem Pengeluaran HC & GA")

# Menu Sidebar
menu = ["Input Tim (Multi-Item)", "Dashboard Manager", "Ekspor Data"]
choice = st.sidebar.selectbox("Menu", menu)
df = load_data()

if choice == "Input Tim (Multi-Item)":
    st.subheader("📝 Form Pengeluaran Bertahap")
    
    # Input modal awal hanya sekali
    with st.expander("Langkah 1: Input Modal dari Manager", expanded=True):
        pic = st.selectbox("Nama Tim", ["Tim A", "Tim B"])
        dana_modal = st.number_input("Total Dana yang Diterima (Modal Awal)", min_value=0, step=1000)

    # Input daftar belanjaan
    st.write("---")
    st.write("### Langkah 2: Input Daftar Belanja")
    
    # Menggunakan session state agar data belanja sementara tidak hilang saat tambah baris
    if 'items' not in st.session_state:
        st.session_state.items = []

    with st.form("tambah_barang"):
        col1, col2 = st.columns(2)
        item_nama = col1.text_input("Nama Barang")
        item_harga = col2.number_input("Harga di Nota", min_value=0, step=500)
        tambah = st.form_submit_button("➕ Tambah ke Daftar Belanja")
        
        if tambah and item_nama:
            st.session_state.items.append({"Barang": item_nama, "Harga": item_harga})

    # Tampilkan daftar belanja sementara
    if st.session_state.items:
        st.write("#### Daftar Belanja Saat Ini:")
        temp_df = pd.DataFrame(st.session_state.items)
        st.table(temp_df)
        
        total_terpakai = temp_df["Harga"].sum()
        sisa_sekarang = dana_modal - total_terpakai
        
        st.metric("Total Belanja", f"Rp{total_terpakai:,}")
        st.metric("Sisa Saldo Uang", f"Rp{sisa_sekarang:,}")

        if st.button("🚀 Kirim Semua Laporan"):
            # Gabungkan semua barang jadi satu baris deskripsi untuk laporan global
            semua_barang = ", ".join([i["Barang"] for i in st.session_state.items])
            new_row = {
                "Tanggal": datetime.now().strftime("%Y-%m-%d"),
                "PIC": pic,
                "Keperluan": semua_barang,
                "Dana_Awal": dana_modal,
                "Total_Belanja": total_terpakai,
                "Sisa": sisa_sekarang,
                "Status": "Pending"
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_csv(DB_FILE, index=False)
            st.session_state.items = [] # Kosongkan daftar belanja setelah kirim
            st.success("Berhasil dikirim ke Manager!")
            st.rerun()

elif choice == "Dashboard Manager":
    st.subheader("🕵️ Dashboard Verifikasi")
    st.dataframe(df, use_container_width=True)
    if st.button("Approve Semua"):
        df["Status"] = "Approved"
        df.to_csv(DB_FILE, index=False)
        st.rerun()

elif choice == "Ekspor Data":
    st.download_button("Download CSV untuk Accounting", df.to_csv(index=False), "laporan_operasional.csv", "text/csv")
