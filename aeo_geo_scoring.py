# aeo_geo_scoring.py — AEO (Answer Engine Optimization) + GEO (Geographic Optimization) focused scoring
from typing import Dict, Any, List, Tuple
from collections import Counter
import re, json, tldextract

# ---------------- AEO + GEO Focused Scoring ----------------

def score_website(audit_data: Dict[str, Any], detail: bool = False) -> Dict[str, Any]:
    """
    Calculate AEO (Answer Engine Optimization) and GEO (Geographic Optimization) scores.
    Focus exclusively on future-focused search optimization for AI search and geographic targeting.
    """
    try:
        pages = audit_data.get("pages", [])
        if not pages:
            return {
                "scores": {
                    "aeo": 0,
                    "geo": 0,
                    "overall": 0
                },
                "aeo_score": 0,
                "geo_score": 0,
                "combined_score": 0,
                "error": "No pages found in audit data"
            }

        # Calculate AEO and GEO scores
        aeo_score, aeo_tasks = calculate_aeo_score(pages)
        geo_score, geo_tasks = calculate_geo_score(pages, audit_data)
        
        # Calculate overall score (weighted average)
        overall_score = (aeo_score * 0.6) + (geo_score * 0.4)  # AEO slightly more important for future
        
        result = {
            "scores": {
                "aeo": aeo_score,
                "geo": geo_score,
                "overall": overall_score
            },
            "aeo_score": aeo_score,
            "geo_score": geo_score,
            "combined_score": overall_score,
            "pages_evaluated": len(pages),
            "aeo_tasks": aeo_tasks,
            "geo_tasks": geo_tasks,
            "pillar_tasks": {
                "AEO": aeo_tasks,
                "GEO": geo_tasks
            }
        }
        
        if detail:
            result["detailed_analysis"] = {
                "aeo_analysis": analyze_aeo_opportunities(pages),
                "geo_analysis": analyze_geo_opportunities(pages, audit_data)
            }
        
        return result
        
    except Exception as e:
        return {
            "scores": {
                "aeo": 0,
                "geo": 0,
                "overall": 0
            },
            "aeo_score": 0,
            "geo_score": 0,
            "combined_score": 0,
            "error": f"Scoring failed: {str(e)}"
        }

def calculate_aeo_score(pages: List[Dict[str, Any]]) -> Tuple[int, List[str]]:
    """
    Calculate AEO (Answer Engine Optimization) score based on:
    - FAQ content and schema
    - Meta descriptions optimized for featured snippets
    - Alt text for images
    - Structured data (JSON-LD)
    - Content structure for AI consumption
    """
    total_score = 0
    max_score = 0
    tasks = []
    
    for page in pages:
        page_score = 0
        page_max = 0
        
        # FAQ Content (25 points)
        faq_score, faq_tasks = check_faq_content(page)
        page_score += faq_score
        page_max += 25
        tasks.extend(faq_tasks)
        
        # Meta Description Optimization (20 points)
        meta_score, meta_tasks = check_meta_descriptions(page)
        page_score += meta_score
        page_max += 20
        tasks.extend(meta_tasks)
        
        # Alt Text Optimization (15 points)
        alt_score, alt_tasks = check_alt_text(page)
        page_score += alt_score
        page_max += 15
        tasks.extend(alt_tasks)
        
        # Structured Data (20 points)
        schema_score, schema_tasks = check_structured_data(page)
        page_score += schema_score
        page_max += 20
        tasks.extend(schema_tasks)
        
        # Content Structure for AI (20 points)
        content_score, content_tasks = check_ai_content_structure(page)
        page_score += content_score
        page_max += 20
        tasks.extend(content_tasks)
        
        total_score += page_score
        max_score += page_max
    
    if max_score == 0:
        return 0, ["No pages to analyze"]
    
    aeo_score = int((total_score / max_score) * 100)
    return aeo_score, list(set(tasks))  # Remove duplicates

def calculate_geo_score(pages: List[Dict[str, Any]], audit_data: Dict[str, Any]) -> Tuple[int, List[str]]:
    """
    Calculate GEO (Geographic Optimization) score based on:
    - Hreflang implementation
    - LocalBusiness schema
    - NAP (Name, Address, Phone) consistency
    - Geographic targeting signals
    - Local SEO elements
    """
    total_score = 0
    max_score = 0
    tasks = []
    
    for page in pages:
        page_score = 0
        page_max = 0
        
        # Hreflang Implementation (25 points)
        hreflang_score, hreflang_tasks = check_hreflang(page)
        page_score += hreflang_score
        page_max += 25
        tasks.extend(hreflang_tasks)
        
        # LocalBusiness Schema (20 points)
        local_schema_score, local_schema_tasks = check_local_schema(page)
        page_score += local_schema_score
        page_max += 20
        tasks.extend(local_schema_tasks)
        
        # NAP Consistency (20 points)
        nap_score, nap_tasks = check_nap_consistency(page)
        page_score += nap_score
        page_max += 20
        tasks.extend(nap_tasks)
        
        # Geographic Targeting (20 points)
        geo_targeting_score, geo_targeting_tasks = check_geographic_targeting(page)
        page_score += geo_targeting_score
        page_max += 20
        tasks.extend(geo_targeting_tasks)
        
        # Local SEO Elements (15 points)
        local_seo_score, local_seo_tasks = check_local_seo_elements(page)
        page_score += local_seo_score
        page_max += 15
        tasks.extend(local_seo_tasks)
        
        total_score += page_score
        max_score += page_max
    
    if max_score == 0:
        return 0, ["No pages to analyze"]
    
    geo_score = int((total_score / max_score) * 100)
    return geo_score, list(set(tasks))  # Remove duplicates

# ---------------- AEO Helper Functions ----------------

def check_faq_content(page: Dict[str, Any]) -> Tuple[int, List[str]]:
    """Check for FAQ content and schema"""
    score = 0
    tasks = []
    
    # Check for FAQ content in page
    content = page.get("content", "") or ""
    title = page.get("title", "") or ""
    h1 = page.get("h1", []) or []
    h2 = page.get("h2", []) or []
    
    # Look for FAQ indicators
    faq_indicators = ["faq", "frequently asked", "questions", "answers", "q&a"]
    has_faq_content = any(indicator in content.lower() for indicator in faq_indicators)
    
    if has_faq_content:
        score += 15
    else:
        tasks.append("Add FAQ section with common questions and answers")
    
    # Check for FAQ schema
    schema = page.get("schema", {})
    json_ld = schema.get("json_ld", [])
    has_faq_schema = any("FAQPage" in str(item) or "Question" in str(item) for item in json_ld)
    
    if has_faq_schema:
        score += 10
    else:
        tasks.append("Add FAQ schema markup (JSON-LD) for better AI understanding")
    
    return score, tasks

def check_meta_descriptions(page: Dict[str, Any]) -> Tuple[int, List[str]]:
    """Check meta descriptions for featured snippet optimization"""
    score = 0
    tasks = []
    
    meta = page.get("meta", "") or ""
    
    if not meta:
        tasks.append("Add meta description optimized for featured snippets")
        return 0, tasks
    
    # Check length (150-160 chars optimal for featured snippets)
    if 150 <= len(meta) <= 160:
        score += 10
    else:
        tasks.append("Optimize meta description length (150-160 characters) for featured snippets")
    
    # Check for question format (good for featured snippets)
    if meta.strip().endswith("?"):
        score += 5
    else:
        tasks.append("Consider question format in meta descriptions for better featured snippet chances")
    
    # Check for structured information
    if any(word in meta.lower() for word in ["how", "what", "why", "when", "where"]):
        score += 5
    else:
        tasks.append("Include question words (how, what, why) in meta descriptions")
    
    return score, tasks

def check_alt_text(page: Dict[str, Any]) -> Tuple[int, List[str]]:
    """Check alt text for images"""
    score = 0
    tasks = []
    
    images = page.get("images", []) or []
    
    if not images:
        return 15, []  # No images = perfect score
    
    total_images = len(images)
    images_with_alt = sum(1 for img in images if img.get("alt", "").strip())
    
    if total_images == 0:
        return 15, []
    
    alt_percentage = (images_with_alt / total_images) * 100
    
    if alt_percentage >= 90:
        score += 15
    elif alt_percentage >= 70:
        score += 10
        tasks.append(f"Add alt text to {total_images - images_with_alt} images")
    else:
        score += 5
        tasks.append(f"Add descriptive alt text to {total_images - images_with_alt} images for better AI understanding")
    
    return score, tasks

def check_structured_data(page: Dict[str, Any]) -> Tuple[int, List[str]]:
    """Check for structured data (JSON-LD)"""
    score = 0
    tasks = []
    
    schema = page.get("schema", {})
    json_ld = schema.get("json_ld", [])
    
    if not json_ld:
        tasks.append("Add JSON-LD structured data for better AI understanding")
        return 0, tasks
    
    # Check for relevant schema types
    schema_types = []
    for item in json_ld:
        if isinstance(item, dict):
            schema_type = item.get("@type", "")
            if schema_type:
                schema_types.append(schema_type)
    
    if any("Organization" in str(schema_types) or "WebSite" in str(schema_types)):
        score += 10
    else:
        tasks.append("Add Organization or WebSite schema markup")
    
    if any("Article" in str(schema_types) or "BlogPosting" in str(schema_types)):
        score += 5
    else:
        tasks.append("Consider adding Article or BlogPosting schema for content pages")
    
    if any("FAQPage" in str(schema_types) or "Question" in str(schema_types)):
        score += 5
    else:
        tasks.append("Add FAQ schema markup for question-answer content")
    
    return score, tasks

def check_ai_content_structure(page: Dict[str, Any]) -> Tuple[int, List[str]]:
    """Check content structure for AI consumption"""
    score = 0
    tasks = []
    
    h1 = page.get("h1", []) or []
    h2 = page.get("h2", []) or []
    h3 = page.get("h3", []) or []
    
    # Check for clear heading hierarchy
    if h1:
        score += 5
    else:
        tasks.append("Add clear H1 heading for better content structure")
    
    if len(h2) >= 2:
        score += 5
    else:
        tasks.append("Add more H2 headings to structure content for AI consumption")
    
    # Check for list content (good for AI)
    content = page.get("content", "") or ""
    has_lists = any(marker in content for marker in ["•", "-", "1.", "2.", "3."])
    
    if has_lists:
        score += 5
    else:
        tasks.append("Use bullet points or numbered lists for better AI content parsing")
    
    # Check for question-answer format
    has_questions = any(word in content.lower() for word in ["what is", "how to", "why", "when", "where"])
    if has_questions:
        score += 5
    else:
        tasks.append("Include question-answer format in content for better AI understanding")
    
    return score, tasks

# ---------------- GEO Helper Functions ----------------

def check_hreflang(page: Dict[str, Any]) -> Tuple[int, List[str]]:
    """Check hreflang implementation"""
    score = 0
    tasks = []
    
    hreflang = page.get("hreflang", []) or []
    
    if not hreflang:
        tasks.append("Implement hreflang tags for multilingual targeting")
        return 0, tasks
    
    # Check for proper hreflang structure
    valid_hreflang = 0
    for item in hreflang:
        if isinstance(item, dict) and "hreflang" in item and "href" in item:
            valid_hreflang += 1
    
    if valid_hreflang >= 2:
        score += 25
    elif valid_hreflang >= 1:
        score += 15
        tasks.append("Add more hreflang tags for complete multilingual coverage")
    else:
        tasks.append("Fix hreflang implementation - ensure proper structure")
    
    return score, tasks

def check_local_schema(page: Dict[str, Any]) -> Tuple[int, List[str]]:
    """Check for LocalBusiness schema"""
    score = 0
    tasks = []
    
    schema = page.get("schema", {})
    json_ld = schema.get("json_ld", [])
    
    has_local_schema = False
    for item in json_ld:
        if isinstance(item, dict):
            schema_type = item.get("@type", "")
            if "LocalBusiness" in str(schema_type) or "Organization" in str(schema_type):
                has_local_schema = True
                break
    
    if has_local_schema:
        score += 20
    else:
        tasks.append("Add LocalBusiness or Organization schema markup")
    
    return score, tasks

def check_nap_consistency(page: Dict[str, Any]) -> Tuple[int, List[str]]:
    """Check NAP (Name, Address, Phone) consistency"""
    score = 0
    tasks = []
    
    nap = page.get("nap", {}) or {}
    phone = nap.get("phone", "") or ""
    address = nap.get("address", "") or ""
    
    if phone and address:
        score += 20
    elif phone or address:
        score += 10
        tasks.append("Complete NAP information - add missing phone or address")
    else:
        tasks.append("Add NAP (Name, Address, Phone) information for local SEO")
    
    return score, tasks

def check_geographic_targeting(page: Dict[str, Any]) -> Tuple[int, List[str]]:
    """Check geographic targeting signals"""
    score = 0
    tasks = []
    
    # Check for location mentions in content
    content = page.get("content", "") or ""
    title = page.get("title", "") or ""
    
    # Look for geographic indicators
    geo_indicators = ["city", "country", "region", "local", "near me", "in", "at"]
    has_geo_signals = any(indicator in content.lower() or indicator in title.lower() for indicator in geo_indicators)
    
    if has_geo_signals:
        score += 20
    else:
        tasks.append("Add geographic targeting signals in content and titles")
    
    return score, tasks

def check_local_seo_elements(page: Dict[str, Any]) -> Tuple[int, List[str]]:
    """Check local SEO elements"""
    score = 0
    tasks = []
    
    # Check for local keywords
    content = page.get("content", "") or ""
    title = page.get("title", "") or ""
    
    local_keywords = ["service", "business", "company", "local", "near me"]
    has_local_keywords = any(keyword in content.lower() or keyword in title.lower() for keyword in local_keywords)
    
    if has_local_keywords:
        score += 15
    else:
        tasks.append("Include local business keywords in content and titles")
    
    return score, tasks

# ---------------- Analysis Functions ----------------

def analyze_aeo_opportunities(pages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Detailed AEO analysis"""
    return {
        "faq_opportunities": "Analyze FAQ content opportunities",
        "meta_optimization": "Meta description optimization for featured snippets",
        "alt_text_gaps": "Image alt text optimization opportunities",
        "schema_opportunities": "Structured data implementation opportunities"
    }

def analyze_geo_opportunities(pages: List[Dict[str, Any]], audit_data: Dict[str, Any]) -> Dict[str, Any]:
    """Detailed GEO analysis"""
    return {
        "hreflang_opportunities": "Multilingual targeting opportunities",
        "local_schema_gaps": "LocalBusiness schema implementation",
        "nap_consistency": "NAP consistency analysis",
        "geographic_targeting": "Geographic targeting optimization"
    }
