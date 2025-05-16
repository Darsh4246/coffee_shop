import streamlit as st
st.set_page_config(page_title="The Coffee Shop", layout="wide")

import sqlite3
import pandas as pd
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
import uuid
import random
import os
import io
from typing import List, Tuple, Dict

# Database configuration
DB_FILE = "coffee_orders.db"
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

# Fun Spotify embed
st.markdown("""
<iframe style="border-radius:12px" src="https://open.spotify.com/embed/track/4gvrJnKCKIPiacNsWVQwEU?utm_source=generator" 
width="100%" height="152" frameBorder="0" allowfullscreen="" 
allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" loading="lazy"></iframe>
""", unsafe_allow_html=True)

page = st.sidebar.selectbox("Choose view", ["Customer", "Serve", "Cook", "Track Order", "Admin Dashboard"])
if page not in ["Customer", "Admin Dashboard", "Track Order"]:
    st_autorefresh(interval=5000, key="auto_refresh")

def initialize_db():
    """Initialize the SQLite database and create tables if they don't exist"""
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS orders
                     (OrderID TEXT PRIMARY KEY,
                      OrderGroupID TEXT,
                      OrderTime TEXT,
                      Status TEXT,
                      Item TEXT,
                      Quantity INTEGER,
                      AddOns TEXT,
                      Name TEXT,
                      TokenNumber TEXT,
                      TotalPrice REAL)''')
        conn.commit()

def generate_token() -> str:
    """Generate a unique token number"""
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute('''SELECT TokenNumber FROM orders''')
        existing_tokens = [row[0] for row in c.fetchall()]
        
    while True:
        token = str(random.randint(100, 999))
        if token not in existing_tokens:
            return token

def create_order(items: List[str], quantities: List[int], addons: str, name: str, token_number: str) -> Tuple[bool, str]:
    """Create a new order in the database"""
    order_group_id = str(uuid.uuid4())
    try:
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            for item, quantity in zip(items, quantities):
                order_id = str(uuid.uuid4())
                total_price = MENU.get(item, 0) * quantity
                c.execute('''INSERT INTO orders VALUES 
                            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                         (order_id, order_group_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                          "Unapproved", item, quantity, addons, name, token_number, total_price))
            conn.commit()
        return True, order_group_id
    except Exception as e:
        st.error(f"Error creating order: {e}")
        return False, ""

def update_order_status(order_id: str, new_status: str):
    """Update the status of an order"""
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute('''UPDATE orders SET Status = ? WHERE OrderID = ?''', 
                  (new_status, order_id))
        conn.commit()

def get_orders_by_status(status: str) -> pd.DataFrame:
    """Get all orders with a specific status"""
    with sqlite3.connect(DB_FILE) as conn:
        return pd.read_sql('''SELECT * FROM orders WHERE Status = ? ORDER BY OrderTime''', 
                          conn, params=(status,))

def get_orders_by_token(token: str) -> pd.DataFrame:
    """Get all orders for a specific token"""
    with sqlite3.connect(DB_FILE) as conn:
        return pd.read_sql('''SELECT * FROM orders WHERE TokenNumber = ? ORDER BY OrderTime''', 
                          conn, params=(str(token),))

def get_all_orders() -> pd.DataFrame:
    """Get all orders from the database"""
    with sqlite3.connect(DB_FILE) as conn:
        return pd.read_sql('''SELECT * FROM orders ORDER BY OrderTime DESC''', conn)

def clear_database():
    """Clear all orders from the database"""
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute('''DELETE FROM orders''')
        conn.commit()

def export_to_excel() -> bytes:
    """Export database to Excel format"""
    df = get_all_orders()
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

def get_order_stats() -> Dict[str, int]:
    """Get statistics about orders"""
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        stats = {}
        c.execute('''SELECT COUNT(*) FROM orders''')
        stats['total'] = c.fetchone()[0]
        c.execute('''SELECT COUNT(*) FROM orders WHERE Status = ?''', ("Unapproved",))
        stats['unapproved'] = c.fetchone()[0]
        c.execute('''SELECT COUNT(*) FROM orders WHERE Status = ?''', ("Pending",))
        stats['pending'] = c.fetchone()[0]
        c.execute('''SELECT COUNT(*) FROM orders WHERE Status = ?''', ("Completed",))
        stats['completed'] = c.fetchone()[0]
        c.execute('''SELECT COUNT(*) FROM orders WHERE Status = ?''', ("Delivered",))
        stats['delivered'] = c.fetchone()[0]
        c.execute('''SELECT COUNT(*) FROM orders WHERE Status = ?''', ("Declined",))
        stats['declined'] = c.fetchone()[0]
        return stats

# Initialize database
initialize_db()

st.title("The Coffee Shop")

# Initialize all session state variables
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
if 'track_results' not in st.session_state:
    st.session_state.track_results = None
if 'tracking_initialized' not in st.session_state:
    st.session_state.tracking_initialized = False
if 'quantities_shown' not in st.session_state:
    st.session_state.quantities_shown = False

if page == "Customer":
    st.header("Welcome to The Coffee Shop")
    st.text_input("Your Name", key="name")
    selected_items = st.multiselect("Select your items:", list(MENU.keys()), key="selected_items")

    if selected_items and st.button("Set Quantity"):
        st.session_state.quantities_shown = True

    if st.session_state.quantities_shown:
        for item in selected_items:
            st.session_state.quantities[item] = st.number_input(f"Quantity for {item}", min_value=1, value=1, key=f"qty_{item}")

    st.text_input("Add-ons / Notes (optional)", key="addons")

    if st.button("Place Order"):
        if not selected_items or not st.session_state.quantities_shown:
            st.warning("Please select items and set their quantities first.")
        else:
            item_list = selected_items
            quantity_list = [st.session_state.quantities.get(i, 1) for i in item_list]
            name = st.session_state.name
            addons = st.session_state.addons
            token = st.session_state.token_number
            success, group_id = create_order(item_list, quantity_list, addons, name, token)
            if success:
                total_price = sum(MENU.get(i, 0) * q for i, q in zip(item_list, quantity_list))
                st.success(f"Order placed! Please pay at the counter. Total: ₹{total_price}")
                st.markdown(f"## Your Token Number: `{token}`")

elif page == "Serve":
    st.header("Serve Orders")
    password = st.text_input("Enter password", type="password")
    if password != PASSWORD:
        st.warning("Incorrect password")
        st.stop()
    
    # Combined approval and serving interface
    tab1, tab2 = st.tabs(["Approve Orders", "Serve Prepared Orders"])
    
    with tab1:
        st.subheader("Approve New Orders")
        unapproved_orders = get_orders_by_status("Unapproved")
        
        if unapproved_orders.empty:
            st.info("No orders waiting for approval")
        else:
            for _, row in unapproved_orders.iterrows():
                with st.expander(f"Token {row['TokenNumber']} - {row['Name']} - {row['Item']} x{row['Quantity']} (₹{row['TotalPrice']})"):
                    st.write(f"**Order:** {row['Item']} x{row['Quantity']}")
                    st.write(f"**Total:** ₹{row['TotalPrice']}")
                    st.write(f"**Notes:** {row['AddOns']}")
                    if st.button("Approve Order", key=f"approve_{row['OrderID']}"):
                        update_order_status(row['OrderID'], "Pending")
                        st.success("Order approved and sent to kitchen!")
                        st.rerun()
                    if st.button("Decline Order", key=f"decline_{row['OrderID']}"):
                        update_order_status(row['OrderID'], "Declined")
                        st.warning("Order declined")
                        st.rerun()
    
    with tab2:
        st.subheader("Serve Prepared Orders")
        completed_orders = get_orders_by_status("Completed")
        
        if completed_orders.empty:
            st.info("No orders ready to serve yet")
        else:
            token_numbers = completed_orders['TokenNumber'].unique()
            for token in token_numbers:
                token_orders = completed_orders[completed_orders['TokenNumber'] == token]
                customer_name = token_orders.iloc[0]['Name']
                
                with st.expander(f"Token {token} - {customer_name}"):
                    st.write("**Order Summary:**")
                    for _, row in token_orders.iterrows():
                        st.write(f"- {row['Item']} x{row['Quantity']} (₹{row['TotalPrice']})")
                    
                    total = token_orders['TotalPrice'].sum()
                    st.write(f"**Total: ₹{total}**")
                    
                    if st.button("Mark as Delivered", key=f"serve_{token}"):
                        for _, row in token_orders.iterrows():
                            update_order_status(row['OrderID'], "Delivered")
                        st.success(f"Order for Token {token} marked as delivered!")
                        st.rerun()

elif page == "Cook":
    st.header("Kitchen - Prepare Orders")
    password = st.text_input("Enter password", type="password")
    if password != PASSWORD:
        st.warning("Incorrect password")
        st.stop()
    
    orders = get_orders_by_status("Pending")
    if orders.empty:
        st.info("No orders to prepare - all caught up!")
    else:
        for _, row in orders.iterrows():
            with st.expander(f"Token {row['TokenNumber']} - {row['Item']} x{row['Quantity']}"):
                st.write(f"**Customer:** {row['Name']}")
                st.write(f"**Notes:** {row['AddOns']}")
                if st.button("Mark as Prepared", key=f"cook_{row['OrderID']}"):
                    update_order_status(row['OrderID'], "Completed")
                    st.success("Order marked as ready to serve!")
                    st.rerun()

elif page == "Track Order":
    st.header("Track Your Order")
    
    # Create a form to maintain the token input
    with st.form("track_order_form"):
        token = st.text_input("Enter your token number to track your order", key="track_token")
        submitted = st.form_submit_button("Track")
    
    # Display area that will auto-update
    track_placeholder = st.empty()
    
    # Function to display order status
    def display_order_status():
        if token:
            orders = get_orders_by_token(token)
            if not orders.empty:
                with track_placeholder.container():
                    st.write(f"### Order Status for Token `{token}`")
                    st.dataframe(orders[["Item", "Quantity", "Status", "TotalPrice"]])
                    
                    # Display summary information
                    total_items = orders['Quantity'].sum()
                    total_price = orders['TotalPrice'].sum()
                    current_status = orders.iloc[0]['Status']
                    
                    st.write("### Order Summary")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Items", total_items)
                    with col2:
                        st.metric("Total Amount", f"₹{total_price}")
                    with col3:
                        st.metric("Current Status", current_status)
                    
                    # Show status progress
                    status_flow = ["Unapproved", "Pending", "Completed", "Delivered"]
                    try:
                        current_index = status_flow.index(current_status)
                        progress = (current_index + 1) / len(status_flow)
                        st.progress(int(progress * 100))
                    except ValueError:
                        st.write("Status: Unknown")
            else:
                with track_placeholder.container():
                    st.warning("No order found with this token number.")
    
    # Initial display
    if submitted or token:
        display_order_status()
    
    # Auto-refresh only the results
    if page == "Track Order":
        st_autorefresh(
            interval=5000, 
            key="track_order_refresh",
            limit=100,
            debounce=True,
            on_refresh=display_order_status
        )

elif page == "Admin Dashboard":
    st.header("Admin Dashboard")
    password = st.text_input("Enter admin password", type="password")
    if password != ADMIN_PASSWORD:
        st.warning("Incorrect password")
        st.stop()
    df = get_all_orders()
    st.subheader("📊 Orders Overview")
    st.dataframe(df, use_container_width=True)
    st.subheader("⬇️ Export or 🧹 Clear Data")
    col1, col2 = st.columns(2)
    with col1:
        st.download_button("Export Orders as Excel", 
                         data=export_to_excel(), 
                         file_name="coffee_orders_export.xlsx")
    with col2:
        if st.button("Clear All Orders"):
            clear_database()
            st.success("All orders have been cleared.")
            st.rerun()
    st.subheader("📈 Quick Stats")
    stats = get_order_stats()
    st.write(f"Total Orders: {stats['total']}")
    st.write(f"Unapproved: {stats['unapproved']}, Pending: {stats['pending']}")
    st.write(f"Cooked: {stats['completed']}, Delivered: {stats['delivered']}, Declined: {stats['declined']}")
