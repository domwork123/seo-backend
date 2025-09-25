#!/usr/bin/env python3
"""
Direct test of ScrapingBee API to debug the integration
"""

import requests
import os

def test_scrapingbee_direct():
    """Test ScrapingBee API directly"""
    
    # Get API key from environment
    api_key = os.getenv("SCRAPINGBEE_API_KEY")
    if not api_key:
        print("ERROR: SCRAPINGBEE_API_KEY not found in environment")
        return
    
    print(f"Using API key: {api_key[:10]}...")
    
    # Test URL
    url = "https://www.parfumada.lt/"
    
    # ScrapingBee API endpoint
    api_url = "https://app.scrapingbee.com/api/v1"
    
    # Parameters based on documentation
    params = {
        "api_key": api_key,
        "url": url,
        "render_js": True,
        "premium_proxy": False,
        "block_resources": True,
        "wait_browser": "domcontentloaded",
        "country_code": "US"
    }
    
    print(f"Making request to ScrapingBee...")
    print(f"URL: {api_url}")
    print(f"Params: {params}")
    
    try:
        response = requests.get(api_url, params=params, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Text (first 500 chars): {response.text[:500]}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: ScrapingBee returned 200")
            print(f"HTML length: {len(response.text)}")
        else:
            print(f"❌ ERROR: ScrapingBee returned {response.status_code}")
            
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")

if __name__ == "__main__":
    test_scrapingbee_direct()
