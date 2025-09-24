#!/usr/bin/env python3
"""
Test script to debug the fallback system
"""
import asyncio
import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from aeo_geo_audit import fetch_with_fallback, is_blocked_html

async def test_fallback():
    """Test the fallback system with parfumada.lt"""
    print("Testing fallback system with parfumada.lt...")
    
    try:
        result = await fetch_with_fallback("https://parfumada.lt/")
        print(f"Result: {result}")
        
        if result['html']:
            print(f"HTML length: {len(result['html'])}")
            print(f"First 500 chars: {result['html'][:500]}")
            
            # Check if it's blocked
            is_blocked = is_blocked_html(result['html'])
            print(f"Is blocked: {is_blocked}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_fallback())
