"""
Unit Tests for Machine Learning Anomaly Detector (Isolation Forest)
"""

import pytest
import pandas as pd
from models.anomaly_detector import ExpenseAnomalyDetector


class TestAnomalyDetector:

    @pytest.fixture
    def detector(self):
        detector = ExpenseAnomalyDetector()
        # Seed simple baseline
        df = pd.DataFrame([
            {"Amount": 45.0, "Role_Budget_Limit": 150.0, "Category": "Meals & Dining", "Submission_Hour": 12, "Expense_Date": "2026-10-14", "Has_Receipt": 1},
            {"Amount": 55.0, "Role_Budget_Limit": 150.0, "Category": "Meals & Dining", "Submission_Hour": 13, "Expense_Date": "2026-10-14", "Has_Receipt": 1},
            {"Amount": 65.0, "Role_Budget_Limit": 150.0, "Category": "Meals & Dining", "Submission_Hour": 12, "Expense_Date": "2026-10-14", "Has_Receipt": 1},
            {"Amount": 70.0, "Role_Budget_Limit": 150.0, "Category": "Meals & Dining", "Submission_Hour": 14, "Expense_Date": "2026-10-14", "Has_Receipt": 1},
            {"Amount": 50.0, "Role_Budget_Limit": 150.0, "Category": "Meals & Dining", "Submission_Hour": 11, "Expense_Date": "2026-10-14", "Has_Receipt": 1},
            {"Amount": 80.0, "Role_Budget_Limit": 150.0, "Category": "Meals & Dining", "Submission_Hour": 18, "Expense_Date": "2026-10-14", "Has_Receipt": 1},
            {"Amount": 40.0, "Role_Budget_Limit": 150.0, "Category": "Meals & Dining", "Submission_Hour": 13, "Expense_Date": "2026-10-14", "Has_Receipt": 1},
            {"Amount": 60.0, "Role_Budget_Limit": 150.0, "Category": "Meals & Dining", "Submission_Hour": 12, "Expense_Date": "2026-10-14", "Has_Receipt": 1},
        ])
        detector.fit(df)
        return detector

    def test_normal_transaction_low_anomaly_score(self, detector):
        res = detector.predict_anomaly(
            amount=55.0,
            policy_limit=150.0,
            category="Meals & Dining",
            submission_time="12:30",
            submission_date="2026-10-14"
        )
        assert 0.0 <= res["anomaly_score"] <= 40.0
        assert res["is_anomaly"] is False

    def test_multivariate_outlier_elevated_score(self, detector):
        res = detector.predict_anomaly(
            amount=2500.0,
            policy_limit=150.0,
            category="Meals & Dining",
            submission_time="03:15",
            submission_date="2026-10-18",
            has_receipt=False
        )
        assert res["anomaly_score"] >= 50.0
        assert res["is_anomaly"] is True

    def test_unfitted_model_safe_fallback(self):
        empty_detector = ExpenseAnomalyDetector()
        res = empty_detector.predict_anomaly(amount=100.0, policy_limit=300.0, category="General")
        assert res["is_anomaly"] is False
        assert 0.0 <= res["anomaly_score"] <= 20.0
