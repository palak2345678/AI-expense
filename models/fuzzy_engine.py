"""
Mamdani-Style Fuzzy Inference System for Expense Audit & Fraud Detection
Academic Course: Soft Computing (CSE / AIML)

Provides genuine Soft Computing multi-criteria fuzzy reasoning:
1. Triangular and Trapezoidal Membership Functions (trimf, trapmf)
2. Linguistic Variables: Amount Ratio, Receipt Risk, Temporal Timing Risk, Historical Spending Deviation
3. 12 Formal Mamdani IF-THEN Rules
4. Mamdani Minimum Implication & Maximum Aggregation
5. Center of Gravity (Centroid) Defuzzification
6. Fault-tolerant handling of missing or incomplete historical records
"""

import numpy as np
from typing import Dict, Any, Tuple, List, Optional


def trimf(x: np.ndarray, params: List[float]) -> np.ndarray:
    """
    Triangular Membership Function: params = [a, b, c]
    mu(x) = 0 for x < a
    mu(x) = (x - a) / (b - a) for a <= x <= b
    mu(x) = (c - x) / (c - b) for b <= x <= c
    mu(x) = 0 for x > c
    """
    a, b, c = float(params[0]), float(params[1]), float(params[2])
    x = np.asarray(x, dtype=float)
    y = np.zeros_like(x)

    # Left slope
    if a != b:
        idx1 = np.logical_and(a <= x, x < b)
        y[idx1] = (x[idx1] - a) / (b - a)
    else:
        y[x == b] = 1.0

    # Peak
    y[x == b] = 1.0

    # Right slope
    if b != c:
        idx2 = np.logical_and(b < x, x <= c)
        y[idx2] = (c - x[idx2]) / (c - b)

    return np.clip(y, 0.0, 1.0)


def trapmf(x: np.ndarray, params: List[float]) -> np.ndarray:
    """
    Trapezoidal Membership Function: params = [a, b, c, d]
    Supports left-open [a, a, c, d] and right-open [a, b, d, d].
    """
    a, b, c, d = float(params[0]), float(params[1]), float(params[2]), float(params[3])
    x = np.asarray(x, dtype=float)
    y = np.zeros_like(x)

    # 1. Left slope / Left-open
    if a == b:
        # Left-open plateau
        idx_plateau = (x <= c)
        y[idx_plateau] = 1.0
    else:
        idx_left = np.logical_and(a <= x, x < b)
        y[idx_left] = (x[idx_left] - a) / (b - a)
        idx_plateau = np.logical_and(b <= x, x <= c)
        y[idx_plateau] = 1.0

    # 2. Right slope / Right-open
    if c == d:
        # Right-open plateau
        idx_right = (x >= b)
        y[idx_right] = 1.0
    else:
        idx_slope = np.logical_and(c < x, x <= d)
        y[idx_slope] = (d - x[idx_slope]) / (d - c)
        y[x > d] = 0.0

    # Ensure outside [a, d] is strictly 0.0 unless open-ended
    if a != b:
        y[x < a] = 0.0
    if c != d:
        y[x > d] = 0.0

    return np.clip(y, 0.0, 1.0)


class SoftComputingFuzzyEngine:
    """
    Mamdani-style Fuzzy Logic Inference System for Expense Risk Evaluation.
    """

    def __init__(self, rule_weights: Optional[List[float]] = None):
        # 12 Mamdani rule weights (defaults to 1.0 each, optimizable via Genetic Algorithm)
        self.num_rules = 12
        if rule_weights is not None and len(rule_weights) == self.num_rules:
            self.rule_weights = [float(w) for w in rule_weights]
        else:
            self.rule_weights = [1.0] * self.num_rules

        # Universe of discourse for Output Risk Score [0, 100]
        self.risk_domain = np.linspace(0.0, 100.0, 201)

        # Output Fuzzy Sets on Risk Domain
        # Low Risk: [0, 0, 20, 38]
        self.risk_low = trapmf(self.risk_domain, [0.0, 0.0, 20.0, 38.0])
        # Medium Risk: [28, 50, 72]
        self.risk_medium = trimf(self.risk_domain, [28.0, 50.0, 72.0])
        # High Risk: [62, 80, 100, 100]
        self.risk_high = trapmf(self.risk_domain, [62.0, 80.0, 100.0, 100.0])

    def fuzzify_inputs(
        self,
        amount_ratio: float,
        receipt_risk: float,
        temporal_risk: float,
        deviation_ratio: float = 1.0
    ) -> Dict[str, Dict[str, float]]:
        """
        Fuzzifies crisp numeric inputs into degrees of membership [0.0, 1.0].
        
        Parameters:
        - amount_ratio: amount / policy_spending_limit (e.g. 1.0 is exactly at limit)
        - receipt_risk: 0.0 (clean verified) to 1.0 (missing / duplicate hash)
        - temporal_risk: 0.0 (regular work hours) to 1.0 (weekend late night)
        - deviation_ratio: amount / historical_average_amount (defaults to 1.0 if no history)
        """
        x_amt = np.array([max(0.0, float(amount_ratio))])
        x_rcpt = np.array([np.clip(float(receipt_risk), 0.0, 1.0)])
        x_time = np.array([np.clip(float(temporal_risk), 0.0, 1.0)])
        x_dev = np.array([max(0.0, float(deviation_ratio))])

        # 1. Amount Ratio Linguistic Sets
        amt_low = float(trapmf(x_amt, [0.0, 0.0, 0.6, 1.0])[0])
        amt_med = float(trimf(x_amt, [0.8, 1.25, 2.0])[0])
        amt_high = float(trimf(x_amt, [1.6, 2.8, 4.0])[0])
        amt_vhigh = float(trapmf(x_amt, [3.2, 5.0, 20.0, 20.0])[0])

        # 2. Receipt Risk Linguistic Sets
        rcpt_low = float(trapmf(x_rcpt, [0.0, 0.0, 0.2, 0.4])[0])
        rcpt_med = float(trimf(x_rcpt, [0.25, 0.5, 0.75])[0])
        rcpt_high = float(trapmf(x_rcpt, [0.6, 0.8, 1.0, 1.0])[0])

        # 3. Temporal Risk Linguistic Sets
        time_low = float(trapmf(x_time, [0.0, 0.0, 0.2, 0.4])[0])
        time_med = float(trimf(x_time, [0.25, 0.5, 0.75])[0])
        time_high = float(trapmf(x_time, [0.6, 0.8, 1.0, 1.0])[0])

        # 4. Historical Deviation Linguistic Sets
        dev_normal = float(trapmf(x_dev, [0.0, 0.0, 1.0, 1.5])[0])
        dev_moderate = float(trimf(x_dev, [1.2, 2.0, 3.2])[0])
        dev_extreme = float(trapmf(x_dev, [2.8, 4.5, 20.0, 20.0])[0])

        return {
            "amount": {"low": amt_low, "medium": amt_med, "high": amt_high, "very_high": amt_vhigh},
            "receipt": {"low": rcpt_low, "medium": rcpt_med, "high": rcpt_high},
            "temporal": {"low": time_low, "medium": time_med, "high": time_high},
            "deviation": {"normal": dev_normal, "moderate": dev_moderate, "extreme": dev_extreme}
        }

    def evaluate_rules(self, fuzzified: Dict[str, Dict[str, float]]) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """
        Evaluates 12 Mamdani IF-THEN Fuzzy Rules.
        Applies fuzzy AND (minimum), multiplies by rule weight, and aggregates with fuzzy OR (maximum).
        """
        amt = fuzzified["amount"]
        rcpt = fuzzified["receipt"]
        time = fuzzified["temporal"]
        dev = fuzzified["deviation"]
        w = self.rule_weights

        # Rule Definitions
        # R1: IF Amount is LOW AND Receipt is LOW AND Temporal is LOW -> LOW
        r1 = min(amt["low"], rcpt["low"], time["low"]) * w[0]

        # R2: IF Amount is LOW AND Temporal is MEDIUM -> LOW
        r2 = min(amt["low"], time["medium"]) * w[1]

        # R3: IF Amount is MEDIUM AND Receipt is LOW AND Temporal is LOW -> LOW
        r3 = min(amt["medium"], rcpt["low"], time["low"]) * w[2]

        # R4: IF Amount is MEDIUM AND Receipt is MEDIUM -> MEDIUM
        r4 = min(amt["medium"], rcpt["medium"]) * w[3]

        # R5: IF Amount is MEDIUM AND Temporal is HIGH -> MEDIUM
        r5 = min(amt["medium"], time["high"]) * w[4]

        # R6: IF Deviation is MODERATE AND Receipt is LOW -> MEDIUM
        r6 = min(dev["moderate"], rcpt["low"]) * w[5]

        # R7: IF Amount is HIGH AND Receipt is LOW -> MEDIUM
        r7 = min(amt["high"], rcpt["low"]) * w[6]

        # R8: IF Receipt is HIGH AND Amount is LOW -> MEDIUM (Missing receipt on low expense is not severe fraud)
        r8 = min(rcpt["high"], amt["low"]) * w[7]

        # R9: IF Amount is HIGH AND Temporal is HIGH -> HIGH
        r9 = min(amt["high"], time["high"]) * w[8]

        # R10: IF Amount is HIGH AND Receipt is HIGH -> HIGH
        r10 = min(amt["high"], rcpt["high"]) * w[9]

        # R11: IF Amount is VERY_HIGH -> HIGH
        r11 = amt["very_high"] * w[10]

        # R12: IF Deviation is EXTREME AND Temporal is HIGH -> HIGH
        r12 = min(dev["extreme"], time["high"]) * w[11]

        rule_records = [
            {"id": "R1", "rule": "IF Amount is LOW AND Receipt is LOW AND Temporal is LOW -> LOW", "fire": round(float(r1), 4), "consequent": "low"},
            {"id": "R2", "rule": "IF Amount is LOW AND Temporal is MEDIUM -> LOW", "fire": round(float(r2), 4), "consequent": "low"},
            {"id": "R3", "rule": "IF Amount is MEDIUM AND Receipt is LOW AND Temporal is LOW -> LOW", "fire": round(float(r3), 4), "consequent": "low"},
            {"id": "R4", "rule": "IF Amount is MEDIUM AND Receipt is MEDIUM -> MEDIUM", "fire": round(float(r4), 4), "consequent": "medium"},
            {"id": "R5", "rule": "IF Amount is MEDIUM AND Temporal is HIGH -> MEDIUM", "fire": round(float(r5), 4), "consequent": "medium"},
            {"id": "R6", "rule": "IF Deviation is MODERATE AND Receipt is LOW -> MEDIUM", "fire": round(float(r6), 4), "consequent": "medium"},
            {"id": "R7", "rule": "IF Amount is HIGH AND Receipt is LOW -> MEDIUM", "fire": round(float(r7), 4), "consequent": "medium"},
            {"id": "R8", "rule": "IF Receipt is HIGH AND Amount is LOW -> MEDIUM", "fire": round(float(r8), 4), "consequent": "medium"},
            {"id": "R9", "rule": "IF Amount is HIGH AND Temporal is HIGH -> HIGH", "fire": round(float(r9), 4), "consequent": "high"},
            {"id": "R10", "rule": "IF Amount is HIGH AND Receipt is HIGH -> HIGH", "fire": round(float(r10), 4), "consequent": "high"},
            {"id": "R11", "rule": "IF Amount is VERY_HIGH -> HIGH", "fire": round(float(r11), 4), "consequent": "high"},
            {"id": "R12", "rule": "IF Deviation is EXTREME AND Temporal is HIGH -> HIGH", "fire": round(float(r12), 4), "consequent": "high"},
        ]

        # Consequent clipping levels (fuzzy OR aggregation per class)
        low_activation = max(r1, r2, r3)
        med_activation = max(r4, r5, r6, r7, r8)
        high_activation = max(r9, r10, r11, r12)

        # Mamdani min-truncation
        clipped_low = np.minimum(low_activation, self.risk_low)
        clipped_med = np.minimum(med_activation, self.risk_medium)
        clipped_high = np.minimum(high_activation, self.risk_high)

        # Aggregated fuzzy output distribution via fuzzy MAX
        aggregated = np.maximum(clipped_low, np.maximum(clipped_med, clipped_high))

        return aggregated, rule_records

    def defuzzify_centroid(self, aggregated: np.ndarray) -> float:
        """
        Defuzzification using Center of Gravity (Centroid) method:
        COG = sum(y * mu(y)) / sum(mu(y))
        """
        sum_mu = np.sum(aggregated)
        if sum_mu == 0.0 or np.isnan(sum_mu):
            return 15.0  # Safe default baseline
        cog = np.sum(self.risk_domain * aggregated) / sum_mu
        return float(np.clip(round(cog, 2), 0.0, 100.0))

    @staticmethod
    def calculate_temporal_risk(submission_time: str, date_str: str) -> float:
        """
        Converts submission date and time into a continuous risk value in [0.0, 1.0].
        Standard hours: Mon-Fri 08:00 - 18:00 -> 0.05
        Late night: 22:00 - 05:00 -> 0.85
        Weekend late night: 0.95
        Weekend daytime: 0.50
        """
        from datetime import datetime
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            is_weekend = dt.weekday() >= 5
        except Exception:
            is_weekend = False

        try:
            hour = int(submission_time.split(":")[0])
        except Exception:
            hour = 12

        if is_weekend:
            if hour >= 22 or hour <= 5:
                return 0.95
            elif hour >= 19:
                return 0.65
            else:
                return 0.45
        else:
            if hour >= 23 or hour <= 4:
                return 0.85
            elif hour >= 20 or hour <= 6:
                return 0.50
            elif 8 <= hour <= 18:
                return 0.08
            else:
                return 0.25

    @staticmethod
    def calculate_receipt_risk(
        has_receipt: bool,
        is_duplicate: bool = False,
        receipt_text: str = ""
    ) -> float:
        """
        Calculates receipt validity risk in [0.0, 1.0].
        """
        if is_duplicate:
            return 1.0  # Highest risk: duplicate receipt
        if not has_receipt:
            return 0.70 # Missing receipt (flagged, but not automatic fraud on its own)
        if receipt_text and len(receipt_text.strip()) < 10:
            return 0.45 # Incomplete / vague receipt details
        return 0.05     # Clean, itemized receipt attached

    def evaluate_expense(
        self,
        amount: float,
        policy_limit: float,
        has_receipt: bool = True,
        is_duplicate: bool = False,
        submission_time: str = "12:00",
        submission_date: str = "2026-10-16",
        historical_average: Optional[float] = None,
        receipt_text: str = ""
    ) -> Dict[str, Any]:
        """
        Complete end-to-end Mamdani Fuzzy Risk Evaluation.
        """
        safe_limit = max(1.0, float(policy_limit))
        amount_ratio = float(amount) / safe_limit

        temporal_risk = self.calculate_temporal_risk(submission_time, submission_date)
        receipt_risk = self.calculate_receipt_risk(has_receipt, is_duplicate, receipt_text)

        if historical_average is not None and historical_average > 0:
            deviation_ratio = float(amount) / float(historical_average)
        else:
            deviation_ratio = 1.0  # Neutral prior when historical baseline is unavailable

        fuzzified = self.fuzzify_inputs(amount_ratio, receipt_risk, temporal_risk, deviation_ratio)
        aggregated, rule_records = self.evaluate_rules(fuzzified)
        fuzzy_score = self.defuzzify_centroid(aggregated)

        # Categorize
        if fuzzy_score >= 65.0:
            risk_category = "High"
        elif fuzzy_score >= 35.0:
            risk_category = "Medium"
        else:
            risk_category = "Low"

        # Active rules (fired with activation > 0.05)
        active_rules = [r for r in rule_records if r["fire"] > 0.05]
        active_rules.sort(key=lambda x: x["fire"], reverse=True)

        return {
            "fuzzy_score": fuzzy_score,
            "risk_category": risk_category,
            "amount_ratio": round(amount_ratio, 3),
            "temporal_risk": round(temporal_risk, 3),
            "receipt_risk": round(receipt_risk, 3),
            "deviation_ratio": round(deviation_ratio, 3),
            "fuzzified_memberships": fuzzified,
            "active_rules": active_rules,
            "all_rules": rule_records
        }


if __name__ == "__main__":
    engine = SoftComputingFuzzyEngine()
    
    # Test Clean normal claim
    res1 = engine.evaluate_expense(amount=120.0, policy_limit=300.0, has_receipt=True, submission_time="11:30")
    print(f"Clean Claim: Score = {res1['fuzzy_score']} ({res1['risk_category']})")

    # Test High-Value Off-Hours Claim
    res2 = engine.evaluate_expense(amount=4500.0, policy_limit=1000.0, has_receipt=False, submission_time="02:30", submission_date="2026-10-18")
    print(f"Suspicious Claim: Score = {res2['fuzzy_score']} ({res2['risk_category']})")
