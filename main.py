# main.py — /audit, /score, /score-bulk, /optimize
from fastapi import FastAPI, Query, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import subprocess, json, os

from scoring import score_website
from optimizer import optimize_site

app = FastAPI()

# ---------- models ----------
class AuditRequest(BaseModel):
    url: str

class ScoreRequest(BaseModel):
    url: Optional[str] = None
    audit: Optional[Dict[str, Any]] = None

class BulkScoreRequest(BaseModel):
    urls: List[str]

class OptimizeRequest(BaseModel):
    url: Optional[str] = None
    audit: Optional[Dict[str, Any]] = None
    limit: int = 10

# ---------- /audit ----------
@app.post("/audit")
async def audit(req: AuditRequest):
    try:
        proc = subprocess.run(
            ["python3", "-m", "pyseoanalyzer", req.url, "-f", "json"],
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
            errors="replace",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"}
        )
        try:
            return json.loads(proc.stdout)
        except json.JSONDecodeError:
            return {"error": "Could not parse JSON output", "raw": proc.stdout}
    except subprocess.CalledProcessError as e:
        return {"error": e.stderr or e.stdout or "Analyzer failed"}

# ---------- /score (GET) ----------
@app.get("/score")
async def score_get(
    url: str = Query(..., description="Page URL to audit and score"),
    detail: int = Query(0, description="Set 1 to include per-page details")
):
    audit_result = await audit(AuditRequest(url=url))  # direct function call
    if "error" in audit_result:
        return JSONResponse(status_code=500, content=audit_result)
    audit_data = audit_result.get("data", audit_result)
    results = score_website(audit_data, detail=bool(detail))
    return {"url": url, **results}

# ---------- /score (POST) ----------
@app.post("/score")
async def score_post(
    payload: ScoreRequest = Body(...),
    detail: int = Query(0, description="Set 1 to include per-page details")
):
    if payload.audit:
        audit_data = payload.audit
        url = payload.url or ""
    elif payload.url:
        audit_result = await audit(AuditRequest(url=payload.url))
        if "error" in audit_result:
            return JSONResponse(status_code=500, content=audit_result)
        audit_data = audit_result.get("data", audit_result)
        url = payload.url
    else:
        return JSONResponse(status_code=400, content={"error": "Provide either 'url' or 'audit'."})

    results = score_website(audit_data, detail=bool(detail))
    return {"url": url, **results}

# ---------- /score-bulk ----------
@app.post("/score-bulk")
async def score_bulk(
    payload: BulkScoreRequest = Body(...),
    detail: int = Query(0, description="Set 1 to include per-page details")
):
    output = []
    for u in payload.urls:
        try:
            audit_result = await audit(AuditRequest(url=u))
            if "error" in audit_result:
                output.append({"url": u, "error": audit_result["error"]})
                continue
            data = audit_result.get("data", audit_result)
            scores = score_website(data, detail=bool(detail))
            output.append({"url": u, **scores})
        except Exception as e:
            output.append({"url": u, "error": str(e)})
    return {"results": output}

# ---------- /optimize ----------
@app.get("/optimize")
async def optimize_get(
    url: str = Query(...),
    limit: int = Query(10, ge=1, le=50)
):
    audit_result = await audit(AuditRequest(url=url))
    if "error" in audit_result:
        return JSONResponse(status_code=500, content=audit_result)
    data = audit_result.get("data", audit_result)
    out = optimize_site(data, limit=limit, detail=True)
    return {"url": url, **out}

@app.post("/optimize")
async def optimize_post(
    payload: OptimizeRequest = Body(...),
    limit: int = Query(10, ge=1, le=50)
):
    if payload.audit:
        data = payload.audit
        url = payload.url or ""
    elif payload.url:
        audit_result = await audit(AuditRequest(url=payload.url))
        if "error" in audit_result:
            return JSONResponse(status_code=500, content=audit_result)
        data = audit_result.get("data", audit_result)
        url = payload.url
    else:
        return JSONResponse(status_code=400, content={"error": "Provide either 'url' or 'audit'."})

    out = optimize_site(data, limit=limit or payload.limit or 10, detail=True)
    return {"url": url, **out}

