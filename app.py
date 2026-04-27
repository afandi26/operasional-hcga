import streamlit as st
import pandas as pd
from datetime import datetime
import os

# 1. KONFIGURASI DATABASE
DB_FILE = "data_pengeluaran.csv"

def load_data():
    if os.path.exists(DB_FILE):
        try:
            df_load = pd.read_csv(DB_FILE)
            cols = ["Tanggal", "PIC", "Keperluan", "Dana_Awal", "Harga_Satuan", "Status"]
            for col in cols:
                if col not in df_load.columns:
                    df_load[col] = None
            return df_load
        except:
            pass
    return pd.DataFrame(columns=["Tanggal", "PIC", "Keperluan", "Dana_Awal", "Harga_Satuan", "Status"])

# 2. SETTING HALAMAN
st.set_page_config(page_title="HC-GA Operasional", layout="wide")
st.title("💰 Sistem Pengeluaran HC & GA")

df = load_data()

# 3. SIDEBAR MENU (Hanya Satu Kali Saja)
menu = ["Dashboard Manager", "Input Tim (Kirim Laporan)", "Lihat Saldo Tim"]
choice = st.sidebar.selectbox("Menu Utama", menu)

# --- MENU 1: DASHBOARD MANAGER (Input Modal & Approval) ---
if choice == "Dashboard Manager":
    st.subheader("🕵️ Dashboard Manager")
    
    # FITUR: INPUT MODAL UNTUK TIM (Penambah Saldo)
    with st.expander("💰 Input Pemberian Modal Baru (Uang Keluar dari Manager)", expanded=False):
        c1, c2 = st.columns(2)
        target_tim = c1.selectbox("Berikan Modal Ke:", ["Tim A", "Tim B"], key="target_modal")
        jumlah_modal = c2.number_input("Jumlah Modal (Rp)", min_value=0, step=50000)
        if st.button("Kirim Modal"):
            new_modal = pd.DataFrame([{
                "Tanggal": datetime.now().strftime("%Y-%m-%d"),
                "PIC": target_tim, 
                "Keperluan": "MODAL AWAL", 
                "Dana_Awal": jumlah_modal, 
                "Harga_Satuan": 0, 
                "Status": "Approved"
            }])
            df = pd.concat([df, new_modal], ignore_index=True)
            df.to_csv(DB_FILE, index=False)
            st.success(f"Berhasil menginput modal Rp{jumlah_modal:,} untuk {target_tim}")
            st.rerun()

    st.write("---")
    
    # FITUR: APPROVAL LAPORAN BARU
    pending_df = df[df["Status"] == "Pending"]
    if not pending_df.empty:
        st.subheader("📩 Laporan Perlu Verifikasi")
        for pic_name in pending_df["PIC"].unique():
            with st.expander(f"🔴 LAPORAN DARI: {pic_name}", expanded=True):
                pic_p = pending_df[pending_df["PIC"] == pic_name]
                st.table(pic_p[["Tanggal", "Keperluan", "Harga_Satuan"]])
                if st.button(f"✅ Approve Semua Laporan {pic_name}", key=f"app_{pic_name}"):
                    df.loc[(df["PIC"] == pic_name) & (df["Status"] == "Pending"), "Status"] = "Approved"
                    df.to_csv(DB_FILE, index=False)
                    st.rerun()
    else:
        st.info("Tidak ada laporan baru yang perlu dicek.")

# --- MENU 2: INPUT TIM (Kirim Daftar Belanja) ---
elif choice == "Input Tim (Kirim Laporan)":
    st.subheader("📝 Form Laporan Pengeluaran Tim")
    pic = st.selectbox("Pilih Nama Tim Anda", ["Tim A", "Tim B"])
    
    if 'items_list' not in st.session_state:
        st.session_state.items_list = []

    with st.form("form_tambah"):
        c1, c2 = st.columns(2)
        item_nama = c1.text_input("Nama Barang/Keperluan")
        item_harga = c2.number_input("Harga Sesuai Nota (Rp)", min_value=0)
        submit = st.form_submit_button("➕ Tambahkan ke Daftar")
        if submit and item_nama:
            st.session_state.items_list.append({"Barang": item_nama, "Harga": item_harga})
            st.rerun()

    if st.session_state.items_list:
        st.write("### Daftar Belanja Sementara:")
        total_skrg = 0
        for i, itm in enumerate(st.session_state.items_list):
            st.write(f"{i+1}. {itm['Barang']} - Rp{itm['Harga']:,}")
            total_skrg += itm['Harga']
        
        st.metric("Total Belanja Ini", f"Rp{total_skrg:,}")
        
        if st.button("🚀 Kirim Semua ke Manager"):
            new_rows = []
            for itm in st.session_state.items_list:
                new_rows.append({
                    "Tanggal": datetime.now().strftime("%Y-%m-%d"),
                    "PIC": pic, 
                    "Keperluan": itm["Barang"], 
                    "Dana_Awal": 0, # Belanja tidak menambah modal
                    "Harga_Satuan": itm["Harga"], 
                    "Status": "Pending"
                })
            df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
            df.to_csv(DB_FILE, index=False)
            st.session_state.items_list = []
            st.success("Laporan berhasil dikirim ke Manager!")
            st.rerun()

# --- MENU 3: LIHAT SALDO (Sinkronisasi Manager & Tim) ---
elif choice == "Lihat Saldo Tim":
    st.subheader("📊 Cek Saldo Real-time")
    pic = st.selectbox("Pilih Tim", ["Tim A", "Tim B"], key="cek_saldo")
    
    pic_data = df[df["PIC"] == pic]
    
    # Hitung Modal Awal dari Manager
    total_modal = pic_data[pic_data["Keperluan"] == "MODAL AWAL"]["Dana_Awal"].sum()
    # Hitung Semua yang sudah disetujui
    total_belanja = pic_data[pic_data["Status"] == "Approved"]["Harga_Satuan"].sum()
    saldo = total_modal - total_belanja

    if total_modal == 0:
        st.error(f"⚠️ Manager belum menginput Modal Awal untuk {pic}.")
    else:
        st.success(f"✅ Saldo Tersisa: **Rp{saldo:,}**")
        
        col1, col2 = st.columns(2)
        col1.metric("Total Modal Diberikan", f"Rp{total_modal:,}")
        col2.metric("Total Penggunaan (Approved)", f"Rp{total_belanja:,}")
        
    st.write("---")
    st.write("### Riwayat Transaksi Anda:")
    st.dataframe(pic_data[["Tanggal", "Keperluan", "Harga_Satuan", "Status"]])
