#!/usr/bin/env python3
"""
Test script to debug parfumada.lt specifically
"""
import requests
import asyncio
import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_parfumada_direct():
    """Test parfumada.lt directly with requests"""
    print("Testing parfumada.lt directly...")
    
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
        
        # Test both URLs
        urls = [
            "https://parfumada.lt/",
            "https://www.parfumada.lt/"
        ]
        
        for url in urls:
            print(f"\nTesting {url}...")
            try:
                response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
                print(f"Status: {response.status_code}")
                print(f"Final URL: {response.url}")
                print(f"Content length: {len(response.text)}")
                print(f"First 200 chars: {response.text[:200]}")
                
                # Check for blocking indicators
                html_lower = response.text.lower()
                blocking_indicators = [
                    'attention required | cloudflare',
                    'checking your browser before accessing',
                    'cloudflare',
                    'captcha',
                    'security check'
                ]
                
                for indicator in blocking_indicators:
                    if indicator in html_lower:
                        print(f"BLOCKED: Found '{indicator}' in content")
                        break
                else:
                    print("Content appears to be accessible")
                    
            except Exception as e:
                print(f"Error: {e}")
                
    except Exception as e:
        print(f"General error: {e}")

if __name__ == "__main__":
    test_parfumada_direct()
