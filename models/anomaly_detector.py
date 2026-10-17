"""
Machine Learning Anomaly Detection Engine (Isolation Forest)
Academic Course: Soft Computing / Applied Machine Learning

Uses unsupervised Isolation Forest from scikit-learn to detect multivariate
outliers in corporate expense transactions without relying on fraud labels (zero leakage).

Important Academic Distinction:
An anomaly identifies an atypical statistical outlier pattern across multiple
dimensions (e.g. unexpected hour + high ratio + non-itemized receipt), but does NOT
guarantee malicious intent or confirmed fraud.
"""

import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


class ExpenseAnomalyDetector:
    """
    Unsupervised Isolation Forest Anomaly Detector for Expense Transactions.
    """

    FEATURE_NAMES = [
        "amount",
        "amount_policy_ratio",
        "amount_category_ratio",
        "submission_hour",
        "is_weekend",
        "receipt_risk"
    ]

    def __init__(self, contamination: float = 0.12, random_state: int = 42):
        self.contamination = contamination
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.model = IsolationForest(
            n_estimators=100,
            contamination=self.contamination,
            random_state=self.random_state,
            n_jobs=-1
        )
        self.is_fitted = False
        self.category_means: Dict[str, float] = {}

    def _extract_feature_row(
        self,
        amount: float,
        policy_limit: float,
        category: str,
        submission_time: str,
        submission_date: str,
        has_receipt: bool,
        is_duplicate: bool = False
    ) -> List[float]:
        """Extracts 6 normalized numeric features for a single transaction."""
        safe_limit = max(1.0, float(policy_limit))
        amount_policy_ratio = float(amount) / safe_limit

        cat_mean = self.category_means.get(category, safe_limit * 0.4)
        cat_mean = max(1.0, cat_mean)
        amount_category_ratio = float(amount) / cat_mean

        try:
            hour = float(submission_time.split(":")[0])
        except Exception:
            hour = 12.0

        try:
            from datetime import datetime
            dt = datetime.strptime(submission_date, "%Y-%m-%d")
            is_weekend = 1.0 if dt.weekday() >= 5 else 0.0
        except Exception:
            is_weekend = 0.0

        if is_duplicate:
            receipt_risk = 1.0
        elif not has_receipt:
            receipt_risk = 0.70
        else:
            receipt_risk = 0.05

        return [
            float(amount),
            float(amount_policy_ratio),
            float(amount_category_ratio),
            float(hour),
            float(is_weekend),
            float(receipt_risk)
        ]

    def fit(self, df_or_records: Any) -> "ExpenseAnomalyDetector":
        """
        Fits StandardScaler and Isolation Forest on training data.
        Ensures strict separation from any fraud ground-truth labels (unsupervised).
        """
        if isinstance(df_or_records, list):
            df = pd.DataFrame(df_or_records)
        else:
            df = df_or_records.copy()

        if len(df) < 5:
            # Insufficient samples for statistical training
            self.is_fitted = False
            return self

        # Precompute category means
        if "Category" in df.columns and "Amount" in df.columns:
            self.category_means = df.groupby("Category")["Amount"].mean().to_dict()
        elif "category" in df.columns and "amount" in df.columns:
            self.category_means = df.groupby("category")["amount"].mean().to_dict()

        feature_matrix = []
        for _, row in df.iterrows():
            amt = float(row.get("Amount", row.get("amount", 100.0)))
            pol = float(row.get("Role_Budget_Limit", row.get("policy_limit", amt * 1.5)))
            cat = str(row.get("Category", row.get("category", "General")))
            time_str = str(row.get("Submission_Hour", row.get("time", "12:00")))
            if ":" not in time_str:
                time_str = f"{int(float(time_str)):02d}:00"
            date_str = str(row.get("Expense_Date", row.get("date", "2026-10-16")))
            has_rcpt = bool(row.get("Has_Receipt", row.get("has_receipt", True)))
            rcpt_hash = str(row.get("Receipt_Hash", row.get("receipt_hash", "")))
            is_dup = (rcpt_hash == "HASH-9999-DUPLICATE")

            feats = self._extract_feature_row(amt, pol, cat, time_str, date_str, has_rcpt, is_dup)
            feature_matrix.append(feats)

        X = np.array(feature_matrix, dtype=float)
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)
        self.is_fitted = True
        return self

    def predict_anomaly(
        self,
        amount: float,
        policy_limit: float,
        category: str,
        submission_time: str = "12:00",
        submission_date: str = "2026-10-16",
        has_receipt: bool = True,
        is_duplicate: bool = False
    ) -> Dict[str, Any]:
        """
        Infers anomaly score [0.0, 100.0] and binary anomaly classification.
        """
        if not self.is_fitted:
            return {
                "anomaly_score": 10.0,
                "is_anomaly": False,
                "raw_decision_score": 0.15,
                "note": "Model uncalibrated; insufficient training samples."
            }

        feats = self._extract_feature_row(
            amount, policy_limit, category, submission_time, submission_date, has_receipt, is_duplicate
        )
        X = np.array([feats], dtype=float)
        X_scaled = self.scaler.transform(X)

        raw_score = float(self.model.decision_function(X_scaled)[0])
        pred_label = int(self.model.predict(X_scaled)[0])  # -1 = anomaly, 1 = normal

        # Map raw decision function to continuous risk scale [0, 100]
        # In scikit-learn IsolationForest, raw_score < 0 indicates an anomaly.
        # Centering at raw_score = 0.0 -> 50%, with slope mapping [-0.25, +0.25] to [100, 0]
        norm_score = np.clip(50.0 - (raw_score * 200.0), 0.0, 100.0)
        norm_score = round(float(norm_score), 2)

        is_anomaly = (pred_label == -1 or norm_score >= 50.0)

        if is_anomaly:
            note = f"Multi-attribute outlier pattern identified by Isolation Forest (score: {norm_score}%). Recommended for auditor inspection."
        else:
            note = "Transaction aligns with expected statistical distribution."

        return {
            "anomaly_score": norm_score,
            "is_anomaly": is_anomaly,
            "raw_decision_score": round(raw_score, 4),
            "note": note
        }

    def save(self, filepath: str):
        """Serializes trained model state to disk."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump({"scaler": self.scaler, "model": self.model, "means": self.category_means, "fitted": self.is_fitted}, filepath)

    def load(self, filepath: str) -> bool:
        """Loads trained model state from disk if available."""
        if not os.path.exists(filepath):
            return False
        try:
            data = joblib.load(filepath)
            self.scaler = data["scaler"]
            self.model = data["model"]
            self.category_means = data.get("means", {})
            self.is_fitted = data.get("fitted", True)
            return True
        except Exception:
            return False


if __name__ == "__main__":
    # Test on synthetic baseline
    detector = ExpenseAnomalyDetector()
    df_sample = pd.DataFrame([
        {"Amount": 45.0, "Role_Budget_Limit": 150.0, "Category": "Meals & Dining", "Submission_Hour": 12, "Expense_Date": "2026-10-14", "Has_Receipt": 1},
        {"Amount": 65.0, "Role_Budget_Limit": 150.0, "Category": "Meals & Dining", "Submission_Hour": 13, "Expense_Date": "2026-10-14", "Has_Receipt": 1},
        {"Amount": 80.0, "Role_Budget_Limit": 150.0, "Category": "Meals & Dining", "Submission_Hour": 14, "Expense_Date": "2026-10-14", "Has_Receipt": 1},
        {"Amount": 35.0, "Role_Budget_Limit": 150.0, "Category": "Meals & Dining", "Submission_Hour": 12, "Expense_Date": "2026-10-14", "Has_Receipt": 1},
        {"Amount": 55.0, "Role_Budget_Limit": 150.0, "Category": "Meals & Dining", "Submission_Hour": 11, "Expense_Date": "2026-10-14", "Has_Receipt": 1},
        {"Amount": 120.0, "Role_Budget_Limit": 150.0, "Category": "Meals & Dining", "Submission_Hour": 18, "Expense_Date": "2026-10-14", "Has_Receipt": 1},
        {"Amount": 95.0, "Role_Budget_Limit": 150.0, "Category": "Meals & Dining", "Submission_Hour": 19, "Expense_Date": "2026-10-14", "Has_Receipt": 1},
        {"Amount": 42.0, "Role_Budget_Limit": 150.0, "Category": "Meals & Dining", "Submission_Hour": 13, "Expense_Date": "2026-10-14", "Has_Receipt": 1},
    ])
    detector.fit(df_sample)

    normal_pred = detector.predict_anomaly(amount=50.0, policy_limit=150.0, category="Meals & Dining")
    outlier_pred = detector.predict_anomaly(amount=1850.0, policy_limit=150.0, category="Meals & Dining", submission_time="03:00", submission_date="2026-10-18")
    
    print("Normal prediction:", normal_pred)
    print("Outlier prediction:", outlier_pred)
