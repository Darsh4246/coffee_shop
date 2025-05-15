import streamlit as st
st.set_page_config(page_title="The Coffee Shop", layout="wide")

import pandas as pd
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
import uuid
import random
import os

EXCEL_FILE = "coffee_orders.xlsx"
PASSWORD = os.getenv("SERVE_COOK_PASSWORD", "admin123")
ADMIN_PASSWORD = os.getenv("ADMIN_DASHBOARD_PASSWORD", "adminpanel")

MENU = {
    "Espresso": 60,
    "Latte": 80,
    "Cappuccino": 75,
    "Mocha": 85,
    "Americano": 70,
    "Butter Popcorn": 40,
    "Caramel Popcorn": 50,
    "Paneer Sandwich": 65,
    "Peri Peri Sandwich": 70,
    "Veg Roll": 55,
    "Paneer Roll": 65
}

page = st.sidebar.selectbox("Choose view", ["Customer", "Serve", "Cook", "Track Order", "Admin Dashboard"])
if page not in ["Customer", "Admin Dashboard"]:
    st_autorefresh(interval=5000, key="auto_refresh")

def initialize_excel():
    try:
        pd.read_excel(EXCEL_FILE)
    except FileNotFoundError:
        df = pd.DataFrame(columns=["OrderID", "OrderTime", "Status", "Item", "Quantity", "AddOns", "Name", "TokenNumber", "TotalPrice", "OrderGroupID"])
        df.to_excel(EXCEL_FILE, index=False)

def generate_token():
    df = pd.read_excel(EXCEL_FILE)
    existing_tokens = df['TokenNumber'].astype(str).tolist()
    while True:
        token = str(random.randint(100, 999))
        if token not in existing_tokens:
            return token

def create_order(item, quantity, addons, name, token_number):
    df = pd.read_excel(EXCEL_FILE)
    order_group_id = str(uuid.uuid4())
    for i, q in zip(item, quantity):
        new_order = {
            "OrderID": str(uuid.uuid4()),
            "OrderGroupID": order_group_id,
            "OrderTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Status": "Unapproved",
            "Item": i,
            "Quantity": q,
            "AddOns": addons,
            "Name": name,
            "TokenNumber": token_number,
            "TotalPrice": MENU.get(i, 0) * q
        }
        df = pd.concat([df, pd.DataFrame([new_order])], ignore_index=True)
    df.to_excel(EXCEL_FILE, index=False)
    return True, order_group_id

def update_order_status(order_id, new_status):
    df = pd.read_excel(EXCEL_FILE)
    df.loc[df["OrderID"] == order_id, "Status"] = new_status
    df.to_excel(EXCEL_FILE, index=False)

def get_orders_by_status(status):
    df = pd.read_excel(EXCEL_FILE)
    return df[df["Status"] == status]

def cook_order(order_id):
    update_order_status(order_id, "Completed")

def serve_order(order_id):
    update_order_status(order_id, "Delivered")

def approve_order(order_id):
    update_order_status(order_id, "Pending")

def decline_order(order_id):
    update_order_status(order_id, "Declined")

def get_orders_by_token(token):
    df = pd.read_excel(EXCEL_FILE)
    return df[df['TokenNumber'].astype(str) == str(token)]

def clear_excel():
    df = pd.DataFrame(columns=["OrderID", "OrderTime", "Status", "Item", "Quantity", "AddOns", "Name", "TokenNumber", "TotalPrice", "OrderGroupID"])
    df.to_excel(EXCEL_FILE, index=False)

def export_excel():
    with open(EXCEL_FILE, "rb") as f:
        return f.read()

initialize_excel()

st.title("The Coffee Shop")

if 'selected_items' not in st.session_state:
    st.session_state.selected_items = []
if 'quantities' not in st.session_state:
    st.session_state.quantities = {}
if 'addons' not in st.session_state:
    st.session_state.addons = ""
if 'name' not in st.session_state:
    st.session_state.name = ""
if 'token_number' not in st.session_state:
    st.session_state.token_number = generate_token()
if 'track_token' not in st.session_state:
    st.session_state.track_token = ""
if 'track_results' not in st.session_state:
    st.session_state.track_results = None
if 'tracking_initialized' not in st.session_state:
    st.session_state.tracking_initialized = False

if page == "Customer":
    st.header("Welcome to The Coffee Shop")
    with st.form("customer_form"):
        st.text_input("Your Name", key="name")
        items = st.multiselect("Select your items:", list(MENU.keys()), key="selected_items")
        for item in items:
            st.number_input(f"Quantity for {item}", min_value=1, value=1, key=f"qty_{item}")
        st.text_input("Add-ons / Notes (optional)", key="addons")
        submitted = st.form_submit_button("Place Order")
        if submitted:
            item_list = st.session_state.selected_items
            quantity_list = [st.session_state[f"qty_{i}"] for i in item_list]
            name = st.session_state.name
            addons = st.session_state.addons
            token = st.session_state.token_number
            success, group_id = create_order(item_list, quantity_list, addons, name, token)
            if success:
                st.success("Order placed! Please pay at the counter.")
                st.markdown(f"## Your Token Number: `{token}`")

elif page == "Serve":
    st.header("Serve Orders")
    password = st.text_input("Enter password", type="password")
    if password != PASSWORD:
        st.warning("Incorrect password")
        st.stop()
    orders = get_orders_by_status("Completed")
    for _, row in orders.iterrows():
        with st.expander(f"Token {row['TokenNumber']} - {row['Item']} x{row['Quantity']}"):
            if st.button("Mark as Delivered", key=f"serve_{row['OrderID']}"):
                serve_order(row['OrderID'])
                st.success("Order marked as delivered.")
            if st.button("Decline Order", key=f"decline_serve_{row['OrderID']}"):
                decline_order(row['OrderID'])
                st.warning("Order Declined")

elif page == "Cook":
    st.header("Cook Orders")
    password = st.text_input("Enter password", type="password")
    if password != PASSWORD:
        st.warning("Incorrect password")
        st.stop()
    orders = get_orders_by_status("Pending")
    for _, row in orders.iterrows():
        with st.expander(f"Token {row['TokenNumber']} - {row['Item']} x{row['Quantity']}"):
            if st.button("Mark as Cooked", key=f"cook_{row['OrderID']}"):
                cook_order(row['OrderID'])
                st.success("Order marked as cooked.")

elif page == "Track Order":
    st.header("Track Your Order")
    token = st.text_input("Enter your token number to track your order")
    if st.button("Track"):
        orders = get_orders_by_token(token)
        if not orders.empty:
            st.write(f"### Order Status for Token `{token}`")
            st.dataframe(orders[["Item", "Quantity", "Status", "TotalPrice"]])
        else:
            st.warning("No order found with this token number.")

elif page == "Admin Dashboard":
    st.header("Admin Dashboard")
    password = st.text_input("Enter admin password", type="password")
    if password != ADMIN_PASSWORD:
        st.warning("Incorrect password")
        st.stop()
    df = pd.read_excel(EXCEL_FILE)
    st.subheader("📊 Orders Overview")
    st.dataframe(df, use_container_width=True)
    st.subheader("⬇️ Export or 🧹 Clear Data")
    col1, col2 = st.columns(2)
    with col1:
        st.download_button("Export Orders as Excel", data=export_excel(), file_name="coffee_orders_export.xlsx")
    with col2:
        if st.button("Clear All Orders"):
            clear_excel()
            st.success("All orders have been cleared.")
            st.rerun()
    st.subheader("📈 Quick Stats")
    st.write(f"Total Orders: {len(df)}")
    st.write(f"Pending: {len(df[df['Status'] == 'Pending'])}, Cooked: {len(df[df['Status'] == 'Completed'])}, Delivered: {len(df[df['Status'] == 'Delivered'])}, Declined: {len(df[df['Status'] == 'Declined'])}")
