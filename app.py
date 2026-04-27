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
            # Pastikan kolom standar tersedia
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

# 3. SIDEBAR MENU
menu = ["Input Tim (Multi-Item)", "Dashboard Manager"]
choice = st.sidebar.selectbox("Menu Utama", menu)

# --- MENU 1: INPUT TIM ---
if choice == "Input Tim (Multi-Item)":
    st.subheader("📝 Form Pengeluaran Tim")
    pic = st.selectbox("Pilih Nama Tim", ["Tim A", "Tim B"])
    dana_modal = st.number_input("Total Dana yang Diterima (Rp)", min_value=0, step=50000)

    st.write("---")
    if 'items_list' not in st.session_state:
        st.session_state.items_list = []

    with st.form("form_tambah"):
        c1, c2 = st.columns(2)
        item_nama = c1.text_input("Nama Barang/Keperluan")
        item_harga = c2.number_input("Harga Sesuai Nota", min_value=0)
        submit = st.form_submit_button("➕ Tambahkan ke Daftar")
        if submit and item_nama:
            st.session_state.items_list.append({"Barang": item_nama, "Harga": item_harga})
            st.rerun()

    if st.session_state.items_list:
        total_skrg = 0
        for i, itm in enumerate(st.session_state.items_list):
            st.write(f"- {itm['Barang']}: Rp{itm['Harga']:,}")
            total_skrg += itm['Harga']
        
        st.metric("Total Belanja Sementara", f"Rp{total_skrg:,}")
        
        if st.button("🚀 Kirim Laporan ke Manager"):
            new_rows = []
            for itm in st.session_state.items_list:
                new_rows.append({
                    "Tanggal": datetime.now().strftime("%Y-%m-%d"),
                    "PIC": pic, "Keperluan": itm["Barang"], 
                    "Dana_Awal": dana_modal, "Harga_Satuan": itm["Harga"], "Status": "Pending"
                })
            df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
            df.to_csv(DB_FILE, index=False)
            st.session_state.items_list = []
            st.success("Berhasil dikirim!")
            st.rerun()

# --- MENU 2: DASHBOARD MANAGER (DENGAN GROUPING TANGGAL) ---
elif choice == "Dashboard Manager":
    st.subheader("🕵️ Dashboard Verifikasi & Edit")
    
    # Bagian 1: Approval (Pending)
    pending_df = df[df["Status"] == "Pending"]
    if not pending_df.empty:
        for pic_name in pending_df["PIC"].unique():
            with st.expander(f"🔴 LAPORAN BARU: {pic_name}", expanded=True):
                pic_p = pending_df[pending_df["PIC"] == pic_name]
                st.table(pic_p[["Tanggal", "Keperluan", "Harga_Satuan"]])
                
                t_modal_p = pic_p["Dana_Awal"].iloc[0]
                t_belanja_p = pic_p["Harga_Satuan"].sum()
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Modal Diterima", f"Rp{t_modal_p:,}")
                c2.metric("Total Belanja", f"Rp{t_belanja_p:,}")
                c3.metric("Sisa", f"Rp{t_modal_p - t_belanja_p:,}")
                
                if st.button(f"✅ Approve {pic_name}", key=f"app_{pic_name}"):
                    df.loc[(df["PIC"] == pic_name) & (df["Status"] == "Pending"), "Status"] = "Approved"
                    df.to_csv(DB_FILE, index=False)
                    st.rerun()
    else:
        st.info("Tidak ada laporan baru untuk diperiksa.")
    
    st.write("---")
    
    # Bagian 2: Riwayat Approved (DENGAN KELOMPOK TANGGAL)
    approved_all = df[df["Status"] == "Approved"]
    if not approved_all.empty:
        st.subheader("📋 Riwayat Pengeluaran (Approved)")
        pics = sorted(approved_all["PIC"].unique())
        tabs = st.tabs(pics)
        
        for i, pic_name in enumerate(pics):
            with tabs[i]:
                pic_data = approved_all[approved_all["PIC"] == pic_name].copy()
                available_dates = sorted(pic_data["Tanggal"].unique(), reverse=True)
                
                for tgl in available_dates:
                    # KELOMPOK PER TANGGAL
                    with st.expander(f"📅 Pengeluaran Tanggal: {tgl}", expanded=True):
                        daily_data = pic_data[pic_data["Tanggal"] == tgl]
                        
                        # Header
                        h1, h2, h3, h4 = st.columns([3, 2, 1, 1])
                        h1.write("**Barang**")
                        h2.write("**Harga**")
                        h3.write("**Simpan**")
                        h4.write("**Hapus**")

                        for idx, row in daily_data.iterrows():
                            c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
                            new_name = c1.text_input("Edit", row["Keperluan"], key=f"n_{idx}", label_visibility="collapsed")
                            new_price = c2.number_input("Harga", value=int(row["Harga_Satuan"]), key=f"p_{idx}", label_visibility="collapsed")
                            
                            if c3.button("💾", key=f"s_{idx}"):
                                df.at[idx, "Keperluan"] = new_name
                                df.at[idx, "Harga_Satuan"] = new_price
                                df.to_csv(DB_FILE, index=False)
                                st.rerun()
                            if c4.button("🗑️", key=f"d_{idx}"):
                                df.drop(idx, inplace=True)
                                df.to_csv(DB_FILE, index=False)
                                st.rerun()
                        
                        st.markdown(f"**Total Belanja tgl {tgl}:** `Rp{daily_data['Harga_Satuan'].sum():,}`")

                # Ringkasan Akumulasi Saldo
                st.write("---")
                t_modal = pic_data.groupby('Tanggal')['Dana_Awal'].first().sum()
                t_belanja = pic_data['Harga_Satuan'].sum()
                
                st.markdown("### 📊 Ringkasan Saldo Keseluruhan")
                m1, m2, m3 = st.columns(3)
                m1.metric("Total Modal Masuk", f"Rp{t_modal:,}")
                m2.metric("Total Belanja", f"Rp{t_belanja:,}")
                m3.metric("Sisa Saldo Tim", f"Rp{t_modal - t_belanja:,}")
