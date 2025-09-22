# main.py — /audit, /score, /score-bulk, /optimize
from fastapi import FastAPI, Query, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import json
import os
from supabase import create_client, Client
from fastapi.middleware.cors import CORSMiddleware   # 👈 ADD THIS LINE

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

from scoring import score_website
from optimizer import optimize_site
from audit import analyze


app = FastAPI()

# ✅ Enable CORS so your frontend (tryevika.com) can call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://preview--ascentiq-pro.lovable.app",   # Lovable preview links
        "https://*.lovable.dev",   # Lovable dev links
        "https://tryevika.com",    # your live site
        "http://localhost:3000",   # local dev testing
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


@app.post("/process")
async def process(req: AuditRequest):
    try:
        print("DEBUG: NEW PROCESS DEPLOYED")
            
        # 1️⃣ Run audit
        audit_results = analyze(req.url)
        
        # 2️⃣ Run score correctly
        score_results = score_website(audit_results, detail=True)
        seo_score = score_results.get("seo_score")
        ai_score = score_results.get("ai_score")
        combined_score = score_results.get("combined_score")
        
        # 3️⃣ Run optimization
        optimize_results = optimize_site(audit_results, limit=10, detail=True)
            
        # 4️⃣ Insert into sites (once)
        site_insert = supabase.table("sites").insert({"url": req.url}).execute()
        site_id = site_insert.data[0]["id"]
         
        # 5️⃣ Insert into audits
        supabase.table("audits").insert({
            "site_id": site_id,
            "url": req.url,
            "results": audit_results
        }).execute()
        
        # 6️⃣ Insert into optimizations
        supabase.table("optimizations").insert({
            "site_id": site_id,
            "url": req.url,
            "results": optimize_results
        }).execute()
        
        # 7️⃣ Insert into scores
        supabase.table("scores").insert({
            "site_id": site_id,
            "seo_score": seo_score,
            "ai_score": ai_score,
            "combined_score": combined_score,
            "results": score_results
        }).execute()
        
        # 8️⃣ Return clean response
        return {
            "url": req.url,
            "audit": audit_results,
            "score": score_results,
            "optimize": optimize_results
        }
        
    except Exception as e:
        return {"error": "Process failed", "details": str(e)}

