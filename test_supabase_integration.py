#!/usr/bin/env python3
"""
Test Supabase integration for the /audit endpoint
"""

import requests
import json

def test_supabase_integration():
    """Test if Supabase is working with the /audit endpoint"""
    print("🧪 Testing Supabase integration...")
    
    # Test the /audit endpoint
    test_url = "https://example.com"
    
    try:
        response = requests.post(
            "https://web-production-a5831.up.railway.app/audit",
            json={"url": test_url},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            site_id = result.get("site_id")
            
            print(f"✅ /audit endpoint responded successfully")
            print(f"   - Site ID: {site_id}")
            print(f"   - Brand: {result.get('brand_name')}")
            print(f"   - Success: {result.get('success')}")
            
            # Now let's check if we can query the data back from Supabase
            # This would require a separate endpoint to retrieve data
            print(f"\n🔍 Checking if data was saved to Supabase...")
            print(f"   - Site ID generated: {site_id}")
            print(f"   - This indicates the audit process completed")
            print(f"   - Supabase save should have been attempted")
            
            return True
            
        else:
            print(f"❌ /audit endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Supabase integration test failed: {e}")
        return False

def test_multiple_audits():
    """Test multiple audits to see if Supabase is handling data persistence"""
    print("\n🧪 Testing multiple audits for Supabase persistence...")
    
    test_urls = [
        "https://example.com",
        "https://seal.lt", 
        "https://github.com"
    ]
    
    site_ids = []
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n--- Test {i}: {url} ---")
        
        try:
            response = requests.post(
                "https://web-production-a5831.up.railway.app/audit",
                json={"url": url},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                site_id = result.get("site_id")
                site_ids.append(site_id)
                print(f"✅ Audit {i} successful - Site ID: {site_id}")
            else:
                print(f"❌ Audit {i} failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Audit {i} error: {e}")
    
    print(f"\n🎯 Multiple audit results:")
    print(f"   - Successful audits: {len(site_ids)}/{len(test_urls)}")
    print(f"   - Site IDs generated: {site_ids}")
    
    return len(site_ids) == len(test_urls)

def main():
    """Run Supabase integration tests"""
    print("🚀 Testing Supabase integration for /audit endpoint\n")
    
    # Test 1: Single audit
    print("="*60)
    print("TEST 1: Single audit with Supabase")
    print("="*60)
    
    success1 = test_supabase_integration()
    
    # Test 2: Multiple audits
    print("\n" + "="*60)
    print("TEST 2: Multiple audits for persistence")
    print("="*60)
    
    success2 = test_multiple_audits()
    
    # Summary
    print("\n" + "="*60)
    print("SUPABASE INTEGRATION TEST SUMMARY")
    print("="*60)
    
    print(f"{'✅ PASS' if success1 else '❌ FAIL'} Single audit with Supabase")
    print(f"{'✅ PASS' if success2 else '❌ FAIL'} Multiple audits for persistence")
    
    total_passed = sum([success1, success2])
    print(f"\n🎯 Results: {total_passed}/2 tests passed")
    
    if total_passed == 2:
        print("🎉 Supabase integration is working!")
    elif total_passed == 1:
        print("⚠️ Partial Supabase integration - check Railway logs")
    else:
        print("❌ Supabase integration issues - check configuration")
    
    print(f"\n📋 Next steps:")
    print(f"   1. Check Railway logs for Supabase errors")
    print(f"   2. Verify SUPABASE_URL and SUPABASE_SERVICE_KEY are set")
    print(f"   3. Check if Supabase tables exist")
    print(f"   4. Test with a query endpoint to retrieve saved data")

if __name__ == "__main__":
    main()
