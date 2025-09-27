#!/usr/bin/env python3
"""
Test script for the /audit endpoint functionality
Tests core components without dependency issues
"""

import sys
import os
sys.path.append('.')

def test_scrapingbee_crawler():
    """Test ScrapingBee crawler functionality"""
    print("🧪 Testing ScrapingBee crawler...")
    
    try:
        from scrapingbee_crawler import crawl_website_with_scrapingbee
        
        # Test with a simple URL
        test_url = "https://example.com"
        result = crawl_website_with_scrapingbee(test_url, max_pages=3)
        
        if result.get("success"):
            print(f"✅ ScrapingBee crawler works - crawled {len(result.get('pages', []))} pages")
            return True
        else:
            print(f"❌ ScrapingBee crawler failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ ScrapingBee crawler error: {e}")
        return False

def test_signal_extractor():
    """Test signal extraction functionality"""
    print("🧪 Testing signal extractor...")
    
    try:
        from signal_extractor import extract_signals_from_pages
        
        # Mock page data
        mock_pages = [
            {
                "url": "https://example.com",
                "title": "Example Website",
                "meta_description": "A great website",
                "html": "<html><head><title>Example</title></head><body><h1>Welcome</h1><p>This is a test.</p></body></html>",
                "raw_text": "Welcome This is a test.",
                "images": [{"src": "/logo.png", "alt": "Logo"}]
            }
        ]
        
        signals = extract_signals_from_pages(mock_pages)
        
        print(f"✅ Signal extractor works - extracted {len(signals)} signal types")
        print(f"   - Brand: {signals.get('brand_name', 'N/A')}")
        print(f"   - Products: {len(signals.get('products', []))}")
        print(f"   - FAQs: {len(signals.get('faqs', []))}")
        return True
        
    except Exception as e:
        print(f"❌ Signal extractor error: {e}")
        return False

def test_audit_workflow():
    """Test the complete audit workflow"""
    print("🧪 Testing complete audit workflow...")
    
    try:
        # Test the workflow without Supabase
        from scrapingbee_crawler import crawl_website_with_scrapingbee
        from signal_extractor import extract_signals_from_pages
        
        # Step 1: Crawl
        test_url = "https://example.com"
        crawl_result = crawl_website_with_scrapingbee(test_url, max_pages=3)
        
        if not crawl_result.get("success"):
            print(f"❌ Crawl failed: {crawl_result.get('error')}")
            return False
        
        pages = crawl_result.get("pages", [])
        print(f"✅ Crawled {len(pages)} pages")
        
        # Step 2: Extract signals
        signals = extract_signals_from_pages(pages)
        print(f"✅ Extracted signals: {list(signals.keys())}")
        
        # Step 3: Simulate response
        response = {
            "site_id": "test-uuid-123",
            "url": test_url,
            "brand_name": signals.get("brand_name", "Unknown"),
            "description": signals.get("description", ""),
            "products": signals.get("products", []),
            "location": signals.get("location", ""),
            "faqs": [faq.get("question", "") for faq in signals.get("faqs", [])],
            "topics": signals.get("topics", []),
            "competitors": signals.get("competitors", []),
            "pages_crawled": len(pages),
            "success": True
        }
        
        print(f"✅ Complete workflow successful")
        print(f"   - Site ID: {response['site_id']}")
        print(f"   - Brand: {response['brand_name']}")
        print(f"   - Pages: {response['pages_crawled']}")
        return True
        
    except Exception as e:
        print(f"❌ Audit workflow error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing EVIKA /audit endpoint components\n")
    
    tests = [
        ("ScrapingBee Crawler", test_scrapingbee_crawler),
        ("Signal Extractor", test_signal_extractor),
        ("Complete Workflow", test_audit_workflow)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Testing: {test_name}")
        print('='*50)
        
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Test {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print('='*50)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! The /audit endpoint is ready!")
    else:
        print("⚠️ Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main()
