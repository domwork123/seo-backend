#!/usr/bin/env python3
"""
Test ScrapingBee integration
"""
import asyncio
from scrapingbee_integration import fetch_with_scrapingbee, test_scrapingbee

async def main():
    print("🧪 Testing ScrapingBee Integration")
    print("=" * 50)
    
    # Test with example.com first
    print("Testing with example.com...")
    result = await fetch_with_scrapingbee("https://example.com")
    print(f"Result: {result['status']}")
    if result['status'] == 'success':
        print(f"Content length: {len(result['html'])}")
        print(f"First 200 chars: {result['html'][:200]}")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")
    
    print("\n" + "=" * 50)
    
    # Test with parfumada.lt
    print("Testing with parfumada.lt...")
    result = await fetch_with_scrapingbee("https://www.parfumada.lt/")
    print(f"Result: {result['status']}")
    if result['status'] == 'success':
        print(f"Content length: {len(result['html'])}")
        print(f"First 200 chars: {result['html'][:200]}")
        
        # Check if it's actually parfumada content
        if "parfumada" in result['html'].lower() or "perfume" in result['html'].lower():
            print("✅ SUCCESS: Got actual parfumada.lt content!")
        else:
            print("❌ WARNING: Content doesn't look like parfumada.lt")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    asyncio.run(main())
