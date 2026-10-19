"""
FINSIGHT - Insight Engine GUI View (gui_ai_view.py)
--------------------------------------------------
Renders the dedicated "Insight Engine" dashboard:
- Top KPI Summary Cards (Health Score, Spending Forecast, Unusual Activity, Goal Progress)
- Section 1: Monthly Spending Forecast
- Section 2: Unusual Spending Alerts
- Section 3: Your Financial Profile
- Section 4: Savings Goal Planner
- Utility: Smart Category Assistant
"""

import tkinter as tk
from tkinter import ttk, messagebox
import gui_theme as theme
import ml_engine

def create_ai_insights_page(app):
    """Creates the full Insight Engine dashboard page."""
    from gui_app import ScrollableFrame
    page = ScrollableFrame(app.content_container)
    frame = page.scrollable_frame

    # 1. Top Bar Header
    top_bar = tk.Frame(frame, bg=theme.BG_MAIN)
    top_bar.pack(fill="x", padx=25, pady=20)

    title_box = tk.Frame(top_bar, bg=theme.BG_MAIN)
    title_box.pack(fill="x")

    tk.Label(
        title_box, 
        text="⚡ Insight Engine", 
        font=theme.FONT_TITLE, 
        fg=theme.TEXT_PRIMARY, 
        bg=theme.BG_MAIN
    ).pack(anchor="w")

    tk.Label(
        title_box, 
        text="Understand your spending, track your goals, and make smarter financial decisions.", 
        font=theme.FONT_BODY, 
        fg=theme.TEXT_MUTED, 
        bg=theme.BG_MAIN
    ).pack(anchor="w", pady=(3, 0))

    # 2. Top KPI Cards Row
    app.ai_kpi_container = tk.Frame(frame, bg=theme.BG_MAIN)
    app.ai_kpi_container.pack(fill="x", padx=25, pady=(0, 15))
    for i in range(4):
        app.ai_kpi_container.columnconfigure(i, weight=1)

    app.ai_kpi_cards = []
    kpi_defs = [
        ("🧬 Financial Health Score", "-- / 100", "Financial Profile", theme.ACCENT),
        ("📈 Projected Month-End Spend", "₹ --", "Spending Forecast", theme.INCOME),
        ("⚠️ Unusual Spending Alerts", "-- Alerts", "Activity Monitoring", theme.WARNING),
        ("🎯 Savings Goal Progress", "-- %", "Goal Feasibility", "#a78bfa")
    ]
    for idx, (title, val, sub, col) in enumerate(kpi_defs):
        c = tk.Frame(app.ai_kpi_container, bg=theme.BG_CARD, highlightbackground=theme.BORDER, highlightthickness=1, height=95)
        c.grid(row=0, column=idx, padx=6, sticky="nsew")
        c.pack_propagate(False)
        
        lbl_t = tk.Label(c, text=title, font=theme.FONT_SMALL, fg=theme.TEXT_MUTED, bg=theme.BG_CARD)
        lbl_t.pack(anchor="w", padx=16, pady=(12, 2))
        
        lbl_v = tk.Label(c, text=val, font=("Segoe UI", 16, "bold"), fg=col, bg=theme.BG_CARD)
        lbl_v.pack(anchor="w", padx=16)
        
        lbl_s = tk.Label(c, text=sub, font=("Segoe UI", 8), fg=theme.TEXT_MUTED, bg=theme.BG_CARD)
        lbl_s.pack(anchor="w", padx=16)
        
        app.ai_kpi_cards.append((lbl_t, lbl_v, lbl_s))

    # 3. Two-Column Main Content Layout
    main_cols = tk.Frame(frame, bg=theme.BG_MAIN)
    main_cols.pack(fill="both", expand=True, padx=25, pady=5)
    main_cols.columnconfigure(0, weight=1)
    main_cols.columnconfigure(1, weight=1)

    left_col = tk.Frame(main_cols, bg=theme.BG_MAIN)
    left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

    right_col = tk.Frame(main_cols, bg=theme.BG_MAIN)
    right_col.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

    # ==============================================================
    # LEFT COLUMN: Spending Forecast + Unusual Spending Alerts
    # ==============================================================
    
    # SECTION 1: Monthly Spending Forecast
    card_fc = tk.Frame(left_col, bg=theme.BG_CARD, highlightbackground=theme.BORDER, highlightthickness=1)
    card_fc.pack(fill="x", pady=(0, 15))
    
    tk.Label(card_fc, text="📈 Monthly Spending Forecast", font=theme.FONT_SUBTITLE, fg=theme.TEXT_PRIMARY, bg=theme.BG_CARD).pack(anchor="w", padx=20, pady=(15, 5))
    tk.Label(card_fc, text="Projected end-of-month expenses based on your daily spending habits.", font=theme.FONT_SMALL, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).pack(anchor="w", padx=20, pady=(0, 10))
    
    app.ai_fc_content = tk.Frame(card_fc, bg=theme.BG_CARD)
    app.ai_fc_content.pack(fill="both", expand=True, padx=20, pady=(0, 15))

    # SECTION 2: Unusual Spending Alerts
    card_anomaly = tk.Frame(left_col, bg=theme.BG_CARD, highlightbackground=theme.BORDER, highlightthickness=1)
    card_anomaly.pack(fill="x", pady=(0, 15))

    tk.Label(card_anomaly, text="⚠️ Unusual Spending Alerts", font=theme.FONT_SUBTITLE, fg=theme.TEXT_PRIMARY, bg=theme.BG_CARD).pack(anchor="w", padx=20, pady=(15, 5))
    tk.Label(card_anomaly, text="Transactions that stand out compared to your typical spending patterns.", font=theme.FONT_SMALL, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).pack(anchor="w", padx=20, pady=(0, 5))

    app.ai_anomaly_content = tk.Frame(card_anomaly, bg=theme.BG_CARD)
    app.ai_anomaly_content.pack(fill="both", expand=True, padx=20, pady=(0, 15))

    # ==============================================================
    # RIGHT COLUMN: Financial Profile + Savings Goals + Category Assistant
    # ==============================================================

    # SECTION 3: Your Financial Profile
    card_persona = tk.Frame(right_col, bg=theme.BG_CARD, highlightbackground=theme.BORDER, highlightthickness=1)
    card_persona.pack(fill="x", pady=(0, 15))

    tk.Label(card_persona, text="🧬 Your Financial Profile", font=theme.FONT_SUBTITLE, fg=theme.TEXT_PRIMARY, bg=theme.BG_CARD).pack(anchor="w", padx=20, pady=(15, 5))
    tk.Label(card_persona, text="A clear overview of your current financial habits and recommendations.", font=theme.FONT_SMALL, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).pack(anchor="w", padx=20, pady=(0, 10))

    app.ai_persona_content = tk.Frame(card_persona, bg=theme.BG_CARD)
    app.ai_persona_content.pack(fill="both", expand=True, padx=20, pady=(0, 15))

    # SECTION 4: Savings Goal Planner
    card_goals = tk.Frame(right_col, bg=theme.BG_CARD, highlightbackground=theme.BORDER, highlightthickness=1)
    card_goals.pack(fill="x", pady=(0, 15))

    tk.Label(card_goals, text="🎯 Savings Goal Planner", font=theme.FONT_SUBTITLE, fg=theme.TEXT_PRIMARY, bg=theme.BG_CARD).pack(anchor="w", padx=20, pady=(15, 5))
    tk.Label(card_goals, text="Track how close you are to reaching your savings targets.", font=theme.FONT_SMALL, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).pack(anchor="w", padx=20, pady=(0, 10))

    app.ai_goals_content = tk.Frame(card_goals, bg=theme.BG_CARD)
    app.ai_goals_content.pack(fill="both", expand=True, padx=20, pady=(0, 15))

    # UTILITY: Smart Category Assistant
    card_nlp = tk.Frame(right_col, bg=theme.BG_CARD, highlightbackground=theme.BORDER, highlightthickness=1)
    card_nlp.pack(fill="x", pady=(0, 15))

    tk.Label(card_nlp, text="💡 Smart Category Assistant", font=theme.FONT_SUBTITLE, fg=theme.TEXT_PRIMARY, bg=theme.BG_CARD).pack(anchor="w", padx=20, pady=(15, 5))
    tk.Label(card_nlp, text="Type an expense description to automatically find the most appropriate category.", font=theme.FONT_SMALL, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).pack(anchor="w", padx=20, pady=(0, 10))

    nlp_test_box = tk.Frame(card_nlp, bg=theme.BG_CARD)
    nlp_test_box.pack(fill="x", padx=20, pady=5)

    tk.Label(nlp_test_box, text="Transaction Description:", font=theme.FONT_BODY_BOLD, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).pack(anchor="w")
    
    app.ai_nlp_input = tk.Entry(
        nlp_test_box,
        font=theme.FONT_BODY,
        bg=theme.BG_MAIN,
        fg=theme.TEXT_PRIMARY,
        insertbackground="white",
        bd=1,
        relief="solid"
    )
    app.ai_nlp_input.pack(fill="x", pady=6)
    app.ai_nlp_input.insert(0, "swiggy pizza dinner with office colleagues")

    btn_nlp_row = tk.Frame(nlp_test_box, bg=theme.BG_CARD)
    btn_nlp_row.pack(fill="x", pady=5)

    tk.Button(
        btn_nlp_row,
        text="✨ Suggest Category",
        font=theme.FONT_BODY_BOLD,
        bg=theme.ACCENT,
        fg=theme.TEXT_DARK,
        bd=0,
        padx=12,
        pady=5,
        cursor="hand2",
        command=lambda: test_nlp_playground(app)
    ).pack(side="left")

    tk.Button(
        btn_nlp_row,
        text="🔄 Sync with My Records",
        font=theme.FONT_SMALL,
        bg="#374151",
        fg=theme.TEXT_PRIMARY,
        bd=0,
        padx=10,
        pady=5,
        cursor="hand2",
        command=lambda: retrain_nlp_user(app)
    ).pack(side="right")

    # Sample prompt pills
    tk.Label(card_nlp, text="Quick Examples:", font=theme.FONT_SMALL, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).pack(anchor="w", padx=20, pady=(8, 2))
    pills_frame = tk.Frame(card_nlp, bg=theme.BG_CARD)
    pills_frame.pack(fill="x", padx=20, pady=2)

    samples = [
        "uber cab to airport",
        "zara jacket & jeans",
        "electricity wifi bill",
        "cult fit monthly gym",
        "apartment flat rent"
    ]
    for s in samples:
        b = tk.Button(
            pills_frame,
            text=f"• {s}",
            font=("Segoe UI", 8),
            bg=theme.BG_MAIN,
            fg=theme.ACCENT,
            bd=0,
            cursor="hand2",
            padx=6,
            pady=3,
            command=lambda text=s: set_and_predict_nlp(app, text)
        )
        b.pack(side="left", padx=2, pady=2)

    # Output Card for Assistant
    app.ai_nlp_result_frame = tk.Frame(card_nlp, bg=theme.BG_MAIN, highlightbackground=theme.BORDER, highlightthickness=1)
    app.ai_nlp_result_frame.pack(fill="x", padx=20, pady=12)

    app.ai_nlp_res_lbl = tk.Label(
        app.ai_nlp_result_frame,
        text="🏷️ Suggested Category: Food   |   Confidence: High (94.5%)",
        font=theme.FONT_BODY_BOLD,
        fg=theme.INCOME,
        bg=theme.BG_MAIN,
        pady=8
    )
    app.ai_nlp_res_lbl.pack()

    return page


def set_and_predict_nlp(app, text):
    app.ai_nlp_input.delete(0, tk.END)
    app.ai_nlp_input.insert(0, text)
    test_nlp_playground(app)


def test_nlp_playground(app):
    text = app.ai_nlp_input.get().strip()
    if not text:
        return
    pred, conf = app.nlp_categorizer.predict(text)
    color = theme.INCOME if conf >= 70 else (theme.WARNING if conf >= 45 else theme.EXPENSE)
    conf_level = "High" if conf >= 70 else ("Moderate" if conf >= 45 else "Low")
    app.ai_nlp_res_lbl.config(
        text=f"🏷️ Suggested Category: {pred}   |   Match Confidence: {conf_level} ({conf:.1f}%)",
        fg=color
    )


def retrain_nlp_user(app):
    try:
        app.nlp_categorizer.train_on_history(app.tracker.db.get_connection())
        messagebox.showinfo("Categorizer Updated", "Smart Category Assistant successfully synchronized with your latest transaction records!")
        test_nlp_playground(app)
    except Exception as e:
        messagebox.showerror("Update Error", str(e))


def refresh_ai_insights(app):
    """Calculates all financial insights and renders fresh data into the view."""
    conn = app.tracker.db.get_connection()
    profile = getattr(app, 'current_portal', 'Personal')
    if profile not in ("Personal", "Business"):
        profile = "Personal"

    try:
        # 1. Monthly Spending Forecast
        fc = ml_engine.ExpenseForecaster.forecast_month_end(conn, profile=profile)
        
        # 2. Your Financial Profile & Health Score
        health = ml_engine.FinancialPersonaClusterer.analyze_health(conn, profile=profile)
        
        # 3. Unusual Spending Alerts
        anomalies = ml_engine.SpendingAnomalyDetector.detect_anomalies(conn, profile=profile)
        
        # 4. Savings Goal Planner
        goals_data = ml_engine.GoalFeasibilityEngine.evaluate_goals(conn, profile=profile)

        # Update Top KPI Cards
        app.ai_kpi_cards[0][1].config(text=f"{health['score']} / 100", fg=health['badge_color'])
        app.ai_kpi_cards[0][2].config(text=health['persona'])

        app.ai_kpi_cards[1][1].config(text=f"₹{fc['projected_total']:,.0f}")
        app.ai_kpi_cards[1][2].config(text=f"Status: {fc['runway_alert']}")

        app.ai_kpi_cards[2][1].config(text=f"{len(anomalies)} Alerts", fg=theme.WARNING if anomalies else theme.INCOME)
        app.ai_kpi_cards[2][2].config(text="Review flagged items" if anomalies else "Normal baseline")

        avg_feas = (sum(g['feasibility_pct'] for g in goals_data) / max(len(goals_data), 1)) if goals_data else 100.0
        app.ai_kpi_cards[3][1].config(text=f"{avg_feas:.1f} %")
        app.ai_kpi_cards[3][2].config(text=f"{len(goals_data)} Active Goals")

        # --- Render Forecast Card Content ---
        for w in app.ai_fc_content.winfo_children():
            w.destroy()

        fc_grid = tk.Frame(app.ai_fc_content, bg=theme.BG_CARD)
        fc_grid.pack(fill="x")
        fc_grid.columnconfigure(0, weight=1)
        fc_grid.columnconfigure(1, weight=1)

        def add_fc_row(parent, r, label, val, color=theme.TEXT_PRIMARY):
            tk.Label(parent, text=label, font=theme.FONT_BODY, fg=theme.TEXT_MUTED, bg=theme.BG_CARD).grid(row=r, column=0, sticky="w", pady=4)
            tk.Label(parent, text=val, font=theme.FONT_BODY_BOLD, fg=color, bg=theme.BG_CARD).grid(row=r, column=1, sticky="e", pady=4)

        add_fc_row(fc_grid, 0, "• Month Total Income:", f"₹{fc['total_income']:,.2f}", theme.INCOME)
        add_fc_row(fc_grid, 1, "• Current Spent So Far:", f"₹{fc['current_spent']:,.2f}", theme.EXPENSE)
        add_fc_row(fc_grid, 2, "• Estimated Month-End Spend:", f"₹{fc['projected_total']:,.2f}", theme.ACCENT)
        add_fc_row(fc_grid, 3, "• Daily Spending Pace:", f"₹{fc['daily_burn_rate']:,.2f} / day")
        add_fc_row(fc_grid, 4, "• Recommended Daily Budget:", f"₹{fc['recommended_daily']:,.2f} / day", theme.INCOME)
        
        status_color = theme.INCOME if fc['runway_alert'] == "Healthy Safe" else (theme.WARNING if fc['runway_alert'] == "Tight Margin" else theme.EXPENSE)
        add_fc_row(fc_grid, 5, "• Budget Runway Status:", f"● {fc['runway_alert']}", status_color)

        # --- Render Financial Profile Content ---
        for w in app.ai_persona_content.winfo_children():
            w.destroy()

        p_badge_frame = tk.Frame(app.ai_persona_content, bg=theme.BG_MAIN, padx=12, pady=8)
        p_badge_frame.pack(fill="x", pady=(0, 8))
        tk.Label(p_badge_frame, text=f"Profile: {health['persona']}", font=theme.FONT_BODY_BOLD, fg=health['badge_color'], bg=theme.BG_MAIN).pack(side="left")
        tk.Label(p_badge_frame, text=f"Health Score: {health['score']}/100", font=theme.FONT_BODY_BOLD, fg=theme.TEXT_PRIMARY, bg=theme.BG_MAIN).pack(side="right")

        # Clean Spending Breakdown (no 50/30/20 ratio text)
        r_frame = tk.Frame(app.ai_persona_content, bg=theme.BG_CARD)
        r_frame.pack(fill="x", pady=4)
        tk.Label(
            r_frame, 
            text=f"Spending Breakdown:  Essential Needs: {health['needs_ratio']:.1f}%  |  Discretionary: {health['wants_ratio']:.1f}%  |  Net Savings: {health['savings_rate']:.1f}%", 
            font=theme.FONT_SMALL, 
            fg=theme.TEXT_MUTED, 
            bg=theme.BG_CARD
        ).pack(anchor="w")

        # Actionable recommendations
        tk.Label(app.ai_persona_content, text="💡 Recommended Next Steps:", font=theme.FONT_BODY_BOLD, fg=theme.TEXT_PRIMARY, bg=theme.BG_CARD).pack(anchor="w", pady=(8, 2))
        for tip in health['tips'][:2]:
            tk.Label(app.ai_persona_content, text=f"→ {tip}", font=theme.FONT_SMALL, fg=theme.ACCENT, bg=theme.BG_CARD, wraplength=480, justify="left").pack(anchor="w", pady=2)

        # --- Render Unusual Spending Alerts Table ---
        for w in app.ai_anomaly_content.winfo_children():
            w.destroy()

        if not anomalies:
            tk.Label(
                app.ai_anomaly_content, 
                text="✅ All recent transactions look normal and match your typical spending habits.", 
                font=theme.FONT_BODY, 
                fg=theme.INCOME, 
                bg=theme.BG_CARD, 
                wraplength=480
            ).pack(pady=30)
        else:
            tree_frame = tk.Frame(app.ai_anomaly_content, bg=theme.BG_CARD)
            tree_frame.pack(fill="both", expand=True)

            cols = ("date", "category", "amount", "severity", "reason")
            tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=5)
            tree.heading("date", text="Date")
            tree.heading("category", text="Category")
            tree.heading("amount", text="Amount")
            tree.heading("severity", text="Alert Level")
            tree.heading("reason", text="Why It Was Flagged")

            tree.column("date", width=85, anchor="center")
            tree.column("category", width=95, anchor="center")
            tree.column("amount", width=85, anchor="e")
            tree.column("severity", width=85, anchor="center")
            tree.column("reason", width=220, anchor="w")

            for a in anomalies[:6]:
                tree.insert("", "end", values=(
                    a['date'],
                    a['category'],
                    f"₹{a['amount']:,.0f}",
                    a['severity'],
                    a['reason']
                ))
            tree.pack(fill="both", expand=True)

        # --- Render Goal Planner Content ---
        for w in app.ai_goals_content.winfo_children():
            w.destroy()

        if not goals_data:
            tk.Label(
                app.ai_goals_content, 
                text="No active savings goals found. Create goals in the '🎯 Saving Goals' tab to track them here.", 
                font=theme.FONT_BODY, 
                fg=theme.TEXT_MUTED, 
                bg=theme.BG_CARD
            ).pack(pady=30)
        else:
            for g in goals_data:
                g_card = tk.Frame(app.ai_goals_content, bg=theme.BG_MAIN, highlightbackground=theme.BORDER, highlightthickness=1, padx=12, pady=10)
                g_card.pack(fill="x", pady=6)

                h_box = tk.Frame(g_card, bg=theme.BG_MAIN)
                h_box.pack(fill="x")
                
                status_color = theme.INCOME if g['status'] == "On Track" else (theme.WARNING if g['status'] == "Minor Shortfall" else theme.EXPENSE)
                tk.Label(h_box, text=f"🎯 {g['name']}", font=theme.FONT_BODY_BOLD, fg=theme.TEXT_PRIMARY, bg=theme.BG_MAIN).pack(side="left")
                tk.Label(h_box, text=f"{g['feasibility_pct']:.0f}% On Schedule ({g['status']})", font=theme.FONT_BODY_BOLD, fg=status_color, bg=theme.BG_MAIN).pack(side="right")

                m_box = tk.Frame(g_card, bg=theme.BG_MAIN)
                m_box.pack(fill="x", pady=(4, 2))
                tk.Label(m_box, text=f"Target: ₹{g['target_amount']:,.0f}   |   Saved: ₹{g['current_savings']:,.0f}   |   Time Remaining: {g['days_left']} days", font=theme.FONT_SMALL, fg=theme.TEXT_MUTED, bg=theme.BG_MAIN).pack(side="left")

                # Actionable recommendation
                tk.Label(g_card, text=f"Suggested Action: {g['prescriptive_advice']}", font=theme.FONT_SMALL, fg=theme.ACCENT, bg=theme.BG_MAIN, wraplength=480, justify="left").pack(anchor="w", pady=(3, 0))

        # Initial test of Assistant
        test_nlp_playground(app)

    finally:
        conn.close()
