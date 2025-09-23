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
        
        # Get base optimizations but filter out sitemap URLs first
        filtered_audit_data = audit_data.copy()
        if "pages" in filtered_audit_data:
            filtered_pages = []
            for page in filtered_audit_data["pages"]:
                if isinstance(page, dict):
                    url = page.get('url', '')
                    # Apply same filtering as LLM optimization
                    technical_patterns = [
                        'sitemap', 'robots.txt', '.xml', 'feed', 'rss', 'atom', 
                        'sitemap.xml', 'post-sitemap', 'page-sitemap', 'tag-sitemap',
                        'category-sitemap', 'product-sitemap', 'job-sitemap',
                        'news-sitemap', 'image-sitemap', 'video-sitemap'
                    ]
                    is_technical_file = any(pattern in url.lower() for pattern in technical_patterns)
                    has_technical_extension = any(url.lower().endswith(ext) for ext in ['.xml', '.txt', '.rss', '.atom'])
                    
                    if not (is_technical_file or has_technical_extension):
                        filtered_pages.append(page)
            filtered_audit_data["pages"] = filtered_pages
        
        base_optimizations = optimize_site(filtered_audit_data)
        print(f"DEBUG: Base optimizations obtained successfully (filtered) - {len(base_optimizations.get('pages_optimized', []))} pages")
        
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
        
        # PROFESSIONAL-GRADE CONTENT FILTERING
        content_pages = []
        skipped_count = 0
        
        for page in pages:
            url = page.get('url', '')
            
            # COMPREHENSIVE TECHNICAL FILE FILTERING
            technical_patterns = [
                'sitemap', 'robots.txt', '.xml', 'feed', 'rss', 'atom', 
                'sitemap.xml', 'post-sitemap', 'page-sitemap', 'tag-sitemap',
                'category-sitemap', 'product-sitemap', 'job-sitemap',
                'news-sitemap', 'image-sitemap', 'video-sitemap'
            ]
            
            # Check if URL contains any technical patterns
            is_technical_file = any(pattern in url.lower() for pattern in technical_patterns)
            
            # Check if URL ends with technical extensions
            technical_extensions = ['.xml', '.txt', '.rss', '.atom']
            has_technical_extension = any(url.lower().endswith(ext) for ext in technical_extensions)
            
            # Skip all technical files
            if is_technical_file or has_technical_extension:
                skipped_count += 1
                print(f"DEBUG: SKIPPING technical file: {url}")
                continue
            
            # INCLUDE ANY PAGE THAT'S NOT A TECHNICAL FILE - NO CONTENT VALIDATION
            content_pages.append(page)
            print(f"DEBUG: INCLUDING content page: {url}")
        
        print(f"DEBUG: FILTERING COMPLETE - {len(content_pages)} content pages, {skipped_count} pages skipped")
        
        pages = content_pages
        
        # FINAL SAFETY CHECK - Remove any remaining sitemap URLs
        final_pages = []
        for page in pages:
            url = page.get('url', '')
            if 'sitemap' not in url.lower() and not url.endswith('.xml'):
                final_pages.append(page)
            else:
                print(f"DEBUG: FINAL SAFETY - Removing sitemap URL: {url}")
        
        pages = final_pages
        print(f"DEBUG: FINAL RESULT - {len(pages)} content pages ready for optimization")
        
        # If no content pages found, try with even more lenient criteria
        if len(pages) == 0:
            print("DEBUG: No content pages found - trying with ultra-lenient criteria")
            ultra_lenient_pages = []
            # Use original pages list, not the filtered one
            original_pages = audit_data.get("pages", [])
            for page in original_pages:
                if not isinstance(page, dict):
                    continue
                url = page.get('url', '')
                # Skip only obvious technical files
                if any(ext in url.lower() for ext in ['.xml', '.txt', '.rss', '.atom']) or 'sitemap' in url.lower():
                    continue
                # Include ANY page that's not a technical file
                ultra_lenient_pages.append(page)
                print(f"DEBUG: ULTRA-LENIENT - Including page: {url}")
            
            if ultra_lenient_pages:
                pages = ultra_lenient_pages
                print(f"DEBUG: ULTRA-LENIENT RESULT - {len(pages)} pages ready for optimization")
            else:
                print("DEBUG: No pages found even with ultra-lenient criteria - returning base optimizations only")
                return base_optimizations
        
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
            for page in pages:  # Process ALL discovered pages for comprehensive optimization
                # Safe access to page data with None checks
                page_info = {
                    'url': page.get('url', '') or '',
                    'title': page.get('title', '') or '',
                    'meta': page.get('meta', '') or '',
                    'h1': page.get('h1', []) or [],
                    'h2': page.get('h2', []) or [],
                    'word_count': page.get('word_count', 0) or 0,
                    'lang': page.get('lang', '') or '',
                    'images_count': len(page.get('images', []) or [])
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

        # Call OpenAI API with simplified but comprehensive prompt
        comprehensive_prompt = f"""
You are an expert SEO consultant specializing in AI-driven search optimization (AEO), Geographic SEO (GEO), and traditional SEO. 

Analyze this website: {site_url}
Pages: {len(pages)} pages found
Languages: {languages_str}

For EACH discovered page, provide comprehensive optimization tasks organized by sector. This is for a future-focused SEO tool that prepares businesses for AI search, LLM optimization, and AEO.

Return JSON format:
{{
  "pages_optimized": [
    {{
      "url": "page_url",
      "page_type": "product|category|content|homepage|contact|about",
      "priority": "high|medium|low",
      "basic_seo": {{
        "new_title": "Optimized title (50-60 chars)",
        "new_meta": "Meta description (150-160 chars)",
        "new_h1": "H1 heading",
        "h2_suggestions": ["H2 suggestion 1", "H2 suggestion 2"],
        "h3_suggestions": ["H3 suggestion 1", "H3 suggestion 2"]
      }},
      "aeo_optimization": {{
        "faq_suggestions": [
          {{"question": "FAQ question 1", "answer": "Detailed answer 1"}},
          {{"question": "FAQ question 2", "answer": "Detailed answer 2"}}
        ],
        "structured_data": "JSON-LD schema markup for this page type",
        "ai_friendly_content": "Content optimization suggestions for AI search",
        "answer_engine_tasks": ["Task 1", "Task 2", "Task 3"]
      }},
      "geo_optimization": {{
        "local_seo_tasks": ["Local SEO task 1", "Local SEO task 2"],
        "hreflang_suggestions": "Hreflang implementation suggestions",
        "location_signals": "Location-based optimization tasks",
        "geo_schema": "Geographic schema markup if applicable"
      }},
      "technical_seo": {{
        "schema_markup": "Complete JSON-LD schema for this page",
        "canonical_suggestions": "Canonical URL recommendations",
        "internal_linking": "Internal linking strategy for this page",
        "technical_tasks": ["Technical task 1", "Technical task 2"]
      }},
      "content_optimization": {{
        "content_gaps": ["Content gap 1", "Content gap 2"],
        "keyword_optimization": "Keyword optimization strategy",
        "content_structure": "Content structure improvements",
        "user_intent": "User intent optimization suggestions"
      }},
      "performance_tasks": {{
        "image_optimization": ["Image optimization task 1", "Image optimization task 2"],
        "speed_optimization": ["Speed optimization task 1", "Speed optimization task 2"],
        "mobile_optimization": ["Mobile optimization task 1", "Mobile optimization task 2"]
      }},
      "future_ai_optimization": {{
        "llm_search_preparation": "Tasks to prepare for LLM search",
        "ai_answer_optimization": "Optimize for AI answer snippets",
        "voice_search_optimization": "Voice search optimization tasks",
        "ai_crawlability": "AI crawler optimization tasks"
      }}
    }}
  ]
}}

Focus on comprehensive, actionable tasks for each page that will help businesses rank in the evolving search landscape.
"""
        
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an SEO expert. Return only valid JSON with optimization suggestions."},
                {"role": "user", "content": comprehensive_prompt}
            ],
            max_tokens=2000,
            temperature=0.3
        )
        
        # Parse LLM response
        llm_content = response.choices[0].message.content.strip()
        print(f"DEBUG: LLM response length: {len(llm_content)}")
        print(f"DEBUG: LLM response preview: {llm_content[:200]}...")
        
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
            try:
                return optimize_site(audit_data)
            except Exception as base_error:
                print(f"Base optimization also failed: {base_error}")
                # Final fallback - return minimal optimizations for ANY website
                return {
                    "pages_optimized": [{
                        "url": audit_data.get("url", ""),
                        "new_title": "Add a compelling title tag",
                        "new_meta": "Add a descriptive meta description",
                        "new_h1": "Add a clear H1 heading",
                        "fallback": True,
                        "error": f"All optimization methods failed: {str(e)}"
                    }],
                    "error": f"Fallback optimizations provided due to: {str(e)}"
                }
            
    except Exception as e:
        print(f"LLM optimization error: {e}")
        # Fallback to comprehensive format instead of old optimize_site
        print(f"LLM optimization failed, using comprehensive fallback format")
        # Final fallback - return comprehensive optimizations for ANY website
        return {
                "pages_optimized": [{
                    "url": audit_data.get("url", ""),
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
                    "error": f"Comprehensive fallback optimizations provided due to: {str(e)}"
                }],
                "error": f"Fallback optimizations provided due to: {str(e)}"
            }
