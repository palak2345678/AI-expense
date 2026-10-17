"""
Rule-Based Expense Auditing Engine
Academic Course: Soft Computing / Fraud Detection

Deterministic and heuristic audit rules detecting:
1. Exact duplicate claims (same employee, same amount, same date or receipt hash)
2. Potential split invoicing / near-duplicate claims (e.g. $450-$499.99 submitted within 24-48h)
3. Expenses exceeding configured departmental / role-based policy spending limits
4. Missing or invalid receipts, scaled by amount threshold
5. Repeated / high-velocity claims (velocity bursts)
6. Irregular timing (weekend / late-night personal leisure claims)
7. Invalid or incomplete transaction data
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional


# Standard Corporate Policy Spending Limits per Department & Category
DEFAULT_POLICY_LIMITS = {
    "Meals & Entertainment": 150.0,
    "Meals & Dining": 150.0,
    "Travel": 1200.0,
    "Travel & Flights": 1200.0,
    "Hotel Accommodation": 350.0,
    "Equipment": 2500.0,
    "Software & IT": 800.0,
    "Software & Cloud Services": 800.0,
    "Office Supplies": 300.0,
    "Consulting": 2000.0,
    "Taxi & Rideshare": 75.0,
    "General": 500.0
}

# Approval threshold below which receipts might traditionally not require manager sign-off
SPLIT_INVOICE_THRESHOLD = 500.0


class ExpenseAuditRuleEngine:
    """
    Executes modular deterministic audit checks on submitted expenses.
    """

    def __init__(self, policy_limits: Optional[Dict[str, float]] = None):
        self.policy_limits = policy_limits or DEFAULT_POLICY_LIMITS

    def get_policy_limit(self, category: str, department: str = "General") -> float:
        """Retrieves applicable policy spending limit."""
        return self.policy_limits.get(category, self.policy_limits.get("General", 500.0))

    def evaluate_rules(
        self,
        current_expense: Dict[str, Any],
        historical_expenses: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Runs comprehensive rule-based checks on an expense transaction against historical records.
        """
        history = historical_expenses or []
        findings: List[Dict[str, Any]] = []
        rule_score_accum = 0.0

        emp = str(current_expense.get("employee", "")).strip()
        amt = float(current_expense.get("amount", 0.0))
        cat = str(current_expense.get("category", "General")).strip()
        date_str = str(current_expense.get("date", "")).strip()
        time_str = str(current_expense.get("time", "12:00")).strip()
        desc = str(current_expense.get("description", "")).strip()
        has_receipt = bool(current_expense.get("has_receipt", True))
        receipt_hash = str(current_expense.get("receipt_hash", "")).strip()

        # Parse current date
        try:
            curr_dt = datetime.strptime(date_str, "%Y-%m-%d")
        except Exception:
            curr_dt = datetime.now()

        # -------------------------------------------------------------
        # Rule 1: Data Integrity Check
        # -------------------------------------------------------------
        if amt <= 0.0:
            findings.append({
                "rule_id": "RULE-01-INTEGRITY",
                "rule_name": "Invalid Transaction Amount",
                "severity": "CRITICAL",
                "explanation": f"Claim amount (${amt:,.2f}) must be strictly positive.",
                "penalty": 100.0
            })
            rule_score_accum += 100.0

        if not desc or len(desc) < 5:
            findings.append({
                "rule_id": "RULE-01B-DESC",
                "rule_name": "Inadequate Business Justification",
                "severity": "WARNING",
                "explanation": "Description or business justification is missing or excessively brief.",
                "penalty": 15.0
            })
            rule_score_accum += 15.0

        # -------------------------------------------------------------
        # Rule 2: Policy Spending Limit Violation
        # -------------------------------------------------------------
        limit = self.get_policy_limit(cat, current_expense.get("department", "General"))
        if amt > limit:
            excess_pct = round(((amt - limit) / limit) * 100, 1)
            if amt >= limit * 2.5:
                severity = "CRITICAL"
                penalty = 45.0
            elif amt >= limit * 1.5:
                severity = "HIGH"
                penalty = 30.0
            else:
                severity = "WARNING"
                penalty = 15.0

            findings.append({
                "rule_id": "RULE-02-POLICY-LIMIT",
                "rule_name": "Spending Limit Exceeded",
                "severity": severity,
                "explanation": f"Amount (${amt:,.2f}) exceeds the {cat} policy threshold of ${limit:,.2f} by {excess_pct}%.",
                "penalty": penalty
            })
            rule_score_accum += penalty

        # -------------------------------------------------------------
        # Rule 3: Exact Duplicate Claim Check
        # -------------------------------------------------------------
        exact_dups = []
        for h in history:
            # Skip comparing expense with itself if ID matches
            if current_expense.get("id") and h.get("id") == current_expense.get("id"):
                continue

            h_emp = str(h.get("employee", "")).strip().lower()
            h_amt = float(h.get("amount", 0.0))
            h_date = str(h.get("date", "")).strip()
            h_hash = str(h.get("receipt_hash", "")).strip()

            same_emp = (h_emp == emp.lower())
            same_amt = (abs(h_amt - amt) < 0.01)
            same_date = (h_date == date_str)
            same_receipt = bool(receipt_hash and h_hash and receipt_hash == h_hash and receipt_hash != "NO_RECEIPT")

            if same_receipt or (same_emp and same_amt and same_date):
                exact_dups.append(h)

        if exact_dups:
            dup_id = exact_dups[0].get("id", "HISTORICAL")
            findings.append({
                "rule_id": "RULE-03-EXACT-DUPLICATE",
                "rule_name": "Exact Duplicate Claim Detected",
                "severity": "CRITICAL",
                "explanation": f"Identical claim detected matching expense ID {dup_id} (Employee: {emp}, Amount: ${amt:,.2f}, Date: {date_str}).",
                "penalty": 80.0
            })
            rule_score_accum += 80.0

        # -------------------------------------------------------------
        # Rule 4: Potential Split Invoicing (Near-Threshold Structuring)
        # -------------------------------------------------------------
        # E.g., multiple submissions just under $500 threshold ($450-$499.99) within 48h
        is_near_threshold = (SPLIT_INVOICE_THRESHOLD * 0.88 <= amt < SPLIT_INVOICE_THRESHOLD)
        split_candidates = []
        for h in history:
            if current_expense.get("id") and h.get("id") == current_expense.get("id"):
                continue
            if str(h.get("employee", "")).strip().lower() != emp.lower():
                continue
            h_amt = float(h.get("amount", 0.0))
            try:
                h_dt = datetime.strptime(str(h.get("date", "")).strip(), "%Y-%m-%d")
                day_diff = abs((curr_dt - h_dt).days)
            except Exception:
                day_diff = 999

            if day_diff <= 2 and (SPLIT_INVOICE_THRESHOLD * 0.88 <= h_amt < SPLIT_INVOICE_THRESHOLD):
                split_candidates.append(h)

        if is_near_threshold and split_candidates:
            findings.append({
                "rule_id": "RULE-04-SPLIT-INVOICING",
                "rule_name": "Potential Threshold Structuring / Split Invoicing",
                "severity": "HIGH",
                "explanation": f"Multiple expenses filed just below the ${SPLIT_INVOICE_THRESHOLD:,.0f} manager approval ceiling within 48 hours.",
                "penalty": 40.0
            })
            rule_score_accum += 40.0

        # -------------------------------------------------------------
        # Rule 5: Missing Receipt Audit
        # -------------------------------------------------------------
        if not has_receipt or receipt_hash == "NO_RECEIPT":
            if amt > 250.0:
                severity = "HIGH"
                penalty = 35.0
            else:
                severity = "WARNING"
                penalty = 15.0

            findings.append({
                "rule_id": "RULE-05-MISSING-RECEIPT",
                "rule_name": "Missing Required Receipt Proof",
                "severity": severity,
                "explanation": f"No receipt documentation attached for claim of ${amt:,.2f} (corporate mandate requires proof for items > $75).",
                "penalty": penalty
            })
            rule_score_accum += penalty

        # -------------------------------------------------------------
        # Rule 6: Velocity Burst Check (Frequency of Claims)
        # -------------------------------------------------------------
        recent_claims = 0
        for h in history:
            if str(h.get("employee", "")).strip().lower() != emp.lower():
                continue
            try:
                h_dt = datetime.strptime(str(h.get("date", "")).strip(), "%Y-%m-%d")
                if 0 <= (curr_dt - h_dt).days <= 3:
                    recent_claims += 1
            except Exception:
                pass

        if recent_claims >= 4:
            findings.append({
                "rule_id": "RULE-06-CLAIM-VELOCITY",
                "rule_name": "Abnormal Claim Velocity",
                "severity": "WARNING",
                "explanation": f"Employee has submitted {recent_claims + 1} expense claims in the past 72 hours.",
                "penalty": 20.0
            })
            rule_score_accum += 20.0

        # -------------------------------------------------------------
        # Rule 7: Irregular Submission Timing (Off-Hours Weekend)
        # -------------------------------------------------------------
        try:
            hour = int(time_str.split(":")[0])
        except Exception:
            hour = 12

        is_weekend = (curr_dt.weekday() >= 5)
        if is_weekend and (hour >= 22 or hour <= 4) and cat in ["Meals & Entertainment", "Meals & Dining", "Office Supplies"]:
            findings.append({
                "rule_id": "RULE-07-OFF-HOURS",
                "rule_name": "Irregular Submission Timing",
                "severity": "WARNING",
                "explanation": f"Transaction filed on a weekend during non-business off-hours ({time_str}) for non-travel category ({cat}).",
                "penalty": 20.0
            })
            rule_score_accum += 20.0

        # Calculate bounded normalized rule risk score [0, 100]
        normalized_rule_score = min(100.0, rule_score_accum)

        reasons = [f["explanation"] for f in findings]
        if not reasons:
            reasons = ["Verified: Transaction complies with standard corporate policy rules."]

        return {
            "rule_risk_score": round(normalized_rule_score, 2),
            "triggered_rules_count": len(findings),
            "findings": findings,
            "reasons": reasons,
            "policy_limit_applied": limit
        }


if __name__ == "__main__":
    engine = ExpenseAuditRuleEngine()

    # Test clean compliant expense
    clean = engine.evaluate_rules({
        "employee": "Sarah Jenkins",
        "amount": 85.0,
        "category": "Meals & Entertainment",
        "date": "2026-10-15",
        "time": "12:30",
        "has_receipt": True,
        "description": "Lunch meeting with engineering vendor"
    })
    print("Clean Rule Test:", clean["rule_risk_score"], clean["reasons"])

    # Test duplicate expense
    dup = engine.evaluate_rules(
        {
            "employee": "Alex Rivera",
            "amount": 3200.0,
            "category": "Meals & Entertainment",
            "date": "2026-10-15",
            "time": "14:00",
            "has_receipt": True,
            "description": "VIP client dinner reservation"
        },
        historical_expenses=[
            {
                "id": "EXP-1001",
                "employee": "Alex Rivera",
                "amount": 3200.0,
                "category": "Meals & Entertainment",
                "date": "2026-10-15",
                "description": "VIP client dinner"
            }
        ]
    )
    print("Duplicate Rule Test:", dup["rule_risk_score"], dup["reasons"])
