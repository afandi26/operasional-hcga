import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Database file
DB_FILE = "data_pengeluaran.csv"

def load_data():
    if os.path.exists(DB_FILE):
        try:
            df_load = pd.read_csv(DB_FILE)
            if 'Total_Belanja' in df_load.columns and 'Harga_Satuan' not in df_load.columns:
                df_load = df_load.rename(columns={'Total_Belanja': 'Harga_Satuan'})
            for col in ["Tanggal", "PIC", "Keperluan", "Dana_Awal", "Harga_Satuan", "Status"]:
                if col not in df_load.columns:
                    df_load[col] = None
            return df_load
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
    
    # 1. Approval (Pending) dengan Rincian Dana
    pending_df = df[df["Status"] == "Pending"]
    if not pending_df.empty:
        for pic_name in pending_df["PIC"].unique():
            with st.expander(f"🔴 LAPORAN BARU: {pic_name}", expanded=True):
                pic_p = pending_df[pending_df["PIC"] == pic_name]
                
                # Tabel Rincian Barang
                st.table(pic_p[["Keperluan", "Harga_Satuan"]])
                
                # PERBAIKAN: Menampilkan Rincian Dana Sebelum Approve
                t_modal_p = pic_p["Dana_Awal"].iloc[0] if not pic_p.empty else 0
                t_belanja_p = pic_p["Harga_Satuan"].sum()
                t_sisa_p = t_modal_p - t_belanja_p
                
                c_p1, c_p2, c_p3 = st.columns(3)
                c_p1.metric("Modal Diterima Tim", f"Rp{t_modal_p:,}")
                c_p2.metric("Total Belanja Laporan Ini", f"Rp{t_belanja_p:,}")
                c_p3.metric("Sisa Saldo di Tim", f"Rp{t_sisa_p:,}")
                
                if st.button(f"✅ Approve Laporan {pic_name}", key=f"app_{pic_name}"):
                    df.loc[(df["PIC"] == pic_name) & (df["Status"] == "Pending"), "Status"] = "Approved"
                    df.to_csv(DB_FILE, index=False)
                    st.rerun()
    else:
        st.info("Tidak ada laporan baru.")
    
    st.write("---")
    
    # 2. Pertanggungjawaban per Tim (Approved)
    approved_all = df[df["Status"] == "Approved"]
    if not approved_all.empty:
        st.subheader("📋 Pertanggungjawaban per Tim (Approved)")
        unique_pics = sorted(approved_all["PIC"].unique())
        tabs = st.tabs(list(unique_pics))
        
        for i, pic_name in enumerate(unique_pics):
            with tabs[i]:
                pic_data = approved_all[approved_all["PIC"] == pic_name].copy()
                
                h1, h2, h3, h4 = st.columns([3, 2, 1, 1])
                h1.write("**Barang**")
                h2.write("**Harga**")
                h3.write("**Simpan**")
                h4.write("**Hapus**")

                for idx, row in pic_data.iterrows():
                    curr_val = int(row["Harga_Satuan"]) if pd.notnull(row["Harga_Satuan"]) else 0
                    with st.container():
                        c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
                        new_name = c1.text_input("Edit Nama", row["Keperluan"], key=f"n_{idx}", label_visibility="collapsed")
                        new_price = c2.number_input("Edit Harga", value=curr_val, key=f"p_{idx}", label_visibility="collapsed")
                        
                        if c3.button("💾", key=f"s_{idx}"):
                            df.at[idx, "Keperluan"] = new_name
                            df.at[idx, "Harga_Satuan"] = new_price
                            df.to_csv(DB_FILE, index=False)
                            st.rerun()
                            
                        if c4.button("🗑️", key=f"d_{idx}"):
                            df.drop(idx, inplace=True)
                            df.to_csv(DB_FILE, index=False)
                            st.rerun()
                
                st.write("---")
                # Perhitungan total modal unik berdasarkan Tanggal dan PIC agar tidak double count
                t_modal = pic_data.groupby('Tanggal')['Dana_Awal'].first().sum()
                t_belanja = pic_data['Harga_Satuan'].sum()
                
                m1, m2, m3 = st.columns(3)
                m1.metric("Total Modal", f"Rp{t_modal:,}")
                m2.metric("Total Belanja", f"Rp{t_belanja:,}")
                m3.metric("Sisa Saldo", f"Rp{t_modal - t_belanja:,}")
