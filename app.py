import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Database file
DB_FILE = "data_pengeluaran.csv"

def load_data():
    if os.path.exists(DB_FILE):
        try:
            return pd.read_csv(DB_FILE)
        except:
            pass
    return pd.DataFrame(columns=["Tanggal", "PIC", "Keperluan", "Dana_Awal", "Total_Belanja", "Sisa", "Status"])

st.set_page_config(page_title="HC-GA Operasional", layout="wide")
st.title("💰 Sistem Pengeluaran HC & GA")

# Menu Sidebar
menu = ["Input Tim (Multi-Item)", "Dashboard Manager", "Ekspor Data"]
choice = st.sidebar.selectbox("Menu", menu)
df = load_data()

if choice == "Input Tim (Multi-Item)":
    st.subheader("📝 Form Pengeluaran Bertahap")
    
    # Input modal awal
    with st.expander("Langkah 1: Input Modal dari Manager", expanded=True):
        pic = st.selectbox("Nama Tim", ["Tim A", "Tim B"])
        dana_modal = st.number_input("Total Dana yang Diterima (Modal Awal)", min_value=0, step=1000)

    st.write("---")
    st.write("### Langkah 2: Input Daftar Belanja")
    
    # Inisialisasi daftar belanja di session state jika belum ada
    if 'items_list' not in st.session_state:
        st.session_state.items_list = []

    # Form untuk tambah barang (supaya tidak refresh setiap ngetik)
    with st.form("tambah_item_form"):
        col1, col2 = st.columns(2)
        item_nama = col1.text_input("Nama Barang")
        item_harga = col2.number_input("Harga di Nota", min_value=0, step=500)
        tambah_klik = st.form_submit_button("➕ Tambah ke Daftar Belanja")
        
        if tambah_klik:
            if item_nama:
                st.session_state.items_list.append({"Barang": item_nama, "Harga": item_harga})
                st.success(f"Berhasil menambah: {item_nama}")
            else:
                st.warning("Nama barang tidak boleh kosong!")

    # Tampilkan daftar dan tombol kirim HANYA jika ada barang
    if len(st.session_state.items_list) > 0:
        st.write("#### Daftar Belanja Saat Ini:")
        temp_df = pd.DataFrame(st.session_state.items_list)
        st.table(temp_df)
        
        total_terpakai = temp_df["Harga"].sum()
        sisa_sekarang = dana_modal - total_terpakai
        
        c1, c2 = st.columns(2)
        c1.metric("Total Belanja", f"Rp{total_terpakai:,}")
        c2.metric("Sisa Saldo Uang", f"Rp{sisa_sekarang:,}")

        if st.button("🚀 Kirim Semua Laporan ke Manager"):
            semua_barang = ", ".join([i["Barang"] for i in st.session_state.items_list])
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
            
            # Reset data setelah kirim
            st.session_state.items_list = []
            st.success("Laporan Global Berhasil Terkirim!")
            st.balloons()
            st.rerun()
            
    if st.button("🗑️ Kosongkan Daftar Belanja"):
        st.session_state.items_list = []
        st.rerun()

elif choice == "Dashboard Manager":
    st.subheader("🕵️ Dashboard Verifikasi")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        if st.button("Approve Semua"):
            df["Status"] = "Approved"
            df.to_csv(DB_FILE, index=False)
            st.success("Data diverifikasi!")
            st.rerun()
    else:
        st.info("Belum ada data masuk.")

elif choice == "Ekspor Data":
    st.subheader("📊 Ekspor")
    if not df.empty:
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Laporan CSV", csv, "laporan_hcga.csv", "text/csv")
    else:
        st.info("Tidak ada data untuk diunduh.")
