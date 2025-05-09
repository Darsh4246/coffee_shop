import pandas as pd
from datetime import datetime
import uuid

# Path to the Excel file
EXCEL_FILE = "coffee_orders.xlsx"

# Initialize the Excel file with headers if it doesn't exist
def initialize_excel():
    try:
        pd.read_excel(EXCEL_FILE)
    except FileNotFoundError:
        df = pd.DataFrame(columns=[
            "OrderID", "OrderTime", "Status", "Details"
        ])
        df.to_excel(EXCEL_FILE, index=False)

# Add a new order
def create_order(details):
    df = pd.read_excel(EXCEL_FILE)
    new_order = {
        "OrderID": str(uuid.uuid4()),
        "OrderTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Status": "Pending",
        "Details": details
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

# Serve order (marks as Delivered)
def serve_order(order_id):
    update_order_status(order_id, "Delivered")

# Cook order (marks as Completed)
def cook_order(order_id):
    update_order_status(order_id, "Completed")

# Call this to initialize Excel file once
initialize_excel()

# Basic CLI for testing
def main():
    while True:
        print("\n--- Coffee Shop Order System ---")
        print("1. Take new order")
        print("2. Show pending orders")
        print("3. Mark order as cooked")
        print("4. Mark order as delivered")
        print("5. Exit")

        choice = input("Enter your choice: ")

        if choice == "1":
            details = input("Enter order details: ")
            order_id = create_order(details)
            print(f"Order placed. Order ID: {order_id}")

        elif choice == "2":
            pending = get_orders_by_status("Pending")
            print("\nPending Orders:")
            print(pending if not pending.empty else "No pending orders.")

        elif choice == "3":
            order_id = input("Enter Order ID to mark as cooked: ")
            cook_order(order_id)
            print("Order marked as cooked.")

        elif choice == "4":
            order_id = input("Enter Order ID to mark as delivered: ")
            serve_order(order_id)
            print("Order marked as delivered.")

        elif choice == "5":
            print("Exiting...")
            break

        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
