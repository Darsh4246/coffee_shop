import pandas as pd
import streamlit as st
from datetime import datetime
import uuid

EXCEL_FILE = "coffee_orders.xlsx"

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
        "Status": "Pending",
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

# Initialize file
initialize_excel()

# Streamlit UI
st.set_page_config(page_title="Coffee Shop", layout="wide")
st.title("Coffee Shop Order Management")

page = st.sidebar.selectbox("Choose view", ["Serve", "Cook"])

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

    # Take new order
    with st.form(key='new_order_form'):
        st.subheader("Take New Order")
        name = st.text_input("Customer Name", "")
        token_number = st.text_input("Token Number", "")
        item = st.text_input("Item", "")
        quantity = st.number_input("Quantity", min_value=1, step=1)
        addons = st.text_area("Add-ons (comma separated)", "")
        submit_button = st.form_submit_button("Submit Order")
        
        if submit_button and item:
            create_order(item, quantity, addons, name, token_number)
            st.success(f"New order for {item} (Qty: {quantity}) added successfully!")

    cooked_orders = get_orders_by_status("Completed")
    if not cooked_orders.empty:
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
