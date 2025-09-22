# wordpress_apply.py — WordPress auto-apply functionality
import os
import requests
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class WordPressConfig:
    site_url: str
    username: str
    password: str  # or app password
    api_endpoint: str

class WordPressApplier:
    def __init__(self, config: WordPressConfig):
        self.config = config
        self.session = requests.Session()
        self.session.auth = (config.username, config.password)
    
    async def apply_optimizations(self, optimizations: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply optimizations to WordPress site
        """
        results = {
            "success": True,
            "applied": [],
            "failed": [],
            "errors": []
        }
        
        try:
            # Get pages from WordPress
            pages = await self._get_wp_pages()
            
            # Apply optimizations to each page
            for page_opt in optimizations.get("pages_optimized", []):
                page_url = page_opt.get("url", "")
                wp_page = self._find_matching_wp_page(pages, page_url)
                
                if wp_page:
                    success = await self._apply_page_optimization(wp_page, page_opt)
                    if success:
                        results["applied"].append(page_url)
                    else:
                        results["failed"].append(page_url)
                else:
                    results["errors"].append(f"WordPress page not found for {page_url}")
            
            # Apply global optimizations (site-wide settings)
            global_opt = optimizations.get("global", {})
            if global_opt:
                await self._apply_global_optimizations(global_opt)
                results["applied"].append("Global optimizations")
                
        except Exception as e:
            results["success"] = False
            results["errors"].append(str(e))
        
        return results
    
    async def _get_wp_pages(self) -> List[Dict[str, Any]]:
        """Get all pages from WordPress"""
        try:
            response = self.session.get(f"{self.config.api_endpoint}/wp-json/wp/v2/pages")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching WordPress pages: {e}")
            return []
    
    def _find_matching_wp_page(self, wp_pages: List[Dict[str, Any]], target_url: str) -> Optional[Dict[str, Any]]:
        """Find WordPress page matching the target URL"""
        for page in wp_pages:
            if page.get("link") == target_url or target_url.endswith(page.get("slug", "")):
                return page
        return None
    
    async def _apply_page_optimization(self, wp_page: Dict[str, Any], optimization: Dict[str, Any]) -> bool:
        """Apply optimization to a specific WordPress page"""
        try:
            page_id = wp_page["id"]
            update_data = {}
            
            # Update title
            if optimization.get("new_title"):
                update_data["title"] = {"rendered": optimization["new_title"]}
            
            # Update meta description (requires SEO plugin or custom fields)
            if optimization.get("new_meta"):
                update_data["meta"] = {
                    "description": optimization["new_meta"]
                }
            
            # Update content (H1 and FAQ)
            if optimization.get("new_h1") or optimization.get("faq"):
                content = wp_page.get("content", {}).get("rendered", "")
                
                # Add H1 if provided
                if optimization.get("new_h1"):
                    content = f"<h1>{optimization['new_h1']}</h1>\n{content}"
                
                # Add FAQ section if provided
                if optimization.get("faq"):
                    faq_html = self._generate_faq_html(optimization["faq"])
                    content += f"\n{faq_html}"
                
                update_data["content"] = content
            
            # Update the page
            if update_data:
                response = self.session.post(
                    f"{self.config.api_endpoint}/wp-json/wp/v2/pages/{page_id}",
                    json=update_data
                )
                response.raise_for_status()
                return True
            
            return False
            
        except Exception as e:
            print(f"Error applying page optimization: {e}")
            return False
    
    def _generate_faq_html(self, faq_items: List[Dict[str, str]]) -> str:
        """Generate FAQ HTML from FAQ items"""
        html = '<div class="faq-section"><h2>Frequently Asked Questions</h2>'
        for item in faq_items:
            html += f'<div class="faq-item"><h3>{item["q"]}</h3><p>{item["a"]}</p></div>'
        html += '</div>'
        return html
    
    async def _apply_global_optimizations(self, global_opt: Dict[str, Any]) -> bool:
        """Apply site-wide optimizations"""
        try:
            # This would typically involve updating theme options, SEO plugin settings, etc.
            # For now, we'll just log what would be applied
            print(f"Global optimizations to apply: {global_opt}")
            return True
        except Exception as e:
            print(f"Error applying global optimizations: {e}")
            return False

# WordPress apply endpoint
async def apply_to_wordpress(
    wp_config: WordPressConfig, 
    optimizations: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Apply optimizations to WordPress site
    """
    applier = WordPressApplier(wp_config)
    return await applier.apply_optimizations(optimizations)
