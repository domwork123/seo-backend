# main.py — /audit, /score, /score-bulk, /optimize
from fastapi import FastAPI, Query, Body, Request, Response, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import json
import os
import stripe
from supabase import create_client, Client
from fastapi.middleware.cors import CORSMiddleware   # 👈 ADD THIS LINE

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Stripe configuration
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
NEXT_PUBLIC_SITE_URL = os.getenv("NEXT_PUBLIC_SITE_URL", "http://localhost:3000")

from aeo_geo_scoring import score_website
from aeo_geo_optimizer import detect_faq, extract_images, optimize_meta_description, run_llm_queries, check_geo_signals, generate_blog_post
from aeo_geo_audit import audit_site_aeo_geo, audit_single_page_aeo_geo
from audit import audit_site
from enhanced_audit import enhanced_audit_site
from query_analyzer import analyze_query_visibility
from scrapingbee_crawler import crawl_website_with_scrapingbee
from signal_extractor import extract_signals_from_pages
from supabase_schema import ensure_schema_exists, save_audit_data
from simple_blog_generator import SimpleBlogGenerator
import re
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

def detect_lang(text: str) -> str:
    """
    Detect language from text using simple dictionary approach.
    Returns 'lt' for Lithuanian, 'en' for English, 'unknown' otherwise.
    """
    if not text:
        return 'unknown'
    
    # Lithuanian indicators
    lt_indicators = ['ą', 'č', 'ę', 'ė', 'į', 'š', 'ų', 'ū', 'ž', 'kur', 'kaip', 'kada', 'kur', 'kas', 'kodėl']
    # English indicators  
    en_indicators = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'what', 'how', 'when', 'where', 'why']
    
    text_lower = text.lower()
    
    lt_count = sum(1 for indicator in lt_indicators if indicator in text_lower)
    en_count = sum(1 for indicator in en_indicators if indicator in text_lower)
    
    if lt_count > en_count:
        return 'lt'
    elif en_count > lt_count:
        return 'en'
    else:
        return 'unknown'

async def get_user_from_session(request: Request) -> Dict[str, Any]:
    """
    Extract user information from Supabase session in request headers or cookies.
    Returns user data if authenticated, raises HTTPException if not.
    """
    try:
        # Get session token from Authorization header first, then cookies
        auth_header = request.headers.get("Authorization")
        session_token = None
        
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header[7:]  # Remove "Bearer " prefix
        else:
            # Fallback to cookies
            session_token = request.cookies.get('sb-access-token') or request.cookies.get('supabase-auth-token')
        
        if not session_token:
            raise HTTPException(status_code=401, detail="No session token found")
        
        print(f"🔐 Authenticating with token: {session_token[:20]}...")
        
        # Verify session with Supabase
        response = supabase.auth.get_user(session_token)
        
        if not response.user:
            raise HTTPException(status_code=401, detail="Invalid session token")
        
        print(f"✅ User authenticated: {response.user.email}")
        
        return {
            "id": response.user.id,
            "email": response.user.email,
            "user_metadata": response.user.user_metadata
        }
        
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")

def get_site_language(site_id: str) -> str:
    """
    Get language from site data in Supabase.
    Returns default 'en' if not found.
    """
    try:
        result = supabase.table("sites").select("language").eq("id", site_id).execute()
        if result.data and len(result.data) > 0:
            return result.data[0].get("language", "en")
    except Exception as e:
        print(f"Error fetching site language: {e}")
    return "en"

async def get_comprehensive_site_data(site_id: str) -> Dict[str, Any]:
    """Get comprehensive site data for recommendation generation"""
    try:
        print(f"🔍 Fetching comprehensive site data for: {site_id}")
        
        # Get site basic info
        site_result = supabase.table("sites").select("*").eq("id", site_id).execute()
        if not site_result.data:
            print(f"❌ Site not found: {site_id}")
            return None
        
        site_data = site_result.data[0]
        print(f"✅ Site data found: {site_data.get('brand_name', 'Unknown')}")
        
        # Get pages data
        pages_result = supabase.table("pages").select("*").eq("site_id", site_id).limit(10).execute()
        pages_data = pages_result.data if pages_result.data else []
        print(f"📄 Pages data found: {len(pages_data)} pages")
        
        # Get audit data
        audit_result = supabase.table("audits").select("*").eq("site_id", site_id).order("created_at", desc=True).limit(1).execute()
        audit_data = audit_result.data[0] if audit_result.data else {}
        print(f"📊 Audit data found: {bool(audit_data)}")
        
        # Extract key information
        return {
            "site_info": {
                "id": site_data.get("id"),
                "url": site_data.get("url"),
                "brand_name": site_data.get("brand_name"),
                "description": site_data.get("description"),
                "location": site_data.get("location"),
                "industry": site_data.get("industry"),
                "language": site_data.get("language", "en")
            },
            "pages": pages_data,
            "audit_data": {
                "faqs": audit_data.get("faqs", []),
                "products": audit_data.get("products", []),
                "competitors": audit_data.get("competitors", []),
                "topics": audit_data.get("topics", []),
                "geo_signals": audit_data.get("geo_signals", {}),
                "alt_text_issues": audit_data.get("alt_text", [])
            }
        }
        
    except Exception as e:
        print(f"❌ Error fetching comprehensive site data: {e}")
        return None

def generate_aeo_recommendations(site_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate AEO-optimized keyword and question recommendations"""
    
    site_info = site_data["site_info"]
    audit_data = site_data["audit_data"]
    
    keywords = []
    questions = []
    
    print(f"🎯 Generating AEO recommendations for: {site_info['brand_name']}")
    
    # AEO KEYWORDS - Focus on answerability and search intent
    
    # 1. Brand Authority Keywords
    if site_info["brand_name"]:
        keywords.extend([
            {
                "keyword": f"what is {site_info['brand_name']}",
                "type": "brand_question",
                "search_volume": "high",
                "difficulty": "easy",
                "intent": "informational",
                "seo_potential": "high",
                "category": "brand_authority"
            },
            {
                "keyword": f"how does {site_info['brand_name']} work",
                "type": "process_question",
                "search_volume": "medium",
                "difficulty": "medium",
                "intent": "informational",
                "seo_potential": "high",
                "category": "brand_authority"
            }
        ])
    
    # 2. Product/Service Keywords
    for product in audit_data["products"][:3]:  # Limit to top 3 products
        keywords.extend([
            {
                "keyword": f"best {product}",
                "type": "product_comparison",
                "search_volume": "high",
                "difficulty": "medium",
                "intent": "commercial",
                "seo_potential": "high",
                "category": "product_optimization"
            },
            {
                "keyword": f"{product} guide",
                "type": "product_guide",
                "search_volume": "medium",
                "difficulty": "easy",
                "intent": "informational",
                "seo_potential": "high",
                "category": "product_optimization"
            }
        ])
    
    # 3. Problem-Solution Keywords
    if site_info["industry"]:
        keywords.extend([
            {
                "keyword": f"how to solve {site_info['industry']} problems",
                "type": "problem_solution",
                "search_volume": "medium",
                "difficulty": "medium",
                "intent": "informational",
                "seo_potential": "high",
                "category": "problem_solving"
            }
        ])
    
    # AEO QUESTIONS - People Also Ask style
    
    # 1. How-to Questions
    for product in audit_data["products"][:2]:
        questions.extend([
            {
                "question": f"How to choose the best {product}?",
                "type": "how_to",
                "search_volume": "high",
                "difficulty": "medium",
                "intent": "informational",
                "seo_potential": "high",
                "category": "tutorial"
            },
            {
                "question": f"What to look for in {product}?",
                "type": "evaluation",
                "search_volume": "medium",
                "difficulty": "easy",
                "intent": "informational",
                "seo_potential": "high",
                "category": "evaluation"
            }
        ])
    
    # 2. Comparison Questions
    if audit_data["competitors"]:
        competitor = audit_data["competitors"][0]
        questions.append({
            "question": f"What makes {site_info['brand_name']} better than {competitor}?",
            "type": "comparison",
            "search_volume": "medium",
            "difficulty": "hard",
            "intent": "comparison",
            "seo_potential": "medium",
            "category": "competitive_analysis"
        })
    
    # 3. Problem-Solution Questions
    questions.extend([
        {
            "question": f"What are the common {site_info['industry']} challenges?",
            "type": "problem_identification",
            "search_volume": "high",
            "difficulty": "easy",
            "intent": "informational",
            "seo_potential": "high",
            "category": "problem_solving"
        }
    ])
    
    print(f"✅ Generated {len(keywords)} AEO keywords and {len(questions)} AEO questions")
    
    return {
        "keywords": keywords[:6],  # Limit to 6 keywords
        "questions": questions[:5],  # Limit to 5 questions
        "mode": "AEO",
        "focus": "answerability_and_search_intent",
        "total_recommendations": len(keywords) + len(questions)
    }

def generate_geo_recommendations(site_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate GEO-optimized keyword and question recommendations"""
    
    site_info = site_data["site_info"]
    audit_data = site_data["audit_data"]
    
    keywords = []
    questions = []
    
    print(f"🌍 Generating GEO recommendations for: {site_info['brand_name']} in {site_info['location']}")
    
    # GEO KEYWORDS - Focus on local search and location-based intent
    
    # 1. Local Brand Keywords
    if site_info["brand_name"] and site_info["location"]:
        keywords.extend([
            {
                "keyword": f"{site_info['brand_name']} in {site_info['location']}",
                "type": "local_brand",
                "search_volume": "medium",
                "difficulty": "easy",
                "intent": "local",
                "seo_potential": "high",
                "category": "local_brand"
            },
            {
                "keyword": f"best {site_info['brand_name']} {site_info['location']}",
                "type": "local_best",
                "search_volume": "medium",
                "difficulty": "medium",
                "intent": "local_commercial",
                "seo_potential": "high",
                "category": "local_brand"
            }
        ])
    
    # 2. Local Service Keywords
    if site_info["location"]:
        for product in audit_data["products"][:2]:
            keywords.extend([
                {
                    "keyword": f"{product} in {site_info['location']}",
                    "type": "local_service",
                    "search_volume": "medium",
                    "difficulty": "easy",
                    "intent": "local",
                    "seo_potential": "high",
                    "category": "local_service"
                },
                {
                    "keyword": f"local {product} {site_info['location']}",
                    "type": "local_search",
                    "search_volume": "low",
                    "difficulty": "easy",
                    "intent": "local",
                    "seo_potential": "medium",
                    "category": "local_service"
                }
            ])
    
    # 3. Local Comparison Keywords
    if audit_data["competitors"] and site_info["location"]:
        competitor = audit_data["competitors"][0]
        keywords.append({
            "keyword": f"{site_info['brand_name']} vs {competitor} {site_info['location']}",
            "type": "local_comparison",
            "search_volume": "low",
            "difficulty": "hard",
            "intent": "local_comparison",
            "seo_potential": "medium",
            "category": "local_competitive"
        })
    
    # GEO QUESTIONS - Local search intent
    
    # 1. Local Service Questions
    if site_info["location"]:
        questions.extend([
            {
                "question": f"Where to find {site_info['brand_name']} in {site_info['location']}?",
                "type": "local_where",
                "search_volume": "medium",
                "difficulty": "easy",
                "intent": "local",
                "seo_potential": "high",
                "category": "local_discovery"
            },
            {
                "question": f"Best {site_info['industry']} services in {site_info['location']}?",
                "type": "local_best",
                "search_volume": "high",
                "difficulty": "medium",
                "intent": "local_commercial",
                "seo_potential": "high",
                "category": "local_services"
            }
        ])
    
    # 2. Local Experience Questions
    questions.extend([
        {
            "question": f"What to expect from {site_info['brand_name']} in {site_info['location']}?",
            "type": "local_experience",
            "search_volume": "low",
            "difficulty": "easy",
            "intent": "local_informational",
            "seo_potential": "medium",
            "category": "local_experience"
        }
    ])
    
    # 3. Local Problem-Solution Questions
    if site_info["location"]:
        questions.append({
            "question": f"Common {site_info['industry']} issues in {site_info['location']}?",
            "type": "local_problems",
            "search_volume": "medium",
            "difficulty": "easy",
            "intent": "local_informational",
            "seo_potential": "high",
            "category": "local_problem_solving"
        })
    
    print(f"✅ Generated {len(keywords)} GEO keywords and {len(questions)} GEO questions")
    
    return {
        "keywords": keywords[:6],  # Limit to 6 keywords
        "questions": questions[:5],  # Limit to 5 questions
        "mode": "GEO",
        "focus": "local_search_and_location_intent",
        "total_recommendations": len(keywords) + len(questions)
    }

async def generate_ai_queries(site_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate 20 AI queries using GPT-4 Mini for dynamic, natural queries"""
    
    site_info = site_data["site_info"]
    audit_data = site_data["audit_data"]
    
    print(f"🎯 Generating dynamic AI queries for: {site_info['brand_name']}")
    
    try:
        # Get OpenAI client
        api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ OpenAI API key not found, using fallback queries")
            return await _generate_fallback_queries(site_data)
        
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        # Create context for query generation
        brand_name = site_info['brand_name']
        services = ', '.join(audit_data.get('products', ['services']))
        location = site_info.get('location', '')
        industry = site_info.get('industry', 'business')
        
        # Determine if location exists for GEO queries
        has_location = bool(location and location.strip())
        
        system_prompt = f"""You are an AI query generator. Generate 20 realistic, natural-language questions that users might ask an AI assistant about this brand.

Brand: {brand_name}
Services/Products: {services}
Location: {location if has_location else 'No specific location'}
Industry: {industry}

Divide queries evenly into 5 categories:
- Brand (4 queries): Questions about the brand itself
- Service/Product (4 queries): Questions about services/products offered
- Competitor (4 queries): Questions comparing with alternatives
- Local/GEO (4 queries): Location-based questions ({"include these" if has_location else "skip these - add 4 more Service/Product queries instead"})
- Problem-solving (4 queries): Questions about solving industry problems

Make queries natural, varied, and realistic. Avoid repetitive patterns.
Output JSON array: [{{"id": 1, "category": "brand", "text": "What is {brand_name}?"}}, ...]"""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.8,
            max_tokens=2000,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Generate 20 queries for {brand_name}"}
            ]
        )
        
        # Parse JSON response
        import json
        raw_output = response.choices[0].message.content or ""
        
        # Clean and parse JSON
        cleaned = raw_output.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        
        try:
            queries = json.loads(cleaned)
            if isinstance(queries, list) and len(queries) == 20:
                print(f"✅ Generated {len(queries)} dynamic AI queries")
                return queries
            else:
                print(f"⚠️ Invalid query count ({len(queries) if isinstance(queries, list) else 'not list'}), using fallback")
                return await _generate_fallback_queries(site_data)
        except json.JSONDecodeError:
            print("⚠️ Failed to parse JSON, using fallback queries")
            return await _generate_fallback_queries(site_data)
        
    except Exception as e:
        print(f"❌ Error generating dynamic queries: {e}")
        return await _generate_fallback_queries(site_data)

async def _generate_fallback_queries(site_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Fallback query generation if GPT-4 Mini fails"""
    
    site_info = site_data["site_info"]
    audit_data = site_data["audit_data"]
    
    queries = []
    query_id = 1
    
    # 1. Brand Queries (4 queries)
    brand_queries = [
        f"What is {site_info['brand_name']}?",
        f"How does {site_info['brand_name']} work?",
        f"Is {site_info['brand_name']} reliable?",
        f"What makes {site_info['brand_name']} different?"
    ]
    
    for query in brand_queries:
        queries.append({
            "id": query_id,
            "category": "brand",
            "text": query
        })
        query_id += 1
    
    # 2. Service/Product Queries (4 queries)
    products = audit_data.get("products", [])
    if not products:
        products = ["services", "solutions", "products"]
    
    service_queries = [
        f"Best {products[0] if products else 'services'} for businesses",
        f"How to choose {products[0] if products else 'services'}?",
        f"What are the top {products[0] if products else 'services'}?",
        f"Compare {products[0] if products else 'services'} options"
    ]
    
    for query in service_queries:
        queries.append({
            "id": query_id,
            "category": "service_product",
            "text": query
        })
        query_id += 1
    
    # 3. Competitor Queries (4 queries)
    competitor_queries = [
        f"{site_info['brand_name']} vs competitors",
        f"Alternatives to {site_info['brand_name']}",
        f"Best {products[0] if products else 'services'} providers",
        f"Compare {site_info['brand_name']} with other options"
    ]
    
    for query in competitor_queries:
        queries.append({
            "id": query_id,
            "category": "competitor",
            "text": query
        })
        query_id += 1
    
    # 4. Local/GEO Queries (4 queries) - only if location exists
    if site_info.get("location"):
        location = site_info["location"]
        geo_queries = [
            f"Best {products[0] if products else 'services'} in {location}",
            f"{site_info['brand_name']} in {location}",
            f"Local {products[0] if products else 'services'} providers in {location}",
            f"Where to find {site_info['brand_name']} in {location}?"
        ]
        
        for query in geo_queries:
            queries.append({
                "id": query_id,
                "category": "local_geo",
                "text": query
            })
            query_id += 1
    else:
        # If no location, add more service/product queries
        additional_queries = [
            f"What are the benefits of {products[0] if products else 'services'}?",
            f"How much does {products[0] if products else 'services'} cost?",
            f"When should I use {products[0] if products else 'services'}?",
            f"What problems does {products[0] if products else 'services'} solve?"
        ]
        
        for query in additional_queries:
            queries.append({
                "id": query_id,
                "category": "service_product",
                "text": query
            })
            query_id += 1
    
    # 5. Problem-solving Queries (4 queries)
    industry = site_info.get("industry", "business")
    problem_queries = [
        f"How to solve {industry} problems?",
        f"What are common {industry} challenges?",
        f"How to improve {industry} efficiency?",
        f"What solutions exist for {industry} issues?"
    ]
    
    for query in problem_queries:
        queries.append({
            "id": query_id,
            "category": "problem_solving",
            "text": query
        })
        query_id += 1
    
    print(f"✅ Generated {len(queries)} fallback queries")
    return queries

async def simulate_ai_response(query: str, brand_name: str, site_data: Dict[str, Any]) -> str:
    """Simulate AI assistant response using GPT-4 Mini"""
    
    try:
        # Get OpenAI client
        api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            return "AI response simulation not available - API key missing"
        
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        # Create context for the AI
        site_info = site_data["site_info"]
        audit_data = site_data["audit_data"]
        
        context = f"""
        Brand: {site_info['brand_name']}
        Description: {site_info.get('description', '')}
        Location: {site_info.get('location', '')}
        Industry: {site_info.get('industry', '')}
        Products/Services: {', '.join(audit_data.get('products', []))}
        Competitors: {', '.join(audit_data.get('competitors', []))}
        """
        
        prompt = f"""
        You are an AI assistant answering user questions. 
        Provide a helpful, informative response to this query: "{query}"
        
        Context about the business:
        {context}
        
        Answer naturally as an AI assistant would, mentioning relevant brands and services when appropriate.
        Keep the response conversational and helpful.
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=500,
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant that provides informative answers to user questions."},
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content or "No response generated"
        
    except Exception as e:
        print(f"❌ Error simulating AI response: {e}")
        return f"AI response simulation failed: {str(e)}"

async def evaluate_brand_detection(response: str, brand_name: str) -> Dict[str, Any]:
    """Evaluate if brand is mentioned using GPT-4 Mini semantic analysis"""
    
    try:
        # Get OpenAI client
        api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ OpenAI API key not found, using fallback brand detection")
            return await _fallback_brand_detection(response, brand_name)
        
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        system_prompt = f"""Does this answer mention the brand "{brand_name}"? 
Classify result as JSON:
{{ "mentioned": true/false, "strength": "Weak/Medium/Strong" }}

Rules:
- Weak = briefly listed among many.
- Medium = clearly included but not the main focus.
- Strong = recommended, highlighted, or positioned as best.

Return only JSON, no other text."""
        
        response_analysis = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.1,
            max_tokens=100,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Answer: {response}"}
            ]
        )
        
        # Parse JSON response
        import json
        raw_output = response_analysis.choices[0].message.content or ""
        
        try:
            result = json.loads(raw_output.strip())
            if "mentioned" in result and "strength" in result:
                return {
                    "is_mentioned": result["mentioned"],
                    "strength": result["strength"],
                    "exact_mentions": 1 if result["mentioned"] else 0,
                    "partial_mentions": 0
                }
            else:
                print("⚠️ Invalid brand detection response, using fallback")
                return await _fallback_brand_detection(response, brand_name)
        except json.JSONDecodeError:
            print("⚠️ Failed to parse brand detection JSON, using fallback")
            return await _fallback_brand_detection(response, brand_name)
        
    except Exception as e:
        print(f"❌ Error in brand detection: {e}")
        return await _fallback_brand_detection(response, brand_name)

async def _fallback_brand_detection(response: str, brand_name: str) -> Dict[str, Any]:
    """Fallback brand detection using string matching"""
    
    response_lower = response.lower()
    brand_lower = brand_name.lower()
    
    # Check for exact brand name mentions
    exact_mentions = response_lower.count(brand_lower)
    
    # Check for partial matches (first word of brand)
    brand_words = brand_name.split()
    if brand_words:
        first_word = brand_words[0].lower()
        partial_mentions = response_lower.count(first_word)
    else:
        partial_mentions = 0
    
    # Determine strength
    if exact_mentions >= 2:
        strength = "Strong"
    elif exact_mentions >= 1:
        strength = "Medium"
    elif partial_mentions >= 1:
        strength = "Weak"
    else:
        strength = "None"
    
    is_mentioned = exact_mentions > 0 or partial_mentions > 0
    
    return {
        "is_mentioned": is_mentioned,
        "strength": strength,
        "exact_mentions": exact_mentions,
        "partial_mentions": partial_mentions
    }

async def extract_competitors(response: str, brand_name: str) -> List[str]:
    """Extract competitor brand names using GPT-4 Mini semantic analysis"""
    
    try:
        # Get OpenAI client
        api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ OpenAI API key not found, using fallback competitor extraction")
            return await _fallback_competitor_extraction(response, brand_name)
        
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        system_prompt = f"""Extract competitor brand names mentioned in this answer that offer similar services/products to "{brand_name}".
Normalize duplicates (e.g., "Spark" and "Spark Car Wash" = "Spark").
Return JSON: {{ "competitors": ["Spark", "SurferSEO"] }}

Only include actual competitor brands, not generic terms or unrelated companies.
Return only JSON, no other text."""
        
        competitor_analysis = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.1,
            max_tokens=200,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Answer: {response}"}
            ]
        )
        
        # Parse JSON response
        import json
        raw_output = competitor_analysis.choices[0].message.content or ""
        
        try:
            result = json.loads(raw_output.strip())
            if "competitors" in result and isinstance(result["competitors"], list):
                competitors = [comp.strip() for comp in result["competitors"] if comp.strip()]
                return competitors[:5]  # Limit to top 5 competitors
            else:
                print("⚠️ Invalid competitor extraction response, using fallback")
                return await _fallback_competitor_extraction(response, brand_name)
        except json.JSONDecodeError:
            print("⚠️ Failed to parse competitor extraction JSON, using fallback")
            return await _fallback_competitor_extraction(response, brand_name)
        
    except Exception as e:
        print(f"❌ Error in competitor extraction: {e}")
        return await _fallback_competitor_extraction(response, brand_name)

async def _fallback_competitor_extraction(response: str, brand_name: str) -> List[str]:
    """Fallback competitor extraction using regex"""
    
    # Common competitor indicators
    competitor_indicators = [
        "alternatives", "competitors", "other options", "similar services",
        "like", "such as", "including", "also", "besides", "in addition to"
    ]
    
    competitors = []
    response_lower = response.lower()
    
    # Look for patterns that indicate competitors
    for indicator in competitor_indicators:
        if indicator in response_lower:
            # Extract text around the indicator
            start = response_lower.find(indicator)
            if start != -1:
                # Get context around the indicator
                context_start = max(0, start - 100)
                context_end = min(len(response), start + 200)
                context = response[context_start:context_end]
                
                # Look for capitalized words (potential brand names)
                import re
                potential_brands = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', context)
                
                for brand in potential_brands:
                    if brand.lower() != brand_name.lower() and len(brand) > 2:
                        competitors.append(brand)
    
    # Remove duplicates and normalize
    competitors = list(set(competitors))
    competitors = [comp.strip() for comp in competitors if comp.strip()]
    
    return competitors[:5]  # Limit to top 5 competitors

async def evaluate_recommendation_strength(response: str, brand_name: str) -> str:
    """Evaluate recommendation strength using GPT-4 Mini semantic analysis"""
    
    try:
        # Get OpenAI client
        api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ OpenAI API key not found, using fallback recommendation strength")
            return await _fallback_recommendation_strength(response, brand_name)
        
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        system_prompt = f"""In this text, how is "{brand_name}" positioned?
Options: "Best option" / "One of many" / "Not mentioned".
Return JSON: {{ "recommendation": "Best option" }}

Return only JSON, no other text."""
        
        recommendation_analysis = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.1,
            max_tokens=50,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Text: {response}"}
            ]
        )
        
        # Parse JSON response
        import json
        raw_output = recommendation_analysis.choices[0].message.content or ""
        
        try:
            result = json.loads(raw_output.strip())
            if "recommendation" in result:
                return result["recommendation"]
            else:
                print("⚠️ Invalid recommendation strength response, using fallback")
                return await _fallback_recommendation_strength(response, brand_name)
        except json.JSONDecodeError:
            print("⚠️ Failed to parse recommendation strength JSON, using fallback")
            return await _fallback_recommendation_strength(response, brand_name)
        
    except Exception as e:
        print(f"❌ Error in recommendation strength analysis: {e}")
        return await _fallback_recommendation_strength(response, brand_name)

async def _fallback_recommendation_strength(response: str, brand_name: str) -> str:
    """Fallback recommendation strength using keyword matching"""
    
    response_lower = response.lower()
    brand_lower = brand_name.lower()
    
    # Strong recommendation indicators
    strong_indicators = [
        "best", "recommended", "top choice", "highly recommend", "excellent",
        "outstanding", "superior", "preferred", "leading", "premier"
    ]
    
    # Weak recommendation indicators
    weak_indicators = [
        "one of many", "several options", "alternatives", "other choices",
        "also consider", "in addition", "besides", "along with"
    ]
    
    # Check for strong indicators
    strong_count = sum(1 for indicator in strong_indicators if indicator in response_lower)
    weak_count = sum(1 for indicator in weak_indicators if indicator in response_lower)
    
    # Check if brand is mentioned
    brand_mentioned = brand_lower in response_lower
    
    if not brand_mentioned:
        return "Not mentioned"
    elif strong_count > weak_count:
        return "Best option"
    elif weak_count > 0:
        return "One of many"
    else:
        return "One of many"

async def save_query_results(site_id: str, query_id: int, query_text: str, 
                             ai_response: str, evaluations: Dict[str, Any]) -> None:
    """Save query results to Supabase"""
    
    try:
        result_data = {
            "site_id": site_id,
            "query_id": query_id,
            "query_text": query_text,
            "ai_response": ai_response,
            "brand_detection": evaluations["brand_detection"],
            "competitors": evaluations["competitors"],
            "recommendation_strength": evaluations["recommendation_strength"],
            "created_at": datetime.now().isoformat()
        }
        
        supabase.table("query_visibility_results").insert(result_data).execute()
        print(f"✅ Saved query result for query {query_id}")
        
    except Exception as e:
        print(f"❌ Error saving query result: {e}")

def calculate_summary_metrics(results: List[Dict[str, Any]], brand_name: str) -> Dict[str, Any]:
    """Calculate weighted summary metrics from all query results"""
    
    total_queries = len(results)
    if total_queries == 0:
        return {
            "visibility_score": 0,
            "share_of_ai_voice": 0,
            "strength_score": 0,
            "top_competitors": [],
            "total_queries": 0
        }
    
    # Category weights for realistic market position
    category_weights = {
        "brand": 1.0,           # Brand queries = 1x
        "service_product": 1.5, # Service/Product queries = 1.5x
        "competitor": 2.0,      # Competitor queries = 2x (most important)
        "local_geo": 1.5,       # Local queries = 1.5x
        "problem_solving": 1.5  # Problem-solving queries = 1.5x
    }
    
    # Calculate weighted visibility score
    weighted_score = 0
    total_weight = 0
    
    for result in results:
        category = result.get("category", "brand")
        weight = category_weights.get(category, 1.0)
        total_weight += weight
        
        if result["brand_detection"]["is_mentioned"]:
            weighted_score += weight
    
    visibility_score = (weighted_score / total_weight) * 100 if total_weight > 0 else 0
    
    # Share of AI Voice (SAV) - brand vs competitor mentions
    all_competitors = []
    for result in results:
        all_competitors.extend(result["competitors"])
    
    brand_mentions = sum(1 for r in results if r["brand_detection"]["is_mentioned"])
    competitor_mentions = len(all_competitors)
    
    if brand_mentions + competitor_mentions == 0:
        share_of_ai_voice = 0
    else:
        share_of_ai_voice = (brand_mentions / (brand_mentions + competitor_mentions)) * 100
    
    # Strength Score - average strength converted to numeric (1-3)
    strength_mapping = {"Weak": 1, "Medium": 2, "Strong": 3}
    strength_scores = []
    
    for result in results:
        if result["brand_detection"]["is_mentioned"]:
            strength = result["brand_detection"]["strength"]
            if strength in strength_mapping:
                strength_scores.append(strength_mapping[strength])
    
    strength_score = sum(strength_scores) / len(strength_scores) if strength_scores else 0
    
    # Top Competitors
    from collections import Counter
    competitor_counts = Counter(all_competitors)
    top_competitors = [
        {"name": name, "mentions": count} 
        for name, count in competitor_counts.most_common(5)
    ]
    
    return {
        "visibility_score": round(visibility_score, 1),
        "share_of_ai_voice": round(share_of_ai_voice, 1),
        "strength_score": round(strength_score, 1),
        "top_competitors": top_competitors,
        "total_queries": total_queries,
        "brand_mentions": brand_mentions,
        "competitor_mentions": competitor_mentions,
        "weighted_analysis": {
            "category_weights": category_weights,
            "total_weight": total_weight,
            "weighted_score": weighted_score
        }
    }

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

class BlogRequest(BaseModel):
    brand_name: str
    target_keyword: str
    language: Optional[str] = None  # Will be required with fallback to sites.language
    mode: Optional[str] = "AEO"  # AEO or GEO
    context: Optional[Dict[str, Any]] = None
    site_id: Optional[str] = None  # For fetching site language from Supabase

class KeywordRecommendationRequest(BaseModel):
    site_id: str
    mode: Optional[str] = "both"  # "AEO", "GEO", or "both"
    language: Optional[str] = "en"
    max_keywords: Optional[int] = 6
    max_questions: Optional[int] = 5

class QueryVisibilityRequest(BaseModel):
    site_id: str
    selected_queries: List[int]  # IDs of selected queries (max 8)
    language: Optional[str] = "en"

class QueryVisibilityResponse(BaseModel):
    success: bool
    site_id: str
    total_queries: int
    selected_queries: int
    results: List[Dict[str, Any]]
    summary: Dict[str, Any]
    generated_at: str

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
        
        try:
            # Save site info
            site_data = {
                "id": site_id,
                "url": req.url,
                "brand_name": signals.get("brand_name", ""),
                "description": signals.get("description", ""),
                "location": signals.get("location", ""),
                "industry": signals.get("industry", "")
            }
            
            supabase.table("sites").insert(site_data).execute()
            print(f"✅ Site info saved: {site_id}")
            
            # Save pages data
            for page in pages:
                page_data = {
                    "site_id": site_id,
                    "url": page.get("url", ""),
                    "title": page.get("title", ""),
                    "raw_text": page.get("raw_text", ""),
                    "images": page.get("images", [])
                }
                
                supabase.table("pages").insert(page_data).execute()
            
            print(f"✅ Pages saved: {len(pages)} pages")
            
            # Save audit results
            audit_data = {
                "site_id": site_id,
                "url": req.url,
                "results": {
                    "faqs": signals.get("faqs", []),
                    "schemas": signals.get("schemas", []),
                    "alt_text_issues": signals.get("alt_text_issues", []),
                    "geo_signals": signals.get("geo_signals", []),
                    "competitors": signals.get("competitors", []),
                    "products": signals.get("products", []),
                    "topics": signals.get("topics", [])
                }
            }
            
            supabase.table("audits").insert(audit_data).execute()
            print(f"✅ Audit data saved")
            
        except Exception as e:
            print(f"❌ Error saving to Supabase: {e}")
            print("⚠️ Continuing without saving to Supabase...")
        
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

# ---------- /test-supabase ----------
@app.get("/test-supabase")
async def test_supabase():
    """
    Test Supabase connection and configuration
    """
    try:
        print(f"🧪 Testing Supabase connection...")
        
        # Check environment variables
        supabase_url = os.getenv("SUPABASE_URL", "")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY", "")
        
        print(f"📋 Supabase URL: {'✅ Set' if supabase_url else '❌ Missing'}")
        print(f"📋 Supabase Key: {'✅ Set' if supabase_key else '❌ Missing'}")
        
        # Test basic connection
        try:
            test_result = supabase.table("sites").select("id").limit(1).execute()
            print(f"✅ Supabase connection successful")
            connection_ok = True
        except Exception as e:
            print(f"❌ Supabase connection failed: {e}")
            connection_ok = False
        
        return {
            "supabase_url_set": bool(supabase_url),
            "supabase_key_set": bool(supabase_key),
            "connection_ok": connection_ok,
            "error": str(e) if not connection_ok else None
        }
        
    except Exception as e:
        print(f"❌ Supabase test failed: {e}")
        return {"error": f"Supabase test failed: {str(e)}"}

# ---------- /generate-ai-queries ----------
@app.post("/generate-ai-queries")
async def generate_ai_queries_endpoint(req: KeywordRecommendationRequest = Body(...)):
    """
    Generate 20 AI queries for testing brand visibility in AI responses
    """
    try:
        print(f"🎯 Generating AI queries for site: {req.site_id}")
        
        # Get comprehensive site data
        site_data = await get_comprehensive_site_data(req.site_id)
        
        if not site_data:
            return {"error": "Site not found", "message": "Please audit a website first"}
        
        # Generate 20 queries across 5 categories
        queries = await generate_ai_queries(site_data)
        
        print(f"✅ Generated {len(queries)} AI queries")
        
        return {
            "success": True,
            "site_id": req.site_id,
            "queries": queries,
            "total_queries": len(queries),
            "categories": {
                "brand": len([q for q in queries if q["category"] == "brand"]),
                "service_product": len([q for q in queries if q["category"] == "service_product"]),
                "competitor": len([q for q in queries if q["category"] == "competitor"]),
                "local_geo": len([q for q in queries if q["category"] == "local_geo"]),
                "problem_solving": len([q for q in queries if q["category"] == "problem_solving"])
            },
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ AI query generation failed: {str(e)}")
        return {"error": f"AI query generation failed: {str(e)}"}

# ---------- /test-query-visibility ----------
@app.post("/test-query-visibility")
async def test_query_visibility(req: QueryVisibilityRequest = Body(...)):
    """
    Test brand visibility in AI responses for selected queries
    """
    try:
        print(f"🔍 Testing query visibility for site: {req.site_id}")
        print(f"📊 Selected queries: {req.selected_queries}")
        
        # Validate selected queries (max 8)
        if len(req.selected_queries) > 8:
            return {"error": "Maximum 8 queries allowed"}
        
        # Get comprehensive site data
        site_data = await get_comprehensive_site_data(req.site_id)
        
        if not site_data:
            return {"error": "Site not found", "message": "Please audit a website first"}
        
        # Generate all queries to get the selected ones
        all_queries = await generate_ai_queries(site_data)
        selected_queries = [q for q in all_queries if q["id"] in req.selected_queries]
        
        if len(selected_queries) != len(req.selected_queries):
            return {"error": "Some selected queries not found"}
        
        results = []
        brand_name = site_data["site_info"]["brand_name"]
        
        # Process each selected query
        for query in selected_queries:
            print(f"🤖 Processing query {query['id']}: {query['text']}")
            
            # Simulate AI response
            ai_response = await simulate_ai_response(query["text"], brand_name, site_data)
            
            # Run 3 evaluations with GPT-4 Mini
            brand_detection = await evaluate_brand_detection(ai_response, brand_name)
            competitors = await extract_competitors(ai_response, brand_name)
            recommendation_strength = await evaluate_recommendation_strength(ai_response, brand_name)
            
            # Save to Supabase
            evaluations = {
                "brand_detection": brand_detection,
                "competitors": competitors,
                "recommendation_strength": recommendation_strength
            }
            
            await save_query_results(req.site_id, query["id"], query["text"], ai_response, evaluations)
            
            # Add to results
            result = {
                "query_id": query["id"],
                "query_text": query["text"],
                "category": query["category"],
                "ai_response": ai_response,
                "brand_detection": brand_detection,
                "competitors": competitors,
                "recommendation_strength": recommendation_strength
            }
            
            results.append(result)
        
        # Calculate summary metrics
        summary = calculate_summary_metrics(results, brand_name)
        
        print(f"✅ Query visibility test completed")
        print(f"📊 Visibility Score: {summary['visibility_score']}%")
        print(f"🎯 Share of AI Voice: {summary['share_of_ai_voice']}%")
        
        return {
            "success": True,
            "site_id": req.site_id,
            "total_queries": len(all_queries),
            "selected_queries": len(selected_queries),
            "results": results,
            "summary": summary,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Query visibility test failed: {str(e)}")
        return {"error": f"Query visibility test failed: {str(e)}"}

# ---------- /recommend-keywords ----------
@app.post("/recommend-keywords")
async def recommend_keywords(req: KeywordRecommendationRequest = Body(...)):
    """
    Generate smart keyword and question recommendations
    for AEO and GEO blog post optimization
    """
    try:
        print(f"🎯 Generating recommendations for site: {req.site_id}")
        print(f"📊 Mode: {req.mode}")
        
        # Get comprehensive site data
        site_data = await get_comprehensive_site_data(req.site_id)
        
        if not site_data:
            return {"error": "Site not found", "message": "Please audit a website first"}
        
        # Generate mode-specific recommendations
        if req.mode == "AEO":
            recommendations = generate_aeo_recommendations(site_data)
        elif req.mode == "GEO":
            recommendations = generate_geo_recommendations(site_data)
        else:
            # Return both for mode selection
            recommendations = {
                "aeo": generate_aeo_recommendations(site_data),
                "geo": generate_geo_recommendations(site_data)
            }
        
        print(f"✅ Generated {len(recommendations.get('keywords', []))} keywords and {len(recommendations.get('questions', []))} questions")
        
        return {
            "success": True,
            "site_id": req.site_id,
            "mode": req.mode,
            "recommendations": recommendations,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Recommendation generation failed: {str(e)}")
        return {"error": f"Recommendation generation failed: {str(e)}"}

# ---------- /generate-blog ----------
@app.post("/generate-blog")
async def generate_blog(req: BlogRequest = Body(...)):
    """
    Generate AEO or GEO optimized blog content
    
    Input:
    - brand_name: Name of the brand
    - target_keyword: Target keyword for SEO
    - language: Language code (default: en)
    - mode: AEO or GEO (default: AEO)
    - context: Additional context from audit data
    
    Output:
    - Complete blog post with JSON-LD schema markup
    """
    try:
        print(f"📝 Generating {req.mode} blog post for {req.brand_name}")
        print(f"🎯 Target keyword: {req.target_keyword}")
        
        # Language validation and fallback logic
        language = req.language
        if not language and req.site_id:
            language = get_site_language(req.site_id)
            print(f"🌍 Language from site: {language}")
        elif not language:
            return {"error": "language required", "message": "Language must be provided or site_id must be provided to fetch from sites table"}
        
        print(f"🌍 Language: {language}")
        
        # Get site data for city mention (AEO requirement)
        site_city = None
        if req.site_id:
            try:
                site_result = supabase.table("sites").select("location").eq("id", req.site_id).execute()
                if site_result.data and len(site_result.data) > 0:
                    site_city = site_result.data[0].get("location", "")
                    print(f"🏙️ Site city: {site_city}")
            except Exception as e:
                print(f"⚠️ Could not fetch site city: {e}")
        
        # Initialize blog generator
        generator = SimpleBlogGenerator()
        
        # Generate blog post
        blog_post = generator.generate_blog_post(
            brand_name=req.brand_name,
            target_keyword=req.target_keyword,
            language=language,
            mode=req.mode,
            context=req.context,
            site_city=site_city,
            site_id=req.site_id,
            supabase_client=supabase
        )
        
        # Language validation and auto-repair
        title_intro_content = f"{blog_post.get('title', '')} {blog_post.get('content', '')[:500]}"
        detected_lang = detect_lang(title_intro_content)
        print(f"🔍 Detected language: {detected_lang}")
        
        if detected_lang != language.split('-')[0] and detected_lang != 'unknown':
            print(f"⚠️ Language mismatch detected: expected {language}, got {detected_lang}")
            # In a real implementation, you might want to regenerate or flag this
        
        print(f"✅ Blog post generated successfully")
        print(f"📊 Word count: {blog_post['word_count']}")
        print(f"📋 Sections: {len(blog_post['sections'])}")
        print(f"❓ FAQs: {len(blog_post['faqs'])}")
        
        return blog_post
        
    except Exception as e:
        print(f"❌ Blog generation failed: {e}")
        return {"error": f"Blog generation failed: {str(e)}"}

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

# ---------- /api/checkout ----------
@app.post("/api/checkout")
async def create_checkout_session(request: Request):
    """
    Create Stripe checkout session for subscription.
    Requires authenticated user from Supabase session.
    """
    try:
        # Get authenticated user
        user = await get_user_from_session(request)
        
        # Create Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{
                "price": STRIPE_PRICE_ID,
                "quantity": 1
            }],
            customer_email=user["email"],
            client_reference_id=user["id"],
            success_url=f"{NEXT_PUBLIC_SITE_URL}/dashboard?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{NEXT_PUBLIC_SITE_URL}/pricing"
        )
        
        return {"url": checkout_session.url}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Checkout session creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Checkout session creation failed: {str(e)}")

# ---------- /api/stripe/webhook ----------
@app.post("/api/stripe/webhook")
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhook events for subscription management.
    Updates Supabase profiles table based on subscription events.
    """
    try:
        # Get raw body and signature
        body = await request.body()
        signature = request.headers.get("stripe-signature")
        
        if not signature:
            print("❌ No Stripe signature found")
            return Response(status_code=400)
        
        # Verify webhook signature
        try:
            event = stripe.Webhook.construct_event(
                body, signature, STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            print(f"❌ Invalid payload: {e}")
            return Response(status_code=400)
        except stripe.error.SignatureVerificationError as e:
            print(f"❌ Invalid signature: {e}")
            return Response(status_code=400)
        
        # Handle the event
        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            user_id = session.get("client_reference_id")
            
            if user_id:
                # Get subscription details
                subscription_id = session.get("subscription")
                customer_id = session.get("customer")
                
                # Update Supabase profiles table
                try:
                    supabase.table("profiles").update({
                        "is_active": True,
                        "stripe_customer_id": customer_id,
                        "stripe_subscription_id": subscription_id
                    }).eq("id", user_id).execute()
                    
                    print(f"✅ Updated profile for user {user_id}: active=True")
                except Exception as e:
                    print(f"❌ Failed to update profile for user {user_id}: {e}")
        
        elif event["type"] == "customer.subscription.updated":
            subscription = event["data"]["object"]
            customer_id = subscription.get("customer")
            
            # Find user by customer_id
            try:
                profile_result = supabase.table("profiles").select("id").eq("stripe_customer_id", customer_id).execute()
                
                if profile_result.data:
                    user_id = profile_result.data[0]["id"]
                    
                    # Update subscription status
                    is_active = subscription.get("status") in ["active", "trialing"]
                    current_period_end = subscription.get("current_period_end")
                    
                    supabase.table("profiles").update({
                        "is_active": is_active,
                        "current_period_end": current_period_end
                    }).eq("id", user_id).execute()
                    
                    print(f"✅ Updated subscription for user {user_id}: active={is_active}")
            except Exception as e:
                print(f"❌ Failed to update subscription: {e}")
        
        elif event["type"] in ["customer.subscription.deleted", "invoice.payment_failed"]:
            subscription = event["data"]["object"]
            customer_id = subscription.get("customer")
            
            # Find user by customer_id
            try:
                profile_result = supabase.table("profiles").select("id").eq("stripe_customer_id", customer_id).execute()
                
                if profile_result.data:
                    user_id = profile_result.data[0]["id"]
                    
                    # Deactivate subscription
                    supabase.table("profiles").update({
                        "is_active": False
                    }).eq("id", user_id).execute()
                    
                    print(f"✅ Deactivated subscription for user {user_id}")
            except Exception as e:
                print(f"❌ Failed to deactivate subscription: {e}")
        
        return Response(status_code=200)
        
    except Exception as e:
        print(f"❌ Webhook processing failed: {e}")
        return Response(status_code=500)

