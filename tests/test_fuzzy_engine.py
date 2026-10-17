"""
Unit Tests for Soft Computing Mamdani Fuzzy Inference Engine
"""

import pytest
import numpy as np
from models.fuzzy_engine import SoftComputingFuzzyEngine, trimf, trapmf


class TestFuzzyEngine:

    @pytest.fixture
    def engine(self):
        return SoftComputingFuzzyEngine()

    def test_trimf_boundary_values(self):
        params = [10.0, 20.0, 30.0]
        x = np.array([5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 35.0])
        y = trimf(x, params)
        assert y[0] == 0.0
        assert y[1] == 0.0
        assert y[2] == 0.5
        assert y[3] == 1.0
        assert y[4] == 0.5
        assert y[5] == 0.0
        assert y[6] == 0.0

    def test_trapmf_left_open(self):
        params = [0.0, 0.0, 10.0, 20.0]
        x = np.array([-5.0, 0.0, 5.0, 10.0, 15.0, 20.0, 25.0])
        y = trapmf(x, params)
        assert y[0] == 1.0  # left open
        assert y[1] == 1.0
        assert y[2] == 1.0
        assert y[3] == 1.0
        assert y[4] == 0.5
        assert y[5] == 0.0
        assert y[6] == 0.0

    def test_trapmf_right_open(self):
        params = [10.0, 20.0, 30.0, 30.0]
        x = np.array([5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 35.0])
        y = trapmf(x, params)
        assert y[0] == 0.0
        assert y[1] == 0.0
        assert y[2] == 0.5
        assert y[3] == 1.0
        assert y[4] == 1.0
        assert y[5] == 1.0
        assert y[6] == 1.0  # right open

    def test_clean_expense_low_risk(self, engine):
        res = engine.evaluate_expense(
            amount=65.0,
            policy_limit=200.0,
            has_receipt=True,
            submission_time="11:30",
            submission_date="2026-10-14"
        )
        assert 0.0 <= res["fuzzy_score"] <= 35.0
        assert res["risk_category"] == "Low"
        assert res["amount_ratio"] < 1.0

    def test_extreme_outlier_high_risk(self, engine):
        res = engine.evaluate_expense(
            amount=8500.0,
            policy_limit=1000.0,
            has_receipt=False,
            submission_time="02:30",
            submission_date="2026-10-18"  # Sunday
        )
        assert res["fuzzy_score"] >= 65.0
        assert res["risk_category"] == "High"
        assert len(res["active_rules"]) > 0

    def test_small_amount_missing_receipt_not_extreme(self, engine):
        # Missing receipt alone on small coffee/snack should not be classified as High risk
        res = engine.evaluate_expense(
            amount=25.0,
            policy_limit=150.0,
            has_receipt=False,
            submission_time="13:00",
            submission_date="2026-10-14"
        )
        # Should remain Medium or Low, strictly below 60.0
        assert res["fuzzy_score"] < 60.0
        assert res["risk_category"] in ["Low", "Medium"]

    def test_missing_history_neutral_fallback(self, engine):
        # When historical_average is None, system uses neutral prior (1.0) without crashing
        res = engine.evaluate_expense(
            amount=100.0,
            policy_limit=300.0,
            historical_average=None
        )
        assert 0.0 <= res["fuzzy_score"] <= 100.0
        assert res["deviation_ratio"] == 1.0
