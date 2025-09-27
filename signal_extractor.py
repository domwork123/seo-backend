"""
Signal extraction for AEO + GEO optimization
Extracts brand, FAQ, schema, and geographic signals from crawled pages
"""

import re
import json
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
import uuid

def extract_signals_from_pages(pages: List[Dict]) -> Dict[str, Any]:
    """
    Extract AEO + GEO signals from crawled pages
    
    Args:
        pages: List of crawled page data
        
    Returns:
        Dict with extracted signals
    """
    
    print(f"🔍 Extracting signals from {len(pages)} pages")
    
    # Initialize signal containers
    all_faqs = []
    all_schemas = []
    all_images = []
    all_geo_signals = []
    competitors = set()
    
    brand_name = ""
    description = ""
    location = ""
    products = []
    topics = []
    
    for page in pages:
        html = page.get("html", "")
        raw_text = page.get("raw_text", "")
        url = page.get("url", "")
        title = page.get("title", "")
        
        # Extract brand name (from first page or most relevant)
        if not brand_name:
            brand_name = _extract_brand_name(html, title, url)
        
        # Extract description (from first page)
        if not description:
            description = page.get("meta_description", "")
        
        # Extract FAQs
        page_faqs = _extract_faqs(html, raw_text)
        all_faqs.extend(page_faqs)
        
        # Extract schema markup
        page_schemas = _extract_schema_markup(html)
        all_schemas.extend(page_schemas)
        
        # Extract images with missing/weak alt text
        page_images = _extract_image_issues(page.get("images", []))
        all_images.extend(page_images)
        
        # Extract geographic signals
        page_geo = _extract_geo_signals(html, raw_text)
        all_geo_signals.extend(page_geo)
        
        # Extract competitors
        page_competitors = _extract_competitors(raw_text)
        competitors.update(page_competitors)
        
        # Extract products/services
        page_products = _extract_products(html, raw_text)
        products.extend(page_products)
        
        # Extract topics
        page_topics = _extract_topics(raw_text, title)
        topics.extend(page_topics)
    
    # Extract location from geo signals or content
    if not location:
        location = _extract_location(all_geo_signals, raw_text)
    
    # Clean and deduplicate
    products = list(set(products))
    topics = list(set(topics))
    competitors = list(competitors)
    
    print(f"✅ Extracted: {len(all_faqs)} FAQs, {len(all_schemas)} schemas, {len(all_images)} image issues")
    
    return {
        "brand_name": brand_name,
        "description": description,
        "location": location,
        "products": products,
        "topics": topics,
        "faqs": all_faqs,
        "schemas": all_schemas,
        "alt_text_issues": all_images,
        "geo_signals": all_geo_signals,
        "competitors": competitors
    }

def _extract_brand_name(html: str, title: str, url: str) -> str:
    """Extract brand name from various sources"""
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Try og:site_name
    og_site = soup.find('meta', property='og:site_name')
    if og_site and og_site.get('content'):
        return og_site['content'].strip()
    
    # Try schema.org Organization
    org_schema = soup.find('script', type='application/ld+json')
    if org_schema:
        try:
            schema_data = json.loads(org_schema.string)
            if isinstance(schema_data, dict) and schema_data.get('@type') == 'Organization':
                return schema_data.get('name', '')
        except:
            pass
    
    # Try title (remove common suffixes)
    if title:
        title_clean = re.sub(r'\s*[-|]\s*(Home|Welcome|Official).*$', '', title)
        if title_clean and len(title_clean) > 3:
            return title_clean
    
    # Fallback to domain name
    from urllib.parse import urlparse
    domain = urlparse(url).netloc
    return domain.replace('www.', '').split('.')[0].title()

def _extract_faqs(html: str, raw_text: str) -> List[Dict[str, str]]:
    """Extract FAQ content from page"""
    
    faqs = []
    soup = BeautifulSoup(html, 'html.parser')
    
    # Look for FAQ schema
    faq_scripts = soup.find_all('script', type='application/ld+json')
    for script in faq_scripts:
        try:
            data = json.loads(script.string)
            if isinstance(data, dict) and data.get('@type') == 'FAQPage':
                main_entity = data.get('mainEntity', [])
                for item in main_entity:
                    if isinstance(item, dict):
                        faqs.append({
                            "question": item.get('name', ''),
                            "answer": item.get('acceptedAnswer', {}).get('text', '')
                        })
        except:
            continue
    
    # Look for Q&A patterns in text
    qa_patterns = [
        r'Q:\s*(.+?)\s*A:\s*(.+?)(?=Q:|$)',
        r'Question:\s*(.+?)\s*Answer:\s*(.+?)(?=Question:|$)',
        r'(.+?)\?\s*(.+?)(?=\n\n|\n[A-Z])'
    ]
    
    for pattern in qa_patterns:
        matches = re.findall(pattern, raw_text, re.DOTALL | re.IGNORECASE)
        for match in matches:
            if len(match) == 2:
                faqs.append({
                    "question": match[0].strip(),
                    "answer": match[1].strip()
                })
    
    return faqs

def _extract_schema_markup(html: str) -> List[Dict[str, Any]]:
    """Extract all schema.org markup from page"""
    
    schemas = []
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find all JSON-LD scripts
    scripts = soup.find_all('script', type='application/ld+json')
    for script in scripts:
        try:
            data = json.loads(script.string)
            schemas.append({
                "type": data.get('@type', 'Unknown'),
                "data": data
            })
        except:
            continue
    
    return schemas

def _extract_image_issues(images: List[Dict]) -> List[Dict[str, str]]:
    """Extract images with missing or weak alt text"""
    
    issues = []
    for img in images:
        alt = img.get('alt', '')
        src = img.get('src', '')
        
        # Check for missing or weak alt text
        if not alt or len(alt) < 3 or alt.lower() in ['image', 'img', 'photo', 'picture']:
            issues.append({
                "src": src,
                "alt": alt,
                "issue": "missing" if not alt else "weak"
            })
    
    return issues

def _extract_geo_signals(html: str, raw_text: str) -> List[Dict[str, Any]]:
    """Extract geographic optimization signals"""
    
    geo_signals = []
    soup = BeautifulSoup(html, 'html.parser')
    
    # Check for hreflang tags
    hreflang_tags = soup.find_all('link', rel='alternate', hreflang=True)
    for tag in hreflang_tags:
        geo_signals.append({
            "type": "hreflang",
            "hreflang": tag.get('hreflang'),
            "href": tag.get('href')
        })
    
    # Check for geo meta tags
    geo_meta = soup.find_all('meta', attrs={'name': re.compile(r'geo\.', re.I)})
    for meta in geo_meta:
        geo_signals.append({
            "type": "geo_meta",
            "name": meta.get('name'),
            "content": meta.get('content')
        })
    
    # Check for LocalBusiness schema
    scripts = soup.find_all('script', type='application/ld+json')
    for script in scripts:
        try:
            data = json.loads(script.string)
            if isinstance(data, dict) and data.get('@type') == 'LocalBusiness':
                geo_signals.append({
                    "type": "LocalBusiness_schema",
                    "data": data
                })
        except:
            continue
    
    return geo_signals

def _extract_competitors(raw_text: str) -> List[str]:
    """Extract competitor mentions from text"""
    
    # Common competitor patterns (this would be more sophisticated in production)
    competitor_keywords = [
        'competitor', 'alternative', 'vs', 'compared to', 'better than',
        'instead of', 'similar to', 'like', 'such as'
    ]
    
    competitors = []
    text_lower = raw_text.lower()
    
    for keyword in competitor_keywords:
        if keyword in text_lower:
            # Extract surrounding context (simplified)
            pattern = rf'\b\w+\s+{keyword}\s+\w+'
            matches = re.findall(pattern, text_lower)
            competitors.extend(matches)
    
    return list(set(competitors))

def _extract_products(html: str, raw_text: str) -> List[str]:
    """Extract products/services mentioned"""
    
    products = []
    soup = BeautifulSoup(html, 'html.parser')
    
    # Look for product schema
    scripts = soup.find_all('script', type='application/ld+json')
    for script in scripts:
        try:
            data = json.loads(script.string)
            if isinstance(data, dict) and data.get('@type') == 'Product':
                products.append(data.get('name', ''))
        except:
            continue
    
    # Extract from headings (H1, H2, H3)
    headings = soup.find_all(['h1', 'h2', 'h3'])
    for heading in headings:
        text = heading.get_text().strip()
        if text and len(text) < 50:  # Reasonable product name length
            products.append(text)
    
    return [p for p in products if p and len(p) > 2]

def _extract_topics(raw_text: str, title: str) -> List[str]:
    """Extract topic keywords from content"""
    
    # Simple keyword extraction (would be more sophisticated in production)
    words = re.findall(r'\b[a-zA-Z]{4,}\b', raw_text.lower())
    
    # Filter common words
    stop_words = {'this', 'that', 'with', 'from', 'they', 'have', 'been', 'were', 'said', 'each', 'which', 'their', 'time', 'will', 'about', 'there', 'could', 'other', 'after', 'first', 'well', 'also', 'where', 'much', 'some', 'these', 'would', 'into', 'has', 'more', 'very', 'what', 'know', 'just', 'first', 'over', 'think', 'also', 'back', 'after', 'use', 'two', 'how', 'our', 'work', 'life', 'only', 'can', 'still', 'should', 'because', 'through', 'before', 'here', 'when', 'much', 'take', 'than', 'its', 'who', 'oil', 'sit', 'now', 'find', 'long', 'down', 'day', 'did', 'get', 'may', 'say', 'she', 'use', 'her', 'many', 'some', 'time', 'very', 'when', 'come', 'here', 'just', 'like', 'long', 'make', 'many', 'over', 'such', 'take', 'than', 'them', 'well', 'were'}
    
    topics = [word for word in words if word not in stop_words]
    
    # Add title words
    title_words = re.findall(r'\b[a-zA-Z]{4,}\b', title.lower())
    topics.extend(title_words)
    
    # Return most common topics
    from collections import Counter
    topic_counts = Counter(topics)
    return [topic for topic, count in topic_counts.most_common(10)]

def _extract_location(geo_signals: List[Dict], raw_text: str) -> str:
    """Extract location from geo signals or content"""
    
    # Check geo signals first
    for signal in geo_signals:
        if signal.get('type') == 'LocalBusiness_schema':
            address = signal.get('data', {}).get('address', {})
            if isinstance(address, dict):
                return address.get('addressLocality', '')
    
    # Look for location patterns in text
    location_patterns = [
        r'in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'located\s+in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'based\s+in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
    ]
    
    for pattern in location_patterns:
        matches = re.findall(pattern, raw_text)
        if matches:
            return matches[0]
    
    return ""
