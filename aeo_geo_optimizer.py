# aeo_geo_optimizer.py — AEO + GEO focused optimization functions
import json
import re
from typing import Dict, Any, List, Tuple
from urllib.parse import urlparse

def detect_faq(url: str, page_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detect FAQ content on a page and suggest improvements.
    Returns FAQ analysis with suggestions for optimization.
    """
    content = page_data.get("content", "") or ""
    title = page_data.get("title", "") or ""
    h1 = page_data.get("h1", []) or []
    h2 = page_data.get("h2", []) or []
    
    # Look for FAQ indicators
    faq_indicators = ["faq", "frequently asked", "questions", "answers", "q&a", "common questions"]
    has_faq_section = any(indicator in content.lower() for indicator in faq_indicators)
    
    # Extract potential Q&A pairs
    qa_pairs = extract_qa_pairs(content)
    
    # Check for FAQ schema
    schema = page_data.get("schema", {})
    json_ld = schema.get("json_ld", [])
    has_faq_schema = any("FAQPage" in str(item) or "Question" in str(item) for item in json_ld)
    
    return {
        "has_faq_content": has_faq_section,
        "qa_pairs_found": len(qa_pairs),
        "qa_pairs": qa_pairs,
        "has_faq_schema": has_faq_schema,
        "suggestions": generate_faq_suggestions(has_faq_section, qa_pairs, has_faq_schema, url)
    }

def extract_qa_pairs(content: str) -> List[Dict[str, str]]:
    """Extract Q&A pairs from content"""
    qa_pairs = []
    
    # Look for question patterns
    question_patterns = [
        r"Q:\s*(.+?)\s*A:\s*(.+?)(?=Q:|$)",
        r"Question:\s*(.+?)\s*Answer:\s*(.+?)(?=Question:|$)",
        r"(.+?)\?\s*(.+?)(?=\n\n|\n[A-Z]|$)"
    ]
    
    for pattern in question_patterns:
        matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
        for match in matches:
            if len(match) == 2:
                qa_pairs.append({
                    "question": match[0].strip(),
                    "answer": match[1].strip()
                })
    
    return qa_pairs

def generate_faq_suggestions(has_faq: bool, qa_pairs: List[Dict[str, str]], has_schema: bool, url: str) -> List[str]:
    """Generate FAQ optimization suggestions"""
    suggestions = []
    
    if not has_faq:
        suggestions.append("Add FAQ section with common customer questions")
        suggestions.append("Include questions like 'What services do you offer?' and 'How can I contact you?'")
    
    if len(qa_pairs) < 3:
        suggestions.append("Add more Q&A pairs (aim for 5-10 common questions)")
    
    if not has_schema:
        suggestions.append("Add FAQ schema markup (JSON-LD) for better AI understanding")
    
    if qa_pairs:
        suggestions.append("Optimize existing Q&A for featured snippets (keep answers under 160 characters)")
    
    return suggestions

def generate_faq_schema(qas: List[Dict[str, str]], page_url: str) -> str:
    """
    Generate JSON-LD FAQ schema markup.
    Returns ready-to-use JSON-LD script.
    """
    if not qas:
        return ""
    
    faq_schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": []
    }
    
    for qa in qas:
        faq_item = {
            "@type": "Question",
            "name": qa.get("question", ""),
            "acceptedAnswer": {
                "@type": "Answer",
                "text": qa.get("answer", "")
            }
        }
        faq_schema["mainEntity"].append(faq_item)
    
    return json.dumps(faq_schema, indent=2)

def extract_images(url: str, page_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract images without alt text and suggest alternatives.
    Returns image analysis with AI-suggested alt text.
    """
    images = page_data.get("images", []) or []
    
    images_without_alt = []
    images_with_alt = []
    
    for img in images:
        alt_text = img.get("alt", "") or ""
        src = img.get("src", "") or ""
        
        if not alt_text.strip():
            images_without_alt.append({
                "src": src,
                "suggested_alt": generate_alt_text_suggestion(src, page_data)
            })
        else:
            images_with_alt.append({
                "src": src,
                "alt": alt_text
            })
    
    return {
        "total_images": len(images),
        "images_without_alt": len(images_without_alt),
        "images_with_alt": len(images_with_alt),
        "missing_alt_images": images_without_alt,
        "suggestions": generate_alt_text_suggestions(images_without_alt)
    }

def generate_alt_text_suggestion(image_src: str, page_data: Dict[str, Any]) -> str:
    """Generate AI-suggested alt text for an image"""
    # Extract context from page
    title = page_data.get("title", "") or ""
    h1 = page_data.get("h1", []) or []
    content = page_data.get("content", "") or ""
    
    # Simple heuristic-based alt text generation
    if "logo" in image_src.lower():
        return f"Logo for {title or 'the website'}"
    elif "product" in image_src.lower():
        return f"Product image for {title or 'the product'}"
    elif "team" in image_src.lower() or "staff" in image_src.lower():
        return f"Team member photo"
    elif "office" in image_src.lower() or "building" in image_src.lower():
        return f"Office or building image"
    else:
        # Generic descriptive alt text
        return f"Image related to {title or 'the content'}"

def generate_alt_text_suggestions(images_without_alt: List[Dict[str, Any]]) -> List[str]:
    """Generate alt text optimization suggestions"""
    suggestions = []
    
    if images_without_alt:
        suggestions.append(f"Add descriptive alt text to {len(images_without_alt)} images")
        suggestions.append("Use specific, descriptive alt text that explains the image content")
        suggestions.append("Avoid generic alt text like 'image' or 'photo'")
        suggestions.append("Include relevant keywords in alt text for better AI understanding")
    
    return suggestions

def optimize_meta_description(text: str, page_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Optimize meta description for featured snippets.
    Returns optimized meta description with suggestions.
    """
    if not text:
        return {
            "original": "",
            "optimized": "",
            "suggestions": ["Add meta description optimized for featured snippets"]
        }
    
    # Check current meta description
    current_length = len(text)
    is_question_format = text.strip().endswith("?")
    has_question_words = any(word in text.lower() for word in ["how", "what", "why", "when", "where"])
    
    # Generate optimized version
    optimized = text
    
    # Length optimization
    if current_length < 150:
        optimized += " Learn more about our services and solutions."
    elif current_length > 160:
        optimized = optimized[:157] + "..."
    
    # Question format optimization
    if not is_question_format and not has_question_words:
        # Try to convert to question format
        if "service" in text.lower():
            optimized = f"What services do we offer? {text}"
        elif "about" in text.lower():
            optimized = f"What is {text.lower().replace('about', '')}?"
    
    suggestions = []
    if current_length < 150 or current_length > 160:
        suggestions.append("Optimize meta description length (150-160 characters)")
    if not is_question_format:
        suggestions.append("Consider question format for better featured snippet chances")
    if not has_question_words:
        suggestions.append("Include question words (how, what, why) for AI optimization")
    
    return {
        "original": text,
        "optimized": optimized,
        "suggestions": suggestions
    }

def run_llm_queries(brand: str, queries: List[str], page_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run LLM queries to test brand visibility.
    Returns query results with visibility scores.
    """
    # Default queries if none provided
    if not queries:
        queries = [
            f"What is {brand}?",
            f"What services does {brand} offer?",
            f"How can I contact {brand}?",
            f"Where is {brand} located?",
            f"What are {brand}'s main products?"
        ]
    
    # Extract brand information from page
    title = page_data.get("title", "") or ""
    content = page_data.get("content", "") or ""
    meta = page_data.get("meta", "") or ""
    
    # Simple brand visibility analysis (in real implementation, this would use actual LLM API)
    brand_mentions = content.lower().count(brand.lower())
    title_mentions = title.lower().count(brand.lower())
    meta_mentions = meta.lower().count(brand.lower())
    
    # Calculate visibility score
    visibility_score = min(100, (brand_mentions * 10) + (title_mentions * 20) + (meta_mentions * 15))
    
    query_results = []
    for query in queries:
        # Simulate LLM query results
        query_results.append({
            "query": query,
            "visibility_score": visibility_score,
            "mentioned": brand_mentions > 0,
            "linked": False,  # Would check for actual links in real implementation
            "snippet_potential": visibility_score > 50
        })
    
    return {
        "brand": brand,
        "overall_visibility": visibility_score,
        "query_results": query_results,
        "suggestions": generate_llm_visibility_suggestions(visibility_score, brand_mentions)
    }

def generate_llm_visibility_suggestions(visibility_score: int, brand_mentions: int) -> List[str]:
    """Generate suggestions for improving LLM visibility"""
    suggestions = []
    
    if visibility_score < 30:
        suggestions.append("Increase brand mentions in content for better AI recognition")
        suggestions.append("Add brand name to page titles and meta descriptions")
        suggestions.append("Create content that answers common questions about your brand")
    elif visibility_score < 60:
        suggestions.append("Optimize existing content for better AI understanding")
        suggestions.append("Add structured data to help AI understand your brand")
        suggestions.append("Create FAQ content that AI can easily extract")
    else:
        suggestions.append("Maintain current visibility and add more specific content")
        suggestions.append("Focus on long-tail questions and detailed answers")
    
    return suggestions

def check_geo_signals(url: str, page_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check geographic optimization signals.
    Returns GEO analysis with optimization suggestions.
    """
    # Extract domain for country detection
    domain = urlparse(url).netloc
    tld = domain.split('.')[-1] if '.' in domain else ''
    
    # Check hreflang
    hreflang = page_data.get("hreflang", []) or []
    hreflang_count = len([item for item in hreflang if isinstance(item, dict) and "hreflang" in item])
    
    # Check LocalBusiness schema
    schema = page_data.get("schema", {})
    json_ld = schema.get("json_ld", [])
    has_local_schema = any("LocalBusiness" in str(item) or "Organization" in str(item) for item in json_ld)
    
    # Check NAP consistency
    nap = page_data.get("nap", {}) or {}
    phone = nap.get("phone", "") or ""
    address = nap.get("address", "") or ""
    nap_completeness = sum([bool(phone), bool(address)]) / 2 * 100
    
    # Check geographic content
    content = page_data.get("content", "") or ""
    title = page_data.get("title", "") or ""
    geo_indicators = ["city", "country", "region", "local", "near me", "in", "at"]
    has_geo_content = any(indicator in content.lower() or indicator in title.lower() for indicator in geo_indicators)
    
    return {
        "domain_tld": tld,
        "hreflang_count": hreflang_count,
        "has_local_schema": has_local_schema,
        "nap_completeness": nap_completeness,
        "has_geo_content": has_geo_content,
        "suggestions": generate_geo_suggestions(hreflang_count, has_local_schema, nap_completeness, has_geo_content)
    }

def generate_geo_suggestions(hreflang_count: int, has_local_schema: bool, nap_completeness: float, has_geo_content: bool) -> List[str]:
    """Generate geographic optimization suggestions"""
    suggestions = []
    
    if hreflang_count < 2:
        suggestions.append("Implement hreflang tags for multilingual targeting")
    
    if not has_local_schema:
        suggestions.append("Add LocalBusiness or Organization schema markup")
    
    if nap_completeness < 100:
        suggestions.append("Complete NAP (Name, Address, Phone) information")
    
    if not has_geo_content:
        suggestions.append("Add geographic targeting signals in content and titles")
        suggestions.append("Include location-specific keywords")
    
    return suggestions

def generate_blog_post(keyword: str, brand: str, page_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a blog post optimized for AEO.
    Returns blog post content with FAQ structure and schema.
    """
    # Generate FAQ-style content
    faq_content = generate_faq_content(keyword, brand)
    
    # Create blog post structure
    blog_post = {
        "title": f"Complete Guide to {keyword.title()}: Everything You Need to Know",
        "introduction": f"Learn everything about {keyword} with our comprehensive guide. We answer the most common questions and provide expert insights.",
        "faq_section": faq_content,
        "conclusion": f"Now you have a complete understanding of {keyword}. For more information, contact {brand}.",
        "meta_description": f"Complete guide to {keyword}. Learn everything you need to know with expert answers to common questions.",
        "schema_markup": generate_faq_schema(faq_content, "")
    }
    
    return blog_post

def generate_faq_content(keyword: str, brand: str) -> List[Dict[str, str]]:
    """Generate FAQ content for a given keyword"""
    return [
        {
            "question": f"What is {keyword}?",
            "answer": f"{keyword} is a comprehensive solution that helps businesses achieve their goals. Learn more about how {brand} can help you with {keyword}."
        },
        {
            "question": f"How does {keyword} work?",
            "answer": f"{keyword} works by providing specialized services and solutions. Our team at {brand} has extensive experience in {keyword} implementation."
        },
        {
            "question": f"Why choose {brand} for {keyword}?",
            "answer": f"{brand} offers expert {keyword} services with proven results. We provide comprehensive support and guidance throughout the process."
        },
        {
            "question": f"What are the benefits of {keyword}?",
            "answer": f"The benefits of {keyword} include improved efficiency, better results, and expert guidance. Contact {brand} to learn more about our {keyword} services."
        }
    ]
