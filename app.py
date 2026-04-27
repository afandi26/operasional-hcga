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
    
    # 1. Fitur Input Modal
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
    
    # 2. Fitur Verifikasi, Edit, dan Hapus
    pending_df = df[df["Status"] == "Pending"]
    if not pending_df.empty:
        st.subheader("📩 Laporan Perlu Verifikasi")
        for index, row in pending_df.iterrows():
            with st.expander(f"📄 Laporan: {row['PIC']} - {row['Keperluan']} (Rp{row['Harga_Satuan']:,})", expanded=True):
                col1, col2 = st.columns([2, 1])
                new_keperluan = col1.text_input("Edit Keperluan", value=row['Keperluan'], key=f"edit_kep_{index}")
                new_harga = col2.number_input("Edit Harga (Rp)", value=int(row['Harga_Satuan']), step=1000, key=f"edit_hrg_{index}")
                
                btn_col1, btn_col2, btn_col3 = st.columns(3)
                if btn_col1.button(f"✅ Approve", key=f"app_{index}"):
                    df.at[index, "Keperluan"] = new_keperluan
                    df.at[index, "Harga_Satuan"] = new_harga
                    df.at[index, "Status"] = "Approved"
                    df.to_csv(DB_FILE, index=False)
                    st.rerun()
                
                if btn_col2.button(f"🗑️ Hapus", key=f"del_{index}"):
                    df = df.drop(index)
                    df.to_csv(DB_FILE, index=False)
                    st.rerun()
                    
                if btn_col3.button(f"❌ Reject", key=f"rej_{index}"):
                    df.at[index, "Status"] = "Rejected"
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
        belanja_user = user_data[user_data["Status"] == "Approved"]["Harga_Satuan"].sum()
        saldo_user = modal_user - belanja_user
        
        st.success(f"💰 Saldo Anda (**{nama_user}**) saat ini: **Rp{saldo_user:,}**")

        # Fitur Refund
        with st.expander("🔄 Kembalikan Sisa Saldo (Refund)", expanded=False):
            st.write(f"Saldo: **Rp{saldo_user:,}**")
            jumlah_refund = st.number_input("Jumlah Refund (Rp)", min_value=0, max_value=int(saldo_user) if saldo_user > 0 else 0)
            alasan_refund = st.text_input("Catatan Refund")
            if st.button("Proses Refund"):
                if jumlah_refund > 0:
                    refund_row = pd.DataFrame([{"Tanggal": datetime.now().strftime("%Y-%m-%d"), "PIC": nama_user, "Keperluan": f"REFUND: {alasan_refund}", "Dana_Awal": 0, "Harga_Satuan": jumlah_refund, "Status": "Approved"}])
                    df = pd.concat([df, refund_row], ignore_index=True)
                    df.to_csv(DB_FILE, index=False)
                    st.rerun()

        # Form Tambah Belanja (Hanya muncul jika saldo > 0)
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
            st.warning("⚠️ Saldo Rp0. Tidak bisa menambah belanja.")

        # Tampilkan Daftar Belanja Sementara
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
        st.metric("Saldo Tersisa", f"Rp{total_modal - total_belanja:,}")
        st.dataframe(pic_data[["Tanggal", "Keperluan", "Harga_Satuan", "Status"]], use_container_width=True)
