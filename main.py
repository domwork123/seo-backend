# main.py — /audit, /score, /score-bulk, /optimize
from fastapi import FastAPI, Query, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import json
import os
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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
        results = analyze(req.url)  # no extra args

        # Save audit to Supabase
        supabase.table("audits").insert({
            "url": req.url,
            "results": results  # ✅ column name matches schema
        }).execute()

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

            # Save scores to Supabase ✅
            supabase.table("scores").insert({
                "url": u,
                "seo_score": scores.get("seo_score"),
                "ai_score": scores.get("ai_score"),
                "combined_score": scores.get("combined_score"),
                "details": scores  # put full JSON into details column
            }).execute()

            output.append({"url": u, **scores})
        except Exception as e:
            output.append({"url": u, "error": str(e)})

    return {"results": output}


# ---------- /optimize ----------
@app.post("/optimize")
async def optimize_post(
    payload: OptimizeRequest = Body(...),
    limit: int = Query(10, ge=1, le=50)
):
    try:
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
            return JSONResponse(
                status_code=400,
                content={"error": "Provide either 'url' or 'audit'."}
            )

        out = optimize_site(data, limit=limit or payload.limit or 10, detail=True)

        # Save optimizations to Supabase ✅
        supabase.table("optimizations").insert({
            "url": url,
            "results": out
        }).execute()

        return {"url": url, **out}
    except Exception as e:
        return {"error": str(e)}


# ---------- /process ----------
@app.post("/process")
async def process(req: AuditRequest):
    try:
        # 1. Run audit
        audit_result = await audit(req)
        if "error" in audit_result:
            return {"error": "Audit failed", "details": audit_result}

        # Save audit
        supabase.table("audits").insert({
            "url": req.url,
            "results": audit_result
        }).execute()

        # 2. Run score
        scores = score_website(audit_result, detail=True)

        # Save scores
        supabase.table("scores").insert({
            "url": req.url,
            "seo_score": scores.get("seo_score"),
            "ai_score": scores.get("ai_score"),
            "combined_score": scores.get("combined_score"),
            "details": scores
        }).execute()

        # 3. Run optimize
        optimizations = optimize_site(audit_result, limit=10, detail=True)

        # Save optimizations
        supabase.table("optimizations").insert({
            "url": req.url,
            "results": optimizations
        }).execute()

        # 4. Build final response
        return {
            "url": req.url,
            "seo_score": scores.get("seo_score"),
            "ai_score": scores.get("ai_score"),
            "combined_score": scores.get("combined_score"),
            "pages_evaluated": scores.get("pages_evaluated"),
            "audit": audit_result,
            "optimizations": optimizations.get("suggestions", []),
        }

    except Exception as e:
        return {"error": str(e)}

