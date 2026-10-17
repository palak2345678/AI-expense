"""
Persistent SQLite Database Engine for Expense Auditing & Fraud Platform
Academic Course: Soft Computing / Full-Stack Engineering

Replaces ephemeral in-memory storage with a persistent relational database:
- Transactions table with full audit fields (fuzzy scores, anomaly scores, rule findings, status)
- Automatic schema initialization
- Seeding from live historical expenses and seed dataset
- SQL aggregation queries for dashboard KPIs, monthly trendlines, and category allocations
"""

import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional


if os.path.exists(os.path.join(os.path.dirname(__file__), "expenses.db")):
    DB_PATH = os.path.join(os.path.dirname(__file__), "expenses.db")
elif os.path.exists(os.path.join(os.path.dirname(__file__), "..", "expenses.db")):
    DB_PATH = os.path.join(os.path.dirname(__file__), "..", "expenses.db")
else:
    DB_PATH = os.path.join(os.path.dirname(__file__), "expenses.db")


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Returns SQLite connection with row factory enabled."""
    path = db_path or DB_PATH
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Optional[str] = None):
    """Initializes tables and indexes."""
    conn = get_connection(db_path)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id TEXT PRIMARY KEY,
        employee TEXT NOT NULL,
        department TEXT NOT NULL,
        category TEXT NOT NULL,
        amount REAL NOT NULL,
        description TEXT NOT NULL,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        has_receipt INTEGER NOT NULL DEFAULT 1,
        receipt_hash TEXT DEFAULT '',
        status TEXT NOT NULL DEFAULT 'flagged',
        risk_score INTEGER NOT NULL DEFAULT 0,
        risk_level TEXT NOT NULL DEFAULT 'Low',
        fuzzy_score REAL NOT NULL DEFAULT 0.0,
        anomaly_score REAL NOT NULL DEFAULT 0.0,
        rule_score REAL NOT NULL DEFAULT 0.0,
        reasons TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    """)

    cur.execute("CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(date);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(category);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_expenses_risk ON expenses(risk_level);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_expenses_status ON expenses(status);")

    conn.commit()
    conn.close()


def seed_database_if_empty(db_path: Optional[str] = None):
    """
    Seeds database with historical live records from initial platform deployment.
    """
    init_db(db_path)
    conn = get_connection(db_path)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) as cnt FROM expenses;")
    count = cur.fetchone()["cnt"]

    if count > 0:
        conn.close()
        return

    # Check for live seed file
    seed_json_path = os.path.join(os.path.dirname(__file__), "..", "dataset", "live_seed_expenses.json")
    if not os.path.exists(seed_json_path):
        seed_json_path = os.path.join(os.path.dirname(__file__), "live_seed_expenses.json")
    if os.path.exists(seed_json_path):
        with open(seed_json_path, "r", encoding="utf-8") as f:
            records = json.load(f)

        for r in records:
            reasons_json = json.dumps(r.get("reasons", ["Verified: Transaction within standard corporate policy thresholds."]))
            cur.execute("""
            INSERT OR IGNORE INTO expenses (
                id, employee, department, category, amount, description,
                date, time, has_receipt, receipt_hash, status, risk_score,
                risk_level, fuzzy_score, anomaly_score, rule_score, reasons, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                r.get("id"),
                r.get("employee"),
                r.get("department", "General"),
                r.get("category"),
                float(r.get("amount", 0.0)),
                r.get("description", "Corporate expense filing"),
                r.get("date"),
                r.get("time", "12:00"),
                1 if r.get("has_receipt", True) else 0,
                r.get("receipt_hash", f"RCPT-{abs(hash(r.get('id', '')))%1000000}"),
                r.get("status", "approved"),
                int(r.get("riskScore", 0)),
                r.get("riskLevel", "Low"),
                float(r.get("riskScore", 0)),
                float(r.get("riskScore", 0) * 0.8),
                float(r.get("riskScore", 0)),
                reasons_json,
                r.get("createdAt", datetime.now().isoformat())
            ))
        conn.commit()

    conn.close()


def insert_expense(expense_dict: Dict[str, Any], db_path: Optional[str] = None) -> Dict[str, Any]:
    """Inserts an audited expense record."""
    conn = get_connection(db_path)
    cur = conn.cursor()

    reasons_str = json.dumps(expense_dict.get("reasons", []))
    created_at = expense_dict.get("createdAt") or datetime.now().isoformat()

    cur.execute("""
    INSERT OR REPLACE INTO expenses (
        id, employee, department, category, amount, description,
        date, time, has_receipt, receipt_hash, status, risk_score,
        risk_level, fuzzy_score, anomaly_score, rule_score, reasons, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        expense_dict["id"],
        expense_dict["employee"],
        expense_dict.get("department", "General"),
        expense_dict["category"],
        float(expense_dict["amount"]),
        expense_dict["description"],
        expense_dict["date"],
        expense_dict.get("time", "12:00"),
        1 if expense_dict.get("has_receipt", True) else 0,
        expense_dict.get("receipt_hash", ""),
        expense_dict["status"],
        int(expense_dict.get("riskScore", expense_dict.get("risk_score", 0))),
        expense_dict.get("riskLevel", expense_dict.get("risk_level", "Low")),
        float(expense_dict.get("fuzzy_score", 0.0)),
        float(expense_dict.get("anomaly_score", 0.0)),
        float(expense_dict.get("rule_score", 0.0)),
        reasons_str,
        created_at
    ))

    conn.commit()
    conn.close()
    return expense_dict


def get_all_expenses(
    category: str = "all",
    risk: str = "all",
    search: str = "",
    db_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Retrieves expenses with dynamic filtering."""
    conn = get_connection(db_path)
    cur = conn.cursor()

    query = "SELECT * FROM expenses WHERE 1=1"
    params = []

    if category and category.lower() != "all":
        query += " AND category = ?"
        params.append(category)

    if risk and risk.lower() != "all":
        query += " AND risk_level = ?"
        params.append(risk)

    if search and search.strip():
        term = f"%{search.strip().lower()}%"
        query += " AND (LOWER(employee) LIKE ? OR LOWER(description) LIKE ? OR LOWER(id) LIKE ?)"
        params.extend([term, term, term])

    query += " ORDER BY date DESC, time DESC;"

    cur.execute(query, params)
    rows = cur.fetchall()

    result = []
    for r in rows:
        reasons = []
        try:
            reasons = json.loads(r["reasons"])
        except Exception:
            reasons = [r["reasons"]] if r["reasons"] else []

        result.append({
            "id": r["id"],
            "employee": r["employee"],
            "department": r["department"],
            "category": r["category"],
            "amount": float(r["amount"]),
            "description": r["description"],
            "date": r["date"],
            "time": r["time"],
            "has_receipt": bool(r["has_receipt"]),
            "receipt_hash": r["receipt_hash"],
            "status": r["status"],
            "riskScore": int(r["risk_score"]),
            "riskLevel": r["risk_level"],
            "fuzzyScore": float(r["fuzzy_score"]),
            "anomalyScore": float(r["anomaly_score"]),
            "ruleScore": float(r["rule_score"]),
            "reasons": reasons,
            "createdAt": r["created_at"]
        })

    conn.close()
    return result


def update_expense_status(expense_id: str, new_status: str, db_path: Optional[str] = None) -> bool:
    """Updates approval status (approved / rejected / flagged)."""
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("UPDATE expenses SET status = ? WHERE id = ?;", (new_status, expense_id))
    affected = cur.rowcount > 0
    conn.commit()
    conn.close()
    return affected


def get_dashboard_stats(db_path: Optional[str] = None) -> Dict[str, Any]:
    """Calculates live KPI metrics from persistent database."""
    conn = get_connection(db_path)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) as total_count, COALESCE(SUM(amount), 0.0) as total_amount, COALESCE(AVG(risk_score), 0.0) as avg_risk FROM expenses;")
    row1 = cur.fetchone()

    cur.execute("SELECT COUNT(*) as flagged_count FROM expenses WHERE risk_level = 'High' OR status = 'flagged';")
    row2 = cur.fetchone()

    cur.execute("SELECT COALESCE(SUM(amount), 0.0) as money_saved FROM expenses WHERE status = 'rejected' OR (risk_level = 'High' AND status = 'flagged');")
    row3 = cur.fetchone()

    conn.close()

    return {
        "totalExpenses": int(row1["total_count"]),
        "totalAmount": round(float(row1["total_amount"]), 2),
        "flaggedCount": int(row2["flagged_count"]),
        "avgRiskScore": round(float(row1["avg_risk"]), 1),
        "moneySaved": round(float(row3["money_saved"]), 2)
    }


def get_monthly_stats(db_path: Optional[str] = None) -> Dict[str, Any]:
    """Calculates monthly expenditure trajectory and flagged amounts for Line Chart."""
    conn = get_connection(db_path)
    cur = conn.cursor()

    cur.execute("""
    SELECT 
        SUBSTR(date, 1, 7) as month_key,
        COUNT(*) as count,
        COALESCE(SUM(amount), 0.0) as total,
        COALESCE(SUM(CASE WHEN risk_level = 'High' OR status = 'flagged' OR status = 'rejected' THEN amount ELSE 0 END), 0.0) as flagged
    FROM expenses
    WHERE date IS NOT NULL AND LENGTH(date) >= 7
    GROUP BY month_key
    ORDER BY month_key ASC;
    """)

    rows = cur.fetchall()
    conn.close()

    labels = []
    totals = []
    flagged = []
    counts = []
    items = []

    for r in rows:
        key = r["month_key"]
        try:
            dt = datetime.strptime(key, "%Y-%m")
            label = dt.strftime("%b %y")
        except Exception:
            label = key

        labels.append(label)
        totals.append(round(float(r["total"]), 2))
        flagged.append(round(float(r["flagged"]), 2))
        counts.append(int(r["count"]))
        items.append({
            "month": label,
            "sortKey": key,
            "total": round(float(r["total"]), 2),
            "flagged": round(float(r["flagged"]), 2),
            "count": int(r["count"])
        })

    return {
        "labels": labels,
        "totals": totals,
        "flagged": flagged,
        "counts": counts,
        "items": items
    }


def get_category_stats(db_path: Optional[str] = None) -> Dict[str, Any]:
    """Calculates category allocation and anomaly distribution for Doughnut & Bar Charts."""
    conn = get_connection(db_path)
    cur = conn.cursor()

    cur.execute("""
    SELECT 
        category,
        COUNT(*) as count,
        COALESCE(SUM(amount), 0.0) as total,
        COALESCE(SUM(CASE WHEN risk_level = 'High' OR status = 'flagged' OR status = 'rejected' THEN 1 ELSE 0 END), 0) as flagged_count
    FROM expenses
    GROUP BY category
    ORDER BY total DESC;
    """)

    rows = cur.fetchall()
    conn.close()

    labels = [r["category"] for r in rows]
    totals = [round(float(r["total"]), 2) for r in rows]
    counts = [int(r["count"]) for r in rows]
    flagged_counts = [int(r["flagged_count"]) for r in rows]

    return {
        "labels": labels,
        "totals": totals,
        "counts": counts,
        "flaggedCounts": flagged_counts
    }


def get_alerts(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves high-risk alerts for the dashboard alerts panel."""
    conn = get_connection(db_path)
    cur = conn.cursor()

    cur.execute("""
    SELECT * FROM expenses
    WHERE risk_level = 'High' OR status = 'flagged'
    ORDER BY date DESC, time DESC
    LIMIT 20;
    """)

    rows = cur.fetchall()
    conn.close()

    alerts = []
    for r in rows:
        reasons = []
        try:
            reasons = json.loads(r["reasons"])
        except Exception:
            reasons = [r["reasons"]] if r["reasons"] else []

        alerts.append({
            "id": r["id"],
            "employee": r["employee"],
            "department": r["department"],
            "category": r["category"],
            "amount": float(r["amount"]),
            "date": r["date"],
            "time": r["time"],
            "status": r["status"],
            "riskScore": int(r["risk_score"]),
            "riskLevel": r["risk_level"],
            "fuzzyScore": float(r["fuzzy_score"]),
            "anomalyScore": float(r["anomaly_score"]),
            "ruleScore": float(r["rule_score"]),
            "reasons": reasons
        })

    return alerts


if __name__ == "__main__":
    seed_database_if_empty()
    stats = get_dashboard_stats()
    print("Database Initialized & Seeded Successfully!")
    print(f"Total Transactions: {stats['totalExpenses']} | Total Volume: ${stats['totalAmount']:,.2f} | Avg Risk: {stats['avgRiskScore']}/100")
