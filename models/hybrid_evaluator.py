"""
Multi-Factor Hybrid Risk Assessment Synthesizer
Academic Course: Soft Computing / AI Fraud Detection

Harmonizes:
1. Soft Computing: Mamdani Fuzzy Inference Engine (45% weight)
2. Machine Learning: Unsupervised Isolation Forest (25% weight)
3. Deterministic: Rule-Based Expense Auditor (30% weight)

Provides documented synthesis with critical override protection:
- Combines continuous soft computing with empirical rules without double counting
- Returns complete transparency: sub-scores, active fuzzy rules, triggered audit rules,
  anomaly indicators, final risk score [0, 100], risk category, reasons, and next action.
"""

import os
import sys
import numpy as np
# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from typing import Dict, Any, List, Optional
try:
    from models.fuzzy_engine import SoftComputingFuzzyEngine
    from models.audit_rules import ExpenseAuditRuleEngine
    from models.anomaly_detector import ExpenseAnomalyDetector
except ModuleNotFoundError:
    from fuzzy_engine import SoftComputingFuzzyEngine
    from audit_rules import ExpenseAuditRuleEngine
    from anomaly_detector import ExpenseAnomalyDetector


class HybridExpenseFraudEvaluator:
    """
    Unified multi-layered evaluation pipeline synthesizing Soft Computing,
    Machine Learning anomaly detection, and deterministic compliance auditing.
    """

    def __init__(
        self,
        fuzzy_weight: float = 0.45,
        anomaly_weight: float = 0.25,
        rule_weight: float = 0.30,
        policy_limits: Optional[Dict[str, float]] = None
    ):
        # Configurable mathematical weights summing to 1.0
        total_w = fuzzy_weight + anomaly_weight + rule_weight
        self.w_fuzzy = fuzzy_weight / total_w
        self.w_anomaly = anomaly_weight / total_w
        self.w_rules = rule_weight / total_w

        self.fuzzy_engine = SoftComputingFuzzyEngine()
        self.rule_engine = ExpenseAuditRuleEngine(policy_limits=policy_limits)
        self.anomaly_detector = ExpenseAnomalyDetector()

    def fit_anomaly_detector(self, dataset: Any):
        """Fits underlying Isolation Forest anomaly detector."""
        self.anomaly_detector.fit(dataset)

    def evaluate(
        self,
        expense: Dict[str, Any],
        historical_expenses: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Executes unified audit and fraud evaluation on a single expense claim.
        """
        history = historical_expenses or []

        # Extract core fields
        amount = float(expense.get("amount", 0.0))
        category = str(expense.get("category", "General")).strip()
        department = str(expense.get("department", "General")).strip()
        date_str = str(expense.get("date", "2026-10-16")).strip()
        time_str = str(expense.get("time", "12:00")).strip()
        description = str(expense.get("description", "")).strip()
        has_receipt = bool(expense.get("has_receipt", True))
        receipt_hash = str(expense.get("receipt_hash", "")).strip()
        is_duplicate = bool(expense.get("is_duplicate", False) or receipt_hash == "HASH-9999-DUPLICATE")

        policy_limit = self.rule_engine.get_policy_limit(category, department)

        # -------------------------------------------------------------
        # 1. Soft Computing Fuzzy Logic Inference
        # -------------------------------------------------------------
        # Compute historical average for this category from history
        cat_history = [
            float(h.get("amount", 0.0))
            for h in history
            if str(h.get("category", "")).strip().lower() == category.lower()
        ]
        historical_avg = sum(cat_history) / len(cat_history) if cat_history else (policy_limit * 0.4)

        fuzzy_res = self.fuzzy_engine.evaluate_expense(
            amount=amount,
            policy_limit=policy_limit,
            has_receipt=has_receipt,
            is_duplicate=is_duplicate,
            submission_time=time_str,
            submission_date=date_str,
            historical_average=historical_avg,
            receipt_text=description
        )
        fuzzy_score = fuzzy_res["fuzzy_score"]

        # -------------------------------------------------------------
        # 2. Rule-Based Deterministic Audit
        # -------------------------------------------------------------
        rule_res = self.rule_engine.evaluate_rules(expense, history)
        rule_score = rule_res["rule_risk_score"]

        # -------------------------------------------------------------
        # 3. Machine Learning Anomaly Detection (Isolation Forest)
        # -------------------------------------------------------------
        anomaly_res = self.anomaly_detector.predict_anomaly(
            amount=amount,
            policy_limit=policy_limit,
            category=category,
            submission_time=time_str,
            submission_date=date_str,
            has_receipt=has_receipt,
            is_duplicate=is_duplicate
        )
        anomaly_score = anomaly_res["anomaly_score"]

        # -------------------------------------------------------------
        # 4. Multi-Factor Hybrid Synthesis & Weight Calibration
        # -------------------------------------------------------------
        raw_final_score = (
            self.w_fuzzy * fuzzy_score +
            self.w_anomaly * anomaly_score +
            self.w_rules * rule_score
        )

        # Critical Override Check:
        # If an exact duplicate claim or critical policy breach was triggered,
        # ensure the score cannot be diluted by low anomaly or neutral sub-scores.
        has_critical_rule = any(f.get("severity") == "CRITICAL" for f in rule_res["findings"])
        if has_critical_rule:
            final_risk_score = max(raw_final_score, 85.0)
        else:
            final_risk_score = raw_final_score

        final_risk_score = float(np.clip(round(final_risk_score, 1), 0.0, 100.0))

        # Categorize
        if final_risk_score >= 60.0:
            risk_level = "High"
            status = "flagged"
            next_action = "Reject Claim / Escalate to Internal Audit Investigation"
        elif final_risk_score >= 30.0:
            risk_level = "Medium"
            status = "flagged"
            next_action = "Queue for Secondary Auditor Review (Manual Receipt Inspection)"
        else:
            risk_level = "Low"
            status = "approved"
            next_action = "Auto-Approve Claim (Low Risk)"

        # Synthesize Human-Readable Auditor Reasons
        synthesized_reasons: List[str] = []

        # Add rule findings
        for f in rule_res["findings"]:
            synthesized_reasons.append(f"{f['rule_name']}: {f['explanation']}")

        # Add active fuzzy reasoning explanation if risk is elevated
        if fuzzy_score >= 40.0 and fuzzy_res["active_rules"]:
            top_rule = fuzzy_res["active_rules"][0]
            synthesized_reasons.append(
                f"Soft Computing Fuzzy Assessment: Fired {top_rule['id']} ({top_rule['consequent'].upper()} Risk, activation {top_rule['fire']:.2f})."
            )

        # Add anomaly detection note if outlier detected
        if anomaly_res["is_anomaly"]:
            synthesized_reasons.append(
                f"ML Anomaly Detection: {anomaly_res['note']}"
            )

        if not synthesized_reasons:
            synthesized_reasons = ["Verified: Transaction complies with standard corporate policy thresholds."]

        return {
            "final_risk_score": final_risk_score,
            "risk_score": int(round(final_risk_score)),  # Backwards compatibility with frontend
            "risk_level": risk_level,
            "riskLevel": risk_level,                      # Backwards compatibility with frontend
            "status": status,
            "reasons": synthesized_reasons,
            "next_action": next_action,
            "weights": {
                "fuzzy": round(self.w_fuzzy, 2),
                "anomaly": round(self.w_anomaly, 2),
                "rules": round(self.w_rules, 2)
            },
            "sub_scores": {
                "fuzzy_risk_score": fuzzy_score,
                "anomaly_risk_score": anomaly_score,
                "rule_risk_score": rule_score
            },
            "fuzzy_details": fuzzy_res,
            "rule_details": rule_res,
            "anomaly_details": anomaly_res
        }


if __name__ == "__main__":
    evaluator = HybridExpenseFraudEvaluator()

    # Test Clean Claim
    clean_claim = {
        "employee": "Sarah Jenkins",
        "department": "Engineering",
        "category": "Meals & Entertainment",
        "amount": 95.0,
        "date": "2026-10-15",
        "time": "12:30",
        "description": "Lunch meeting with engineering vendor",
        "has_receipt": True
    }
    r_clean = evaluator.evaluate(clean_claim)
    print("CLEAN CLAIM RESULT:")
    print(f"Risk Score: {r_clean['final_risk_score']} | Level: {r_clean['risk_level']} | Status: {r_clean['status']}")
    print(f"Sub-scores: {r_clean['sub_scores']}")
    print(f"Reasons: {r_clean['reasons']}\n")

    # Test High-Risk Fraud Claim
    fraud_claim = {
        "employee": "Marcus Vance",
        "department": "Executive",
        "category": "Equipment",
        "amount": 16500.0,
        "date": "2026-10-18",
        "time": "23:45",
        "description": "Executive portable workstation setup",
        "has_receipt": False
    }
    r_fraud = evaluator.evaluate(fraud_claim)
    print("HIGH-RISK CLAIM RESULT:")
    print(f"Risk Score: {r_fraud['final_risk_score']} | Level: {r_fraud['risk_level']} | Status: {r_fraud['status']}")
    print(f"Sub-scores: {r_fraud['sub_scores']}")
    print(f"Reasons: {r_fraud['reasons']}")
