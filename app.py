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
    
    # 1. Fitur Input Modal (Tetap sama)
    with st.expander("💰 Input Pemberian Modal Baru", expanded=False):
        c1, c2 = st.columns(2)
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

    st.write("---")
    
    # 2. Fitur Verifikasi, Edit, dan Hapus
    pending_df = df[df["Status"] == "Pending"]
    if not pending_df.empty:
        st.subheader("📩 Laporan Perlu Verifikasi")
        
        # Iterasi per baris agar bisa diedit/dihapus satu per satu
        for index, row in pending_df.iterrows():
            with st.expander(f"📄 Laporan: {row['PIC']} - {row['Keperluan']} (Rp{row['Harga_Satuan']:,})", expanded=True):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                # Form Edit Sederhana
                new_keperluan = col1.text_input("Edit Keperluan", value=row['Keperluan'], key=f"edit_kep_{index}")
                new_harga = col2.number_input("Edit Harga (Rp)", value=int(row['Harga_Satuan']), step=1000, key=f"edit_hrg_{index}")
                
                btn_col1, btn_col2, btn_col3 = st.columns(3)
                
                # TOMBOL APPROVE
                if btn_col1.button(f"✅ Approve", key=f"app_{index}"):
                    df.at[index, "Keperluan"] = new_keperluan
                    df.at[index, "Harga_Satuan"] = new_harga
                    df.at[index, "Status"] = "Approved"
                    df.to_csv(DB_FILE, index=False)
                    st.toast(f"Laporan {row['PIC']} disetujui!")
                    st.rerun()
                
                # TOMBOL HAPUS (Jika tidak sesuai/palsu)
                if btn_col2.button(f"🗑️ Hapus", key=f"del_{index}"):
                    df = df.drop(index)
                    df.to_csv(DB_FILE, index=False)
                    st.warning(f"Laporan {row['PIC']} telah dihapus.")
                    st.rerun()
                    
                # TOMBOL REJECT (Opsional: Tandai reject tanpa hapus data)
                if btn_col3.button(f"❌ Reject", key=f"rej_{index}"):
                    df.at[index, "Status"] = "Rejected"
                    df.to_csv(DB_FILE, index=False)
                    st.error(f"Laporan {row['PIC']} ditolak.")
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
        # Perhitungan belanja menyertakan nominal positif (belanja) dan negatif (refund modal)
        belanja_user = user_data[user_data["Status"] == "Approved"]["Harga_Satuan"].sum()
        # Saldo = Total Modal - Total Belanja
        saldo_user = modal_user - belanja_user
        
        if modal_user > 0:
            st.success(f"💰 Saldo Anda (**{nama_user}**) saat ini: **Rp{saldo_user:,}**")
        else:
            st.warning(f"⚠️ Nama '{nama_user}' belum ada di data Manager.")

        st.write("---")

        # --- FITUR REFUND (PASTIKAN INDENTASI SEPERTI INI) ---
        with st.expander("🔄 Kembalikan Sisa Saldo (Refund ke Manager)", expanded=False):
            st.write(f"Saldo Anda saat ini adalah **Rp{saldo_user:,}**")
            jumlah_refund = st.number_input("Jumlah uang yang dikembalikan (Rp)", min_value=0, max_value=int(saldo_user) if saldo_user > 0 else 0, step=1000)
            alasan_refund = st.text_input("Catatan (Misal: Sudah tidak ada belanja lagi)")
            
            if st.button("Proses Pengembalian"):
                if jumlah_refund > 0:
                    refund_row = pd.DataFrame([{
                        "Tanggal": datetime.now().strftime("%Y-%m-%d"),
                        "PIC": nama_user,
                        "Keperluan": f"PENGEMBALIAN: {alasan_refund}",
                        "Dana_Awal": 0,
                        "Harga_Satuan": jumlah_refund, # Dicatat sebagai 'belanja' agar saldo berkurang jadi 0
                        "Status": "Approved"
                    }])
                    df = pd.concat([df, refund_row], ignore_index=True)
                    df.to_csv(DB_FILE, index=False)
                    st.success(f"Berhasil! Sisa saldo telah dikembalikan ke sistem.")
                    st.rerun()
                else:
                    st.error("Masukkan nominal pengembalian!")

        # --- 3. Form Input Barang ---
        st.write("---")
        st.write("### ➕ Tambah Belanja Baru")
        
        # Validasi: Hanya tampilkan form jika saldo lebih dari 0
        if saldo_user > 0:
            with st.form("form_tambah_barang", clear_on_submit=True):
                c1, c2 = st.columns(2)
                item_nama = c1.text_input("Nama Barang/Keperluan")
                
                # Max value diatur agar tidak bisa input melebihi sisa saldo
                item_harga = c2.number_input(
                    "Harga Sesuai Nota (Rp)", 
                    min_value=0, 
                    max_value=int(saldo_user), 
                    step=1000,
                    help=f"Maksimal input: Rp{saldo_user:,}"
                )
                submit_tambah = st.form_submit_button("➕ Tambahkan ke Daftar")
                
                if submit_tambah:
                    if item_nama and item_harga > 0:
                        st.session_state.items_list.append({"Barang": item_nama, "Harga": item_harga})
                        st.rerun()
                    else:
                        st.error("Isi nama barang dan harganya!")
        else:
            # Tampilan jika saldo Rp0
            st.warning("⚠️ **Saldo Anda sudah habis (Rp0).** Anda tidak dapat menambah daftar belanja lagi.")
            st.info("Silakan hubungi Manager jika memerlukan penambahan modal operasional.")

# --- MENU 3: LIHAT SALDO PERSONAL ---
elif choice == "Lihat Saldo Personal":
    st.subheader("📊 Cek Saldo Real-time")
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
