"""
ScrapingBee integration for EVIKA audit crawler
Handles website crawling with ScrapingBee API
"""

import requests
import json
import time
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin, urlparse
import os

# ScrapingBee configuration
SCRAPINGBEE_API_KEY = os.getenv("SCRAPINGBEE_API_KEY")
SCRAPINGBEE_BASE_URL = "https://app.scrapingbee.com/api/v1"

def crawl_website_with_scrapingbee(url: str, max_pages: int = 15) -> Dict[str, Any]:
    """
    Crawl a website using ScrapingBee API
    
    Args:
        url: Website URL to crawl
        max_pages: Maximum number of pages to crawl
        
    Returns:
        Dict with crawled pages data
    """
    
    # ⚠️ DEVELOPMENT MODE: Skip ScrapingBee to save credits
    if os.getenv("DEVELOPMENT_MODE", "false").lower() == "true":
        print("🔧 DEVELOPMENT MODE: Using mock data instead of ScrapingBee")
        return _get_mock_crawl_data(url)
    
    if not SCRAPINGBEE_API_KEY:
        print("❌ ScrapingBee API key not found, using mock data")
        return _get_mock_crawl_data(url)
    
    print(f"🕷️ Starting ScrapingBee crawl for: {url}")
    
    try:
        # Step 1: Get initial page to discover internal links
        initial_page = _fetch_page_with_scrapingbee(url)
        if not initial_page:
            return {"error": "Could not fetch initial page", "pages": []}
        
        pages_data = [initial_page]
        discovered_urls = set([url])
        urls_to_crawl = _extract_internal_links(initial_page["html"], url)
        
        print(f"🔍 Found {len(urls_to_crawl)} internal links")
        
        # Step 2: Crawl additional pages (limit to max_pages)
        for page_url in urls_to_crawl[:max_pages-1]:  # -1 because we already have initial page
            if page_url in discovered_urls:
                continue
                
            print(f"📄 Crawling: {page_url}")
            page_data = _fetch_page_with_scrapingbee(page_url)
            
            if page_data:
                pages_data.append(page_data)
                discovered_urls.add(page_url)
                
                # Extract more links from this page
                new_links = _extract_internal_links(page_data["html"], url)
                for new_link in new_links:
                    if new_link not in discovered_urls and len(urls_to_crawl) < max_pages * 2:
                        urls_to_crawl.append(new_link)
            
            # Rate limiting
            time.sleep(0.5)
        
        print(f"✅ Crawled {len(pages_data)} pages")
        return {
            "success": True,
            "pages": pages_data,
            "total_pages": len(pages_data)
        }
        
    except Exception as e:
        print(f"❌ ScrapingBee crawl failed: {e}")
        return {"error": str(e), "pages": []}

def _fetch_page_with_scrapingbee(url: str) -> Optional[Dict[str, Any]]:
    """Fetch a single page using ScrapingBee API"""
    
    params = {
        "api_key": SCRAPINGBEE_API_KEY,
        "url": url,
        "render_js": "true",  # Enable JavaScript rendering
        "premium_proxy": "true",  # Use premium proxies
        "block_resources": "false",  # Don't block images/CSS
        "country_code": "US"  # Use US proxies
    }
    
    try:
        response = requests.get(SCRAPINGBEE_BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        
        html_content = response.text
        
        # Parse basic page info
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract title
        title = soup.find('title')
        title_text = title.get_text().strip() if title else ""
        
        # Extract meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        description = meta_desc.get('content', '').strip() if meta_desc else ""
        
        # Extract visible text
        for script in soup(["script", "style"]):
            script.decompose()
        visible_text = soup.get_text()
        
        # Extract images
        images = []
        for img in soup.find_all('img'):
            images.append({
                "src": img.get('src', ''),
                "alt": img.get('alt', '')
            })
        
        return {
            "url": url,
            "title": title_text,
            "meta_description": description,
            "html": html_content,
            "raw_text": visible_text,
            "images": images
        }
        
    except Exception as e:
        print(f"❌ Failed to fetch {url}: {e}")
        return None

def _extract_internal_links(html: str, base_url: str) -> List[str]:
    """Extract internal links from HTML"""
    
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    
    base_domain = urlparse(base_url).netloc
    internal_links = []
    
    for link in soup.find_all('a', href=True):
        href = link['href']
        full_url = urljoin(base_url, href)
        parsed_url = urlparse(full_url)
        
        # Only include internal links
        if parsed_url.netloc == base_domain:
            # Clean URL (remove fragments, query params for deduplication)
            clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
            if clean_url not in internal_links:
                internal_links.append(clean_url)
    
    return internal_links

def _get_mock_crawl_data(url: str) -> Dict[str, Any]:
    """Return mock crawl data for development/testing"""
    
    print(f"🎭 Using mock data for: {url}")
    
    # Mock pages data
    mock_pages = [
        {
            "url": url,
            "title": "Example Website - Homepage",
            "meta_description": "Welcome to our website. We offer great products and services.",
            "html": "<html><head><title>Example Website</title></head><body><h1>Welcome</h1><p>This is a sample page.</p></body></html>",
            "raw_text": "Welcome This is a sample page.",
            "images": [
                {"src": "/images/logo.png", "alt": "Company Logo"},
                {"src": "/images/product.jpg", "alt": ""}  # Missing alt text
            ]
        }
    ]
    
    # Add more mock pages if it's a known test site
    if "seal.lt" in url:
        mock_pages.extend([
            {
                "url": f"{url}/about",
                "title": "About Us - Seal.lt",
                "meta_description": "Learn about our company and mission.",
                "html": "<html><head><title>About Us</title></head><body><h1>About Us</h1><p>We are a leading company.</p></body></html>",
                "raw_text": "About Us We are a leading company.",
                "images": [{"src": "/images/team.jpg", "alt": "Our Team"}]
            },
            {
                "url": f"{url}/products",
                "title": "Products - Seal.lt",
                "meta_description": "Browse our product catalog.",
                "html": "<html><head><title>Products</title></head><body><h1>Products</h1><p>Check out our products.</p></body></html>",
                "raw_text": "Products Check out our products.",
                "images": [{"src": "/images/product1.jpg", "alt": "Product 1"}]
            }
        ])
    
    return {
        "success": True,
        "pages": mock_pages,
        "total_pages": len(mock_pages)
    }
