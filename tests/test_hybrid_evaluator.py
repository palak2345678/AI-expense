"""
Unit Tests for Multi-Factor Hybrid Risk Synthesizer
"""

import pytest
from models.hybrid_evaluator import HybridExpenseFraudEvaluator


class TestHybridEvaluator:

    @pytest.fixture
    def evaluator(self):
        return HybridExpenseFraudEvaluator()

    def test_clean_expense_auto_approve(self, evaluator):
        expense = {
            "employee": "Sarah Jenkins",
            "department": "Engineering",
            "category": "Meals & Entertainment",
            "amount": 80.0,
            "date": "2026-10-15",
            "time": "12:30",
            "description": "Team lunch",
            "has_receipt": True
        }
        res = evaluator.evaluate(expense)
        assert res["final_risk_score"] < 35.0
        assert res["risk_level"] == "Low"
        assert res["status"] == "approved"
        assert "Auto-Approve" in res["next_action"]

    def test_high_risk_flagged_status(self, evaluator):
        expense = {
            "employee": "Marcus Vance",
            "department": "Executive",
            "category": "Equipment",
            "amount": 16500.0,
            "date": "2026-10-18",
            "time": "23:45",
            "description": "Late night equipment purchase",
            "has_receipt": False
        }
        res = evaluator.evaluate(expense)
        assert res["final_risk_score"] >= 60.0
        assert res["risk_level"] == "High"
        assert res["status"] == "flagged"

    def test_critical_override_exact_duplicate(self, evaluator):
        expense = {
            "id": "EXP-2001",
            "employee": "Alex Rivera",
            "department": "Sales",
            "category": "Travel",
            "amount": 1200.0,
            "date": "2026-10-15",
            "time": "14:00",
            "description": "Flight booking duplicate test",
            "has_receipt": True
        }
        history = [
            {
                "id": "EXP-1002",
                "employee": "Alex Rivera",
                "amount": 1200.0,
                "category": "Travel",
                "date": "2026-10-15",
                "description": "Flight booking"
            }
        ]
        res = evaluator.evaluate(expense, history)
        # Critical override should guarantee risk score >= 85
        assert res["final_risk_score"] >= 85.0
        assert res["risk_level"] == "High"

    def test_risk_score_bounds_and_structure(self, evaluator):
        expense = {
            "employee": "Test User",
            "amount": 500.0,
            "category": "General",
            "date": "2026-10-15",
            "description": "General claim"
        }
        res = evaluator.evaluate(expense)
        assert 0.0 <= res["final_risk_score"] <= 100.0
        assert "sub_scores" in res
        assert "fuzzy_details" in res
        assert "rule_details" in res
        assert "anomaly_details" in res
