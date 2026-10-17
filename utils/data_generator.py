"""
Synthetic Expense Dataset Generator for Soft Computing Audit & Fraud Detection
Academic Course: Soft Computing (CSE / AIML)

Generates a realistic corporate expense dataset with:
- Normal lognormal expense distribution across standard corporate categories
- 6 deliberately engineered fraud scenarios representing common real-world expense schemes
- Clear synthetic provenance metadata (never masquerading as real corporate data)
- Clean feature separation ensuring zero data leakage for ML evaluation
"""

import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List


# Departmental and Categorical Baseline Limits (in USD)
DEPARTMENT_LIMITS: Dict[str, Dict[str, float]] = {
    "Engineering": {"Meals & Entertainment": 120.0, "Travel": 1000.0, "Equipment": 2500.0, "Software & IT": 1500.0, "Office Supplies": 200.0, "Consulting": 1000.0},
    "Sales": {"Meals & Entertainment": 300.0, "Travel": 2000.0, "Equipment": 1500.0, "Software & IT": 600.0, "Office Supplies": 250.0, "Consulting": 1500.0},
    "Marketing": {"Meals & Entertainment": 250.0, "Travel": 1500.0, "Equipment": 2000.0, "Software & IT": 1200.0, "Office Supplies": 400.0, "Consulting": 2500.0},
    "Finance": {"Meals & Entertainment": 100.0, "Travel": 800.0, "Equipment": 1200.0, "Software & IT": 1000.0, "Office Supplies": 300.0, "Consulting": 3000.0},
    "Executive": {"Meals & Entertainment": 500.0, "Travel": 3500.0, "Equipment": 4000.0, "Software & IT": 2000.0, "Office Supplies": 500.0, "Consulting": 5000.0},
    "Operations": {"Meals & Entertainment": 100.0, "Travel": 1000.0, "Equipment": 3000.0, "Software & IT": 800.0, "Office Supplies": 600.0, "Consulting": 1200.0},
    "Human Resources": {"Meals & Entertainment": 150.0, "Travel": 900.0, "Equipment": 1000.0, "Software & IT": 800.0, "Office Supplies": 400.0, "Consulting": 1500.0}
}

CATEGORY_MEANS: Dict[str, float] = {
    "Meals & Entertainment": 75.0,
    "Travel": 750.0,
    "Equipment": 1200.0,
    "Software & IT": 350.0,
    "Office Supplies": 95.0,
    "Consulting": 1800.0
}

EMPLOYEE_POOL = [
    ("Sarah Jenkins", "Engineering"),
    ("Alex Rivera", "Sales"),
    ("Marcus Vance", "Executive"),
    ("Elena Rostova", "Finance"),
    ("David Chen", "Consulting"),
    ("Priya Sharma", "Marketing"),
    ("Michael Scott", "Operations"),
    ("Rachel Green", "Human Resources"),
    ("James Wilson", "Engineering"),
    ("Sophia Martinez", "Sales"),
    ("Daniel Lee", "Finance"),
    ("Aaliyah Khan", "Marketing"),
    ("Thomas Anderson", "Engineering"),
    ("Chloe Bennet", "Operations")
]


def generate_synthetic_dataset(n_samples: int = 650, random_seed: int = 42) -> pd.DataFrame:
    """
    Generates synthetic corporate expense dataset.
    """
    random.seed(random_seed)
    np.random.seed(random_seed)

    start_date = datetime(2026, 5, 1)
    records: List[Dict[str, Any]] = []

    categories = list(CATEGORY_MEANS.keys())

    for i in range(1, n_samples + 1):
        emp_name, default_dept = random.choice(EMPLOYEE_POOL)
        category = random.choice(categories)
        cat_mean = CATEGORY_MEANS[category]

        dept_limits = DEPARTMENT_LIMITS.get(default_dept, DEPARTMENT_LIMITS["Engineering"])
        policy_limit = dept_limits.get(category, cat_mean * 1.5)

        # Base normal amount sampled from lognormal distribution
        # mean of underlying lognormal = log(cat_mean) - (sigma^2)/2
        sigma = 0.45
        mu = np.log(cat_mean * 0.75)
        amount = round(float(np.random.lognormal(mean=mu, sigma=sigma)), 2)
        amount = max(12.50, amount)

        # Date & Time
        day_offset = random.randint(0, 165)
        exp_date = start_date + timedelta(days=day_offset)
        date_str = exp_date.strftime("%Y-%m-%d")
        day_of_week = exp_date.strftime("%A")
        is_weekend = 1 if exp_date.weekday() >= 5 else 0

        # Normal business hours: 09:00 - 18:00
        hour = random.randint(9, 18)
        minute = random.choice([0, 15, 30, 45, random.randint(1, 59)])
        time_str = f"{hour:02d}:{minute:02d}"

        has_receipt = 1 if random.random() > 0.08 else 0
        receipt_hash = f"RCPT-{random.randint(100000, 999999)}" if has_receipt else "NO_RECEIPT"

        descriptions = {
            "Meals & Entertainment": [
                "Lunch with prospective enterprise client",
                "Team milestone celebration lunch",
                "Working dinner during sprint release",
                "Quarterly departmental dinner"
            ],
            "Travel": [
                "Roundtrip flight to regional branch office",
                "Conference lodging and ground transit",
                "Client on-site consulting travel expense",
                "Airport rideshare and lodging"
            ],
            "Equipment": [
                "High-performance developer monitor & peripheral dock",
                "Replacement ergonomic workstation seating",
                "Lab hardware prototyping components",
                "Departmental server rack accessories"
            ],
            "Software & IT": [
                "Monthly cloud container hosting subscription",
                "Developer IDE enterprise team licenses",
                "Security vulnerability scanning SaaS tool",
                "Database performance monitoring toolkit"
            ],
            "Office Supplies": [
                "Whiteboard pens, notebooks and presentation folders",
                "Printer toner cartridges and high-grade printing stock",
                "Shipping and courier supplies for branch mailings",
                "Desk organizational fixtures"
            ],
            "Consulting": [
                "Third-party regulatory compliance audit review",
                "Cloud architectural security advisory hours",
                "Legal advisory on contract IP clauses",
                "Brand positioning strategic consultation"
            ]
        }
        description = random.choice(descriptions[category])

        is_fraud = 0
        fraud_type = "Legitimate"

        # -------------------------------------------------------------
        # Inject realistic fraud patterns (~14% total fraud rate)
        # -------------------------------------------------------------
        roll = random.random()

        if roll < 0.025:
            # Pattern 1: Split Invoicing ($480 - $499.99)
            amount = round(random.uniform(482.00, 499.50), 2)
            category = "Office Supplies"
            policy_limit = dept_limits.get(category, 300.0)
            is_fraud = 1
            fraud_type = "Threshold Split Invoicing"
            description = "Subdivided bulk departmental supply batch"

        elif roll < 0.050:
            # Pattern 2: Weekend Luxury / Personal Entertainment
            amount = round(random.uniform(950.00, 3200.00), 2)
            category = "Meals & Entertainment"
            is_weekend = 1
            hour = random.choice([22, 23, 0, 1, 2])
            time_str = f"{hour:02d}:{random.randint(0, 59):02d}"
            is_fraud = 1
            fraud_type = "Unauthorized Weekend Luxury"
            description = "Late night executive lounge and premium hospitality"

        elif roll < 0.075:
            # Pattern 3: Excessive Policy Outlier
            multiplier = random.uniform(3.5, 7.0)
            amount = round(policy_limit * multiplier, 2)
            is_fraud = 1
            fraud_type = "Policy Limit Breach"
            description = "Unapproved premium expedited procurement"

        elif roll < 0.100:
            # Pattern 4: Ghost Expense (High-Value, No Receipt)
            amount = round(random.uniform(650.00, 2200.00), 2)
            has_receipt = 0
            receipt_hash = "NO_RECEIPT"
            is_fraud = 1
            fraud_type = "Missing Receipt High Value"
            description = "Miscellaneous field operations expense (lost physical invoice)"

        elif roll < 0.125:
            # Pattern 5: Duplicate Receipt Claim
            receipt_hash = "HASH-9999-DUPLICATE"
            is_fraud = 1
            fraud_type = "Duplicate Receipt Submission"
            description = "Re-submitted travel expense claim"

        elif roll < 0.145:
            # Pattern 6: Velocity Anomaly
            amount = round(random.uniform(220.00, 480.00), 2)
            is_fraud = 1
            fraud_type = "Velocity Anomaly"
            description = "Repeated rapid succession claim"

        records.append({
            "Expense_ID": f"EXP-{2000 + i}",
            "Employee_ID": f"EMP-{100 + (hash(emp_name) % 50)}",
            "Employee_Name": emp_name,
            "Department": default_dept,
            "Category": category,
            "Amount": amount,
            "Policy_Limit": policy_limit,
            "Expense_Date": date_str,
            "Day_Of_Week": day_of_week,
            "Submission_Time": time_str,
            "Submission_Hour": hour,
            "Is_Weekend": is_weekend,
            "Has_Receipt": has_receipt,
            "Receipt_Hash": receipt_hash,
            "Description": description,
            "Is_Fraud": is_fraud,
            "Fraud_Type": fraud_type,
            "Is_Synthetic": 1,
            "Data_Source": "Academic Synthetic Dataset for Soft Computing Project"
        })

    df = pd.DataFrame(records)
    return df


if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__), "..", "dataset")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "synthetic_expenses.csv")

    df_gen = generate_synthetic_dataset(650)
    df_gen.to_csv(out_path, index=False)

    total = len(df_gen)
    fraud_count = df_gen["Is_Fraud"].sum()
    fraud_pct = round((fraud_count / total) * 100, 2)

    print(f"Generated {total} synthetic records at: {out_path}")
    print(f"Total Fraud Injected: {fraud_count} ({fraud_pct}%)")
    print("\nFraud Breakdown by Topology:")
    print(df_gen[df_gen["Is_Fraud"] == 1]["Fraud_Type"].value_counts())
