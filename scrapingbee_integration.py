# ScrapingBee Integration for Website Scraping
import requests
import json
from typing import Dict, Any, Optional
from scrapingbee_config import get_scrapingbee_config

async def fetch_with_scrapingbee(url: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Fetch website content using ScrapingBee API
    
    Args:
        url: The URL to scrape
        options: Additional options for ScrapingBee
        
    Returns:
        Dict containing HTML content, status, and metadata
    """
    try:
        config = get_scrapingbee_config()
        
        # Default options for ScrapingBee
        default_options = {
            "render_js": True,  # Execute JavaScript
            "premium_proxy": True,  # Use premium proxies
            "country_code": "US",  # Target country
            "wait": 3000,  # Wait 3 seconds for page load
            "wait_for": "networkidle",  # Wait for network to be idle
        }
        
        # Merge with provided options
        if options:
            default_options.update(options)
        
        # Prepare request
        params = {
            "api_key": config["api_key"],
            "url": url,
            **default_options
        }
        
        print(f"DEBUG: Fetching {url} with ScrapingBee")
        
        # Make request to ScrapingBee
        response = requests.get(
            config["base_url"],
            params=params,
            timeout=60
        )
        
        print(f"DEBUG: ScrapingBee response status: {response.status_code}")
        
        if response.status_code == 200:
            html_content = response.text
            print(f"DEBUG: ScrapingBee HTML length: {len(html_content)}")
            
            # Check if content is valid
            if len(html_content) > 200 and not _is_blocked_content(html_content):
                return {
                    "status": "success",
                    "html": html_content,
                    "method": "scrapingbee",
                    "metadata": {
                        "content_length": len(html_content),
                        "options_used": default_options
                    }
                }
            else:
                return {
                    "status": "blocked",
                    "html": html_content,
                    "method": "scrapingbee",
                    "error": "Content appears to be blocked or invalid"
                }
        else:
            return {
                "status": "failed",
                "html": "",
                "method": "scrapingbee",
                "error": f"ScrapingBee HTTP {response.status_code}: {response.text}"
            }
            
    except Exception as e:
        print(f"DEBUG: ScrapingBee error: {e}")
        return {
            "status": "failed",
            "html": "",
            "method": "scrapingbee",
            "error": str(e)
        }

def _is_blocked_content(html: str) -> bool:
    """Check if content is blocked or invalid"""
    if not html or len(html) < 200:
        return True
    
    html_lower = html.lower()
    
    # Check for blocking indicators
    blocking_indicators = [
        "access denied",
        "blocked",
        "captcha",
        "cloudflare",
        "rate limited",
        "too many requests"
    ]
    
    for indicator in blocking_indicators:
        if indicator in html_lower:
            return True
    
    return False

async def test_scrapingbee():
    """Test ScrapingBee with a simple website"""
    test_url = "https://example.com"
    result = await fetch_with_scrapingbee(test_url)
    
    print(f"ScrapingBee test result: {result['status']}")
    if result['status'] == 'success':
        print(f"Content length: {len(result['html'])}")
        print(f"First 200 chars: {result['html'][:200]}")
    
    return result
