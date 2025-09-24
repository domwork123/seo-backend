# aeo_geo_audit.py — AEO + GEO focused audit engine
import asyncio
import httpx
import re
import json
import requests
from typing import Dict, Any, List, Tuple, Optional
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup
import tldextract
from collections import Counter
import time
from playwright.async_api import async_playwright

def is_blocked_html(html: str) -> bool:
    """
    Check if HTML content indicates the page is blocked by protection services.
    
    Args:
        html: The HTML content to check
        
    Returns:
        bool: True if the page appears to be blocked
    """
    if not html or len(html) < 200:
        return True
    
    html_lower = html.lower()
    
    # Check for common blocking indicators
    blocking_indicators = [
        'attention required | cloudflare',
        'checking your browser before accessing',
        'please wait while we check your browser',
        'cloudflare',
        'captcha',
        'security check',
        'access denied',
        'blocked',
        'rate limited',
        'too many requests',
        'please enable javascript',
        'javascript is disabled'
    ]
    
    for indicator in blocking_indicators:
        if indicator in html_lower:
            return True
    
    return False

async def fetch_with_fallback(url: str) -> Dict[str, Any]:
    """
    Fetch URL content with fallback from requests to Playwright for protected sites.
    
    Args:
        url: The URL to fetch
        
    Returns:
        Dict containing 'html', 'status', 'method', and 'error' if applicable
    """
    result = {
        'html': '',
        'status': 'success',
        'method': 'requests',
        'error': None
    }
    
    # Step 1: Try normal requests.get() with realistic browser headers
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        
        response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
        
        if response.status_code == 200:
            html = response.text
            
            # Check if content is blocked
            if is_blocked_html(html):
                print(f"DEBUG: Content blocked, trying Playwright fallback for {url}")
                # Step 2: Try Playwright fallback
                return await _fetch_with_playwright(url)
            else:
                result['html'] = html
                result['status'] = 'success'
                result['method'] = 'requests'
                return result
        else:
            print(f"DEBUG: HTTP {response.status_code} for {url}, trying Playwright fallback")
            # Step 2: Try Playwright fallback
            return await _fetch_with_playwright(url)
            
    except Exception as e:
        print(f"DEBUG: Requests failed for {url}: {e}, trying Playwright fallback")
        # Step 2: Try Playwright fallback
        return await _fetch_with_playwright(url)

async def _fetch_with_playwright(url: str) -> Dict[str, Any]:
    """
    Fetch URL content using Playwright as fallback for protected sites.
    
    Args:
        url: The URL to fetch
        
    Returns:
        Dict containing 'html', 'status', 'method', and 'error' if applicable
    """
    result = {
        'html': '',
        'status': 'success',
        'method': 'playwright',
        'error': None
    }
    
    try:
        async with async_playwright() as p:
            # Launch Chromium browser
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu'
                ]
            )
            
            # Create new page with realistic settings
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1280, 'height': 800},
                locale='en-US',
                timezone_id='America/New_York'
            )
            
            page = await context.new_page()
            
            # Navigate to URL and wait for network to be idle
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Get page content
            html = await page.content()
            
            # Check if content is still blocked
            if is_blocked_html(html):
                result['status'] = 'blocked_by_protection'
                result['html'] = html
                result['error'] = 'Content blocked by protection service'
            else:
                result['html'] = html
                result['status'] = 'success'
            
            await browser.close()
            return result
            
    except Exception as e:
        print(f"DEBUG: Playwright failed for {url}: {e}")
        result['status'] = 'blocked_by_protection'
        result['error'] = f'Playwright failed: {str(e)}'
        return result

class AEOGeoAuditor:
    def __init__(self):
        self.session = None
        self.visited_urls = set()
        self.internal_urls = set()
        self.platform_indicators = {
            'wordpress': ['wp-content', 'wp-includes', 'wp-admin', 'wordpress'],
            'shopify': ['shopify', 'myshopify.com', 'cdn.shopify.com'],
            'wix': ['wix.com', 'wixstatic.com', 'wixsite.com'],
            'hostinger': ['hostinger', 'hpanel'],
            'squarespace': ['squarespace.com', 'sqs-cdn.com'],
            'custom': []
        }
        
    async def __aenter__(self):
        self.session = httpx.AsyncClient(
            timeout=60.0,
            follow_redirects=True,
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0'
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.aclose()

    async def audit_site(self, root_url: str, target_language: str = "en", max_pages: int = 100) -> Dict[str, Any]:
        """
        Main audit function for AEO + GEO analysis
        """
        start_time = time.time()
        
        try:
            # 1. Crawl the website
            crawl_results = await self._crawl_website(root_url, max_pages)
            
            # 2. Detect platform
            platform = self._detect_platform(crawl_results['pages'])
            
            # 3. Analyze each page for AEO + GEO signals
            analyzed_pages = []
            print(f"DEBUG: Analyzing {len(crawl_results['pages'])} crawled pages")
            for i, page_data in enumerate(crawl_results['pages']):
                print(f"DEBUG: Analyzing page {i+1}: {page_data.get('url', 'unknown')}")
                if page_data.get('html'):
                    print(f"DEBUG: Page has HTML content, length: {len(page_data.get('html', ''))}")
                    analysis = await self._analyze_page(page_data, target_language)
                    analyzed_pages.append(analysis)
                    print(f"DEBUG: Analysis completed for page {i+1}")
                else:
                    print(f"DEBUG: Page {i+1} has no HTML content")
            
            # 4. Calculate scores
            scores = self._calculate_scores(analyzed_pages)
            
            # 5. Generate recommendations
            recommendations = self._generate_recommendations(analyzed_pages, scores)
            
            # Calculate fetch method statistics
            fetch_methods = {}
            blocked_pages = 0
            for page in analyzed_pages:
                method = page.get('fetch_method', 'unknown')
                status = page.get('fetch_status', 'unknown')
                fetch_methods[method] = fetch_methods.get(method, 0) + 1
                if status == 'blocked_by_protection':
                    blocked_pages += 1
            
            return {
                "domain": urlparse(root_url).netloc,
                "platform": platform,
                "target_language": target_language,
                "pages_analyzed": len(analyzed_pages),
                "crawl_time": time.time() - start_time,
                "scores": scores,
                "pages": analyzed_pages,
                "recommendations": recommendations,
                "audit_type": "AEO + GEO Focused",
                "fetch_methods": fetch_methods,
                "blocked_pages": blocked_pages,
                "protection_status": "blocked" if blocked_pages > 0 else "accessible"
            }
            
        except Exception as e:
            return {
                "error": f"Audit failed: {str(e)}",
                "domain": urlparse(root_url).netloc,
                "audit_type": "AEO + GEO Focused"
            }

    async def _crawl_website(self, root_url: str, max_pages: int) -> Dict[str, Any]:
        """Crawl website and collect all internal pages"""
        domain = urlparse(root_url).netloc
        to_crawl = [root_url]
        crawled_pages = []
        errors = []
        
        print(f"DEBUG: Starting crawl for {root_url}, max_pages: {max_pages}")
        
        while to_crawl and len(crawled_pages) < max_pages:
            current_url = to_crawl.pop(0)
            
            if current_url in self.visited_urls:
                continue
                
            self.visited_urls.add(current_url)
            print(f"DEBUG: Crawling {current_url}")
            
            # Add delay between requests to be respectful
            if len(crawled_pages) > 0:
                await asyncio.sleep(0.5)
            
            try:
                # Use the new fallback system
                fetch_result = await fetch_with_fallback(current_url)
                
                if fetch_result['status'] == 'success':
                    html = fetch_result['html']
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract page data
                    page_data = {
                        "url": current_url,
                        "html": html,
                        "soup": soup,
                        "title": soup.find('title').get_text().strip() if soup.find('title') else "",
                        "meta_description": self._extract_meta_description(soup),
                        "lang": soup.find('html', {}).get('lang', ''),
                        "fetch_method": fetch_result['method'],
                        "fetch_status": fetch_result['status']
                    }
                    
                    crawled_pages.append(page_data)
                    print(f"DEBUG: Successfully crawled page {len(crawled_pages)}: {current_url} (method: {fetch_result['method']})")
                    
                    # Find internal links
                    internal_links = self._extract_internal_links(soup, current_url, domain)
                    print(f"DEBUG: Found {len(internal_links)} internal links")
                    for link in internal_links:
                        if link not in self.visited_urls and link not in to_crawl:
                            to_crawl.append(link)
                            
                elif fetch_result['status'] == 'blocked_by_protection':
                    error_msg = f"Blocked by protection service: {fetch_result.get('error', 'Unknown protection')}"
                    print(f"DEBUG: {error_msg} for {current_url}")
                    errors.append(error_msg)
                    continue
                else:
                    error_msg = f"Fetch failed: {fetch_result.get('error', 'Unknown error')}"
                    print(f"DEBUG: {error_msg} for {current_url}")
                    errors.append(error_msg)
                    continue
                            
            except Exception as e:
                error_msg = f"Error crawling {current_url}: {e}"
                print(f"DEBUG: {error_msg}")
                errors.append(error_msg)
                continue
        
        print(f"DEBUG: Crawl completed. Pages: {len(crawled_pages)}, Errors: {len(errors)}")
        return {"pages": crawled_pages, "errors": errors}

    def _extract_internal_links(self, soup: BeautifulSoup, current_url: str, domain: str) -> List[str]:
        """Extract internal links from page"""
        links = []
        base_domain = urlparse(current_url).netloc
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Skip javascript, mailto, tel, etc.
            if href.startswith(('javascript:', 'mailto:', 'tel:', '#', 'data:')):
                continue
                
            try:
                full_url = urljoin(current_url, href)
                parsed_url = urlparse(full_url)
                
                # Only include internal links
                if parsed_url.netloc == base_domain:
                    # Clean URL (remove fragments and query params for deduplication)
                    clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
                    if clean_url not in self.visited_urls and clean_url not in links:
                        links.append(clean_url)
            except Exception as e:
                print(f"DEBUG: Error processing link {href}: {e}")
                continue
        
        return links

    def _extract_meta_description(self, soup: BeautifulSoup) -> str:
        """Extract meta description"""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        return meta_desc.get('content', '') if meta_desc else ''

    def _detect_platform(self, pages: List[Dict[str, Any]]) -> str:
        """Detect CMS/platform from page content"""
        platform_scores = Counter()
        
        for page in pages:
            html = page.get('html', '').lower()
            
            for platform, indicators in self.platform_indicators.items():
                if platform == 'custom':
                    continue
                    
                for indicator in indicators:
                    if indicator.lower() in html:
                        platform_scores[platform] += 1
        
        if platform_scores:
            return platform_scores.most_common(1)[0][0]
        return 'custom'

    async def _analyze_page(self, page_data: Dict[str, Any], target_language: str) -> Dict[str, Any]:
        """Analyze a single page for AEO + GEO signals"""
        soup = page_data['soup']
        url = page_data['url']
        
        # AEO Analysis
        aeo_signals = self._analyze_aeo_signals(soup, target_language)
        
        # GEO Analysis  
        geo_signals = self._analyze_geo_signals(soup, url)
        
        # Calculate page scores with detailed breakdown
        aeo_score = self._calculate_aeo_score(aeo_signals)
        geo_score = self._calculate_geo_score(geo_signals)
        
        return {
            "url": url,
            "title": page_data['title'],
            "meta_description": page_data['meta_description'],
            "language": page_data['lang'],
            "aeo_signals": aeo_signals,
            "geo_signals": geo_signals,
            "aeo_score": aeo_score,
            "geo_score": geo_score,
            "overall_score": (aeo_score['score'] + geo_score['score']) / 2
        }

    def _analyze_aeo_signals(self, soup: BeautifulSoup, target_language: str) -> Dict[str, Any]:
        """Analyze AEO (Answer Engine Optimization) signals"""
        signals = {
            "faq_content": self._detect_faq_content(soup),
            "faq_schema": self._detect_faq_schema(soup),
            "other_schemas": self._detect_other_schemas(soup),
            "meta_description": self._analyze_meta_description(soup),
            "snippet_suitability": self._analyze_snippet_suitability(soup),
            "question_headings": self._detect_question_headings(soup, target_language)
        }
        return signals

    def _analyze_geo_signals(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Analyze GEO (Geographic Optimization) signals"""
        signals = {
            "hreflang_tags": self._detect_hreflang_tags(soup),
            "local_business_schema": self._detect_local_business_schema(soup),
            "nap_consistency": self._check_nap_consistency(soup),
            "geo_meta_tags": self._detect_geo_meta_tags(soup),
            "map_embeds": self._detect_map_embeds(soup),
            "domain_tld": self._extract_domain_tld(url)
        }
        return signals

    def _detect_faq_content(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Detect FAQ content on page"""
        faq_indicators = ['faq', 'frequently asked', 'questions', 'answers', 'q&a']
        faq_content = []
        
        # Look for FAQ sections
        for element in soup.find_all(['div', 'section', 'article']):
            text = element.get_text().lower()
            if any(indicator in text for indicator in faq_indicators):
                # Extract potential Q&A pairs
                qa_pairs = self._extract_qa_pairs(element)
                if qa_pairs:
                    faq_content.extend(qa_pairs)
        
        return {
            "has_faq_content": len(faq_content) > 0,
            "qa_pairs": faq_content,
            "count": len(faq_content)
        }

    def _extract_qa_pairs(self, element) -> List[Dict[str, str]]:
        """Extract Q&A pairs from element"""
        qa_pairs = []
        
        # Look for question patterns
        for heading in element.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            heading_text = heading.get_text().strip()
            if heading_text.endswith('?') or any(word in heading_text.lower() for word in ['what', 'how', 'why', 'when', 'where']):
                # Find answer in next sibling
                answer_element = heading.find_next_sibling()
                if answer_element:
                    answer_text = answer_element.get_text().strip()
                    if answer_text:
                        qa_pairs.append({
                            "question": heading_text,
                            "answer": answer_text[:200] + "..." if len(answer_text) > 200 else answer_text
                        })
        
        return qa_pairs

    def _detect_faq_schema(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Detect FAQ schema markup"""
        faq_schemas = []
        
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and data.get('@type') == 'FAQPage':
                    faq_schemas.append(data)
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get('@type') == 'FAQPage':
                            faq_schemas.append(item)
            except:
                continue
        
        return {
            "has_faq_schema": len(faq_schemas) > 0,
            "schemas": faq_schemas,
            "count": len(faq_schemas)
        }

    def _detect_other_schemas(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Detect other relevant schema types"""
        schemas = []
        schema_types = []
        
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    schema_type = data.get('@type', '')
                    if schema_type:
                        schemas.append(data)
                        schema_types.append(schema_type)
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            schema_type = item.get('@type', '')
                            if schema_type:
                                schemas.append(item)
                                schema_types.append(schema_type)
            except:
                continue
        
        return {
            "schemas": schemas,
            "types": list(set(schema_types)),
            "count": len(schemas)
        }

    def _analyze_meta_description(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze meta description for AEO optimization"""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        description = meta_desc.get('content', '') if meta_desc else ''
        
        return {
            "exists": bool(description),
            "length": len(description),
            "optimal_length": 150 <= len(description) <= 160,
            "content": description,
            "snippet_suitable": self._is_snippet_suitable(description)
        }

    def _is_snippet_suitable(self, text: str) -> bool:
        """Check if text is suitable for featured snippets"""
        if not text:
            return False
        
        # Check for question format
        if text.strip().endswith('?'):
            return True
        
        # Check for structured information
        structured_indicators = ['•', '-', '1.', '2.', '3.', ':', ';']
        return any(indicator in text for indicator in structured_indicators)

    def _analyze_snippet_suitability(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze page content for snippet suitability"""
        content = soup.get_text()
        
        # Count structured elements
        lists = len(soup.find_all(['ul', 'ol']))
        tables = len(soup.find_all('table'))
        short_paragraphs = len([p for p in soup.find_all('p') if len(p.get_text()) < 200])
        
        return {
            "lists_count": lists,
            "tables_count": tables,
            "short_paragraphs": short_paragraphs,
            "snippet_score": min(100, (lists * 10) + (tables * 15) + (short_paragraphs * 2))
        }

    def _detect_question_headings(self, soup: BeautifulSoup, target_language: str) -> Dict[str, Any]:
        """Detect question-style headings"""
        question_words = {
            'en': ['what', 'how', 'why', 'when', 'where', 'who'],
            'es': ['qué', 'cómo', 'por qué', 'cuándo', 'dónde', 'quién'],
            'fr': ['quoi', 'comment', 'pourquoi', 'quand', 'où', 'qui'],
            'de': ['was', 'wie', 'warum', 'wann', 'wo', 'wer'],
            'it': ['cosa', 'come', 'perché', 'quando', 'dove', 'chi']
        }
        
        words = question_words.get(target_language, question_words['en'])
        question_headings = []
        
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            text = heading.get_text().lower().strip()
            if any(word in text for word in words) or text.endswith('?'):
                question_headings.append(heading.get_text().strip())
        
        return {
            "headings": question_headings,
            "count": len(question_headings)
        }

    def _detect_hreflang_tags(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Detect hreflang tags"""
        hreflang_tags = []
        
        for link in soup.find_all('link', rel='alternate'):
            hreflang = link.get('hreflang')
            href = link.get('href')
            if hreflang and href:
                hreflang_tags.append({
                    "hreflang": hreflang,
                    "href": href
                })
        
        return {
            "tags": hreflang_tags,
            "count": len(hreflang_tags)
        }

    def _detect_local_business_schema(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Detect LocalBusiness schema"""
        local_business_schemas = []
        
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and 'LocalBusiness' in str(data.get('@type', '')):
                    local_business_schemas.append(data)
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and 'LocalBusiness' in str(item.get('@type', '')):
                            local_business_schemas.append(item)
            except:
                continue
        
        return {
            "schemas": local_business_schemas,
            "count": len(local_business_schemas),
            "has_local_business": len(local_business_schemas) > 0
        }

    def _check_nap_consistency(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Check NAP (Name, Address, Phone) consistency"""
        # Extract NAP from schema
        schema_nap = self._extract_nap_from_schema(soup)
        
        # Extract NAP from page content
        content_nap = self._extract_nap_from_content(soup)
        
        # Check consistency
        consistency_score = self._calculate_nap_consistency(schema_nap, content_nap)
        
        return {
            "schema_nap": schema_nap,
            "content_nap": content_nap,
            "consistency_score": consistency_score,
            "is_consistent": consistency_score > 70
        }

    def _extract_nap_from_schema(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract NAP from schema markup"""
        nap = {"name": "", "address": "", "phone": ""}
        
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    if 'name' in data:
                        nap["name"] = data['name']
                    if 'address' in data:
                        nap["address"] = str(data['address'])
                    if 'telephone' in data:
                        nap["phone"] = data['telephone']
            except:
                continue
        
        return nap

    def _extract_nap_from_content(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract NAP from page content"""
        content = soup.get_text()
        
        # Simple regex patterns for NAP extraction
        phone_pattern = r'(\+?[\d\s\-\(\)]{10,})'
        address_pattern = r'(\d+[^,]*,[^,]*,[^,]*\d{5})'
        
        phone_match = re.search(phone_pattern, content)
        address_match = re.search(address_pattern, content)
        
        return {
            "name": soup.find('title').get_text() if soup.find('title') else "",
            "address": address_match.group(1) if address_match else "",
            "phone": phone_match.group(1) if phone_match else ""
        }

    def _calculate_nap_consistency(self, schema_nap: Dict[str, str], content_nap: Dict[str, str]) -> int:
        """Calculate NAP consistency score"""
        score = 0
        
        # Check name consistency
        if schema_nap["name"] and content_nap["name"]:
            if schema_nap["name"].lower() in content_nap["name"].lower():
                score += 33
        
        # Check address consistency
        if schema_nap["address"] and content_nap["address"]:
            if any(word in content_nap["address"].lower() for word in schema_nap["address"].lower().split()):
                score += 33
        
        # Check phone consistency
        if schema_nap["phone"] and content_nap["phone"]:
            # Normalize phone numbers
            schema_phone = re.sub(r'\D', '', schema_nap["phone"])
            content_phone = re.sub(r'\D', '', content_nap["phone"])
            if schema_phone and content_phone and schema_phone in content_phone:
                score += 34
        
        return score

    def _detect_geo_meta_tags(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Detect geographic meta tags"""
        geo_tags = {}
        
        for meta in soup.find_all('meta'):
            name = meta.get('name', '').lower()
            if 'geo' in name:
                geo_tags[name] = meta.get('content', '')
        
        return {
            "tags": geo_tags,
            "count": len(geo_tags)
        }

    def _detect_map_embeds(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Detect map embeds"""
        map_embeds = []
        
        # Google Maps
        for iframe in soup.find_all('iframe'):
            src = iframe.get('src', '')
            if 'google.com/maps' in src or 'maps.google.com' in src:
                map_embeds.append({"type": "google_maps", "src": src})
        
        # OpenStreetMap
        for iframe in soup.find_all('iframe'):
            src = iframe.get('src', '')
            if 'openstreetmap.org' in src:
                map_embeds.append({"type": "openstreetmap", "src": src})
        
        return {
            "embeds": map_embeds,
            "count": len(map_embeds)
        }

    def _extract_domain_tld(self, url: str) -> str:
        """Extract domain TLD"""
        parsed = urlparse(url)
        return tldextract.extract(parsed.netloc).suffix

    def _calculate_aeo_score(self, aeo_signals: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate AEO score for a page with detailed breakdown"""
        score = 0
        breakdown = {
            "faq_content": {"score": 0, "max": 25, "present": False, "details": ""},
            "faq_schema": {"score": 0, "max": 20, "present": False, "details": ""},
            "other_schemas": {"score": 0, "max": 15, "present": False, "details": ""},
            "meta_description": {"score": 0, "max": 20, "present": False, "details": ""},
            "snippet_suitability": {"score": 0, "max": 10, "present": False, "details": ""},
            "question_headings": {"score": 0, "max": 10, "present": False, "details": ""}
        }
        
        # FAQ content (25 points)
        if aeo_signals['faq_content']['has_faq_content']:
            breakdown["faq_content"]["score"] += 15
            breakdown["faq_content"]["present"] = True
            breakdown["faq_content"]["details"] = f"Found {aeo_signals['faq_content']['count']} Q&A pairs"
        if aeo_signals['faq_content']['count'] > 0:
            breakdown["faq_content"]["score"] += min(10, aeo_signals['faq_content']['count'] * 2)
        
        # FAQ schema (20 points)
        if aeo_signals['faq_schema']['has_faq_schema']:
            breakdown["faq_schema"]["score"] = 20
            breakdown["faq_schema"]["present"] = True
            breakdown["faq_schema"]["details"] = f"Found {aeo_signals['faq_schema']['count']} FAQ schemas"
        
        # Other schemas (15 points)
        if aeo_signals['other_schemas']['count'] > 0:
            breakdown["other_schemas"]["score"] = min(15, aeo_signals['other_schemas']['count'] * 3)
            breakdown["other_schemas"]["present"] = True
            breakdown["other_schemas"]["details"] = f"Found schemas: {', '.join(aeo_signals['other_schemas']['types'])}"
        
        # Meta description (20 points)
        meta_desc = aeo_signals['meta_description']
        if meta_desc['exists']:
            breakdown["meta_description"]["score"] += 10
            breakdown["meta_description"]["present"] = True
            breakdown["meta_description"]["details"] = f"Meta description exists ({meta_desc['length']} chars)"
        if meta_desc['optimal_length']:
            breakdown["meta_description"]["score"] += 10
            breakdown["meta_description"]["details"] += " - Optimal length"
        elif meta_desc['exists']:
            breakdown["meta_description"]["details"] += " - Length not optimal"
        
        # Snippet suitability (10 points)
        snippet_score = aeo_signals['snippet_suitability']['snippet_score']
        breakdown["snippet_suitability"]["score"] = min(10, snippet_score // 10)
        if breakdown["snippet_suitability"]["score"] > 0:
            breakdown["snippet_suitability"]["present"] = True
            breakdown["snippet_suitability"]["details"] = f"Snippet score: {snippet_score}"
        
        # Question headings (10 points)
        if aeo_signals['question_headings']['count'] > 0:
            breakdown["question_headings"]["score"] = min(10, aeo_signals['question_headings']['count'] * 2)
            breakdown["question_headings"]["present"] = True
            breakdown["question_headings"]["details"] = f"Found {aeo_signals['question_headings']['count']} question headings"
        
        # Calculate total score
        for signal in breakdown.values():
            score += signal["score"]
        
        return {
            "score": min(100, score),
            "breakdown": breakdown,
            "signals_present": sum(1 for s in breakdown.values() if s["present"]),
            "signals_total": len(breakdown)
        }

    def _calculate_geo_score(self, geo_signals: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate GEO score for a page with detailed breakdown"""
        score = 0
        breakdown = {
            "hreflang_tags": {"score": 0, "max": 25, "present": False, "details": ""},
            "local_business_schema": {"score": 0, "max": 25, "present": False, "details": ""},
            "nap_consistency": {"score": 0, "max": 25, "present": False, "details": ""},
            "geo_meta_tags": {"score": 0, "max": 15, "present": False, "details": ""},
            "map_embeds": {"score": 0, "max": 10, "present": False, "details": ""}
        }
        
        # Hreflang tags (25 points)
        hreflang_count = geo_signals['hreflang_tags']['count']
        breakdown["hreflang_tags"]["score"] = min(25, hreflang_count * 5)
        if hreflang_count > 0:
            breakdown["hreflang_tags"]["present"] = True
            breakdown["hreflang_tags"]["details"] = f"Found {hreflang_count} hreflang tags"
        
        # LocalBusiness schema (25 points)
        if geo_signals['local_business_schema']['has_local_business']:
            breakdown["local_business_schema"]["score"] = 25
            breakdown["local_business_schema"]["present"] = True
            breakdown["local_business_schema"]["details"] = f"Found {geo_signals['local_business_schema']['count']} LocalBusiness schemas"
        
        # NAP consistency (25 points)
        nap_consistency = geo_signals['nap_consistency']
        if nap_consistency['is_consistent']:
            breakdown["nap_consistency"]["score"] = 25
            breakdown["nap_consistency"]["present"] = True
            breakdown["nap_consistency"]["details"] = "NAP data is consistent"
        else:
            breakdown["nap_consistency"]["score"] = nap_consistency['consistency_score'] // 4
            breakdown["nap_consistency"]["present"] = True
            breakdown["nap_consistency"]["details"] = f"NAP consistency: {nap_consistency['consistency_score']}%"
        
        # Geo meta tags (15 points)
        geo_meta_count = geo_signals['geo_meta_tags']['count']
        if geo_meta_count > 0:
            breakdown["geo_meta_tags"]["score"] = min(15, geo_meta_count * 5)
            breakdown["geo_meta_tags"]["present"] = True
            breakdown["geo_meta_tags"]["details"] = f"Found {geo_meta_count} geo meta tags"
        
        # Map embeds (10 points)
        map_count = geo_signals['map_embeds']['count']
        if map_count > 0:
            breakdown["map_embeds"]["score"] = 10
            breakdown["map_embeds"]["present"] = True
            breakdown["map_embeds"]["details"] = f"Found {map_count} map embeds"
        
        # Calculate total score
        for signal in breakdown.values():
            score += signal["score"]
        
        return {
            "score": min(100, score),
            "breakdown": breakdown,
            "signals_present": sum(1 for s in breakdown.values() if s["present"]),
            "signals_total": len(breakdown)
        }

    def _calculate_scores(self, analyzed_pages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall site scores with detailed breakdown"""
        if not analyzed_pages:
            return {
                "aeo": 0, 
                "geo": 0, 
                "overall": 0,
                "page_count": 0,
                "aeo_breakdown": {},
                "geo_breakdown": {}
            }
        
        # Extract scores from detailed scoring format
        aeo_scores = [page['aeo_score']['score'] for page in analyzed_pages]
        geo_scores = [page['geo_score']['score'] for page in analyzed_pages]
        
        # Calculate site-level scores
        site_aeo = int(sum(aeo_scores) / len(aeo_scores))
        site_geo = int(sum(geo_scores) / len(geo_scores))
        site_overall = int((site_aeo + site_geo) / 2)
        
        # Calculate signal coverage across all pages
        aeo_breakdown = self._calculate_site_breakdown(analyzed_pages, 'aeo')
        geo_breakdown = self._calculate_site_breakdown(analyzed_pages, 'geo')
        
        return {
            "aeo": site_aeo,
            "geo": site_geo,
            "overall": site_overall,
            "page_count": len(analyzed_pages),
            "aeo_breakdown": aeo_breakdown,
            "geo_breakdown": geo_breakdown
        }
    
    def _calculate_site_breakdown(self, analyzed_pages: List[Dict[str, Any]], score_type: str) -> Dict[str, Any]:
        """Calculate site-level signal breakdown"""
        if not analyzed_pages:
            return {}
        
        # Collect all signals across all pages
        all_signals = {}
        for page in analyzed_pages:
            page_breakdown = page[f'{score_type}_score']['breakdown']
            for signal_name, signal_data in page_breakdown.items():
                if signal_name not in all_signals:
                    all_signals[signal_name] = {
                        "pages_with_signal": 0,
                        "total_pages": len(analyzed_pages),
                        "total_score": 0,
                        "max_possible": signal_data["max"]
                    }
                
                if signal_data["present"]:
                    all_signals[signal_name]["pages_with_signal"] += 1
                all_signals[signal_name]["total_score"] += signal_data["score"]
        
        # Calculate percentages and coverage
        for signal_name, signal_data in all_signals.items():
            signal_data["coverage_percentage"] = int((signal_data["pages_with_signal"] / signal_data["total_pages"]) * 100)
            signal_data["average_score"] = int(signal_data["total_score"] / signal_data["total_pages"])
            signal_data["strength"] = "strong" if signal_data["coverage_percentage"] >= 80 else "moderate" if signal_data["coverage_percentage"] >= 50 else "weak"
        
        return all_signals

    def _generate_recommendations(self, analyzed_pages: List[Dict[str, Any]], scores: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AEO + GEO recommendations based on detailed scoring"""
        recommendations = {
            "aeo": [],
            "geo": [],
            "priority": [],
            "quick_wins": []
        }
        
        # AEO recommendations based on site-level breakdown
        aeo_breakdown = scores.get('aeo_breakdown', {})
        for signal_name, signal_data in aeo_breakdown.items():
            if signal_data['coverage_percentage'] < 50:
                if signal_name == 'faq_content':
                    recommendations["aeo"].append("Add FAQ sections with common customer questions")
                elif signal_name == 'faq_schema':
                    recommendations["aeo"].append("Implement FAQ schema markup (JSON-LD)")
                elif signal_name == 'meta_description':
                    recommendations["aeo"].append("Optimize meta descriptions for featured snippets")
                elif signal_name == 'question_headings':
                    recommendations["aeo"].append("Add question-style headings (What, How, Why)")
                elif signal_name == 'other_schemas':
                    recommendations["aeo"].append("Add structured data markup (HowTo, Product, Organization)")
                elif signal_name == 'snippet_suitability':
                    recommendations["aeo"].append("Improve content structure for featured snippets")
        
        # GEO recommendations based on site-level breakdown
        geo_breakdown = scores.get('geo_breakdown', {})
        for signal_name, signal_data in geo_breakdown.items():
            if signal_data['coverage_percentage'] < 50:
                if signal_name == 'hreflang_tags':
                    recommendations["geo"].append("Implement hreflang tags for multilingual targeting")
                elif signal_name == 'local_business_schema':
                    recommendations["geo"].append("Add LocalBusiness schema markup")
                elif signal_name == 'nap_consistency':
                    recommendations["geo"].append("Ensure NAP (Name, Address, Phone) consistency")
                elif signal_name == 'geo_meta_tags':
                    recommendations["geo"].append("Add geographic meta tags")
                elif signal_name == 'map_embeds':
                    recommendations["geo"].append("Add map embeds for location visibility")
        
        # Priority recommendations (lowest scoring signals)
        if aeo_breakdown:
            weakest_aeo = min(aeo_breakdown.items(), key=lambda x: x[1]['coverage_percentage'])
            if weakest_aeo[1]['coverage_percentage'] < 30:
                recommendations["priority"].append(f"Priority: Improve {weakest_aeo[0].replace('_', ' ')} (only {weakest_aeo[1]['coverage_percentage']}% coverage)")
        
        if geo_breakdown:
            weakest_geo = min(geo_breakdown.items(), key=lambda x: x[1]['coverage_percentage'])
            if weakest_geo[1]['coverage_percentage'] < 30:
                recommendations["priority"].append(f"Priority: Improve {weakest_geo[0].replace('_', ' ')} (only {weakest_geo[1]['coverage_percentage']}% coverage)")
        
        # Quick wins (signals that are easy to implement)
        quick_wins = []
        if scores.get('aeo', 0) < 70:
            quick_wins.append("Add meta descriptions to pages missing them")
            quick_wins.append("Add question-style headings to key pages")
        if scores.get('geo', 0) < 70:
            quick_wins.append("Add hreflang tags to homepage")
            quick_wins.append("Add LocalBusiness schema to contact page")
        
        recommendations["quick_wins"] = quick_wins
        
        return recommendations

# Main audit function
async def audit_site_aeo_geo(root_url: str, target_language: str = "en", max_pages: int = 100) -> Dict[str, Any]:
    """Main function to audit a site for AEO + GEO optimization"""
    async with AEOGeoAuditor() as auditor:
        return await auditor.audit_site(root_url, target_language, max_pages)
