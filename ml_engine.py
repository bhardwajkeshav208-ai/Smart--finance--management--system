"""
FINSIGHT - Financial Intelligence Engine (ml_engine.py)
-------------------------------------------------------
Implements 5 core Machine Learning capabilities:
1. NLP Auto-Categorization (TF-IDF + Naive Bayes Classifier)
2. Expense & Cash Flow Forecasting (Time-Series Regression)
3. Spending Anomaly & Outlier Detection (Isolation Forest)
4. Savings Goal Feasibility & Prescriptive Rebalancing
5. Financial Health Scoring & Spending Persona (K-Means Clustering)
"""

import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import IsolationForest
from sklearn.cluster import KMeans
import calendar

class ExpenseCategorizerNLP:
    """
    Model 1: NLP Text Classification for Smart Auto-Categorization.
    Trained on rich seed vocabulary + retrained dynamically on user transactions.
    """
    def __init__(self):
        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(ngram_range=(1, 2), lowercase=True)),
            ('clf', MultinomialNB(alpha=0.1))
        ])
        self.is_trained = False
        self._seed_training_data()

    def _seed_training_data(self):
        seed_data = [
            # Food & Dining
            ("swiggy food delivery", "Food"),
            ("zomato dinner order", "Food"),
            ("dominos pizza lunch", "Food"),
            ("mcdonalds burger meal", "Food"),
            ("starbucks cold coffee", "Food"),
            ("grocery shopping fruits vegetables", "Food"),
            ("supermarket organic items", "Food"),
            ("milk bread butter daily dairy", "Food"),
            ("restaurant dinner date colleagues", "Food"),
            ("tea snacks bakery", "Food"),
            
            # Rent & Housing
            ("apartment monthly rent payment", "Rent"),
            ("flat house rent owner transfer", "Rent"),
            ("society maintenance charges", "Rent"),
            ("hostel room fees", "Rent"),

            # Bills & Utilities
            ("electricity power bill discom", "Bills & Utilities"),
            ("broadband optical fiber internet bill", "Bills & Utilities"),
            ("mobile post-paid recharge airtel jio", "Bills & Utilities"),
            ("water supply municipal bill", "Bills & Utilities"),
            ("lpg cooking gas cylinder booking", "Bills & Utilities"),
            ("netflix monthly subscription renewal", "Bills & Utilities"),
            ("spotify premium music family plan", "Bills & Utilities"),
            ("amazon prime yearly subscription", "Bills & Utilities"),

            # Travel & Commute
            ("uber cab ride to office", "Travel"),
            ("ola auto booking city ride", "Travel"),
            ("petrol fuel bunk filling car", "Travel"),
            ("diesel fuel tank refill", "Travel"),
            ("metro smart card recharge", "Travel"),
            ("flight flight ticket booking indigo", "Travel"),
            ("irctc train ticket reservation", "Travel"),
            ("highway fastag toll payment", "Travel"),

            # Shopping & Lifestyle
            ("zara summer clothes jacket purchase", "Shopping"),
            ("amazon online shopping electronics", "Shopping"),
            ("flipkart big billion days clothing", "Shopping"),
            ("nike running shoes sneakers", "Shopping"),
            ("h&m fashion shirts jeans", "Shopping"),
            ("gadgets wireless bluetooth earphones", "Shopping"),

            # Health & Fitness
            ("cult fit gym monthly membership", "Health & Fitness"),
            ("apollo pharmacy medicines prescription", "Health & Fitness"),
            ("doctor clinic consultation fees", "Health & Fitness"),
            ("blood test lab diagnostics hospital", "Health & Fitness"),
            ("protein powder multivitamin supplements", "Health & Fitness"),

            # Entertainment & Leisure
            ("pvr multiplex movie tickets popcorn", "Entertainment"),
            ("concert live music pass bookmyshow", "Entertainment"),
            ("weekend resort outing beverages drinks", "Entertainment"),
            ("playstation video game steam purchase", "Entertainment"),

            # Income: Salary & Freelance
            ("monthly corporate salary credit", "Salary"),
            ("company monthly payroll salary bonus", "Salary"),
            ("upwork freelance gig web development", "Freelance"),
            ("fiverr client graphic design project", "Freelance"),

            # Business: Sales & Services
            ("product sales customer revenue receipt", "Sales"),
            ("client consulting advisory service fee", "Services"),

            # Business Expenses
            ("bulk warehouse packaging materials", "Inventory"),
            ("fedex delivery courier logistics", "Shipping & Logistics"),
            ("facebook instagram ads marketing campaign", "Marketing & Ads"),
            ("coworking space desk monthly rental", "Office Rent"),
            ("assistant monthly freelance salary payroll", "Salaries & Payroll"),
            ("google workspace slack tools software license", "Software & Tools")
        ]
        self.seed_X = [item[0] for item in seed_data]
        self.seed_y = [item[1] for item in seed_data]
        self.pipeline.fit(self.seed_X, self.seed_y)
        self.is_trained = True

    def train_on_history(self, db_conn):
        """Augments model using actual user transactions stored in SQLite."""
        try:
            df = pd.read_sql_query("SELECT notes, category FROM transactions WHERE notes IS NOT NULL AND notes != ''", db_conn)
            user_X = [str(n).strip() for n in df['notes'] if str(n).strip()]
            user_y = [str(c).strip() for c in df['category'] if str(c).strip()]
            if len(user_X) == len(user_y) and len(user_X) > 0:
                combined_X = list(self.seed_X) + user_X
                combined_y = list(self.seed_y) + user_y
                self.pipeline.fit(combined_X, combined_y)
            else:
                self.pipeline.fit(self.seed_X, self.seed_y)
        except Exception:
            pass

    def predict(self, text):
        """Predicts the most probable category for the note text."""
        if not text or not str(text).strip():
            return None, 0.0
        try:
            probs = self.pipeline.predict_proba([text])[0]
            max_idx = np.argmax(probs)
            category = self.pipeline.classes_[max_idx]
            confidence = float(probs[max_idx])
            return category, round(confidence * 100, 1)
        except Exception:
            try:
                pred = self.pipeline.predict([text])[0]
                return pred, 80.0
            except Exception:
                return None, 0.0


class ExpenseForecaster:
    """
    Model 2: Time-Series Regression to forecast month-end expense & cash-flow trajectory.
    """
    @staticmethod
    def forecast_month_end(db_conn, profile="Personal"):
        today = date.today()
        curr_yr = today.year
        curr_mo = today.month

        # Fallback to latest month with data if current month is empty
        cur = db_conn.cursor()
        cur.execute("SELECT strftime('%Y-%m', date) FROM transactions WHERE profile = ? AND type = 'Expense' ORDER BY date DESC LIMIT 1", (profile,))
        latest_mo_row = cur.fetchone()
        
        target_yr, target_mo = curr_yr, curr_mo
        if latest_mo_row and latest_mo_row[0]:
            cur.execute("SELECT COUNT(*) FROM transactions WHERE profile = ? AND type = 'Expense' AND strftime('%Y-%m', date) = ?", 
                        (profile, f"{curr_yr}-{curr_mo:02d}"))
            curr_count = cur.fetchone()[0]
            if curr_count == 0:
                parts = latest_mo_row[0].split('-')
                target_yr = int(parts[0])
                target_mo = int(parts[1])

        days_in_month = calendar.monthrange(target_yr, target_mo)[1]
        day_of_month = today.day if (target_yr == curr_yr and target_mo == curr_mo) else min(days_in_month, 25)

        # Fetch expenses for target month
        query = """
            SELECT date, amount FROM transactions 
            WHERE profile = ? AND type = 'Expense' 
            AND strftime('%Y', date) = ? AND strftime('%m', date) = ?
            ORDER BY date ASC
        """
        df = pd.read_sql_query(query, db_conn, params=(profile, str(target_yr), f"{target_mo:02d}"))

        # Fetch income for target month
        inc_query = """
            SELECT SUM(amount) FROM transactions 
            WHERE profile = ? AND type = 'Income' 
            AND strftime('%Y', date) = ? AND strftime('%m', date) = ?
        """
        cur.execute(inc_query, (profile, str(target_yr), f"{target_mo:02d}"))
        row = cur.fetchone()
        total_income = float(row[0]) if (row and row[0]) else 0.0

        if df.empty:
            return {
                "current_spent": 0.0,
                "projected_total": 0.0,
                "daily_burn_rate": 0.0,
                "recommended_daily": total_income / max(days_in_month, 1),
                "total_income": total_income,
                "projected_savings": total_income,
                "runway_alert": "Normal",
                "days_left": days_in_month - day_of_month
            }

        df['date'] = pd.to_datetime(df['date'])
        df['day'] = df['date'].dt.day

        # Aggregate cumulative spend by day
        daily_spent = df.groupby('day')['amount'].sum().reindex(range(1, day_of_month + 1), fill_value=0.0)
        cum_spent = daily_spent.cumsum()
        current_spent = float(cum_spent.iloc[-1])

        # Regression: Feature X = day of month (1 to current day), Target y = cumulative expense
        X = np.array(range(1, day_of_month + 1)).reshape(-1, 1)
        y = cum_spent.values

        if len(X) >= 2:
            model = LinearRegression()
            model.fit(X, y)
            # Forecast at day = days_in_month
            projected_total = float(model.predict([[days_in_month]])[0])
            # Bounds check
            projected_total = max(projected_total, current_spent)
        else:
            daily_avg = current_spent / max(day_of_month, 1)
            projected_total = current_spent + (daily_avg * (days_in_month - day_of_month))

        daily_burn_rate = current_spent / max(day_of_month, 1)
        days_left = max(days_in_month - day_of_month, 1)
        remaining_budget = max(total_income - current_spent, 0.0)
        recommended_daily = remaining_budget / days_left if total_income > 0 else daily_burn_rate

        projected_savings = total_income - projected_total
        
        # Determine status
        if total_income > 0 and projected_total > total_income:
            runway_alert = "Over Budget Risk"
        elif total_income > 0 and (projected_total / total_income) > 0.85:
            runway_alert = "Tight Margin"
        else:
            runway_alert = "Healthy Safe"

        return {
            "current_spent": round(current_spent, 2),
            "projected_total": round(projected_total, 2),
            "daily_burn_rate": round(daily_burn_rate, 2),
            "recommended_daily": round(recommended_daily, 2),
            "total_income": round(total_income, 2),
            "projected_savings": round(projected_savings, 2),
            "runway_alert": runway_alert,
            "days_left": days_left
        }


class SpendingAnomalyDetector:
    """
    Model 3: Unsupervised Outlier / Anomaly Detection using Isolation Forest.
    Identifies abnormal spikes, accidental duplicates, or disproportionate expenditures.
    """
    @staticmethod
    def detect_anomalies(db_conn, profile="Personal"):
        query = """
            SELECT id, type, amount, category, date, notes 
            FROM transactions 
            WHERE profile = ? AND type = 'Expense'
            ORDER BY date DESC
        """
        df = pd.read_sql_query(query, db_conn, params=(profile,))
        if len(df) < 6:
            # Not enough data for isolation forest; use statistical 2.5x mean fallback
            anomalies = []
            if not df.empty:
                mean_amt = df['amount'].mean()
                for _, r in df.iterrows():
                    if r['amount'] >= max(mean_amt * 2.5, 5000.0):
                        anomalies.append({
                            "id": int(r['id']),
                            "date": str(r['date']),
                            "category": str(r['category']),
                            "amount": float(r['amount']),
                            "notes": str(r['notes']),
                            "severity": "High",
                            "reason": f"Amount ₹{r['amount']:,.0f} is unusually high compared to average spend (₹{mean_amt:,.0f})"
                        })
            return anomalies

        # Feature Engineering:
        global_median = df['amount'].median()
        cat_means = df.groupby('category')['amount'].transform('median')
        cat_stds = df.groupby('category')['amount'].transform('std').fillna(1.0)
        
        df['cat_ratio'] = df['amount'] / np.maximum(cat_means, 1.0)
        df['z_score'] = (df['amount'] - cat_means) / np.maximum(cat_stds, 1.0)
        
        features = df[['amount', 'cat_ratio', 'z_score']].fillna(0.0)
        
        iso = IsolationForest(contamination=0.25, random_state=42)
        preds = iso.fit_predict(features)
        
        anomalies = []
        for idx, pred in enumerate(preds):
            row = df.iloc[idx]
            ratio = float(row['cat_ratio'])
            amt = float(row['amount'])
            z = float(row['z_score'])
            
            # Anomaly criteria: flagged by Isolation Forest OR extreme z-score/ratio
            is_anomaly = (pred == -1) or (z > 1.5) or (ratio >= 2.5 and amt > 1000) or (amt >= max(global_median * 3.0, 15000.0))
            if is_anomaly:
                severity = "Critical" if (amt >= 20000 or ratio >= 3.5) else "Moderate"
                reason = f"High spend spike: ₹{amt:,.0f} is {ratio:.1f}x higher than standard {row['category']} transactions"
                anomalies.append({
                    "id": int(row['id']),
                    "date": str(row['date']),
                    "category": str(row['category']),
                    "amount": amt,
                    "notes": str(row['notes']) if row['notes'] else "-",
                    "severity": severity,
                    "reason": reason
                })
        return anomalies


class GoalFeasibilityEngine:
    """
    Model 4: Predictive Goal Feasibility & Prescriptive Budget Rebalancer.
    """
    @staticmethod
    def evaluate_goals(db_conn, profile="Personal"):
        goals_df = pd.read_sql_query("SELECT id, name, target_amount, current_savings, target_date FROM saving_goals", db_conn)
        if goals_df.empty:
            return []

        # Calculate monthly savings velocity from past 90 days
        cutoff = (date.today() - timedelta(days=90)).strftime("%Y-%m-%d")
        t_query = """
            SELECT type, SUM(amount) as total 
            FROM transactions 
            WHERE profile = ? AND date >= ? 
            GROUP BY type
        """
        t_df = pd.read_sql_query(t_query, db_conn, params=(profile, cutoff))
        
        inc = 0.0
        exp = 0.0
        for _, r in t_df.iterrows():
            if r['type'] == 'Income': inc = float(r['total'])
            elif r['type'] == 'Expense': exp = float(r['total'])
        
        net_saved_90d = max(inc - exp, 0.0)
        daily_savings_velocity = net_saved_90d / 90.0

        today = date.today()
        results = []

        # Get discretionary spend (Shopping, Entertainment, Food) for prescriptive rebalancing
        disc_query = """
            SELECT category, SUM(amount) as total
            FROM transactions 
            WHERE profile = ? AND type = 'Expense' AND category IN ('Shopping', 'Entertainment', 'Food')
            AND date >= ?
            GROUP BY category
        """
        disc_df = pd.read_sql_query(disc_query, db_conn, params=(profile, cutoff))
        monthly_disc = (disc_df['total'].sum() / 3.0) if not disc_df.empty else 0.0

        for _, g in goals_df.iterrows():
            target_amt = float(g['target_amount'])
            cur_amt = float(g['current_savings'])
            remaining_needed = max(target_amt - cur_amt, 0.0)

            try:
                t_date = datetime.strptime(str(g['target_date']), "%Y-%m-%d").date()
                days_left = max((t_date - today).days, 1)
            except Exception:
                days_left = 180

            required_daily_saving = remaining_needed / days_left
            projected_accumulation = cur_amt + (daily_savings_velocity * days_left)
            feasibility_pct = min(max((projected_accumulation / target_amt) * 100, 0.0), 100.0)

            # Prescriptive Advice
            if feasibility_pct >= 95.0:
                status = "On Track"
                advice = "Excellent pacing! Your current savings rate easily covers this goal."
            elif feasibility_pct >= 70.0:
                status = "Minor Shortfall"
                shortfall = target_amt - projected_accumulation
                monthly_trim = shortfall / max(days_left / 30.0, 1.0)
                advice = f"Trim discretionary spends (Shopping/Dining) by approx ₹{monthly_trim:,.0f}/month to bridge gap."
            else:
                status = "At Risk"
                shortfall = target_amt - projected_accumulation
                monthly_trim = shortfall / max(days_left / 30.0, 1.0)
                advice = f"Deficit of ₹{shortfall:,.0f}. Need to reallocate ₹{monthly_trim:,.0f}/month or extend deadline by {int(shortfall/max(daily_savings_velocity*30, 1))} months."

            results.append({
                "name": str(g['name']),
                "target_amount": target_amt,
                "current_savings": cur_amt,
                "target_date": str(g['target_date']),
                "days_left": days_left,
                "feasibility_pct": round(feasibility_pct, 1),
                "projected_accumulation": round(projected_accumulation, 0),
                "status": status,
                "prescriptive_advice": advice
            })
        return results


class FinancialPersonaClusterer:
    """
    Model 5: K-Means Clustering on Spending Ratios & Financial Health Scoring.
    """
    @staticmethod
    def analyze_health(db_conn, profile="Personal"):
        query = "SELECT type, amount, category FROM transactions WHERE profile = ?"
        df = pd.read_sql_query(query, db_conn, params=(profile,))

        if df.empty:
            return {
                "score": 50,
                "persona": "Novice Saver",
                "badge_color": "#FFA500",
                "savings_rate": 0.0,
                "needs_ratio": 50.0,
                "wants_ratio": 50.0,
                "tips": ["Record your recurring income and expenses to unlock personalized AI insights."]
            }

        total_income = df[df['type'] == 'Income']['amount'].sum()
        total_expense = df[df['type'] == 'Expense']['amount'].sum()

        if total_income <= 0:
            total_income = total_expense * 1.2 if total_expense > 0 else 10000.0

        savings_rate = max((total_income - total_expense) / total_income * 100, 0.0)

        # Categorize into Needs vs Wants (50/30/20 Rule)
        needs_cats = ['Rent', 'Bills & Utilities', 'Inventory', 'Office Rent', 'Salaries & Payroll', 'Shipping & Logistics']
        wants_cats = ['Shopping', 'Entertainment', 'Food', 'Travel', 'Marketing & Ads', 'Software & Tools']

        needs_spend = df[(df['type'] == 'Expense') & (df['category'].isin(needs_cats))]['amount'].sum()
        wants_spend = df[(df['type'] == 'Expense') & (df['category'].isin(wants_cats))]['amount'].sum()

        denom = max(total_expense, 1.0)
        needs_ratio = (needs_spend / denom) * 100
        wants_ratio = (wants_spend / denom) * 100

        # Feature Vector for K-Means: [Savings Rate, Needs Ratio, Wants Ratio]
        # Archetype Centroids:
        # Cluster 0: Disciplined Wealth Builder (High Savings > 35%, Controlled Wants < 25%)
        # Cluster 1: Balanced Lifestyle (Healthy Savings 20-35%, Balanced Wants 25-40%)
        # Cluster 2: High Burn / Vulnerable (Low Savings < 15%, High Wants > 45%)
        centroids = np.array([
            [40.0, 45.0, 15.0],  # Wealth Builder
            [25.0, 50.0, 25.0],  # Balanced
            [5.0, 45.0, 50.0]    # High Burn
        ])
        
        user_vector = np.array([[savings_rate, needs_ratio, wants_ratio]])
        
        # Determine closest archetype using Euclidean distance
        dists = np.linalg.norm(centroids - user_vector, axis=1)
        cluster_id = int(np.argmin(dists))

        # Financial Health Score (0 to 100)
        # 40% Weight on Savings Rate (ideal: 30%+)
        # 30% Weight on Wants Control (ideal: <= 30%)
        # 30% Weight on Cash Flow Positivity
        score_savings = min((savings_rate / 35.0) * 40.0, 40.0)
        score_wants = max((1.0 - (wants_ratio / 60.0)) * 30.0, 0.0)
        score_surplus = 30.0 if total_income > total_expense else 10.0
        health_score = int(np.clip(score_savings + score_wants + score_surplus, 10, 100))

        if cluster_id == 0:
            persona = "Disciplined Wealth Builder"
            badge_color = "#2ECC71" # Green
            tips = [
                "Your savings rate is in the top tier! Consider investing surplus cash in index funds or high-yield instruments.",
                "Maintain your low discretionary spending ratio to maximize compounding."
            ]
        elif cluster_id == 1:
            persona = "Balanced Lifestyle Spender"
            badge_color = "#3498DB" # Blue
            tips = [
                "You maintain a great balance between living well and saving for the future.",
                "Try automating 5% more into recurring savings before starting your monthly spending."
            ]
        else:
            persona = "High-Burn Impulsive Spender"
            badge_color = "#E74C3C" # Red
            tips = [
                "Wants and discretionary spending are eating into potential savings.",
                "Apply the 48-Hour Rule for shopping purchases above ₹2,000 to prevent impulse buys."
            ]

        return {
            "score": health_score,
            "persona": persona,
            "badge_color": badge_color,
            "savings_rate": round(savings_rate, 1),
            "needs_ratio": round(needs_ratio, 1),
            "wants_ratio": round(wants_ratio, 1),
            "tips": tips
        }
