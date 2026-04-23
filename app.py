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
    dana_modal = st.number_input("Total Dana yang Diterima (Rp)", min_value=0, step=1000, key="modal_input")

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

    if st.session_state.items_list:
        st.write("#### Daftar Belanja Saat Ini:")
        total_terpakai = 0
        for index, item in enumerate(st.session_state.items_list):
            c1, c2, c3 = st.columns([3, 2, 1])
            c1.write(item["Barang"])
            c2.write(f"Rp{item['Harga']:,}")
            total_terpakai += item["Harga"]
            if c3.button("🗑️ Hapus", key=f"del_input_{index}"):
                st.session_state.items_list.pop(index)
                st.rerun()
        
        st.write("---")
        sisa_sekarang = dana_modal - total_terpakai
        st.metric("Total Belanja", f"Rp{total_terpakai:,}")
        st.metric("Sisa Saldo Uang", f"Rp{sisa_sekarang:,}")

        if st.button("🚀 Kirim Laporan ke Manager", use_container_width=True):
            if dana_modal <= 0:
                st.error("Gagal! Isi Modal terlebih dahulu.")
            else:
                new_rows = []
                for i in st.session_state.items_list:
                    new_rows.append({
                        "Tanggal": datetime.now().strftime("%Y-%m-%d"),
                        "PIC": pic, "Keperluan": i["Barang"], "Dana_Awal": dana_modal,
                        "Harga_Satuan": i["Harga"], "Status": "Pending"
                    })
                df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
                df.to_csv(DB_FILE, index=False)
                st.session_state.items_list = []
                st.success("Laporan Terkirim!")
                st.rerun()

elif choice == "Dashboard Manager":
    st.subheader("🕵️ Dashboard Verifikasi & Edit")
    
    # 1. Bagian Approval (Pending)
    pending_df = df[df["Status"] == "Pending"]
    if not pending_df.empty:
        for pic_name in pending_df["PIC"].unique():
            with st.expander(f"🔴 LAPORAN BARU: {pic_name}", expanded=True):
                pic_pending = pending_df[pending_df["PIC"] == pic_name]
                st.table(pic_pending[["Keperluan", "Harga_Satuan"]])
                if st.button(f"✅ Approve Laporan {pic_name}", key=f"app_{pic_name}"):
                    df.loc[(df["PIC"] == pic_name) & (df["Status"] == "Pending"), "Status"] = "Approved"
                    df.to_csv(DB_FILE, index=False)
                    st.rerun()
    
    st.write("---")
    
    # 2. Bagian Riwayat Terpisah per Tim (Pertanggungjawaban Masing-masing)
    st.subheader("📋 Pertanggungjawaban per Tim (Approved)")
    approved_all = df[df["Status"] == "Approved"]
    
    if not approved_all.empty:
        tabs = st.tabs(list(approved_all["PIC"].unique()))
        
        for i, pic_name in enumerate(approved_all["PIC"].unique()):
            with tabs[i]:
                pic_data = approved_all[approved_all["PIC"] == pic_name].copy()
                
                # Fitur Edit/Hapus Per Baris
                for idx, row in pic_data.iterrows():
                    with st.container():
                        c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
                        new_name = c1.text_input("Barang", row["Keperluan"], key=f"edit_n_{idx}")
                        new_price = c2.number_input("Harga", value=int(row["Harga_Satuan"]), key=f"edit_p_{idx}")
                        
                        if c3.button("💾 Simpan", key=f"save_{idx}"):
                            df.at[idx, "Keperluan"] = new_name
                            df.at[idx, "Harga_Satuan"] = new_price
                            df.to_csv(DB_FILE, index=False)
                            st.rerun()
                            
                        if c4.button("🗑️ Hapus", key=f"del_final_{idx}"):
                            df.drop(idx, inplace=True)
                            df.to_csv(DB_FILE, index=False)
                            st.rerun()
                
                st.write("---")
                # Ringkasan per Tim
                t_modal = pic_data.groupby('Tanggal')['Dana_Awal'].first().sum()
                t_belanja = pic_data['Harga_Satuan'].sum()
                
                m1, m2, m3 = st.columns(3)
                m1.metric(f"Total Modal {pic_name}", f"Rp{t_modal:,}")
                m2.metric(f"Total Belanja {pic_name}", f"Rp{t_belanja:,}")
                m3.metric(f"Sisa Saldo {pic_name}", f"Rp{t_modal - t_belanja:,}")
    else:
        st.info("Belum ada data yang disetujui.")

elif choice == "Ekspor Data":
    st.subheader("📊 Ekspor")
    if not df.empty:
        st.download_button("Download CSV", df.to_csv(index=False).encode('utf-8'), "laporan_hcga.csv", "text/csv")
