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

# 3. SIDEBAR MENU
menu = ["Dashboard Manager", "Input Laporan Tim", "Lihat Saldo Personal"]
choice = st.sidebar.selectbox("Menu Utama", menu)

# --- MENU 1: DASHBOARD MANAGER ---
if choice == "Dashboard Manager":
    st.subheader("🕵️ Dashboard Manager")
    
    with st.expander("💰 Input Pemberian Modal Baru", expanded=False):
        c1, c2 = st.columns(2)
        # DIUBAH: Menggunakan text_input agar bisa ketik nama siapa saja (Andes, Arif, dll)
        target_nama = c1.text_input("Berikan Modal Ke Nama (Contoh: Andes):")
        jumlah_modal = c2.number_input("Jumlah Modal (Rp)", min_value=0, step=50000)
        
        if st.button("Kirim Modal"):
            if target_nama:
                new_modal = pd.DataFrame([{
                    "Tanggal": datetime.now().strftime("%Y-%m-%d"),
                    "PIC": target_nama.strip().title(), 
                    "Keperluan": "MODAL AWAL", 
                    "Dana_Awal": jumlah_modal, 
                    "Harga_Satuan": 0, 
                    "Status": "Approved"
                }])
                df = pd.concat([df, new_modal], ignore_index=True)
                df.to_csv(DB_FILE, index=False)
                st.success(f"Berhasil menginput modal Rp{jumlah_modal:,} untuk {target_nama}")
                st.rerun()
            else:
                st.error("Nama harus diisi!")

    st.write("---")
    
    # Fitur Verifikasi
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
        st.info("Tidak ada laporan baru.")

# --- MENU 2: INPUT TIM ---
elif choice == "Input Laporan Tim":
    st.subheader("📝 Form Laporan Pengeluaran")
    # DIUBAH: Tim mengetikkan nama mereka sendiri
    nama_user = st.text_input("Ketik Nama Anda (Samakan dengan input Manager):").strip().title()
    
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
        
        if st.button("🚀 Kirim Semua ke Manager"):
            if nama_user:
                new_rows = []
                for itm in st.session_state.items_list:
                    new_rows.append({
                        "Tanggal": datetime.now().strftime("%Y-%m-%d"),
                        "PIC": nama_user, 
                        "Keperluan": itm["Barang"], 
                        "Dana_Awal": 0,
                        "Harga_Satuan": itm["Harga"], 
                        "Status": "Pending"
                    })
                df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
                df.to_csv(DB_FILE, index=False)
                st.session_state.items_list = []
                st.success(f"Laporan {nama_user} berhasil dikirim!")
                st.rerun()
            else:
                st.error("Tolong isi Nama Anda sebelum mengirim!")

# --- MENU 3: LIHAT SALDO PERSONAL ---
elif choice == "Lihat Saldo Personal":
    st.subheader("📊 Cek Saldo Real-time")
    # Mengambil daftar nama unik yang pernah ada di database
    daftar_nama = sorted(df["PIC"].unique())
    if daftar_nama:
        pic = st.selectbox("Pilih Nama Anda", daftar_nama)
        
        pic_data = df[df["PIC"] == pic]
        total_modal = pic_data[pic_data["Keperluan"] == "MODAL AWAL"]["Dana_Awal"].sum()
        total_belanja = pic_data[pic_data["Status"] == "Approved"]["Harga_Satuan"].sum()
        saldo = total_modal - total_belanja

        st.success(f"✅ Saldo Tersisa untuk **{pic}**: **Rp{saldo:,}**")
        
        c1, c2 = st.columns(2)
        c1.metric("Total Modal Diterima", f"Rp{total_modal:,}")
        c2.metric("Total Belanja Approved", f"Rp{total_belanja:,}")
        
        st.write("### Riwayat Transaksi:")
        st.dataframe(pic_data[["Tanggal", "Keperluan", "Harga_Satuan", "Status"]], use_container_width=True)
    else:
        st.info("Belum ada data transaksi di sistem.")
