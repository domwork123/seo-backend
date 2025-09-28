#!/usr/bin/env python3
"""
Simple test for the blog generator to isolate the issue
"""

import json
from simple_blog_generator import SimpleBlogGenerator

def test_simple_generation():
    """Test the blog generator with minimal parameters"""
    try:
        print("🧪 Testing SimpleBlogGenerator...")
        
        # Create generator
        generator = SimpleBlogGenerator()
        print("✅ Generator created successfully")
        
        # Test with minimal parameters
        result = generator.generate_blog_post(
            brand_name="Mobilus Detailing",
            target_keyword="kaip plauti automobili",
            language="lt",
            mode="AEO"
        )
        
        print("✅ Blog post generated successfully")
        print(f"📊 Result keys: {list(result.keys())}")
        print(f"📝 Title: {result.get('title', 'No title')}")
        print(f"📄 Word count: {result.get('word_count', 0)}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_simple_generation()
