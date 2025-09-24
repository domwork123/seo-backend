#!/usr/bin/env python3
"""
Test script to verify Browserless can bypass Cloudflare protection
"""
import requests
import json
import time

def test_browserless_local():
    """Test if Browserless is running locally"""
    try:
        print("Testing local Browserless instance...")
        response = requests.post(
            "http://localhost:3000/content",
            json={
                "url": "https://www.parfumada.lt/",
                "options": {
                    "waitUntil": "networkidle0",
                    "timeout": 30000
                }
            },
            timeout=60
        )
        
        if response.status_code == 200:
            html = response.text
            print(f"✅ SUCCESS: Got HTML content ({len(html)} chars)")
            print(f"First 200 chars: {html[:200]}")
            
            # Check if it's actually parfumada.lt content
            if "parfumada" in html.lower() or "perfume" in html.lower():
                print("✅ CONFIRMED: This is actual parfumada.lt content!")
                return True
            else:
                print("❌ WARNING: Content doesn't look like parfumada.lt")
                return False
        else:
            print(f"❌ FAILED: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Browserless not running locally")
        print("💡 To start Browserless locally, run:")
        print("   docker run -p 3000:3000 ghcr.io/browserless/chromium")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_browserless_cloud():
    """Test Browserless cloud service (requires API token)"""
    try:
        print("\nTesting Browserless cloud service...")
        response = requests.post(
            "https://chrome.browserless.io/content",
            json={
                "url": "https://www.parfumada.lt/",
                "options": {
                    "waitUntil": "networkidle0",
                    "timeout": 30000
                }
            },
            timeout=60
        )
        
        if response.status_code == 200:
            html = response.text
            print(f"✅ SUCCESS: Got HTML content ({len(html)} chars)")
            return True
        elif response.status_code == 401:
            print("❌ AUTH REQUIRED: Need API token for cloud service")
            print("💡 Sign up at https://www.browserless.io/sign-up")
            return False
        else:
            print(f"❌ FAILED: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_regular_requests():
    """Test regular requests for comparison"""
    try:
        print("\nTesting regular requests (should fail)...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get("https://www.parfumada.lt/", headers=headers, timeout=30)
        
        if response.status_code == 200:
            html = response.text
            print(f"Response length: {len(html)} chars")
            
            # Check if blocked
            if len(html) < 200 or "cloudflare" in html.lower() or "attention required" in html.lower():
                print("❌ CONFIRMED: Regular requests are blocked by Cloudflare")
                return False
            else:
                print("✅ UNEXPECTED: Regular requests worked!")
                return True
        else:
            print(f"❌ FAILED: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Browserless Cloudflare Bypass")
    print("=" * 50)
    
    # Test regular requests first
    regular_works = test_regular_requests()
    
    # Test Browserless cloud
    cloud_works = test_browserless_cloud()
    
    # Test local Browserless
    local_works = test_browserless_local()
    
    print("\n" + "=" * 50)
    print("📊 RESULTS:")
    print(f"Regular requests: {'✅ Works' if regular_works else '❌ Blocked'}")
    print(f"Browserless cloud: {'✅ Works' if cloud_works else '❌ Failed'}")
    print(f"Browserless local: {'✅ Works' if local_works else '❌ Not running'}")
    
    if local_works or cloud_works:
        print("\n🎉 SUCCESS: Browserless can bypass Cloudflare!")
        print("💡 We can proceed with implementation")
    else:
        print("\n❌ FAILED: Browserless not working")
        print("💡 Need to set up Browserless properly first")
