# ... (kode bagian atas tetap sama hingga choice == "Dashboard Manager")

elif choice == "Dashboard Manager":
    st.subheader("🕵️ Dashboard Verifikasi & Edit")
    
    # 1. Approval (Pending)
    pending_df = df[df["Status"] == "Pending"]
    if not pending_df.empty:
        for pic_name in pending_df["PIC"].unique():
            with st.expander(f"🔴 LAPORAN BARU: {pic_name}", expanded=True):
                pic_p = pending_df[pending_df["PIC"] == pic_name]
                st.table(pic_p[["Tanggal", "Keperluan", "Harga_Satuan"]])
                
                t_modal_p = pic_p["Dana_Awal"].iloc[0] if not pic_p.empty else 0
                t_belanja_p = pic_p["Harga_Satuan"].sum()
                
                c_p1, c_p2, c_p3 = st.columns(3)
                c_p1.metric("Modal Laporan Ini", f"Rp{t_modal_p:,}")
                c_p2.metric("Belanja Laporan Ini", f"Rp{t_belanja_p:,}")
                c_p3.metric("Sisa", f"Rp{t_modal_p - t_belanja_p:,}")
                
                if st.button(f"✅ Approve Laporan {pic_name}", key=f"app_{pic_name}"):
                    df.loc[(df["PIC"] == pic_name) & (df["Status"] == "Pending"), "Status"] = "Approved"
                    df.to_csv(DB_FILE, index=False)
                    st.rerun()
    
    st.write("---")
    
    # 2. Pertanggungjawaban per Tim (Approved) - DENGAN PENGELOMPOKAN TANGGAL
    approved_all = df[df["Status"] == "Approved"]
    if not approved_all.empty:
        st.subheader("📋 Pertanggungjawaban per Tim (Approved)")
        unique_pics = sorted(approved_all["PIC"].unique())
        tabs = st.tabs(list(unique_pics))
        
        for i, pic_name in enumerate(unique_pics):
            with tabs[i]:
                pic_data = approved_all[approved_all["PIC"] == pic_name].copy()
                
                # Urutkan tanggal dari yang terbaru
                available_dates = sorted(pic_data["Tanggal"].unique(), reverse=True)
                
                for tgl in available_dates:
                    # Buat container/expander untuk setiap kelompok tanggal
                    with st.expander(f"📅 Pengeluaran Tanggal: {tgl}", expanded=True):
                        # Ambil hanya data di tanggal tersebut
                        daily_data = pic_data[pic_data["Tanggal"] == tgl]
                        
                        h1, h2, h3, h4 = st.columns([3, 2, 1, 1])
                        h1.write("**Barang**")
                        h2.write("**Harga**")
                        h3.write("**Simpan**")
                        h4.write("**Hapus**")

                        for idx, row in daily_data.iterrows():
                            curr_val = int(row["Harga_Satuan"]) if pd.notnull(row["Harga_Satuan"]) else 0
                            with st.container():
                                c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
                                new_name = c1.text_input("Edit", row["Keperluan"], key=f"n_{idx}", label_visibility="collapsed")
                                new_price = c2.number_input("Harga", value=curr_val, key=f"p_{idx}", label_visibility="collapsed")
                                
                                if c3.button("💾", key=f"s_{idx}"):
                                    df.at[idx, "Keperluan"] = new_name
                                    df.at[idx, "Harga_Satuan"] = new_price
                                    df.to_csv(DB_FILE, index=False)
                                    st.rerun()
                                if c4.button("🗑️", key=f"d_{idx}"):
                                    df.drop(idx, inplace=True)
                                    df.to_csv(DB_FILE, index=False)
                                    st.rerun()
                        
                        # Ringkasan kecil per tanggal
                        daily_total = daily_data["Harga_Satuan"].sum()
                        st.markdown(f"**Total Belanja tgl {tgl}:** `Rp{daily_total:,}`")
                
                st.write("---")
                # Perhitungan Akumulasi Seluruh Tanggal
                t_modal = pic_data.groupby('Tanggal')['Dana_Awal'].first().sum()
                t_belanja = pic_data['Harga_Satuan'].sum()
                
                st.markdown("### 📊 Ringkasan Saldo Keseluruhan")
                m1, m2, m3 = st.columns(3)
                m1.metric("Total Semua Modal", f"Rp{t_modal:,}")
                m2.metric("Total Belanja Akumulasi", f"Rp{t_belanja:,}")
                m3.metric("Sisa Saldo Saat Ini", f"Rp{t_modal - t_belanja:,}")
