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

# ... (Bagian import dan load_data tetap sama)

# --- TAMBAHAN DI SIDEBAR MENU ---
menu = ["Dashboard Manager", "Input Tim (Lihat Saldo)"]
choice = st.sidebar.selectbox("Menu Utama", menu)

# --- MENU 1: DASHBOARD MANAGER (Tempat Input Modal) ---
if choice == "Dashboard Manager":
    st.subheader("🕵️ Dashboard Manager")
    
    # FITUR BARU: INPUT MODAL UNTUK TIM
    with st.expander("💰 Input Pemberian Modal Baru", expanded=False):
        c1, c2 = st.columns(2)
        target_tim = c1.selectbox("Berikan Modal Ke:", ["Tim A", "Tim B"], key="target_modal")
        jumlah_modal = c2.number_input("Jumlah Modal (Rp)", min_value=0, step=50000)
        if st.button("Kirim Modal"):
            new_modal = pd.DataFrame([{
                "Tanggal": datetime.now().strftime("%Y-%m-%d"),
                "PIC": target_tim, "Keperluan": "MODAL AWAL", 
                "Dana_Awal": jumlah_modal, "Harga_Satuan": 0, "Status": "Approved"
            }])
            df = pd.concat([df, new_modal], ignore_index=True)
            df.to_csv(DB_FILE, index=False)
            st.success(f"Berhasil menginput modal Rp{jumlah_modal:,} untuk {target_tim}")
            st.rerun()

    # ... (Logika Approval & Riwayat Tanggal yang sebelumnya tetap di sini)

# --- MENU 2: INPUT TIM (SINKRON DENGAN MODAL MANAGER) ---
elif choice == "Input Tim (Lihat Saldo)":
    st.subheader("📝 Form Pengeluaran Tim")
    pic = st.selectbox("Siapa Anda?", ["Tim A", "Tim B"])
    
    # CEK SALDO DARI MANAGER
    pic_data = df[df["PIC"] == pic]
    total_modal_manager = pic_data.groupby('Tanggal')['Dana_Awal'].first().sum()
    total_belanja_tim = pic_data['Harga_Satuan'].sum()
    saldo_saat_ini = total_modal_manager - total_belanja_tim

    # TAMPILAN SALDO UNTUK SALING MENGINGATKAN
    if total_modal_manager == 0:
        st.error(f"⚠️ PERINGATAN: Manager belum menginput modal untuk {pic}. Silakan ingatkan Manager!")
    else:
        st.info(f"✅ Saldo Anda yang tercatat di sistem: **Rp{saldo_saat_ini:,}**")
        
    # Tim tetap bisa input belanja jika saldo ada
    if saldo_saat_ini > 0:
        with st.form("input_belanja"):
            # ... (Daftar belanja seperti kode sebelumnya)
            pass
