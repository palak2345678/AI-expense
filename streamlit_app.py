"""
Streamlit Web Application for AI Expense Audit & Fraud Detection Platform
Academic Course: Soft Computing (CSE / AIML, Semester V)
Authors: Palak Hajare (24070521237) & Pratham Khetan
Institution: Symbiosis Institute of Technology (SIT Nagpur)
"""

import os
import sys
import json
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime

# Set page configuration
st.set_page_config(
    page_title="AuditAI — Soft Computing Expense Fraud Detection",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from models.fuzzy_engine import SoftComputingFuzzyEngine
from models.audit_rules import ExpenseAuditRuleEngine
from models.anomaly_detector import ExpenseAnomalyDetector
from models.hybrid_evaluator import HybridExpenseFraudEvaluator
from backend.database import (
    seed_database_if_empty,
    get_all_expenses,
    insert_expense,
    get_dashboard_stats,
    get_monthly_stats,
    get_category_stats,
    get_alerts
)

# Custom Styling (Dark Glassmorphic UI matching original theme)
st.markdown("""
<style>
    .main { background-color: #0b0f19; }
    .stMetric {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 12px 18px;
    }
    .badge-high { color: #f43f5e; font-weight: bold; }
    .badge-medium { color: #f59e0b; font-weight: bold; }
    .badge-low { color: #10b981; font-weight: bold; }
    .reason-box {
        background: rgba(255, 255, 255, 0.03);
        border-left: 4px solid #3b82f6;
        padding: 10px 14px;
        border-radius: 4px;
        margin-bottom: 6px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize database
seed_database_if_empty()

@st.cache_resource
def load_evaluator():
    ev = HybridExpenseFraudEvaluator()
    history = get_all_expenses()
    ev.fit_anomaly_detector(history)
    return ev

evaluator = load_evaluator()

# Sidebar Navigation
st.sidebar.markdown("""
<div style='display: flex; align-items: center; gap: 10px; margin-bottom: 14px;'>
    <h2 style='margin:0; color:#38bdf8;'>🛡️ Audit<span style='color:#f43f5e;'>AI</span></h2>
</div>
<small style='color: #94a3b8;'>Soft Computing & ML Fraud Platform<br>SIT Nagpur · Sem V</small>
""", unsafe_allow_html=True)

page = st.sidebar.radio(
    "Navigation Menu",
    [
        "📊 Executive Audit Dashboard",
        "⚡ Submit Expense for AI Audit",
        "🧠 Soft Computing & Fuzzy Visualizer",
        "📈 Model Benchmark & Evaluation",
        "📖 Viva Q&A & Architecture"
    ]
)

st.sidebar.markdown("---")
st.sidebar.caption("👨‍🎓 **Palak Hajare (24070521237)** & Pratham Khetan")
st.sidebar.caption("Group: **NeuroX** · Symbiosis University")


# =========================================================================
# Page 1: Executive Audit Dashboard
# =========================================================================
if page == "📊 Executive Audit Dashboard":
    st.title("📊 Executive Expense Auditing & Governance Dashboard")
    st.markdown("Real-time telemetry, transaction surveillance, and autonomous fraud risk categorization.")

    stats = get_dashboard_stats()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Audited Claims", f"{stats['totalExpenses']:,}")
    col2.metric("Audited Volume", f"${stats['totalAmount']:,.2f}")
    col3.metric("Flagged At-Risk", f"{stats['flaggedCount']}", delta="High/Med Risk", delta_color="inverse")
    col4.metric("Losses Prevented", f"${stats['moneySaved']:,.2f}", delta="Recovered", delta_color="normal")
    col5.metric("System Risk Index", f"{stats['avgRiskScore']}/100")

    st.markdown("---")

    # Interactive Charts
    monthly_data = get_monthly_stats()
    cat_data = get_category_stats()

    c1, c2 = st.columns([3, 2])
    with c1:
        st.subheader("Expenditure Trajectory vs Flagged Losses")
        df_monthly = pd.DataFrame(monthly_data["items"])
        if not df_monthly.empty:
            fig_line = go.Figure()
            fig_line.add_trace(go.Scatter(x=df_monthly["month"], y=df_monthly["total"], mode="lines+markers", name="Total Spend ($)", line=dict(color="#38bdf8", width=3)))
            fig_line.add_trace(go.Bar(x=df_monthly["month"], y=df_monthly["flagged"], name="Flagged Losses ($)", marker_color="rgba(244, 63, 94, 0.7)"))
            fig_line.update_layout(template="plotly_dark", height=320, margin=dict(l=20, r=20, t=30, b=20), legend=dict(orientation="h", yanchor="bottom", y=1.02))
            st.plotly_chart(fig_line, use_container_width=True)

    with c2:
        st.subheader("Category Volume Allocation")
        if cat_data["labels"]:
            fig_pie = px.pie(
                names=cat_data["labels"],
                values=cat_data["totals"],
                hole=0.45,
                color_discrete_sequence=px.colors.sequential.Tealgrn
            )
            fig_pie.update_layout(template="plotly_dark", height=320, margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig_pie, use_container_width=True)

    # Audited Transactions Table
    st.subheader("Corporate Audited Transactions")
    fcol1, fcol2, fcol3 = st.columns([1, 1, 2])
    with fcol1:
        cat_filter = st.selectbox("Filter Category", ["all", "Meals & Entertainment", "Travel", "Equipment", "Software & IT", "Office Supplies", "Consulting"])
    with fcol2:
        risk_filter = st.selectbox("Filter Risk", ["all", "High", "Medium", "Low"])
    with fcol3:
        search_query = st.text_input("Search Employee, ID, or Description", "")

    expenses = get_all_expenses(category=cat_filter, risk=risk_filter, search=search_query)
    
    if expenses:
        df_table = pd.DataFrame(expenses)[["id", "employee", "department", "category", "amount", "date", "riskScore", "riskLevel", "status"]]
        st.dataframe(
            df_table.rename(columns={
                "id": "ID", "employee": "Employee", "department": "Department",
                "category": "Category", "amount": "Amount ($)", "date": "Date",
                "riskScore": "Risk", "riskLevel": "Level", "status": "Status"
            }),
            use_container_width=True,
            height=300
        )
    else:
        st.info("No matching records found.")


# =========================================================================
# Page 2: Submit Expense for AI Audit
# =========================================================================
elif page == "⚡ Submit Expense for AI Audit":
    st.title("⚡ Real-Time Expense Submission & AI Audit")
    st.markdown("Submit an expense to invoke the **Mamdani Fuzzy Logic Engine**, **Isolation Forest ML**, and **Policy Rules** simultaneously.")

    # Quick Presets
    st.markdown("**Quick Test Scenarios:**")
    pcol1, pcol2, pcol3, pcol4 = st.columns(4)
    preset_data = None
    if pcol1.button("✅ Clean Claim ($145)"):
        preset_data = {"emp": "Sarah Jenkins", "dept": "Engineering", "cat": "Meals & Entertainment", "amt": 145.50, "desc": "Team celebration lunch with itemized receipt", "rcpt": True, "hash": "RCPT-CLEAN-1049"}
    if pcol2.button("⚠️ Duplicate Claim ($3.2k)"):
        preset_data = {"emp": "Alex Rivera", "dept": "Sales", "cat": "Meals & Entertainment", "amt": 3200.00, "desc": "VIP Client dinner & lounge reservation", "rcpt": True, "hash": "HASH-9999-DUPLICATE"}
    if pcol3.button("🚨 High-Value ($16.5k)"):
        preset_data = {"emp": "Marcus Vance", "dept": "Executive", "cat": "Equipment", "amt": 16500.00, "desc": "Executive portable workstation setup", "rcpt": False, "hash": "NO_RECEIPT"}
    if pcol4.button("🌙 Off-Hours 2 AM ($5k)"):
        preset_data = {"emp": "David Chen", "dept": "Consulting", "cat": "Consulting", "amt": 5000.00, "desc": "Emergency offshore architectural consulting advisory", "rcpt": True, "hash": "RCPT-OFFSHORE-921"}

    with st.form("expense_form"):
        r1_col1, r1_col2 = st.columns(2)
        with r1_col1:
            emp = st.text_input("Employee Name *", value=preset_data["emp"] if preset_data else "Alex Rivera")
            dept = st.selectbox("Department *", ["Engineering", "Sales", "Marketing", "Finance", "Executive", "Operations", "Human Resources"], index=1 if not preset_data else ["Engineering", "Sales", "Marketing", "Finance", "Executive", "Operations", "Human Resources"].index(preset_data["dept"]))
            cat = st.selectbox("Expense Category *", ["Meals & Entertainment", "Travel", "Equipment", "Software & IT", "Office Supplies", "Consulting"], index=0 if not preset_data else ["Meals & Entertainment", "Travel", "Equipment", "Software & IT", "Office Supplies", "Consulting"].index(preset_data["cat"]))
        
        with r1_col2:
            amt = st.number_input("Amount (USD $) *", min_value=0.01, max_value=100000.0, value=preset_data["amt"] if preset_data else 320.0, step=10.0)
            exp_date = st.date_input("Expense Date *", value=datetime.today())
            exp_time = st.time_input("Submission Time *", value=datetime.strptime("14:30", "%H:%M").time())

        desc = st.text_area("Description & Business Justification *", value=preset_data["desc"] if preset_data else "Quarterly vendor collaboration dinner")

        r3_col1, r3_col2 = st.columns(2)
        with r3_col1:
            has_rcpt = st.checkbox("Receipt Documentation Attached", value=preset_data["rcpt"] if preset_data else True)
        with r3_col2:
            rcpt_hash = st.text_input("Receipt Hash / ID", value=preset_data["hash"] if preset_data else "RCPT-AUTO-2918")

        submit = st.form_submit_button("🚀 Run AI Fraud Audit", use_container_width=True)

    if submit:
        all_current = get_all_expenses()
        existing_ids = [int(e["id"].replace("EXP-", "")) for e in all_current if "EXP-" in e["id"] and e["id"].replace("EXP-", "").isdigit()]
        next_num = (max(existing_ids) + 1) if existing_ids else 1001
        exp_id = f"EXP-{next_num}"

        date_str = exp_date.strftime("%Y-%m-%d")
        time_str = exp_time.strftime("%H:%M")

        payload = {
            "id": exp_id,
            "employee": emp.strip(),
            "department": dept,
            "category": cat,
            "amount": float(amt),
            "date": date_str,
            "time": time_str,
            "description": desc.strip(),
            "has_receipt": has_rcpt,
            "receipt_hash": rcpt_hash.strip()
        }

        # Evaluate through Hybrid Soft Computing Engine
        with st.spinner("Executing Mamdani Fuzzy Inference & Isolation Forest..."):
            res = evaluator.evaluate(payload, historical_expenses=all_current)

        # Store in SQLite
        record = {
            **payload,
            "status": res["status"],
            "riskScore": res["risk_score"],
            "riskLevel": res["risk_level"],
            "fuzzy_score": res["sub_scores"]["fuzzy_risk_score"],
            "anomaly_score": res["sub_scores"]["anomaly_risk_score"],
            "rule_score": res["sub_scores"]["rule_risk_score"],
            "reasons": res["reasons"],
            "nextAction": res["next_action"],
            "createdAt": datetime.utcnow().isoformat() + "Z"
        }
        insert_expense(record)

        # Render Results
        st.markdown("---")
        st.subheader("🎯 Audit Result & Risk Assessment")

        res_col1, res_col2 = st.columns([1, 2])
        with res_col1:
            score = res["final_risk_score"]
            level = res["risk_level"]
            color = "#f43f5e" if level == "High" else "#f59e0b" if level == "Medium" else "#10b981"
            
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=score,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': f"Risk Score: {level.upper()}", 'font': {'color': color, 'size': 20}},
                gauge={
                    'axis': {'range': [0, 100], 'tickcolor': "#fff"},
                    'bar': {'color': color},
                    'steps': [
                        {'range': [0, 35], 'color': "rgba(16, 185, 129, 0.2)"},
                        {'range': [35, 65], 'color': "rgba(245, 158, 11, 0.2)"},
                        {'range': [65, 100], 'color': "rgba(244, 63, 94, 0.2)"}
                    ]
                }
            ))
            fig_gauge.update_layout(template="plotly_dark", height=240, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig_gauge, use_container_width=True)

        with res_col2:
            st.markdown(f"**Transaction ID:** `{exp_id}` · **Status:** `{res['status'].upper()}`")
            st.markdown(f"**Recommended Action:** `{res['next_action']}`")
            
            # Sub-scores strip
            sc_c1, sc_c2, sc_c3 = st.columns(3)
            sc_c1.metric("🧠 Fuzzy Risk", f"{res['sub_scores']['fuzzy_risk_score']:.1f}%")
            sc_c2.metric("🔬 ML Anomaly", f"{res['sub_scores']['anomaly_risk_score']:.1f}%")
            sc_c3.metric("⚖️ Rule Breaches", f"{res['sub_scores']['rule_risk_score']:.1f}%")

            st.markdown("**Itemized Findings & Violations:**")
            for r in res["reasons"]:
                st.markdown(f"<div class='reason-box'>⚠️ {r}</div>", unsafe_allow_html=True)


# =========================================================================
# Page 3: Soft Computing & Fuzzy Visualizer
# =========================================================================
elif page == "🧠 Soft Computing & Fuzzy Visualizer":
    st.title("🧠 Soft Computing — Mamdani Fuzzy Inference System")
    st.markdown("Visualizing universe of discourse, membership functions, and linguistic fuzzy inference.")

    engine = SoftComputingFuzzyEngine()

    tab1, tab2, tab3 = st.tabs(["📐 Membership Functions", "📋 12 Mamdani IF-THEN Rules", "⚙️ Defuzzification Mechanics"])

    with tab1:
        st.subheader("Input Linguistic Membership Functions")
        
        # Plot Amount Ratio Membership Functions
        x_amt = np.linspace(0, 5, 200)
        from models.fuzzy_engine import trapmf, trimf
        y_low = trapmf(x_amt, [0.0, 0.0, 0.6, 1.0])
        y_med = trimf(x_amt, [0.8, 1.25, 2.0])
        y_high = trimf(x_amt, [1.6, 2.8, 4.0])
        y_vhigh = trapmf(x_amt, [3.2, 5.0, 10.0, 10.0])

        fig_mf = go.Figure()
        fig_mf.add_trace(go.Scatter(x=x_amt, y=y_low, name="Low (<= 1.0x)", line=dict(color="#10b981", width=2.5)))
        fig_mf.add_trace(go.Scatter(x=x_amt, y=y_med, name="Medium (1.25x)", line=dict(color="#f59e0b", width=2.5)))
        fig_mf.add_trace(go.Scatter(x=x_amt, y=y_high, name="High (2.8x)", line=dict(color="#f43f5e", width=2.5)))
        fig_mf.add_trace(go.Scatter(x=x_amt, y=y_vhigh, name="Very High (> 3.5x)", line=dict(color="#a855f7", width=2.5)))
        fig_mf.update_layout(
            title="Amount Ratio Universe of Discourse: Amount / Policy Limit",
            xaxis_title="Amount-to-Limit Ratio",
            yaxis_title="Degree of Membership μ(x)",
            template="plotly_dark",
            height=340
        )
        st.plotly_chart(fig_mf, use_container_width=True)

    with tab2:
        st.subheader("12 Formal Mamdani Fuzzy Rules")
        rules_data = [
            ("R1", "IF Amount is LOW AND Receipt is LOW AND Temporal is LOW", "Risk is LOW"),
            ("R2", "IF Amount is LOW AND Temporal is MEDIUM", "Risk is LOW"),
            ("R3", "IF Amount is MEDIUM AND Receipt is LOW AND Temporal is LOW", "Risk is LOW"),
            ("R4", "IF Amount is MEDIUM AND Receipt is MEDIUM", "Risk is MEDIUM"),
            ("R5", "IF Amount is MEDIUM AND Temporal is HIGH", "Risk is MEDIUM"),
            ("R6", "IF Deviation is MODERATE AND Receipt is LOW", "Risk is MEDIUM"),
            ("R7", "IF Amount is HIGH AND Receipt is LOW", "Risk is MEDIUM"),
            ("R8", "IF Receipt is HIGH AND Amount is LOW (Missing receipt small item)", "Risk is MEDIUM"),
            ("R9", "IF Amount is HIGH AND Temporal is HIGH (Large off-hours)", "Risk is HIGH"),
            ("R10", "IF Amount is HIGH AND Receipt is HIGH (Large missing receipt)", "Risk is HIGH"),
            ("R11", "IF Amount is VERY_HIGH (Extreme Outlier)", "Risk is HIGH"),
            ("R12", "IF Deviation is EXTREME AND Temporal is HIGH", "Risk is HIGH")
        ]
        df_rules = pd.DataFrame(rules_data, columns=["Rule ID", "Antecedent (IF)", "Consequent (THEN)"])
        st.table(df_rules)

    with tab3:
        st.subheader("Centroid Defuzzification Formula")
        st.latex(r"COG = \frac{\sum_{i=1}^{N} y_i \cdot \mu_{agg}(y_i)}{\sum_{i=1}^{N} \mu_{agg}(y_i)}")
        st.markdown("""
        - **Antecedent Evaluation**: $T(a, b) = \min(a, b)$ (Mamdani Min operator)
        - **Implication**: Clips output fuzzy sets at rule firing strength $\mu_{C'}(y) = \min(\alpha_i, \mu_C(y))$
        - **Aggregation**: Combines clipped sets via $S(a, b) = \max(a, b)$
        - **Defuzzification**: Center of Gravity (COG) converts continuous distribution into crisp risk score $[0, 100]$.
        """)


# =========================================================================
# Page 4: Model Benchmark & Evaluation
# =========================================================================
elif page == "📈 Model Benchmark & Evaluation":
    st.title("📈 Model Evaluation Benchmark & Performance Metrics")
    st.markdown("Rigorous evaluation on stratified 70/30 holdout split from `dataset/synthetic_expenses.csv` (zero data leakage).")

    benchmark_data = [
        {"Model Component": "Soft Computing Fuzzy Logic", "Accuracy": "89.74%", "Precision": "58.33%", "Recall": "80.77%", "F1-Score": "67.74%"},
        {"Model Component": "Deterministic Audit Rules", "Accuracy": "89.74%", "Precision": "63.64%", "Recall": "53.85%", "F1-Score": "58.33%"},
        {"Model Component": "ML Isolation Forest Anomaly", "Accuracy": "96.92%", "Precision": "88.46%", "Recall": "88.46%", "F1-Score": "88.46%"},
        {"Model Component": "Hybrid Synthesized Platform", "Accuracy": "91.28%", "Precision": "69.57%", "Recall": "61.54%", "F1-Score": "65.31%"}
    ]
    st.table(pd.DataFrame(benchmark_data))

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Hybrid Platform Confusion Matrix")
        cm_data = [[162, 7], [10, 16]]
        fig_cm = px.imshow(
            cm_data,
            labels=dict(x="Predicted Class", y="Actual Class", color="Count"),
            x=["Legitimate (0)", "Fraud (1)"],
            y=["Legitimate (0)", "Fraud (1)"],
            text_auto=True,
            color_continuous_scale="Blues"
        )
        fig_cm.update_layout(template="plotly_dark", height=280)
        st.plotly_chart(fig_cm, use_container_width=True)

    with c2:
        st.subheader("Detection Metrics Comparison")
        df_chart = pd.DataFrame([
            {"Model": "Fuzzy Logic", "F1": 67.74, "Recall": 80.77},
            {"Model": "Audit Rules", "F1": 58.33, "Recall": 53.85},
            {"Model": "Isolation Forest", "F1": 88.46, "Recall": 88.46},
            {"Model": "Hybrid Platform", "F1": 65.31, "Recall": 61.54}
        ])
        fig_bar = px.bar(df_chart, x="Model", y=["Recall", "F1"], barmode="group", color_discrete_sequence=["#38bdf8", "#f43f5e"])
        fig_bar.update_layout(template="plotly_dark", height=280)
        st.plotly_chart(fig_bar, use_container_width=True)


# =========================================================================
# Page 5: Viva Q&A & Architecture
# =========================================================================
elif page == "📖 Viva Q&A & Architecture":
    st.title("📖 Academic Viva & Soft Computing Preparation")
    
    with st.expander("Q1: Why is this considered Soft Computing rather than Hard Computing?", expanded=True):
        st.markdown("**Answer:** Hard Computing requires exact mathematical formulations and binary Boolean truth values (0 or 1). In expense auditing, fraud indicators are imprecise and uncertain (e.g. 'moderately excessive amount', 'unusual timing'). Soft Computing uses Mamdani Fuzzy Sets to handle gradations of truth and human-like reasoning.")

    with st.expander("Q2: Why Mamdani Fuzzy Inference over Sugeno (TSK)?"):
        st.markdown("**Answer:** Mamdani inference uses fuzzy linguistic sets for both inputs and outputs (Low, Medium, High), making audit decisions explainable and justifiable to corporate auditors. Sugeno uses polynomial outputs suitable for control systems, which lacks interpretability for human compliance auditing.")

    with st.expander("Q3: How does defuzzification work in your system?"):
        st.markdown("**Answer:** We use Center of Gravity (Centroid / COG):")
        st.latex(r"COG = \frac{\int y \cdot \mu_{agg}(y) \, dy}{\int \mu_{agg}(y) \, dy}")
        st.markdown("It calculates the balance point under the clipped aggregated output curve, producing a continuous crisp risk score in [0, 100].")

    with st.expander("Q4: How does your Genetic Algorithm optimize rule weights?"):
        st.markdown("**Answer:** The GA represents the 12 rule weights as a real-valued chromosome. It evaluates population fitness using F1-score against historical ground truth, evolving weights through tournament selection, uniform crossover, and Gaussian mutation.")

    with st.expander("Q5: How does the system prevent false fraud accusations when a receipt is missing?"):
        st.markdown("**Answer:** Under Rule 8 (IF Receipt is HIGH AND Amount is LOW -> Risk is MEDIUM), a missing receipt on an inexpensive item (e.g. $25 coffee or taxi) only produces moderate caution (Medium risk), requesting a receipt re-upload rather than triggering an outright fraud rejection.")
