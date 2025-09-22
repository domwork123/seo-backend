# llm_optimizer.py — LLM-powered optimization using OpenAI
import os
import json
from typing import Dict, Any, List
from optimizer import optimize_site
from llm_ruleset import get_optimization_guidelines, detect_industry_from_content, prioritize_recommendations

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
        print("DEBUG: Getting base optimizations...")
        print(f"DEBUG: audit_data type: {type(audit_data)}")
        print(f"DEBUG: scores type: {type(scores)}")
        print(f"DEBUG: audit_data keys: {list(audit_data.keys()) if isinstance(audit_data, dict) else 'Not a dict'}")
        print(f"DEBUG: scores keys: {list(scores.keys()) if isinstance(scores, dict) else 'Not a dict'}")
        
        base_optimizations = optimize_site(audit_data)
        print("DEBUG: Base optimizations obtained successfully")
        
        # Check if OpenAI is available
        if not openai:
            print("OpenAI not available, using base optimizations")
            return base_optimizations
        
        # Extract key information for LLM with safety checks
        site_url = audit_data.get("url", "")
        pages = audit_data.get("pages", [])
        languages = audit_data.get("languages", [])
        
        # Ensure pages is a list and filter out non-dict items and sitemap URLs
        if not isinstance(pages, list):
            pages = []
        pages = [p for p in pages if isinstance(p, dict)]
        
        # Filter out sitemap URLs and other non-content pages
        content_pages = []
        for page in pages:
            url = page.get('url', '')
            # Skip sitemap URLs, robots.txt, and other non-content pages
            if any(skip in url.lower() for skip in ['sitemap', 'robots.txt', '.xml', 'feed', 'rss']):
                continue
            
            # Only include pages with some content (more lenient filtering)
            has_title = bool(page.get('title', '').strip())
            has_meta = bool(page.get('meta', '').strip())
            has_h1 = bool(page.get('h1', []))
            has_content = page.get('word_count', 0) > 20  # Reduced from 50 to 20 words
            
            # Must have at least 1 of: title, meta, h1, or some content
            content_score = sum([has_title, has_meta, has_h1, has_content])
            if content_score >= 1:
                content_pages.append(page)
                print(f"DEBUG: Including page {url} (content score: {content_score})")
            else:
                print(f"DEBUG: Skipping page {url} (content score: {content_score} - insufficient content)")
        
        pages = content_pages
        print(f"DEBUG: Filtered to {len(pages)} content pages with substantial content")
        
        # Ensure languages is a list
        if not isinstance(languages, list):
            languages = []
        
        # Build context for LLM with safe access
        scores_data = scores.get("scores", {}) if isinstance(scores, dict) else {}
        context = {
            "site_url": site_url,
            "languages": languages,
            "pages_count": len(pages),
            "seo_score": scores_data.get("seo", 0),
            "aeo_score": scores_data.get("aeo", 0),
            "overall_score": scores_data.get("overall", 0)
        }
        
        # Create LLM prompt with error handling
        try:
            print("DEBUG: Starting LLM prompt generation...")
            # Safe string operations
            languages_str = ', '.join(str(l) for l in languages) if languages else 'Unknown'
            print(f"DEBUG: Languages processed: {languages_str}")
            
            # Count issues safely
            print("DEBUG: Counting missing titles...")
            missing_titles = len([p for p in pages if isinstance(p, dict) and not p.get('title')])
            print(f"DEBUG: Missing titles: {missing_titles}")
            
            print("DEBUG: Counting missing meta...")
            missing_meta = len([p for p in pages if isinstance(p, dict) and not p.get('meta')])
            print(f"DEBUG: Missing meta: {missing_meta}")
            
            print("DEBUG: Counting missing H1...")
            missing_h1 = len([p for p in pages if isinstance(p, dict) and not p.get('h1')])
            print(f"DEBUG: Missing H1: {missing_h1}")
            
            print("DEBUG: Counting total images...")
            total_images = sum(len(p.get('images', [])) for p in pages if isinstance(p, dict))
            print(f"DEBUG: Total images: {total_images}")
            
            # Detect industry and get comprehensive optimization guidelines
            industry = detect_industry_from_content(audit_data)
            guidelines = get_optimization_guidelines(industry, "technical", "safe")
            print(f"DEBUG: Detected industry: {industry}")
            print(f"DEBUG: Using guidelines for: {industry}")
            
            # Build detailed page content for LLM analysis
            page_details = []
            for page in pages[:10]:  # Increased to 10 pages for more comprehensive analysis
                page_info = {
                    'url': page.get('url', ''),
                    'title': page.get('title', ''),
                    'meta': page.get('meta', ''),
                    'h1': page.get('h1', []),
                    'h2': page.get('h2', []),
                    'word_count': page.get('word_count', 0),
                    'lang': page.get('lang', ''),
                    'images_count': len(page.get('images', []))
                }
                page_details.append(page_info)
            
            prompt = f"""
You are an expert SEO and content optimization specialist following comprehensive professional guidelines. Analyze this website audit data and provide enhanced, actionable optimizations.

WEBSITE ANALYSIS:
Website: {site_url}
Languages: {languages_str}
Content pages analyzed: {len(pages)} (excluding sitemaps and technical files)
SEO Score: {scores_data.get('seo', 0)}/100
AEO Score: {scores_data.get('aeo', 0)}/100
Overall Score: {scores_data.get('overall', 0)}/100

DETECTED INDUSTRY: {industry}
OPTIMIZATION GUIDELINES: {guidelines['industry_template']}

CURRENT ISSUES FOUND:
- {missing_titles} pages missing titles
- {missing_meta} pages missing meta descriptions
- {missing_h1} pages missing H1 tags
- {total_images} total images, many missing ALT text

ACTUAL PAGE CONTENT TO ANALYZE:
{page_details}

PROFESSIONAL OPTIMIZATION RULES:
1. COVER ALL CORE CATEGORIES: SEO, AEO, GEO, Accessibility, Technical, Performance, UX, Conversions, Content
2. FOLLOW INDUSTRY-SPECIFIC TEMPLATES: {guidelines['industry_template']}
3. PRIORITIZE HIGH-IMPACT, LOW-EFFORT OPTIMIZATIONS FIRST
4. ENSURE COMPLIANCE WITH: Google Search Essentials, WCAG 2.1, Core Web Vitals, Schema.org
5. BASE RECOMMENDATIONS ON ACTUAL CONTENT, NOT URL PATTERNS
6. ONLY OPTIMIZE PAGES WITH SUBSTANTIAL CONTENT (title, meta, H1, or 50+ words)
7. FOLLOW E-E-A-T PRINCIPLES (Experience, Expertise, Authoritativeness, Trustworthiness)
8. IMPLEMENT STRUCTURED DATA APPROPRIATELY
9. FOCUS ON USER INTENT AND PEOPLE-FIRST CONTENT
10. PROVIDE ACTIONABLE, SPECIFIC RECOMMENDATIONS

CRITICAL INSTRUCTIONS:
- ONLY analyze pages that actually exist and have content
- Base optimizations on ACTUAL content, not URL patterns
- If a page has no title, meta, or H1, it likely doesn't exist - SKIP IT
- Analyze real content to understand what the page is about
- Do NOT make assumptions based on URL keywords
- Only provide optimizations for pages with actual, relevant content
- Follow industry-specific templates and guidelines
- Prioritize recommendations by impact/effort matrix

For each REAL content page that needs optimization, provide:
1. Enhanced title (50-60 chars, keyword-rich, compelling)
2. Meta description (150-160 chars, action-oriented)
3. H1 tag (clear, keyword-focused)
4. FAQ section (3-5 relevant questions with detailed answers)
5. JSON-LD schema (Organization, LocalBusiness, or Product as appropriate)

IMPORTANT: Provide optimizations for ALL pages that have content. Do not limit to just one page. 
Each page should get its own optimization section with the page URL clearly identified.
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
        except Exception as prompt_error:
            print(f"Error generating prompt: {prompt_error}")
            return base_optimizations

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
