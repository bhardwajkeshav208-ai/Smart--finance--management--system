import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from datetime import datetime, date
import shutil
import os
import pandas as pd
import numpy as np

# Matplotlib integration
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

# Custom modules
import gui_theme as theme
from tracker_oop import BudgetTracker
import analytics
from pdf_generator import PDFReportGenerator
import ml_engine
import gui_ai_view

def clean_amount_str(val_str):
    if not val_str:
        return "0"
    return val_str.replace(",", "").replace("₹", "").replace(" ", "").strip()



class ScrollableFrame(tk.Frame):
    """
    A robust scrollable container using Canvas and Scrollbar.
    """
    def __init__(self, container, bg_color=theme.BG_MAIN, *args, **kwargs):
        super().__init__(container, bg=bg_color, *args, **kwargs)
        self.canvas = tk.Canvas(self, bg=bg_color, bd=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=bg_color)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        self.bind("<Configure>", self._on_frame_configure)
        
    def _on_frame_configure(self, event):
        # Resize scrollable frame width to match canvas width
        self.canvas.itemconfig(self.canvas_window, width=event.width)


class SmartBudgetTrackerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FINSIGHT - Smart Finance & Business Management System")
        self.geometry("1180x780")
        self.configure(bg=theme.BG_MAIN)
        self.resizable(True, True)

        # Initialize Finance Tracker OOP Controller
        self.tracker = BudgetTracker()

        # Initialize Machine Learning NLP Categorizer
        self.nlp_categorizer = ml_engine.ExpenseCategorizerNLP()
        try:
            self.nlp_categorizer.train_on_history(self.tracker.db.get_connection())
        except Exception:
            pass

        # Apply Styles
        theme.setup_ttk_styles()

        # Sidebar navigation index
        self.current_page = None
        self.pages = {}

        # Selected transaction ID for editing
        self.selected_transaction_id = None

        self.setup_ui()
        self.switch_page("landing")

    def setup_ui(self):
        # Master Layout: Sidebar + Main Content Frame
        self.sidebar = tk.Frame(self, bg=theme.BG_SIDEBAR, width=220, bd=0)
        # Note: self.sidebar packing is managed dynamically in switch_page
        
        self.content_container = tk.Frame(self, bg=theme.BG_MAIN)
        self.content_container.pack(side="right", fill="both", expand=True)

        self.nav_buttons = {}

        # Pre-instantiate Pages
        self.pages["landing"] = self.create_landing_page()
        self.pages["dashboard"] = self.create_dashboard_page()
        self.pages["transactions"] = self.create_transactions_page()
        self.pages["goals"] = self.create_goals_page()
        self.pages["subscriptions"] = self.create_subscriptions_page()
        self.pages["suggestions"] = self.create_suggestions_page()
        self.pages["exports"] = self.create_exports_page()
        self.pages["ai_insights"] = gui_ai_view.create_ai_insights_page(self)
        
        # Business Pages
        self.pages["biz_dashboard"] = self.create_biz_dashboard_page()
        self.pages["biz_sales"] = self.create_biz_sales_page()
        self.pages["biz_expenses"] = self.create_biz_expenses_page()
        self.pages["biz_pl"] = self.create_biz_pl_page()
        self.pages["biz_inventory"] = self.create_biz_inventory_page()
        self.pages["biz_customers"] = self.create_biz_customers_page()
        self.pages["biz_vendors"] = self.create_biz_vendors_page()
        self.pages["biz_monthly"] = self.create_biz_monthly_page()
        self.pages["biz_gst"] = self.create_biz_gst_page()
        self.pages["biz_cashflow"] = self.create_biz_cashflow_page()
        self.pages["biz_payroll"] = self.create_biz_payroll_page()
        self.pages["biz_invoice"] = self.create_biz_invoice_page()

    def switch_page(self, page_name):
        if self.current_page:
            self.pages[self.current_page].pack_forget()
            if self.current_page in self.nav_buttons:
                self.nav_buttons[self.current_page].configure(bg=theme.BG_SIDEBAR, fg=theme.TEXT_MUTED)

        self.current_page = page_name
        
        if page_name == "landing":
            self.sidebar.pack_forget()
            self.content_container.pack_forget()
            self.content_container.pack(side="right", fill="both", expand=True)
        else:
            self.sidebar.pack_forget()
            self.content_container.pack_forget()
            self.sidebar.pack(side="left", fill="y")
            self.content_container.pack(side="right", fill="both", expand=True)
            
        self.pages[page_name].pack(fill="both", expand=True)
        if page_name in self.nav_buttons:
            self.nav_buttons[page_name].configure(bg=theme.BG_CARD, fg=theme.ACCENT)

        # Refresh page data when switching to it
        self.refresh_page_data(page_name)

    def quick_add_transaction(self, type_val):
        # Switch to transactions tab
        self.switch_page("transactions")
        # Reset any active form selection
        self.clear_tx_form()
        # Set the target type (Income/Expense)
        self.tx_type_var.set(type_val)
        self.on_tx_type_change()
        # Focus on amount box for fast typing
        self.tx_amt_entry.focus_set()


    def refresh_page_data(self, page_name):
        # Refresh OOP database models
        transactions = self.tracker.get_transactions()
        df = analytics.load_dataframe(transactions)
        
        if page_name == "dashboard":
            self.refresh_dashboard(df, transactions)
        elif page_name == "transactions":
            self.refresh_transactions_table(transactions)
        elif page_name == "goals":
            self.refresh_goals()
        elif page_name == "subscriptions":
            self.refresh_subscriptions()
        elif page_name == "exports":
            self.refresh_exports(df)
        elif page_name == "ai_insights":
            self.refresh_ai_insights()
        elif page_name.startswith("biz_"):
            self.refresh_biz_page(page_name)

    # ==========================================
    # --- DASHBOARD PAGE ---
    # ==========================================
    def create_dashboard_page(self):
        page = ScrollableFrame(self.content_container)
        frame = page.scrollable_frame

        # Page Header
        top_bar = tk.Frame(frame, bg=theme.BG_MAIN)
        top_bar.pack(fill="x", padx=25, pady=20)
        
        title = tk.Label(top_bar, text="Financial Dashboard", font=theme.FONT_TITLE, fg=theme.TEXT_PRIMARY, bg=theme.BG_MAIN)
        title.pack(side="left")

        # Top section: Executive Cards & Gauge
        top_grid = tk.Frame(frame, bg=theme.BG_MAIN)
        top_grid.pack(fill="x", padx=25, pady=5)

        # Left Column for Cards (Income, Expense, Balance)
        self.cards_frame = tk.Frame(top_grid, bg=theme.BG_MAIN)
        self.cards_frame.pack(side="left", fill="both", expand=True)
        self.cards_frame.columnconfigure(0, weight=1)
        self.cards_frame.columnconfigure(1, weight=1)

        # Stat cards (Custom styled labels inside Card canvases)
        self.income_card = theme.Card(self.cards_frame, width=220, height=90)
        self.income_card.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        self.income_lbl = tk.Label(self.income_card, text="TOTAL INCOME\n₹0.00", font=theme.FONT_BODY_BOLD, fg=theme.INCOME, bg=theme.BG_CARD)
        self.income_lbl.place(relx=0.5, rely=0.32, anchor="center")
        
        self.income_add_btn = tk.Button(
            self.income_card,
            text="+ Add Income",
            font=theme.FONT_SMALL,
            fg=theme.TEXT_DARK,
            bg=theme.INCOME,
            activebackground=theme.INCOME,
            bd=0,
            cursor="hand2",
            padx=8,
            command=lambda: self.quick_add_transaction("Income")
        )
        self.income_add_btn.place(relx=0.5, rely=0.72, anchor="center")

        self.expense_card = theme.Card(self.cards_frame, width=220, height=90)
        self.expense_card.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        self.expense_lbl = tk.Label(self.expense_card, text="TOTAL EXPENSE\n₹0.00", font=theme.FONT_BODY_BOLD, fg=theme.EXPENSE, bg=theme.BG_CARD)
        self.expense_lbl.place(relx=0.5, rely=0.32, anchor="center")
        
        self.expense_add_btn = tk.Button(
            self.expense_card,
            text="+ Add Expense",
            font=theme.FONT_SMALL,
            fg=theme.TEXT_PRIMARY,
            bg=theme.EXPENSE,
            activebackground=theme.EXPENSE,
            bd=0,
            cursor="hand2",
            padx=8,
            command=lambda: self.quick_add_transaction("Expense")
        )
        self.expense_add_btn.place(relx=0.5, rely=0.72, anchor="center")

        self.balance_card = theme.Card(self.cards_frame, width=220, height=80)
        self.balance_card.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        self.balance_lbl = tk.Label(self.balance_card, text="CURRENT BALANCE\n₹0.00", font=theme.FONT_SUBTITLE, fg=theme.TEXT_PRIMARY, bg=theme.BG_CARD)
        self.balance_lbl.place(relx=0.5, rely=0.5, anchor="center")

        # Right Column for Health Score circular gauge
        gauge_container = theme.Card(top_grid, width=200, height=170)
        gauge_container.pack(side="right", padx=10, pady=5)
        
        self.gauge = theme.CircularGauge(gauge_container, size=150)
        self.gauge.place(relx=0.5, rely=0.5, anchor="center")

        # Mid section: Budget Alert Progress bar
        budget_card = theme.Card(frame, width=680, height=110)
        budget_card.pack(fill="x", padx=25, pady=15)
        
        # Labels for budget card
        self.budget_limit_lbl = tk.Label(
            budget_card, 
            text="Monthly Budget Limit: ₹0.00", 
            font=theme.FONT_BODY_BOLD, 
            fg=theme.TEXT_PRIMARY, 
            bg=theme.BG_CARD
        )
        self.budget_limit_lbl.place(x=20, y=15)

        self.budget_alert_lbl = tk.Label(
            budget_card, 
            text="Status: Normal (0% used)", 
            font=theme.FONT_BODY_BOLD, 
            fg=theme.INCOME, 
            bg=theme.BG_CARD
        )
        self.budget_alert_lbl.place(relx=0.95, y=15, anchor="ne")

        # Budget limit configuration button
        set_budget_btn = tk.Button(
            budget_card,
            text="⚙ Set Limit",
            font=theme.FONT_SMALL,
            fg=theme.ACCENT,
            bg=theme.BG_CARD,
            bd=1,
            relief="solid",
            highlightthickness=0,
            cursor="hand2",
            command=self.configure_budget_limit
        )
        set_budget_btn.place(x=220, y=14)

        # Progress bar (ttk styled)
        self.budget_progress = ttk.Progressbar(budget_card, orient="horizontal", mode="determinate")
        self.budget_progress.place(x=20, y=55, relwidth=0.94)

        self.budget_spent_lbl = tk.Label(
            budget_card, 
            text="Spent: ₹0.00 | Remaining: ₹0.00", 
            font=theme.FONT_SMALL, 
            fg=theme.TEXT_MUTED, 
            bg=theme.BG_CARD
        )
        self.budget_spent_lbl.place(x=20, y=82)


        # Bottom section: Charts Panel
        self.chart_card = theme.Card(frame, width=680, height=360)
        self.chart_card.pack(fill="both", expand=True, padx=25, pady=10)
        
        chart_title = tk.Label(self.chart_card, text="Spending Visualizations", font=theme.FONT_SUBTITLE, fg=theme.TEXT_PRIMARY, bg=theme.BG_CARD)
        chart_title.pack(pady=10, anchor="w", padx=20)
        
        self.chart_container = tk.Frame(self.chart_card, bg=theme.BG_CARD)
        self.chart_container.pack(fill="both", expand=True, padx=10, pady=10)

        return page

    def configure_budget_limit(self):
        # Open a small dialog to input budget limit
        dialog = tk.Toplevel(self)
        dialog.title("Set Budget Limit")
        dialog.geometry("300x150")
        dialog.configure(bg=theme.BG_MAIN)
        dialog.transient(self)
        dialog.grab_set()

        lbl = tk.Label(dialog, text="Enter Monthly Budget Limit (₹):", font=theme.FONT_BODY_BOLD, fg=theme.TEXT_PRIMARY, bg=theme.BG_MAIN)
        lbl.pack(pady=15)

        entry = tk.Entry(dialog, font=theme.FONT_BODY, bg=theme.BG_CARD, fg=theme.TEXT_PRIMARY, insertbackground="white")
        entry.insert(0, str(int(self.tracker.budget_limit)))
        entry.pack(pady=5)
        entry.focus_set()

        def save():
            try:
                val = float(clean_amount_str(entry.get()))
                if val <= 0:
                    raise ValueError
                self.tracker.save_budget_limit(val)
                dialog.destroy()
                self.refresh_page_data("dashboard")
            except ValueError:
                messagebox.showerror("Error", "Please enter a positive numeric value.", parent=dialog)

        btn = tk.Button(dialog, text="Save Settings", font=theme.FONT_BODY_BOLD, bg=theme.ACCENT, fg=theme.TEXT_DARK, activebackground=theme.ACCENT, bd=0, command=save)
        btn.pack(pady=15)

    def refresh_dashboard(self, df, transactions):
        today = date.today()
        summary = analytics.get_monthly_summary(df, today.year, today.month)
        
        # 1. Update text fields
        self.income_lbl.configure(text=f"TOTAL INCOME\n₹{summary['income']:,.2f}")
        self.expense_lbl.configure(text=f"TOTAL EXPENSE\n₹{summary['expense']:,.2f}")
        
        balance = summary["income"] - summary["expense"]
        bal_color = theme.INCOME if balance >= 0 else theme.EXPENSE
        self.balance_lbl.configure(text=f"CURRENT BALANCE\n₹{balance:,.2f}", fg=bal_color)

        # 2. Update health circular gauge
        goals = self.tracker.get_goals()
        subs = self.tracker.get_subscriptions()
        health = analytics.calculate_health_score(df, self.tracker.budget_limit, goals, subs)
        self.gauge.set_score(health["score"], health["status"], health["color"])

        # 3. Update budget status card
        spent = summary["expense"]
        limit = self.tracker.budget_limit
        pct = (spent / limit * 100) if limit > 0 else 100
        
        self.budget_limit_lbl.configure(text=f"Monthly Budget Limit: ₹{limit:,.2f}")
        
        # Color coding alert
        if pct >= 90:
            alert_text = f"🚨 Red Alert! ({pct:.1f}% used)"
            alert_color = theme.EXPENSE
        elif pct >= 70:
            alert_text = f"⚠️ Yellow Alert! ({pct:.1f}% used)"
            alert_color = theme.WARNING
        else:
            alert_text = f"✅ Normal ({pct:.1f}% used)"
            alert_color = theme.INCOME
            
        self.budget_alert_lbl.configure(text=alert_text, fg=alert_color)
        self.budget_progress["value"] = min(pct, 100.0)
        
        rem = max(0.0, limit - spent)
        self.budget_spent_lbl.configure(text=f"Spent: ₹{spent:,.2f} | Remaining: ₹{rem:,.2f}")

        # 4. Render embedded Matplotlib charts
        # Clear container
        for child in self.chart_container.winfo_children():
            child.destroy()

        if df.empty or spent == 0:
            lbl = tk.Label(self.chart_container, text="No expenses recorded this month yet.\nAdd expenses under the 'Transactions' tab to see visual graphs.", font=theme.FONT_BODY, fg=theme.TEXT_MUTED, bg=theme.BG_CARD)
            lbl.pack(expand=True)
            return

        try:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 3.2), facecolor=theme.BG_CARD)
            
            # --- Chart 1: Expenses Pie Chart ---
            cat_spending = analytics.get_category_wise_spending(df, today.year, today.month)
            if cat_spending:
                categories = list(cat_spending.keys())
                amounts = list(cat_spending.values())
                colors_list = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#6b7280']
                
                wedges, texts, autotexts = ax1.pie(
                    amounts, 
                    labels=categories, 
                    autopct='%1.0f%%', 
                    startangle=140, 
                    colors=colors_list[:len(categories)],
                    textprops=dict(color=theme.TEXT_PRIMARY)
                )
                # Style inner percent labels
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontsize(8)
                ax1.set_title("Expense Distribution", color=theme.TEXT_PRIMARY, fontdict={'fontsize': 10, 'weight': 'bold'})
            else:
                ax1.text(0.5, 0.5, 'No Expense Data', ha='center', va='center', color=theme.TEXT_MUTED)
                ax1.axis('off')

            # --- Chart 2: Income vs Expense Bar Chart ---
            # Group recent 3 months to show trends
            monthly_data = df.groupby(["year", "month", "type"])["amount"].sum().unstack(fill_value=0)
            
            # Reindex to make sure Income & Expense columns exist
            for col in ["Income", "Expense"]:
                if col not in monthly_data.columns:
                    monthly_data[col] = 0.0

            # Get the last 3 months
            monthly_data = monthly_data.tail(3)
            
            # Format labels as 'MMM YY'
            x_labels = []
            for idx in monthly_data.index:
                yr, mo = idx
                month_name = datetime(yr, mo, 1).strftime("%b %y")
                x_labels.append(month_name)

            x = range(len(x_labels))
            width = 0.35

            if len(x_labels) > 0:
                ax2.bar([i - width/2 for i in x], monthly_data["Income"], width, label='Income', color=theme.INCOME)
                ax2.bar([i + width/2 for i in x], monthly_data["Expense"], width, label='Expense', color=theme.EXPENSE)
                
                ax2.set_xticks(x)
                ax2.set_xticklabels(x_labels, color=theme.TEXT_PRIMARY)
                ax2.tick_params(colors=theme.TEXT_MUTED, labelsize=8)
                ax2.yaxis.grid(True, linestyle='--', alpha=0.1, color='white')
                ax2.legend(facecolor=theme.BG_CARD, edgecolor=theme.BORDER, labelcolor=theme.TEXT_PRIMARY, fontsize=7)
                ax2.set_title("Income vs Expense Trend", color=theme.TEXT_PRIMARY, fontdict={'fontsize': 10, 'weight': 'bold'})
                
                # Style spines
                for spine in ax2.spines.values():
                    spine.set_color(theme.BORDER)
            else:
                ax2.text(0.5, 0.5, 'No Trends Data', ha='center', va='center', color=theme.TEXT_MUTED)
                ax2.axis('off')

            fig.tight_layout()
            
            # Draw on Tkinter canvas
            canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
            plt.close(fig)
        except Exception as e:
            # Fallback label in case mathplotlib throws error
            lbl = tk.Label(self.chart_container, text=f"Charts are loading... ({str(e)})", font=theme.FONT_BODY, fg=theme.TEXT_MUTED, bg=theme.BG_CARD)
            lbl.pack(expand=True)

    # ==========================================
    # --- TRANSACTIONS PAGE ---
    # ==========================================
    def create_transactions_page(self):
        page = tk.Frame(self.content_container, bg=theme.BG_MAIN)

        # Page Header
        top_bar = tk.Frame(page, bg=theme.BG_MAIN)
        top_bar.pack(fill="x", padx=25, pady=20)
        title = tk.Label(top_bar, text="Transaction History & Entry", font=theme.FONT_TITLE, fg=theme.TEXT_PRIMARY, bg=theme.BG_MAIN)
        title.pack(side="left")

        # Two-column layout: Form (left 350px) + Table (right expanded)
        main_layout = tk.Frame(page, bg=theme.BG_MAIN)
        main_layout.pack(fill="both", expand=True, padx=25, pady=5)

        # --- Left Panel: Transaction Input Form ---
        form_card = theme.Card(main_layout, width=320, height=530)
        form_card.pack(side="left", fill="y", padx=(0, 15))
        form_card.pack_propagate(False)

        form_title = tk.Label(form_card, text="📝 Record Transaction", font=theme.FONT_SUBTITLE, fg=theme.TEXT_PRIMARY, bg=theme.BG_CARD)
        form_title.pack(pady=15, padx=20, anchor="w")

        # Transaction type
        tk.Label(form_card, text="Type", font=theme.FONT_BODY_BOLD, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).pack(anchor="w", padx=20)
        self.tx_type_var = tk.StringVar(value="Expense")
        self.tx_type_cmb = ttk.Combobox(form_card, textvariable=self.tx_type_var, values=["Income", "Expense"], state="readonly", width=35)
        self.tx_type_cmb.pack(pady=5, padx=20)
        self.tx_type_cmb.bind("<<ComboboxSelected>>", self.on_tx_type_change)

        # Category
        tk.Label(form_card, text="Category", font=theme.FONT_BODY_BOLD, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).pack(anchor="w", padx=20, pady=(5,0))
        self.tx_cat_var = tk.StringVar()
        self.tx_cat_cmb = ttk.Combobox(form_card, textvariable=self.tx_cat_var, values=self.tracker.get_categories(), width=35)
        self.tx_cat_cmb.pack(pady=5, padx=20)

        # Amount
        tk.Label(form_card, text="Amount (₹)", font=theme.FONT_BODY_BOLD, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).pack(anchor="w", padx=20, pady=(5,0))
        self.tx_amt_entry = tk.Entry(form_card, font=theme.FONT_BODY, bg=theme.BG_MAIN, fg=theme.TEXT_PRIMARY, insertbackground="white", bd=1, relief="solid")
        self.tx_amt_entry.pack(pady=5, padx=20, fill="x")

        # Date
        tk.Label(form_card, text="Date (YYYY-MM-DD)", font=theme.FONT_BODY_BOLD, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).pack(anchor="w", padx=20, pady=(5,0))
        self.tx_date_entry = tk.Entry(form_card, font=theme.FONT_BODY, bg=theme.BG_MAIN, fg=theme.TEXT_PRIMARY, insertbackground="white", bd=1, relief="solid")
        self.tx_date_entry.insert(0, date.today().strftime("%Y-%m-%d"))
        self.tx_date_entry.pack(pady=5, padx=20, fill="x")

        # Notes
        tk.Label(form_card, text="Notes", font=theme.FONT_BODY_BOLD, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).pack(anchor="w", padx=20, pady=(5,0))
        self.tx_notes_entry = tk.Entry(form_card, font=theme.FONT_BODY, bg=theme.BG_MAIN, fg=theme.TEXT_PRIMARY, insertbackground="white", bd=1, relief="solid")
        self.tx_notes_entry.pack(pady=5, padx=20, fill="x")

        # AI Auto-Categorize Indicator Label
        self.tx_ai_lbl = tk.Label(form_card, text="🤖 AI: Type notes for auto-category", font=("Segoe UI", 9, "italic"), fg=theme.ACCENT, bg=theme.BG_CARD)
        self.tx_ai_lbl.pack(anchor="w", padx=20, pady=(2, 0))
        self.tx_notes_entry.bind("<KeyRelease>", self.on_tx_notes_change)

        # Buttons
        btn_frame = tk.Frame(form_card, bg=theme.BG_CARD)
        btn_frame.pack(pady=20, padx=20, fill="x")

        self.btn_submit_tx = tk.Button(
            btn_frame, 
            text="Save Record", 
            font=theme.FONT_BODY_BOLD, 
            bg=theme.ACCENT, 
            fg=theme.TEXT_DARK, 
            activebackground=theme.ACCENT, 
            bd=0, 
            cursor="hand2", 
            command=self.save_transaction
        )
        self.btn_submit_tx.pack(side="left", fill="x", expand=True, padx=(0,5))

        self.btn_clear_tx = tk.Button(
            btn_frame, 
            text="Reset", 
            font=theme.FONT_BODY_BOLD, 
            bg="#374151", 
            fg=theme.TEXT_PRIMARY, 
            activebackground="#4b5563", 
            bd=0, 
            cursor="hand2", 
            command=self.clear_tx_form
        )
        self.btn_clear_tx.pack(side="right", fill="x", expand=True, padx=(5,0))

        # --- Right Panel: Ledger Search & Table ---
        right_panel = tk.Frame(main_layout, bg=theme.BG_MAIN)
        right_panel.pack(side="right", fill="both", expand=True)

        # Filters Bar
        filter_card = theme.Card(right_panel, width=500, height=60)
        filter_card.pack(fill="x", pady=(0, 10))
        filter_card.pack_propagate(False)

        tk.Label(filter_card, text="🔍 Filter:", font=theme.FONT_BODY_BOLD, fg=theme.TEXT_PRIMARY, bg=theme.BG_CARD).pack(side="left", padx=(15,5))
        
        self.filter_key_var = tk.StringVar()
        self.filter_key_entry = tk.Entry(filter_card, textvariable=self.filter_key_var, font=theme.FONT_BODY, bg=theme.BG_MAIN, fg=theme.TEXT_PRIMARY, insertbackground="white", bd=1, relief="solid", width=18)
        self.filter_key_entry.pack(side="left", padx=5, pady=15)
        self.filter_key_var.trace_add("write", lambda *args: self.apply_filters())

        tk.Label(filter_card, text="Category:", font=theme.FONT_BODY_BOLD, fg=theme.TEXT_PRIMARY, bg=theme.BG_CARD).pack(side="left", padx=(10,5))
        self.filter_cat_var = tk.StringVar(value="All")
        self.filter_cat_cmb = ttk.Combobox(filter_card, textvariable=self.filter_cat_var, values=["All"] + self.tracker.get_categories() + ["Salary", "Investments", "Others"], state="readonly", width=12)
        self.filter_cat_cmb.pack(side="left", padx=5, pady=15)
        self.filter_cat_cmb.bind("<<ComboboxSelected>>", lambda e: self.apply_filters())

        # Clear Filters button
        btn_reset_filters = tk.Button(
            filter_card,
            text="Clear",
            font=theme.FONT_SMALL,
            fg=theme.TEXT_PRIMARY,
            bg="#374151",
            bd=0,
            cursor="hand2",
            padx=10,
            command=self.reset_filters
        )
        btn_reset_filters.pack(side="right", padx=15, pady=15)

        # Table container card
        table_card = theme.Card(right_panel, width=500, height=380)
        table_card.pack(fill="both", expand=True)
        
        # Scrollbars and Treeview Table
        table_frame = tk.Frame(table_card, bg=theme.BG_CARD)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # columns definition
        columns = ("id", "type", "category", "amount", "date", "notes")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", style="Treeview")
        
        self.tree.heading("id", text="ID")
        self.tree.heading("type", text="Type")
        self.tree.heading("category", text="Category")
        self.tree.heading("amount", text="Amount (₹)")
        self.tree.heading("date", text="Date")
        self.tree.heading("notes", text="Notes")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("type", width=70, anchor="center")
        self.tree.column("category", width=100, anchor="w")
        self.tree.column("amount", width=90, anchor="e")
        self.tree.column("date", width=90, anchor="center")
        self.tree.column("notes", width=150, anchor="w")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview, style="Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self.on_row_select)

        # Actions buttons under table
        table_actions = tk.Frame(right_panel, bg=theme.BG_MAIN)
        table_actions.pack(fill="x", pady=10)

        self.btn_delete_tx = tk.Button(
            table_actions,
            text="❌ Delete Selected",
            font=theme.FONT_BODY_BOLD,
            fg=theme.TEXT_PRIMARY,
            bg=theme.EXPENSE,
            activebackground=theme.EXPENSE,
            bd=0,
            padx=15,
            pady=8,
            cursor="hand2",
            state="disabled",
            command=self.delete_selected_transaction
        )
        self.btn_delete_tx.pack(side="right", padx=5)

        return page

    def on_tx_type_change(self, event=None):
        # Dynamically change available categories in dropdown based on type selection
        t = self.tx_type_var.get()
        if t == "Income":
            self.tx_cat_cmb.configure(values=["Salary", "Investments", "Freelance", "Gifts", "Others"])
            self.tx_cat_var.set("Salary")
        else:
            self.tx_cat_cmb.configure(values=self.tracker.get_categories())
            self.tx_cat_var.set("Food")

    def clear_tx_form(self):
        self.selected_transaction_id = None
        self.tx_type_var.set("Expense")
        self.on_tx_type_change()
        self.tx_amt_entry.delete(0, tk.END)
        self.tx_date_entry.delete(0, tk.END)
        self.tx_date_entry.insert(0, date.today().strftime("%Y-%m-%d"))
        self.tx_notes_entry.delete(0, tk.END)
        if hasattr(self, 'tx_ai_lbl'):
            self.tx_ai_lbl.config(text="🤖 AI: Type notes for auto-category", fg=theme.TEXT_MUTED)
        self.btn_submit_tx.configure(text="Save Record", bg=theme.ACCENT)
        self.btn_delete_tx.configure(state="disabled")
        self.tree.selection_remove(self.tree.selection())

    def on_tx_notes_change(self, event=None):
        text = self.tx_notes_entry.get().strip()
        if len(text) >= 3 and hasattr(self, 'nlp_categorizer'):
            pred_cat, conf = self.nlp_categorizer.predict(text)
            if pred_cat and conf >= 40.0:
                self.tx_cat_var.set(pred_cat)
                self.tx_ai_lbl.config(text=f"🤖 AI Categorized: {pred_cat} ({conf}%)", fg=theme.ACCENT)
            else:
                self.tx_ai_lbl.config(text="🤖 AI: Analyzing...", fg=theme.TEXT_MUTED)
        elif not text and hasattr(self, 'tx_ai_lbl'):
            self.tx_ai_lbl.config(text="🤖 AI: Type notes for auto-category", fg=theme.TEXT_MUTED)

    def on_row_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        
        row_data = self.tree.item(selection[0], "values")
        self.selected_transaction_id = int(row_data[0])
        
        # Populate Form for updating
        self.tx_type_var.set(row_data[1])
        self.on_tx_type_change()
        self.tx_cat_var.set(row_data[2])
        
        # Extract numerical amount, strip currency symbol if present
        amt_str = row_data[3].replace("₹", "").replace(",", "")
        self.tx_amt_entry.delete(0, tk.END)
        self.tx_amt_entry.insert(0, amt_str)
        
        self.tx_date_entry.delete(0, tk.END)
        self.tx_date_entry.insert(0, row_data[4])
        
        self.tx_notes_entry.delete(0, tk.END)
        self.tx_notes_entry.insert(0, row_data[5] if row_data[5] != "-" else "")

        self.btn_submit_tx.configure(text="Update Record", bg=theme.WARNING)
        self.btn_delete_tx.configure(state="normal")

    def save_transaction(self):
        # Validate Form
        t_type = self.tx_type_var.get()
        cat = self.tx_cat_var.get().strip()
        amt_str = clean_amount_str(self.tx_amt_entry.get())
        dt_str = self.tx_date_entry.get().strip()
        notes = self.tx_notes_entry.get().strip()

        if not cat:
            messagebox.showerror("Validation Error", "Category is required.")
            return

        try:
            amt = float(amt_str)
            if amt <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Validation Error", "Please enter a valid positive number for amount.")
            return

        try:
            # Validate date format
            datetime.strptime(dt_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Validation Error", "Please enter a valid date in YYYY-MM-DD format.")
            return

        # Check budget alert dynamically when adding expenses
        if t_type == "Expense" and self.selected_transaction_id is None:
            # Recalculate how much budget would be spent
            transactions = self.tracker.get_transactions()
            df = analytics.load_dataframe(transactions)
            current_month_summary = analytics.get_monthly_summary(df, date.today().year, date.today().month)
            projected_spent = current_month_summary["expense"] + amt
            limit = self.tracker.budget_limit
            
            # Show a warning if exceeding
            if projected_spent >= limit:
                ans = messagebox.askyesno(
                    "⚠️ Budget Exceeded Alert", 
                    f"Warning: Adding this expense will exceed your monthly budget limit of ₹{limit:,.2f}.\n"
                    f"Projected Monthly Expenses: ₹{projected_spent:,.2f}\n"
                    f"Do you still want to proceed with recording this expense?",
                    icon="warning"
                )
                if not ans:
                    return

        # Insert or Update
        if self.selected_transaction_id is None:
            # Add
            self.tracker.add_transaction(t_type, amt, cat, dt_str, notes)
            messagebox.showinfo("Success", "Transaction added successfully!")
        else:
            # Update
            self.tracker.update_transaction(self.selected_transaction_id, t_type, amt, cat, dt_str, notes)
            messagebox.showinfo("Success", "Transaction updated successfully!")

        self.clear_tx_form()
        self.refresh_page_data("transactions")

    def delete_selected_transaction(self):
        if self.selected_transaction_id is None:
            return
        
        ans = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete the selected transaction?")
        if ans:
            self.tracker.delete_transaction(self.selected_transaction_id)
            messagebox.showinfo("Deleted", "Transaction deleted successfully.")
            self.clear_tx_form()
            self.refresh_page_data("transactions")

    def refresh_transactions_table(self, transactions):
        self.tree.delete(*self.tree.get_children())
        for t in transactions:
            notes = t.notes if t.notes else "-"
            # Display colored rows
            self.tree.insert("", "end", values=(t.id, t.type, t.category, f"₹{t.amount:,.2f}", t.date, notes))

    def apply_filters(self):
        key = self.filter_key_var.get().strip()
        cat = self.filter_cat_var.get()
        
        cat_filter = None if cat == "All" else cat
        key_filter = None if key == "" else key

        filtered_rows = self.tracker.db.search_transactions(keyword=key_filter, category=cat_filter)
        self.tree.delete(*self.tree.get_children())
        for row in filtered_rows:
            # row: (id, type, amount, category, date, notes)
            notes = row[5] if row[5] else "-"
            self.tree.insert("", "end", values=(row[0], row[1], row[3], f"₹{row[2]:,.2f}", row[4], notes))

    def reset_filters(self):
        self.filter_key_var.set("")
        self.filter_cat_var.set("All")
        self.refresh_page_data("transactions")

    # ==========================================
    # --- SAVING GOALS PAGE ---
    # ==========================================
    def create_goals_page(self):
        page = tk.Frame(self.content_container, bg=theme.BG_MAIN)

        # Header
        top_bar = tk.Frame(page, bg=theme.BG_MAIN)
        top_bar.pack(fill="x", padx=25, pady=20)
        title = tk.Label(top_bar, text="Saving Goal Tracker", font=theme.FONT_TITLE, fg=theme.TEXT_PRIMARY, bg=theme.BG_MAIN)
        title.pack(side="left")

        # Split: Left side Goals Card list, Right side Add Goal Form
        main_layout = tk.Frame(page, bg=theme.BG_MAIN)
        main_layout.pack(fill="both", expand=True, padx=25, pady=5)

        # Left: Goals List (Scrollable Frame)
        self.goals_list_container = ScrollableFrame(main_layout, bg_color=theme.BG_MAIN)
        self.goals_list_container.pack(side="left", fill="both", expand=True, padx=(0, 15))

        # Right: Add Goal Form
        form_card = theme.Card(main_layout, width=320, height=420)
        form_card.pack(side="right", fill="y")
        form_card.pack_propagate(False)

        form_title = tk.Label(form_card, text="🎯 Define New Savings Goal", font=theme.FONT_SUBTITLE, fg=theme.TEXT_PRIMARY, bg=theme.BG_CARD)
        form_title.pack(pady=15, padx=20, anchor="w")

        # Name
        tk.Label(form_card, text="Goal Name (e.g. Laptop, Bike)", font=theme.FONT_BODY_BOLD, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).pack(anchor="w", padx=20)
        self.goal_name_entry = tk.Entry(form_card, font=theme.FONT_BODY, bg=theme.BG_MAIN, fg=theme.TEXT_PRIMARY, insertbackground="white", bd=1, relief="solid")
        self.goal_name_entry.pack(pady=5, padx=20, fill="x")

        # Target
        tk.Label(form_card, text="Target Amount (₹)", font=theme.FONT_BODY_BOLD, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).pack(anchor="w", padx=20, pady=(5,0))
        self.goal_target_entry = tk.Entry(form_card, font=theme.FONT_BODY, bg=theme.BG_MAIN, fg=theme.TEXT_PRIMARY, insertbackground="white", bd=1, relief="solid")
        self.goal_target_entry.pack(pady=5, padx=20, fill="x")

        # Current Saved
        tk.Label(form_card, text="Current Savings (₹)", font=theme.FONT_BODY_BOLD, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).pack(anchor="w", padx=20, pady=(5,0))
        self.goal_saved_entry = tk.Entry(form_card, font=theme.FONT_BODY, bg=theme.BG_MAIN, fg=theme.TEXT_PRIMARY, insertbackground="white", bd=1, relief="solid")
        self.goal_saved_entry.pack(pady=5, padx=20, fill="x")

        # Target Date
        tk.Label(form_card, text="Target Date (YYYY-MM-DD)", font=theme.FONT_BODY_BOLD, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).pack(anchor="w", padx=20, pady=(5,0))
        self.goal_date_entry = tk.Entry(form_card, font=theme.FONT_BODY, bg=theme.BG_MAIN, fg=theme.TEXT_PRIMARY, insertbackground="white", bd=1, relief="solid")
        self.goal_date_entry.insert(0, date.today().replace(year=date.today().year + 1).strftime("%Y-%m-%d"))
        self.goal_date_entry.pack(pady=5, padx=20, fill="x")

        # Add Goal Button
        btn_add_goal = tk.Button(
            form_card, 
            text="Add Saving Goal", 
            font=theme.FONT_BODY_BOLD, 
            bg=theme.ACCENT, 
            fg=theme.TEXT_DARK, 
            activebackground=theme.ACCENT, 
            bd=0, 
            cursor="hand2", 
            command=self.save_goal
        )
        btn_add_goal.pack(pady=20, padx=20, fill="x")

        return page

    def save_goal(self):
        name = self.goal_name_entry.get().strip()
        target_str = clean_amount_str(self.goal_target_entry.get())
        saved_str = clean_amount_str(self.goal_saved_entry.get())
        dt_str = self.goal_date_entry.get().strip()

        if not name:
            messagebox.showerror("Validation Error", "Goal name is required.")
            return

        try:
            target = float(target_str)
            saved = float(saved_str) if saved_str else 0.0
            if target <= 0 or saved < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Validation Error", "Please enter positive numeric values for target and savings.")
            return

        try:
            datetime.strptime(dt_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Validation Error", "Please enter a valid target date (YYYY-MM-DD).")
            return

        # Add goal
        self.tracker.add_goal(name, target, saved, dt_str)
        messagebox.showinfo("Success", "Savings Goal defined successfully!")
        
        # Clear form
        self.goal_name_entry.delete(0, tk.END)
        self.goal_target_entry.delete(0, tk.END)
        self.goal_saved_entry.delete(0, tk.END)
        self.goal_date_entry.delete(0, tk.END)
        self.goal_date_entry.insert(0, date.today().replace(year=date.today().year + 1).strftime("%Y-%m-%d"))

        self.refresh_page_data("goals")

    def refresh_goals(self):
        # Clear list
        list_frame = self.goals_list_container.scrollable_frame
        for child in list_frame.winfo_children():
            child.destroy()

        goals = self.tracker.get_goals()

        if not goals:
            lbl = tk.Label(list_frame, text="No savings goals created yet.\nDefine a goal on the right panel to track your progress!", font=theme.FONT_BODY, fg=theme.TEXT_MUTED, bg=theme.BG_MAIN)
            lbl.pack(pady=100)
            return

        for g in goals:
            # Draw custom Card canvas for each goal
            card = theme.Card(list_frame, width=500, height=130)
            card.pack(fill="x", pady=8, padx=5)
            card.pack_propagate(False)

            title_lbl = tk.Label(card, text=f"🎯 {g.name}", font=theme.FONT_SUBTITLE, fg=theme.TEXT_PRIMARY, bg=theme.BG_CARD)
            title_lbl.place(x=20, y=12)

            days = g.days_remaining()
            status_text = f"Completed! 🎉" if g.is_completed else (f"Overdue" if days <= 0 else f"{days} days remaining")
            status_color = theme.INCOME if g.is_completed else (theme.EXPENSE if days <= 0 else theme.ACCENT)
            
            status_lbl = tk.Label(card, text=status_text, font=theme.FONT_SMALL, fg=status_color, bg=theme.BG_CARD)
            status_lbl.place(x=400, y=15)

            # Details
            details_text = f"Saved: ₹{g.current_savings:,.2f} of ₹{g.target_amount:,.2f} ({g.progress_percentage}%)"
            details_lbl = tk.Label(card, text=details_text, font=theme.FONT_BODY, fg=theme.TEXT_MUTED, bg=theme.BG_CARD)
            details_lbl.place(x=20, y=42)

            # Goal Progressbar
            progress = ttk.Progressbar(card, orient="horizontal", length=460, mode="determinate")
            progress["value"] = g.progress_percentage
            progress.place(x=20, y=70)

            # Actions inside the card
            btn_update = tk.Button(
                card,
                text="Update Savings",
                font=theme.FONT_SMALL,
                fg=theme.ACCENT,
                bg=theme.BG_CARD,
                bd=1,
                relief="solid",
                cursor="hand2",
                command=lambda id_=g.id, name=g.name, current=g.current_savings: self.update_goal_savings_dialog(id_, name, current)
            )
            btn_update.place(x=20, y=98)

            btn_delete = tk.Button(
                card,
                text="🗑 Delete Goal",
                font=theme.FONT_SMALL,
                fg=theme.EXPENSE,
                bg=theme.BG_CARD,
                bd=0,
                cursor="hand2",
                command=lambda id_=g.id: self.delete_goal(id_)
            )
            btn_delete.place(x=400, y=98)

    def update_goal_savings_dialog(self, goal_id, goal_name, current_val):
        dialog = tk.Toplevel(self)
        dialog.title(f"Update: {goal_name}")
        dialog.geometry("320x160")
        dialog.configure(bg=theme.BG_MAIN)
        dialog.transient(self)
        dialog.grab_set()

        lbl = tk.Label(dialog, text=f"Enter current savings for {goal_name} (₹):", font=theme.FONT_BODY_BOLD, fg=theme.TEXT_PRIMARY, bg=theme.BG_MAIN)
        lbl.pack(pady=15)

        entry = tk.Entry(dialog, font=theme.FONT_BODY, bg=theme.BG_CARD, fg=theme.TEXT_PRIMARY, insertbackground="white")
        entry.insert(0, str(current_val))
        entry.pack(pady=5)
        entry.focus_set()

        def save():
            try:
                val = float(clean_amount_str(entry.get()))
                if val < 0:
                    raise ValueError
                self.tracker.update_goal_savings(goal_id, val)
                dialog.destroy()
                self.refresh_page_data("goals")
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid positive savings value.", parent=dialog)

        btn = tk.Button(dialog, text="Save Updates", font=theme.FONT_BODY_BOLD, bg=theme.ACCENT, fg=theme.TEXT_DARK, activebackground=theme.ACCENT, bd=0, command=save)
        btn.pack(pady=15)

    def delete_goal(self, goal_id):
        ans = messagebox.askyesno("Delete Goal", "Are you sure you want to delete this savings goal?")
        if ans:
            self.tracker.delete_goal(goal_id)
            self.refresh_page_data("goals")

    # ==========================================
    # --- SUBSCRIPTIONS PAGE ---
    # ==========================================
    def create_subscriptions_page(self):
        page = tk.Frame(self.content_container, bg=theme.BG_MAIN)

        # Header
        top_bar = tk.Frame(page, bg=theme.BG_MAIN)
        top_bar.pack(fill="x", padx=25, pady=20)
        title = tk.Label(top_bar, text="Subscription Reminders", font=theme.FONT_TITLE, fg=theme.TEXT_PRIMARY, bg=theme.BG_MAIN)
        title.pack(side="left")

        # Layout
        main_layout = tk.Frame(page, bg=theme.BG_MAIN)
        main_layout.pack(fill="both", expand=True, padx=25, pady=5)

        # Left list, right add form
        self.subs_list_container = ScrollableFrame(main_layout, bg_color=theme.BG_MAIN)
        self.subs_list_container.pack(side="left", fill="both", expand=True, padx=(0, 15))

        # Add form
        form_card = theme.Card(main_layout, width=320, height=380)
        form_card.pack(side="right", fill="y")
        form_card.pack_propagate(False)

        form_title = tk.Label(form_card, text="⏰ Add Subscription", font=theme.FONT_SUBTITLE, fg=theme.TEXT_PRIMARY, bg=theme.BG_CARD)
        form_title.pack(pady=15, padx=20, anchor="w")

        # Name
        tk.Label(form_card, text="Subscription Name (e.g. Netflix)", font=theme.FONT_BODY_BOLD, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).pack(anchor="w", padx=20)
        self.sub_name_entry = tk.Entry(form_card, font=theme.FONT_BODY, bg=theme.BG_MAIN, fg=theme.TEXT_PRIMARY, insertbackground="white", bd=1, relief="solid")
        self.sub_name_entry.pack(pady=5, padx=20, fill="x")

        # Cost
        tk.Label(form_card, text="Cost (₹)", font=theme.FONT_BODY_BOLD, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).pack(anchor="w", padx=20, pady=(5,0))
        self.sub_cost_entry = tk.Entry(form_card, font=theme.FONT_BODY, bg=theme.BG_MAIN, fg=theme.TEXT_PRIMARY, insertbackground="white", bd=1, relief="solid")
        self.sub_cost_entry.pack(pady=5, padx=20, fill="x")

        # Billing Cycle
        tk.Label(form_card, text="Billing Cycle", font=theme.FONT_BODY_BOLD, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).pack(anchor="w", padx=20, pady=(5,0))
        self.sub_cycle_var = tk.StringVar(value="Monthly")
        self.sub_cycle_cmb = ttk.Combobox(form_card, textvariable=self.sub_cycle_var, values=["Monthly", "Yearly"], state="readonly", width=35)
        self.sub_cycle_cmb.pack(pady=5, padx=20)

        # Renewal Date
        tk.Label(form_card, text="Next Renewal Date (YYYY-MM-DD)", font=theme.FONT_BODY_BOLD, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).pack(anchor="w", padx=20, pady=(5,0))
        self.sub_date_entry = tk.Entry(form_card, font=theme.FONT_BODY, bg=theme.BG_MAIN, fg=theme.TEXT_PRIMARY, insertbackground="white", bd=1, relief="solid")
        self.sub_date_entry.insert(0, date.today().strftime("%Y-%m-%d"))
        self.sub_date_entry.pack(pady=5, padx=20, fill="x")

        # Add Button
        btn_add_sub = tk.Button(
            form_card, 
            text="Add Subscription", 
            font=theme.FONT_BODY_BOLD, 
            bg=theme.ACCENT, 
            fg=theme.TEXT_DARK, 
            activebackground=theme.ACCENT, 
            bd=0, 
            cursor="hand2", 
            command=self.save_subscription
        )
        btn_add_sub.pack(pady=20, padx=20, fill="x")

        return page

    def save_subscription(self):
        name = self.sub_name_entry.get().strip()
        cost_str = clean_amount_str(self.sub_cost_entry.get())
        cycle = self.sub_cycle_var.get()
        dt_str = self.sub_date_entry.get().strip()

        if not name:
            messagebox.showerror("Validation Error", "Subscription name is required.")
            return

        try:
            cost = float(cost_str)
            if cost <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Validation Error", "Please enter a valid positive cost amount.")
            return

        try:
            datetime.strptime(dt_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Validation Error", "Please enter a valid next renewal date (YYYY-MM-DD).")
            return

        self.tracker.add_subscription(name, cost, cycle, dt_str)
        messagebox.showinfo("Success", f"{name} subscription added!")

        # Clear form
        self.sub_name_entry.delete(0, tk.END)
        self.sub_cost_entry.delete(0, tk.END)
        self.sub_date_entry.delete(0, tk.END)
        self.sub_date_entry.insert(0, date.today().strftime("%Y-%m-%d"))

        self.refresh_page_data("subscriptions")

    def refresh_subscriptions(self):
        list_frame = self.subs_list_container.scrollable_frame
        for child in list_frame.winfo_children():
            child.destroy()

        # Get sorted renewals (OOP implementation sorting by date)
        subs = self.tracker.check_subscription_renewals()

        if not subs:
            lbl = tk.Label(list_frame, text="No active subscriptions tracked yet.\nRegister one on the right frame!", font=theme.FONT_BODY, fg=theme.TEXT_MUTED, bg=theme.BG_MAIN)
            lbl.pack(pady=100)
            return

        # Header statistics card for subscriptions
        total_sub_cost = sum(s.amount for s in subs)
        stats_sub_card = theme.Card(list_frame, width=500, height=55, bg_color=theme.BG_SIDEBAR)
        stats_sub_card.pack(fill="x", pady=(0, 10), padx=5)
        stats_sub_lbl = tk.Label(
            stats_sub_card, 
            text=f"Total Monthly Subscription Cost: ₹{total_sub_cost:,.2f}", 
            font=theme.FONT_BODY_BOLD, 
            fg=theme.ACCENT, 
            bg=theme.BG_SIDEBAR
        )
        stats_sub_lbl.place(relx=0.5, rely=0.5, anchor="center")

        for s in subs:
            card = theme.Card(list_frame, width=500, height=80)
            card.pack(fill="x", pady=5, padx=5)
            card.pack_propagate(False)

            title_lbl = tk.Label(card, text=f"🔔 {s.name}", font=theme.FONT_SUBTITLE, fg=theme.TEXT_PRIMARY, bg=theme.BG_CARD)
            title_lbl.place(x=20, y=15)

            cost_lbl = tk.Label(card, text=f"₹{s.amount:,.2f} ({s.billing_cycle})", font=theme.FONT_BODY, fg=theme.TEXT_MUTED, bg=theme.BG_CARD)
            cost_lbl.place(x=20, y=42)

            days = s.days_until_renewal()
            if days < 0:
                alert_text = f"Overdue by {abs(days)} days"
                alert_color = theme.EXPENSE
            elif days <= 3:
                alert_text = f"Renews in {days} days! ⚠️"
                alert_color = theme.WARNING
            else:
                alert_text = f"Next Renewal: {s.renewal_date} ({days} days)"
                alert_color = theme.INCOME

            renew_lbl = tk.Label(card, text=alert_text, font=theme.FONT_BODY_BOLD, fg=alert_color, bg=theme.BG_CARD)
            renew_lbl.place(x=240, y=20)

            # Delete button
            btn_delete = tk.Button(
                card,
                text="🗑 Cancel",
                font=theme.FONT_SMALL,
                fg=theme.EXPENSE,
                bg=theme.BG_CARD,
                bd=0,
                cursor="hand2",
                command=lambda id_=s.id: self.delete_subscription(id_)
            )
            btn_delete.place(x=430, y=45)

    def delete_subscription(self, sub_id):
        ans = messagebox.askyesno("Cancel Subscription", "Are you sure you want to stop tracking this subscription?")
        if ans:
            self.tracker.delete_subscription(sub_id)
            self.refresh_page_data("subscriptions")

    # ==========================================
    # --- SMART SHOPPING SUGGESTIONS ---
    # ==========================================
    def create_suggestions_page(self):
        page = ScrollableFrame(self.content_container, bg_color=theme.BG_MAIN)
        frame = page.scrollable_frame

        # Header
        top_bar = tk.Frame(frame, bg=theme.BG_MAIN)
        top_bar.pack(fill="x", padx=25, pady=20)
        title = tk.Label(top_bar, text="Smart Shopping Suggestions", font=theme.FONT_TITLE, fg=theme.TEXT_PRIMARY, bg=theme.BG_MAIN)
        title.pack(side="left")

        # Search & Budget Input Card
        search_card = tk.Frame(frame, bg=theme.BG_CARD, highlightbackground=theme.BORDER, highlightthickness=1)
        search_card.pack(fill="x", padx=25, pady=(0, 15))
        
        info_lbl = tk.Label(
            search_card, 
            text="Thinking of buying something expensive? Enter your product and budget below to independently search and compare\nreal-time prices across Amazon India, Flipkart, Croma, and Reliance Digital without platform bias.", 
            font=theme.FONT_BODY, 
            fg=theme.TEXT_MUTED, 
            bg=theme.BG_CARD,
            justify="left"
        )
        info_lbl.pack(pady=(15, 10), padx=20, anchor="w")

        # Inputs frame
        input_frame = tk.Frame(search_card, bg=theme.BG_CARD)
        input_frame.pack(fill="x", padx=20, pady=(0, 15))

        # Item Name
        tk.Label(input_frame, text="Product Name / Keyword", font=theme.FONT_BODY_BOLD, fg=theme.TEXT_PRIMARY, bg=theme.BG_CARD).grid(row=0, column=0, sticky="w", pady=(0, 5))
        self.suggest_name_entry = tk.Entry(input_frame, font=theme.FONT_BODY, bg=theme.BG_MAIN, fg=theme.TEXT_PRIMARY, insertbackground="white", bd=1, relief="solid", width=32)
        self.suggest_name_entry.grid(row=1, column=0, sticky="w", padx=(0, 15))

        # Expected / Budget Price
        tk.Label(input_frame, text="Expected Budget (₹)", font=theme.FONT_BODY_BOLD, fg=theme.TEXT_PRIMARY, bg=theme.BG_CARD).grid(row=0, column=1, sticky="w", pady=(0, 5))
        self.suggest_price_entry = tk.Entry(input_frame, font=theme.FONT_BODY, bg=theme.BG_MAIN, fg=theme.TEXT_PRIMARY, insertbackground="white", bd=1, relief="solid", width=18)
        self.suggest_price_entry.grid(row=1, column=1, sticky="w", padx=(0, 15))

        # Run Button
        btn_run = tk.Button(
            input_frame, 
            text="🔍 Compare 4 Platforms", 
            font=theme.FONT_BODY_BOLD, 
            bg=theme.ACCENT, 
            fg=theme.TEXT_DARK, 
            activebackground=theme.ACCENT, 
            bd=0, 
            pady=8,
            padx=20,
            cursor="hand2", 
            command=self.run_suggestions_engine
        )
        btn_run.grid(row=1, column=2, sticky="w")

        # Results area (expands vertically without height restriction)
        self.suggest_results_frame = tk.Frame(frame, bg=theme.BG_MAIN)
        self.suggest_results_frame.pack(fill="both", expand=True, padx=25, pady=(0, 25))

        # Welcome Placeholder
        self.suggest_placeholder = tk.Label(
            self.suggest_results_frame, 
            text="Enter a product name (e.g. 'iPhone 15', 'Samsung S24', 'LG TV 32 inch')\nand your expected budget above to search all four platforms.",
            font=theme.FONT_BODY, 
            fg="#4b5563", 
            bg=theme.BG_MAIN
        )
        self.suggest_placeholder.pack(expand=True, pady=40)

        return page

    def run_suggestions_engine(self):
        item_keyword = self.suggest_name_entry.get().strip()
        price_str = clean_amount_str(self.suggest_price_entry.get())

        if not item_keyword or not price_str:
            messagebox.showerror("Error", "Please fill in both product name and budget price.")
            return

        try:
            user_budget = float(price_str)
            if user_budget <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid positive number for budget price.")
            return

        # Clear results panel
        for child in self.suggest_results_frame.winfo_children():
            child.destroy()

        # Show Loading Spinner / Status
        loading_box = tk.Frame(self.suggest_results_frame, bg=theme.BG_CARD)
        loading_box.pack(expand=True, fill="both", pady=30)
        
        tk.Label(
            loading_box,
            text="🔍 Searching 4 E-Commerce Platforms...\n"
                 "• Amazon India   • Flipkart   • Croma   • Reliance Digital\n\n"
                 "Fetching real-time product listings and verifying prices. Please wait...",
            font=theme.FONT_BODY_BOLD,
            fg=theme.ACCENT,
            bg=theme.BG_CARD,
            justify="center"
        ).pack(expand=True)
        
        # Start search in background thread
        import threading
        def bg_search():
            try:
                from price_comparison_service import search_all_platforms, evaluate_price_comparison
                offers = search_all_platforms(item_keyword)
                comp_result = evaluate_price_comparison(offers, user_budget)
                self.after(10, lambda: self.display_suggestions_results(item_keyword, user_budget, comp_result))
            except Exception as e:
                print("Suggestions search thread error:", e)
                self.after(10, lambda: self.display_suggestions_error(str(e)))

        threading.Thread(target=bg_search, daemon=True).start()


    def display_suggestions_results(self, item_keyword, user_budget, comp_res):
        import webbrowser
        
        # Clear results panel
        for child in self.suggest_results_frame.winfo_children():
            child.destroy()
            
        if not comp_res or not comp_res.offers:
            self.display_suggestions_error("No product offers could be retrieved.")
            return

        results_panel = tk.Frame(self.suggest_results_frame, bg=theme.BG_MAIN)
        results_panel.pack(fill="both", expand=True)

        # -------------------------------------------------------------
        # 1. TOP METRIC BADGES (User Budget, Lowest Price, Best Deal, Variance)
        # -------------------------------------------------------------
        metrics_frame = tk.Frame(results_panel, bg=theme.BG_MAIN)
        metrics_frame.pack(fill="x", pady=(0, 12))
        for i in range(4):
            metrics_frame.columnconfigure(i, weight=1)

        # Card 1: User Budget
        c1 = tk.Frame(metrics_frame, bg=theme.BG_CARD, highlightbackground=theme.BORDER, highlightthickness=1, padx=14, pady=10)
        c1.grid(row=0, column=0, sticky="nsew", padx=4)
        tk.Label(c1, text="YOUR BUDGET", font=theme.FONT_SMALL, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).pack(anchor="w")
        tk.Label(c1, text=f"₹{user_budget:,.2f}", font=theme.FONT_BODY_BOLD, fg=theme.TEXT_PRIMARY, bg=theme.BG_CARD).pack(anchor="w", pady=(3, 0))

        # Card 2: Lowest Verified Price
        c2 = tk.Frame(metrics_frame, bg=theme.BG_CARD, highlightbackground=theme.BORDER, highlightthickness=1, padx=14, pady=10)
        c2.grid(row=0, column=1, sticky="nsew", padx=4)
        tk.Label(c2, text="LOWEST VERIFIED", font=theme.FONT_SMALL, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).pack(anchor="w")
        lowest_txt = f"₹{comp_res.lowest_verified_price:,.2f}" if comp_res.lowest_verified_price else "Unavailable"
        lowest_color = theme.INCOME if comp_res.lowest_verified_price else theme.TEXT_MUTED
        tk.Label(c2, text=lowest_txt, font=theme.FONT_BODY_BOLD, fg=lowest_color, bg=theme.BG_CARD).pack(anchor="w", pady=(3, 0))

        # Card 3: Cheapest Platform
        c3 = tk.Frame(metrics_frame, bg=theme.BG_CARD, highlightbackground=theme.BORDER, highlightthickness=1, padx=14, pady=10)
        c3.grid(row=0, column=2, sticky="nsew", padx=4)
        tk.Label(c3, text="CHEAPEST STORE", font=theme.FONT_SMALL, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).pack(anchor="w")
        if comp_res.has_tie:
            best_platform_name = "🤝 " + " & ".join([o.platform for o in comp_res.cheapest_offers])
        elif comp_res.cheapest_offers:
            best_platform_name = "👑 " + comp_res.cheapest_offers[0].platform
        else:
            best_platform_name = "None Verified"
        tk.Label(c3, text=best_platform_name, font=theme.FONT_BODY_BOLD, fg=theme.ACCENT if comp_res.cheapest_offers else theme.TEXT_MUTED, bg=theme.BG_CARD).pack(anchor="w", pady=(3, 0))

        # Card 4: Budget Variance / Savings
        c4 = tk.Frame(metrics_frame, bg=theme.BG_CARD, highlightbackground=theme.BORDER, highlightthickness=1, padx=14, pady=10)
        c4.grid(row=0, column=3, sticky="nsew", padx=4)
        tk.Label(c4, text="BUDGET VARIANCE", font=theme.FONT_SMALL, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).pack(anchor="w")
        if comp_res.lowest_verified_price is not None:
            diff = comp_res.lowest_verified_price - user_budget
            if diff <= 0:
                var_txt = f"Saved: ₹{abs(diff):,.2f}"
                var_color = theme.INCOME
            else:
                var_txt = f"Over: +₹{diff:,.2f}"
                var_color = theme.EXPENSE
        else:
            var_txt = "Unverified"
            var_color = theme.TEXT_MUTED
        tk.Label(c4, text=var_txt, font=theme.FONT_BODY_BOLD, fg=var_color, bg=theme.BG_CARD).pack(anchor="w", pady=(3, 0))

        # -------------------------------------------------------------
        # 2. PROMINENT "VISIT CHEAPEST DEAL" HERO BANNER
        # -------------------------------------------------------------
        cheapest_banner = tk.Frame(results_panel, bg="#13262f", highlightbackground=theme.ACCENT, highlightthickness=1)
        cheapest_banner.pack(fill="x", pady=(0, 12))

        cb_info = tk.Frame(cheapest_banner, bg="#13262f")
        cb_info.pack(side="left", padx=16, pady=12, fill="x", expand=True)

        if comp_res.lowest_verified_price is not None and comp_res.cheapest_offers:
            deal_store_txt = ("Tied: " if comp_res.has_tie else "") + ", ".join(o.platform for o in comp_res.cheapest_offers)
            diff = comp_res.lowest_verified_price - user_budget
            if diff <= 0:
                stat_tag = f"✅ ₹{abs(diff):,.2f} Below Budget"
            else:
                stat_tag = f"⚠️ ₹{diff:,.2f} Above Budget (Cheapest Available)"
            cb_title = f"👑 BEST VERIFIED DEAL: {deal_store_txt} — ₹{comp_res.lowest_verified_price:,.2f}"
            cb_sub = f"Status: {stat_tag}   •   Last Checked: {comp_res.checked_time}"
        else:
            cb_title = "⚠️ No Verified Platform Offer Available"
            cb_sub = "Prices could not be verified live. Check individual platform statuses below."

        tk.Label(cb_info, text=cb_title, font=theme.FONT_SUBTITLE, fg=theme.ACCENT, bg="#13262f").pack(anchor="w")
        tk.Label(cb_info, text=cb_sub, font=theme.FONT_BODY, fg=theme.TEXT_PRIMARY, bg="#13262f").pack(anchor="w", pady=(2, 0))

        def open_cheapest_deal():
            if not comp_res.cheapest_offers or comp_res.lowest_verified_price is None:
                messagebox.showinfo(
                    "Cheapest Deal Unavailable",
                    "No verified product listing is currently available. Please check the individual platform verification status in the table below."
                )
                return
            best_offer = comp_res.cheapest_offers[0]
            url = (best_offer.url or "").strip()
            if not url or not (url.startswith("http://") or url.startswith("https://")):
                messagebox.showwarning(
                    "Listing Link Unavailable",
                    f"A direct product link for {best_offer.platform} could not be found."
                )
                return
            webbrowser.open(url)

        btn_cheapest_cta = tk.Button(
            cheapest_banner,
            text="🛒 Visit Cheapest Deal",
            font=theme.FONT_BODY_BOLD,
            bg=theme.ACCENT,
            fg=theme.TEXT_DARK,
            activebackground="#5df5ff",
            activeforeground=theme.TEXT_DARK,
            bd=0,
            padx=20,
            pady=10,
            cursor="hand2",
            command=open_cheapest_deal
        )
        btn_cheapest_cta.pack(side="right", padx=16, pady=12)

        # -------------------------------------------------------------
        # 3. DYNAMIC CASE BANNER & STATUS
        # -------------------------------------------------------------
        if comp_res.case == "A":
            banner_bg = "#064e3b"
            banner_border = theme.INCOME
            banner_title = "🎉 VERIFIED DEAL AVAILABLE BELOW BUDGET!"
            banner_title_color = theme.INCOME
        elif comp_res.case == "B":
            banner_bg = "#451a03"
            banner_border = theme.WARNING
            banner_title = "ℹ️ ALL AVAILABLE OFFERS EXCEED YOUR BUDGET"
            banner_title_color = theme.WARNING
        else:
            banner_bg = "#1e293b"
            banner_border = theme.ACCENT
            banner_title = "⚠️ SEARCH & VERIFICATION STATUS"
            banner_title_color = theme.ACCENT

        alert_box = tk.Frame(results_panel, bg=banner_bg, highlightbackground=banner_border, highlightthickness=1)
        alert_box.pack(fill="x", pady=(0, 12))

        tk.Label(
            alert_box,
            text=banner_title,
            font=theme.FONT_BODY_BOLD,
            fg=banner_title_color,
            bg=banner_bg
        ).pack(anchor="w", padx=15, pady=(8, 2))

        tk.Label(
            alert_box,
            text=comp_res.summary_message,
            font=theme.FONT_BODY,
            fg=theme.TEXT_PRIMARY,
            bg=banner_bg,
            justify="left",
            wraplength=720
        ).pack(anchor="w", padx=15, pady=(2, 6))

        if comp_res.health_score_impact > 0:
            savings_amt = user_budget - comp_res.lowest_verified_price
            tk.Label(
                alert_box,
                text=f"💡 Financial Health Impact: Saving ₹{savings_amt:,.2f} will increase your projected Financial Health Score by roughly +{comp_res.health_score_impact} pts next month!",
                font=theme.FONT_SMALL,
                fg=theme.INCOME,
                bg=banner_bg,
                justify="left"
            ).pack(anchor="w", padx=15, pady=(0, 8))

        # -------------------------------------------------------------
        # 4. FOUR-PLATFORM COMPARISON TABLE (Expansive, Taller, Responsive)
        # -------------------------------------------------------------
        table_container = tk.Frame(results_panel, bg=theme.BG_CARD, highlightbackground=theme.BORDER, highlightthickness=1)
        table_container.pack(fill="both", expand=True, pady=(0, 10))

        # Table Header
        header_frame = tk.Frame(table_container, bg=theme.BG_SIDEBAR)
        header_frame.pack(fill="x")
        header_frame.columnconfigure(0, weight=2, minsize=140)
        header_frame.columnconfigure(1, weight=5, minsize=260)
        header_frame.columnconfigure(2, weight=2, minsize=120)
        header_frame.columnconfigure(3, weight=2, minsize=140)
        header_frame.columnconfigure(4, weight=2, minsize=140)
        header_frame.columnconfigure(5, weight=1, minsize=110)

        headers = [
            ("Platform", 0, "w"),
            ("Product Listing / Variant", 1, "w"),
            ("Listed Price", 2, "e"),
            ("Budget Status", 3, "center"),
            ("Verification Status", 4, "center"),
            ("Action", 5, "center")
        ]

        for col_name, col_idx, col_anchor in headers:
            lbl = tk.Label(
                header_frame,
                text=col_name,
                font=theme.FONT_BODY_BOLD,
                fg=theme.TEXT_PRIMARY,
                bg=theme.BG_SIDEBAR,
                anchor=col_anchor
            )
            lbl.grid(row=0, column=col_idx, sticky="ew", padx=10, pady=10)

        # Cheaper offer platform names for quick identification
        cheapest_platform_names = {o.platform for o in comp_res.cheapest_offers} if comp_res.lowest_verified_price else set()

        for idx, offer in enumerate(comp_res.offers):
            is_best = (offer.platform in cheapest_platform_names) and offer.is_verified
            row_bg = "#192231" if is_best else (theme.BG_CARD if idx % 2 == 0 else "#14151a")
            border_color = theme.ACCENT if is_best else theme.BORDER
            thickness = 2 if is_best else 1

            row_frame = tk.Frame(table_container, bg=row_bg, highlightbackground=border_color, highlightthickness=thickness)
            row_frame.pack(fill="x", padx=4, pady=3)
            row_frame.columnconfigure(0, weight=2, minsize=140)
            row_frame.columnconfigure(1, weight=5, minsize=260)
            row_frame.columnconfigure(2, weight=2, minsize=120)
            row_frame.columnconfigure(3, weight=2, minsize=140)
            row_frame.columnconfigure(4, weight=2, minsize=140)
            row_frame.columnconfigure(5, weight=1, minsize=110)

            # 1. Platform Cell
            plat_cell = tk.Frame(row_frame, bg=row_bg)
            plat_cell.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

            if is_best:
                badge_text = "🤝 TIE DEAL" if comp_res.has_tie else "👑 BEST DEAL"
                tk.Label(plat_cell, text=badge_text, font=("Segoe UI", 8, "bold"), fg=theme.ACCENT, bg=row_bg, anchor="w").pack(anchor="w")
                tk.Label(plat_cell, text=offer.platform, font=theme.FONT_BODY_BOLD, fg=theme.TEXT_PRIMARY, bg=row_bg, anchor="w").pack(anchor="w")
            else:
                tk.Label(plat_cell, text=offer.platform, font=theme.FONT_BODY_BOLD, fg=theme.TEXT_PRIMARY, bg=row_bg, anchor="w").pack(anchor="w", pady=(8, 0))

            # 2. Product Name & Variant Cell
            prod_cell = tk.Frame(row_frame, bg=row_bg)
            prod_cell.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

            clean_title = offer.product_name
            if len(clean_title) > 65:
                clean_title = clean_title[:62] + "..."
            tk.Label(prod_cell, text=clean_title, font=theme.FONT_BODY, fg=theme.TEXT_PRIMARY, bg=row_bg, anchor="w", wraplength=280, justify="left").pack(anchor="w")
            if offer.variant and offer.variant != "Standard":
                tk.Label(prod_cell, text=f"Model/Variant: {offer.variant}", font=theme.FONT_SMALL, fg=theme.TEXT_MUTED, bg=row_bg, anchor="w").pack(anchor="w", pady=(2, 0))

            # 3. Listed Price Cell
            price_cell = tk.Frame(row_frame, bg=row_bg)
            price_cell.grid(row=0, column=2, sticky="nsew", padx=10, pady=10)

            if offer.price is not None:
                pr_text = f"₹{offer.price:,.2f}"
                pr_color = theme.INCOME if is_best else theme.TEXT_PRIMARY
                pr_font = ("Segoe UI", 11, "bold") if is_best else theme.FONT_BODY_BOLD
            else:
                pr_text = "Price unavailable"
                pr_color = theme.TEXT_MUTED
                pr_font = theme.FONT_BODY
            tk.Label(price_cell, text=pr_text, font=pr_font, fg=pr_color, bg=row_bg, anchor="e").pack(fill="x", pady=(8, 0))

            # 4. Budget Status Cell
            b_cell = tk.Frame(row_frame, bg=row_bg)
            b_cell.grid(row=0, column=3, sticky="nsew", padx=10, pady=10)

            if "Under Budget" in offer.budget_status:
                bs_color = theme.INCOME
            elif "Over Budget" in offer.budget_status:
                bs_color = theme.EXPENSE
            else:
                bs_color = theme.TEXT_MUTED
            tk.Label(b_cell, text=offer.budget_status, font=theme.FONT_BODY_BOLD if is_best else theme.FONT_BODY, fg=bs_color, bg=row_bg, anchor="center").pack(fill="x", pady=(8, 0))

            # 5. Verification Status Cell
            v_cell = tk.Frame(row_frame, bg=row_bg)
            v_cell.grid(row=0, column=4, sticky="nsew", padx=10, pady=10)

            if offer.is_verified:
                v_text = "✅ Verified Live"
                v_color = theme.INCOME
            else:
                v_text = "⚠️ " + (offer.status.split("(")[0].strip() if "(" in offer.status else offer.status)
                v_color = theme.TEXT_MUTED
            tk.Label(v_cell, text=v_text, font=theme.FONT_SMALL, fg=v_color, bg=row_bg, anchor="center").pack(fill="x", pady=(8, 0))

            # 6. Action: Individual View Deal Button
            btn_cell = tk.Frame(row_frame, bg=row_bg)
            btn_cell.grid(row=0, column=5, sticky="nsew", padx=10, pady=10)

            def make_open_offer_handler(target_url, plat_name):
                def _open():
                    url = (target_url or "").strip()
                    if not url or not (url.startswith("http://") or url.startswith("https://")):
                        messagebox.showwarning(
                            "Listing Unavailable",
                            f"Direct product listing URL for {plat_name} is not available."
                        )
                        return
                    webbrowser.open(url)
                return _open

            btn_deal = tk.Button(
                btn_cell,
                text="🔗 View Deal",
                font=theme.FONT_SMALL,
                bg=theme.ACCENT if is_best else "#2e3039",
                fg=theme.TEXT_DARK if is_best else theme.TEXT_PRIMARY,
                activebackground=theme.ACCENT,
                activeforeground=theme.TEXT_DARK,
                bd=0,
                padx=10,
                pady=5,
                cursor="hand2",
                command=make_open_offer_handler(offer.url, offer.platform)
            )
            btn_deal.pack(anchor="center", pady=(6, 0))

        # Table Footer Tip & Verification Info
        footer_frame = tk.Frame(results_panel, bg=theme.BG_MAIN)
        footer_frame.pack(fill="x", pady=(6, 12))

        tk.Label(
            footer_frame,
            text=f"🕒 Last Checked: {comp_res.checked_time}   |   🛡️ Search Status: {comp_res.verified_count} of {comp_res.total_count} platforms verified live   |   💡 Tip: Click 'View Deal' on any row or 'Visit Cheapest Deal' to open exact listings.",
            font=theme.FONT_SMALL,
            fg=theme.TEXT_MUTED,
            bg=theme.BG_MAIN
        ).pack(anchor="w")


    def display_suggestions_error(self, err_details=""):
        for child in self.suggest_results_frame.winfo_children():
            child.destroy()
            
        err_card = tk.Frame(self.suggest_results_frame, bg=theme.BG_MAIN, highlightbackground=theme.EXPENSE, highlightthickness=1, padx=20, pady=20)
        err_card.pack(fill="both", expand=True, pady=10)
        
        tk.Label(
            err_card,
            text="⚠️ Price Comparison Could Not Complete",
            font=theme.FONT_SUBTITLE,
            fg=theme.EXPENSE,
            bg=theme.BG_MAIN
        ).pack(anchor="w", pady=(0, 6))
        
        msg = "We encountered an issue while querying the platforms. Please check your internet connection and try again."
        if err_details:
            msg += f"\n\nDetails: {err_details}"
            
        tk.Label(
            err_card,
            text=msg,
            font=theme.FONT_BODY,
            fg=theme.TEXT_PRIMARY,
            bg=theme.BG_MAIN,
            justify="left",
            wraplength=600
        ).pack(anchor="w", pady=4)
        
        tk.Button(
            err_card,
            text="🔄 Try Again",
            font=theme.FONT_BODY_BOLD,
            bg=theme.ACCENT,
            fg=theme.TEXT_DARK,
            bd=0,
            padx=15,
            pady=6,
            cursor="hand2",
            command=self.run_suggestions_engine
        ).pack(anchor="w", pady=(10, 0))


    # ==========================================
    # --- INSIGHTS & EXPORTS PAGE ---
    # ==========================================
    def create_exports_page(self):
        page = tk.Frame(self.content_container, bg=theme.BG_MAIN)

        # Header
        top_bar = tk.Frame(page, bg=theme.BG_MAIN)
        top_bar.pack(fill="x", padx=25, pady=20)
        title = tk.Label(top_bar, text="Spending Insights & Exports", font=theme.FONT_TITLE, fg=theme.TEXT_PRIMARY, bg=theme.BG_MAIN)
        title.pack(side="left")

        # Two main panels: Insights Card (top/left) + Export Card (right/bottom)
        main_layout = tk.Frame(page, bg=theme.BG_MAIN)
        main_layout.pack(fill="both", expand=True, padx=25, pady=5)

        # Left panel for natural language insights
        self.insights_card = theme.Card(main_layout, width=420, height=450)
        self.insights_card.pack(side="left", fill="both", expand=True, padx=(0, 15))
        
        ins_title = tk.Label(self.insights_card, text="💡 AI Spending Insights (Pandas-Generated)", font=theme.FONT_SUBTITLE, fg=theme.TEXT_PRIMARY, bg=theme.BG_CARD)
        ins_title.pack(pady=15, padx=20, anchor="w")

        self.insights_container = tk.Frame(self.insights_card, bg=theme.BG_CARD)
        self.insights_container.pack(fill="both", expand=True, padx=20, pady=10)

        # Right panel for PDF/CSV operations
        export_card = theme.Card(main_layout, width=320, height=520)
        export_card.pack(side="right", fill="y")
        export_card.pack_propagate(False)

        exp_title = tk.Label(export_card, text="📦 Database & Exports", font=theme.FONT_SUBTITLE, fg=theme.TEXT_PRIMARY, bg=theme.BG_CARD)
        exp_title.pack(pady=12, padx=20, anchor="w")

        info_export = tk.Label(
            export_card, 
            text="Generate printable reports, export worksheets to Excel, or safeguard your database with backups.", 
            font=theme.FONT_BODY, 
            fg=theme.TEXT_MUTED, 
            bg=theme.BG_CARD,
            wraplength=280,
            justify="left"
        )
        info_export.pack(pady=5, padx=20, anchor="w")

        # PDF Button
        btn_pdf = tk.Button(
            export_card,
            text="📄 Generate Monthly PDF Report",
            font=theme.FONT_BODY_BOLD,
            bg=theme.ACCENT,
            fg=theme.TEXT_DARK,
            activebackground=theme.ACCENT,
            bd=0,
            pady=10,
            cursor="hand2",
            command=self.export_pdf_report
        )
        btn_pdf.pack(fill="x", padx=20, pady=8)

        # CSV Button
        btn_csv = tk.Button(
            export_card,
            text="📊 Export Ledgers to Excel (CSV)",
            font=theme.FONT_BODY_BOLD,
            bg=theme.INCOME,
            fg=theme.TEXT_PRIMARY,
            activebackground=theme.INCOME,
            bd=0,
            pady=10,
            cursor="hand2",
            command=self.export_csv_data
        )
        btn_csv.pack(fill="x", padx=20, pady=8)

        # Backup Button
        btn_backup = tk.Button(
            export_card,
            text="💾 Backup Financial Database",
            font=theme.FONT_BODY_BOLD,
            bg="#374151",
            fg=theme.TEXT_PRIMARY,
            activebackground="#4b5563",
            bd=0,
            pady=10,
            cursor="hand2",
            command=self.export_database_file
        )
        btn_backup.pack(fill="x", padx=20, pady=8)

        # Restore Button
        btn_restore = tk.Button(
            export_card,
            text="🔄 Restore Database Backup",
            font=theme.FONT_BODY_BOLD,
            bg="#374151",
            fg=theme.TEXT_PRIMARY,
            activebackground="#4b5563",
            bd=0,
            pady=10,
            cursor="hand2",
            command=self.import_database_file
        )
        btn_restore.pack(fill="x", padx=20, pady=8)

        # Reset Button
        btn_reset = tk.Button(
            export_card,
            text="🧹 Clear All Data & Start Fresh",
            font=theme.FONT_BODY_BOLD,
            bg=theme.EXPENSE,
            fg=theme.TEXT_PRIMARY,
            activebackground=theme.EXPENSE,
            bd=0,
            pady=10,
            cursor="hand2",
            command=self.reset_database
        )
        btn_reset.pack(fill="x", padx=20, pady=6)

        # Load Demo Data Button
        btn_demo = tk.Button(
            export_card,
            text="🌱 Load Demo / Sample Data",
            font=theme.FONT_BODY_BOLD,
            bg="#1e293b",
            fg=theme.TEXT_PRIMARY,
            activebackground="#334155",
            bd=1,
            relief="solid",
            pady=10,
            cursor="hand2",
            command=self.load_demo_data
        )
        btn_demo.pack(fill="x", padx=20, pady=6)

        return page

    def refresh_exports(self, df):
        # Clear insights container
        for child in self.insights_container.winfo_children():
            child.destroy()

        # Load natural language spending insights
        insights_list = analytics.get_spending_insights(df)

        for ins in insights_list:
            # Draw bullet-point line with border
            bullet_frame = tk.Frame(self.insights_container, bg=theme.BG_CARD, pady=8)
            bullet_frame.pack(fill="x", anchor="w")

            bullet = tk.Label(bullet_frame, text="• ", font=theme.FONT_SUBTITLE, fg=theme.ACCENT, bg=theme.BG_CARD)
            bullet.pack(side="left", anchor="n")

            ins_lbl = tk.Label(bullet_frame, text=ins, font=theme.FONT_BODY, fg=theme.TEXT_PRIMARY, bg=theme.BG_CARD, justify="left", wraplength=480)
            ins_lbl.pack(side="left", fill="x", expand=True, anchor="w")

    def export_pdf_report(self):
        transactions = self.tracker.get_transactions()
        df = analytics.load_dataframe(transactions)
        
        if df.empty:
            messagebox.showwarning("Warning", "Cannot generate report: No transactions found in database.")
            return

        today = date.today()
        summary = analytics.get_monthly_summary(df, today.year, today.month)
        cat_spending = analytics.get_category_wise_spending(df, today.year, today.month)
        goals = self.tracker.get_goals()
        subs = self.tracker.get_subscriptions()
        health = analytics.calculate_health_score(df, self.tracker.budget_limit, goals, subs)

        report_filename = f"finance_report_{today.strftime('%b_%Y')}.pdf"
        
        try:
            # Filter transactions to only pass Personal ones to PDF report
            personal_txs = [t for t in transactions if t.profile == "Personal"]
            PDFReportGenerator.generate_report(
                personal_txs, 
                summary, 
                cat_spending, 
                health, 
                goals, 
                file_path=report_filename
            )
            # Create a full path link
            full_path = os.path.abspath(report_filename)
            
            # Automatically open the generated PDF
            try:
                os.startfile(full_path)
            except Exception:
                pass
        except Exception as e:
            messagebox.showerror("Export Failed", f"An error occurred while compiling the PDF: {str(e)}")

    def export_csv_data(self):
        transactions = self.tracker.get_transactions()
        df = analytics.load_dataframe(transactions)

        # Filter for Personal transactions only
        if "profile" in df.columns:
            df = df[df["profile"] == "Personal"]

        if df.empty:
            messagebox.showwarning("Warning", "No transaction ledger available to export.")
            return

        csv_filename = "transactions_export.csv"
        try:
            # Export structured pandas dataframe to csv
            # We select clean columns to present in Excel
            clean_df = df[["date", "type", "category", "amount", "notes"]].copy()
            clean_df.columns = ["Date", "Type", "Category", "Amount (INR)", "Notes / Description"]
            
            clean_df.to_csv(csv_filename, index=False)
            full_path = os.path.abspath(csv_filename)
            
            # Automatically open the generated CSV in Excel
            try:
                os.startfile(full_path)
            except Exception:
                pass
        except Exception as e:
            messagebox.showerror("Export Failed", f"An error occurred during CSV export: {str(e)}")

    def reset_database(self):
        ans = messagebox.askyesno(
            "⚠️ Reset Database & Start Fresh",
            "Are you sure you want to delete all transactions, saving goals, and subscriptions?\n\n"
            "This will permanently delete all records and let you track your own personal finances from scratch.",
            icon="warning"
        )
        if ans:
            try:
                # 1. Create fail-safe automatic backup in backups folder before wiping
                os.makedirs("backups", exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"backups/auto_backup_before_reset_{timestamp}.db"
                try:
                    shutil.copy("finance_assistant.db", backup_path)
                    backup_msg = f"\n\n(A safety backup was saved automatically to: {backup_path})"
                except Exception:
                    backup_msg = ""

                # 2. Wipe SQLite tables
                conn = self.tracker.db.get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM transactions")
                cursor.execute("DELETE FROM saving_goals")
                cursor.execute("DELETE FROM subscriptions")
                conn.commit()
                conn.close()
                
                # Set settings.json 'seeded' flag to True to prevent re-seeding
                import json
                settings = {}
                if os.path.exists("settings.json"):
                    try:
                        with open("settings.json", "r") as f:
                            settings = json.load(f)
                    except Exception:
                        pass
                settings["seeded"] = True
                try:
                    with open("settings.json", "w") as f:
                        json.dump(settings, f)
                except Exception:
                    pass
                
                messagebox.showinfo("Success", f"All data has been cleared! The application is now ready for your personal use.{backup_msg}")
                self.refresh_page_data(self.current_page)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to reset database: {str(e)}")

    def backup_database(self):
        try:
            # Check if active database exists
            if not os.path.exists("finance_assistant.db"):
                messagebox.showerror("Error", "No database found to backup.")
                return
                
            # Create backups folder if missing
            os.makedirs("backups", exist_ok=True)
            backup_path = "backups/quick_backup.db"
            
            # Direct copy
            shutil.copy("finance_assistant.db", backup_path)
            messagebox.showinfo("Backup Success", "Quick backup created successfully!\n\nYour data has been saved to 'backups/quick_backup.db'.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create backup: {str(e)}")

    def restore_database(self):
        backup_path = "backups/quick_backup.db"
        if not os.path.exists(backup_path):
            messagebox.showwarning("Restore Failed", "No quick backup found!\n\nPlease click 'Backup Financial Database' to save your current data first.")
            return

        ans = messagebox.askyesno(
            "⚠️ Restore Database Backup",
            "Are you sure you want to restore the quick backup?\n\nThis will overwrite all current transactions, goals, and subscriptions with your previously backed up data.",
            icon="warning"
        )
        if ans:
            try:
                # Overwrite active database file
                shutil.copy(backup_path, "finance_assistant.db")
                
                # Re-initialize SQL schemas (in case restoring from an older version schema)
                self.tracker.db.init_db()
                
                # Force refresh data across all pages
                self.refresh_page_data(self.current_page)
                
                messagebox.showinfo("Success", "Database backup restored successfully! All your previous data is now visible on the dashboard.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to restore backup: {str(e)}")

    def export_database_file(self):
        try:
            if not os.path.exists("finance_assistant.db"):
                messagebox.showerror("Error", "No database found to export.")
                return
                
            today_str = datetime.now().strftime("%Y%m%d")
            file_path = filedialog.asksaveasfilename(
                title="Export Database Backup File",
                defaultextension=".db",
                filetypes=[("Database Files", "*.db"), ("All Files", "*.*")],
                initialfile=f"finance_backup_{today_str}.db"
            )
            
            if file_path:
                shutil.copy("finance_assistant.db", file_path)
                messagebox.showinfo("Export Success", f"Database backup file exported successfully to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export backup: {str(e)}")

    def import_database_file(self):
        ans = messagebox.askyesno(
            "⚠️ Import Database Backup",
            "Importing a database file will overwrite all your current transactions, goals, and subscriptions.\n\n"
            "Do you want to proceed?",
            icon="warning"
        )
        if ans:
            try:
                file_path = filedialog.askopenfilename(
                    title="Select Database File to Import",
                    filetypes=[("Database Files", "*.db"), ("All Files", "*.*")]
                )
                
                if file_path:
                    shutil.copy(file_path, "finance_assistant.db")
                    self.tracker.db.init_db()
                    
                    # Force refresh UI data across all pages
                    self.refresh_page_data(self.current_page)
                    messagebox.showinfo("Import Success", "Database backup imported successfully! All your previous data has loaded.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import backup: {str(e)}")

    def load_demo_data(self):
        ans = messagebox.askyesno(
            "🌱 Load Demo / Sample Data",
            "Are you sure you want to load the sample demo transactions, goals, and subscriptions?\n\n"
            "This will add realistic sample data for you to test the app features.",
            icon="info"
        )
        if ans:
            try:
                # Force settings.json seeded status to false temporarily to allow seeding
                import json
                settings = {}
                if os.path.exists("settings.json"):
                    try:
                        with open("settings.json", "r") as f:
                            settings = json.load(f)
                    except Exception:
                        pass
                settings["seeded"] = False
                with open("settings.json", "w") as f:
                    json.dump(settings, f)
                
                # Run the seeding engine
                import main
                main.seed_sample_data(self.tracker.db)
                
                # Refresh current view
                self.refresh_page_data(self.current_page)
                messagebox.showinfo("Success", "Demo data loaded successfully! The dashboard and ledger have been updated.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load demo data: {str(e)}")

    def create_ai_insights_page(self):
        return gui_ai_view.create_ai_insights_page(self)

    def refresh_ai_insights(self):
        gui_ai_view.refresh_ai_insights(self)

    def create_landing_page(self):
        page = tk.Frame(self.content_container, bg=theme.BG_MAIN)
        
        # Center container
        center_frame = tk.Frame(page, bg=theme.BG_MAIN)
        center_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # App Title
        tk.Label(
            center_frame, 
            text="⚡ FINSIGHT", 
            font=("Segoe UI", 32, "bold"), 
            fg=theme.ACCENT, 
            bg=theme.BG_MAIN
        ).pack(pady=(0, 2))

        tk.Label(
            center_frame, 
            text="Smart Financial Intelligence & Business Management System", 
            font=("Segoe UI", 12, "bold"), 
            fg=theme.TEXT_PRIMARY, 
            bg=theme.BG_MAIN
        ).pack(pady=(0, 6))
        
        tk.Label(
            center_frame, 
            text="Choose a portal to manage your personal savings or business operations", 
            font=("Segoe UI", 12), 
            fg=theme.TEXT_MUTED, 
            bg=theme.BG_MAIN
        ).pack(pady=(0, 40))
        
        # Grid for cards
        grid_frame = tk.Frame(center_frame, bg=theme.BG_MAIN)
        grid_frame.pack()
        
        # Card 1: Personal Finance
        card1 = tk.Frame(grid_frame, bg=theme.BG_CARD, highlightbackground=theme.BORDER, highlightthickness=1, width=320, height=420)
        card1.grid(row=0, column=0, padx=25, pady=10)
        card1.pack_propagate(False)
        
        tk.Label(card1, text="✨", font=("Segoe UI", 36), bg=theme.BG_CARD).pack(pady=(20, 5))
        tk.Label(card1, text="Personal Finance", font=("Segoe UI", 18, "bold"), fg=theme.TEXT_PRIMARY, bg=theme.BG_CARD).pack(pady=5)
        
        desc1 = (
            "• Smart Budget Tracking & Limits\n"
            "• ⚡ Insight Engine & Spending Forecast\n"
            "• Smart Spending Alerts & Goal Planner\n"
            "• Financial Health Profile Score\n"
            "• Automated PDF/Excel Reports"
        )
        tk.Label(card1, text=desc1, font=("Segoe UI", 10), fg=theme.TEXT_MUTED, bg=theme.BG_CARD, justify="left").pack(pady=15, padx=20)
        
        btn1 = tk.Button(
            card1,
            text="Launch Personal Portal",
            font=theme.FONT_BODY_BOLD,
            bg=theme.ACCENT,
            fg=theme.TEXT_DARK,
            activebackground=theme.ACCENT,
            bd=0,
            padx=20,
            pady=10,
            cursor="hand2",
            command=lambda: self.launch_portal("Personal")
        )
        btn1.pack(side="bottom", pady=25)
        
        # Card 2: Business Finance ERP
        card2 = tk.Frame(grid_frame, bg=theme.BG_CARD, highlightbackground=theme.BORDER, highlightthickness=1, width=320, height=420)
        card2.grid(row=0, column=1, padx=25, pady=10)
        card2.pack_propagate(False)
        
        tk.Label(card2, text="🏢", font=("Segoe UI", 36), bg=theme.BG_CARD).pack(pady=(20, 5))
        tk.Label(card2, text="Business Finance ERP", font=("Segoe UI", 18, "bold"), fg=theme.TEXT_PRIMARY, bg=theme.BG_CARD).pack(pady=5)
        
        desc2 = (
            "• Daily Sales & OpEx Ledger\n"
            "• Profit & Loss (P&L) Statements\n"
            "• Inventory & Restock Alerts\n"
            "• Customers & Vendors Tracker\n"
            "• GST & Cash Flow Analyzers\n"
            "• Automated PDF Invoice Generator"
        )
        tk.Label(card2, text=desc2, font=("Segoe UI", 10), fg=theme.TEXT_MUTED, bg=theme.BG_CARD, justify="left").pack(pady=15, padx=20)
        
        btn2 = tk.Button(
            card2,
            text="Launch Business ERP",
            font=theme.FONT_BODY_BOLD,
            bg=theme.INCOME,
            fg=theme.TEXT_DARK,
            activebackground=theme.INCOME,
            bd=0,
            padx=20,
            pady=10,
            cursor="hand2",
            command=lambda: self.launch_portal("Business")
        )
        btn2.pack(side="bottom", pady=25)
        
        # Seed initial business data if database is fresh
        self.seed_business_sample_data()
        
        return page

    def launch_portal(self, mode):
        self.load_sidebar_menu(mode)
        if mode == "Personal":
            self.switch_page("dashboard")
        else:
            self.switch_page("biz_dashboard")

    def load_sidebar_menu(self, mode):
        # Clear existing widgets from sidebar
        for child in self.sidebar.winfo_children():
            child.destroy()
            
        # Add a back to hub button at the very top
        btn_hub = tk.Button(
            self.sidebar,
            text="🏠 Back to Selection Hub",
            font=theme.FONT_SMALL,
            fg=theme.ACCENT,
            bg=theme.BG_SIDEBAR,
            activebackground=theme.BG_SIDEBAR,
            activeforeground=theme.ACCENT,
            bd=0,
            padx=10,
            pady=10,
            cursor="hand2",
            command=lambda: self.switch_page("landing")
        )
        btn_hub.pack(fill="x", pady=(10, 5), padx=10)
        
        # Add horizontal separator line
        sep = tk.Frame(self.sidebar, bg=theme.BORDER, height=1)
        sep.pack(fill="x", padx=10, pady=5)
        
        if mode == "Personal":
            header_lbl = tk.Label(
                self.sidebar, 
                text="✨ Personal Finance", 
                fg=theme.ACCENT, 
                bg=theme.BG_SIDEBAR, 
                font=theme.FONT_SUBTITLE
            )
            header_lbl.pack(pady=(10, 20), padx=10)
            
            menu_items = [
                ("dashboard", "📊 Dashboard"),
                ("transactions", "💸 Transactions"),
                ("goals", "🎯 Saving Goals"),
                ("subscriptions", "⏰ Subscriptions"),
                ("suggestions", "💡 Smart Suggestions"),
                ("exports", "📈 Insights & Exports"),
                ("ai_insights", "⚡ Insight Engine")
            ]
        else: # Business
            header_lbl = tk.Label(
                self.sidebar, 
                text="🏢 Business ERP", 
                fg=theme.INCOME, 
                bg=theme.BG_SIDEBAR, 
                font=theme.FONT_SUBTITLE
            )
            header_lbl.pack(pady=(10, 20), padx=10)
            
            menu_items = [
                ("biz_dashboard", "💼 ERP Dashboard"),
                ("biz_sales", "📈 Daily Sales"),
                ("biz_expenses", "💸 Expenses"),
                ("biz_pl", "📊 P&L Calculator"),
                ("biz_inventory", "📦 Inventory Tracker"),
                ("biz_customers", "👥 Customers"),
                ("biz_vendors", "🤝 Vendor Ledger"),
                ("biz_monthly", "📅 Monthly Reports"),
                ("biz_gst", "🧮 GST Calculator"),
                ("biz_cashflow", "🌊 Cash Flow"),
                ("biz_payroll", "👥 Employee Payroll"),
                ("biz_invoice", "🧾 Invoice Generator")
            ]
            
        self.nav_buttons = {}
        for page_name, label in menu_items:
            btn = tk.Button(
                self.sidebar,
                text=label,
                font=theme.FONT_BODY_BOLD,
                fg=theme.TEXT_MUTED,
                bg=theme.BG_SIDEBAR,
                bd=0,
                activebackground=theme.BG_CARD,
                activeforeground=theme.TEXT_PRIMARY,
                anchor="w",
                padx=20,
                pady=7 if mode == "Business" else 12,
                cursor="hand2",
                command=lambda name=page_name: self.switch_page(name)
            )
            btn.pack(fill="x", padx=10, pady=1)
            self.nav_buttons[page_name] = btn

    def refresh_biz_page(self, page_name):
        if page_name == "biz_dashboard":
            self.refresh_biz_dashboard()
        elif page_name == "biz_sales":
            self.refresh_biz_sales()
        elif page_name == "biz_expenses":
            self.refresh_biz_expenses()
        elif page_name == "biz_pl":
            self.refresh_biz_pl()
        elif page_name == "biz_inventory":
            self.refresh_biz_inventory()
        elif page_name == "biz_customers":
            self.refresh_biz_customers()
        elif page_name == "biz_vendors":
            self.refresh_biz_vendors()
        elif page_name == "biz_monthly":
            self.refresh_biz_monthly()
        elif page_name == "biz_cashflow":
            self.refresh_biz_cashflow()
        elif page_name == "biz_payroll":
            self.refresh_biz_payroll()

    # ==========================================
    # --- BUSINESS MODULES ---
    # ==========================================

    def create_biz_dashboard_page(self):
        page = ScrollableFrame(self.content_container)
        frame = page.scrollable_frame
        
        # 1. Header
        top_bar = tk.Frame(frame, bg=theme.BG_MAIN)
        top_bar.pack(fill="x", padx=20, pady=15)
        tk.Label(top_bar, text="Business Suite ERP Dashboard", font=theme.FONT_TITLE, fg=theme.TEXT_PRIMARY, bg=theme.BG_MAIN).pack(side="left")
        
        # 2. Executive Summaries (Sales, OpEx, Profit)
        cards_frame = tk.Frame(frame, bg=theme.BG_MAIN)
        cards_frame.pack(fill="x", padx=20, pady=5)
        cards_frame.columnconfigure((0, 1, 2), weight=1)
        
        # Card 1: Revenue
        c1 = tk.Frame(cards_frame, bg=theme.BG_CARD, highlightbackground=theme.BORDER, highlightthickness=1)
        c1.grid(row=0, column=0, padx=10, sticky="ew")
        tk.Label(c1, text="GROSS REVENUE", font=theme.FONT_SMALL, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).pack(anchor="w", padx=15, pady=(15, 2))
        self.biz_rev_lbl = tk.Label(c1, text="₹0.00", font=theme.FONT_TITLE, fg=theme.INCOME, bg=theme.BG_CARD)
        self.biz_rev_lbl.pack(anchor="w", padx=15, pady=(2, 15))
        
        # Card 2: Expenses
        c2 = tk.Frame(cards_frame, bg=theme.BG_CARD, highlightbackground=theme.BORDER, highlightthickness=1)
        c2.grid(row=0, column=1, padx=10, sticky="ew")
        tk.Label(c2, text="OPERATIONAL EXPENSES", font=theme.FONT_SMALL, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).pack(anchor="w", padx=15, pady=(15, 2))
        self.biz_exp_lbl = tk.Label(c2, text="₹0.00", font=theme.FONT_TITLE, fg=theme.EXPENSE, bg=theme.BG_CARD)
        self.biz_exp_lbl.pack(anchor="w", padx=15, pady=(2, 15))
        
        # Card 3: Profit
        c3 = tk.Frame(cards_frame, bg=theme.BG_CARD, highlightbackground=theme.BORDER, highlightthickness=1)
        c3.grid(row=0, column=2, padx=10, sticky="ew")
        tk.Label(c3, text="NET PROFIT / LOSS", font=theme.FONT_SMALL, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).pack(anchor="w", padx=15, pady=(15, 2))
        self.biz_profit_lbl = tk.Label(c3, text="₹0.00", font=theme.FONT_TITLE, fg=theme.TEXT_PRIMARY, bg=theme.BG_CARD)
        self.biz_profit_lbl.pack(anchor="w", padx=15, pady=(2, 15))

        # 3. Middle Section (Health circular gauge, AI Heuristic alerts, advisor)
        mid_frame = tk.Frame(frame, bg=theme.BG_MAIN)
        mid_frame.pack(fill="x", padx=20, pady=15)
        mid_frame.columnconfigure(0, weight=1)
        mid_frame.columnconfigure(1, weight=1)
        
        # Left Panel: Health Score & Trend Prediction
        left_panel = tk.Frame(mid_frame, bg=theme.BG_CARD, highlightbackground=theme.BORDER, highlightthickness=1)
        left_panel.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        
        tk.Label(left_panel, text="Business Health & Trajectory", font=theme.FONT_BODY_BOLD, fg=theme.TEXT_PRIMARY, bg=theme.BG_CARD).pack(anchor="w", padx=15, pady=10)
        
        # Dial Frame
        dial_frame = tk.Frame(left_panel, bg=theme.BG_CARD)
        dial_frame.pack(pady=5)
        self.biz_health_gauge = theme.CircularGauge(dial_frame, size=140)
        self.biz_health_gauge.pack()
        
        # Prediction
        pred_box = tk.Frame(left_panel, bg=theme.BG_MAIN, highlightbackground=theme.BORDER, highlightthickness=1)
        pred_box.pack(fill="x", padx=15, pady=(10, 15))
        tk.Label(pred_box, text="📈 Next Month Profit Prediction (Moving Average):", font=theme.FONT_SMALL, fg=theme.TEXT_MUTED, bg=theme.BG_MAIN).pack(anchor="w", padx=10, pady=(5, 2))
        self.biz_pred_lbl = tk.Label(pred_box, text="₹0.00", font=theme.FONT_BODY_BOLD, fg=theme.ACCENT, bg=theme.BG_MAIN)
        self.biz_pred_lbl.pack(anchor="w", padx=10, pady=(2, 5))
        
        # Right Panel: AI Expense Analyzer & Smart Saving suggestions
        right_panel = tk.Frame(mid_frame, bg=theme.BG_CARD, highlightbackground=theme.BORDER, highlightthickness=1)
        right_panel.grid(row=0, column=1, padx=(10, 0), sticky="nsew")
        
        tk.Label(right_panel, text="AI Audits & Opportunities", font=theme.FONT_BODY_BOLD, fg=theme.TEXT_PRIMARY, bg=theme.BG_CARD).pack(anchor="w", padx=15, pady=10)
        
        # Alert Box 1: Expense Analyzer
        self.biz_analyzer_box = tk.Frame(right_panel, bg="#450a0a", highlightbackground=theme.EXPENSE, highlightthickness=1)
        self.biz_analyzer_box.pack(fill="x", padx=15, pady=5)
        
        # Alert Box 2: Smart Saving Suggestions
        self.biz_savings_box = tk.Frame(right_panel, bg="#451e0a", highlightbackground=theme.WARNING, highlightthickness=1)
        self.biz_savings_box.pack(fill="x", padx=15, pady=5)
        
        # Smart Purchase Advisor
        adv_box = tk.Frame(right_panel, bg=theme.BG_MAIN, highlightbackground=theme.BORDER, highlightthickness=1)
        adv_box.pack(fill="x", padx=15, pady=(10, 15))
        tk.Label(adv_box, text="🛒 Smart Purchase Advisor", font=theme.FONT_SMALL, fg=theme.TEXT_MUTED, bg=theme.BG_MAIN).pack(anchor="w", padx=10, pady=(5, 2))
        
        adv_inputs = tk.Frame(adv_box, bg=theme.BG_MAIN)
        adv_inputs.pack(fill="x", padx=10, pady=2)
        
        self.adv_name_var = tk.StringVar()
        self.adv_price_var = tk.StringVar()
        
        tk.Entry(adv_inputs, textvariable=self.adv_name_var, font=theme.FONT_BODY, bg=theme.BG_CARD, fg=theme.TEXT_PRIMARY, insertbackground="white", width=12).pack(side="left", padx=2)
        self.adv_name_var.set("Printer")
        
        tk.Entry(adv_inputs, textvariable=self.adv_price_var, font=theme.FONT_BODY, bg=theme.BG_CARD, fg=theme.TEXT_PRIMARY, insertbackground="white", width=8).pack(side="left", padx=2)
        self.adv_price_var.set("15000")
        
        tk.Button(adv_inputs, text="Advise", font=theme.FONT_SMALL, bg=theme.ACCENT, fg=theme.TEXT_DARK, bd=0, padx=6, pady=2, command=self.run_advisor_action).pack(side="left", padx=5)

        # 4. Chart Visualization Panel
        chart_box = tk.Frame(frame, bg=theme.BG_CARD, highlightbackground=theme.BORDER, highlightthickness=1)
        chart_box.pack(fill="x", padx=20, pady=(0, 20))
        
        tk.Label(chart_box, text="Financial & Cash Flow Diagnostics Grid", font=theme.FONT_BODY_BOLD, fg=theme.TEXT_PRIMARY, bg=theme.BG_CARD).pack(anchor="w", padx=15, pady=10)
        
        self.biz_charts_container = tk.Frame(chart_box, bg=theme.BG_CARD)
        self.biz_charts_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 4b. AI Weakness Auditor Panel
        self.weakness_card = tk.Frame(frame, bg=theme.BG_CARD, highlightbackground=theme.BORDER, highlightthickness=1)
        self.weakness_card.pack(fill="x", padx=20, pady=(0, 20))
        
        # 5. Top Metrics details (Top product, Top Customer, Top Expense)
        bottom_grid = tk.Frame(frame, bg=theme.BG_MAIN)
        bottom_grid.pack(fill="x", padx=20, pady=(0, 20))
        bottom_grid.columnconfigure((0, 1, 2), weight=1)
        
        t1 = tk.Frame(bottom_grid, bg=theme.BG_CARD, highlightbackground=theme.BORDER, highlightthickness=1)
        t1.grid(row=0, column=0, padx=10, sticky="ew")
        tk.Label(t1, text="Top Selling Product", font=theme.FONT_SMALL, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).pack(anchor="w", padx=15, pady=(10, 2))
        self.biz_top_prod_lbl = tk.Label(t1, text="-", font=theme.FONT_BODY_BOLD, fg=theme.TEXT_PRIMARY, bg=theme.BG_CARD)
        self.biz_top_prod_lbl.pack(anchor="w", padx=15, pady=(2, 10))
        
        t2 = tk.Frame(bottom_grid, bg=theme.BG_CARD, highlightbackground=theme.BORDER, highlightthickness=1)
        t2.grid(row=0, column=1, padx=10, sticky="ew")
        tk.Label(t2, text="Top Customer", font=theme.FONT_SMALL, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).pack(anchor="w", padx=15, pady=(10, 2))
        self.biz_top_cust_lbl = tk.Label(t2, text="-", font=theme.FONT_BODY_BOLD, fg=theme.TEXT_PRIMARY, bg=theme.BG_CARD)
        self.biz_top_cust_lbl.pack(anchor="w", padx=15, pady=(2, 10))
        
        t3 = tk.Frame(bottom_grid, bg=theme.BG_CARD, highlightbackground=theme.BORDER, highlightthickness=1)
        t3.grid(row=0, column=2, padx=10, sticky="ew")
        tk.Label(t3, text="Top Expense", font=theme.FONT_SMALL, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).pack(anchor="w", padx=15, pady=(10, 2))
        self.biz_top_exp_lbl = tk.Label(t3, text="-", font=theme.FONT_BODY_BOLD, fg=theme.TEXT_PRIMARY, bg=theme.BG_CARD)
        self.biz_top_exp_lbl.pack(anchor="w", padx=15, pady=(2, 10))
        
        return page

    def run_advisor_action(self):
        item = self.adv_name_var.get()
        p_str = clean_amount_str(self.adv_price_var.get())
        try:
            price = float(p_str)
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid numeric price.")
            return
            
        stats = self.get_biz_stats()
        # Remaining budget target is 50000 - monthly expenses (or simulate)
        rem_budget = max(0.0, 50000.0 - stats["expenses"])
        
        adv = analytics.run_smart_purchase_advisor(item, price, rem_budget)
        
        # Show advise in popup
        title = "🛒 Smart Advisor Verdict"
        status_word = "EXCEEDED" if adv["status"] == "exceeded" else "APPROVED"
        color = "red" if adv["status"] == "exceeded" else "green"
        msg = f"Item: {item}\nPrice: ₹{price:,.2f}\n\nStatus: {status_word}\n\nWarning:\n{adv['warning']}\n\nRecommendation:\n{adv['recommendation']}"
        
        messagebox.showinfo(title, msg)

    def create_biz_sales_page(self):
        page = ScrollableFrame(self.content_container)
        frame = page.scrollable_frame
        
        # Header
        top_bar = tk.Frame(frame, bg=theme.BG_MAIN)
        top_bar.pack(fill="x", padx=20, pady=15)
        tk.Label(top_bar, text="Daily Sales Entry Ledger", font=theme.FONT_TITLE, fg=theme.TEXT_PRIMARY, bg=theme.BG_MAIN).pack(side="left")
        
        # Today's Sales Banner
        self.biz_today_sales_lbl = tk.Label(top_bar, text="Today's Sales = ₹0.00", font=theme.FONT_SUBTITLE, fg=theme.INCOME, bg=theme.BG_MAIN)
        self.biz_today_sales_lbl.pack(side="right", padx=10)
        
        # Entry Grid
        entry_box = tk.Frame(frame, bg=theme.BG_CARD, highlightbackground=theme.BORDER, highlightthickness=1)
        entry_box.pack(fill="x", padx=20, pady=5)
        
        # Customer Name, Invoice, Amount, Date, Payment method
        fields = [("Date (YYYY-MM-DD)", "UPI"), ("Customer Name", ""), ("Invoice No.", ""), ("Amount (₹)", ""), ("Payment Method", "combobox")]
        
        grid_f = tk.Frame(entry_box, bg=theme.BG_CARD)
        grid_f.pack(padx=15, pady=15, fill="x")
        
        self.sale_date_var = tk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        self.sale_cust_var = tk.StringVar()
        self.sale_inv_var = tk.StringVar()
        self.sale_amt_var = tk.StringVar()
        self.sale_method_var = tk.StringVar(value="UPI")
        
        # Date
        tk.Label(grid_f, text="Date", font=theme.FONT_SMALL, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).grid(row=0, column=0, padx=5, sticky="w")
        tk.Entry(grid_f, textvariable=self.sale_date_var, font=theme.FONT_BODY, bg=theme.BG_MAIN, fg=theme.TEXT_PRIMARY, insertbackground="white", width=12).grid(row=1, column=0, padx=5, pady=2)
        
        # Customer
        tk.Label(grid_f, text="Customer Name", font=theme.FONT_SMALL, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).grid(row=0, column=1, padx=5, sticky="w")
        tk.Entry(grid_f, textvariable=self.sale_cust_var, font=theme.FONT_BODY, bg=theme.BG_MAIN, fg=theme.TEXT_PRIMARY, insertbackground="white", width=18).grid(row=1, column=1, padx=5, pady=2)
        
        # Invoice
        tk.Label(grid_f, text="Invoice No.", font=theme.FONT_SMALL, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).grid(row=0, column=2, padx=5, sticky="w")
        tk.Entry(grid_f, textvariable=self.sale_inv_var, font=theme.FONT_BODY, bg=theme.BG_MAIN, fg=theme.TEXT_PRIMARY, insertbackground="white", width=12).grid(row=1, column=2, padx=5, pady=2)
        
        # Amount
        tk.Label(grid_f, text="Amount (₹)", font=theme.FONT_SMALL, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).grid(row=0, column=3, padx=5, sticky="w")
        tk.Entry(grid_f, textvariable=self.sale_amt_var, font=theme.FONT_BODY, bg=theme.BG_MAIN, fg=theme.TEXT_PRIMARY, insertbackground="white", width=12).grid(row=1, column=3, padx=5, pady=2)
        
        # Method
        tk.Label(grid_f, text="Payment Method", font=theme.FONT_SMALL, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).grid(row=0, column=4, padx=5, sticky="w")
        meth_cb = ttk.Combobox(grid_f, textvariable=self.sale_method_var, values=["UPI", "Cash", "Card", "Net Banking"], width=12, state="readonly")
        meth_cb.grid(row=1, column=4, padx=5, pady=2)
        
        # Add button
        tk.Button(grid_f, text="Add Sale Entry", font=theme.FONT_BODY_BOLD, bg=theme.INCOME, fg=theme.TEXT_DARK, bd=0, padx=15, pady=5, command=self.add_sale_action).grid(row=1, column=5, padx=15)
        
        # Ledger table
        t_box = tk.Frame(frame, bg=theme.BG_CARD, highlightbackground=theme.BORDER, highlightthickness=1)
        t_box.pack(fill="both", expand=True, padx=20, pady=15)
        
        scroll_y = ttk.Scrollbar(t_box, orient="vertical")
        columns = ("id", "date", "customer", "invoice", "amount", "method")
        self.sales_tree = ttk.Treeview(t_box, columns=columns, show="headings", yscrollcommand=scroll_y.set, style="Custom.Treeview", height=12)
        scroll_y.config(command=self.sales_tree.yview)
        scroll_y.pack(side="right", fill="y")
        
        self.sales_tree.heading("id", text="ID")
        self.sales_tree.heading("date", text="Date")
        self.sales_tree.heading("customer", text="Customer")
        self.sales_tree.heading("invoice", text="Invoice No")
        self.sales_tree.heading("amount", text="Amount")
        self.sales_tree.heading("method", text="Payment Method")
        
        self.sales_tree.column("id", width=40, anchor="center")
        self.sales_tree.column("date", width=90, anchor="center")
        self.sales_tree.column("customer", width=160, anchor="w")
        self.sales_tree.column("invoice", width=95, anchor="center")
        self.sales_tree.column("amount", width=100, anchor="e")
        self.sales_tree.column("method", width=110, anchor="center")
        
        self.sales_tree.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.sales_tree.bind("<Double-1>", self.on_double_click_sales)
        
        return page

    def add_sale_action(self):
        dt = self.sale_date_var.get()
        cust = self.sale_cust_var.get().strip()
        inv = self.sale_inv_var.get().strip()
        amt_str = clean_amount_str(self.sale_amt_var.get())
        meth = self.sale_method_var.get()
        
        if not cust or not amt_str:
            messagebox.showerror("Error", "Please enter Customer Name and Amount.")
            return
            
        try:
            amt = float(amt_str)
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid numeric amount.")
            return
            
        self.tracker.db.add_business_sale(dt, cust, inv, amt, meth)
        
        # Clear fields
        self.sale_cust_var.set("")
        self.sale_inv_var.set("")
        self.sale_amt_var.set("")
        
        self.refresh_biz_sales()

    def on_double_click_sales(self, event):
        item = self.sales_tree.focus()
        if not item:
            return
        vals = self.sales_tree.item(item, "values")
        tx_id = int(vals[0])
        
        ans = messagebox.askyesno("🗑 Delete Sale Entry", f"Are you sure you want to delete this sale transaction (ID: {tx_id})?", icon="warning")
        if ans:
            self.tracker.db.delete_business_sale(tx_id)
            self.refresh_biz_sales()

    def create_biz_expenses_page(self):
        page = ScrollableFrame(self.content_container)
        frame = page.scrollable_frame
        
        # Header
        top_bar = tk.Frame(frame, bg=theme.BG_MAIN)
        top_bar.pack(fill="x", padx=20, pady=15)
        tk.Label(top_bar, text="Business Expenses Entry Ledger", font=theme.FONT_TITLE, fg=theme.TEXT_PRIMARY, bg=theme.BG_MAIN).pack(side="left")
        
        # Entry Grid
        entry_box = tk.Frame(frame, bg=theme.BG_CARD, highlightbackground=theme.BORDER, highlightthickness=1)
        entry_box.pack(fill="x", padx=20, pady=5)
        
        grid_f = tk.Frame(entry_box, bg=theme.BG_CARD)
        grid_f.pack(padx=15, pady=15, fill="x")
        
        self.exp_date_var = tk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        self.exp_cat_var = tk.StringVar(value="Miscellaneous")
        self.exp_amt_var = tk.StringVar()
        self.exp_notes_var = tk.StringVar()
        
        categories = ["Employee Salary", "Electricity Bill", "Internet", "Office Rent", "Marketing", "Transportation", "Raw Material", "Miscellaneous"]
        
        # Date
        tk.Label(grid_f, text="Date", font=theme.FONT_SMALL, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).grid(row=0, column=0, padx=5, sticky="w")
        tk.Entry(grid_f, textvariable=self.exp_date_var, font=theme.FONT_BODY, bg=theme.BG_MAIN, fg=theme.TEXT_PRIMARY, insertbackground="white", width=12).grid(row=1, column=0, padx=5, pady=2)
        
        # Category
        tk.Label(grid_f, text="Category", font=theme.FONT_SMALL, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).grid(row=0, column=1, padx=5, sticky="w")
        cat_cb = ttk.Combobox(grid_f, textvariable=self.exp_cat_var, values=categories, width=18, state="readonly")
        cat_cb.grid(row=1, column=1, padx=5, pady=2)
        
        # Amount
        tk.Label(grid_f, text="Amount (₹)", font=theme.FONT_SMALL, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).grid(row=0, column=2, padx=5, sticky="w")
        tk.Entry(grid_f, textvariable=self.exp_amt_var, font=theme.FONT_BODY, bg=theme.BG_MAIN, fg=theme.TEXT_PRIMARY, insertbackground="white", width=12).grid(row=1, column=2, padx=5, pady=2)
        
        # Notes
        tk.Label(grid_f, text="Notes", font=theme.FONT_SMALL, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).grid(row=0, column=3, padx=5, sticky="w")
        tk.Entry(grid_f, textvariable=self.exp_notes_var, font=theme.FONT_BODY, bg=theme.BG_MAIN, fg=theme.TEXT_PRIMARY, insertbackground="white", width=20).grid(row=1, column=3, padx=5, pady=2)
        
        # Add button
        tk.Button(grid_f, text="Add Expense Entry", font=theme.FONT_BODY_BOLD, bg=theme.EXPENSE, fg=theme.TEXT_PRIMARY, bd=0, padx=15, pady=5, command=self.add_expense_action).grid(row=1, column=4, padx=15)
        
        # Ledger table
        t_box = tk.Frame(frame, bg=theme.BG_CARD, highlightbackground=theme.BORDER, highlightthickness=1)
        t_box.pack(fill="both", expand=True, padx=20, pady=15)
        
        scroll_y = ttk.Scrollbar(t_box, orient="vertical")
        columns = ("id", "date", "category", "amount", "notes")
        self.exp_tree = ttk.Treeview(t_box, columns=columns, show="headings", yscrollcommand=scroll_y.set, style="Custom.Treeview", height=12)
        scroll_y.config(command=self.exp_tree.yview)
        scroll_y.pack(side="right", fill="y")
        
        self.exp_tree.heading("id", text="ID")
        self.exp_tree.heading("date", text="Date")
        self.exp_tree.heading("category", text="Category")
        self.exp_tree.heading("amount", text="Amount")
        self.exp_tree.heading("notes", text="Notes")
        
        self.exp_tree.column("id", width=40, anchor="center")
        self.exp_tree.column("date", width=95, anchor="center")
        self.exp_tree.column("category", width=140, anchor="w")
        self.exp_tree.column("amount", width=105, anchor="e")
        self.exp_tree.column("notes", width=250, anchor="w")
        
        self.exp_tree.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.exp_tree.bind("<Double-1>", self.on_double_click_expenses)
        
        return page

    def add_expense_action(self):
        dt = self.exp_date_var.get()
        cat = self.exp_cat_var.get()
        amt_str = clean_amount_str(self.exp_amt_var.get())
        notes = self.exp_notes_var.get().strip()
        
        if not amt_str:
            messagebox.showerror("Error", "Please enter an Amount.")
            return
            
        try:
            amt = float(amt_str)
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid numeric amount.")
            return
            
        self.tracker.db.add_business_expense(dt, cat, amt, notes)
        
        # Clear fields
        self.exp_amt_var.set("")
        self.exp_notes_var.set("")
        
        self.refresh_biz_expenses()

    def on_double_click_expenses(self, event):
        item = self.exp_tree.focus()
        if not item:
            return
        vals = self.exp_tree.item(item, "values")
        tx_id = int(vals[0])
        
        ans = messagebox.askyesno("🗑 Delete Expense Entry", f"Are you sure you want to delete this expense transaction (ID: {tx_id})?", icon="warning")
        if ans:
            self.tracker.db.delete_business_expense(tx_id)
            self.refresh_biz_expenses()

    def create_biz_pl_page(self):
        page = ScrollableFrame(self.content_container)
        frame = page.scrollable_frame
        
        # Header
        top_bar = tk.Frame(frame, bg=theme.BG_MAIN)
        top_bar.pack(fill="x", padx=20, pady=15)
        tk.Label(top_bar, text="Profit / Loss (P&L) Statements", font=theme.FONT_TITLE, fg=theme.TEXT_PRIMARY, bg=theme.BG_MAIN).pack(side="left")
        
        # Statement Box
        self.pl_card = tk.Frame(frame, bg=theme.BG_CARD, highlightbackground=theme.BORDER, highlightthickness=1)
        self.pl_card.pack(fill="x", padx=20, pady=10)
        
        self.pl_title_lbl = tk.Label(self.pl_card, text="PROFIT CALCULATOR", font=theme.FONT_BODY_BOLD, fg=theme.TEXT_PRIMARY, bg=theme.BG_CARD)
        self.pl_title_lbl.pack(pady=(15, 5))
        
        self.pl_value_lbl = tk.Label(self.pl_card, text="Profit = ₹0.00", font=("Segoe UI", 24, "bold"), fg=theme.INCOME, bg=theme.BG_CARD)
        self.pl_value_lbl.pack(pady=(5, 15))
        
        # Details list
        self.pl_details_box = tk.Frame(frame, bg=theme.BG_CARD, highlightbackground=theme.BORDER, highlightthickness=1)
        self.pl_details_box.pack(fill="both", expand=True, padx=20, pady=15)
        
        return page

    def create_biz_inventory_page(self):
        page = ScrollableFrame(self.content_container)
        frame = page.scrollable_frame
        
        # Header
        top_bar = tk.Frame(frame, bg=theme.BG_MAIN)
        top_bar.pack(fill="x", padx=20, pady=15)
        tk.Label(top_bar, text="Business Inventory Tracker", font=theme.FONT_TITLE, fg=theme.TEXT_PRIMARY, bg=theme.BG_MAIN).pack(side="left")
        
        # Alert Box
        self.biz_alert_frame = tk.Frame(frame, bg=theme.BG_MAIN)
        self.biz_alert_frame.pack(fill="x", padx=20, pady=5)
        
        # Add item Form
        entry_box = tk.Frame(frame, bg=theme.BG_CARD, highlightbackground=theme.BORDER, highlightthickness=1)
        entry_box.pack(fill="x", padx=20, pady=5)
        
        grid_f = tk.Frame(entry_box, bg=theme.BG_CARD)
        grid_f.pack(padx=15, pady=15, fill="x")
        
        self.inv_name_var = tk.StringVar()
        self.inv_stock_var = tk.StringVar()
        
        tk.Label(grid_f, text="Item Name / Model", font=theme.FONT_SMALL, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).grid(row=0, column=0, padx=5, sticky="w")
        tk.Entry(grid_f, textvariable=self.inv_name_var, font=theme.FONT_BODY, bg=theme.BG_MAIN, fg=theme.TEXT_PRIMARY, insertbackground="white", width=25).grid(row=1, column=0, padx=5, pady=2)
        
        tk.Label(grid_f, text="Initial Stock Count", font=theme.FONT_SMALL, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).grid(row=0, column=1, padx=5, sticky="w")
        tk.Entry(grid_f, textvariable=self.inv_stock_var, font=theme.FONT_BODY, bg=theme.BG_MAIN, fg=theme.TEXT_PRIMARY, insertbackground="white", width=12).grid(row=1, column=1, padx=5, pady=2)
        
        tk.Button(grid_f, text="Add / Update Product", font=theme.FONT_BODY_BOLD, bg=theme.ACCENT, fg=theme.TEXT_DARK, bd=0, padx=15, pady=5, command=self.add_inventory_action).grid(row=1, column=2, padx=15)
        
        # Inventory Table
        t_box = tk.Frame(frame, bg=theme.BG_CARD, highlightbackground=theme.BORDER, highlightthickness=1)
        t_box.pack(fill="both", expand=True, padx=20, pady=15)
        
        scroll_y = ttk.Scrollbar(t_box, orient="vertical")
        columns = ("id", "name", "stock", "sold", "remaining")
        self.inv_tree = ttk.Treeview(t_box, columns=columns, show="headings", yscrollcommand=scroll_y.set, style="Custom.Treeview", height=12)
        scroll_y.config(command=self.inv_tree.yview)
        scroll_y.pack(side="right", fill="y")
        
        self.inv_tree.heading("id", text="ID")
        self.inv_tree.heading("name", text="Product Name")
        self.inv_tree.heading("stock", text="Total Stock")
        self.inv_tree.heading("sold", text="Sold")
        self.inv_tree.heading("remaining", text="Remaining")
        
        self.inv_tree.column("id", width=40, anchor="center")
        self.inv_tree.column("name", width=220, anchor="w")
        self.inv_tree.column("stock", width=95, anchor="center")
        self.inv_tree.column("sold", width=95, anchor="center")
        self.inv_tree.column("remaining", width=95, anchor="center")
        
        self.inv_tree.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Buttons for quick interaction below table
        btn_box = tk.Frame(frame, bg=theme.BG_MAIN)
        btn_box.pack(fill="x", padx=20, pady=(0, 15))
        
        tk.Button(btn_box, text="⚡ Mark 1 Sold", font=theme.FONT_SMALL, bg=theme.INCOME, fg=theme.TEXT_DARK, bd=0, padx=12, pady=6, command=self.quick_sell_action).pack(side="left", padx=5)
        tk.Button(btn_box, text="📥 Restock +10", font=theme.FONT_SMALL, bg=theme.ACCENT, fg=theme.TEXT_DARK, bd=0, padx=12, pady=6, command=self.quick_restock_action).pack(side="left", padx=5)
        tk.Button(btn_box, text="🗑 Delete Product", font=theme.FONT_SMALL, bg=theme.EXPENSE, fg=theme.TEXT_PRIMARY, bd=0, padx=12, pady=6, command=self.delete_inventory_action).pack(side="right", padx=5)
        
        return page

    def add_inventory_action(self):
        name = self.inv_name_var.get().strip()
        stock_str = clean_amount_str(self.inv_stock_var.get())
        if not name or not stock_str:
            messagebox.showerror("Error", "Please fill in all fields.")
            return
        try:
            stock = int(stock_str)
        except ValueError:
            messagebox.showerror("Error", "Stock count must be an integer.")
            return
            
        self.tracker.db.add_inventory_item(name, stock)
        self.inv_name_var.set("")
        self.inv_stock_var.set("")
        self.refresh_biz_inventory()

    def quick_sell_action(self):
        selected = self.inv_tree.focus()
        if not selected:
            messagebox.showwarning("Warning", "Select a product from the table first.")
            return
        vals = self.inv_tree.item(selected, "values")
        id_ = int(vals[0])
        stock = int(vals[2])
        sold = int(vals[3]) + 1
        
        if sold > stock:
            messagebox.showerror("Error", "Sold count cannot exceed total stock!")
            return
            
        self.tracker.db.update_inventory_item(id_, stock, sold)
        self.refresh_biz_inventory()

    def quick_restock_action(self):
        selected = self.inv_tree.focus()
        if not selected:
            messagebox.showwarning("Warning", "Select a product from the table first.")
            return
        vals = self.inv_tree.item(selected, "values")
        id_ = int(vals[0])
        stock = int(vals[2]) + 10
        sold = int(vals[3])
        
        self.tracker.db.update_inventory_item(id_, stock, sold)
        self.refresh_biz_inventory()

    def delete_inventory_action(self):
        selected = self.inv_tree.focus()
        if not selected:
            messagebox.showwarning("Warning", "Select a product from the table first.")
            return
        vals = self.inv_tree.item(selected, "values")
        id_ = int(vals[0])
        
        ans = messagebox.askyesno("🗑 Delete Product", f"Delete '{vals[1]}' from catalog?", icon="warning")
        if ans:
            self.tracker.db.delete_inventory_item(id_)
            self.refresh_biz_inventory()

    def create_biz_customers_page(self):
        page = ScrollableFrame(self.content_container)
        frame = page.scrollable_frame
        
        # Header
        top_bar = tk.Frame(frame, bg=theme.BG_MAIN)
        top_bar.pack(fill="x", padx=20, pady=15)
        tk.Label(top_bar, text="Client & Customer Management", font=theme.FONT_TITLE, fg=theme.TEXT_PRIMARY, bg=theme.BG_MAIN).pack(side="left")
        
        # Customer Add Form
        entry_box = tk.Frame(frame, bg=theme.BG_CARD, highlightbackground=theme.BORDER, highlightthickness=1)
        entry_box.pack(fill="x", padx=20, pady=5)
        
        grid_f = tk.Frame(entry_box, bg=theme.BG_CARD)
        grid_f.pack(padx=15, pady=15, fill="x")
        
        self.cust_name_var = tk.StringVar()
        self.cust_phone_var = tk.StringVar()
        self.cust_pend_var = tk.StringVar(value="0")
        self.cust_paid_var = tk.StringVar(value="0")
        self.cust_due_var = tk.StringVar()
        
        # Customer Name
        tk.Label(grid_f, text="Customer Name", font=theme.FONT_SMALL, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).grid(row=0, column=0, padx=5, sticky="w")
        tk.Entry(grid_f, textvariable=self.cust_name_var, font=theme.FONT_BODY, bg=theme.BG_MAIN, fg=theme.TEXT_PRIMARY, insertbackground="white", width=18).grid(row=1, column=0, padx=5, pady=2)
        
        # Phone
        tk.Label(grid_f, text="Phone No.", font=theme.FONT_SMALL, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).grid(row=0, column=1, padx=5, sticky="w")
        tk.Entry(grid_f, textvariable=self.cust_phone_var, font=theme.FONT_BODY, bg=theme.BG_MAIN, fg=theme.TEXT_PRIMARY, insertbackground="white", width=12).grid(row=1, column=1, padx=5, pady=2)
        
        # Pending Amount
        tk.Label(grid_f, text="Pending Amount (₹)", font=theme.FONT_SMALL, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).grid(row=0, column=2, padx=5, sticky="w")
        tk.Entry(grid_f, textvariable=self.cust_pend_var, font=theme.FONT_BODY, bg=theme.BG_MAIN, fg=theme.TEXT_PRIMARY, insertbackground="white", width=12).grid(row=1, column=2, padx=5, pady=2)
        
        # Paid Amount
        tk.Label(grid_f, text="Paid Amount (₹)", font=theme.FONT_SMALL, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).grid(row=0, column=3, padx=5, sticky="w")
        tk.Entry(grid_f, textvariable=self.cust_paid_var, font=theme.FONT_BODY, bg=theme.BG_MAIN, fg=theme.TEXT_PRIMARY, insertbackground="white", width=12).grid(row=1, column=3, padx=5, pady=2)
        
        # Due Date
        tk.Label(grid_f, text="Due Date", font=theme.FONT_SMALL, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).grid(row=0, column=4, padx=5, sticky="w")
        tk.Entry(grid_f, textvariable=self.cust_due_var, font=theme.FONT_BODY, bg=theme.BG_MAIN, fg=theme.TEXT_PRIMARY, insertbackground="white", width=12).grid(row=1, column=4, padx=5, pady=2)
        self.cust_due_var.set(date.today().strftime("%Y-%m-%d"))
        
        tk.Button(grid_f, text="Add Customer", font=theme.FONT_BODY_BOLD, bg=theme.INCOME, fg=theme.TEXT_DARK, bd=0, padx=15, pady=5, command=self.add_customer_action).grid(row=1, column=5, padx=15)
        
        # Customer Table
        t_box = tk.Frame(frame, bg=theme.BG_CARD, highlightbackground=theme.BORDER, highlightthickness=1)
        t_box.pack(fill="both", expand=True, padx=20, pady=15)
        
        scroll_y = ttk.Scrollbar(t_box, orient="vertical")
        columns = ("id", "name", "phone", "pending", "paid", "due_date")
        self.cust_tree = ttk.Treeview(t_box, columns=columns, show="headings", yscrollcommand=scroll_y.set, style="Custom.Treeview", height=12)
        scroll_y.config(command=self.cust_tree.yview)
        scroll_y.pack(side="right", fill="y")
        
        self.cust_tree.heading("id", text="ID")
        self.cust_tree.heading("name", text="Customer Name")
        self.cust_tree.heading("phone", text="Phone No")
        self.cust_tree.heading("pending", text="Pending Amount")
        self.cust_tree.heading("paid", text="Paid Amount")
        self.cust_tree.heading("due_date", text="Due Date")
        
        self.cust_tree.column("id", width=40, anchor="center")
        self.cust_tree.column("name", width=180, anchor="w")
        self.cust_tree.column("phone", width=110, anchor="center")
        self.cust_tree.column("pending", width=120, anchor="e")
        self.cust_tree.column("paid", width=120, anchor="e")
        self.cust_tree.column("due_date", width=100, anchor="center")
        
        self.cust_tree.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Bottom controls: Record payment & delete
        btn_box = tk.Frame(frame, bg=theme.BG_MAIN)
        btn_box.pack(fill="x", padx=20, pady=(0, 15))
        
        self.rec_amt_var = tk.StringVar(value="1000")
        tk.Label(btn_box, text="Amount Received (₹):", font=theme.FONT_SMALL, fg=theme.TEXT_PRIMARY, bg=theme.BG_MAIN).pack(side="left", padx=5)
        tk.Entry(btn_box, textvariable=self.rec_amt_var, font=theme.FONT_SMALL, bg=theme.BG_CARD, fg=theme.TEXT_PRIMARY, insertbackground="white", width=10).pack(side="left", padx=5)
        
        tk.Button(btn_box, text="💰 Record Client Payment", font=theme.FONT_SMALL, bg=theme.INCOME, fg=theme.TEXT_DARK, bd=0, padx=12, pady=6, command=self.record_cust_payment_action).pack(side="left", padx=10)
        tk.Button(btn_box, text="🗑 Delete Client", font=theme.FONT_SMALL, bg=theme.EXPENSE, fg=theme.TEXT_PRIMARY, bd=0, padx=12, pady=6, command=self.delete_customer_action).pack(side="right", padx=5)
        
        return page

    def add_customer_action(self):
        name = self.cust_name_var.get().strip()
        phone = self.cust_phone_var.get().strip()
        pend = float(clean_amount_str(self.cust_pend_var.get()) or 0)
        paid = float(clean_amount_str(self.cust_paid_var.get()) or 0)
        due = self.cust_due_var.get()
        
        if not name:
            messagebox.showerror("Error", "Customer Name is required.")
            return
            
        self.tracker.db.add_customer(name, phone, pend, paid, due)
        
        self.cust_name_var.set("")
        self.cust_phone_var.set("")
        self.cust_pend_var.set("0")
        self.cust_paid_var.set("0")
        
        self.refresh_biz_customers()

    def record_cust_payment_action(self):
        selected = self.cust_tree.focus()
        if not selected:
            messagebox.showwarning("Warning", "Select a customer from the ledger first.")
            return
            
        vals = self.cust_tree.item(selected, "values")
        id_ = int(vals[0])
        pend = float(vals[3].replace("₹", "").replace(",", ""))
        paid = float(vals[4].replace("₹", "").replace(",", ""))
        
        rec_str = clean_amount_str(self.rec_amt_var.get())
        try:
            rec_val = float(rec_str)
        except ValueError:
            messagebox.showerror("Error", "Enter a valid payment amount.")
            return
            
        if rec_val > pend:
            messagebox.showerror("Error", "Received amount cannot exceed pending invoice balance!")
            return
            
        new_pend = pend - rec_val
        new_paid = paid + rec_val
        
        self.tracker.db.update_customer_payment(id_, new_pend, new_paid)
        self.refresh_biz_customers()

    def delete_customer_action(self):
        selected = self.cust_tree.focus()
        if not selected:
            messagebox.showwarning("Warning", "Select a customer from the ledger first.")
            return
        vals = self.cust_tree.item(selected, "values")
        id_ = int(vals[0])
        
        ans = messagebox.askyesno("🗑 Delete Client", f"Remove '{vals[1]}' from database?", icon="warning")
        if ans:
            self.tracker.db.delete_customer(id_)
            self.refresh_biz_customers()

    def create_biz_vendors_page(self):
        page = ScrollableFrame(self.content_container)
        frame = page.scrollable_frame
        
        # Header
        top_bar = tk.Frame(frame, bg=theme.BG_MAIN)
        top_bar.pack(fill="x", padx=20, pady=15)
        tk.Label(top_bar, text="Vendor & Supplier Ledger", font=theme.FONT_TITLE, fg=theme.TEXT_PRIMARY, bg=theme.BG_MAIN).pack(side="left")
        
        # Add vendor Form
        entry_box = tk.Frame(frame, bg=theme.BG_CARD, highlightbackground=theme.BORDER, highlightthickness=1)
        entry_box.pack(fill="x", padx=20, pady=5)
        
        grid_f = tk.Frame(entry_box, bg=theme.BG_CARD)
        grid_f.pack(padx=15, pady=15, fill="x")
        
        self.vend_name_var = tk.StringVar()
        self.vend_amt_var = tk.StringVar()
        self.vend_due_var = tk.StringVar()
        self.vend_status_var = tk.StringVar(value="Unpaid")
        
        # Vendor Name
        tk.Label(grid_f, text="Supplier Name", font=theme.FONT_SMALL, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).grid(row=0, column=0, padx=5, sticky="w")
        tk.Entry(grid_f, textvariable=self.vend_name_var, font=theme.FONT_BODY, bg=theme.BG_MAIN, fg=theme.TEXT_PRIMARY, insertbackground="white", width=22).grid(row=1, column=0, padx=5, pady=2)
        
        # Amount Payable
        tk.Label(grid_f, text="Amount Payable (₹)", font=theme.FONT_SMALL, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).grid(row=0, column=1, padx=5, sticky="w")
        tk.Entry(grid_f, textvariable=self.vend_amt_var, font=theme.FONT_BODY, bg=theme.BG_MAIN, fg=theme.TEXT_PRIMARY, insertbackground="white", width=12).grid(row=1, column=1, padx=5, pady=2)
        
        # Due Date
        tk.Label(grid_f, text="Due Date", font=theme.FONT_SMALL, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).grid(row=0, column=2, padx=5, sticky="w")
        tk.Entry(grid_f, textvariable=self.vend_due_var, font=theme.FONT_BODY, bg=theme.BG_MAIN, fg=theme.TEXT_PRIMARY, insertbackground="white", width=12).grid(row=1, column=2, padx=5, pady=2)
        self.vend_due_var.set(date.today().strftime("%Y-%m-%d"))
        
        # Status
        tk.Label(grid_f, text="Payment Status", font=theme.FONT_SMALL, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).grid(row=0, column=3, padx=5, sticky="w")
        status_cb = ttk.Combobox(grid_f, textvariable=self.vend_status_var, values=["Unpaid", "Paid"], width=10, state="readonly")
        status_cb.grid(row=1, column=3, padx=5, pady=2)
        
        tk.Button(grid_f, text="Add Supplier", font=theme.FONT_BODY_BOLD, bg=theme.INCOME, fg=theme.TEXT_DARK, bd=0, padx=15, pady=5, command=self.add_vendor_action).grid(row=1, column=4, padx=15)
        
        # Vendor Table
        t_box = tk.Frame(frame, bg=theme.BG_CARD, highlightbackground=theme.BORDER, highlightthickness=1)
        t_box.pack(fill="both", expand=True, padx=20, pady=15)
        
        scroll_y = ttk.Scrollbar(t_box, orient="vertical")
        columns = ("id", "name", "payable", "due_date", "status")
        self.vend_tree = ttk.Treeview(t_box, columns=columns, show="headings", yscrollcommand=scroll_y.set, style="Custom.Treeview", height=12)
        scroll_y.config(command=self.vend_tree.yview)
        scroll_y.pack(side="right", fill="y")
        
        self.vend_tree.heading("id", text="ID")
        self.vend_tree.heading("name", text="Supplier / Vendor")
        self.vend_tree.heading("payable", text="Amount Payable")
        self.vend_tree.heading("due_date", text="Payment Due Date")
        self.vend_tree.heading("status", text="Status")
        
        self.vend_tree.column("id", width=40, anchor="center")
        self.vend_tree.column("name", width=220, anchor="w")
        self.vend_tree.column("payable", width=120, anchor="e")
        self.vend_tree.column("due_date", width=110, anchor="center")
        self.vend_tree.column("status", width=100, anchor="center")
        
        self.vend_tree.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Vendor control buttons
        btn_box = tk.Frame(frame, bg=theme.BG_MAIN)
        btn_box.pack(fill="x", padx=20, pady=(0, 15))
        
        tk.Button(btn_box, text="✅ Mark Paid", font=theme.FONT_SMALL, bg=theme.INCOME, fg=theme.TEXT_DARK, bd=0, padx=12, pady=6, command=self.quick_pay_vendor_action).pack(side="left", padx=5)
        tk.Button(btn_box, text="🗑 Delete Vendor", font=theme.FONT_SMALL, bg=theme.EXPENSE, fg=theme.TEXT_PRIMARY, bd=0, padx=12, pady=6, command=self.delete_vendor_action).pack(side="right", padx=5)
        
        return page

    def add_vendor_action(self):
        name = self.vend_name_var.get().strip()
        amt = float(clean_amount_str(self.vend_amt_var.get()) or 0)
        due = self.vend_due_var.get()
        status = self.vend_status_var.get()
        
        if not name:
            messagebox.showerror("Error", "Supplier Name is required.")
            return
            
        self.tracker.db.add_vendor(name, amt, due, status)
        self.vend_name_var.set("")
        self.vend_amt_var.set("")
        self.refresh_biz_vendors()

    def quick_pay_vendor_action(self):
        selected = self.vend_tree.focus()
        if not selected:
            messagebox.showwarning("Warning", "Select a vendor from the ledger first.")
            return
        vals = self.vend_tree.item(selected, "values")
        id_ = int(vals[0])
        
        self.tracker.db.update_vendor_status(id_, "Paid")
        self.refresh_biz_vendors()

    def delete_vendor_action(self):
        selected = self.vend_tree.focus()
        if not selected:
            messagebox.showwarning("Warning", "Select a vendor from the ledger first.")
            return
        vals = self.vend_tree.item(selected, "values")
        id_ = int(vals[0])
        
        ans = messagebox.askyesno("🗑 Delete Vendor", f"Remove vendor '{vals[1]}'?", icon="warning")
        if ans:
            self.tracker.db.delete_vendor(id_)
            self.refresh_biz_vendors()

    def create_biz_monthly_page(self):
        page = ScrollableFrame(self.content_container)
        frame = page.scrollable_frame
        
        # Header
        top_bar = tk.Frame(frame, bg=theme.BG_MAIN)
        top_bar.pack(fill="x", padx=20, pady=15)
        tk.Label(top_bar, text="Monthly Revenue & Performance Statements", font=theme.FONT_TITLE, fg=theme.TEXT_PRIMARY, bg=theme.BG_MAIN).pack(side="left")
        
        # Reports Table Frame
        t_box = tk.Frame(frame, bg=theme.BG_CARD, highlightbackground=theme.BORDER, highlightthickness=1)
        t_box.pack(fill="both", expand=True, padx=20, pady=15)
        
        scroll_y = ttk.Scrollbar(t_box, orient="vertical")
        columns = ("month", "revenue", "expenses", "profit")
        self.monthly_tree = ttk.Treeview(t_box, columns=columns, show="headings", yscrollcommand=scroll_y.set, style="Custom.Treeview", height=12)
        scroll_y.config(command=self.monthly_tree.yview)
        scroll_y.pack(side="right", fill="y")
        
        self.monthly_tree.heading("month", text="Reporting Month")
        self.monthly_tree.heading("revenue", text="Gross Revenue")
        self.monthly_tree.heading("expenses", text="Operational Expenses")
        self.monthly_tree.heading("profit", text="Net Profit / Loss")
        
        self.monthly_tree.column("month", width=180, anchor="center")
        self.monthly_tree.column("revenue", width=140, anchor="e")
        self.monthly_tree.column("expenses", width=140, anchor="e")
        self.monthly_tree.column("profit", width=140, anchor="e")
        
        self.monthly_tree.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Monthly performance charts box
        self.monthly_chart_box = tk.Frame(frame, bg=theme.BG_CARD, highlightbackground=theme.BORDER, highlightthickness=1)
        self.monthly_chart_box.pack(fill="both", expand=True, padx=20, pady=(5, 20))
        
        return page

    def create_biz_gst_page(self):
        page = ScrollableFrame(self.content_container)
        frame = page.scrollable_frame
        
        # Header
        top_bar = tk.Frame(frame, bg=theme.BG_MAIN)
        top_bar.pack(fill="x", padx=20, pady=15)
        tk.Label(top_bar, text="GST Tax Calculator", font=theme.FONT_TITLE, fg=theme.TEXT_PRIMARY, bg=theme.BG_MAIN).pack(side="left")
        
        # Calculator Frame
        calc_box = tk.Frame(frame, bg=theme.BG_CARD, highlightbackground=theme.BORDER, highlightthickness=1, width=450, height=380)
        calc_box.pack(pady=30)
        calc_box.pack_propagate(False)
        
        tk.Label(calc_box, text="GST TAX ASSESSOR", font=theme.FONT_BODY_BOLD, fg=theme.ACCENT, bg=theme.BG_CARD).pack(pady=(20, 15))
        
        self.gst_amt_var = tk.StringVar(value="5000")
        self.gst_pct_var = tk.StringVar(value="18%")
        self.custom_gst_var = tk.StringVar(value="15")
        
        # Original Amount Input
        f1 = tk.Frame(calc_box, bg=theme.BG_CARD)
        f1.pack(pady=5)
        tk.Label(f1, text="Original Amount (₹):", font=theme.FONT_BODY, fg=theme.TEXT_PRIMARY, bg=theme.BG_CARD, width=18, anchor="e").pack(side="left")
        tk.Entry(f1, textvariable=self.gst_amt_var, font=theme.FONT_BODY, bg=theme.BG_MAIN, fg=theme.TEXT_PRIMARY, insertbackground="white", width=14).pack(side="left", padx=10)
        
        # GST Rate Input
        f2 = tk.Frame(calc_box, bg=theme.BG_CARD)
        f2.pack(pady=5)
        tk.Label(f2, text="GST Rate:", font=theme.FONT_BODY, fg=theme.TEXT_PRIMARY, bg=theme.BG_CARD, width=18, anchor="e").pack(side="left")
        self.gst_cb = ttk.Combobox(f2, textvariable=self.gst_pct_var, values=["0%", "5%", "12%", "18%", "28%", "Custom"], width=12, state="readonly")
        self.gst_cb.pack(side="left", padx=10)
        self.gst_cb.bind("<<ComboboxSelected>>", self.on_gst_rate_change)
        
        # Custom Rate Input (Hidden initially)
        self.custom_gst_frame = tk.Frame(calc_box, bg=theme.BG_CARD)
        
        # Calculate Button
        tk.Button(calc_box, text="Calculate GST", font=theme.FONT_BODY_BOLD, bg=theme.ACCENT, fg=theme.TEXT_DARK, bd=0, padx=20, pady=8, command=self.calculate_gst_action).pack(pady=15)
        
        # Result output
        self.gst_out_lbl = tk.Label(calc_box, text="GST Component = ₹0.00\nFinal Amount = ₹0.00", font=theme.FONT_BODY_BOLD, fg=theme.TEXT_PRIMARY, bg=theme.BG_CARD, justify="center")
        self.gst_out_lbl.pack(pady=10)
        
        return page

    def on_gst_rate_change(self, event=None):
        if self.gst_pct_var.get() == "Custom":
            self.custom_gst_frame.pack(pady=5, before=self.gst_out_lbl)
            if not self.custom_gst_frame.winfo_children():
                tk.Label(self.custom_gst_frame, text="Custom Rate (%):", font=theme.FONT_BODY, fg=theme.TEXT_PRIMARY, bg=theme.BG_CARD, width=18, anchor="e").pack(side="left")
                tk.Entry(self.custom_gst_frame, textvariable=self.custom_gst_var, font=theme.FONT_BODY, bg=theme.BG_MAIN, fg=theme.TEXT_PRIMARY, insertbackground="white", width=14).pack(side="left", padx=10)
        else:
            self.custom_gst_frame.pack_forget()

    def calculate_gst_action(self):
        amt_str = clean_amount_str(self.gst_amt_var.get())
        rate_sel = self.gst_pct_var.get()
        
        if rate_sel == "Custom":
            pct_str = self.custom_gst_var.get().strip()
        else:
            pct_str = rate_sel.replace("%", "").strip()
            
        try:
            amt = float(amt_str)
            pct = float(pct_str)
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid numeric amount and rate percentage.")
            return
            
        gst_val = amt * (pct / 100.0)
        final_val = amt + gst_val
        
        self.gst_out_lbl.configure(
            text=f"GST ({pct:.0f}%) = ₹{gst_val:,.2f}\nFinal Total = ₹{final_val:,.2f}"
        )

    def create_biz_cashflow_page(self):
        page = ScrollableFrame(self.content_container)
        frame = page.scrollable_frame
        
        # Header
        top_bar = tk.Frame(frame, bg=theme.BG_MAIN)
        top_bar.pack(fill="x", padx=20, pady=15)
        tk.Label(top_bar, text="Cash Flow Statements", font=theme.FONT_TITLE, fg=theme.TEXT_PRIMARY, bg=theme.BG_MAIN).pack(side="left")
        
        # Statement Card
        self.cf_card = tk.Frame(frame, bg=theme.BG_CARD, highlightbackground=theme.BORDER, highlightthickness=1)
        self.cf_card.pack(fill="both", expand=True, padx=20, pady=15)
        
        return page

    def create_biz_payroll_page(self):
        page = ScrollableFrame(self.content_container)
        frame = page.scrollable_frame
        
        # Header
        top_bar = tk.Frame(frame, bg=theme.BG_MAIN)
        top_bar.pack(fill="x", padx=20, pady=15)
        tk.Label(top_bar, text="Employee Salary & Payroll Tracker", font=theme.FONT_TITLE, fg=theme.TEXT_PRIMARY, bg=theme.BG_MAIN).pack(side="left")
        
        # Entry form
        entry_box = tk.Frame(frame, bg=theme.BG_CARD, highlightbackground=theme.BORDER, highlightthickness=1)
        entry_box.pack(fill="x", padx=20, pady=5)
        
        grid_f = tk.Frame(entry_box, bg=theme.BG_CARD)
        grid_f.pack(padx=15, pady=15, fill="x")
        
        self.emp_name_var = tk.StringVar()
        self.emp_sal_var = tk.StringVar()
        self.emp_paid_var = tk.StringVar(value="0")
        
        tk.Label(grid_f, text="Employee Name", font=theme.FONT_SMALL, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).grid(row=0, column=0, padx=5, sticky="w")
        tk.Entry(grid_f, textvariable=self.emp_name_var, font=theme.FONT_BODY, bg=theme.BG_MAIN, fg=theme.TEXT_PRIMARY, insertbackground="white", width=25).grid(row=1, column=0, padx=5, pady=2)
        
        tk.Label(grid_f, text="Contracted Monthly Salary", font=theme.FONT_SMALL, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).grid(row=0, column=1, padx=5, sticky="w")
        tk.Entry(grid_f, textvariable=self.emp_sal_var, font=theme.FONT_BODY, bg=theme.BG_MAIN, fg=theme.TEXT_PRIMARY, insertbackground="white", width=15).grid(row=1, column=1, padx=5, pady=2)
        
        tk.Label(grid_f, text="Paid Amount (₹)", font=theme.FONT_SMALL, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).grid(row=0, column=2, padx=5, sticky="w")
        tk.Entry(grid_f, textvariable=self.emp_paid_var, font=theme.FONT_BODY, bg=theme.BG_MAIN, fg=theme.TEXT_PRIMARY, insertbackground="white", width=12).grid(row=1, column=2, padx=5, pady=2)
        
        tk.Button(grid_f, text="Add Employee Record", font=theme.FONT_BODY_BOLD, bg=theme.INCOME, fg=theme.TEXT_DARK, bd=0, padx=15, pady=5, command=self.add_employee_action).grid(row=1, column=3, padx=15)
        
        # Payroll Table
        t_box = tk.Frame(frame, bg=theme.BG_CARD, highlightbackground=theme.BORDER, highlightthickness=1)
        t_box.pack(fill="both", expand=True, padx=20, pady=15)
        
        scroll_y = ttk.Scrollbar(t_box, orient="vertical")
        columns = ("id", "name", "salary", "paid", "pending")
        self.emp_tree = ttk.Treeview(t_box, columns=columns, show="headings", yscrollcommand=scroll_y.set, style="Custom.Treeview", height=12)
        scroll_y.config(command=self.emp_tree.yview)
        scroll_y.pack(side="right", fill="y")
        
        self.emp_tree.heading("id", text="ID")
        self.emp_tree.heading("name", text="Employee Name")
        self.emp_tree.heading("salary", text="Monthly Salary")
        self.emp_tree.heading("paid", text="Paid Amount")
        self.emp_tree.heading("pending", text="Pending Balance")
        
        self.emp_tree.column("id", width=40, anchor="center")
        self.emp_tree.column("name", width=220, anchor="w")
        self.emp_tree.column("salary", width=120, anchor="e")
        self.emp_tree.column("paid", width=120, anchor="e")
        self.emp_tree.column("pending", width=120, anchor="e")
        
        self.emp_tree.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Payroll controls
        btn_box = tk.Frame(frame, bg=theme.BG_MAIN)
        btn_box.pack(fill="x", padx=20, pady=(0, 15))
        
        self.pay_amt_var = tk.StringVar(value="5000")
        tk.Label(btn_box, text="Disburse Salary Amount (₹):", font=theme.FONT_SMALL, fg=theme.TEXT_PRIMARY, bg=theme.BG_MAIN).pack(side="left", padx=5)
        tk.Entry(btn_box, textvariable=self.pay_amt_var, font=theme.FONT_SMALL, bg=theme.BG_CARD, fg=theme.TEXT_PRIMARY, insertbackground="white", width=10).pack(side="left", padx=5)
        
        tk.Button(btn_box, text="💸 Record Salary Disbursement", font=theme.FONT_SMALL, bg=theme.INCOME, fg=theme.TEXT_DARK, bd=0, padx=12, pady=6, command=self.record_employee_payment_action).pack(side="left", padx=10)
        tk.Button(btn_box, text="🗑 Remove Employee", font=theme.FONT_SMALL, bg=theme.EXPENSE, fg=theme.TEXT_PRIMARY, bd=0, padx=12, pady=6, command=self.delete_employee_action).pack(side="right", padx=5)
        
        return page

    def add_employee_action(self):
        name = self.emp_name_var.get().strip()
        sal = float(clean_amount_str(self.emp_sal_var.get()) or 0)
        paid = float(clean_amount_str(self.emp_paid_var.get()) or 0)
        
        if not name:
            messagebox.showerror("Error", "Employee Name is required.")
            return
            
        pend = max(0.0, sal - paid)
        self.tracker.db.add_employee_salary(name, sal, paid, pend)
        
        self.emp_name_var.set("")
        self.emp_sal_var.set("")
        self.emp_paid_var.set("0")
        
        self.refresh_biz_payroll()

    def record_employee_payment_action(self):
        selected = self.emp_tree.focus()
        if not selected:
            messagebox.showwarning("Warning", "Select an employee from the table first.")
            return
        vals = self.emp_tree.item(selected, "values")
        id_ = int(vals[0])
        sal = float(vals[2].replace("₹", "").replace(",", ""))
        paid = float(vals[3].replace("₹", "").replace(",", ""))
        pend = float(vals[4].replace("₹", "").replace(",", ""))
        
        disb_str = clean_amount_str(self.pay_amt_var.get())
        try:
            disb_val = float(disb_str)
        except ValueError:
            messagebox.showerror("Error", "Enter a valid disbursement amount.")
            return
            
        if disb_val > pend:
            messagebox.showerror("Error", "Disbursed amount cannot exceed pending salary balance!")
            return
            
        new_paid = paid + disb_val
        new_pend = pend - disb_val
        
        self.tracker.db.update_employee_payment(id_, new_paid, new_pend)
        
        # Record it automatically under expenses (Employee Salary)
        self.tracker.db.add_business_expense(date.today().strftime("%Y-%m-%d"), "Employee Salary", disb_val, f"Salary payout (ID: {id_})")
        
        self.refresh_biz_payroll()

    def delete_employee_action(self):
        selected = self.emp_tree.focus()
        if not selected:
            messagebox.showwarning("Warning", "Select an employee from the table first.")
            return
        vals = self.emp_tree.item(selected, "values")
        id_ = int(vals[0])
        
        ans = messagebox.askyesno("🗑 Remove Employee", f"Delete record of '{vals[1]}'?", icon="warning")
        if ans:
            self.tracker.db.delete_employee_salary(id_)
            self.refresh_biz_payroll()

    def create_biz_invoice_page(self):
        page = ScrollableFrame(self.content_container)
        frame = page.scrollable_frame
        
        # Header
        top_bar = tk.Frame(frame, bg=theme.BG_MAIN)
        top_bar.pack(fill="x", padx=20, pady=15)
        tk.Label(top_bar, text="Automated Tax Invoice Generator", font=theme.FONT_TITLE, fg=theme.TEXT_PRIMARY, bg=theme.BG_MAIN).pack(side="left")
        
        # Generator Card Form
        form_box = tk.Frame(frame, bg=theme.BG_CARD, highlightbackground=theme.BORDER, highlightthickness=1, width=500, height=450)
        form_box.pack(pady=20)
        form_box.pack_propagate(False)
        
        tk.Label(form_box, text="TAX INVOICE SPECIFICATIONS", font=theme.FONT_BODY_BOLD, fg=theme.ACCENT, bg=theme.BG_CARD).pack(pady=(20, 15))
        
        self.inv_cust_var = tk.StringVar(value="Rahul")
        self.inv_prod_var = tk.StringVar(value="Laptop")
        self.inv_price_var = tk.StringVar(value="45000")
        self.inv_gst_var = tk.StringVar(value="18%")
        self.inv_pay_var = tk.StringVar(value="UPI")
        
        # Customer Name
        f1 = tk.Frame(form_box, bg=theme.BG_CARD)
        f1.pack(pady=4)
        tk.Label(f1, text="Customer Name:", font=theme.FONT_BODY, fg=theme.TEXT_PRIMARY, bg=theme.BG_CARD, width=18, anchor="e").pack(side="left")
        tk.Entry(f1, textvariable=self.inv_cust_var, font=theme.FONT_BODY, bg=theme.BG_MAIN, fg=theme.TEXT_PRIMARY, insertbackground="white", width=18).pack(side="left", padx=10)
        
        # Product Description
        f2 = tk.Frame(form_box, bg=theme.BG_CARD)
        f2.pack(pady=4)
        tk.Label(f2, text="Product Name / Desc:", font=theme.FONT_BODY, fg=theme.TEXT_PRIMARY, bg=theme.BG_CARD, width=18, anchor="e").pack(side="left")
        tk.Entry(f2, textvariable=self.inv_prod_var, font=theme.FONT_BODY, bg=theme.BG_MAIN, fg=theme.TEXT_PRIMARY, insertbackground="white", width=18).pack(side="left", padx=10)
        
        # Unit Price
        f3 = tk.Frame(form_box, bg=theme.BG_CARD)
        f3.pack(pady=4)
        tk.Label(f3, text="Unit Price (Excl GST):", font=theme.FONT_BODY, fg=theme.TEXT_PRIMARY, bg=theme.BG_CARD, width=18, anchor="e").pack(side="left")
        tk.Entry(f3, textvariable=self.inv_price_var, font=theme.FONT_BODY, bg=theme.BG_MAIN, fg=theme.TEXT_PRIMARY, insertbackground="white", width=18).pack(side="left", padx=10)
        
        # GST Rate
        f4 = tk.Frame(form_box, bg=theme.BG_CARD)
        f4.pack(pady=4)
        tk.Label(f4, text="GST Rate Category:", font=theme.FONT_BODY, fg=theme.TEXT_PRIMARY, bg=theme.BG_CARD, width=18, anchor="e").pack(side="left")
        gst_cb = ttk.Combobox(f4, textvariable=self.inv_gst_var, values=["0%", "5%", "12%", "18%", "28%"], width=16, state="readonly")
        gst_cb.pack(side="left", padx=10)
        
        # Payment Mode
        f5 = tk.Frame(form_box, bg=theme.BG_CARD)
        f5.pack(pady=4)
        tk.Label(f5, text="Payment Method:", font=theme.FONT_BODY, fg=theme.TEXT_PRIMARY, bg=theme.BG_CARD, width=18, anchor="e").pack(side="left")
        pay_cb = ttk.Combobox(f5, textvariable=self.inv_pay_var, values=["UPI", "Cash", "Card", "Net Banking"], width=16, state="readonly")
        pay_cb.pack(side="left", padx=10)
        
        # Generate Button
        tk.Button(form_box, text="⚙️ Generate tax Invoice PDF", font=theme.FONT_BODY_BOLD, bg=theme.ACCENT, fg=theme.TEXT_DARK, bd=0, padx=25, pady=10, command=self.generate_invoice_pdf_action).pack(pady=20)
        
        return page

    def generate_invoice_pdf_action(self):
        cust = self.inv_cust_var.get().strip()
        prod = self.inv_prod_var.get().strip()
        price_str = clean_amount_str(self.inv_price_var.get())
        gst_rate = self.inv_gst_var.get()
        pay = self.inv_pay_var.get()
        
        if not cust or not prod or not price_str:
            messagebox.showerror("Error", "Please fill in all specifications.")
            return
            
        try:
            price = float(price_str)
        except ValueError:
            messagebox.showerror("Error", "Unit Price must be numeric.")
            return
            
        file_path = "business_tax_invoice.pdf"
        
        try:
            PDFReportGenerator.generate_invoice(cust, prod, price, gst_rate, pay, file_path)
            
            # Record it automatically under daily sales as well!
            gst_pct = float(gst_rate.replace("%", "").strip())
            total_amt = price + (price * gst_pct / 100.0)
            self.tracker.db.add_business_sale(date.today().strftime("%Y-%m-%d"), cust, "INV-AUTO", total_amt, pay)
            
            # Launch PDF immediately
            if os.path.exists(file_path):
                os.startfile(file_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate invoice PDF: {str(e)}")

    def refresh_biz_dashboard(self):
        # 1. Fetch KPI Stats
        stats = self.get_biz_stats()
        self.biz_rev_lbl.configure(text=f"₹{stats['revenue']:,.2f}")
        self.biz_exp_lbl.configure(text=f"₹{stats['expenses']:,.2f}")
        
        profit = stats['profit']
        if profit >= 0:
            self.biz_profit_lbl.configure(text=f"₹{profit:,.2f}", fg=theme.INCOME)
        else:
            self.biz_profit_lbl.configure(text=f"-₹{abs(profit):,.2f}", fg=theme.EXPENSE)
            
        self.biz_top_prod_lbl.configure(text=stats['top_product'])
        self.biz_top_cust_lbl.configure(text=stats['top_customer'])
        self.biz_top_exp_lbl.configure(text=stats['top_expense'])
        
        # 2. Update Extended Health Score circular gauge
        db = self.tracker.db
        sales_df = pd.DataFrame(db.get_all_business_sales(), columns=["id", "date", "customer_name", "invoice_no", "amount", "payment_method"])
        expenses_df = pd.DataFrame(db.get_all_business_expenses(), columns=["id", "date", "category", "amount", "notes"])
        customers_df = pd.DataFrame(db.get_all_customers(), columns=["id", "customer_name", "phone", "pending_amount", "paid_amount", "due_date"])
        
        health = analytics.calculate_business_health_score_extended(sales_df, expenses_df, customers_df)
        self.biz_health_gauge.set_score(health["score"], health["status"], health["color"])
        
        # 3. Profit Prediction (Without ML)
        pred_profit, trend = analytics.predict_next_month_profit(sales_df, expenses_df)
        trend_symbols = {"up": "📈 Upward", "down": "📉 Downward", "stable": "➡️ Stable"}
        self.biz_pred_lbl.configure(text=f"₹{pred_profit:,.2f} ({trend_symbols.get(trend, 'Stable')})")
        
        # 4. Expense Analyzer AI Alert
        warnings = analytics.run_business_expense_analyzer(sales_df, expenses_df)
        for child in self.biz_analyzer_box.winfo_children():
            child.destroy()
        if warnings:
            tk.Label(self.biz_analyzer_box, text="💡 Expense Analyzer Alerts:", font=theme.FONT_BODY_BOLD, fg=theme.EXPENSE, bg="#450a0a", anchor="w").pack(fill="x", padx=10, pady=(5, 2))
            for w in warnings[:2]:
                tk.Label(self.biz_analyzer_box, text=f"• {w['suggestion']}", font=theme.FONT_SMALL, fg=theme.TEXT_PRIMARY, bg="#450a0a", wraplength=280, justify="left", anchor="w").pack(fill="x", padx=10, pady=2)
        else:
            tk.Label(self.biz_analyzer_box, text="✅ Expense Analyzer:\nCategory expenses are stable. No abnormal spikes detected.", font=theme.FONT_SMALL, fg=theme.INCOME, bg=theme.BG_CARD, justify="left", anchor="w").pack(fill="x", padx=10, pady=10)
            
        # 5. Smart Saving Suggestion AI Alert
        savings = analytics.run_business_saving_suggestions(expenses_df)
        for child in self.biz_savings_box.winfo_children():
            child.destroy()
        if savings:
            tk.Label(self.biz_savings_box, text="💰 Saving Suggestions:", font=theme.FONT_BODY_BOLD, fg=theme.WARNING, bg="#451e0a", anchor="w").pack(fill="x", padx=10, pady=(5, 2))
            for s in savings[:2]:
                tk.Label(self.biz_savings_box, text=f"• {s['suggestion']}", font=theme.FONT_SMALL, fg=theme.TEXT_PRIMARY, bg="#451e0a", wraplength=280, justify="left", anchor="w").pack(fill="x", padx=10, pady=2)
        else:
            tk.Label(self.biz_savings_box, text="✅ Smart Savings:\nUtility and office costs are optimized.", font=theme.FONT_SMALL, fg=theme.INCOME, bg=theme.BG_CARD, justify="left", anchor="w").pack(fill="x", padx=10, pady=10)
            
        # 6. Update AI Weakness Auditor card
        weakness = analytics.analyze_weak_sections(sales_df, expenses_df, customers_df)
        
        for child in self.weakness_card.winfo_children():
            child.destroy()
            
        tk.Label(
            self.weakness_card, 
            text="🔍 AI Business Weakness Auditor & Improvement Suggestions", 
            font=theme.FONT_BODY_BOLD, 
            fg=theme.ACCENT, 
            bg=theme.BG_CARD
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        w_sec = weakness["weak_section"]
        w_desc = weakness["description"]
        w_impact = weakness["impact"]
        
        w_color = theme.EXPENSE if w_sec != "None (Operational Efficiency is Good)" else theme.INCOME
        
        lbl_sec = tk.Label(
            self.weakness_card, 
            text=f"Weakest Section: {w_sec} (Impact: {w_impact})", 
            font=theme.FONT_BODY_BOLD, 
            fg=w_color, 
            bg=theme.BG_CARD
        )
        lbl_sec.pack(anchor="w", padx=15, pady=2)
        
        lbl_desc = tk.Label(
            self.weakness_card, 
            text=w_desc, 
            font=theme.FONT_SMALL, 
            fg=theme.TEXT_PRIMARY, 
            bg=theme.BG_CARD,
            wraplength=700,
            justify="left"
        )
        lbl_desc.pack(anchor="w", padx=15, pady=2)
        
        tk.Frame(self.weakness_card, bg=theme.BORDER, height=1).pack(fill="x", padx=15, pady=8)
        
        tk.Label(
            self.weakness_card, 
            text="💡 Actionable Steps to Improve:", 
            font=theme.FONT_BODY_BOLD, 
            fg=theme.TEXT_MUTED, 
            bg=theme.BG_CARD
        ).pack(anchor="w", padx=15, pady=2)
        
        for sugg in weakness["suggestions"]:
            tk.Label(
                self.weakness_card, 
                text=f"• {sugg}", 
                font=theme.FONT_SMALL, 
                fg=theme.TEXT_PRIMARY, 
                bg=theme.BG_CARD,
                wraplength=700,
                justify="left",
                anchor="w"
            ).pack(fill="x", padx=25, pady=2)
 
        # 7. Render Charts (2x2 analytics diagnostic grid)
        self.render_biz_charts(sales_df, expenses_df)

    def render_biz_charts(self, sales_df, expenses_df):
        for child in self.biz_charts_container.winfo_children():
            child.destroy()
            
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(10, 5.0), dpi=100)
        fig.patch.set_facecolor(theme.BG_CARD)
        
        months = []
        if not sales_df.empty:
            sales_df = sales_df.copy()
            sales_df["date"] = pd.to_datetime(sales_df["date"])
            sales_df["month"] = sales_df["date"].dt.strftime("%Y-%m")
            sales_m = sales_df.groupby("month")["amount"].sum()
            
            expenses_m = pd.Series(dtype=float)
            if not expenses_df.empty:
                expenses_df = expenses_df.copy()
                expenses_df["date"] = pd.to_datetime(expenses_df["date"])
                expenses_df["month"] = expenses_df["date"].dt.strftime("%Y-%m")
                expenses_m = expenses_df.groupby("month")["amount"].sum()
                
            months = sorted(list(set(sales_m.index).union(expenses_m.index)))[-6:]
            
            x = np.arange(len(months))
            width = 0.35
            
            sales_vals = [sales_m.get(m, 0.0) for m in months]
            exp_vals = [expenses_m.get(m, 0.0) for m in months]
            
            ax1.bar(x - width/2, sales_vals, width, label="Sales", color=theme.INCOME)
            ax1.bar(x + width/2, exp_vals, width, label="Expenses", color=theme.EXPENSE)
            
            ax1.set_title("Revenue vs OpEx (Last 6 Months)", color=theme.TEXT_PRIMARY, fontsize=9, fontweight="bold")
            ax1.set_xticks(x)
            ax1.set_xticklabels([datetime.strptime(m, "%Y-%m").strftime("%b %y") for m in months], color=theme.TEXT_MUTED, fontsize=7)
            ax1.set_facecolor(theme.BG_CARD)
            ax1.spines['bottom'].set_color(theme.BORDER)
            ax1.spines['left'].set_color(theme.BORDER)
            ax1.spines['top'].set_visible(False)
            ax1.spines['right'].set_visible(False)
            ax1.tick_params(colors=theme.TEXT_MUTED, labelsize=7)
            ax1.legend(facecolor=theme.BG_CARD, edgecolor="none", labelcolor=theme.TEXT_PRIMARY, fontsize=6)
        else:
            ax1.text(0.5, 0.5, "No sales recorded yet", color=theme.TEXT_MUTED, ha="center", va="center")
            ax1.axis("off")
            
        if not expenses_df.empty:
            cat_sums = expenses_df.groupby("category")["amount"].sum()
            categories = list(cat_sums.index)
            amounts = list(cat_sums.values)
            
            colors_list = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#6b7280']
            ax2.pie(
                amounts,
                labels=categories,
                autopct='%1.0f%%',
                startangle=140,
                colors=colors_list[:len(categories)],
                textprops={'fontsize': 6, 'color': theme.TEXT_PRIMARY}
            )
            ax2.set_title("Expense Distribution", color=theme.TEXT_PRIMARY, fontsize=9, fontweight="bold")
            ax2.set_facecolor(theme.BG_CARD)
        else:
            ax2.text(0.5, 0.5, "No expenses recorded yet", color=theme.TEXT_MUTED, ha="center", va="center")
            ax2.axis("off")
            
        if months:
            prof_vals = [sales_m.get(m, 0.0) - expenses_m.get(m, 0.0) for m in months]
            x = np.arange(len(months))
            ax3.plot(x, prof_vals, marker='o', color=theme.ACCENT, linewidth=2, label='Net Profit')
            ax3.axhline(0, color='white', linestyle='--', alpha=0.3)
            
            ax3.fill_between(x, prof_vals, 0, where=(np.array(prof_vals) >= 0), color=theme.INCOME, alpha=0.1)
            ax3.fill_between(x, prof_vals, 0, where=(np.array(prof_vals) < 0), color=theme.EXPENSE, alpha=0.1)
            
            ax3.set_title("Monthly Net Profit / Loss Trend", color=theme.TEXT_PRIMARY, fontsize=9, fontweight="bold")
            ax3.set_xticks(x)
            ax3.set_xticklabels([datetime.strptime(m, "%Y-%m").strftime("%b %y") for m in months], color=theme.TEXT_MUTED, fontsize=7)
            ax3.set_facecolor(theme.BG_CARD)
            ax3.spines['bottom'].set_color(theme.BORDER)
            ax3.spines['left'].set_color(theme.BORDER)
            ax3.spines['top'].set_visible(False)
            ax3.spines['right'].set_visible(False)
            ax3.tick_params(colors=theme.TEXT_MUTED, labelsize=7)
        else:
            ax3.text(0.5, 0.5, "No trend data available", color=theme.TEXT_MUTED, ha="center", va="center")
            ax3.axis("off")
            
        db = self.tracker.db
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT SUM(amount) FROM business_sales")
        total_cash_in = cursor.fetchone()[0] or 0.0
        
        cursor.execute("SELECT SUM(amount) FROM business_expenses")
        opex_sum = cursor.fetchone()[0] or 0.0
        cursor.execute("SELECT SUM(amount_payable) FROM vendors WHERE status='Paid'")
        paid_vend = cursor.fetchone()[0] or 0.0
        total_cash_out = opex_sum + paid_vend
        
        conn.close()
        
        if total_cash_in > 0 or total_cash_out > 0:
            categories_cf = ['Cash In', 'Cash Out']
            cf_vals = [total_cash_in, total_cash_out]
            ax4.bar(categories_cf, cf_vals, color=[theme.INCOME, theme.EXPENSE], width=0.4)
            ax4.set_title("Cumulative Cash Flow Position", color=theme.TEXT_PRIMARY, fontsize=9, fontweight="bold")
            ax4.set_facecolor(theme.BG_CARD)
            ax4.spines['bottom'].set_color(theme.BORDER)
            ax4.spines['left'].set_color(theme.BORDER)
            ax4.spines['top'].set_visible(False)
            ax4.spines['right'].set_visible(False)
            ax4.tick_params(colors=theme.TEXT_MUTED, labelsize=7)
            
            for i, val in enumerate(cf_vals):
                ax4.text(i, val + max(cf_vals)*0.02, f"₹{val:,.0f}", ha='center', va='bottom', color=theme.TEXT_PRIMARY, fontsize=7, fontweight='bold')
        else:
            ax4.text(0.5, 0.5, "No cash flow data", color=theme.TEXT_MUTED, ha="center", va="center")
            ax4.axis("off")
            
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=self.biz_charts_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def refresh_biz_sales(self):
        # 1. Clear existing rows
        for item in self.sales_tree.get_children():
            self.sales_tree.delete(item)
            
        # 2. Fetch from DB
        sales = self.tracker.db.get_all_business_sales()
        
        # 3. Populate
        today_total = 0.0
        today_str = date.today().strftime("%Y-%m-%d")
        for s in sales:
            self.sales_tree.insert("", "end", values=(s[0], s[1], s[2], s[3] if s[3] else "-", f"₹{s[4]:,.2f}", s[5]))
            if s[1] == today_str:
                today_total += s[4]
                
        # 4. Update summary label
        self.biz_today_sales_lbl.configure(text=f"Today's Sales = ₹{today_total:,.2f}")

    def refresh_biz_expenses(self):
        for item in self.exp_tree.get_children():
            self.exp_tree.delete(item)
            
        expenses = self.tracker.db.get_all_business_expenses()
        for e in expenses:
            self.exp_tree.insert("", "end", values=(e[0], e[1], e[2], f"₹{e[3]:,.2f}", e[4] if e[4] else "-"))

    def refresh_biz_pl(self):
        # Fetch stats
        stats = self.get_biz_stats()
        rev = stats["revenue"]
        exp = stats["expenses"]
        diff = stats["profit"]
        
        if diff >= 0:
            self.pl_value_lbl.configure(text=f"Profit = ₹{diff:,.2f}", fg=theme.INCOME)
            self.pl_title_lbl.configure(text="NET BUSINESS SURPLUS (PROFIT)")
        else:
            self.pl_value_lbl.configure(text=f"Loss = ₹{abs(diff):,.2f}", fg=theme.EXPENSE)
            self.pl_title_lbl.configure(text="NET BUSINESS DEFICIT (LOSS)")
            
        # Repopulate details table in PL page
        for child in self.pl_details_box.winfo_children():
            child.destroy()
            
        # Categories list
        tk.Label(self.pl_details_box, text="Financial Categories Breakup Statement", font=theme.FONT_BODY_BOLD, fg=theme.TEXT_PRIMARY, bg=theme.BG_CARD).pack(anchor="w", padx=15, pady=10)
        
        items_f = tk.Frame(self.pl_details_box, bg=theme.BG_CARD)
        items_f.pack(fill="x", padx=15, pady=5)
        
        # Gross revenue row
        r1 = tk.Frame(items_f, bg=theme.BG_CARD)
        r1.pack(fill="x", pady=4)
        tk.Label(r1, text="Gross Revenue (Daily Sales)", font=theme.FONT_BODY, fg=theme.TEXT_PRIMARY, bg=theme.BG_CARD).pack(side="left")
        tk.Label(r1, text=f"₹{rev:,.2f}", font=theme.FONT_BODY_BOLD, fg=theme.INCOME, bg=theme.BG_CARD).pack(side="right")
        
        # Line separator
        tk.Frame(items_f, bg=theme.BORDER, height=1).pack(fill="x", pady=8)
        
        # Category spending
        db = self.tracker.db
        cursor = db.get_connection().cursor()
        cursor.execute("SELECT category, SUM(amount) FROM business_expenses GROUP BY category ORDER BY SUM(amount) DESC")
        
        has_exp = False
        for category, amount in cursor.fetchall():
            has_exp = True
            r = tk.Frame(items_f, bg=theme.BG_CARD)
            r.pack(fill="x", pady=2)
            tk.Label(r, text=f"Less: {category}", font=theme.FONT_BODY, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).pack(side="left")
            tk.Label(r, text=f"-₹{amount:,.2f}", font=theme.FONT_BODY, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).pack(side="right")
            
        if not has_exp:
            r = tk.Frame(items_f, bg=theme.BG_CARD)
            r.pack(fill="x", pady=2)
            tk.Label(r, text="No expenses registered", font=theme.FONT_SMALL, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).pack(side="left")
            
        # Line separator
        tk.Frame(items_f, bg=theme.BORDER, height=1).pack(fill="x", pady=8)
        
        # Net row
        rn = tk.Frame(items_f, bg=theme.BG_CARD)
        rn.pack(fill="x", pady=4)
        tk.Label(rn, text="Net Surplus/Deficit", font=theme.FONT_BODY_BOLD, fg=theme.TEXT_PRIMARY, bg=theme.BG_CARD).pack(side="left")
        net_color = theme.INCOME if diff >= 0 else theme.EXPENSE
        tk.Label(rn, text=f"₹{diff:,.2f}", font=theme.FONT_BODY_BOLD, fg=net_color, bg=theme.BG_CARD).pack(side="right")
        
        # P&L Chart Box
        pl_chart_frame = tk.Frame(self.pl_details_box, bg=theme.BG_CARD)
        pl_chart_frame.pack(fill="both", expand=True, padx=15, pady=(15, 10))
        
        try:
            fig, ax = plt.subplots(figsize=(6, 2.0), dpi=100)
            fig.patch.set_facecolor(theme.BG_CARD)
            
            categories = ['Gross Revenue', 'Total OpEx', 'Net Profit/Loss']
            values = [rev, exp, diff]
            colors_list = [theme.INCOME, theme.EXPENSE, theme.ACCENT if diff >= 0 else theme.EXPENSE]
            
            bars = ax.bar(categories, values, color=colors_list, width=0.4)
            ax.set_title("P&L Statement Visualization (Revenue vs Expenses vs Profit)", color=theme.TEXT_PRIMARY, fontsize=9, fontweight="bold")
            
            ax.set_facecolor(theme.BG_CARD)
            ax.spines['bottom'].set_color(theme.BORDER)
            ax.spines['left'].set_color(theme.BORDER)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.tick_params(colors=theme.TEXT_MUTED, labelsize=8)
            
            # Add values on top of bars
            for bar in bars:
                height = bar.get_height()
                label_y = height + (max(values)*0.015 if height >= 0 else min(values)*0.015)
                ax.text(bar.get_x() + bar.get_width()/2, label_y, f"₹{height:,.2f}", 
                        va='bottom' if height >= 0 else 'top', ha='center',
                        color=theme.TEXT_PRIMARY, fontsize=7, fontweight='bold')
                        
            plt.tight_layout()
            
            canvas = FigureCanvasTkAgg(fig, master=pl_chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
        except Exception as e:
            print("Error rendering P&L charts:", e)

    def refresh_biz_inventory(self):
        # 1. Clear rows
        for item in self.inv_tree.get_children():
            self.inv_tree.delete(item)
            
        # 2. Fetch inventory
        items = self.tracker.db.get_all_inventory()
        
        alerts = []
        for i in items:
            rem = i[2] - i[3]
            self.inv_tree.insert("", "end", values=(i[0], i[1], i[2], i[3], rem))
            if rem < 5:
                alerts.append(f"⚠️ Restock Alert: {i[1]} has only {rem} units left in stock!")
                
        # 3. Update alert box
        for child in self.biz_alert_frame.winfo_children():
            child.destroy()
            
        if alerts:
            alert_box = tk.Frame(self.biz_alert_frame, bg="#451e0a", highlightbackground=theme.WARNING, highlightthickness=1)
            alert_box.pack(fill="x", pady=5)
            for a in alerts:
                tk.Label(alert_box, text=a, font=theme.FONT_SMALL, fg=theme.TEXT_PRIMARY, bg="#451e0a", anchor="w").pack(fill="x", padx=15, pady=4)

    def refresh_biz_customers(self):
        for item in self.cust_tree.get_children():
            self.cust_tree.delete(item)
            
        customers = self.tracker.db.get_all_customers()
        for c in customers:
            self.cust_tree.insert("", "end", values=(c[0], c[1], c[2] if c[2] else "-", f"₹{c[3]:,.2f}", f"₹{c[4]:,.2f}", c[5] if c[5] else "-"))

    def refresh_biz_vendors(self):
        for item in self.vend_tree.get_children():
            self.vend_tree.delete(item)
            
        vendors = self.tracker.db.get_all_vendors()
        for v in vendors:
            self.vend_tree.insert("", "end", values=(v[0], v[1], f"₹{v[2]:,.2f}", v[3], v[4]))

    def refresh_biz_monthly(self):
        for item in self.monthly_tree.get_children():
            self.monthly_tree.delete(item)
            
        # Group sales and expenses by month YYYY-MM
        db = self.tracker.db
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Monthly Revenue
        cursor.execute("SELECT strftime('%Y-%m', date) as month, SUM(amount) FROM business_sales GROUP BY month")
        rev_m = {r[0]: r[1] for r in cursor.fetchall()}
        
        # Monthly Expenses
        cursor.execute("SELECT strftime('%Y-%m', date) as month, SUM(amount) FROM business_expenses GROUP BY month")
        exp_m = {r[0]: r[1] for r in cursor.fetchall()}
        
        all_months = sorted(list(set(rev_m.keys()).union(exp_m.keys())), reverse=True)
        for m in all_months:
            r_val = rev_m.get(m, 0.0)
            e_val = exp_m.get(m, 0.0)
            profit = r_val - e_val
            
            # Format month name
            try:
                date_obj = datetime.strptime(m, "%Y-%m")
                month_name = date_obj.strftime("%B %Y")
            except Exception:
                month_name = m
                
            self.monthly_tree.insert("", "end", values=(month_name, f"₹{r_val:,.2f}", f"₹{e_val:,.2f}", f"₹{profit:,.2f}"))
            
        conn.close()
        
        # Render trend chart in self.monthly_chart_box
        for child in self.monthly_chart_box.winfo_children():
            child.destroy()
            
        if all_months:
            # Chronological order for chart
            chrono_months = sorted(all_months)
            
            labels = []
            rev_vals = []
            exp_vals = []
            prof_vals = []
            
            for m in chrono_months:
                try:
                    date_obj = datetime.strptime(m, "%Y-%m")
                    lbl = date_obj.strftime("%b %y")
                except Exception:
                    lbl = m
                labels.append(lbl)
                rev_vals.append(rev_m.get(m, 0.0))
                exp_vals.append(exp_m.get(m, 0.0))
                prof_vals.append(rev_m.get(m, 0.0) - exp_m.get(m, 0.0))
                
            try:
                fig, ax = plt.subplots(figsize=(6, 2.0), dpi=100)
                fig.patch.set_facecolor(theme.BG_CARD)
                
                ax.plot(labels, rev_vals, marker='o', label='Revenue', color=theme.INCOME, linewidth=2)
                ax.plot(labels, exp_vals, marker='s', label='Expenses', color=theme.EXPENSE, linewidth=2)
                ax.plot(labels, prof_vals, marker='^', label='Net Profit', color=theme.ACCENT, linewidth=2)
                
                ax.axhline(0, color='white', linestyle='--', alpha=0.2)
                ax.set_title("Monthly Financial Trends", color=theme.TEXT_PRIMARY, fontsize=9, fontweight="bold")
                
                ax.set_facecolor(theme.BG_CARD)
                ax.spines['bottom'].set_color(theme.BORDER)
                ax.spines['left'].set_color(theme.BORDER)
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.tick_params(colors=theme.TEXT_MUTED, labelsize=8)
                ax.legend(facecolor=theme.BG_CARD, edgecolor="none", labelcolor=theme.TEXT_PRIMARY, fontsize=7)
                
                plt.tight_layout()
                
                canvas = FigureCanvasTkAgg(fig, master=self.monthly_chart_box)
                canvas.draw()
                canvas.get_tk_widget().pack(fill="both", expand=True)
            except Exception as e:
                print("Error rendering Monthly Report chart:", e)

    def refresh_biz_cashflow(self):
        for child in self.cf_card.winfo_children():
            child.destroy()
            
        db = self.tracker.db
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Cash In: sales
        cursor.execute("SELECT SUM(amount) FROM business_sales")
        sales_sum = cursor.fetchone()[0] or 0.0
        
        cash_in = sales_sum
        
        # Cash Out: expenses + paid supplier payments
        cursor.execute("SELECT SUM(amount) FROM business_expenses")
        expenses_sum = cursor.fetchone()[0] or 0.0
        
        cursor.execute("SELECT SUM(amount_payable) FROM vendors WHERE status='Paid'")
        paid_vend_sum = cursor.fetchone()[0] or 0.0
        
        cash_out = expenses_sum + paid_vend_sum
        
        net_flow = cash_in - cash_out
        
        conn.close()
        
        # Layout inside cashflow panel
        tk.Label(self.cf_card, text="CASH FLOW STATEMENT", font=theme.FONT_BODY_BOLD, fg=theme.ACCENT, bg=theme.BG_CARD).pack(pady=(15, 10))
        
        grid_cf = tk.Frame(self.cf_card, bg=theme.BG_CARD)
        grid_cf.pack(padx=20, pady=10, fill="x")
        grid_cf.columnconfigure(0, weight=1)
        grid_cf.columnconfigure(1, weight=1)
        
        # Left Inflow
        lf = tk.Frame(grid_cf, bg=theme.BG_CARD)
        lf.grid(row=0, column=0, padx=10, sticky="nsew")
        tk.Label(lf, text="CASH INFLOWS", font=theme.FONT_BODY_BOLD, fg=theme.INCOME, bg=theme.BG_CARD).pack(anchor="w", pady=5)
        
        r_sales = tk.Frame(lf, bg=theme.BG_CARD)
        r_sales.pack(fill="x", pady=2)
        tk.Label(r_sales, text="• Revenue from Sales:", font=theme.FONT_BODY, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).pack(side="left")
        tk.Label(r_sales, text=f"₹{sales_sum:,.2f}", font=theme.FONT_BODY, fg=theme.TEXT_PRIMARY, bg=theme.BG_CARD).pack(side="right")
        
        tk.Frame(lf, bg=theme.BORDER, height=1).pack(fill="x", pady=5)
        
        r_in = tk.Frame(lf, bg=theme.BG_CARD)
        r_in.pack(fill="x", pady=2)
        tk.Label(r_in, text="Total Cash In:", font=theme.FONT_BODY_BOLD, fg=theme.TEXT_PRIMARY, bg=theme.BG_CARD).pack(side="left")
        tk.Label(r_in, text=f"₹{cash_in:,.2f}", font=theme.FONT_BODY_BOLD, fg=theme.INCOME, bg=theme.BG_CARD).pack(side="right")
        
        # Right Outflow
        rf = tk.Frame(grid_cf, bg=theme.BG_CARD)
        rf.grid(row=0, column=1, padx=10, sticky="nsew")
        tk.Label(rf, text="CASH OUTFLOWS", font=theme.FONT_BODY_BOLD, fg=theme.EXPENSE, bg=theme.BG_CARD).pack(anchor="w", pady=5)
        
        r_exp = tk.Frame(rf, bg=theme.BG_CARD)
        r_exp.pack(fill="x", pady=2)
        tk.Label(r_exp, text="• Operational Expenses:", font=theme.FONT_BODY, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).pack(side="left")
        tk.Label(r_exp, text=f"₹{expenses_sum:,.2f}", font=theme.FONT_BODY, fg=theme.TEXT_PRIMARY, bg=theme.BG_CARD).pack(side="right")
        
        r_vend = tk.Frame(rf, bg=theme.BG_CARD)
        r_vend.pack(fill="x", pady=2)
        tk.Label(r_vend, text="• Vendor Debts Cleared:", font=theme.FONT_BODY, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).pack(side="left")
        tk.Label(r_vend, text=f"₹{paid_vend_sum:,.2f}", font=theme.FONT_BODY, fg=theme.TEXT_PRIMARY, bg=theme.BG_CARD).pack(side="right")
        
        tk.Frame(rf, bg=theme.BORDER, height=1).pack(fill="x", pady=5)
        
        r_out = tk.Frame(rf, bg=theme.BG_CARD)
        r_out.pack(fill="x", pady=2)
        tk.Label(r_out, text="Total Cash Out:", font=theme.FONT_BODY_BOLD, fg=theme.TEXT_PRIMARY, bg=theme.BG_CARD).pack(side="left")
        tk.Label(r_out, text=f"₹{cash_out:,.2f}", font=theme.FONT_BODY_BOLD, fg=theme.EXPENSE, bg=theme.BG_CARD).pack(side="right")
        
        # Net Cash Card
        net_box = tk.Frame(self.cf_card, bg=theme.BG_MAIN, highlightbackground=theme.BORDER, highlightthickness=1)
        net_box.pack(fill="x", padx=30, pady=(15, 15))
        
        tk.Label(net_box, text="NET LIQUID CASH POSITION", font=theme.FONT_SMALL, fg=theme.TEXT_MUTED, bg=theme.BG_MAIN).pack(anchor="w", padx=15, pady=(10, 2))
        cf_color = theme.INCOME if net_flow >= 0 else theme.EXPENSE
        cf_sym = "+" if net_flow >= 0 else ""
        tk.Label(net_box, text=f"{cf_sym}₹{net_flow:,.2f}", font=("Segoe UI", 20, "bold"), fg=cf_color, bg=theme.BG_MAIN).pack(anchor="w", padx=15, pady=(2, 10))
        
        # Cash Flow Chart Box
        chart_box = tk.Frame(self.cf_card, bg=theme.BG_CARD)
        chart_box.pack(fill="both", expand=True, padx=30, pady=(5, 15))
        
        try:
            fig, ax = plt.subplots(figsize=(6, 2.0), dpi=100)
            fig.patch.set_facecolor(theme.BG_CARD)
            
            categories = ['Total Inflow', 'Total Outflow', 'Net Flow']
            values = [cash_in, cash_out, net_flow]
            colors_list = [theme.INCOME, theme.EXPENSE, theme.ACCENT if net_flow >= 0 else theme.EXPENSE]
            
            bars = ax.barh(categories, values, color=colors_list, height=0.45)
            ax.set_title("Cash Flow Analysis (Inflow vs Outflow vs Net Position)", color=theme.TEXT_PRIMARY, fontsize=9, fontweight="bold")
            
            ax.set_facecolor(theme.BG_CARD)
            ax.spines['bottom'].set_color(theme.BORDER)
            ax.spines['left'].set_color(theme.BORDER)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.tick_params(colors=theme.TEXT_MUTED, labelsize=8)
            
            # Add value labels
            for bar in bars:
                width = bar.get_width()
                label_x = width + (max(values)*0.02 if width >= 0 else min(values)*0.02)
                ax.text(label_x, bar.get_y() + bar.get_height()/2, f"₹{width:,.2f}", 
                        va='center', ha='left' if width >= 0 else 'right',
                        color=theme.TEXT_PRIMARY, fontsize=7, fontweight='bold')
            
            plt.tight_layout()
            
            canvas = FigureCanvasTkAgg(fig, master=chart_box)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
        except Exception as e:
            print("Error rendering Cash Flow chart:", e)

    def refresh_biz_payroll(self):
        for item in self.emp_tree.get_children():
            self.emp_tree.delete(item)
            
        salaries = self.tracker.db.get_all_employee_salaries()
        for s in salaries:
            self.emp_tree.insert("", "end", values=(s[0], s[1], f"₹{s[2]:,.2f}", f"₹{s[3]:,.2f}", f"₹{s[4]:,.2f}"))

    def get_biz_stats(self):
        db = self.tracker.db
        
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(amount) FROM business_sales")
        revenue = cursor.fetchone()[0] or 0.0
        
        cursor.execute("SELECT SUM(amount) FROM business_expenses")
        expenses = cursor.fetchone()[0] or 0.0
        
        cursor.execute("SELECT item_name, sold FROM inventory ORDER BY sold DESC LIMIT 1")
        top_prod_row = cursor.fetchone()
        top_product = f"{top_prod_row[0]} ({top_prod_row[1]} sold)" if top_prod_row else "None"
        
        cursor.execute("SELECT customer_name, paid_amount FROM customers ORDER BY paid_amount DESC LIMIT 1")
        top_cust_row = cursor.fetchone()
        top_customer = f"{top_cust_row[0]} (₹{top_cust_row[1]:,.0f})" if top_cust_row else "None"
        
        cursor.execute("SELECT category, SUM(amount) FROM business_expenses GROUP BY category ORDER BY SUM(amount) DESC LIMIT 1")
        top_exp_row = cursor.fetchone()
        top_expense = f"{top_exp_row[0]} (₹{top_exp_row[1]:,.0f})" if top_exp_row else "None"
        
        conn.close()
        
        return {
            "revenue": revenue,
            "expenses": expenses,
            "profit": revenue - expenses,
            "top_product": top_product,
            "top_customer": top_customer,
            "top_expense": top_expense
        }

    def seed_business_sample_data(self):
        db = self.tracker.db
        
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM business_sales")
            if cursor.fetchone()[0] == 0:
                sales = [
                    ("2026-06-01", "Rahul", "INV-1001", 12000.0, "UPI"),
                    ("2026-06-10", "Aman", "INV-1002", 15400.0, "Cash"),
                    ("2026-06-15", "Vikram", "INV-1003", 8500.0, "Card"),
                    ("2026-06-25", "Neha", "INV-1004", 22000.0, "UPI"),
                    ("2026-07-01", "Rohan", "INV-1005", 25400.0, "UPI")
                ]
                cursor.executemany("INSERT INTO business_sales (date, customer_name, invoice_no, amount, payment_method) VALUES (?, ?, ?, ?, ?)", sales)
                
                expenses = [
                    ("2026-06-02", "Office Rent", 15000.0, "Monthly Rent"),
                    ("2026-06-05", "Employee Salary", 20000.0, "Staff Salaries"),
                    ("2026-06-12", "Electricity Bill", 6500.0, "Power Bill"),
                    ("2026-06-18", "Marketing", 5000.0, "Google Ads Campaign"),
                    ("2026-06-22", "Internet", 1500.0, "Fiber ISP"),
                    ("2026-07-01", "Electricity Bill", 9000.0, "High summer usage"),
                    ("2026-07-01", "Marketing", 6750.0, "Increased social campaign")
                ]
                cursor.executemany("INSERT INTO business_expenses (date, category, amount, notes) VALUES (?, ?, ?, ?)", expenses)
                
                inventory = [
                    ("Laptop", 15, 4),
                    ("Printer", 8, 5),
                    ("Monitor", 12, 2),
                    ("Keyboard", 6, 2)
                ]
                cursor.executemany("INSERT INTO inventory (item_name, stock, sold) VALUES (?, ?, ?)", inventory)
                
                customers = [
                    ("Rahul", "9876543210", 5000.0, 12000.0, "2026-07-15"),
                    ("Aman", "9123456789", 0.0, 15400.0, ""),
                    ("Neha", "8877665544", 2500.0, 19500.0, "2026-07-20")
                ]
                cursor.executemany("INSERT INTO customers (customer_name, phone, pending_amount, paid_amount, due_date) VALUES (?, ?, ?, ?, ?)", customers)
                
                vendors = [
                    ("Supplier A (Tech Corp)", 18000.0, "2026-07-10", "Unpaid"),
                    ("Supplier B (Paper Mart)", 4500.0, "2026-06-28", "Paid")
                ]
                cursor.executemany("INSERT INTO vendors (supplier_name, amount_payable, due_date, status) VALUES (?, ?, ?, ?)", vendors)
                
                salaries = [
                    ("Rajesh Kumar", 12000.0, 12000.0, 0.0),
                    ("Kiran Sen", 8000.0, 4000.0, 4000.0)
                ]
                cursor.executemany("INSERT INTO employee_salaries (employee_name, salary, paid_amount, pending_amount) VALUES (?, ?, ?, ?)", salaries)
                
                conn.commit()
        except sqlite3.OperationalError:
            pass
        finally:
            conn.close()

if __name__ == "__main__":
    app = SmartBudgetTrackerApp()
    app.mainloop()
