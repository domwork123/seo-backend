# ScrapingBee Integration for Website Scraping
import requests
import json
from typing import Dict, Any, Optional
from scrapingbee_config import get_scrapingbee_config

def fetch_with_scrapingbee(url: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
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
        
        # Default options for ScrapingBee (based on official documentation)
        default_options = {
            "render_js": True,  # Execute JavaScript (boolean)
            "premium_proxy": False,  # Use classic proxy (boolean)
            "country_code": "US",  # Target country
            "wait": 0,  # No wait
            "wait_browser": "domcontentloaded",  # Wait for DOM content loaded
            "block_resources": True,  # Block resources (boolean)
            "timeout": 30000,  # 30 second timeout
        }
        
        # Merge with provided options
        if options:
            default_options.update(options)
        
        # Prepare request parameters (GET method with query params)
        params = {
            "api_key": config["api_key"],
            "url": url,
            **default_options
        }
        
        print(f"DEBUG: Fetching {url} with ScrapingBee")
        print(f"DEBUG: ScrapingBee params: {params}")
        
        # Make GET request to ScrapingBee (correct method based on your successful test)
        response = requests.get(
            config["base_url"],
            params=params,
            timeout=60
        )
        
        print(f"DEBUG: ScrapingBee response status: {response.status_code}")
        print(f"DEBUG: ScrapingBee response text: {response.text[:500]}")
        
        if response.status_code == 200:
            html_content = response.text
            print(f"DEBUG: ScrapingBee HTML length: {len(html_content)}")
            
            # Check if content is valid
            is_blocked = _is_blocked_content(html_content)
            print(f"DEBUG: Content length: {len(html_content)}")
            print(f"DEBUG: Is blocked: {is_blocked}")
            print(f"DEBUG: First 200 chars: {html_content[:200]}")
            
            if len(html_content) > 200 and not is_blocked:
                print(f"DEBUG: ScrapingBee SUCCESS for {url}")
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
                print(f"DEBUG: ScrapingBee BLOCKED for {url} - length: {len(html_content)}, blocked: {is_blocked}")
                return {
                    "status": "blocked",
                    "html": html_content,
                    "method": "scrapingbee",
                    "error": f"Content appears to be blocked or invalid - length: {len(html_content)}, blocked: {is_blocked}"
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
    
    # Check for specific blocking indicators (more precise)
    blocking_indicators = [
        "access denied",
        "blocked by",
        "captcha required",
        "cloudflare checking your browser",
        "rate limited",
        "too many requests",
        "please wait while we check your browser"
    ]
    
    for indicator in blocking_indicators:
        if indicator in html_lower:
            return True
    
    # Check for very short content that might be error pages
    if len(html) < 500:
        return True
    
    return False

def test_scrapingbee():
    """Test ScrapingBee with a simple website"""
    test_url = "https://example.com"
    result = fetch_with_scrapingbee(test_url)
    
    print(f"ScrapingBee test result: {result['status']}")
    if result['status'] == 'success':
        print(f"Content length: {len(result['html'])}")
        print(f"First 200 chars: {result['html'][:200]}")
    
    return result
