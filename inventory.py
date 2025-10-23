import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import pandas as pd
from datetime import datetime
import os

DB_NAME = "inventory.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS suppliers (
            supplier_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            contact TEXT,
            email TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS stock (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT,
            supplier_id INTEGER,
            qty INTEGER,
            price REAL,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS purchase_orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER,
            supplier_id INTEGER,
            qty INTEGER,
            order_date TEXT,
            FOREIGN KEY (item_id) REFERENCES stock(item_id),
            FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
        )
    """)
    conn.commit()
    conn.close()


class InventoryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Inventory Management System - Gadgets Trade")
        self.root.geometry("1100x700")
        self.root.configure(bg="#f5f6fa")

        # Title
        title = tk.Label(root, text="📦 Inventory Management System",
                         font=("Segoe UI", 22, "bold"), bg="#004aad", fg="white", pady=15)
        title.pack(fill="x")

        self.tabs = ttk.Notebook(root)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=10)

        self.create_stock_tab()
        self.create_supplier_tab()
        self.create_order_tab()

    # ---------- STOCK TAB ---------- #
    def create_stock_tab(self):
        stock_tab = tk.Frame(self.tabs, bg="#f5f6fa")
        self.tabs.add(stock_tab, text="Stock Management")

        # Fields
        form = tk.LabelFrame(stock_tab, text="Add / Update Stock", font=("Segoe UI", 12, "bold"),
                             bg="#f5f6fa", padx=10, pady=10)
        form.pack(fill="x", pady=10)

        tk.Label(form, text="Item Name:", font=("Segoe UI", 11), bg="#f5f6fa").grid(row=0, column=0, padx=10)
        tk.Label(form, text="Supplier ID:", font=("Segoe UI", 11), bg="#f5f6fa").grid(row=0, column=1, padx=10)
        tk.Label(form, text="Quantity:", font=("Segoe UI", 11), bg="#f5f6fa").grid(row=0, column=2, padx=10)
        tk.Label(form, text="Price:", font=("Segoe UI", 11), bg="#f5f6fa").grid(row=0, column=3, padx=10)

        self.item_name = tk.Entry(form, font=("Segoe UI", 11), justify="center", width=25)
        self.supplier_id = tk.Entry(form, font=("Segoe UI", 11), justify="center", width=10)
        self.item_qty = tk.Entry(form, font=("Segoe UI", 11), justify="center", width=10)
        self.item_price = tk.Entry(form, font=("Segoe UI", 11), justify="center", width=10)

        self.item_name.grid(row=1, column=0, padx=10, pady=5)
        self.supplier_id.grid(row=1, column=1, padx=10, pady=5)
        self.item_qty.grid(row=1, column=2, padx=10, pady=5)
        self.item_price.grid(row=1, column=3, padx=10, pady=5)

        tk.Button(form, text="Add / Update", command=self.add_update_stock, bg="#004aad", fg="white",
                  font=("Segoe UI", 11, "bold"), width=15).grid(row=1, column=4, padx=10)
        tk.Button(form, text="Delete", command=self.delete_stock, bg="#dc3545", fg="white",
                  font=("Segoe UI", 11, "bold"), width=10).grid(row=1, column=5, padx=10)

        # Table
        self.stock_tree = ttk.Treeview(stock_tab, columns=("ID", "Item", "Supplier", "Qty", "Price"),
                                       show="headings", height=12)
        for col in self.stock_tree["columns"]:
            self.stock_tree.heading(col, text=col)
            self.stock_tree.column(col, width=150, anchor="center")
        self.stock_tree.pack(fill="both", expand=True, pady=10)

        tk.Button(stock_tab, text="Export to Excel", command=self.export_stock_excel, bg="#28a745", fg="white",
                  font=("Segoe UI", 11, "bold"), width=18).pack(pady=5)

        self.load_stock()
        self.check_low_stock()

    def add_update_stock(self):
        name = self.item_name.get()
        supplier = self.supplier_id.get()
        qty = self.item_qty.get()
        price = self.item_price.get()
        if not (name and supplier and qty and price):
            messagebox.showwarning("Input Error", "Please fill all fields.")
            return
        try:
            qty = int(qty)
            price = float(price)
        except ValueError:
            messagebox.showerror("Error", "Invalid quantity or price.")
            return
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT item_id FROM stock WHERE item_name=?", (name,))
        row = cur.fetchone()
        if row:
            cur.execute("UPDATE stock SET qty=?, price=?, supplier_id=? WHERE item_name=?",
                        (qty, price, supplier, name))
        else:
            cur.execute("INSERT INTO stock (item_name, supplier_id, qty, price) VALUES (?, ?, ?, ?)",
                        (name, supplier, qty, price))
        conn.commit()
        conn.close()
        self.load_stock()
        messagebox.showinfo("Success", "Stock updated successfully.")
        self.clear_stock_fields()

    def delete_stock(self):
        selected = self.stock_tree.focus()
        if not selected:
            messagebox.showwarning("Select Item", "Please select an item to delete.")
            return
        item = self.stock_tree.item(selected)["values"]
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("DELETE FROM stock WHERE item_id=?", (item[0],))
        conn.commit()
        conn.close()
        self.load_stock()
        messagebox.showinfo("Deleted", f"Item '{item[1]}' deleted successfully.")

    def load_stock(self):
        for row in self.stock_tree.get_children():
            self.stock_tree.delete(row)
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT * FROM stock")
        rows = cur.fetchall()
        for row in rows:
            self.stock_tree.insert("", "end", values=row)
        conn.close()

    def check_low_stock(self):
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT item_name, qty FROM stock WHERE qty < 10")
        low_stock = cur.fetchall()
        conn.close()
        if low_stock:
            alert_text = "\n".join([f"{item} - Qty: {qty}" for item, qty in low_stock])
            messagebox.showwarning("Low Stock Alert", f"The following items are low in stock:\n\n{alert_text}")

    def clear_stock_fields(self):
        self.item_name.delete(0, tk.END)
        self.supplier_id.delete(0, tk.END)
        self.item_qty.delete(0, tk.END)
        self.item_price.delete(0, tk.END)

    def export_stock_excel(self):
        conn = sqlite3.connect(DB_NAME)
        df = pd.read_sql_query("SELECT * FROM stock", conn)
        conn.close()
        file = "Stock_Report.xlsx"
        df.to_excel(file, index=False)
        messagebox.showinfo("Exported", f"Stock report saved as {file}")

    # ---------- SUPPLIER TAB ---------- #
    def create_supplier_tab(self):
        supplier_tab = tk.Frame(self.tabs, bg="#f5f6fa")
        self.tabs.add(supplier_tab, text="Suppliers")

        form = tk.LabelFrame(supplier_tab, text="Add Supplier", font=("Segoe UI", 12, "bold"),
                             bg="#f5f6fa", padx=10, pady=10)
        form.pack(fill="x", pady=10)
        tk.Label(form, text="Name:", font=("Segoe UI", 11), bg="#f5f6fa").grid(row=0, column=0, padx=10)
        tk.Label(form, text="Contact:", font=("Segoe UI", 11), bg="#f5f6fa").grid(row=0, column=1, padx=10)
        tk.Label(form, text="Email:", font=("Segoe UI", 11), bg="#f5f6fa").grid(row=0, column=2, padx=10)
        self.sup_name = tk.Entry(form, font=("Segoe UI", 11), justify="center", width=25)
        self.sup_contact = tk.Entry(form, font=("Segoe UI", 11), justify="center", width=15)
        self.sup_email = tk.Entry(form, font=("Segoe UI", 11), justify="center", width=25)
        self.sup_name.grid(row=1, column=0, padx=10, pady=5)
        self.sup_contact.grid(row=1, column=1, padx=10, pady=5)
        self.sup_email.grid(row=1, column=2, padx=10, pady=5)
        tk.Button(form, text="Add Supplier", command=self.add_supplier, bg="#004aad", fg="white",
                  font=("Segoe UI", 11, "bold"), width=15).grid(row=1, column=3, padx=10)

        self.supplier_tree = ttk.Treeview(supplier_tab, columns=("ID", "Name", "Contact", "Email"),
                                          show="headings", height=12)
        for col in self.supplier_tree["columns"]:
            self.supplier_tree.heading(col, text=col)
            self.supplier_tree.column(col, width=200, anchor="center")
        self.supplier_tree.pack(fill="both", expand=True, pady=10)

        tk.Button(supplier_tab, text="Export to Excel", command=self.export_suppliers_excel, bg="#28a745", fg="white",
                  font=("Segoe UI", 11, "bold"), width=18).pack(pady=5)
        self.load_suppliers()

    def add_supplier(self):
        name, contact, email = self.sup_name.get(), self.sup_contact.get(), self.sup_email.get()
        if not name:
            messagebox.showwarning("Input Error", "Supplier name required.")
            return
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("INSERT INTO suppliers (name, contact, email) VALUES (?, ?, ?)", (name, contact, email))
        conn.commit()
        conn.close()
        self.load_suppliers()
        messagebox.showinfo("Success", "Supplier added successfully.")
        self.sup_name.delete(0, tk.END)
        self.sup_contact.delete(0, tk.END)
        self.sup_email.delete(0, tk.END)

    def load_suppliers(self):
        for row in self.supplier_tree.get_children():
            self.supplier_tree.delete(row)
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT * FROM suppliers")
        rows = cur.fetchall()
        for row in rows:
            self.supplier_tree.insert("", "end", values=row)
        conn.close()

    def export_suppliers_excel(self):
        conn = sqlite3.connect(DB_NAME)
        df = pd.read_sql_query("SELECT * FROM suppliers", conn)
        conn.close()
        file = "Suppliers_Report.xlsx"
        df.to_excel(file, index=False)
        messagebox.showinfo("Exported", f"Supplier report saved as {file}")

    # ---------- PURCHASE ORDERS TAB ---------- #
    def create_order_tab(self):
        order_tab = tk.Frame(self.tabs, bg="#f5f6fa")
        self.tabs.add(order_tab, text="Purchase Orders")

        form = tk.LabelFrame(order_tab, text="Add Purchase Order", font=("Segoe UI", 12, "bold"),
                             bg="#f5f6fa", padx=10, pady=10)
        form.pack(fill="x", pady=10)

        tk.Label(form, text="Item ID:", font=("Segoe UI", 11), bg="#f5f6fa").grid(row=0, column=0, padx=10)
        tk.Label(form, text="Supplier ID:", font=("Segoe UI", 11), bg="#f5f6fa").grid(row=0, column=1, padx=10)
        tk.Label(form, text="Quantity:", font=("Segoe UI", 11), bg="#f5f6fa").grid(row=0, column=2, padx=10)

        self.order_item = tk.Entry(form, font=("Segoe UI", 11), justify="center", width=15)
        self.order_supplier = tk.Entry(form, font=("Segoe UI", 11), justify="center", width=15)
        self.order_qty = tk.Entry(form, font=("Segoe UI", 11), justify="center", width=15)

        self.order_item.grid(row=1, column=0, padx=10, pady=5)
        self.order_supplier.grid(row=1, column=1, padx=10, pady=5)
        self.order_qty.grid(row=1, column=2, padx=10, pady=5)

        tk.Button(form, text="Record Order", command=self.record_order, bg="#004aad", fg="white",
                  font=("Segoe UI", 11, "bold"), width=15).grid(row=1, column=3, padx=10)

        self.order_tree = ttk.Treeview(order_tab, columns=("Order ID", "Item ID", "Supplier ID", "Qty", "Date"),
                                       show="headings", height=12)
        for col in self.order_tree["columns"]:
            self.order_tree.heading(col, text=col)
            self.order_tree.column(col, width=150, anchor="center")
        self.order_tree.pack(fill="both", expand=True, pady=10)

        self.load_orders()

    def record_order(self):
        item, supplier, qty = self.order_item.get(), self.order_supplier.get(), self.order_qty.get()
        if not (item and supplier and qty):
            messagebox.showwarning("Input Error", "Please fill all fields.")
            return
        try:
            qty = int(qty)
        except ValueError:
            messagebox.showerror("Error", "Invalid quantity.")
            return
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("INSERT INTO purchase_orders (item_id, supplier_id, qty, order_date) VALUES (?, ?, ?, ?)",
                    (item, supplier, qty, datetime.now().strftime("%Y-%m-%d")))
        cur.execute("UPDATE stock SET qty = qty + ? WHERE item_id = ?", (qty, item))
        conn.commit()
        conn.close()
        self.load_orders()
        self.load_stock()
        messagebox.showinfo("Success", "Purchase order recorded and stock updated.")

    def load_orders(self):
        for row in self.order_tree.get_children():
            self.order_tree.delete(row)
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT * FROM purchase_orders")
        rows = cur.fetchall()
        for row in rows:
            self.order_tree.insert("", "end", values=row)
        conn.close()


if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    app = InventoryApp(root)
    root.mainloop()
