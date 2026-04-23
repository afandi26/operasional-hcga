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

menu = ["Input Tim (Multi-Item)", "Dashboard Manager", "Ekspor Data"]
choice = st.sidebar.selectbox("Menu", menu)
df = load_data()

if choice == "Input Tim (Multi-Item)":
    st.subheader("📝 Form Pengeluaran Bertahap")
    with st.expander("Langkah 1: Input Modal dari Manager", expanded=True):
        pic = st.selectbox("Nama Tim", ["Tim A", "Tim B"])
        dana_modal = st.number_input("Total Dana yang Diterima (Modal Awal)", min_value=0, step=1000)

    st.write("---")
    st.write("### Langkah 2: Input Daftar Belanja")
    if 'items_list' not in st.session_state:
        st.session_state.items_list = []

    with st.form("tambah_item_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        item_nama = col1.text_input("Nama Barang")
        item_harga = col2.number_input("Harga di Nota", min_value=0, step=500)
        if st.form_submit_button("➕ Tambah ke Daftar"):
            if item_nama:
                st.session_state.items_list.append({"Barang": item_nama, "Harga": item_harga})
                st.rerun()

    if len(st.session_state.items_list) > 0:
        st.write("#### Daftar Belanja Saat Ini:")
        h1, h2, h3 = st.columns([3, 2, 1])
        h1.write("**Nama Barang**")
        h2.write("**Harga**")
        h3.write("**Aksi**")
        
        total_terpakai = 0
        for index, item in enumerate(st.session_state.items_list):
            c1, c2, c3 = st.columns([3, 2, 1])
            c1.write(item["Barang"])
            c2.write(f"Rp{item['Harga']:,}")
            total_terpakai += item["Harga"]
            if c3.button("🗑️ Hapus", key=f"del_{index}"):
                st.session_state.items_list.pop(index)
                st.rerun()
        
        st.write("---")
        sisa_sekarang = dana_modal - total_terpakai
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("Total Belanja", f"Rp{total_terpakai:,}")
        col_m2.metric("Sisa Saldo Uang", f"Rp{sisa_sekarang:,}")

        if st.button("🚀 Kirim Laporan ke Manager", use_container_width=True):
            semua_barang = ", ".join([i["Barang"] for i in st.session_state.items_list])
            new_row = {
                "Tanggal": datetime.now().strftime("%Y-%m-%d"),
                "PIC": pic, "Keperluan": semua_barang, "Dana_Awal": dana_modal,
                "Total_Belanja": total_terpakai, "Sisa": sisa_sekarang, "Status": "Pending"
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_csv(DB_FILE, index=False)
            st.session_state.items_list = []
            st.success("Terkirim!")
            st.rerun()

elif choice == "Dashboard Manager":
    st.subheader("🕵️ Dashboard Verifikasi")
    
    if not df.empty:
        # Menampilkan tabel dengan kontrol per baris
        for index, row in df.iterrows():
            # Hanya tampilkan yang masih Pending
            if row["Status"] == "Pending":
                with st.container():
                    st.write(f"**Tanggal:** {row['Tanggal']} | **PIC:** {row['PIC']}")
                    st.write(f"**Barang:** {row['Keperluan']}")
                    col_a, col_b, col_c, col_d = st.columns(4)
                    col_a.write(f"Modal: Rp{row['Dana_Awal']:,}")
                    col_b.write(f"Belanja: Rp{row['Total_Belanja']:,}")
                    col_c.write(f"Sisa: Rp{row['Sisa']:,}")
                    
                    # Tombol Approve dan Reject
                    btn_col1, btn_col2 = st.columns([1, 4])
                    if btn_col1.button("✅ Approve", key=f"app_{index}"):
                        df.at[index, "Status"] = "Approved"
                        df.to_csv(DB_FILE, index=False)
                        st.success(f"Laporan {row['PIC']} Disetujui!")
                        st.rerun()
                    
                    if btn_col2.button("❌ Tolak (Hapus)", key=f"rej_{index}"):
                        df.drop(index, inplace=True)
                        df.to_csv(DB_FILE, index=False)
                        st.warning(f"Laporan {row['PIC']} Ditolak & Dihapus!")
                        st.rerun()
                st.write("---")
        
        # Tampilkan data yang sudah Approved di bagian bawah
        with st.expander("Lihat Riwayat Approved"):
            st.dataframe(df[df["Status"] == "Approved"], use_container_width=True)
    else:
        st.info("Belum ada data.")

elif choice == "Ekspor Data":
    st.subheader("📊 Ekspor")
    if not df.empty:
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Laporan CSV", csv, "laporan_hcga.csv", "text/csv")
