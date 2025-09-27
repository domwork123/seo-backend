#!/usr/bin/env python3
"""
Direct test of the /audit endpoint functionality
Tests the core logic without FastAPI server dependencies
"""

import sys
import os
import uuid
sys.path.append('.')

def test_audit_endpoint_direct():
    """Test the audit endpoint logic directly"""
    print("🧪 Testing /audit endpoint logic directly...")
    
    try:
        # Import the core components
        from scrapingbee_crawler import crawl_website_with_scrapingbee
        from signal_extractor import extract_signals_from_pages
        from supabase_schema import ensure_schema_exists, save_audit_data
        
        # Simulate the /audit endpoint request
        test_url = "https://example.com"
        print(f"🚀 Starting EVIKA audit for: {test_url}")
        
        # Generate unique site_id for this audit
        site_id = str(uuid.uuid4())
        print(f"📋 Generated site_id: {site_id}")
        
        # Ensure Supabase schema exists
        print("🔧 Ensuring Supabase schema...")
        schema_ok = ensure_schema_exists()
        if not schema_ok:
            print("⚠️ Schema setup failed, continuing anyway...")
        
        # Step 1: Crawl website with ScrapingBee (15 pages max)
        print(f"🕷️ Crawling website with ScrapingBee...")
        crawl_result = crawl_website_with_scrapingbee(test_url, max_pages=15)
        
        if not crawl_result.get("success"):
            return {
                "error": f"Crawl failed: {crawl_result.get('error', 'Unknown error')}",
                "site_id": site_id
            }
        
        pages = crawl_result.get("pages", [])
        print(f"✅ Crawled {len(pages)} pages successfully")
        
        # Step 2: Extract signals from crawled data
        print(f"🔍 Extracting AEO + GEO signals...")
        signals = extract_signals_from_pages(pages)
        
        # Step 3: Save to Supabase
        print(f"💾 Saving to Supabase...")
        save_success = save_audit_data(site_id, test_url, pages, signals)
        
        if not save_success:
            print("⚠️ Failed to save to Supabase, but continuing...")
        
        # Step 4: Return structured JSON (simulating the endpoint response)
        response = {
            "site_id": site_id,
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
        
        print(f"✅ /audit endpoint logic works!")
        print(f"   - Site ID: {response['site_id']}")
        print(f"   - Brand: {response['brand_name']}")
        print(f"   - Description: {response['description']}")
        print(f"   - Products: {len(response['products'])}")
        print(f"   - Location: {response['location']}")
        print(f"   - FAQs: {len(response['faqs'])}")
        print(f"   - Topics: {len(response['topics'])}")
        print(f"   - Competitors: {len(response['competitors'])}")
        print(f"   - Pages Crawled: {response['pages_crawled']}")
        print(f"   - Success: {response['success']}")
        
        return response
        
    except Exception as e:
        print(f"❌ /audit endpoint logic failed: {e}")
        return {
            "error": f"Audit failed: {str(e)}",
            "site_id": site_id if 'site_id' in locals() else None
        }

def test_multiple_urls():
    """Test with different URLs to verify robustness"""
    print("\n🧪 Testing with multiple URLs...")
    
    test_urls = [
        "https://example.com",
        "https://seal.lt",
        "https://github.com"
    ]
    
    results = []
    
    for url in test_urls:
        print(f"\n--- Testing {url} ---")
        try:
            from scrapingbee_crawler import crawl_website_with_scrapingbee
            from signal_extractor import extract_signals_from_pages
            
            # Test crawl
            crawl_result = crawl_website_with_scrapingbee(url, max_pages=3)
            if crawl_result.get("success"):
                pages = crawl_result.get("pages", [])
                signals = extract_signals_from_pages(pages)
                
                print(f"✅ {url}: {len(pages)} pages, brand: {signals.get('brand_name', 'N/A')}")
                results.append(True)
            else:
                print(f"❌ {url}: Crawl failed")
                results.append(False)
                
        except Exception as e:
            print(f"❌ {url}: Error - {e}")
            results.append(False)
    
    passed = sum(results)
    total = len(results)
    print(f"\n🎯 Multiple URL test: {passed}/{total} passed")
    return passed == total

def main():
    """Run direct endpoint tests"""
    print("🚀 Testing EVIKA /audit endpoint directly\n")
    
    # Test 1: Direct endpoint logic
    print("="*60)
    print("TEST 1: Direct /audit endpoint logic")
    print("="*60)
    
    result1 = test_audit_endpoint_direct()
    success1 = result1.get("success", False) and "error" not in result1
    
    # Test 2: Multiple URLs
    print("\n" + "="*60)
    print("TEST 2: Multiple URL testing")
    print("="*60)
    
    success2 = test_multiple_urls()
    
    # Summary
    print("\n" + "="*60)
    print("DIRECT TEST SUMMARY")
    print("="*60)
    
    print(f"{'✅ PASS' if success1 else '❌ FAIL'} Direct endpoint logic")
    print(f"{'✅ PASS' if success2 else '❌ FAIL'} Multiple URL testing")
    
    total_passed = sum([success1, success2])
    print(f"\n🎯 Results: {total_passed}/2 tests passed")
    
    if total_passed == 2:
        print("🎉 All direct tests passed! The /audit endpoint logic is working!")
    else:
        print("⚠️ Some tests failed. Check the errors above.")
    
    return total_passed == 2

if __name__ == "__main__":
    main()
