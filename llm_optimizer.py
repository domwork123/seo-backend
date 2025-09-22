# llm_optimizer.py — LLM-powered optimization using OpenAI
import os
import json
from typing import Dict, Any, List
from optimizer import optimize_site

# Initialize OpenAI client
try:
    import openai
    openai.api_key = os.getenv("LLM_API_KEY")
except ImportError:
    openai = None

async def optimize_with_llm(audit_data: Dict[str, Any], scores: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate LLM-powered optimizations using OpenAI GPT-4o-mini
    """
    try:
        # Get base optimizations first
        base_optimizations = optimize_site(audit_data, scores)
        
        # Check if OpenAI is available
        if not openai:
            print("OpenAI not available, using base optimizations")
            return base_optimizations
        
        # Extract key information for LLM
        site_url = audit_data.get("url", "")
        pages = audit_data.get("pages", [])
        languages = audit_data.get("languages", [])
        
        # Build context for LLM
        context = {
            "site_url": site_url,
            "languages": languages,
            "pages_count": len(pages),
            "seo_score": scores.get("seo_score", 0),
            "aeo_score": scores.get("aeo_score", 0),
            "overall_score": scores.get("overall", 0)
        }
        
        # Create LLM prompt
        prompt = f"""
You are an expert SEO and content optimization specialist. Analyze this website audit data and provide enhanced, actionable optimizations.

Website: {site_url}
Languages: {', '.join(languages)}
Pages analyzed: {len(pages)}
SEO Score: {scores.get('seo_score', 0)}/100
AEO Score: {scores.get('aeo_score', 0)}/100
Overall Score: {scores.get('overall', 0)}/100

Current issues found:
- {len([p for p in pages if not p.get('title')])} pages missing titles
- {len([p for p in pages if not p.get('meta')])} pages missing meta descriptions
- {len([p for p in pages if not p.get('h1')])} pages missing H1 tags
- {sum(len(p.get('images', [])) for p in pages)} total images, many missing ALT text

For each page that needs optimization, provide:
1. Enhanced title (50-60 chars, keyword-rich, compelling)
2. Meta description (150-160 chars, action-oriented)
3. H1 tag (clear, keyword-focused)
4. FAQ section (3-5 relevant questions with detailed answers)
5. JSON-LD schema (Organization, LocalBusiness, or Product as appropriate)
6. ALT text suggestions for images missing them

Focus on:
- Local SEO if business detected
- E-commerce optimization if product pages found
- Content authority and expertise
- User intent matching
- Technical SEO improvements

Return as JSON with this structure:
{{
  "brand_guess": "detected brand name",
  "global": {{
    "new_title": "site-wide title template",
    "new_meta": "site-wide meta template", 
    "new_h1": "site-wide H1 template",
    "faq": [{{"q": "question", "a": "answer"}}],
    "json_ld": "Organization schema JSON-LD"
  }},
  "pages_optimized": [
    {{
      "url": "page_url",
      "new_title": "optimized title",
      "new_meta": "optimized meta description",
      "new_h1": "optimized H1",
      "faq": [{{"q": "question", "a": "answer"}}],
      "json_ld": "page-specific JSON-LD",
      "alt_text_suggestions": ["alt text for image1", "alt text for image2"],
      "slug_suggestion": "improved-url-slug"
    }}
  ]
}}

Make all content production-ready and copy-pasteable.
"""

        # Call OpenAI API
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert SEO specialist. Provide actionable, production-ready optimizations in valid JSON format."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=4000,
            temperature=0.7
        )
        
        # Parse LLM response
        llm_content = response.choices[0].message.content.strip()
        
        # Try to extract JSON from response
        try:
            # Look for JSON block in response
            if "```json" in llm_content:
                json_start = llm_content.find("```json") + 7
                json_end = llm_content.find("```", json_start)
                json_str = llm_content[json_start:json_end].strip()
            elif "```" in llm_content:
                json_start = llm_content.find("```") + 3
                json_end = llm_content.find("```", json_start)
                json_str = llm_content[json_start:json_end].strip()
            else:
                json_str = llm_content
            
            llm_optimizations = json.loads(json_str)
            
            # Merge with base optimizations for fallback
            if not llm_optimizations.get("pages_optimized"):
                llm_optimizations["pages_optimized"] = base_optimizations.get("pages_optimized", [])
            
            return llm_optimizations
            
        except json.JSONDecodeError:
            # Fallback to base optimizations if LLM response is invalid
            print(f"LLM response parsing failed, using base optimizations: {llm_content[:200]}...")
            return base_optimizations
            
    except Exception as e:
        print(f"LLM optimization error: {e}")
        # Fallback to base optimizations
        return optimize_site(audit_data, scores)
