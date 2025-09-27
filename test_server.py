#!/usr/bin/env python3
"""
Simple server test for the /audit endpoint
Tests the FastAPI endpoint without dependency issues
"""

import json
import requests
import time
import subprocess
import signal
import os
import sys

def start_server():
    """Start the FastAPI server in background"""
    print("🚀 Starting FastAPI server...")
    
    # Set environment variables for development
    env = os.environ.copy()
    env['DEVELOPMENT_MODE'] = 'true'
    env['SCRAPINGBEE_API_KEY'] = 'test-key'
    env['SUPABASE_URL'] = 'https://test.supabase.co'
    env['SUPABASE_SERVICE_KEY'] = 'test-key'
    
    # Start server
    process = subprocess.Popen(
        ['python3', '-m', 'uvicorn', 'main:app', '--host', '0.0.0.0', '--port', '8000'],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to start
    time.sleep(3)
    
    return process

def test_audit_endpoint():
    """Test the /audit endpoint"""
    print("🧪 Testing /audit endpoint...")
    
    try:
        # Test data
        test_data = {
            "url": "https://example.com"
        }
        
        # Make request
        response = requests.post(
            "http://localhost:8000/audit",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ /audit endpoint works!")
            print(f"   - Status: {response.status_code}")
            print(f"   - Site ID: {result.get('site_id', 'N/A')}")
            print(f"   - Brand: {result.get('brand_name', 'N/A')}")
            print(f"   - Pages: {result.get('pages_crawled', 0)}")
            print(f"   - Success: {result.get('success', False)}")
            return True
        else:
            print(f"❌ /audit endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ /audit endpoint error: {e}")
        return False

def test_health_endpoint():
    """Test the /health endpoint"""
    print("🧪 Testing /health endpoint...")
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ /health endpoint works!")
            print(f"   - Status: {result.get('status', 'N/A')}")
            return True
        else:
            print(f"❌ /health endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ /health endpoint error: {e}")
        return False

def main():
    """Run server tests"""
    print("🚀 Testing EVIKA FastAPI server\n")
    
    server_process = None
    
    try:
        # Start server
        server_process = start_server()
        
        # Wait a bit more for server to be ready
        time.sleep(2)
        
        # Test endpoints
        tests = [
            ("Health Endpoint", test_health_endpoint),
            ("Audit Endpoint", test_audit_endpoint)
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
        print("SERVER TEST SUMMARY")
        print('='*50)
        
        passed = 0
        for test_name, success in results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {test_name}")
            if success:
                passed += 1
        
        print(f"\n🎯 Results: {passed}/{len(results)} tests passed")
        
        if passed == len(results):
            print("🎉 All server tests passed! The /audit endpoint is working!")
        else:
            print("⚠️ Some server tests failed. Check the errors above.")
            
    except Exception as e:
        print(f"❌ Server test error: {e}")
        
    finally:
        # Clean up server
        if server_process:
            print("\n🛑 Stopping server...")
            server_process.terminate()
            server_process.wait()
            print("✅ Server stopped")

if __name__ == "__main__":
    main()
