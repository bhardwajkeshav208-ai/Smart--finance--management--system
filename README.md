# ⚡ FINSIGHT - Smart Financial Intelligence & Business ERP System

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/GUI-Tkinter%20%2F%20Custom%20Theme-cyan.svg)]()
[![Database](https://img.shields.io/badge/Database-SQLite3-lightgrey.svg)]()
[![Intelligence](https://img.shields.io/badge/Engine-Scikit--Learn%20%7C%20Pandas%20%7C%20NumPy-orange.svg)]()
[![Reports](https://img.shields.io/badge/Exports-PDF%20%7C%20Excel%20%7C%20CSV-green.svg)]()

**FINSIGHT** is a comprehensive, modern desktop application designed to bridge personal wealth management with enterprise-grade business operations. Featuring a modern dark-mode interface, an applied **Insight Engine**, and real-time **Smart Shopping Suggestions**, FINSIGHT empowers individuals and small business owners to monitor cash flow, plan savings, detect anomalous spending, and run daily ERP workflows seamlessly.

---

## 🌟 Key Features

### 👤 1. Personal Finance Portal

- **📊 Comprehensive Financial Dashboard**:
  - Live income, total expenses, and net balance summary cards.
  - Interactive Financial Health Gauge with real-time scoring.
  - Dynamic monthly budget limit tracker with visual utilization progress.
- **⚡ Insight Engine**:
  - **📈 Monthly Spending Forecast**: Projects end-of-month expenditure, daily burn velocity, and safe remaining daily allowances.
  - **⚠️ Unusual Spending Alerts**: Automatically flags statistical spending anomalies and unusual spikes with plain-language explanations.
  - **🧬 Your Financial Profile**: Evaluates user spending archetypes (*e.g., Disciplined Wealth Builder*, *Balanced Lifestyle Spender*), overall health score out of 100, and essential vs. discretionary breakdowns.
  - **🎯 Savings Goal Planner**: Tracks active goals, projected completion timelines, and actionable savings advice.
  - **💡 Smart Category Assistant**: Suggests appropriate expense categories from freeform transaction descriptions.
- **🛒 Smart Shopping Suggestions (4-Platform Independent Price Comparison)**:
  - Independently compares real-time prices across **Amazon India**, **Flipkart**, **Croma**, and **Reliance Digital**.
  - Completely bias-free evaluation supporting deals below budget as well as cheapest available options exceeding budget.
  - Prominent **`🛒 Visit Cheapest Deal`** button dynamically opens the verified lowest offer in your default browser.
  - Individual **`🔗 View Deal`** buttons on every verified platform row.
- **💸 Ledger & Transaction Management**:
  - Full CRUD operations with instant search and category filtering.
  - Live category-based breakdown charts and monthly trend analytics.
- **⏰ Subscription Manager**:
  - Tracks recurring digital subscriptions, renewal cycles, and monthly commitments.
- **📈 Reports & Document Generation**:
  - One-click printable **PDF Financial Health Statements** via ReportLab.
  - Full data backup, restore, and CSV/Excel ledger exports.

---

### 🏢 2. Business ERP Portal

- **💼 Executive Suite Dashboard**:
  - Gross Revenue, Operational Expenses (OpEx), Net Profit & Margin overview.
- **📈 Daily Sales Ledger**:
  - Multi-payment tracking (Cash, UPI, Card, Net Banking) with instant entry.
- **📊 Profit & Loss (P&L) Statements**:
  - Monthly financial health calculation, cost of goods sold (COGS), and operating margins.
- **📦 Inventory Tracker**:
  - Real-time stock counts, reorder alert thresholds, and valuation.
- **👥 Customer & Vendor Management**:
  - Customer directory with balance due tracking.
  - Vendor ledger for procurement and purchase history.
- **🧮 GST & Cash Flow Analyzers**:
  - Calculates SGST / CGST / IGST tax slabs (5%, 12%, 18%, 28%).
  - Inflow vs. outflow cash projection modeling.
- **👥 Employee Payroll**:
  - Salary tracking, department assignments, and payment statuses.
- **🧾 Automated PDF Invoice Generator**:
  - Generates professional client invoices with itemized billing and company details.

---

## 🛠 Tech Stack

| Domain | Technologies |
|---|---|
| **Core Language** | Python 3.10+ |
| **Graphical Interface** | Tkinter, ttk, Custom Vector Vector Canvas Widgets (`gui_theme.py`) |
| **Database** | SQLite3 (Persistent, ACID-compliant, localized) |
| **Financial Engine** | Scikit-learn, Pandas, NumPy |
| **Web Services** | Requests, BeautifulSoup4, Urllib, Webbrowser integration |
| **Document Generation** | ReportLab (Vector PDF Generation), CSV |
| **Architecture** | Model-View-Controller (MVC) + Object-Oriented Domain Layer |

---

## 📂 Project Architecture

```text
├── main.py                     # Application entry point & initial seed manager
├── gui_app.py                  # Primary Tkinter GUI layout, router & controller
├── gui_theme.py                # Modern dark-mode palette, typography & vector widgets
├── gui_ai_view.py              # Dedicated Insight Engine dashboard view
├── ml_engine.py                # Time-series regression, clustering & anomaly detection
├── price_comparison_service.py # 4-Platform web scraper & independent comparison logic
├── tracker_oop.py              # Domain OOP classes (Transaction, Goal, Subscription, etc.)
├── db_manager.py               # SQLite connection manager & schema migrations
├── analytics.py                # Pandas financial metrics & aggregation utilities
├── pdf_generator.py            # Automated ReportLab PDF statement & invoice generator
├── test_price_comparison.py    # Automated test suite for price comparison logic
├── run_app.bat                 # Convenient Windows launch script
└── settings.json               # Application runtime configuration
```

---

## 🚀 Quick Start & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/bhardwajkeshav208-ai/Smart--finance--management--system.git
cd Smart--finance--management--system
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```
*Or install required packages directly:*
```bash
pip install pandas numpy scikit-learn reportlab beautifulsoup4 requests
```

### 3. Launch FINSIGHT
```bash
python main.py
```
*On Windows, you can also double-click `run_app.bat`.*

---

## 🧪 Running Automated Tests

Run the test suite to verify the independent comparison engine:
```bash
python test_price_comparison.py
```

---

## 👨‍💻 Developed By

**Keshav Bhardwaj**  
- GitHub: [@bhardwajkeshav208-ai](https://github.com/bhardwajkeshav208-ai)
