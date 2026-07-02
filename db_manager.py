import sqlite3
import os

class DatabaseManager:
    def __init__(self, db_name="finance_assistant.db"):
        self.db_name = db_name
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_name)

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        # Create Transactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL CHECK(type IN ('Income', 'Expense')),
                amount REAL NOT NULL CHECK(amount > 0),
                category TEXT NOT NULL,
                date TEXT NOT NULL, -- YYYY-MM-DD
                notes TEXT,
                profile TEXT DEFAULT 'Personal'
            )
        """)

        # Create Saving Goals table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS saving_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                target_amount REAL NOT NULL CHECK(target_amount > 0),
                current_savings REAL NOT NULL DEFAULT 0.0 CHECK(current_savings >= 0),
                target_date TEXT NOT NULL -- YYYY-MM-DD
            )
        """)

        # Create Subscriptions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                billing_cycle TEXT NOT NULL DEFAULT 'Monthly',
                renewal_date TEXT NOT NULL -- YYYY-MM-DD
            )
        """)

        # Create Smart Product Suggestions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS smart_suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT NOT NULL,
                alternative_store TEXT NOT NULL,
                alternative_price REAL NOT NULL CHECK(alternative_price > 0)
            )
        """)

        # Create Business Sales table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS business_sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                customer_name TEXT NOT NULL,
                invoice_no TEXT,
                amount REAL NOT NULL CHECK(amount >= 0),
                payment_method TEXT NOT NULL
            )
        """)

        # Create Business Expenses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS business_expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount >= 0),
                notes TEXT
            )
        """)

        # Create Inventory table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT NOT NULL UNIQUE,
                stock INTEGER NOT NULL DEFAULT 0 CHECK(stock >= 0),
                sold INTEGER NOT NULL DEFAULT 0 CHECK(sold >= 0)
            )
        """)

        # Create Customers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                phone TEXT,
                pending_amount REAL NOT NULL DEFAULT 0.0 CHECK(pending_amount >= 0),
                paid_amount REAL NOT NULL DEFAULT 0.0 CHECK(paid_amount >= 0),
                due_date TEXT
            )
        """)

        # Create Vendors table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vendors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier_name TEXT NOT NULL,
                amount_payable REAL NOT NULL CHECK(amount_payable >= 0),
                due_date TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('Paid', 'Unpaid'))
            )
        """)

        # Create Employee Salaries table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employee_salaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_name TEXT NOT NULL,
                salary REAL NOT NULL CHECK(salary >= 0),
                paid_amount REAL NOT NULL DEFAULT 0.0 CHECK(paid_amount >= 0),
                pending_amount REAL NOT NULL DEFAULT 0.0 CHECK(pending_amount >= 0)
            )
        """)

        # Run Database migrations
        try:
            cursor.execute("ALTER TABLE transactions ADD COLUMN profile TEXT DEFAULT 'Personal'")
            conn.commit()
        except sqlite3.OperationalError:
            pass

        conn.commit()

        # Seed initial smart suggestions if empty
        cursor.execute("SELECT COUNT(*) FROM smart_suggestions")
        if cursor.fetchone()[0] == 0:
            mock_suggestions = [
                # Laptops
                ("Laptop", "Amazon", 45000.0),
                ("Laptop", "Croma", 48000.0),
                ("MacBook", "Reliance Digital", 78000.0),
                ("MacBook", "Amazon", 75000.0),
                # Phones
                ("iPhone 15", "Flipkart", 65999.0),
                ("iPhone 15", "Croma", 67000.0),
                ("Samsung S24", "Amazon", 69999.0),
                ("Samsung S24", "Samsung Store", 71999.0),
                # Shoes
                ("Nike Shoes", "Myntra", 3500.0),
                ("Adidas Shoes", "Ajio", 2999.0),
                # Electronics
                ("Sony XM4", "Amazon", 18990.0),
                ("Sony XM4", "Headphone Zone", 17990.0),
                ("iPad", "Amazon", 29999.0),
                ("iPad", "Croma", 31500.0),
                ("Smart Watch", "Flipkart", 4500.0),
                ("Smart Watch", "Amazon", 4200.0)
            ]
            cursor.executemany("""
                INSERT INTO smart_suggestions (item_name, alternative_store, alternative_price)
                VALUES (?, ?, ?)
            """, mock_suggestions)
            conn.commit()

        conn.close()

    # --- Transactions CRUD ---
    def add_transaction(self, type_, amount, category, date, notes="", profile="Personal"):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO transactions (type, amount, category, date, notes, profile)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (type_, amount, category, date, notes, profile))
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id

    def get_all_transactions(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, type, amount, category, date, notes, profile FROM transactions ORDER BY date DESC, id DESC")
        rows = cursor.fetchall()
        conn.close()
        return rows

    def search_transactions(self, keyword=None, category=None, date=None, profile=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        query = "SELECT id, type, amount, category, date, notes, profile FROM transactions WHERE 1=1"
        params = []
        if keyword:
            query += " AND (category LIKE ? OR notes LIKE ?)"
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        if category:
            query += " AND category = ?"
            params.append(category)
        if date:
            query += " AND date = ?"
            params.append(date)
        if profile:
            query += " AND profile = ?"
            params.append(profile)
        
        query += " ORDER BY date DESC, id DESC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return rows

    def update_transaction(self, id_, type_, amount, category, date, notes="", profile="Personal"):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE transactions
            SET type = ?, amount = ?, category = ?, date = ?, notes = ?, profile = ?
            WHERE id = ?
        """, (type_, amount, category, date, notes, profile, id_))
        conn.commit()
        conn.close()

    def delete_transaction(self, id_):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transactions WHERE id = ?", (id_,))
        conn.commit()
        conn.close()

    # --- Saving Goals CRUD ---
    def add_goal(self, name, target_amount, current_savings, target_date):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO saving_goals (name, target_amount, current_savings, target_date)
            VALUES (?, ?, ?, ?)
        """, (name, target_amount, current_savings, target_date))
        conn.commit()
        conn.close()

    def get_goals(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, target_amount, current_savings, target_date FROM saving_goals ORDER BY target_date ASC")
        rows = cursor.fetchall()
        conn.close()
        return rows

    def update_goal(self, id_, current_savings):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE saving_goals
            SET current_savings = ?
            WHERE id = ?
        """, (current_savings, id_))
        conn.commit()
        conn.close()

    def delete_goal(self, id_):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM saving_goals WHERE id = ?", (id_,))
        conn.commit()
        conn.close()

    # --- Subscriptions CRUD ---
    def add_subscription(self, name, amount, billing_cycle, renewal_date):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO subscriptions (name, amount, billing_cycle, renewal_date)
            VALUES (?, ?, ?, ?)
        """, (name, amount, billing_cycle, renewal_date))
        conn.commit()
        conn.close()

    def get_subscriptions(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, amount, billing_cycle, renewal_date FROM subscriptions ORDER BY renewal_date ASC")
        rows = cursor.fetchall()
        conn.close()
        return rows

    def update_subscription_date(self, id_, next_renewal_date):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE subscriptions
            SET renewal_date = ?
            WHERE id = ?
        """, (next_renewal_date, id_))
        conn.commit()
        conn.close()

    def delete_subscription(self, id_):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM subscriptions WHERE id = ?", (id_,))
        conn.commit()
        conn.close()

    # --- Smart Product Suggestions ---
    def get_suggestions(self, item_keyword):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT alternative_store, alternative_price 
            FROM smart_suggestions 
            WHERE item_name LIKE ?
            ORDER BY alternative_price ASC
        """, (f"%{item_keyword}%",))
        rows = cursor.fetchall()
        conn.close()
        return rows

    # --- Business Sales CRUD ---
    def add_business_sale(self, date, customer_name, invoice_no, amount, payment_method):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO business_sales (date, customer_name, invoice_no, amount, payment_method)
            VALUES (?, ?, ?, ?, ?)
        """, (date, customer_name, invoice_no, amount, payment_method))
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id

    def get_all_business_sales(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, date, customer_name, invoice_no, amount, payment_method FROM business_sales ORDER BY date DESC, id DESC")
        rows = cursor.fetchall()
        conn.close()
        return rows

    def delete_business_sale(self, id_):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM business_sales WHERE id = ?", (id_,))
        conn.commit()
        conn.close()

    # --- Business Expenses CRUD ---
    def add_business_expense(self, date, category, amount, notes=""):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO business_expenses (date, category, amount, notes)
            VALUES (?, ?, ?, ?)
        """, (date, category, amount, notes))
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id

    def get_all_business_expenses(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, date, category, amount, notes FROM business_expenses ORDER BY date DESC, id DESC")
        rows = cursor.fetchall()
        conn.close()
        return rows

    def delete_business_expense(self, id_):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM business_expenses WHERE id = ?", (id_,))
        conn.commit()
        conn.close()

    # --- Inventory CRUD ---
    def add_inventory_item(self, item_name, stock, sold=0):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO inventory (item_name, stock, sold)
                VALUES (?, ?, ?)
            """, (item_name, stock, sold))
            conn.commit()
        except sqlite3.IntegrityError:
            cursor.execute("""
                UPDATE inventory 
                SET stock = stock + ? 
                WHERE item_name = ?
            """, (stock, item_name))
            conn.commit()
        conn.close()

    def update_inventory_item(self, id_, stock, sold):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE inventory
            SET stock = ?, sold = ?
            WHERE id = ?
        """, (stock, sold, id_))
        conn.commit()
        conn.close()

    def get_all_inventory(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, item_name, stock, sold FROM inventory ORDER BY item_name ASC")
        rows = cursor.fetchall()
        conn.close()
        return rows

    def delete_inventory_item(self, id_):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM inventory WHERE id = ?", (id_,))
        conn.commit()
        conn.close()

    # --- Customers CRUD ---
    def add_customer(self, customer_name, phone, pending_amount, paid_amount, due_date):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO customers (customer_name, phone, pending_amount, paid_amount, due_date)
            VALUES (?, ?, ?, ?, ?)
        """, (customer_name, phone, pending_amount, paid_amount, due_date))
        conn.commit()
        conn.close()

    def update_customer_payment(self, id_, pending_amount, paid_amount):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE customers
            SET pending_amount = ?, paid_amount = ?
            WHERE id = ?
        """, (pending_amount, paid_amount, id_))
        conn.commit()
        conn.close()

    def get_all_customers(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, customer_name, phone, pending_amount, paid_amount, due_date FROM customers ORDER BY customer_name ASC")
        rows = cursor.fetchall()
        conn.close()
        return rows

    def delete_customer(self, id_):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM customers WHERE id = ?", (id_,))
        conn.commit()
        conn.close()

    # --- Vendors CRUD ---
    def add_vendor(self, supplier_name, amount_payable, due_date, status):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO vendors (supplier_name, amount_payable, due_date, status)
            VALUES (?, ?, ?, ?)
        """, (supplier_name, amount_payable, due_date, status))
        conn.commit()
        conn.close()

    def update_vendor_status(self, id_, status):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE vendors
            SET status = ?
            WHERE id = ?
        """, (status, id_))
        conn.commit()
        conn.close()

    def get_all_vendors(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, supplier_name, amount_payable, due_date, status FROM vendors ORDER BY due_date ASC")
        rows = cursor.fetchall()
        conn.close()
        return rows

    def delete_vendor(self, id_):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM vendors WHERE id = ?", (id_,))
        conn.commit()
        conn.close()

    # --- Employee Salaries CRUD ---
    def add_employee_salary(self, employee_name, salary, paid_amount, pending_amount):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO employee_salaries (employee_name, salary, paid_amount, pending_amount)
            VALUES (?, ?, ?, ?)
        """, (employee_name, salary, paid_amount, pending_amount))
        conn.commit()
        conn.close()

    def update_employee_payment(self, id_, paid_amount, pending_amount):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE employee_salaries
            SET paid_amount = ?, pending_amount = ?
            WHERE id = ?
        """, (paid_amount, pending_amount, id_))
        conn.commit()
        conn.close()

    def get_all_employee_salaries(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, employee_name, salary, paid_amount, pending_amount FROM employee_salaries ORDER BY employee_name ASC")
        rows = cursor.fetchall()
        conn.close()
        return rows

    def delete_employee_salary(self, id_):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM employee_salaries WHERE id = ?", (id_,))
        conn.commit()
        conn.close()
