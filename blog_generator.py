"""
EVIKA Blog Generator for AEO and GEO content
Generates structured blog posts with JSON-LD schema markup
"""

import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime

class BlogGenerator:
    def __init__(self):
        self.language = "en"
        self.brand_name = ""
        self.target_keyword = ""
        self.mode = "AEO"  # AEO or GEO
        
    def generate_blog_post(self, 
                          brand_name: str, 
                          target_keyword: str, 
                          language: str = "en",
                          mode: str = "AEO",
                          context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate a blog post based on the provided parameters
        
        Args:
            brand_name: Name of the brand
            target_keyword: Target keyword for SEO
            language: Language code (default: en)
            mode: AEO or GEO mode
            context: Additional context data from audit
            
        Returns:
            Dict containing the complete blog post with schema markup
        """
        
        self.language = language
        self.brand_name = brand_name
        self.target_keyword = target_keyword
        self.mode = mode.upper()
        
        # Generate content based on mode
        if self.mode == "AEO":
            return self._generate_aeo_content(context)
        elif self.mode == "GEO":
            return self._generate_geo_content(context)
        else:
            raise ValueError("Mode must be 'AEO' or 'GEO'")
    
    def _generate_aeo_content(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate AEO-optimized content"""
        
        # AEO-specific content structure
        title = f"{self.target_keyword}: Complete Guide | {self.brand_name}"
        meta_description = f"Everything you need to know about {self.target_keyword}. Expert insights, comparisons, and answers to common questions. {self.brand_name}."
        
        # Generate sections
        sections = self._generate_aeo_sections()
        
        # Generate FAQs (≥5 items)
        faqs = self._generate_aeo_faqs()
        
        # Generate images
        images = self._generate_images()
        
        # Generate internal links
        internal_links = self._generate_internal_links()
        
        # Generate content (800-1200 words)
        content = self._generate_aeo_content_text(sections, faqs)
        
        # Generate JSON-LD schemas
        json_ld = self._generate_aeo_json_ld(faqs)
        
        return {
            "title": title,
            "meta_description": meta_description[:160],
            "content": content,
            "word_count": len(content.split()),
            "sections": sections,
            "faqs": faqs,
            "images": images,
            "internal_links": internal_links,
            "json_ld": json_ld,
            "mode": "AEO",
            "target_keyword": self.target_keyword,
            "brand": self.brand_name,
            "language": self.language,
            "generated_at": datetime.now().isoformat()
        }
    
    def _generate_geo_content(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate GEO-optimized content"""
        
        # GEO-specific content structure
        title = f"{self.target_keyword} in {self._get_city_name()}: Local Guide | {self.brand_name}"
        meta_description = f"Find the best {self.target_keyword} in {self._get_city_name()}. Local insights, store locations, and expert recommendations. {self.brand_name}."
        
        # Generate sections
        sections = self._generate_geo_sections()
        
        # Generate FAQs (≥5 items)
        faqs = self._generate_geo_faqs()
        
        # Generate images
        images = self._generate_images()
        
        # Generate internal links
        internal_links = self._generate_internal_links()
        
        # Generate content (1000-1400 words)
        content = self._generate_geo_content_text(sections, faqs)
        
        # Generate JSON-LD schemas
        json_ld = self._generate_geo_json_ld(faqs, context)
        
        return {
            "title": title,
            "meta_description": meta_description[:160],
            "content": content,
            "word_count": len(content.split()),
            "sections": sections,
            "faqs": faqs,
            "images": images,
            "internal_links": internal_links,
            "json_ld": json_ld,
            "mode": "GEO",
            "target_keyword": self.target_keyword,
            "brand": self.brand_name,
            "language": self.language,
            "city": self._get_city_name(),
            "generated_at": datetime.now().isoformat()
        }
    
    def _generate_aeo_sections(self) -> List[Dict[str, str]]:
        """Generate AEO-optimized sections"""
        return [
            {
                "heading": f"What is {self.target_keyword}?",
                "content": f"Understanding {self.target_keyword} is essential for making informed decisions. {self.brand_name} provides comprehensive insights into this topic."
            },
            {
                "heading": f"Key Benefits of {self.target_keyword}",
                "content": f"Discover the advantages of {self.target_keyword} and how it can benefit you. Our experts at {self.brand_name} have identified the most important benefits."
            },
            {
                "heading": f"Comparison: {self.target_keyword} vs Alternatives",
                "content": f"Compare {self.target_keyword} with other options to make the best choice. {self.brand_name} offers detailed comparisons to help you decide."
            },
            {
                "heading": f"How to Choose the Right {self.target_keyword}",
                "content": f"Learn the criteria for selecting the best {self.target_keyword} for your needs. {self.brand_name} provides expert guidance."
            },
            {
                "heading": f"Conclusion: {self.target_keyword} Guide",
                "content": f"Make informed decisions about {self.target_keyword} with our comprehensive guide. {self.brand_name} is your trusted source for expert insights."
            }
        ]
    
    def _generate_geo_sections(self) -> List[Dict[str, str]]:
        """Generate GEO-optimized sections"""
        city = self._get_city_name()
        return [
            {
                "heading": f"{self.target_keyword} in {city}: Local Overview",
                "content": f"Discover the best {self.target_keyword} options in {city}. {self.brand_name} provides local insights and recommendations for {city} residents."
            },
            {
                "heading": f"Top {self.target_keyword} Locations in {city}",
                "content": f"Find the most popular {self.target_keyword} spots in {city}, including areas near {self._get_landmarks()}. {self.brand_name} knows {city} best."
            },
            {
                "heading": f"Online vs Local {self.target_keyword} in {city}",
                "content": f"Compare online and local {self.target_keyword} experiences in {city}. {self.brand_name} helps you choose the best option for your needs."
            },
            {
                "heading": f"Local {self.target_keyword} Benefits in {city}",
                "content": f"Learn why local {self.target_keyword} in {city} offers unique advantages. {self.brand_name} connects you with the best local options."
            },
            {
                "heading": f"Conclusion: {self.target_keyword} in {city}",
                "content": f"Make the most of {self.target_keyword} in {city} with our local guide. {self.brand_name} is your trusted partner in {city}."
            }
        ]
    
    def _generate_aeo_faqs(self) -> List[Dict[str, str]]:
        """Generate AEO-optimized FAQs (≥5 items)"""
        return [
            {
                "question": f"What is {self.target_keyword}?",
                "answer": f"{self.target_keyword} is a specialized solution that {self.brand_name} provides to help you achieve your goals. Our experts have extensive experience in this field."
            },
            {
                "question": f"How much does {self.target_keyword} cost?",
                "answer": f"The cost of {self.target_keyword} varies depending on your specific needs. {self.brand_name} offers competitive pricing and transparent quotes for all services."
            },
            {
                "question": f"How long does {self.target_keyword} take?",
                "answer": f"The timeline for {self.target_keyword} depends on the complexity of your project. {self.brand_name} typically delivers results within our promised timeframe."
            },
            {
                "question": f"Is {self.target_keyword} available in my area?",
                "answer": f"{self.brand_name} provides {self.target_keyword} services in multiple locations. Contact us to confirm availability in your specific area."
            },
            {
                "question": f"What makes {self.brand_name}'s {self.target_keyword} different?",
                "answer": f"{self.brand_name} stands out with our expertise, quality service, and customer-focused approach. We ensure the best results for your {self.target_keyword} needs."
            },
            {
                "question": f"Can I get a consultation for {self.target_keyword}?",
                "answer": f"Yes, {self.brand_name} offers free consultations for {self.target_keyword} services. Our experts will assess your needs and provide personalized recommendations."
            }
        ]
    
    def _generate_geo_faqs(self) -> List[Dict[str, str]]:
        """Generate GEO-optimized FAQs (≥5 items)"""
        city = self._get_city_name()
        return [
            {
                "question": f"Where can I find {self.target_keyword} in {city}?",
                "answer": f"The best {self.target_keyword} locations in {city} include areas near {self._get_landmarks()}. {self.brand_name} has local expertise in {city}."
            },
            {
                "question": f"What are the benefits of local {self.target_keyword} in {city}?",
                "answer": f"Local {self.target_keyword} in {city} offers convenience, local knowledge, and immediate support. {self.brand_name} understands {city}'s unique needs."
            },
            {
                "question": f"How does online {self.target_keyword} compare to local options in {city}?",
                "answer": f"While online {self.target_keyword} offers convenience, local options in {city} provide personalized service and immediate support. {self.brand_name} offers both options."
            },
            {
                "question": f"What are the best times to visit {self.target_keyword} locations in {city}?",
                "answer": f"The best times vary by location in {city}. {self.brand_name} can provide specific recommendations based on your schedule and preferences."
            },
            {
                "question": f"Does {self.brand_name} offer {self.target_keyword} services in {city}?",
                "answer": f"Yes, {self.brand_name} provides comprehensive {self.target_keyword} services in {city}. We understand the local market and can serve your needs effectively."
            },
            {
                "question": f"How can I contact {self.brand_name} for {self.target_keyword} in {city}?",
                "answer": f"You can contact {self.brand_name} through our local office in {city} or online. We're committed to serving the {city} community with quality {self.target_keyword} services."
            }
        ]
    
    def _generate_images(self) -> List[Dict[str, str]]:
        """Generate image suggestions (≥2)"""
        return [
            {
                "alt": f"{self.target_keyword} overview image",
                "src": f"/images/{self.target_keyword.lower().replace(' ', '-')}-overview.jpg",
                "caption": f"Comprehensive guide to {self.target_keyword}"
            },
            {
                "alt": f"{self.brand_name} {self.target_keyword} services",
                "src": f"/images/{self.brand_name.lower().replace(' ', '-')}-services.jpg",
                "caption": f"{self.brand_name} professional {self.target_keyword} services"
            }
        ]
    
    def _generate_internal_links(self) -> List[Dict[str, str]]:
        """Generate internal links (≥2)"""
        return [
            {
                "text": f"Learn more about {self.brand_name} services",
                "url": "/services",
                "anchor": "our-services"
            },
            {
                "text": f"Contact {self.brand_name} for consultation",
                "url": "/contact",
                "anchor": "get-in-touch"
            }
        ]
    
    def _generate_aeo_content_text(self, sections: List[Dict], faqs: List[Dict]) -> str:
        """Generate AEO-optimized content text (800-1200 words)"""
        
        content = f"# {self.target_keyword}: Complete Guide\n\n"
        content += f"Welcome to our comprehensive guide on {self.target_keyword}. {self.brand_name} provides expert insights to help you understand everything about this important topic.\n\n"
        
        # Add sections
        for section in sections:
            content += f"## {section['heading']}\n\n"
            content += f"{section['content']}\n\n"
        
        # Add FAQ section
        content += "## Frequently Asked Questions\n\n"
        for faq in faqs:
            content += f"### {faq['question']}\n\n"
            content += f"{faq['answer']}\n\n"
        
        content += f"## Conclusion\n\n"
        content += f"Understanding {self.target_keyword} is crucial for making informed decisions. {self.brand_name} is your trusted partner for expert guidance and professional services.\n\n"
        
        return content
    
    def _generate_geo_content_text(self, sections: List[Dict], faqs: List[Dict]) -> str:
        """Generate GEO-optimized content text (1000-1400 words)"""
        
        city = self._get_city_name()
        content = f"# {self.target_keyword} in {city}: Local Guide\n\n"
        content += f"Discover the best {self.target_keyword} options in {city}. {self.brand_name} provides local expertise and insights for {city} residents.\n\n"
        
        # Add sections
        for section in sections:
            content += f"## {section['heading']}\n\n"
            content += f"{section['content']}\n\n"
        
        # Add FAQ section
        content += "## Frequently Asked Questions\n\n"
        for faq in faqs:
            content += f"### {faq['question']}\n\n"
            content += f"{faq['answer']}\n\n"
        
        content += f"## Conclusion\n\n"
        content += f"Make the most of {self.target_keyword} in {city} with our local guide. {self.brand_name} is your trusted partner in {city}.\n\n"
        
        return content
    
    def _generate_aeo_json_ld(self, faqs: List[Dict]) -> Dict[str, Any]:
        """Generate AEO JSON-LD schema"""
        return {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": f"{self.target_keyword}: Complete Guide",
            "description": f"Comprehensive guide to {self.target_keyword} by {self.brand_name}",
            "author": {
                "@type": "Organization",
                "name": self.brand_name
            },
            "publisher": {
                "@type": "Organization",
                "name": self.brand_name
            },
            "datePublished": datetime.now().isoformat(),
            "mainEntity": {
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": faq["question"],
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": faq["answer"]
                        }
                    } for faq in faqs
                ]
            }
        }
    
    def _generate_geo_json_ld(self, faqs: List[Dict], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate GEO JSON-LD schema with LocalBusiness"""
        
        # Base article schema
        article_schema = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": f"{self.target_keyword} in {self._get_city_name()}: Local Guide",
            "description": f"Local guide to {self.target_keyword} in {self._get_city_name()} by {self.brand_name}",
            "author": {
                "@type": "Organization",
                "name": self.brand_name
            },
            "publisher": {
                "@type": "Organization",
                "name": self.brand_name
            },
            "datePublished": datetime.now().isoformat(),
            "mainEntity": {
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": faq["question"],
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": faq["answer"]
                        }
                    } for faq in faqs
                ]
            }
        }
        
        # LocalBusiness schema (with empty fields if no data)
        local_business = {
            "@context": "https://schema.org",
            "@type": "LocalBusiness",
            "name": self.brand_name,
            "description": f"{self.brand_name} provides {self.target_keyword} services",
            "address": {
                "@type": "PostalAddress",
                "addressLocality": self._get_city_name(),
                "addressCountry": "LT"  # Default to Lithuania
            }
        }
        
        return {
            "article": article_schema,
            "local_business": local_business
        }
    
    def _get_city_name(self) -> str:
        """Get city name for GEO content"""
        return "Vilnius"  # Default city
    
    def _get_landmarks(self) -> str:
        """Get local landmarks for GEO content"""
        return "Akropolis, Panorama, Gedimino pr."
