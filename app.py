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
        target_nama = c1.text_input("Berikan Modal Ke Nama:")
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

    st.write("---")
    
    pending_df = df[df["Status"] == "Pending"]
    if not pending_df.empty:
        st.subheader("📩 Laporan Perlu Verifikasi (Group by Nama)")
        
        for pic, group in pending_df.groupby("PIC"):
            # LOGIKA PERBAIKAN SALDO:
            user_all_data = df[df["PIC"] == pic]
            total_modal_pic = user_all_data[user_all_data["Keperluan"] == "MODAL AWAL"]["Dana_Awal"].sum()
            
            # Belanja yang sudah disetujui sebelumnya
            belanja_approved_lama = user_all_data[user_all_data["Status"] == "Approved"]["Harga_Satuan"].sum()
            
            # Total pengajuan yang sedang diperiksa sekarang
            total_pengajuan_skrg = group["Harga_Satuan"].sum()
            
            # Estimasi sisa saldo jika semua di-approve
            estimasi_saldo_akhir = total_modal_pic - (belanja_approved_lama + total_pengajuan_skrg)

            with st.expander(f"👤 PIC: {pic} | Total Pengajuan: Rp{total_pengajuan_skrg:,} | Estimasi Sisa Saldo: Rp{estimasi_saldo_akhir:,}", expanded=True):
                st.info(f"Jika laporan ini disetujui, sisa uang di tangan {pic} menjadi **Rp{estimasi_saldo_akhir:,}**")
                st.write("**Daftar Pengajuan:**")
                
                for idx, row in group.iterrows():
                    col_item, col_price, col_action = st.columns([3, 2, 2])
                    col_item.text(f"• {row['Keperluan']}")
                    col_price.text(f"Rp{row['Harga_Satuan']:,}")
                    
                    if col_action.button("🗑️ Hapus", key=f"del_{idx}"):
                        df = df.drop(idx)
                        df.to_csv(DB_FILE, index=False)
                        st.rerun()

                st.write("---")
                c_app, c_rej = st.columns(2)
                if c_app.button(f"✅ Approve Semua Laporan {pic}", key=f"app_all_{pic}"):
                    df.loc[group.index, "Status"] = "Approved"
                    df.to_csv(DB_FILE, index=False)
                    st.success(f"Semua laporan {pic} disetujui!")
                    st.rerun()
                
                if c_rej.button(f"❌ Reject Semua Laporan {pic}", key=f"rej_all_{pic}"):
                    df.loc[group.index, "Status"] = "Rejected"
                    df.to_csv(DB_FILE, index=False)
                    st.rerun()
    else:
        st.info("Tidak ada laporan baru yang perlu dicek.")

# --- MENU 2: INPUT TIM ---
elif choice == "Input Laporan Tim":
    st.subheader("📝 Form Laporan Pengeluaran")
    nama_user = st.text_input("Ketik Nama Anda:", key="input_nama_user").strip().title()
    
    if 'items_list' not in st.session_state:
        st.session_state.items_list = []

    if nama_user:
        user_data = df[df["PIC"] == nama_user]
        modal_user = user_data[user_data["Keperluan"] == "MODAL AWAL"]["Dana_Awal"].sum()
        
        # Di sisi user, kita tampilkan saldo real (yang sudah approved + sedang pending) 
        # agar mereka tidak belanja melebihi modal yang ada
        belanja_total = user_data[user_data["Status"].isin(["Approved", "Pending"])]["Harga_Satuan"].sum()
        saldo_user = modal_user - belanja_total
        
        st.success(f"💰 Sisa Saldo Tersedia untuk Belanja (**{nama_user}**): **Rp{saldo_user:,}**")

        st.write("### ➕ Tambah Belanja Baru")
        if saldo_user > 0:
            with st.form("form_tambah_barang", clear_on_submit=True):
                c1, c2 = st.columns(2)
                item_nama = c1.text_input("Nama Barang")
                item_harga = c2.number_input("Harga (Rp)", min_value=0, max_value=int(saldo_user), step=1000)
                if st.form_submit_button("➕ Tambahkan ke Daftar"):
                    if item_nama and item_harga > 0:
                        st.session_state.items_list.append({"Barang": item_nama, "Harga": item_harga})
                        st.rerun()
        else:
            st.warning("⚠️ Saldo tidak mencukupi untuk belanja baru.")

        if st.session_state.items_list:
            st.write("### 🛒 Daftar Belanja (Belum Terkirim)")
            total_skrg = 0
            for i, itm in enumerate(st.session_state.items_list):
                st.write(f"{i+1}. {itm['Barang']} - Rp{itm['Harga']:,}")
                total_skrg += itm['Harga']
            
            if st.button("🚀 Kirim Semua Laporan ke Manager"):
                new_rows = []
                for itm in st.session_state.items_list:
                    new_rows.append({"Tanggal": datetime.now().strftime("%Y-%m-%d"), "PIC": nama_user, "Keperluan": itm["Barang"], "Dana_Awal": 0, "Harga_Satuan": itm["Harga"], "Status": "Pending"})
                df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
                df.to_csv(DB_FILE, index=False)
                st.session_state.items_list = []
                st.success("Laporan terkirim!")
                st.rerun()

# --- MENU 3: LIHAT SALDO PERSONAL ---
elif choice == "Lihat Saldo Personal":
    st.subheader("📊 Cek Saldo Real-time")
    daftar_nama = sorted(df["PIC"].unique())
    if daftar_nama:
        pic = st.selectbox("Pilih Nama", daftar_nama)
        pic_data = df[df["PIC"] == pic]
        total_modal = pic_data[pic_data["Keperluan"] == "MODAL AWAL"]["Dana_Awal"].sum()
        total_belanja = pic_data[pic_data["Status"] == "Approved"]["Harga_Satuan"].sum()
        st.metric("Saldo Resmi (Approved)", f"Rp{total_modal - total_belanja:,}")
        st.dataframe(pic_data[["Tanggal", "Keperluan", "Harga_Satuan", "Status"]], use_container_width=True)
