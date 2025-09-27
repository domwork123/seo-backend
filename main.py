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

from aeo_geo_scoring import score_website
from aeo_geo_optimizer import detect_faq, extract_images, optimize_meta_description, run_llm_queries, check_geo_signals, generate_blog_post
from aeo_geo_audit import audit_site_aeo_geo, audit_single_page_aeo_geo
from audit import audit_site
from enhanced_audit import enhanced_audit_site
from query_analyzer import analyze_query_visibility
from scrapingbee_crawler import crawl_website_with_scrapingbee
from signal_extractor import extract_signals_from_pages
from supabase_schema import ensure_schema_exists, save_audit_data
import uuid
from datetime import datetime


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

class NewAuditRequest(BaseModel):
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

class QueryCheckRequest(BaseModel):
    site_id: str
    queries: Optional[List[str]] = None

class AuditRequest(BaseModel):
    url: str
    language: Optional[str] = "en"
    max_pages: Optional[int] = 50

# ---------- /audit ----------
@app.post("/audit")
async def audit(req: AuditRequest = Body(...)):
    """
    EVIKA SaaS audit endpoint that:
    1. Crawls website using ScrapingBee (15 pages max)
    2. Extracts AEO + GEO signals from all pages
    3. Saves everything to Supabase with unique site_id
    4. Returns structured overview with site_id
    """
    try:
        print(f"🚀 Starting EVIKA audit for: {req.url}")
        
        # Generate unique site_id for this audit
        site_id = str(uuid.uuid4())
        print(f"📋 Generated site_id: {site_id}")
        
        # Ensure Supabase schema exists
        print("🔧 Ensuring Supabase schema...")
        if not ensure_schema_exists():
            print("⚠️ Schema setup failed, continuing anyway...")
        
        # Step 1: Crawl website with ScrapingBee (15 pages max)
        print(f"🕷️ Crawling website with ScrapingBee...")
        crawl_result = crawl_website_with_scrapingbee(req.url, max_pages=15)
        
        if not crawl_result.get("success"):
            return {
                "error": f"Crawl failed: {crawl_result.get('error', 'Unknown error')}",
                "site_id": site_id
            }
        
        pages = crawl_result.get("pages", [])
        print(f"✅ Crawled {len(pages)} pages successfully")
        
        # Step 2: Extract signals from crawled data
        print(f"🔍 Extracting AEO + GEO signals...")
        signals = extract_signals_from_pages(pages)
        
        # Step 3: Save to Supabase
        print(f"💾 Saving to Supabase...")
        save_success = save_audit_data(site_id, req.url, pages, signals)
        
        if not save_success:
            print("⚠️ Failed to save to Supabase, but continuing...")
        
        # Step 4: Return structured JSON
        return {
            "site_id": site_id,
            "url": req.url,
            "brand_name": signals.get("brand_name", "Unknown"),
            "description": signals.get("description", ""),
            "products": signals.get("products", []),
            "location": signals.get("location", ""),
            "faqs": [faq.get("question", "") for faq in signals.get("faqs", [])],
            "topics": signals.get("topics", []),
            "competitors": signals.get("competitors", []),
            "pages_crawled": len(pages),
            "success": True
        }
        
    except Exception as e:
        print(f"❌ Audit failed: {e}")
        return {
            "error": f"Audit failed: {str(e)}",
            "site_id": site_id if 'site_id' in locals() else None
        }

# Legacy audit endpoint (keeping for backward compatibility)
@app.post("/audit-legacy")
async def audit_legacy(req: AuditRequest = Body(...), max_pages: int = Query(50, ge=1, le=200)):
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
        
        # 3️⃣ Run LLM-powered optimization
        try:
            optimize_results = await optimize_with_llm(audit_results, score_results)
            print(f"DEBUG: LLM optimization completed for {req.url}")
        except Exception as llm_error:
            print(f"DEBUG: LLM optimization failed for {req.url}: {llm_error}")
            # Fallback to base optimizations
            try:
                optimize_results = optimize_site(audit_results, limit=10, detail=True)
                print(f"DEBUG: Using base optimizations as fallback for {req.url}")
            except Exception as base_error:
                print(f"DEBUG: Base optimization also failed for {req.url}: {base_error}")
                optimize_results = {
                    "pages_optimized": [{
                        "url": req.url,
                        "new_title": "Add a compelling title tag",
                        "new_meta": "Add a descriptive meta description",
                        "new_h1": "Add a clear H1 heading",
                        "fallback": True,
                        "error": f"All optimization methods failed: {str(base_error)}"
                    }],
                    "error": f"Fallback optimizations provided due to: {str(base_error)}"
                }
            
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

# ---------- /query-site ----------
@app.get("/query-site/{site_id}")
async def query_site(site_id: str):
    """
    Query saved audit data by site_id
    """
    try:
        print(f"🔍 Querying site data for: {site_id}")
        
        # Get site info
        try:
            site_result = supabase.table("sites").select("*").eq("id", site_id).execute()
            site_data = site_result.data[0] if site_result.data else None
            print(f"📋 Site data found: {site_data is not None}")
        except Exception as e:
            print(f"❌ Error querying site: {e}")
            site_data = None
        
        # Get pages data
        try:
            pages_result = supabase.table("pages").select("*").eq("site_id", site_id).execute()
            pages_data = pages_result.data if pages_result.data else []
            print(f"📄 Pages data found: {len(pages_data)} pages")
        except Exception as e:
            print(f"❌ Error querying pages: {e}")
            pages_data = []
        
        # Get audit results
        try:
            audit_result = supabase.table("audits").select("*").eq("site_id", site_id).execute()
            audit_data = audit_result.data[0] if audit_result.data else None
            print(f"📊 Audit data found: {audit_data is not None}")
        except Exception as e:
            print(f"❌ Error querying audit: {e}")
            audit_data = None
        
        return {
            "site_id": site_id,
            "site_data": site_data,
            "pages_count": len(pages_data),
            "pages_data": pages_data,
            "audit_data": audit_data,
            "success": site_data is not None or len(pages_data) > 0 or audit_data is not None
        }
        
    except Exception as e:
        print(f"❌ Query failed: {e}")
        return {"error": f"Query failed: {str(e)}", "site_id": site_id}

# ---------- /list-sites ----------
@app.get("/list-sites")
async def list_sites():
    """
    List all saved sites
    """
    try:
        print(f"📋 Listing all sites...")
        
        # Get all sites
        try:
            sites_result = supabase.table("sites").select("*").order("created_at", desc=True).limit(10).execute()
            sites_data = sites_result.data if sites_result.data else []
            print(f"✅ Found {len(sites_data)} sites")
        except Exception as e:
            print(f"❌ Error listing sites: {e}")
            sites_data = []
        
        return {
            "sites": sites_data,
            "count": len(sites_data),
            "success": True
        }
        
    except Exception as e:
        print(f"❌ List sites failed: {e}")
        return {"error": f"List sites failed: {str(e)}"}

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
            # Return comprehensive fallback optimizations
            llm_optimizations = {
                "pages_optimized": [{
                    "url": url,
                    "page_type": "homepage",
                    "priority": "high",
                    "basic_seo": {
                        "new_title": "Add a compelling title tag (50-60 characters)",
                        "new_meta": "Add a descriptive meta description (150-160 characters)",
                        "new_h1": "Add a clear H1 heading",
                        "h2_suggestions": ["Add relevant H2 headings", "Structure content with H2s"],
                        "h3_suggestions": ["Add supporting H3 headings", "Break down content with H3s"]
                    },
                    "aeo_optimization": {
                        "faq_suggestions": [
                            {"question": "What is your main service?", "answer": "Provide a clear answer about your primary service or product"},
                            {"question": "How can customers contact you?", "answer": "Include contact information and methods"}
                        ],
                        "structured_data": "Add JSON-LD schema markup for your business type",
                        "ai_friendly_content": "Optimize content for AI search by using clear, structured information",
                        "answer_engine_tasks": ["Create FAQ section", "Add structured data", "Optimize for voice search"]
                    },
                    "geo_optimization": {
                        "local_seo_tasks": ["Add location information", "Optimize for local search"],
                        "hreflang_suggestions": "Implement hreflang if targeting multiple languages",
                        "location_signals": "Add location-based keywords and content",
                        "geo_schema": "Add LocalBusiness schema markup"
                    },
                    "technical_seo": {
                        "schema_markup": "Add appropriate JSON-LD schema for your page type",
                        "canonical_suggestions": "Set up canonical URLs",
                        "internal_linking": "Create internal linking strategy",
                        "technical_tasks": ["Fix technical issues", "Optimize site structure"]
                    },
                    "content_optimization": {
                        "content_gaps": ["Identify content gaps", "Add missing information"],
                        "keyword_optimization": "Research and implement target keywords",
                        "content_structure": "Improve content structure and readability",
                        "user_intent": "Optimize for user search intent"
                    },
                    "performance_tasks": {
                        "image_optimization": ["Optimize images", "Add alt text"],
                        "speed_optimization": ["Improve page speed", "Optimize loading times"],
                        "mobile_optimization": ["Ensure mobile responsiveness", "Test mobile experience"]
                    },
                    "future_ai_optimization": {
                        "llm_search_preparation": "Prepare content for LLM search",
                        "ai_answer_optimization": "Optimize for AI answer snippets",
                        "voice_search_optimization": "Optimize for voice search queries",
                        "ai_crawlability": "Ensure AI crawlers can understand your content"
                    },
                    "fallback": True,
                    "error": f"Comprehensive fallback optimizations provided due to: {str(llm_error)}"
                }],
                "error": f"Fallback optimizations provided due to: {str(llm_error)}"
            }
            print(f"DEBUG: Using comprehensive fallback optimizations for {url}")
        
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

# ---------- Enhanced Audit with JavaScript Support ----------
@app.post("/optimize-llm-enhanced")
async def optimize_llm_enhanced(req: AuditRequest = Body(...)):
    """Enhanced optimization with JavaScript rendering for complex websites"""
    try:
        url = req.url
        if not url:
            return {"error": "Missing 'url'."}

        print(f"DEBUG: Starting enhanced LLM optimization for {url}")
        
        # 1. Get enhanced audit data with JavaScript rendering
        try:
            audit_result = await enhanced_audit_site(url, max_pages=50, use_js=True)
            print(f"DEBUG: Enhanced audit completed for {url}")
        except Exception as audit_error:
            print(f"DEBUG: Enhanced audit failed for {url}: {audit_error}")
            # Fallback to regular audit
            try:
                audit_result = await audit_site(url, max_pages=50)
                print(f"DEBUG: Fallback audit completed for {url}")
            except Exception as fallback_error:
                print(f"DEBUG: Both audits failed for {url}: {fallback_error}")
                audit_result = {
                    "url": url,
                    "pages": [{"url": url, "title": "", "meta": "", "h1": [], "h2": [], "h3": [], "word_count": 0}],
                    "languages": ["en"],
                    "error": f"All audit methods failed: {str(audit_error)}"
                }
        
        # 2. Get base scores with error handling
        try:
            scores = score_website(audit_result)
            print(f"DEBUG: Scoring completed for {url}")
        except Exception as score_error:
            print(f"DEBUG: Scoring failed for {url}: {score_error}")
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
            print(f"DEBUG: Enhanced LLM optimization completed for {url}")
        except Exception as llm_error:
            print(f"DEBUG: LLM optimization failed for {url}: {llm_error}")
            # Fallback to base optimizations
            try:
                llm_optimizations = optimize_site(audit_result)
                print(f"DEBUG: Using base optimizations as fallback for {url}")
            except Exception as base_error:
                print(f"DEBUG: Base optimization also failed for {url}: {base_error}")
                llm_optimizations = {
                    "pages_optimized": [{
                        "url": url,
                        "new_title": "Add a compelling title tag",
                        "new_meta": "Add a descriptive meta description",
                        "new_h1": "Add a clear H1 heading",
                        "fallback": True,
                        "error": f"All optimization methods failed: {str(llm_error)}"
                    }],
                    "error": f"Fallback optimizations provided due to: {str(llm_error)}"
                }
        
        return {
            "url": url,
            "audit": audit_result,
            "scores": scores,
            "optimize": llm_optimizations
        }
        
    except Exception as e:
        print(f"DEBUG: Complete enhanced failure for {req.url}: {e}")
        return {
            "url": req.url,
            "audit": {"url": req.url, "pages": [], "error": f"Complete enhanced failure: {str(e)}"},
            "scores": {"scores": {"overall": 0}, "error": f"Complete enhanced failure: {str(e)}"},
            "optimize": {"pages_optimized": [], "error": f"Complete enhanced failure: {str(e)}"}
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

@app.post("/optimize-aeo-geo")
async def optimize_aeo_geo(req: AuditRequest = Body(...)):
    """
    AEO + GEO focused optimization endpoint.
    Returns comprehensive AEO and GEO optimization suggestions.
    """
    try:
        url = req.url
        if not url:
            return {"error": "Missing 'url'."}

        print(f"DEBUG: Starting AEO + GEO optimization for {url}")
        
        # 1. Get audit data
        try:
            audit_result = await audit_site(url, max_pages=50)
            print(f"DEBUG: Audit completed for {url}")
        except Exception as audit_error:
            print(f"DEBUG: Audit failed for {url}: {audit_error}")
            audit_result = {
                "url": url,
                "pages": [{"url": url, "title": "", "meta": "", "h1": [], "h2": [], "h3": [], "word_count": 0, "content": "", "images": [], "schema": {"json_ld": []}, "hreflang": [], "nap": {}}],
                "languages": ["en"],
                "error": f"Audit failed: {str(audit_error)}"
            }
        
        # 2. Get AEO + GEO scores
        try:
            scores = score_website(audit_result)
            print(f"DEBUG: AEO + GEO scoring completed for {url}")
        except Exception as score_error:
            print(f"DEBUG: Scoring failed for {url}: {score_error}")
            scores = {
                "scores": {"aeo": 0, "geo": 0, "overall": 0},
                "aeo_score": 0,
                "geo_score": 0,
                "combined_score": 0,
                "error": f"Scoring failed: {str(score_error)}"
            }
        
        # 3. Generate AEO + GEO optimizations
        pages_optimized = []
        
        for page in audit_result.get("pages", []):
            page_url = page.get("url", url)
            
            # AEO Optimizations
            faq_analysis = detect_faq(page_url, page)
            image_analysis = extract_images(page_url, page)
            meta_optimization = optimize_meta_description(page.get("meta", ""), page)
            
            # GEO Optimizations
            geo_analysis = check_geo_signals(page_url, page)
            
            # Combine optimizations
            page_optimization = {
                "url": page_url,
                "page_type": "homepage" if page_url == url else "content",
                "priority": "high",
                "aeo_optimization": {
                    "faq_analysis": faq_analysis,
                    "image_analysis": image_analysis,
                    "meta_optimization": meta_optimization,
                    "suggestions": generate_aeo_suggestions(faq_analysis, image_analysis, meta_optimization)
                },
                "geo_optimization": {
                    "geo_analysis": geo_analysis,
                    "suggestions": geo_analysis.get("suggestions", [])
                }
            }
            
            pages_optimized.append(page_optimization)
        
        return {
            "url": url,
            "audit": audit_result,
            "scores": scores,
            "optimize": {
                "pages_optimized": pages_optimized,
                "aeo_focus": "Answer Engine Optimization for AI search",
                "geo_focus": "Geographic Optimization for local targeting"
            }
        }
        
    except Exception as e:
        print(f"DEBUG: AEO + GEO optimization failed for {req.url}: {e}")
        return {
            "error": "AEO + GEO optimization failed", 
            "details": str(e),
            "url": req.url
        }

def generate_aeo_suggestions(faq_analysis, image_analysis, meta_optimization):
    """Generate AEO optimization suggestions"""
    suggestions = []
    
    # FAQ suggestions
    if not faq_analysis.get("has_faq_content"):
        suggestions.append("Add FAQ section with common customer questions")
    if not faq_analysis.get("has_faq_schema"):
        suggestions.append("Add FAQ schema markup (JSON-LD) for better AI understanding")
    
    # Image suggestions
    if image_analysis.get("images_without_alt", 0) > 0:
        suggestions.append(f"Add alt text to {image_analysis['images_without_alt']} images")
    
    # Meta description suggestions
    suggestions.extend(meta_optimization.get("suggestions", []))
    
    return suggestions

@app.post("/generate-blog-post")
async def generate_blog_post_endpoint(req: dict = Body(...)):
    """Generate AEO-optimized blog post"""
    try:
        keyword = req.get("keyword", "")
        brand = req.get("brand", "")
        url = req.get("url", "")
        
        if not keyword or not brand:
            return {"error": "Missing 'keyword' or 'brand' parameter"}
        
        # Get page data for context
        try:
            audit_result = await audit_site(url, max_pages=1) if url else {"pages": [{"content": "", "title": ""}]}
            page_data = audit_result.get("pages", [{}])[0] if audit_result.get("pages") else {}
        except:
            page_data = {"content": "", "title": ""}
        
        blog_post = generate_blog_post(keyword, brand, page_data)
        
        return {
            "keyword": keyword,
            "brand": brand,
            "blog_post": blog_post,
            "aeo_optimized": True
        }
        
    except Exception as e:
        return {"error": "Blog post generation failed", "details": str(e)}

@app.post("/test-llm-queries")
async def test_llm_queries_endpoint(req: dict = Body(...)):
    """Test LLM query visibility"""
    try:
        brand = req.get("brand", "")
        queries = req.get("queries", [])
        url = req.get("url", "")
        
        if not brand:
            return {"error": "Missing 'brand' parameter"}
        
        # Get page data for context
        try:
            audit_result = await audit_site(url, max_pages=1) if url else {"pages": [{"content": "", "title": ""}]}
            page_data = audit_result.get("pages", [{}])[0] if audit_result.get("pages") else {}
        except:
            page_data = {"content": "", "title": ""}
        
        query_results = run_llm_queries(brand, queries, page_data)
        
        return {
            "brand": brand,
            "query_results": query_results,
            "visibility_analysis": "Test your brand's visibility in AI search results"
        }
        
    except Exception as e:
        return {"error": "LLM query testing failed", "details": str(e)}

@app.post("/audit-aeo-geo")
async def audit_aeo_geo(req: AuditRequest = Body(...)):
    """
    AEO + GEO focused audit endpoint.
    Comprehensive audit engine for Answer Engine Optimization and Geographic Optimization.
    """
    try:
        url = req.url
        if not url:
            return {"error": "Missing 'url'."}

        print(f"DEBUG: Starting AEO + GEO audit for {url}")
        
        # Get target language from request (default to 'en')
        target_language = getattr(req, 'language', 'en')
        max_pages = getattr(req, 'max_pages', 100)
        
        print(f"DEBUG: Parameters - language: {target_language}, max_pages: {max_pages}")
        
        # Run comprehensive AEO + GEO audit
        audit_result = await audit_site_aeo_geo(url, target_language, max_pages)
        
        print(f"DEBUG: AEO + GEO audit completed for {url}, pages: {audit_result.get('pages_analyzed', 0)}")
        
        return {
            "url": url,
            "audit": audit_result,
            "audit_type": "AEO + GEO Focused",
            "target_language": target_language
        }
        
    except Exception as e:
        print(f"DEBUG: AEO + GEO audit failed for {req.url}: {e}")
        return {
            "error": "AEO + GEO audit failed", 
            "details": str(e),
            "url": req.url
        }

@app.post("/audit-single-page")
async def audit_single_page(req: AuditRequest = Body(...)):
    """
    Single page AEO + GEO audit endpoint.
    Much simpler and more reliable than full website crawling.
    """
    try:
        url = req.url
        if not url:
            return {"error": "Missing 'url'."}

        print(f"DEBUG: Starting single page AEO + GEO audit for {url}")
        
        # Get target language from request (default to 'en')
        target_language = getattr(req, 'language', 'en')
        
        print(f"DEBUG: Parameters - language: {target_language}")
        
        # Run single page AEO + GEO audit
        audit_result = await audit_single_page_aeo_geo(url, target_language)
        
        print(f"DEBUG: Single page audit completed for {url}")
        
        return {
            "url": url,
            "audit": audit_result,
            "audit_type": "AEO + GEO Single Page",
            "target_language": target_language
        }
        
    except Exception as e:
        print(f"DEBUG: Single page audit failed for {req.url}: {e}")
        return {
            "error": "Single page audit failed", 
            "details": str(e),
            "url": req.url
        }

@app.post("/audit-full-website")
async def audit_full_website(req: AuditRequest = Body(...)):
    """
    Full website AEO + GEO audit endpoint using ScrapingBee.
    Crawls entire website and analyzes all pages.
    """
    try:
        url = req.url
        if not url:
            return {"error": "Missing 'url'."}

        print(f"DEBUG: Starting full website AEO + GEO audit for {url}")
        
        # Get target language and max pages from request
        target_language = getattr(req, 'language', 'en')
        max_pages = getattr(req, 'max_pages', 10)
        
        print(f"DEBUG: Parameters - language: {target_language}, max_pages: {max_pages}")
        
        # Run full website AEO + GEO audit using ScrapingBee
        audit_result = await audit_site_aeo_geo(url, target_language, max_pages)
        
        print(f"DEBUG: Full website audit completed for {url}")
        
        return {
            "url": url,
            "audit": audit_result,
            "audit_type": "AEO + GEO Full Website",
            "target_language": target_language,
            "max_pages": max_pages
        }
        
    except Exception as e:
        print(f"DEBUG: Full website audit failed for {req.url}: {e}")
        return {
            "error": "Full website audit failed", 
            "details": str(e),
            "url": req.url
        }

# ---------- /query-check ----------
@app.post("/query-check")
async def query_check(req: QueryCheckRequest = Body(...)):
    """
    Analyze how a brand appears in AI query responses
    
    Input:
    - url: Website URL to analyze
    - queries: Optional list of custom queries (if empty, auto-generate)
    
    Output:
    - Analysis results with AI responses and recommendations
    """
    try:
        print(f"🔍 Starting query visibility analysis for site_id: {req.site_id}")
        
        # Get site data from Supabase
        try:
            site_response = supabase.table("sites").select("*").eq("site_id", req.site_id).execute()
            if not site_response.data:
                return {"error": f"Site not found for site_id: {req.site_id}"}
            
            site_data = site_response.data[0]
            print(f"📋 Found site: {site_data['brand_name']} ({site_data['url']})")
            
        except Exception as e:
            print(f"❌ Error fetching site data: {e}")
            return {"error": f"Failed to fetch site data: {str(e)}"}
        
        # Get pages data from Supabase
        try:
            pages_response = supabase.table("pages").select("*").eq("site_id", req.site_id).execute()
            pages_data = pages_response.data
            print(f"📄 Found {len(pages_data)} pages for analysis")
            
        except Exception as e:
            print(f"❌ Error fetching pages data: {e}")
            return {"error": f"Failed to fetch pages data: {str(e)}"}
        
        # Get audit data from Supabase
        try:
            audit_response = supabase.table("audit_data").select("*").eq("site_id", req.site_id).execute()
            audit_data = audit_response.data[0] if audit_response.data else {}
            print(f"📊 Found audit data with scores: AEO={audit_data.get('aeo_score', 0)}, GEO={audit_data.get('geo_score', 0)}")
            
        except Exception as e:
            print(f"❌ Error fetching audit data: {e}")
            return {"error": f"Failed to fetch audit data: {str(e)}"}
        
        # Analyze query visibility using the stored data
        result = analyze_query_visibility_from_data(
            site_data=site_data,
            pages_data=pages_data,
            audit_data=audit_data,
            queries=req.queries
        )
        
        print(f"✅ Query analysis completed for site_id: {req.site_id}")
        
        return {
            "success": True,
            "site_id": req.site_id,
            "url": site_data['url'],
            "query_analysis": result,
            "analysis_type": "AI Query Visibility"
        }
        
    except Exception as e:
        print(f"❌ Query check failed: {e}")
        return {"error": f"Query check failed: {str(e)}"}

# ---------- /audit-new ----------
@app.post("/audit-new")
async def audit_new(req: NewAuditRequest = Body(...)):
    """
    NEW EVIKA audit endpoint with ScrapingBee integration:
    1. Crawls website using ScrapingBee (15 pages max)
    2. Extracts AEO + GEO signals from all pages  
    3. Saves everything to Supabase with unique site_id
    4. Returns structured overview with site_id
    """
    try:
        print(f"🚀 Starting NEW EVIKA audit for: {req.url}")
        
        # Generate unique site_id for this audit
        site_id = str(uuid.uuid4())
        print(f"📋 Generated site_id: {site_id}")
        
        # Ensure Supabase schema exists
        if not ensure_schema_exists():
            print("⚠️ Schema setup failed, continuing anyway...")
        
        # Step 1: Crawl website with ScrapingBee
        print("🕷️ Starting website crawl...")
        crawl_result = crawl_website_with_scrapingbee(req.url, max_pages=15)
        
        if not crawl_result.get("success", False):
            return {
                "error": f"Crawl failed: {crawl_result.get('error', 'Unknown error')}",
                "site_id": site_id
            }
        
        pages_data = crawl_result.get("pages", [])
        print(f"✅ Crawled {len(pages_data)} pages")
        
        # Step 2: Extract signals from crawled data
        print("🔍 Extracting AEO + GEO signals...")
        signals = extract_signals_from_pages(pages_data)
        
        # Step 3: Save to Supabase
        print("💾 Saving to Supabase...")
        save_success = save_audit_data(site_id, req.url, pages_data, signals)
        
        if not save_success:
            print("⚠️ Failed to save to Supabase, but continuing...")
        
        # Step 4: Return structured JSON
        return {
            "site_id": site_id,
            "url": req.url,
            "brand_name": signals.get("brand_name", ""),
            "description": signals.get("description", ""),
            "products": signals.get("products", []),
            "location": signals.get("location", ""),
            "faqs": [faq.get("question", "") for faq in signals.get("faqs", [])],
            "topics": signals.get("topics", []),
            "competitors": signals.get("competitors", []),
            "pages_crawled": len(pages_data),
            "success": True
        }
        
    except Exception as e:
        print(f"❌ NEW audit failed: {e}")
        return {
            "error": f"Audit failed: {str(e)}",
            "site_id": site_id if 'site_id' in locals() else None
        }

