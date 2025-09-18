# main.py — /audit (UTF-8), /score (detail), /score-bulk, /optimize
from fastapi import FastAPI, Query, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import subprocess, json, os
import httpx

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
            return JSONResponse(status_code=500, content={"error":"Could not parse JSON output", "raw": proc.stdout})
    except subprocess.CalledProcessError as e:
        return JSONResponse(status_code=500, content={"error": e.stderr or e.stdout or "Analyzer failed"})

# ---------- /score (GET) ----------
@app.get("/score")
async def score_get(
    url: str = Query(..., description="Page URL to audit and score"),
    timeout: int = Query(180, ge=10, le=600),
    detail: int = Query(0, description="Set 1 to include per-page details")
):
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post("http://127.0.0.1:8000/audit", json={"url": url})
        r.raise_for_status()
        audit = r.json()
    audit_data = audit.get("data", audit)
    results = score_website(audit_data, detail=bool(detail))
    return {"url": url, **results}

# ---------- /score (POST) ----------
@app.post("/score")
async def score_post(
    payload: ScoreRequest = Body(...),
    timeout: int = Query(180, ge=10, le=600),
    detail: int = Query(0, description="Set 1 to include per-page details")
):
    if payload.audit:
        audit_data = payload.audit
        url = payload.url or ""
    elif payload.url:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post("http://127.0.0.1:8000/audit", json={"url": payload.url})
            r.raise_for_status()
            audit = r.json()
        audit_data = audit.get("data", audit)
        url = payload.url
    else:
        return JSONResponse(status_code=400, content={"error":"Provide either 'url' or 'audit'."})
    results = score_website(audit_data, detail=bool(detail))
    return {"url": url, **results}

# ---------- /score-bulk ----------
@app.post("/score-bulk")
async def score_bulk(
    payload: BulkScoreRequest = Body(...),
    timeout: int = Query(180, ge=10, le=600),
    detail: int = Query(0, description="Set 1 to include per-page details")
):
    output = []
    async with httpx.AsyncClient(timeout=timeout) as client:
        for u in payload.urls:
            try:
                r = await client.post("http://127.0.0.1:8000/audit", json={"url": u})
                r.raise_for_status()
                audit = r.json()
                data = audit.get("data", audit)
                scores = score_website(data, detail=bool(detail))
                output.append({"url": u, **scores})
            except Exception as e:
                output.append({"url": u, "error": str(e)})
    return {"results": output}

# ---------- /optimize ----------
@app.get("/optimize")
async def optimize_get(
    url: str = Query(...),
    limit: int = Query(10, ge=1, le=50),
    timeout: int = Query(180, ge=10, le=600)
):
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post("http://127.0.0.1:8000/audit", json={"url": url})
        r.raise_for_status()
        audit = r.json()
    data = audit.get("data", audit)
    out = optimize_site(data, limit=limit, detail=True)
    return {"url": url, **out}

@app.post("/optimize")
async def optimize_post(
    payload: OptimizeRequest = Body(...),
    limit: int = Query(10, ge=1, le=50),
    timeout: int = Query(180, ge=10, le=600)
):
    if payload.audit:
        data = payload.audit
        url = payload.url or ""
    elif payload.url:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post("http://127.0.0.1:8000/audit", json={"url": payload.url})
            r.raise_for_status()
            audit = r.json()
        data = audit.get("data", audit)
        url = payload.url
    else:
        return JSONResponse(status_code=400, content={"error":"Provide either 'url' or 'audit'."})

    out = optimize_site(data, limit=limit or payload.limit or 10, detail=True)
    return {"url": url, **out}

