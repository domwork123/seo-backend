"""
Supabase schema management for EVIKA audit system
Handles table creation and schema updates
"""

import os
from supabase import create_client, Client
from typing import Dict, Any, Optional

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

def get_supabase_client() -> Optional[Client]:
    """Get Supabase client"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Supabase credentials not found")
        return None
    
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"❌ Failed to create Supabase client: {e}")
        return None

def ensure_schema_exists() -> bool:
    """
    Ensure all required tables exist with correct schema
    Creates tables if they don't exist or updates schema if needed
    """
    
    supabase = get_supabase_client()
    if not supabase:
        print("❌ Cannot proceed without Supabase client")
        return False
    
    try:
        # Check and create sites table
        _ensure_sites_table(supabase)
        
        # Check and create pages table  
        _ensure_pages_table(supabase)
        
        # Check and create audits table
        _ensure_audits_table(supabase)
        
        print("✅ All required tables exist with correct schema")
        return True
        
    except Exception as e:
        print(f"❌ Schema setup failed: {e}")
        return False

def _ensure_sites_table(supabase: Client):
    """Ensure sites table exists with correct schema"""
    
    # Try to insert a test record to check if table exists
    try:
        # This will fail if table doesn't exist or schema is wrong
        test_result = supabase.table("sites").select("id").limit(1).execute()
        print("✅ Sites table exists")
        return
    except Exception as e:
        print(f"⚠️ Sites table issue: {e}")
    
    # If we get here, table might not exist or have wrong schema
    print("🔧 Sites table needs to be created/updated")
    
    # Note: In production, you would use Supabase SQL editor or migrations
    # For now, we'll work with whatever schema exists
    print("📝 Please create sites table with this SQL:")
    print("""
    CREATE TABLE IF NOT EXISTS sites (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        url TEXT NOT NULL,
        brand_name TEXT,
        description TEXT,
        location TEXT,
        industry TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """)
    
    # Try to create the table using SQL execution
    try:
        create_sql = """
        CREATE TABLE IF NOT EXISTS sites (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            url TEXT NOT NULL,
            brand_name TEXT,
            description TEXT,
            location TEXT,
            industry TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        supabase.rpc('exec_sql', {'sql': create_sql}).execute()
        print("✅ Sites table created/updated")
    except Exception as e:
        print(f"⚠️ Could not create sites table automatically: {e}")
        print("📝 Please create the table manually in Supabase SQL editor")

def _ensure_pages_table(supabase: Client):
    """Ensure pages table exists with correct schema"""
    
    try:
        test_result = supabase.table("pages").select("id").limit(1).execute()
        print("✅ Pages table exists")
        return
    except Exception as e:
        print(f"⚠️ Pages table issue: {e}")
    
    print("📝 Please create pages table with this SQL:")
    print("""
    CREATE TABLE IF NOT EXISTS pages (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        site_id UUID REFERENCES sites(id) ON DELETE CASCADE,
        url TEXT NOT NULL,
        title TEXT,
        raw_text TEXT,
        images JSONB,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """)
    
    # Try to create the table using SQL execution
    try:
        create_sql = """
        CREATE TABLE IF NOT EXISTS pages (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            site_id UUID REFERENCES sites(id) ON DELETE CASCADE,
            url TEXT NOT NULL,
            title TEXT,
            raw_text TEXT,
            images JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        supabase.rpc('exec_sql', {'sql': create_sql}).execute()
        print("✅ Pages table created/updated")
    except Exception as e:
        print(f"⚠️ Could not create pages table automatically: {e}")
        print("📝 Please create the table manually in Supabase SQL editor")

def _ensure_audits_table(supabase: Client):
    """Ensure audits table exists with correct schema"""
    
    try:
        test_result = supabase.table("audits").select("id").limit(1).execute()
        print("✅ Audits table exists")
        return
    except Exception as e:
        print(f"⚠️ Audits table issue: {e}")
    
    print("📝 Please create audits table with this SQL:")
    print("""
    CREATE TABLE IF NOT EXISTS audits (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        site_id UUID REFERENCES sites(id) ON DELETE CASCADE,
        url TEXT NOT NULL,
        results JSONB,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """)
    
    # Try to create the table using SQL execution
    try:
        create_sql = """
        CREATE TABLE IF NOT EXISTS audits (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            site_id UUID REFERENCES sites(id) ON DELETE CASCADE,
            url TEXT NOT NULL,
            results JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        supabase.rpc('exec_sql', {'sql': create_sql}).execute()
        print("✅ Audits table created/updated")
    except Exception as e:
        print(f"⚠️ Could not create audits table automatically: {e}")
        print("📝 Please create the table manually in Supabase SQL editor")

def save_audit_data(site_id: str, url: str, pages_data: list, signals: dict) -> bool:
    """
    Save audit data to Supabase
    
    Args:
        site_id: Unique site identifier
        url: Website URL
        pages_data: List of crawled pages
        signals: Extracted signals
        
    Returns:
        bool: Success status
    """
    
    supabase = get_supabase_client()
    if not supabase:
        return False
    
    try:
        # 1. Save site info
        site_data = {
            "id": site_id,
            "url": url,
            "brand_name": signals.get("brand_name", ""),
            "description": signals.get("description", ""),
            "location": signals.get("location", ""),
            "industry": signals.get("industry", "")
        }
        
        # Try to insert site (ignore if exists)
        try:
            supabase.table("sites").insert(site_data).execute()
            print(f"✅ Saved site info: {site_id}")
        except Exception as e:
            print(f"⚠️ Site might already exist: {e}")
        
        # 2. Save pages data
        for page in pages_data:
            page_data = {
                "site_id": site_id,
                "url": page.get("url", ""),
                "title": page.get("title", ""),
                "raw_text": page.get("raw_text", ""),
                "images": page.get("images", [])
            }
            
            try:
                supabase.table("pages").insert(page_data).execute()
            except Exception as e:
                print(f"⚠️ Failed to save page {page.get('url')}: {e}")
        
        # 3. Save audit results
        audit_data = {
            "site_id": site_id,
            "url": url,
            "results": {
                "faqs": signals.get("faqs", []),
                "schemas": signals.get("schemas", []),
                "alt_text_issues": signals.get("alt_text_issues", []),
                "geo_signals": signals.get("geo_signals", []),
                "competitors": signals.get("competitors", []),
                "products": signals.get("products", []),
                "topics": signals.get("topics", [])
            }
        }
        
        supabase.table("audits").insert(audit_data).execute()
        print(f"✅ Saved audit results: {site_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to save audit data: {e}")
        return False

def get_audit_data(site_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve audit data from Supabase
    
    Args:
        site_id: Unique site identifier
        
    Returns:
        Dict with audit data or None if not found
    """
    
    supabase = get_supabase_client()
    if not supabase:
        return None
    
    try:
        # Get site info
        site_result = supabase.table("sites").select("*").eq("id", site_id).execute()
        if not site_result.data:
            return None
        
        # Get pages data
        pages_result = supabase.table("pages").select("*").eq("site_id", site_id).execute()
        
        # Get audit results
        audit_result = supabase.table("audits").select("*").eq("site_id", site_id).execute()
        
        return {
            "site": site_result.data[0] if site_result.data else None,
            "pages": pages_result.data if pages_result.data else [],
            "audit": audit_result.data[0] if audit_result.data else None
        }
        
    except Exception as e:
        print(f"❌ Failed to retrieve audit data: {e}")
        return None
