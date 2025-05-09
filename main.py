import pandas as pd
import streamlit as st
from datetime import datetime
import uuid

EXCEL_FILE = "coffee_orders.xlsx"
PASSWORD = "admin123"  # simple password for serve and cook pages

MENU = {
    "Espresso": 100,
    "Latte": 150,
    "Cappuccino": 130,
    "Mocha": 160,
    "Americano": 110
}

# Initialize Excel if not exists
def initialize_excel():
    try:
        pd.read_excel(EXCEL_FILE)
    except FileNotFoundError:
        df = pd.DataFrame(columns=["OrderID", "OrderTime", "Status", "Item", "Quantity", "AddOns", "Name", "TokenNumber"])
        df.to_excel(EXCEL_FILE, index=False)

# Create new order
def create_order(item, quantity, addons, name, token_number):
    df = pd.read_excel(EXCEL_FILE)
    new_order = {
        "OrderID": str(uuid.uuid4()),
        "OrderTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Status": "Unapproved",
        "Item": item,
        "Quantity": quantity,
        "AddOns": addons,
        "Name": name,
        "TokenNumber": token_number
    }
    df = pd.concat([df, pd.DataFrame([new_order])], ignore_index=True)
    df.to_excel(EXCEL_FILE, index=False)
    return new_order["OrderID"]

# Update order status
def update_order_status(order_id, new_status):
    df = pd.read_excel(EXCEL_FILE)
    df.loc[df["OrderID"] == order_id, "Status"] = new_status
    df.to_excel(EXCEL_FILE, index=False)

# Get orders by status
def get_orders_by_status(status):
    df = pd.read_excel(EXCEL_FILE)
    return df[df["Status"] == status]

# Mark as cooked
def cook_order(order_id):
    update_order_status(order_id, "Completed")

# Mark as served
def serve_order(order_id):
    update_order_status(order_id, "Delivered")

# Approve order after payment
def approve_order(order_id):
    update_order_status(order_id, "Pending")

# Initialize file
initialize_excel()

# Streamlit UI
st.set_page_config(page_title="The Coffee Shop", layout="wide")
st.title("The Coffee Shop")

page = st.sidebar.selectbox("Choose view", ["Customer", "Serve", "Cook"])

if page == "Customer":
    st.header("Customer - Place Your Order")
    with st.form(key='customer_order_form'):
        name = st.text_input("Customer Name")
        token_number = st.text_input("Token Number")
        item = st.selectbox("Choose your item", list(MENU.keys()))
        quantity = st.number_input("Quantity", min_value=1, step=1)
        addons = st.text_area("Add-ons (comma separated)", "")
        submitted = st.form_submit_button("Place Order (Pay in Cash)")
        if submitted:
            create_order(item, quantity, addons, name, token_number)
            st.success("Order placed! Please pay at the counter for approval.")

elif page in ["Serve", "Cook"]:
    password = st.text_input("Enter password to access this page", type="password")
    if password != PASSWORD:
        st.warning("Incorrect password")
        st.stop()

    if page == "Cook":
        st.header("Kitchen - Orders to Prepare")
        pending_orders = get_orders_by_status("Pending")
        if not pending_orders.empty:
            for idx, row in pending_orders.iterrows():
                with st.expander(f"Order: {row['Item']} (Qty: {row['Quantity']})"):
                    st.text(f"Add-ons: {row['AddOns']}")
                    st.text(f"Customer: {row['Name']}, Token: {row['TokenNumber']}")
                    if st.button("Mark as Cooked", key=row["OrderID"]):
                        cook_order(row["OrderID"])
                        st.success("Order marked as cooked.")
                        st.rerun()
        else:
            st.info("No pending orders.")

    elif page == "Serve":
        st.header("Serve - Orders to Deliver")

        # Approve new unapproved orders
        unapproved_orders = get_orders_by_status("Unapproved")
        if not unapproved_orders.empty:
            st.subheader("Approve Orders (After Payment)")
            for idx, row in unapproved_orders.iterrows():
                with st.expander(f"Unapproved Order - {row['Item']} (Qty: {row['Quantity']})"):
                    st.text(f"Customer: {row['Name']}, Token: {row['TokenNumber']}")
                    if st.button("Approve Order", key=f"approve_{row['OrderID']}"):
                        approve_order(row["OrderID"])
                        st.success("Order approved.")
                        st.rerun()

        cooked_orders = get_orders_by_status("Completed")
        if not cooked_orders.empty:
            st.subheader("Ready to Serve")
            for idx, row in cooked_orders.iterrows():
                with st.expander(f"Order: {row['Item']} (Qty: {row['Quantity']})"):
                    st.text(f"Add-ons: {row['AddOns']}")
                    st.text(f"Customer: {row['Name']}, Token: {row['TokenNumber']}")
                    if st.button("Mark as Delivered", key=row["OrderID"]):
                        serve_order(row["OrderID"])
                        st.success("Order marked as delivered.")
                        st.rerun()
        else:
            st.info("No orders ready to serve.")
