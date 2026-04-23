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
    return pd.DataFrame(columns=["Tanggal", "PIC", "Keperluan", "Dana_Awal", "Harga_Satuan", "Status"])

st.set_page_config(page_title="HC-GA Operasional", layout="wide")
st.title("💰 Sistem Pengeluaran HC & GA")

menu = ["Input Tim (Multi-Item)", "Dashboard Manager", "Ekspor Data"]
choice = st.sidebar.selectbox("Menu", menu)
df = load_data()

if choice == "Input Tim (Multi-Item)":
    st.subheader("📝 Form Pengeluaran Bertahap")
    
    pic = st.selectbox("Nama Tim", ["Tim A", "Tim B"])
    dana_modal = st.number_input("Total Dana yang Diterima dari Manager (Rp)", min_value=0, step=1000, key="modal_input")

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
            if dana_modal <= 0:
                st.error("Gagal! Anda belum mengisi 'Total Dana yang Diterima'.")
            else:
                # PERBAIKAN: Simpan setiap barang sebagai baris baru
                new_rows = []
                for i in st.session_state.items_list:
                    new_rows.append({
                        "Tanggal": datetime.now().strftime("%Y-%m-%d"),
                        "PIC": pic, 
                        "Keperluan": i["Barang"], 
                        "Dana_Awal": dana_modal,
                        "Harga_Satuan": i["Harga"], 
                        "Status": "Pending"
                    })
                
                df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
                df.to_csv(DB_FILE, index=False)
                st.session_state.items_list = []
                st.success("Laporan Terinci Berhasil Terkirim!")
                st.rerun()

elif choice == "Dashboard Manager":
    st.subheader("🕵️ Dashboard Verifikasi")
    if not df.empty:
        # Menampilkan barang yang butuh approval (dikelompokkan per PIC & Tanggal agar tidak berantakan)
        pending_items = df[df["Status"] == "Pending"]
        
        if not pending_items.empty:
            for pic_name in pending_items["PIC"].unique():
                st.write(f"### Laporan dari {pic_name}")
                pic_df = pending_items[pending_items["PIC"] == pic_name]
                
                # Tampilkan tabel ringkas untuk yang sedang di-review
                st.table(pic_df[["Keperluan", "Harga_Satuan"]])
                
                total_pic = pic_df["Harga_Satuan"].sum()
                modal_pic = pic_df["Dana_Awal"].iloc[0]
                st.write(f"**Total Belanja:** Rp{total_pic:,} | **Modal:** Rp{modal_pic:,} | **Sisa:** Rp{modal_pic - total_pic:,}")
                
                b1, b2 = st.columns([1, 5])
                if b1.button(f"✅ Approve Semua dari {pic_name}", key=f"app_{pic_name}"):
                    df.loc[(df["PIC"] == pic_name) & (df["Status"] == "Pending"), "Status"] = "Approved"
                    df.to_csv(DB_FILE, index=False)
                    st.rerun()
                if b2.button(f"❌ Tolak (Hapus) Laporan {pic_name}", key=f"rej_{pic_name}"):
                    df.drop(df[(df["PIC"] == pic_name) & (df["Status"] == "Pending")].index, inplace=True)
                    df.to_csv(DB_FILE, index=False)
                    st.rerun()
                st.write("---")
        else:
            st.info("Tidak ada laporan baru.")

        with st.expander("Lihat Riwayat Approved (Rincian per Item)"):
            approved_df = df[df["Status"] == "Approved"].copy()
            if not approved_df.empty:
                # Tampilkan rincian per item
                st.dataframe(approved_df[["Tanggal", "PIC", "Keperluan", "Harga_Satuan"]], use_container_width=True)
                st.write(f"**Total Pengeluaran Keseluruhan:** Rp{approved_df['Harga_Satuan'].sum():,}")
            else:
                st.write("Belum ada riwayat.")
    else:
        st.info("Belum ada data.")

elif choice == "Ekspor Data":
    st.subheader("📊 Ekspor")
    if not df.empty:
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Laporan Rinci (CSV)", csv, "laporan_rinci_hcga.csv", "text/csv")
