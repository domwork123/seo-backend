# enhanced_audit.py - Advanced audit with JavaScript rendering support
import asyncio
import httpx
import re
from urllib.parse import urljoin, urlparse, urldefrag
from bs4 import BeautifulSoup
from w3lib.html import get_base_url
import tldextract
import json
from typing import List, Dict, Any, Set, Tuple, Optional
import lxml.html
import lxml.etree
import extruct
from playwright.async_api import async_playwright, Browser, Page

DEFAULT_TIMEOUT = 15
MAX_CONCURRENCY = 8
IMG_HEAD_LIMIT = 20
LINK_CHECK_LIMIT = 100

_phone_re = re.compile(r"(?:\+\d{1,3}\s?)?(?:\(?\d{1,4}\)?[\s.-]?)\d{3,4}[\s.-]?\d{3,4}")
_address_hint_re = re.compile(r"\b(street|str\.|ul\.|avenue|ave\.|road|rd\.|g\.)\b|\b(Vilnius|Kaunas|Rīga|Riga|Tallinn|Warsaw|Warszawa|Kraków|Praha|Praague|Berlin|Munich|Paris|Lyon|Madrid|Barcelona|Lisboa|Lisbon|Roma|Milano|Amsterdam|Rotterdam|Brussels|Antwerpen)\b", re.I)

_question_re = re.compile(r"^\s*(who|what|when|where|why|how|can|does|do|is|are|should|which|kada|kaip|kodėl|kas|ar|kur)\b.*\?\s*$", re.I)
_q_prefix_re = re.compile(r"^\s*(Q:|Question:|FAQ:)", re.I)
_a_prefix_re = re.compile(r"^\s*(A:|Answer:)", re.I)

HEADERS = {
    "User-Agent": "AscentIQAuditBot/1.0 (+https://tryevika.com; contact: audit@tryevika.com)"
}

def _norm(u: str) -> str:
    return urldefrag(u.strip())[0]

def _same_site(seed: str, other: str) -> bool:
    a, b = tldextract.extract(seed), tldextract.extract(other)
    return (a.domain, a.suffix) == (b.domain, b.suffix)

async def _fetch_with_js(browser: Browser, url: str, timeout: int = DEFAULT_TIMEOUT) -> Dict[str, Any]:
    """Fetch page with JavaScript rendering using Playwright"""
    try:
        page = await browser.new_page()
        await page.set_viewport_size({"width": 1920, "height": 1080})
        
        # Set headers
        await page.set_extra_http_headers(HEADERS)
        
        # Navigate with timeout
        response = await page.goto(url, wait_until="networkidle", timeout=timeout * 1000)
        
        if not response:
            return {"status": None, "html": "", "headers": {}}
        
        # Wait for content to load
        await page.wait_for_timeout(2000)  # Wait 2 seconds for dynamic content
        
        # Get the rendered HTML
        html = await page.content()
        headers = dict(response.headers)
        
        await page.close()
        
        return {
            "status": response.status,
            "html": html,
            "headers": headers,
            "url": response.url
        }
        
    except Exception as e:
        print(f"DEBUG: JavaScript rendering failed for {url}: {e}")
        return {"status": None, "html": "", "headers": {}, "error": str(e)}

async def _extract_links_enhanced(page: Page, base_url: str, seed_url: str) -> Tuple[List[str], List[str]]:
    """Enhanced link extraction that works with JavaScript-rendered content"""
    try:
        # Wait for links to be rendered
        await page.wait_for_selector("a[href]", timeout=5000)
        
        # Extract all links
        links = await page.evaluate("""
            () => {
                const links = Array.from(document.querySelectorAll('a[href]'));
                return links.map(link => ({
                    href: link.href,
                    text: link.textContent?.trim() || '',
                    isInternal: link.hostname === window.location.hostname
                }));
            }
        """)
        
        internal_links = []
        external_links = []
        
        for link in links:
            href = link['href']
            if not href or href.startswith('#') or href.startswith('javascript:'):
                continue
                
            try:
                # Normalize URL
                full_url = urljoin(base_url, href)
                full_url = _norm(full_url)
                
                if _same_site(seed_url, full_url):
                    internal_links.append(full_url)
                else:
                    external_links.append(full_url)
            except:
                continue
        
        return list(set(internal_links)), list(set(external_links))
        
    except Exception as e:
        print(f"DEBUG: Enhanced link extraction failed: {e}")
        return [], []

async def _analyze_page_enhanced(browser: Browser, url: str, seed: str) -> Dict[str, Any]:
    """Enhanced page analysis with JavaScript rendering"""
    try:
        page = await browser.new_page()
        await page.set_viewport_size({"width": 1920, "height": 1080})
        await page.set_extra_http_headers(HEADERS)
        
        # Navigate to page
        response = await page.goto(url, wait_until="networkidle", timeout=DEFAULT_TIMEOUT * 1000)
        
        if not response:
            await page.close()
            return {
                "url": url,
                "status": None,
                "title": "",
                "meta": "",
                "h1": [],
                "h2": [],
                "h3": [],
                "lang": "en",
                "canonical": url,
                "meta_robots": None,
                "x_robots_tag": None,
                "hreflang": [],
                "images": [],
                "links": {"internal": [], "external": [], "broken_internal": []},
                "schema": {"json_ld": [], "microdata": [], "opengraph": [], "rdfa": []},
                "faq": [],
                "nap": {"phone": "", "address": ""},
                "a11y": {"images_missing_alt": 0},
                "performance_hints": {"html_bytes": 0, "images_total_bytes_sampled": 0, "images_with_lazy": 0, "images_missing_dimensions": 0},
                "word_count": 0,
                "headers": {}
            }
        
        # Wait for content to load
        await page.wait_for_timeout(2000)
        
        # Extract content using JavaScript
        content = await page.evaluate("""
            () => {
                return {
                    title: document.title || '',
                    meta: document.querySelector('meta[name="description"]')?.content || '',
                    h1: Array.from(document.querySelectorAll('h1')).map(h => h.textContent?.trim() || ''),
                    h2: Array.from(document.querySelectorAll('h2')).map(h => h.textContent?.trim() || ''),
                    h3: Array.from(document.querySelectorAll('h3')).map(h => h.textContent?.trim() || ''),
                    lang: document.documentElement.lang || 'en',
                    canonical: document.querySelector('link[rel="canonical"]')?.href || '',
                    metaRobots: document.querySelector('meta[name="robots"]')?.content || '',
                    xRobotsTag: document.querySelector('meta[http-equiv="x-robots-tag"]')?.content || '',
                    hreflang: Array.from(document.querySelectorAll('link[rel="alternate"][hreflang]')).map(link => ({
                        hreflang: link.getAttribute('hreflang'),
                        href: link.href
                    })),
                    images: Array.from(document.querySelectorAll('img')).map(img => ({
                        src: img.src,
                        alt: img.alt || '',
                        loading: img.loading || '',
                        width: img.width || '',
                        height: img.height || '',
                        bytes: null
                    })),
                    wordCount: document.body.textContent?.trim().split(/\\s+/).length || 0
                };
            }
        """)
        
        # Extract links
        internal_links, external_links = await _extract_links_enhanced(page, url, seed)
        
        # Extract schema markup
        schema_data = await page.evaluate("""
            () => {
                const scripts = Array.from(document.querySelectorAll('script[type="application/ld+json"]'));
                return scripts.map(script => {
                    try {
                        return JSON.parse(script.textContent);
                    } catch (e) {
                        return null;
                    }
                }).filter(Boolean);
            }
        """)
        
        await page.close()
        
        # Build response
        return {
            "url": url,
            "status": response.status,
            "title": content.get("title", ""),
            "meta": content.get("meta", ""),
            "h1": content.get("h1", []),
            "h2": content.get("h2", []),
            "h3": content.get("h3", []),
            "lang": content.get("lang", "en"),
            "canonical": content.get("canonical", url),
            "meta_robots": content.get("metaRobots"),
            "x_robots_tag": content.get("xRobotsTag"),
            "hreflang": content.get("hreflang", []),
            "images": content.get("images", []),
            "links": {
                "internal": internal_links,
                "external": external_links,
                "broken_internal": []
            },
            "schema": {
                "json_ld": schema_data,
                "microdata": [],
                "opengraph": [],
                "rdfa": []
            },
            "faq": [],
            "nap": {"phone": "", "address": ""},
            "a11y": {"images_missing_alt": 0},
            "performance_hints": {
                "html_bytes": len(content.get("html", "")),
                "images_total_bytes_sampled": 0,
                "images_with_lazy": 0,
                "images_missing_dimensions": 0
            },
            "word_count": content.get("wordCount", 0),
            "headers": dict(response.headers)
        }
        
    except Exception as e:
        print(f"DEBUG: Enhanced page analysis failed for {url}: {e}")
        return {
            "url": url,
            "status": None,
            "title": "",
            "meta": "",
            "h1": [],
            "h2": [],
            "h3": [],
            "lang": "en",
            "canonical": url,
            "meta_robots": None,
            "x_robots_tag": None,
            "hreflang": [],
            "images": [],
            "links": {"internal": [], "external": [], "broken_internal": []},
            "schema": {"json_ld": [], "microdata": [], "opengraph": [], "rdfa": []},
            "faq": [],
            "nap": {"phone": "", "address": ""},
            "a11y": {"images_missing_alt": 0},
            "performance_hints": {"html_bytes": 0, "images_total_bytes_sampled": 0, "images_with_lazy": 0, "images_missing_dimensions": 0},
            "word_count": 0,
            "headers": {}
        }

async def enhanced_audit_site(seed_url: str, max_pages: int = 50, use_js: bool = True) -> Dict[str, Any]:
    """Enhanced audit with JavaScript rendering support"""
    try:
        seed_url = _norm(seed_url)
        parsed = urlparse(seed_url)
        root = f"{parsed.scheme}://{parsed.netloc}"
        visited: Set[str] = set()
        queue: List[str] = []
        
        if use_js:
            # Use Playwright for JavaScript rendering
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                
                try:
                    # Start with the seed URL
                    queue.append(seed_url)
                    pages: List[Dict[str, Any]] = []
                    broken_site_links: Set[str] = set()
                    
                    # Process pages with JavaScript rendering
                    while queue and len(visited) < max_pages:
                        url = queue.pop(0)
                        if url in visited:
                            continue
                        visited.add(url)
                        
                        print(f"DEBUG: Processing {url} with JavaScript rendering")
                        page_data = await _analyze_page_enhanced(browser, url, seed_url)
                        pages.append(page_data)
                        
                        # Add new internal links to queue
                        for next_url in page_data.get("links", {}).get("internal", []):
                            if len(visited) + len(queue) >= max_pages:
                                break
                            if next_url not in visited and next_url not in queue and _same_site(seed_url, next_url):
                                queue.append(next_url)
                                print(f"DEBUG: Added to queue: {next_url}")
                    
                    await browser.close()
                    
                    # Build audit response
                    discovered = len(pages)
                    langs = list({p.get("lang") for p in pages if p.get("lang")})
                    canonicals = sum(1 for p in pages if p.get("canonical"))
                    
                    return {
                        "url": seed_url,
                        "pages_discovered": discovered,
                        "languages": langs,
                        "pages_with_canonical": canonicals,
                        "robots": {"raw": "", "disallow": [], "sitemaps": []},
                        "pages_blocked_by_robots": 0,
                        "meta_robots_summary": {"index": 0, "noindex": 0},
                        "broken_internal_links_unique": sorted(list(broken_site_links)),
                        "a11y_summary": {"images_missing_alt_total": 0},
                        "pages": pages,
                    }
                    
                except Exception as e:
                    await browser.close()
                    raise e
        else:
            # Fallback to regular HTTP crawling
            from audit import audit_site
            return await audit_site(seed_url, max_pages)
            
    except Exception as e:
        print(f"DEBUG: Enhanced audit failed for {seed_url}: {e}")
        # Fallback to regular audit
        from audit import audit_site
        return await audit_site(seed_url, max_pages)
