# main.py — /audit, /score, /score-bulk, /optimize
from fastapi import FastAPI, Query, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import json

from scoring import score_website
from optimizer import optimize_site
from pyseoanalyzer import analyze

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
        # Call pyseoanalyzer directly in Python
results = analyze(
    req.url,
    follow_links=False
)
        return results
    except Exception as e:
        return {"error": str(e)}

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

