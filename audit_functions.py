# EVIKA Audit Functions
import asyncio
import re
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
from scrapingbee_integration import fetch_with_scrapingbee
from urllib.parse import urljoin, urlparse
import json

async def crawl_website_with_scrapingbee(url: str, max_pages: int = 15) -> Dict[str, Any]:
    """
    Crawl website using ScrapingBee with 15 pages maximum
    
    Args:
        url: Website URL to crawl
        max_pages: Maximum number of pages to crawl (default 15)
        
    Returns:
        Dict with success status and crawled pages
    """
    try:
        print(f"🕷️ Starting ScrapingBee crawl for: {url}")
        
        # Normalize URL
        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"
        
        # Start with homepage
        to_crawl = [url]
        visited = set()
        pages = []
        
        while to_crawl and len(pages) < max_pages:
            current_url = to_crawl.pop(0)
            
            if current_url in visited:
                continue
                
            visited.add(current_url)
            print(f"📄 Crawling: {current_url}")
            
            try:
                # Fetch page with ScrapingBee
                html_content = fetch_with_scrapingbee(current_url)
                
                if html_content == "blocked_by_protection":
                    print(f"⚠️ Page blocked: {current_url}")
                    continue
                
                if not html_content or len(html_content) < 100:
                    print(f"⚠️ Empty content: {current_url}")
                    continue
                
                # Parse HTML
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Extract page data
                page_data = {
                    "url": current_url,
                    "title": extract_title(soup),
                    "meta_description": extract_meta_description(soup),
                    "raw_text": extract_visible_text(soup),
                    "images": extract_images(soup),
                    "links": extract_internal_links(soup, url)
                }
                
                pages.append(page_data)
                print(f"✅ Extracted: {page_data['title'][:50]}...")
                
                # Add new internal links to crawl queue
                for link in page_data["links"]:
                    if link not in visited and len(pages) < max_pages:
                        to_crawl.append(link)
                
                # Small delay to be respectful
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Error crawling {current_url}: {e}")
                continue
        
        print(f"✅ Crawl completed: {len(pages)} pages")
        
        return {
            "success": True,
            "pages": pages,
            "total_crawled": len(pages)
        }
        
    except Exception as e:
        print(f"❌ Crawl failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "pages": []
        }

def extract_signals_from_pages(pages: List[Dict]) -> Dict[str, Any]:
    """
    Extract AEO + GEO signals from crawled pages
    
    Args:
        pages: List of crawled page data
        
    Returns:
        Dict with extracted signals
    """
    try:
        print(f"🔍 Extracting signals from {len(pages)} pages")
        
        # Initialize signal containers
        signals = {
            "brand_name": "Unknown",
            "description": "",
            "location": "",
            "industry": "Unknown",
            "products": [],
            "faqs": [],
            "topics": [],
            "competitors": [],
            "schema": [],
            "alt_text": [],
            "geo_signals": []
        }
        
        # Process each page
        for page in pages:
            soup = BeautifulSoup(page.get("raw_text", ""), 'html.parser')
            
            # Extract brand name
            brand = extract_brand_name(soup, page.get("title", ""))
            if brand and brand != "Unknown":
                signals["brand_name"] = brand
            
            # Extract description
            desc = page.get("meta_description", "")
            if desc and not signals["description"]:
                signals["description"] = desc
            
            # Extract location
            location = extract_location(soup)
            if location and not signals["location"]:
                signals["location"] = location
            
            # Extract products/services
            products = extract_products(soup)
            signals["products"].extend(products)
            
            # Extract FAQs
            faqs = extract_faqs(soup)
            signals["faqs"].extend(faqs)
            
            # Extract topics
            topics = extract_topics(soup)
            signals["topics"].extend(topics)
            
            # Extract competitors
            competitors = extract_competitors(soup)
            signals["competitors"].extend(competitors)
            
            # Extract schema
            schema = extract_schema(soup)
            signals["schema"].extend(schema)
            
            # Extract alt text issues
            alt_issues = extract_alt_text_issues(page.get("images", []))
            signals["alt_text"].extend(alt_issues)
            
            # Extract geo signals
            geo = extract_geo_signals(soup)
            signals["geo_signals"].extend(geo)
        
        # Deduplicate lists
        signals["products"] = list(set(signals["products"]))
        signals["faqs"] = list(set(signals["faqs"]))
        signals["topics"] = list(set(signals["topics"]))
        signals["competitors"] = list(set(signals["competitors"]))
        signals["schema"] = list(set(signals["schema"]))
        signals["alt_text"] = list(set(signals["alt_text"]))
        signals["geo_signals"] = list(set(signals["geo_signals"]))
        
        print(f"✅ Signals extracted: {signals['brand_name']}, {len(signals['faqs'])} FAQs, {len(signals['products'])} products")
        
        return signals
        
    except Exception as e:
        print(f"❌ Signal extraction failed: {e}")
        return {
            "brand_name": "Unknown",
            "description": "",
            "location": "",
            "industry": "Unknown",
            "products": [],
            "faqs": [],
            "topics": [],
            "competitors": [],
            "schema": [],
            "alt_text": [],
            "geo_signals": []
        }

# Helper functions for extraction

def extract_title(soup: BeautifulSoup) -> str:
    """Extract page title"""
    title_tag = soup.find('title')
    return title_tag.get_text().strip() if title_tag else ""

def extract_meta_description(soup: BeautifulSoup) -> str:
    """Extract meta description"""
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    return meta_desc.get('content', '').strip() if meta_desc else ""

def extract_visible_text(soup: BeautifulSoup) -> str:
    """Extract visible text content"""
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()
    
    # Get text
    text = soup.get_text()
    
    # Clean up whitespace
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = ' '.join(chunk for chunk in chunks if chunk)
    
    return text

def extract_images(soup: BeautifulSoup) -> List[Dict]:
    """Extract image data"""
    images = []
    for img in soup.find_all('img'):
        images.append({
            "src": img.get('src', ''),
            "alt": img.get('alt', ''),
            "title": img.get('title', '')
        })
    return images

def extract_internal_links(soup: BeautifulSoup, base_url: str) -> List[str]:
    """Extract internal links"""
    links = []
    base_domain = urlparse(base_url).netloc
    
    for link in soup.find_all('a', href=True):
        href = link['href']
        full_url = urljoin(base_url, href)
        link_domain = urlparse(full_url).netloc
        
        if link_domain == base_domain:
            links.append(full_url)
    
    return list(set(links))

def extract_brand_name(soup: BeautifulSoup, title: str) -> str:
    """Extract brand name from various sources"""
    # Try og:site_name
    og_site = soup.find('meta', property='og:site_name')
    if og_site:
        return og_site.get('content', '').strip()
    
    # Try schema.org Organization
    org_schema = soup.find('script', type='application/ld+json')
    if org_schema:
        try:
            data = json.loads(org_schema.string)
            if isinstance(data, dict) and data.get('@type') == 'Organization':
                return data.get('name', '').strip()
        except:
            pass
    
    # Use title as fallback
    return title.split(' - ')[0].split(' | ')[0].strip()

def extract_location(soup: BeautifulSoup) -> str:
    """Extract location information"""
    # Try LocalBusiness schema
    schema_scripts = soup.find_all('script', type='application/ld+json')
    for script in schema_scripts:
        try:
            data = json.loads(script.string)
            if isinstance(data, dict) and data.get('@type') == 'LocalBusiness':
                address = data.get('address', {})
                if isinstance(address, dict):
                    return address.get('addressLocality', '')
        except:
            pass
    
    # Look for contact information in text
    text = soup.get_text().lower()
    locations = ['lithuania', 'latvia', 'estonia', 'poland', 'germany', 'france', 'spain', 'italy']
    for location in locations:
        if location in text:
            return location.title()
    
    return ""

def extract_products(soup: BeautifulSoup) -> List[str]:
    """Extract products/services"""
    products = []
    
    # Look for product schema
    schema_scripts = soup.find_all('script', type='application/ld+json')
    for script in schema_scripts:
        try:
            data = json.loads(script.string)
            if isinstance(data, dict) and data.get('@type') == 'Product':
                products.append(data.get('name', ''))
        except:
            pass
    
    # Look for headings that might indicate products
    headings = soup.find_all(['h1', 'h2', 'h3'])
    for heading in headings:
        text = heading.get_text().strip().lower()
        if any(word in text for word in ['product', 'service', 'perfume', 'subscription']):
            products.append(heading.get_text().strip())
    
    return products

def extract_faqs(soup: BeautifulSoup) -> List[str]:
    """Extract FAQ questions"""
    faqs = []
    
    # Look for FAQ schema
    schema_scripts = soup.find_all('script', type='application/ld+json')
    for script in schema_scripts:
        try:
            data = json.loads(script.string)
            if isinstance(data, dict) and data.get('@type') == 'FAQPage':
                main_entity = data.get('mainEntity', [])
                for item in main_entity:
                    if isinstance(item, dict):
                        faqs.append(item.get('name', ''))
        except:
            pass
    
    # Look for question patterns in text
    text = soup.get_text()
    question_pattern = r'(?:What|How|Why|When|Where|Can|Is|Are|Do|Does)\s+[^?]*\?'
    questions = re.findall(question_pattern, text, re.IGNORECASE)
    faqs.extend(questions[:5])  # Limit to 5 questions
    
    return faqs

def extract_topics(soup: BeautifulSoup) -> List[str]:
    """Extract topic keywords"""
    topics = []
    
    # Look for keywords in headings
    headings = soup.find_all(['h1', 'h2', 'h3'])
    for heading in headings:
        text = heading.get_text().strip().lower()
        if len(text) < 50:  # Short headings are likely topics
            topics.append(text)
    
    return topics[:10]  # Limit to 10 topics

def extract_competitors(soup: BeautifulSoup) -> List[str]:
    """Extract competitor mentions"""
    competitors = []
    text = soup.get_text().lower()
    
    # Common competitor patterns
    competitor_patterns = [
        r'vs\s+(\w+)',
        r'compared\s+to\s+(\w+)',
        r'alternative\s+to\s+(\w+)',
        r'better\s+than\s+(\w+)'
    ]
    
    for pattern in competitor_patterns:
        matches = re.findall(pattern, text)
        competitors.extend(matches)
    
    return list(set(competitors))

def extract_schema(soup: BeautifulSoup) -> List[str]:
    """Extract schema.org types"""
    schemas = []
    schema_scripts = soup.find_all('script', type='application/ld+json')
    
    for script in schema_scripts:
        try:
            data = json.loads(script.string)
            if isinstance(data, dict) and '@type' in data:
                schemas.append(data['@type'])
        except:
            pass
    
    return schemas

def extract_alt_text_issues(images: List[Dict]) -> List[str]:
    """Extract images with missing/weak alt text"""
    issues = []
    
    for img in images:
        alt = img.get('alt', '').strip()
        if not alt:
            issues.append(f"Missing alt text: {img.get('src', '')}")
        elif len(alt) < 5:
            issues.append(f"Weak alt text: {img.get('src', '')} - '{alt}'")
    
    return issues

def extract_geo_signals(soup: BeautifulSoup) -> List[str]:
    """Extract geographic signals"""
    signals = []
    
    # Look for hreflang
    hreflang_links = soup.find_all('link', rel='alternate', hreflang=True)
    for link in hreflang_links:
        signals.append(f"hreflang: {link.get('hreflang')}")
    
    # Look for geo meta tags
    geo_meta = soup.find_all('meta', attrs={'name': re.compile(r'geo\.', re.I)})
    for meta in geo_meta:
        signals.append(f"geo: {meta.get('name')} = {meta.get('content')}")
    
    return signals
