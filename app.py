import streamlit as st
from module.controller import ReceiptController

st.set_page_config(page_title="AI Bill Splitter", layout="wide")

# Load controller dari session
if "controller" not in st.session_state:
    st.session_state.controller = ReceiptController()

ctl = st.session_state.controller

st.title("📄 Bill Splitter")

if ctl.step == 1:
    api_key = st.text_input("Masukkan Google API Key", type="password")
    uploaded = st.file_uploader("Upload gambar nota", type=["jpg", "jpeg", "png"])

    if uploaded and api_key:
        ctl.process_receipt(api_key, uploaded)
        st.success("Nota berhasil dibaca!")
        if st.button("Lanjut"):
            st.rerun()
    else:
        st.info("Masukkan API Key dan upload nota untuk lanjut.")

elif ctl.step == 2:
    receipt = ctl.receipt

    st.subheader("🧾 Isi Nota")
    rows = [
        {
            "Item": item.name,
            "Qty": item.quantity,
            "Unit Price": item.unit_price,
            "Total Price": item.total_price
        }
        for item in receipt.items
    ]
    html_table = """
    <table style="width: 100%; border-collapse: collapse;">
    <tr>
        <th style="border-bottom: 1px solid #ddd; text-align:left;">Item</th>
        <th style="border-bottom: 1px solid #ddd; text-align:center;">Qty</th>
        <th style="border-bottom: 1px solid #ddd; text-align:right;">Unit Price</th>
        <th style="border-bottom: 1px solid #ddd; text-align:right;">Total Price</th>
    </tr>
    """
    
    for item in rows:
        html_table += f"""
    <tr>
        <td style="padding:4px 8px;">{item['Item']}</td>
        <td style="padding:4px 8px; text-align:center;">{item['Qty']}</td>
        <td style="padding:4px 8px; text-align:right;">Rp {item['Unit Price']:,}</td>
        <td style="padding:4px 8px; text-align:right;">Rp {item['Total Price']:,}</td>
    </tr>
    """
    
    html_table += "</table>"
    
    st.markdown(html_table, unsafe_allow_html=True)

    st.markdown(
        f"""
        <div style="width: 300px; margin: 0 auto; font-size:16px;">
            <div style="display:flex; justify-content:space-between;">
                <span>Subtotal</span>
                <span>Rp {receipt.subtotal:,.0f}</span>
            </div>
            <div style="display:flex; justify-content:space-between;">
                <span>Tax</span>
                <span>Rp {receipt.tax:,.0f}</span>
            </div>
            <div style="display:flex; justify-content:space-between;">
                <span>Service Charge</span>
                <span>Rp {receipt.service_charge:,.0f}</span>
            </div>
            <div style="display:flex; justify-content:space-between;">
                <span>Others</span>
                <span>Rp {receipt.others:,.0f}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")
    st.markdown(
        f"""
        <div style="font-size: 26px; font-weight: bold; text-align: center;">
            TOTAL BAYAR: Rp {receipt.total:,.0f}
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown("---")

    st.subheader("👥 Tambahkan Orang")

    person_name = st.text_input("Nama orang", key="input_person")

    # Simpan agar tidak hilang saat rerun
    if person_name:
        st.session_state.current_person = person_name

    if "current_person" in st.session_state:
        person_name = st.session_state.current_person

        # Siapkan memory orang jika belum ada
        if person_name not in ctl.temp_people:
            ctl.temp_people[person_name] = {}

        st.markdown("### Pilih menu & jumlah")

        col1, col2 = st.columns([3, 1])

        with col1:
            menu_choice = st.selectbox(
                "",
                [item.name for item in receipt.items],
                key=f"menu_{person_name}"
            )
            st.caption("Menu")

        with col2:
            qty = st.number_input(
                "",
                min_value=1,
                value=1,
                step=1,
                key=f"qty_{person_name}"
            )
            st.caption("Jumlah")

        if st.button("Tambah Menu"):
            ctl.add_temp_menu(person_name, menu_choice, qty)
            st.success(f"{menu_choice} ditambahkan untuk {person_name}")
            st.rerun()

        if ctl.temp_people[person_name]:
            st.subheader("Menu yang sudah dipilih")
            st.table([
                {"Item": item, "Qty": q}
                for item, q in ctl.temp_people[person_name].items()
            ])

        if st.button(f"Selesai tambah untuk {person_name}"):
            ctl.commit_person(person_name)
            del st.session_state.current_person
            st.success(f"{person_name} ditambahkan!")
            st.rerun()

    if ctl.people:
        st.subheader("Daftar Orang")

        for p in ctl.people:
            st.markdown(f"### {p['name']}")

            for item, qty in p["menu"].items():
                st.markdown(f"- **{item}** × {qty}")

            st.markdown("---")
    
    if st.button("Lanjut ke hasil"):
        ctl.step = 3
        st.rerun()


elif ctl.step == 3:
    totals = ctl.compute_bill()

    st.subheader("💰 Total Bayar per Orang")
    st.table([
        {"Nama": name, "Total": int(total)}
        for name, total in totals.items()
    ])

    if st.button("Mulai ulang"):
        ctl.reset()
        st.rerun()