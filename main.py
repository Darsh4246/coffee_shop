import pandas as pd
import streamlit as st
from datetime import datetime
import uuid
import random

EXCEL_FILE = "coffee_orders.xlsx"
PASSWORD = "admin123"  # simple password for serve and cook pages

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

# Initialize Excel if not exists
def initialize_excel():
    try:
        pd.read_excel(EXCEL_FILE)
    except FileNotFoundError:
        df = pd.DataFrame(columns=["OrderID", "OrderTime", "Status", "Item", "Quantity", "AddOns", "Name", "TokenNumber", "TotalPrice", "OrderGroupID"])
        df.to_excel(EXCEL_FILE, index=False)

# Generate a 3-digit unique token number
def generate_token():
    df = pd.read_excel(EXCEL_FILE)
    existing_tokens = df['TokenNumber'].astype(str).tolist()
    while True:
        token = str(random.randint(100, 999))
        if token not in existing_tokens:
            return token

# Create new order
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

# Get all orders for a token number
def get_orders_by_token(token):
    df = pd.read_excel(EXCEL_FILE)
    return df[df['TokenNumber'].astype(str) == str(token)]

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
        token_number = generate_token()

        selected_items = st.multiselect("Select Items", list(MENU.keys()))
        quantities = []
        total_price = 0

        if selected_items:
            for item in selected_items:
                q = st.number_input(f"Quantity for {item}", min_value=1, step=1, key=item)
                quantities.append(q)
                total_price += MENU[item] * q

        addons = st.text_area("Add-ons (comma separated)", "")

        st.write(f"### Total Price: ₹{total_price}")

        submitted = st.form_submit_button("Place Order (Pay in Cash)")
        if submitted:
            if selected_items:
                success, order_group_id = create_order(selected_items, quantities, addons, name, token_number)
                st.success("Order placed! Please pay at the counter for approval.")
                st.markdown(f"## Your Token Number: {token_number}")
                st.markdown("---")

                # Show Track Order Immediately
                st.header("Track Your Order")
                orders = get_orders_by_token(token_number)
                if not orders.empty:
                    st.markdown(f"## Token: {token_number}")
                    for idx, row in orders.iterrows():
                        st.write(f"{row['Item']} x {row['Quantity']} - Status: {row['Status']}")
                else:
                    st.warning("No orders found for this token number.")
            else:
                st.warning("Please select at least one item.")

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
                    st.text(f"Total Price: ₹{row['TotalPrice']}")
                    if st.button("Mark as Cooked", key=row["OrderID"]):
                        cook_order(row["OrderID"])
                        st.success("Order marked as cooked.")
                        st.rerun()
        else:
            st.info("No pending orders.")

    elif page == "Serve":
        st.header("Serve - Orders to Deliver")

        unapproved_orders = get_orders_by_status("Unapproved")
        if not unapproved_orders.empty:
            st.subheader("Approve Orders (After Payment)")
            grouped = unapproved_orders.groupby("OrderGroupID")
            for group_id, group_df in grouped:
                with st.expander(f"Order Group - Token: {group_df.iloc[0]['TokenNumber']}, Customer: {group_df.iloc[0]['Name']}"):
                    for idx, row in group_df.iterrows():
                        st.text(f"{row['Item']} x {row['Quantity']} (Add-ons: {row['AddOns']}) - ₹{row['TotalPrice']}")
                    group_total = group_df["TotalPrice"].sum()
                    st.text(f"Total Price: ₹{group_total}")
                    if st.button("Approve Order", key=f"approve_{group_id}"):
                        for idx, row in group_df.iterrows():
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
                    st.text(f"Total Price: ₹{row['TotalPrice']}")
                    if st.button("Mark as Delivered", key=row["OrderID"]):
                        serve_order(row["OrderID"])
                        st.success("Order marked as delivered.")
                        st.rerun()
        else:
            st.info("No orders ready to serve.")
