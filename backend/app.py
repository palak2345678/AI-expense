"""
FastAPI Production Backend for AI Expense Audit & Fraud Detection Platform
Academic Course: Soft Computing / Full-Stack Engineering

Key Capabilities:
1. End-to-End AI/ML Inference Pipeline:
   - Soft Computing: Mamdani Fuzzy Inference System (45%)
   - Machine Learning: Unsupervised Isolation Forest (25%)
   - Deterministic Rule Engine: Exact duplicates, split invoicing, policy limits (30%)
2. Persistent SQLite Database: Real transactions, alerts, and live dashboard KPI aggregations.
3. Full REST API Contract matching the deployed Vercel frontend.
4. Local Static File Serving: Directly serves the complete frontend application at http://localhost:5001.
5. Permissive CORS Middleware: Allows seamless cross-origin requests from Vercel deployments.
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

try:
    from backend.database import (
        seed_database_if_empty,
        insert_expense,
        get_all_expenses,
        update_expense_status,
        get_dashboard_stats,
        get_monthly_stats,
        get_category_stats,
        get_alerts
    )
except (ImportError, ModuleNotFoundError):
    from database import (
        seed_database_if_empty,
        insert_expense,
        get_all_expenses,
        update_expense_status,
        get_dashboard_stats,
        get_monthly_stats,
        get_category_stats,
        get_alerts
    )

try:
    from models.hybrid_evaluator import HybridExpenseFraudEvaluator
except (ImportError, ModuleNotFoundError):
    from hybrid_evaluator import HybridExpenseFraudEvaluator

# Initialize database on startup
seed_database_if_empty()

# Initialize AI/ML Hybrid Evaluation Engine
evaluator = HybridExpenseFraudEvaluator()

# Train Anomaly Detector using historical database records
try:
    historical_data = get_all_expenses()
    evaluator.fit_anomaly_detector(historical_data)
except Exception as e:
    print(f"Warning: Initial anomaly detector fit deferred: {e}")

app = FastAPI(
    title="AuditAI Expense & Fraud Detection Platform",
    description="Soft Computing & ML Powered Autonomous Expense Auditing System",
    version="2.0.0"
)

# CORS Configuration: allow localhost & Vercel deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic Schemas for Request Validation
class ExpenseSubmission(BaseModel):
    employee: str = Field(..., min_length=2, description="Employee Full Name")
    department: Optional[str] = Field("General", description="Corporate Department")
    category: str = Field(..., min_length=2, description="Expense Category")
    amount: float = Field(..., gt=0.0, description="Transaction Amount in USD")
    date: str = Field(..., description="Expense Date (YYYY-MM-DD)")
    time: Optional[str] = Field("12:00", description="Submission Time (HH:MM)")
    description: str = Field(..., min_length=3, description="Business Purpose Justification")
    has_receipt: Optional[bool] = Field(True, description="Receipt Documentation Attached")
    receipt_hash: Optional[str] = Field("", description="Unique Document Hash")


class StatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(approved|rejected|flagged|pending)$")


# -------------------------------------------------------------------------
# REST API Endpoints
# -------------------------------------------------------------------------

@app.get("/health", summary="Health Check")
def health_check():
    """Returns service health and active Soft Computing engine status."""
    return {
        "status": "healthy",
        "service": "AuditAI Soft Computing Backend API",
        "version": "2.0.0",
        "engine": "Mamdani Fuzzy Logic + Isolation Forest + Deterministic Rules",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@app.get("/api/expenses", summary="List Audited Expenses")
def list_expenses(
    category: str = Query("all", description="Category filter"),
    risk: str = Query("all", description="Risk level filter"),
    search: str = Query("", description="Search term")
):
    """Retrieves audited expenses matching filter criteria."""
    return get_all_expenses(category=category, risk=risk, search=search)


@app.post("/api/expenses", status_code=status.HTTP_201_CREATED, summary="Submit & Audit Expense")
def create_and_audit_expense(submission: ExpenseSubmission):
    """
    Submits an expense claim, invokes genuine Soft Computing Mamdani Fuzzy Inference,
    ML Anomaly Detection, and deterministic rule auditing, stores the record persistently,
    and returns the complete risk assessment.
    """
    # Generate unique transaction ID
    all_current = get_all_expenses()
    existing_ids = [int(e["id"].replace("EXP-", "")) for e in all_current if "EXP-" in e["id"] and e["id"].replace("EXP-", "").isdigit()]
    next_num = (max(existing_ids) + 1) if existing_ids else 1001
    expense_id = f"EXP-{next_num}"

    # Generate synthetic receipt hash if none provided
    receipt_hash = submission.receipt_hash.strip()
    if not receipt_hash:
        receipt_hash = f"HASH-{abs(hash(expense_id + submission.employee)) % 9000 + 1000}" if submission.has_receipt else "NO_RECEIPT"

    expense_data = {
        "id": expense_id,
        "employee": submission.employee.strip(),
        "department": submission.department.strip() if submission.department else "General",
        "category": submission.category.strip(),
        "amount": round(float(submission.amount), 2),
        "date": submission.date.strip(),
        "time": submission.time.strip() if submission.time else "12:00",
        "description": submission.description.strip(),
        "has_receipt": bool(submission.has_receipt),
        "receipt_hash": receipt_hash
    }

    # Execute Multi-Factor Hybrid AI Audit
    assessment = evaluator.evaluate(expense_data, historical_expenses=all_current)

    # Build persistent record
    record = {
        **expense_data,
        "status": assessment["status"],
        "riskScore": assessment["risk_score"],
        "riskLevel": assessment["risk_level"],
        "fuzzy_score": assessment["sub_scores"]["fuzzy_risk_score"],
        "anomaly_score": assessment["sub_scores"]["anomaly_risk_score"],
        "rule_score": assessment["sub_scores"]["rule_risk_score"],
        "reasons": assessment["reasons"],
        "nextAction": assessment["next_action"],
        "fuzzyDetails": assessment["fuzzy_details"],
        "ruleDetails": assessment["rule_details"],
        "anomalyDetails": assessment["anomaly_details"],
        "createdAt": datetime.utcnow().isoformat() + "Z"
    }

    # Persist in SQLite
    insert_expense(record)

    return record


@app.patch("/api/expenses/{expense_id}/status", summary="Update Expense Status")
def update_status(expense_id: str, body: StatusUpdate):
    """Updates expense status (approved / rejected / flagged)."""
    success = update_expense_status(expense_id, body.status)
    if not success:
        raise HTTPException(status_code=404, detail="Expense record not found")
    return {"id": expense_id, "status": body.status, "updated": True}


@app.get("/api/stats", summary="KPI Metrics")
def stats():
    """Returns high-level aggregate KPI statistics for dashboard stat cards."""
    return get_dashboard_stats()


@app.get("/api/stats/monthly", summary="Monthly Expenditure Trajectory")
def monthly_stats():
    """Returns monthly spending and flagged losses for Chart.js line graph."""
    return get_monthly_stats()


@app.get("/api/stats/categories", summary="Category Breakdown")
def category_stats():
    """Returns category volume and anomaly distribution for Doughnut & Bar charts."""
    return get_category_stats()


@app.get("/api/alerts", summary="High-Risk Fraud Alerts")
def alerts():
    """Returns high-priority fraud alerts requiring immediate auditor intervention."""
    return get_alerts()


# -------------------------------------------------------------------------
# Robust Static Asset & Frontend Serving
# -------------------------------------------------------------------------
search_dirs = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "frontend")),
    os.path.abspath(os.path.dirname(__file__)),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
]

def find_file(relative_subpath: str) -> Optional[str]:
    """Finds a static file across potential frontend directories or flat layouts."""
    flat_name = os.path.basename(relative_subpath)
    for base in search_dirs:
        # Check direct path e.g. base/css/style.css
        p = os.path.join(base, relative_subpath)
        if os.path.isfile(p):
            return p
        # Check flat path e.g. base/style.css
        p_flat = os.path.join(base, flat_name)
        if os.path.isfile(p_flat):
            return p_flat
    return None

# Mount directories if present
mounted_dirs = set()
for base in search_dirs:
    for sub in ["css", "js", "assets"]:
        sub_path = os.path.join(base, sub)
        if os.path.isdir(sub_path) and sub not in mounted_dirs:
            try:
                app.mount(f"/{sub}", StaticFiles(directory=sub_path), name=f"static_{sub}_{base}")
                mounted_dirs.add(sub)
            except Exception:
                pass

# Explicit fallback handlers for css, js, and html so nothing ever 404s
@app.get("/css/{file_name}", include_in_schema=False)
def serve_css(file_name: str):
    path = find_file(os.path.join("css", file_name)) or find_file(file_name)
    if path:
        return FileResponse(path, media_type="text/css")
    raise HTTPException(status_code=404, detail=f"CSS file '{file_name}' not found")

@app.get("/style.css", include_in_schema=False)
def serve_root_style():
    path = find_file("style.css") or find_file(os.path.join("css", "style.css"))
    if path:
        return FileResponse(path, media_type="text/css")
    raise HTTPException(status_code=404, detail="Stylesheet 'style.css' not found")

@app.get("/js/{file_name}", include_in_schema=False)
def serve_js(file_name: str):
    path = find_file(os.path.join("js", file_name)) or find_file(file_name)
    if path:
        return FileResponse(path, media_type="application/javascript")
    raise HTTPException(status_code=404, detail=f"JavaScript file '{file_name}' not found")

@app.get("/", include_in_schema=False)
def serve_index():
    path = find_file("index.html")
    if path:
        return FileResponse(path)
    return {"message": "AuditAI API Online. Visit /docs for Swagger UI or /dashboard for Auditor Console."}

@app.get("/index.html", include_in_schema=False)
def serve_index_html():
    path = find_file("index.html")
    if path:
        return FileResponse(path)
    raise HTTPException(status_code=404, detail="index.html not found")

@app.get("/dashboard", include_in_schema=False)
def serve_dashboard():
    path = find_file("dashboard.html")
    if path:
        return FileResponse(path)
    raise HTTPException(status_code=404, detail="dashboard.html not found")

@app.get("/dashboard.html", include_in_schema=False)
def serve_dashboard_html():
    path = find_file("dashboard.html")
    if path:
        return FileResponse(path)
    raise HTTPException(status_code=404, detail="dashboard.html not found")


if __name__ == "__main__":
    import uvicorn
    print("Starting AuditAI Production FastAPI Server on http://localhost:5001 ...")
    uvicorn.run("backend.app:app", host="0.0.0.0", port=5001, reload=False)
