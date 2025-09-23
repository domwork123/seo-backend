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
from audit import audit_site
from llm_optimizer import optimize_with_llm


app = FastAPI()

# ✅ Enable CORS so your frontend (tryevika.com) can call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://preview--ascentiq-pro.lovable.app",   # Lovable preview links
        "https://ascentiq-pro.lovable.app",           # Lovable production
        "https://*.lovable.dev",   # Lovable dev links
        "https://tryevika.com",    # your live site
        "http://localhost:3000",   # local dev testing
        "http://127.0.0.1:3000"    # local dev testing
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
async def audit(req: AuditRequest = Body(...), max_pages: int = Query(50, ge=1, le=200)):
    url = req.url
    if not url:
        return {"error": "Missing 'url'."}

    # Full-site crawl (sitemap first, fallback to homepage links)
    result = await audit_site(url, max_pages=max_pages)

    # (optional) persist to Supabase
    try:
        supabase.table("audits").insert({
            "url": url,
            "results": result
        }).execute()
    except Exception:
        # Allow running without Supabase configured
        pass

    return result


# ---------- /score-bulk ----------
@app.post("/score-bulk")
async def score_bulk(
    payload: BulkScoreRequest = Body(...),
    detail: int = Query(0, description="Set 1 to include per-page details")
):
    output = []
    for u in payload.urls:
        try:
            # Run audit directly to avoid route-call mismatches
            audit_result = await audit_site(u, max_pages=50)
            if "error" in audit_result:
                output.append({"url": u, "error": audit_result["error"]})
                continue

            data = audit_result.get("data", audit_result)
            scores = score_website(data, detail=bool(detail))

            # Save scores to Supabase ✅
            try:
                supabase.table("scores").insert({
                    "url": u,
                    "seo_score": scores.get("seo_score"),
                    "ai_score": scores.get("ai_score"),
                    "combined_score": scores.get("combined_score"),
                    "details": scores  # put full JSON into details column
                }).execute()
            except Exception:
                pass

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
            audit_result = await audit_site(payload.url, max_pages=50)
            if isinstance(audit_result, dict) and "error" in audit_result:
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
        try:
            supabase.table("optimizations").insert({
                "url": url,
                "results": out
            }).execute()
        except Exception:
            pass

        return {"url": url, **out}
    except Exception as e:
        return {"error": str(e)}


@app.post("/process")
async def process(req: AuditRequest):
    try:
        print("DEBUG: NEW PROCESS DEPLOYED")
            
        # 1️⃣ Run audit
        audit_results = await audit_site(req.url, max_pages=50)
        
        # 2️⃣ Run score correctly
        score_results = score_website(audit_results, detail=True)
        seo_score = score_results.get("seo_score")
        ai_score = score_results.get("ai_score")
        combined_score = score_results.get("combined_score")
        
        # 3️⃣ Run optimization
        optimize_results = optimize_site(audit_results, limit=10, detail=True)
            
        # 4️⃣ Insert into sites (once)
        site_id = None
        try:
            site_insert = supabase.table("sites").insert({"url": req.url}).execute()
            site_id = site_insert.data[0]["id"] if getattr(site_insert, "data", None) else None
        except Exception:
            pass
         
        # 5️⃣ Insert into audits
        try:
            supabase.table("audits").insert({
                "site_id": site_id,
                "url": req.url,
                "results": audit_results
            }).execute()
        except Exception:
            pass
        
        # 6️⃣ Insert into optimizations
        try:
            supabase.table("optimizations").insert({
                "site_id": site_id,
                "url": req.url,
                "results": optimize_results
            }).execute()
        except Exception:
            pass
        
        # 7️⃣ Insert into scores
        try:
            supabase.table("scores").insert({
                "site_id": site_id,
                "seo_score": seo_score,
                "ai_score": ai_score,
                "combined_score": combined_score,
                "results": score_results
            }).execute()
        except Exception:
            pass
        
        # 8️⃣ Return clean response
        return {
            "url": req.url,
            "audit": audit_results,
            "score": score_results,
            "optimize": optimize_results
        }
        
    except Exception as e:
        return {"error": "Process failed", "details": str(e)}

# ---------- /version ----------
@app.get("/version")
async def version():
    return {"version": "1.0.0", "status": "active"}

# ---------- /health ----------
@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}

# ---------- /optimize-llm ----------
@app.post("/optimize-llm")
async def optimize_llm(req: AuditRequest = Body(...)):
    try:
        url = req.url
        if not url:
            return {"error": "Missing 'url'."}

        print(f"DEBUG: Starting LLM optimization for {url}")
        
        # 1. Get audit data with comprehensive error handling
        try:
            audit_result = await audit_site(url, max_pages=50)
            print(f"DEBUG: Audit completed for {url}")
        except Exception as audit_error:
            print(f"DEBUG: Audit failed for {url}: {audit_error}")
            # Return minimal audit data to prevent complete failure
            audit_result = {
                "url": url,
                "pages": [{"url": url, "title": "", "meta": "", "h1": [], "h2": [], "h3": [], "word_count": 0}],
                "languages": ["en"],
                "error": f"Audit failed: {str(audit_error)}"
            }
        
        # 2. Get base scores with error handling
        try:
            scores = score_website(audit_result)
            print(f"DEBUG: Scoring completed for {url}")
        except Exception as score_error:
            print(f"DEBUG: Scoring failed for {url}: {score_error}")
            # Return minimal scores to prevent complete failure
            scores = {
                "scores": {
                    "seo": 0,
                    "aeo": 0,
                    "geo": 0,
                    "accessibility": 0,
                    "technical": 0,
                    "overall": 0
                },
                "seo_score": 0,
                "ai_score": 0,
                "combined_score": 0,
                "error": f"Scoring failed: {str(score_error)}"
            }
        
        # 3. Generate LLM-powered optimizations with error handling
        try:
            llm_optimizations = await optimize_with_llm(audit_result, scores)
            print(f"DEBUG: LLM optimization completed for {url}")
        except Exception as llm_error:
            print(f"DEBUG: LLM optimization failed for {url}: {llm_error}")
            # Return base optimizations as fallback
            try:
                llm_optimizations = optimize_site(audit_result)
                print(f"DEBUG: Using base optimizations as fallback for {url}")
            except Exception as base_error:
                print(f"DEBUG: Base optimization also failed for {url}: {base_error}")
                # Return minimal optimizations
                llm_optimizations = {
                    "pages_optimized": [],
                    "error": f"All optimization methods failed: {str(llm_error)}"
                }
        
        return {
            "url": url,
            "audit": audit_result,
            "scores": scores,
            "optimize": llm_optimizations
        }
        
    except Exception as e:
        print(f"DEBUG: Complete failure for {req.url}: {e}")
        return {
            "error": "LLM optimization failed", 
            "details": str(e),
            "url": req.url,
            "audit": {"url": req.url, "pages": [], "error": "Complete failure"},
            "scores": {"scores": {"overall": 0}, "error": "Complete failure"},
            "optimize": {"pages_optimized": [], "error": "Complete failure"}
        }

# ---------- /apply-wordpress ----------
class WordPressApplyRequest(BaseModel):
    url: str
    wp_site_url: str
    wp_username: str
    wp_password: str
    optimizations: Dict[str, Any]

@app.post("/apply-wordpress")
async def apply_wordpress(req: WordPressApplyRequest = Body(...)):
    try:
        from wordpress_apply import WordPressConfig, apply_to_wordpress
        
        # Create WordPress config
        wp_config = WordPressConfig(
            site_url=req.wp_site_url,
            username=req.wp_username,
            password=req.wp_password,
            api_endpoint=req.wp_site_url.rstrip('/')
        )
        
        # Apply optimizations
        results = await apply_to_wordpress(wp_config, req.optimizations)
        
        return {
            "success": results["success"],
            "applied": results["applied"],
            "failed": results["failed"],
            "errors": results["errors"]
        }
        
    except Exception as e:
        return {"error": "WordPress apply failed", "details": str(e)}

