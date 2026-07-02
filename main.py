import sys
from datetime import datetime, timedelta, date
from db_manager import DatabaseManager
from gui_app import SmartBudgetTrackerApp

def seed_sample_data(db):
    """
    Seeds database with realistic sample transactions, saving goals, and
    subscriptions for the current month so the UI displays graphs and metrics out-of-the-box.
    """
    import json
    import os
    
    seeded_flag = False
    try:
        if os.path.exists("settings.json"):
            with open("settings.json", "r") as f:
                settings = json.load(f)
                seeded_flag = settings.get("seeded", False)
    except Exception:
        pass
        
    if seeded_flag:
        return

    conn = db.get_connection()
    cursor = conn.cursor()

    # Check if personal transactions are empty
    cursor.execute("SELECT COUNT(*) FROM transactions WHERE profile = 'Personal'")
    personal_count = cursor.fetchone()[0]

    # Check if business transactions are empty
    cursor.execute("SELECT COUNT(*) FROM transactions WHERE profile = 'Business'")
    business_count = cursor.fetchone()[0]

    today = date.today()
    curr_yr = today.year
    curr_mo = today.month

    to_insert = []

    if personal_count == 0:
        print("Seeding sample personal transactions...")
        to_insert.extend([
            # Personal Incomes
            ("Income", 85000.0, "Salary", f"{curr_yr}-{curr_mo:02d}-01", "Monthly Corporate Salary", "Personal"),
            ("Income", 12000.0, "Freelance", f"{curr_yr}-{curr_mo:02d}-15", "Web Development Freelance Gig", "Personal"),
            
            # Personal Expenses
            ("Expense", 16000.0, "Rent", f"{curr_yr}-{curr_mo:02d}-02", "Apartment monthly rent payment", "Personal"),
            ("Expense", 4200.0, "Food", f"{curr_yr}-{curr_mo:02d}-04", "Weekly organic grocery shopping", "Personal"),
            ("Expense", 3200.0, "Bills & Utilities", f"{curr_yr}-{curr_mo:02d}-07", "Electricity and optical fiber internet bill", "Personal"),
            ("Expense", 649.0, "Bills & Utilities", f"{curr_yr}-{curr_mo:02d}-10", "Netflix monthly premium renewal", "Personal"),
            ("Expense", 2500.0, "Entertainment", f"{curr_yr}-{curr_mo:02d}-12", "Concert tickets and beverages", "Personal"),
            ("Expense", 5800.0, "Shopping", f"{curr_yr}-{curr_mo:02d}-16", "Zara summer jackets and clothes", "Personal"),
            ("Expense", 3100.0, "Travel", f"{curr_yr}-{curr_mo:02d}-19", "Petrol and highway tolls for weekend getaway", "Personal"),
            ("Expense", 1500.0, "Health & Fitness", f"{curr_yr}-{curr_mo:02d}-21", "Gym monthly access pass", "Personal"),
            ("Expense", 1950.0, "Food", f"{curr_yr}-{curr_mo:02d}-23", "Dinner date with office colleagues", "Personal"),
            ("Expense", 850.0, "Others", f"{curr_yr}-{curr_mo:02d}-25", "Laundry services", "Personal"),
        ])
        
        # Also add a couple of records from last month to enable Spending Insights trends!
        prev_yr, prev_mo = (curr_yr - 1, 12) if curr_mo == 1 else (curr_yr, curr_mo - 1)
        to_insert.extend([
            ("Income", 85000.0, "Salary", f"{prev_yr}-{prev_mo:02d}-01", "Salary", "Personal"),
            ("Expense", 16000.0, "Rent", f"{prev_yr}-{prev_mo:02d}-02", "Rent", "Personal"),
            ("Expense", 3800.0, "Food", f"{prev_yr}-{prev_mo:02d}-05", "Groceries", "Personal"),
            ("Expense", 6800.0, "Shopping", f"{prev_yr}-{prev_mo:02d}-15", "Winter jackets", "Personal"),
            ("Expense", 2800.0, "Bills & Utilities", f"{prev_yr}-{prev_mo:02d}-07", "Internet", "Personal"),
        ])

    if business_count == 0:
        print("Seeding sample business transactions...")
        to_insert.extend([
            # Business Revenues (Incomes)
            ("Income", 150000.0, "Sales", f"{curr_yr}-{curr_mo:02d}-02", "Product Sales Revenue", "Business"),
            ("Income", 45000.0, "Services", f"{curr_yr}-{curr_mo:02d}-10", "Consulting Fee Client A", "Business"),
            
            # Business COGS Expenses
            ("Expense", 35000.0, "Inventory", f"{curr_yr}-{curr_mo:02d}-03", "Bulk warehouse packaging purchase", "Business"),
            ("Expense", 8500.0, "Shipping & Logistics", f"{curr_yr}-{curr_mo:02d}-06", "FedEx delivery services", "Business"),
            
            # Business OpEx Expenses
            ("Expense", 12000.0, "Marketing & Ads", f"{curr_yr}-{curr_mo:02d}-05", "Facebook & Instagram Ads campaign", "Business"),
            ("Expense", 18000.0, "Office Rent", f"{curr_yr}-{curr_mo:02d}-01", "Co-working space desk rental", "Business"),
            ("Expense", 25000.0, "Salaries & Payroll", f"{curr_yr}-{curr_mo:02d}-25", "Freelance assistant monthly salary", "Business"),
            ("Expense", 4500.0, "Software & Tools", f"{curr_yr}-{curr_mo:02d}-12", "Google Workspace & Slack tools subscription", "Business")
        ])

    if to_insert:
        cursor.executemany("""
            INSERT INTO transactions (type, amount, category, date, notes, profile)
            VALUES (?, ?, ?, ?, ?, ?)
        """, to_insert)
        conn.commit()

    # Check if goals table is empty
    cursor.execute("SELECT COUNT(*) FROM saving_goals")
    goal_count = cursor.fetchone()[0]

    if goal_count == 0:
        print("Seeding sample savings goals...")
        today = date.today()
        # Compute dates in future
        date_6mo = (today + timedelta(days=180)).strftime("%Y-%m-%d")
        date_12mo = (today + timedelta(days=365)).strftime("%Y-%m-%d")
        date_3mo = (today + timedelta(days=90)).strftime("%Y-%m-%d")

        sample_goals = [
            ("MacBook Pro 16", 140000.0, 55000.0, date_6mo),
            ("Europe Summer Tour", 150000.0, 45000.0, date_12mo),
            ("Emergency Safety Reserve", 60000.0, 30000.0, date_3mo)
        ]
        cursor.executemany("""
            INSERT INTO saving_goals (name, target_amount, current_savings, target_date)
            VALUES (?, ?, ?, ?)
        """, sample_goals)
        conn.commit()

    # Check if subscriptions table is empty
    cursor.execute("SELECT COUNT(*) FROM subscriptions")
    sub_count = cursor.fetchone()[0]

    if sub_count == 0:
        print("Seeding sample subscriptions...")
        today = date.today()
        
        # Next renewal dates
        date_netflix = (today + timedelta(days=4)).strftime("%Y-%m-%d")
        date_spotify = (today + timedelta(days=12)).strftime("%Y-%m-%d")
        date_prime = (today + timedelta(days=45)).strftime("%Y-%m-%d")

        sample_subs = [
            ("Netflix Premium", 649.0, "Monthly", date_netflix),
            ("Spotify Premium Duo", 179.0, "Monthly", date_spotify),
            ("Amazon Prime Membership", 1499.0, "Yearly", date_prime)
        ]
        cursor.executemany("""
            INSERT INTO subscriptions (name, amount, billing_cycle, renewal_date)
            VALUES (?, ?, ?, ?)
        """, sample_subs)
        conn.commit()

    conn.close()

    # Save initialized flag to settings
    try:
        settings = {}
        if os.path.exists("settings.json"):
            with open("settings.json", "r") as f:
                settings = json.load(f)
        settings["seeded"] = True
        with open("settings.json", "w") as f:
            json.dump(settings, f)
    except Exception:
        pass


def main():
    print("=========================================================")
    print("Smart Budget Tracker & Personal Finance Assistant Booter")
    print("=========================================================")
    
    # 1. Initialize DB Manager
    try:
        db = DatabaseManager()
        # Seed Mock Data to display beautiful graphs on startup
        seed_sample_data(db)
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to instantiate database: {e}")
        sys.exit(1)

    # 2. Boot Tkinter Dashboard App
    print("Loading UI Interface Frame...")
    try:
        app = SmartBudgetTrackerApp()
        print("Application window loaded successfully. Main loop running.")
        app.mainloop()
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to load Tkinter UI engine: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()