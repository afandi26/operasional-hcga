import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Database sederhana
DB_FILE = "data_pengeluaran.csv"

def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["Tanggal", "PIC", "Keperluan", "Dana_Awal", "Total_Belanja", "Sisa", "Status"])

st.set_page_config(page_title="HC-GA Operasional", layout="wide")
st.title("💰 Sistem Pengeluaran HC & GA")

menu = ["Input Tim", "Dashboard Manager", "Ekspor Data"]
choice = st.sidebar.selectbox("Menu", menu)
df = load_data()

if choice == "Input Tim":
    st.subheader("📝 Form Pengeluaran")
    with st.form("input_form"):
        pic = st.selectbox("Nama Tim", ["Tim A", "Tim B"])
        keperluan = st.text_input("Barang yang dibeli")
        dana = st.number_input("Dana yang Diterima", min_value=0)
        spent = st.number_input("Total Belanja", min_value=0)
        if st.form_submit_button("Kirim"):
            new_row = {"Tanggal": datetime.now().strftime("%Y-%m-%d"), "PIC": pic, "Keperluan": keperluan, "Dana_Awal": dana, "Total_Belanja": spent, "Sisa": dana-spent, "Status": "Pending"}
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_csv(DB_FILE, index=False)
            st.success(f"Terkirim! Sisa uang: Rp{dana-spent:,}")

elif choice == "Dashboard Manager":
    st.subheader("🕵️ Cek Pengeluaran")
    st.dataframe(df)
    if st.button("Approve Semua"):
        df["Status"] = "Approved"
        df.to_csv(DB_FILE, index=False)
        st.rerun()

elif choice == "Ekspor Data":
    st.download_button("Download CSV untuk Accounting", df.to_csv(index=False), "laporan.csv", "text/csv")
