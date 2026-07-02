from datetime import datetime
from db_manager import DatabaseManager

class Transaction:
    def __init__(self, id_, type_, amount, category, date, notes="", profile="Personal"):
        self.id = id_
        self.type = type_  # 'Income' or 'Expense'
        self.amount = float(amount)
        self.category = category
        self.date = date  # YYYY-MM-DD
        self.notes = notes
        self.profile = profile

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "amount": self.amount,
            "category": self.category,
            "date": self.date,
            "notes": self.notes,
            "profile": self.profile
        }

    def __repr__(self):
        return f"Transaction({self.type}, ₹{self.amount}, {self.category}, {self.date}, Profile: {self.profile})"


class SavingGoal:
    def __init__(self, id_, name, target_amount, current_savings, target_date):
        self.id = id_
        self.name = name
        self.target_amount = float(target_amount)
        self.current_savings = float(current_savings)
        self.target_date = target_date  # YYYY-MM-DD

    @property
    def progress_percentage(self):
        if self.target_amount <= 0:
            return 0.0
        pct = (self.current_savings / self.target_amount) * 100.0
        return min(round(pct, 2), 100.0)

    @property
    def is_completed(self):
        return self.current_savings >= self.target_amount

    def days_remaining(self):
        try:
            target_dt = datetime.strptime(self.target_date, "%Y-%m-%d").date()
            today = datetime.now().date()
            delta = (target_dt - today).days
            return max(delta, 0)
        except Exception:
            return 0

    def __repr__(self):
        return f"SavingGoal({self.name}, Goal: ₹{self.target_amount}, Saved: ₹{self.current_savings})"


class Subscription:
    def __init__(self, id_, name, amount, billing_cycle, renewal_date):
        self.id = id_
        self.name = name
        self.amount = float(amount)
        self.billing_cycle = billing_cycle  # 'Monthly' or 'Yearly'
        self.renewal_date = renewal_date  # YYYY-MM-DD

    def days_until_renewal(self):
        try:
            renewal_dt = datetime.strptime(self.renewal_date, "%Y-%m-%d").date()
            today = datetime.now().date()
            delta = (renewal_dt - today).days
            return delta  # Can be negative if overdue
        except Exception:
            return 999

    def __repr__(self):
        return f"Subscription({self.name}, ₹{self.amount}, Next: {self.renewal_date})"


class BudgetTracker:
    def __init__(self, db_manager=None):
        self.db = db_manager if db_manager else DatabaseManager()
        self.budget_limit = 50000.0  # Default budget limit
        self.business_budget_limit = 100000.0  # Default business budget limit
        self.load_budget_limit()

    def load_budget_limit(self):
        # We can store the budget limit in a small settings.json file to keep it persistent.
        import json
        try:
            if os.path.exists("settings.json"):
                with open("settings.json", "r") as f:
                    settings = json.load(f)
                    self.budget_limit = float(settings.get("budget_limit", 50000.0))
                    self.business_budget_limit = float(settings.get("business_budget_limit", 100000.0))
        except Exception:
            pass

    def save_budget_limit(self, limit):
        import json
        self.budget_limit = float(limit)
        try:
            settings = {}
            if os.path.exists("settings.json"):
                with open("settings.json", "r") as f:
                    settings = json.load(f)
            settings["budget_limit"] = self.budget_limit
            with open("settings.json", "w") as f:
                json.dump(settings, f)
        except Exception:
            pass

    def save_business_budget_limit(self, limit):
        import json
        self.business_budget_limit = float(limit)
        try:
            settings = {}
            if os.path.exists("settings.json"):
                with open("settings.json", "r") as f:
                    settings = json.load(f)
            settings["business_budget_limit"] = self.business_budget_limit
            with open("settings.json", "w") as f:
                json.dump(settings, f)
        except Exception:
            pass

    # --- Transaction OOP Interfaces ---
    def add_transaction(self, type_, amount, category, date, notes="", profile="Personal"):
        return self.db.add_transaction(type_, amount, category, date, notes, profile)

    def get_transactions(self):
        rows = self.db.get_all_transactions()
        return [Transaction(*row) for row in rows]

    def delete_transaction(self, id_):
        self.db.delete_transaction(id_)

    def update_transaction(self, id_, type_, amount, category, date, notes="", profile="Personal"):
        self.db.update_transaction(id_, type_, amount, category, date, notes, profile)

    def get_categories(self):
        # Default categories for expenses
        return ["Food", "Shopping", "Bills & Utilities", "Rent", "Entertainment", "Travel", "Health & Fitness", "Others"]

    def get_business_categories(self, type_):
        if type_ == "Revenue":
            return ["Sales", "Services", "Consulting", "Royalties", "Others"]
        elif type_ == "COGS":
            return ["Inventory", "Raw Materials", "Shipping & Logistics", "Subcontractors", "Others"]
        else: # Operating Expense (OpEx)
            return ["Marketing & Ads", "Salaries & Payroll", "Office Rent", "Software & Tools", "Utilities", "Others"]

    # --- Saving Goals OOP Interfaces ---
    def add_goal(self, name, target_amount, current_savings, target_date):
        self.db.add_goal(name, target_amount, current_savings, target_date)

    def get_goals(self):
        rows = self.db.get_goals()
        return [SavingGoal(*row) for row in rows]

    def update_goal_savings(self, id_, current_savings):
        self.db.update_goal(id_, current_savings)

    def delete_goal(self, id_):
        self.db.delete_goal(id_)

    # --- Subscriptions OOP Interfaces ---
    def add_subscription(self, name, amount, billing_cycle, renewal_date):
        self.db.add_subscription(name, amount, billing_cycle, renewal_date)

    def get_subscriptions(self):
        rows = self.db.get_subscriptions()
        return [Subscription(*row) for row in rows]

    def delete_subscription(self, id_):
        self.db.delete_subscription(id_)
        
    def check_subscription_renewals(self):
        # Checks if subscriptions are due and handles dates (automatically moves overdue ones)
        # For simplicity, we just return the list of subscriptions ordered by days remaining.
        return sorted(self.get_subscriptions(), key=lambda s: s.days_until_renewal())

    # --- Product Suggestion interface ---
    def get_shopping_suggestions(self, item_keyword):
        return self.db.get_suggestions(item_keyword)
