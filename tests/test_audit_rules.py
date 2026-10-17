"""
Unit Tests for Rule-Based Expense Auditing Engine
"""

import pytest
from models.audit_rules import ExpenseAuditRuleEngine


class TestAuditRules:

    @pytest.fixture
    def engine(self):
        return ExpenseAuditRuleEngine()

    def test_compliant_expense_zero_penalty(self, engine):
        expense = {
            "employee": "Sarah Jenkins",
            "department": "Engineering",
            "category": "Meals & Entertainment",
            "amount": 75.0,
            "date": "2026-10-15",
            "time": "12:30",
            "description": "Team project milestone lunch",
            "has_receipt": True
        }
        res = engine.evaluate_rules(expense)
        assert res["rule_risk_score"] == 0.0
        assert res["triggered_rules_count"] == 0

    def test_exact_duplicate_detection(self, engine):
        expense = {
            "employee": "Alex Rivera",
            "amount": 1500.0,
            "category": "Travel",
            "date": "2026-10-15",
            "has_receipt": True,
            "description": "Flight booking to client conference"
        }
        history = [
            {
                "id": "EXP-1005",
                "employee": "Alex Rivera",
                "amount": 1500.0,
                "category": "Travel",
                "date": "2026-10-15",
                "description": "Flight booking"
            }
        ]
        res = engine.evaluate_rules(expense, history)
        assert res["rule_risk_score"] >= 80.0
        assert any(f["rule_id"] == "RULE-03-EXACT-DUPLICATE" for f in res["findings"])

    def test_split_invoicing_detection(self, engine):
        expense = {
            "employee": "Marcus Vance",
            "amount": 495.0,
            "category": "Office Supplies",
            "date": "2026-10-15",
            "has_receipt": True,
            "description": "Supply batch part B"
        }
        history = [
            {
                "id": "EXP-1010",
                "employee": "Marcus Vance",
                "amount": 490.0,
                "category": "Office Supplies",
                "date": "2026-10-14",
                "description": "Supply batch part A"
            }
        ]
        res = engine.evaluate_rules(expense, history)
        assert any(f["rule_id"] == "RULE-04-SPLIT-INVOICING" for f in res["findings"])

    def test_missing_receipt_high_value(self, engine):
        expense = {
            "employee": "Elena Rostova",
            "amount": 1200.0,
            "category": "Equipment",
            "date": "2026-10-15",
            "has_receipt": False,
            "receipt_hash": "NO_RECEIPT",
            "description": "Monitor and peripheral purchase without invoice"
        }
        res = engine.evaluate_rules(expense)
        assert any(f["rule_id"] == "RULE-05-MISSING-RECEIPT" for f in res["findings"])

    def test_invalid_negative_amount(self, engine):
        expense = {
            "employee": "Test User",
            "amount": -50.0,
            "category": "General",
            "date": "2026-10-15",
            "description": "Invalid negative entry"
        }
        res = engine.evaluate_rules(expense)
        assert any(f["rule_id"] == "RULE-01-INTEGRITY" for f in res["findings"])
        assert res["rule_risk_score"] == 100.0
