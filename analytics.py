import pandas as pd
import numpy as np
from datetime import datetime, date
import calendar

def load_dataframe(transactions):
    """
    Converts list of Transaction objects to a Pandas DataFrame.
    """
    if not transactions:
        return pd.DataFrame(columns=["id", "type", "amount", "category", "date", "notes", "year", "month", "day"])
    
    data = [t.to_dict() for t in transactions]
    df = pd.DataFrame(data)
    
    # Ensure proper data types
    df["amount"] = pd.to_numeric(df["amount"])
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["day"] = df["date"].dt.day
    
    return df

def get_monthly_summary(df, year=None, month=None):
    """
    Returns total income, total expense, net savings, and savings rate.
    If year and month are none, defaults to current month.
    """
    if df.empty:
        return {"income": 0.0, "expense": 0.0, "savings": 0.0, "savings_rate": 0.0}
        
    if "profile" in df.columns:
        df = df[df["profile"] == "Personal"]

    if year is None or month is None:
        today = date.today()
        year, month = today.year, today.month
        
    # Filter for the specific month/year
    month_df = df[(df["year"] == year) & (df["month"] == month)]
    
    if month_df.empty:
        return {"income": 0.0, "expense": 0.0, "savings": 0.0, "savings_rate": 0.0}
        
    income = month_df[month_df["type"] == "Income"]["amount"].sum()
    expense = month_df[month_df["type"] == "Expense"]["amount"].sum()
    savings = income - expense
    
    savings_rate = (savings / income * 100) if income > 0 else (0.0 if savings >= 0 else (savings / max(expense, 1) * 100))
    # Clip savings rate to realistic percentage for visual presentation
    savings_rate = max(-100.0, min(100.0, savings_rate))
    
    return {
        "income": float(income),
        "expense": float(expense),
        "savings": float(savings),
        "savings_rate": round(float(savings_rate), 2)
    }

def get_category_wise_spending(df, year=None, month=None):
    """
    Returns a dictionary of category: total_expense.
    """
    if df.empty:
        return {}
        
    if "profile" in df.columns:
        df = df[df["profile"] == "Personal"]

    if year is None or month is None:
        today = date.today()
        year, month = today.year, today.month
        
    month_expense = df[(df["year"] == year) & (df["month"] == month) & (df["type"] == "Expense")]
    
    if month_expense.empty:
        return {}
        
    category_group = month_expense.groupby("category")["amount"].sum().sort_values(ascending=False)
    return category_group.to_dict()

def get_highest_expense_category(df, year=None, month=None):
    """
    Returns (category, amount) for the highest spending category of the month.
    """
    cat_spending = get_category_wise_spending(df, year, month)
    if not cat_spending:
        return ("None", 0.0)
    highest_cat = max(cat_spending, key=cat_spending.get)
    return (highest_cat, float(cat_spending[highest_cat]))

def get_average_daily_spending(df, year=None, month=None):
    """
    Calculates average daily spending in the selected month.
    """
    if df.empty:
        return 0.0
        
    if "profile" in df.columns:
        df = df[df["profile"] == "Personal"]

    today = date.today()
    if year is None or month is None:
        year, month = today.year, today.month
        
    month_expense = df[(df["year"] == year) & (df["month"] == month) & (df["type"] == "Expense")]
    if month_expense.empty:
        return 0.0
        
    total_expense = month_expense["amount"].sum()
    
    # Calculate days in the selected month
    if year == today.year and month == today.month:
        # If current month, use today's date to divide by elapsed days
        days = today.day
    else:
        # Use total days in that calendar month
        _, days = calendar.monthrange(int(year), int(month))
        
    return round(float(total_expense / max(days, 1)), 2)

def get_spending_insights(df):
    """
    Compares the current month's expenses with the previous month's.
    If no previous month, compares to the general historical average.
    """
    if df.empty:
        return ["No transaction history to analyze yet. Add transactions to see insights!"]
        
    if "profile" in df.columns:
        df = df[df["profile"] == "Personal"]

    insights = []
    today = date.today()
    curr_yr, curr_mo = today.year, today.month
    
    # Calculate last month's indices
    if curr_mo == 1:
        prev_yr, prev_mo = curr_yr - 1, 12
    else:
        prev_yr, prev_mo = curr_yr, curr_mo - 1
        
    # Get expenses only
    expenses_df = df[df["type"] == "Expense"]
    if expenses_df.empty:
        return ["No expenses recorded yet. Add expenses to get insights!"]
        
    curr_month_df = expenses_df[(expenses_df["year"] == curr_yr) & (expenses_df["month"] == curr_mo)]
    prev_month_df = expenses_df[(expenses_df["year"] == prev_yr) & (expenses_df["month"] == prev_mo)]
    
    # Group by category
    curr_by_cat = curr_month_df.groupby("category")["amount"].sum() if not curr_month_df.empty else pd.Series(dtype=float)
    prev_by_cat = prev_month_df.groupby("category")["amount"].sum() if not prev_month_df.empty else pd.Series(dtype=float)
    
    # If we have comparisons
    if not curr_by_cat.empty and not prev_by_cat.empty:
        for cat in curr_by_cat.index:
            curr_amt = curr_by_cat[cat]
            if cat in prev_by_cat.index:
                prev_amt = prev_by_cat[cat]
                diff_pct = ((curr_amt - prev_amt) / prev_amt) * 100
                if abs(diff_pct) >= 5:
                    status_word = "more" if diff_pct > 0 else "less"
                    insights.append(f"You spent {abs(diff_pct):.0f}% {status_word} on {cat} this month compared to last month.")
            else:
                insights.append(f"New category spend: You spent ₹{curr_amt:,.0f} on {cat} this month (no spending last month).")
                
        # Also check categories in previous but not in current
        for cat in prev_by_cat.index:
            if cat not in curr_by_cat.index:
                insights.append(f"Great job! You saved 100% on {cat} this month (spent ₹{prev_by_cat[cat]:,.0f} last month).")
    else:
        # Fallback: Compare current month to historical average per category
        hist_df = expenses_df[~((expenses_df["year"] == curr_yr) & (expenses_df["month"] == curr_mo))]
        if not hist_df.empty:
            # Group by year-month-category to find average monthly spend per category
            hist_monthly = hist_df.groupby(["year", "month", "category"])["amount"].sum().reset_index()
            cat_avg = hist_monthly.groupby("category")["amount"].mean()
            
            for cat in curr_by_cat.index:
                curr_amt = curr_by_cat[cat]
                if cat in cat_avg.index:
                    avg_amt = cat_avg[cat]
                    diff_pct = ((curr_amt - avg_amt) / avg_amt) * 100
                    if abs(diff_pct) >= 5:
                        status_word = "higher" if diff_pct > 0 else "lower"
                        insights.append(f"Your {cat} spending is {abs(diff_pct):.0f}% {status_word} than your historical monthly average.")
        else:
            insights.append("Tracking started: Collect data for at least two months to see automatic month-over-month trends.")
            
    # Add general summaries
    total_curr_exp = curr_month_df["amount"].sum() if not curr_month_df.empty else 0
    total_prev_exp = prev_month_df["amount"].sum() if not prev_month_df.empty else 0
    if total_curr_exp > 0 and total_prev_exp > 0:
        diff_pct = ((total_curr_exp - total_prev_exp) / total_prev_exp) * 100
        direction = "increased" if diff_pct > 0 else "decreased"
        insights.insert(0, f"Overall spending has {direction} by {abs(diff_pct):.1f}% compared to last month.")
        
    if not insights:
        insights.append("Your expenses are stable and close to your standard averages. Keep it up!")
        
    return insights[:5]  # Limit to top 5 insights

def calculate_health_score(df, budget_limit, goals, subscriptions):
    """
    Computes a Financial Health Score out of 100.
    Weights:
      - Savings Rate: 40 points
      - Budget Adherence: 35 points
      - Subscriptions burden: 15 points
      - Goal progress: 10 points
    """
    today = date.today()
    summary = get_monthly_summary(df, today.year, today.month)
    
    # 1. Savings Rate Score (Max 40 points)
    # Target: 30%+ savings rate gets full points. Negative savings rate gets 0.
    savings_rate = summary["savings_rate"]
    if savings_rate >= 30:
        savings_score = 40.0
    elif savings_rate <= 0:
        savings_score = 0.0
    else:
        savings_score = (savings_rate / 30.0) * 40.0
        
    # 2. Budget Adherence Score (Max 35 points)
    # If expenses are below budget, full points. If exceeded, scale down.
    expense = summary["expense"]
    if expense <= budget_limit:
        budget_score = 35.0
    else:
        over_ratio = (expense - budget_limit) / budget_limit
        budget_score = max(0.0, 35.0 - (over_ratio * 35.0))
        
    # 3. Subscriptions Burden (Max 15 points)
    # If monthly subscriptions consume >20% of income, score scales down.
    income = summary["income"]
    sub_total = sum(s.amount for s in subscriptions)
    if sub_total == 0:
        sub_score = 15.0
    elif income == 0:
        sub_score = 5.0  # Basic penalty if subscriptions run without income
    else:
        sub_ratio = sub_total / income
        if sub_ratio <= 0.05:
            sub_score = 15.0
        elif sub_ratio >= 0.25:
            sub_score = 0.0
        else:
            # Linear scaling between 5% and 25%
            sub_score = 15.0 * (1.0 - (sub_ratio - 0.05) / 0.20)
            
    # 4. Saving Goal Progress (Max 10 points)
    # Average progress of all active goals.
    if not goals:
        goal_score = 10.0  # Default to full if no goals are set
    else:
        avg_progress = np.mean([g.progress_percentage for g in goals])
        goal_score = (avg_progress / 100.0) * 10.0
        
    total_score = round(savings_score + budget_score + sub_score + goal_score)
    total_score = max(0, min(100, total_score))
    
    # Determine status
    if total_score >= 85:
        status = "Excellent"
        color = "#10b981"  # Green
    elif total_score >= 70:
        status = "Good"
        color = "#3b82f6"  # Blue
    elif total_score >= 50:
        status = "Average"
        color = "#f59e0b"  # Amber
    elif total_score >= 30:
        status = "Poor"
        color = "#f97316"  # Orange
    else:
        status = "Critical"
        color = "#ef4444"  # Red
        
    return {
        "score": total_score,
        "status": status,
        "color": color,
        "breakdown": {
            "savings_rate_score": round(savings_score, 1),
            "budget_score": round(budget_score, 1),
            "subscription_score": round(sub_score, 1),
            "goal_score": round(goal_score, 1)
        }
    }

def get_business_summary(df, year=None, month=None):
    """
    Returns Gross Revenue, COGS, OpEx, Gross Profit, Net Profit, and Net Margin.
    """
    if df.empty:
        return {"revenue": 0.0, "cogs": 0.0, "opex": 0.0, "gross_profit": 0.0, "net_profit": 0.0, "net_margin": 0.0}
        
    if year is None or month is None:
        today = date.today()
        year, month = today.year, today.month

    if "profile" not in df.columns:
        return {"revenue": 0.0, "cogs": 0.0, "opex": 0.0, "gross_profit": 0.0, "net_profit": 0.0, "net_margin": 0.0}

    biz_df = df[(df["profile"] == "Business") & (df["year"] == year) & (df["month"] == month)]
    if biz_df.empty:
        return {"revenue": 0.0, "cogs": 0.0, "opex": 0.0, "gross_profit": 0.0, "net_profit": 0.0, "net_margin": 0.0}

    revenue = biz_df[biz_df["type"] == "Income"]["amount"].sum()
    
    cogs_categories = ["Inventory", "Raw Materials", "Shipping & Logistics", "Subcontractors"]
    cogs = biz_df[(biz_df["type"] == "Expense") & (biz_df["category"].isin(cogs_categories))]["amount"].sum()
    opex = biz_df[(biz_df["type"] == "Expense") & (~biz_df["category"].isin(cogs_categories))]["amount"].sum()
    
    gross_profit = revenue - cogs
    net_profit = gross_profit - opex
    
    net_margin = (net_profit / revenue * 100) if revenue > 0 else 0.0
    net_margin = max(-100.0, min(100.0, net_margin))
    
    return {
        "revenue": float(revenue),
        "cogs": float(cogs),
        "opex": float(opex),
        "gross_profit": float(gross_profit),
        "net_profit": float(net_profit),
        "net_margin": round(float(net_margin), 2)
    }

def get_business_pl_statement(df, year=None, month=None):
    """
    Returns category-wise breakdown of Revenue, COGS, and OpEx for P&L presentation.
    """
    if df.empty or "profile" not in df.columns:
        return {"revenue_by_cat": {}, "cogs_by_cat": {}, "opex_by_cat": {}}
        
    if year is None or month is None:
        today = date.today()
        year, month = today.year, today.month
        
    biz_df = df[(df["profile"] == "Business") & (df["year"] == year) & (df["month"] == month)]
    if biz_df.empty:
        return {"revenue_by_cat": {}, "cogs_by_cat": {}, "opex_by_cat": {}}
        
    rev_df = biz_df[biz_df["type"] == "Income"]
    cogs_categories = ["Inventory", "Raw Materials", "Shipping & Logistics", "Subcontractors"]
    cogs_df = biz_df[(biz_df["type"] == "Expense") & (biz_df["category"].isin(cogs_categories))]
    opex_df = biz_df[(biz_df["type"] == "Expense") & (~biz_df["category"].isin(cogs_categories))]
    
    revenue_by_cat = rev_df.groupby("category")["amount"].sum().sort_values(ascending=False).to_dict()
    cogs_by_cat = cogs_df.groupby("category")["amount"].sum().sort_values(ascending=False).to_dict()
    opex_by_cat = opex_df.groupby("category")["amount"].sum().sort_values(ascending=False).to_dict()
    
    return {
        "revenue_by_cat": {k: float(v) for k, v in revenue_by_cat.items()},
        "cogs_by_cat": {k: float(v) for k, v in cogs_by_cat.items()},
        "opex_by_cat": {k: float(v) for k, v in opex_by_cat.items()}
    }

def calculate_business_health_score(df, budget_limit):
    """
    Computes a Business Financial Health Score out of 100.
    Weights:
      - Net Profit Margin: 45 points (Net Margin >= 25% gets full points. Margin <= 0 gets 0 points)
      - Budget Adherence: 35 points (Business Expenses <= Business Budget Limit gets full points)
      - Cash Flow Health: 20 points (Total Revenue >= 1.5 * Total Expenses gets full points)
    """
    today = date.today()
    summary = get_business_summary(df, today.year, today.month)
    
    # 1. Net Profit Margin Score (Max 45 points)
    margin = summary["net_margin"]
    if margin >= 25.0:
        margin_score = 45.0
    elif margin <= 0.0:
        margin_score = 0.0
    else:
        margin_score = (margin / 25.0) * 45.0
        
    # 2. Budget Adherence Score (Max 35 points)
    expenses = summary["cogs"] + summary["opex"]
    if expenses <= budget_limit:
        budget_score = 35.0
    else:
        over_ratio = (expenses - budget_limit) / budget_limit
        budget_score = max(0.0, 35.0 - (over_ratio * 35.0))
        
    # 3. Cash Flow Health Score (Max 20 points)
    revenue = summary["revenue"]
    if revenue == 0:
        cf_score = 0.0
    elif expenses == 0:
        cf_score = 20.0
    else:
        ratio = revenue / expenses
        if ratio >= 1.5:
            cf_score = 20.0
        elif ratio <= 1.0:
            cf_score = 5.0
        else:
            cf_score = 5.0 + ((ratio - 1.0) / 0.5) * 15.0
            
    total_score = round(margin_score + budget_score + cf_score)
    total_score = max(0, min(100, total_score))
    
    # Determine status
    if total_score >= 85:
        status = "Excellent"
        color = "#10b981"  # Green
    elif total_score >= 70:
        status = "Good"
        color = "#3b82f6"  # Blue
    elif total_score >= 50:
        status = "Average"
        color = "#f59e0b"  # Amber
    elif total_score >= 30:
        status = "Poor"
        color = "#f97316"  # Orange
    else:
        status = "Critical"
        color = "#ef4444"  # Red
        
    return {
        "score": total_score,
        "status": status,
        "color": color,
        "breakdown": {
            "margin_score": round(margin_score, 1),
            "budget_score": round(budget_score, 1),
            "cash_flow_score": round(cf_score, 1)
        }
    }

def run_business_expense_analyzer(sales_df, expenses_df):
    """
    Compares current month category expenses with the previous month.
    Returns list of warning dicts: {category, pct_increase, suggestion}
    """
    if expenses_df.empty:
        return []
    
    # Ensure date is datetime
    expenses_df = expenses_df.copy()
    expenses_df["date"] = pd.to_datetime(expenses_df["date"])
    expenses_df["year"] = expenses_df["date"].dt.year
    expenses_df["month"] = expenses_df["date"].dt.month
    
    today = date.today()
    curr_yr, curr_mo = today.year, today.month
    if curr_mo == 1:
        prev_yr, prev_mo = curr_yr - 1, 12
    else:
        prev_yr, prev_mo = curr_yr, curr_mo - 1
        
    curr_exp = expenses_df[(expenses_df["year"] == curr_yr) & (expenses_df["month"] == curr_mo)]
    prev_exp = expenses_df[(expenses_df["year"] == prev_yr) & (expenses_df["month"] == prev_mo)]
    
    if curr_exp.empty or prev_exp.empty:
        return []
        
    curr_by_cat = curr_exp.groupby("category")["amount"].sum()
    prev_by_cat = prev_exp.groupby("category")["amount"].sum()
    
    warnings = []
    for cat in curr_by_cat.index:
        if cat in prev_by_cat.index:
            c_amt = curr_by_cat[cat]
            p_amt = prev_by_cat[cat]
            if p_amt > 0:
                diff_pct = ((c_amt - p_amt) / p_amt) * 100
                if diff_pct >= 15.0:
                    suggestions = {
                        "Marketing": "Review unnecessary campaigns and focus on high-conversion channels.",
                        "Raw Material": "Negotiate volume discounts with vendors or source alternative suppliers.",
                        "Transportation": "Optimize delivery routes and audit carrier fuel surcharges.",
                        "Employee Salary": "Review overtime allocations and contractor headcounts.",
                        "Miscellaneous": "Audit petty cash slips and eliminate non-essential office supplies."
                    }
                    sug = suggestions.get(cat, f"{cat} cost increased. Review itemized invoices to find savings.")
                    warnings.append({
                        "category": cat,
                        "pct_increase": round(diff_pct, 1),
                        "current": float(c_amt),
                        "previous": float(p_amt),
                        "suggestion": f"{cat} cost increased by {diff_pct:.0f}%. {sug}"
                    })
    return warnings

def run_business_saving_suggestions(expenses_df):
    """
    Checks if utility bill expenses (Electricity, Internet, etc.) exceed historical averages.
    Returns list of recommendation dicts.
    """
    if expenses_df.empty:
        return []
        
    expenses_df = expenses_df.copy()
    expenses_df["date"] = pd.to_datetime(expenses_df["date"])
    expenses_df["year"] = expenses_df["date"].dt.year
    expenses_df["month"] = expenses_df["date"].dt.month
    
    today = date.today()
    curr_yr, curr_mo = today.year, today.month
    
    curr_exp = expenses_df[(expenses_df["year"] == curr_yr) & (expenses_df["month"] == curr_mo)]
    hist_exp = expenses_df[~((expenses_df["year"] == curr_yr) & (expenses_df["month"] == curr_mo))]
    
    if curr_exp.empty or hist_exp.empty:
        return []
        
    curr_by_cat = curr_exp.groupby("category")["amount"].sum()
    hist_monthly = hist_exp.groupby(["year", "month", "category"])["amount"].sum().reset_index()
    hist_avg = hist_monthly.groupby("category")["amount"].mean()
    
    suggestions = []
    target_categories = ["Electricity Bill", "Internet", "Office Rent", "Miscellaneous"]
    
    for cat in curr_by_cat.index:
        if cat in target_categories and cat in hist_avg.index:
            c_val = curr_by_cat[cat]
            h_avg = hist_avg[cat]
            if h_avg > 0 and c_val > h_avg * 1.20:
                diff_pct = ((c_val - h_avg) / h_avg) * 100
                if cat == "Electricity Bill":
                    msg = "Switch off heavy hardware during idle hours and install energy-efficient lighting."
                elif cat == "Internet":
                    msg = "Downgrade unused bandwidth lines or re-negotiate internet service provider contracts."
                else:
                    msg = "Conduct audits on utility meters or look for service leakage."
                suggestions.append({
                    "category": cat,
                    "current": float(c_val),
                    "average": float(h_avg),
                    "pct_extra": round(diff_pct, 1),
                    "suggestion": f"You are spending {diff_pct:.0f}% extra on {cat} compared to historical averages (₹{c_val:,.0f} vs ₹{h_avg:,.0f}). {msg}"
                })
    return suggestions

def predict_next_month_profit(sales_df, expenses_df):
    """
    Calculates profit trajectory over the last 6 months to predict next month's profit using a moving average.
    Returns: projected_profit, trend_direction ('up', 'down', 'stable')
    """
    if sales_df.empty:
        return 0.0, "stable"
        
    sales_df = sales_df.copy()
    sales_df["date"] = pd.to_datetime(sales_df["date"])
    sales_df["year_month"] = sales_df["date"].dt.to_period("M")
    
    monthly_sales = sales_df.groupby("year_month")["amount"].sum()
    
    monthly_exp = pd.Series(dtype=float)
    if not expenses_df.empty:
        expenses_df = expenses_df.copy()
        expenses_df["date"] = pd.to_datetime(expenses_df["date"])
        expenses_df["year_month"] = expenses_df["date"].dt.to_period("M")
        monthly_exp = expenses_df.groupby("year_month")["amount"].sum()
        
    all_months = monthly_sales.index.union(monthly_exp.index).sort_values()[-6:]
    profits = []
    for m in all_months:
        rev = monthly_sales.get(m, 0.0)
        exp = monthly_exp.get(m, 0.0)
        profits.append(rev - exp)
        
    if not profits:
        return 0.0, "stable"
        
    avg_profit = float(np.mean(profits))
    
    if len(profits) >= 2:
        diffs = np.diff(profits)
        avg_diff = np.mean(diffs)
        if avg_diff > 1000:
            trend = "up"
        elif avg_diff < -1000:
            trend = "down"
        else:
            trend = "stable"
    else:
        trend = "stable"
        
    return round(avg_profit, 2), trend

def calculate_business_health_score_extended(sales_df, expenses_df, customers_df):
    """
    Calculates the extended Business Health Score (out of 100) based on:
    - Revenue Growth (20 points)
    - Profit Margin (30 points)
    - Pending Payments Ratio (20 points)
    - Cash Flow (15 points)
    - Expense Control (15 points)
    """
    score = 0
    breakdown = {}
    
    total_rev = sales_df["amount"].sum() if not sales_df.empty else 0.0
    total_exp = expenses_df["amount"].sum() if not expenses_df.empty else 0.0
    net_profit = total_rev - total_exp
    
    # 1. Profit Margin Score (Max 30 points)
    margin = (net_profit / total_rev) if total_rev > 0 else 0.0
    if margin >= 0.20:
        margin_score = 30
    elif margin <= 0:
        margin_score = 0
    else:
        margin_score = int((margin / 0.20) * 30)
    score += margin_score
    breakdown["Profit Margin"] = margin_score
    
    # 2. Revenue Growth (Max 20 points)
    if not sales_df.empty:
        sales_df = sales_df.copy()
        sales_df["date"] = pd.to_datetime(sales_df["date"])
        sales_df["month"] = sales_df["date"].dt.month
        sales_df["year"] = sales_df["date"].dt.year
        
        today = date.today()
        curr_sales = sales_df[(sales_df["year"] == today.year) & (sales_df["month"] == today.month)]["amount"].sum()
        
        lm_yr, lm_mo = (today.year - 1, 12) if today.month == 1 else (today.year, today.month - 1)
        prev_sales = sales_df[(sales_df["year"] == lm_yr) & (sales_df["month"] == lm_mo)]["amount"].sum()
        
        if prev_sales > 0:
            growth = (curr_sales - prev_sales) / prev_sales
            if growth >= 0.10:
                growth_score = 20
            elif growth <= -0.10:
                growth_score = 5
            else:
                growth_score = int(12 + (growth / 0.10) * 8)
        else:
            growth_score = 15
    else:
        growth_score = 0
    score += growth_score
    breakdown["Revenue Growth"] = growth_score
    
    # 3. Pending Payments Ratio (Max 20 points)
    total_pending = customers_df["pending_amount"].sum() if not customers_df.empty else 0.0
    if total_pending == 0:
        pending_score = 20
    elif total_rev == 0:
        pending_score = 10
    else:
        pending_ratio = total_pending / total_rev
        if pending_ratio <= 0.05:
            pending_score = 20
        elif pending_ratio >= 0.30:
            pending_score = 0
        else:
            pending_score = int(20 * (1.0 - (pending_ratio - 0.05) / 0.25))
    score += pending_score
    breakdown["Receivables Risk"] = pending_score
    
    # 4. Cash Flow Health (Max 15 points)
    if total_rev > 0:
        cf_ratio = (total_rev - total_exp) / total_rev
        if cf_ratio >= 0.15:
            cf_score = 15
        elif cf_ratio <= 0:
            cf_score = 0
        else:
            cf_score = int((cf_ratio / 0.15) * 15)
    else:
        cf_score = 0
    score += cf_score
    breakdown["Cash Flow"] = cf_score
    
    # 5. Expense Control (Max 15 points)
    if total_rev > 0:
        exp_ratio = total_exp / total_rev
        if exp_ratio <= 0.70:
            exp_score = 15
        elif exp_ratio >= 1.0:
            exp_score = 0
        else:
            exp_score = int(15 * (1.0 - (exp_ratio - 0.70) / 0.30))
    else:
        exp_score = 10
    score += exp_score
    breakdown["Expense Control"] = exp_score
    
    # Determine Status
    if score >= 85:
        status = "Excellent"
        color = "#10b981"
    elif score >= 70:
        status = "Good"
        color = "#3b82f6"
    elif score >= 50:
        status = "Average"
        color = "#f59e0b"
    elif score >= 30:
        status = "Poor"
        color = "#f97316"
    else:
        status = "Critical"
        color = "#ef4444"
        
    return {
        "score": score,
        "status": status,
        "color": color,
        "breakdown": breakdown
    }

def run_smart_purchase_advisor(item_name, price, remaining_budget, inventory_list=None):
    """
    Advises the user on capital purchases.
    """
    advisor_result = {}
    
    if price > remaining_budget:
        advisor_result["status"] = "exceeded"
        advisor_result["warning"] = f"Budget Exceeded! The item costs ₹{price:,.2f}, which is above your remaining budget of ₹{remaining_budget:,.2f}."
    else:
        advisor_result["status"] = "ok"
        advisor_result["warning"] = f"The item costs ₹{price:,.2f}, which fits within your remaining budget of ₹{remaining_budget:,.2f}."
        
    q_lower = item_name.lower().strip()
    catalog_averages = {
        "printer": 11500.0,
        "laptop": 42000.0,
        "chair": 4500.0,
        "desk": 8000.0,
        "monitor": 9500.0,
        "scanner": 7500.0
    }
    
    avg_price = None
    for k, v in catalog_averages.items():
        if k in q_lower:
            avg_price = v
            break
            
    if avg_price:
        advisor_result["average_price"] = avg_price
        if price > avg_price:
            savings = price - avg_price
            pct_over = ((price - avg_price) / avg_price) * 100
            advisor_result["recommendation"] = f"This purchase is {pct_over:.0f}% higher than the average catalog price of ₹{avg_price:,.0f} for a {item_name}. Recommend purchasing from Vendor B to save ₹{savings:,.0f}."
        else:
            advisor_result["recommendation"] = f"Great deal! This price is below or equal to the average catalog price of ₹{avg_price:,.0f}."
    else:
        advisor_result["average_price"] = price * 0.95
        advisor_result["recommendation"] = f"Compare quotes from at least 2 alternate suppliers to ensure you get the best bulk pricing."
        
    return advisor_result

def analyze_weak_sections(sales_df, expenses_df, customers_df):
    """
    Analyzes business transactions and ledger states to pinpoint the weakest
    operational area causing profit erosion or cash flow congestion.
    """
    result = {
        "weak_section": "None (Operational Efficiency is Good)",
        "description": "Gross profit margins are strong, opex is controlled, and customer accounts are current.",
        "impact": "0%",
        "suggestions": [
            "Maintain current cost control measures.",
            "Consider investing surplus profits into low-risk yield assets or inventory expansion."
        ]
    }
    
    total_sales = sales_df["amount"].sum() if not sales_df.empty else 0.0
    total_expenses = expenses_df["amount"].sum() if not expenses_df.empty else 0.0
    net_profit = total_sales - total_expenses
    
    # 1. Deficit checking (Net operating loss)
    if net_profit < 0 and total_sales > 0:
        expense_ratio = (total_expenses / total_sales) * 100
        result["weak_section"] = "Net Operating Deficit (High Expense Ratio)"
        result["description"] = f"Your business is running a net operating loss of ₹{abs(net_profit):,.2f} because operational expenditures take up {expense_ratio:.1f}% of total sales."
        result["impact"] = f"{expense_ratio - 100:.1f}% Expense Overrun"
        
        biggest_cat = "N/A"
        if not expenses_df.empty:
            cat_sums = expenses_df.groupby("category")["amount"].sum()
            if not cat_sums.empty:
                biggest_cat = cat_sums.idxmax()
                biggest_cat_val = cat_sums.max()
                biggest_cat_pct = (biggest_cat_val / total_expenses) * 100
                result["suggestions"] = [
                    f"Audit and cut down on the largest expenditure: {biggest_cat} (₹{biggest_cat_val:,.2f}), which is {biggest_cat_pct:.1f}% of total expenses.",
                    "Review utility and monthly subscriptions to lower fixed overheads.",
                    "Halt marketing campaigns that are not driving direct conversions.",
                    "Renegotiate payment schedules with vendors to defer payments."
                ]
                return result

    # 2. Receivables lag (Unpaid customer balance bottlenecking cash flow)
    total_pending_cust = 0.0
    total_paid_cust = 0.0
    if not customers_df.empty:
        total_pending_cust = customers_df["pending_amount"].sum()
        total_paid_cust = customers_df["paid_amount"].sum()
        
    if total_pending_cust > 0 and (total_pending_cust / (total_paid_cust + total_pending_cust)) > 0.15:
        pending_ratio = (total_pending_cust / (total_paid_cust + total_pending_cust)) * 100
        result["weak_section"] = "Customer Receivables (Cash Flow Lag)"
        result["description"] = f"Your cash flow is bottlenecked by outstanding customer receivables. Customers owe ₹{total_pending_cust:,.2f}, representing {pending_ratio:.1f}% of all client billing."
        result["impact"] = f"₹{total_pending_cust:,.2f} Cash Bottleneck"
        result["suggestions"] = [
            "Implement a strict credit control policy with penalties for late payments.",
            "Send automated payment reminders to clients past their due dates.",
            "Offer early settlement discounts (e.g., 2% off if paid in 5 days) to accelerate recovery.",
            "Transition to milestone payments or advance deposits for high-value orders."
        ]
        return result

    # 3. High Utility Overhead Spikes
    utility_categories = ["Electricity Bill", "Internet"]
    if not expenses_df.empty:
        utilities_sum = expenses_df[expenses_df["category"].isin(utility_categories)]["amount"].sum()
        if total_expenses > 0 and (utilities_sum / total_expenses) > 0.15:
            util_ratio = (utilities_sum / total_expenses) * 100
            result["weak_section"] = "Utility Overhead Costs"
            result["description"] = f"Utility expenses (Electricity, Internet) represent {util_ratio:.1f}% of your total expenses (₹{utilities_sum:,.2f}), exceeding standard benchmarks."
            result["impact"] = f"{util_ratio:.1f}% of Overhead"
            result["suggestions"] = [
                "Audit energy usage in the office during non-operating hours.",
                "Renegotiate internet packages or switch to a cheaper commercial ISP.",
                "Enforce shut-down policies for workstations when idle."
            ]
            return result

    # 4. Low Revenue Volume
    if total_sales < 10000.0:
        result["weak_section"] = "Low Revenue Volume"
        result["description"] = f"Your monthly sales are extremely low (₹{total_sales:,.2f}), which makes it impossible to cover baseline expenses."
        result["impact"] = f"Insufficient Volume"
        result["suggestions"] = [
            "Launch local promotional marketing or digital campaigns to drive foot traffic.",
            "Bundle slow-moving stock with popular products to clear items.",
            "Offer introductory discounts or loyalty benefits to expand the customer base.",
            "Review pricing sheets to see if current prices are too low."
        ]
        return result

    # 5. COGS (Inventory / Raw Materials) drain
    cogs_categories = ["Inventory", "Raw Materials"]
    if not expenses_df.empty:
        cogs_sum = expenses_df[expenses_df["category"].isin(cogs_categories)]["amount"].sum()
        if total_sales > 0 and (cogs_sum / total_sales) > 0.60:
            cogs_ratio = (cogs_sum / total_sales) * 100
            result["weak_section"] = "Cost of Goods Sold (COGS)"
            result["description"] = f"Your procurement and raw material expenses represent {cogs_ratio:.1f}% of your gross revenue, leaving narrow margins for operating expenses."
            result["impact"] = f"{cogs_ratio:.1f}% of Revenue"
            result["suggestions"] = [
                "Renegotiate unit pricing with your suppliers for raw materials.",
                "Audit inventory storage to minimize wastage and spoilage.",
                "Increase retail selling prices slightly to improve the gross profit margin.",
                "Look for wholesale alternatives or buy in bulk to lower the cost per unit."
            ]
            return result

    return result


