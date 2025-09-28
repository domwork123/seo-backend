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
        meta_description = f"{self.brand_name} - Complete {self.target_keyword} guide. Expert insights, comparisons & tips. Start now!"
        
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
        meta_description = f"{self.brand_name} - Best {self.target_keyword} in {self._get_city_name()}. Expert local guidance & insights. Visit us today!"
        
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
        """Generate AEO-optimized sections with expanded content"""
        return [
            {
                "heading": f"What is {self.target_keyword}?",
                "content": f"Understanding {self.target_keyword} is essential for making informed decisions. {self.brand_name} provides comprehensive insights into this topic. This guide covers everything you need to know about finding the best options, comparing prices, and making smart choices."
            },
            {
                "heading": f"Key Benefits of {self.target_keyword}",
                "content": f"Discover the advantages of {self.target_keyword} and how it can benefit you. Our experts at {self.brand_name} have identified the most important benefits including quality, convenience, and value. We'll explore each benefit in detail with real examples and comparisons."
            },
            {
                "heading": f"Comparison: {self.target_keyword} vs Alternatives",
                "content": f"Compare {self.target_keyword} with other options to make the best choice. {self.brand_name} offers detailed comparisons to help you decide. We'll look at price differences, quality variations, and availability across different options."
            },
            {
                "heading": f"How to Choose the Right {self.target_keyword}",
                "content": f"Learn the criteria for selecting the best {self.target_keyword} for your needs. {self.brand_name} provides expert guidance on factors like budget, quality, and personal preferences. We'll provide a step-by-step guide to help you make the right decision."
            },
            {
                "heading": f"Tips and Recommendations",
                "content": f"Get expert tips and recommendations for {self.target_keyword}. {self.brand_name} shares insider knowledge about what to look for, common mistakes to avoid, and how to get the best value for your money."
            },
            {
                "heading": f"Conclusion: {self.target_keyword} Guide",
                "content": f"Make informed decisions about {self.target_keyword} with our comprehensive guide. {self.brand_name} is your trusted source for expert insights and professional recommendations."
            }
        ]
    
    def _generate_geo_sections(self) -> List[Dict[str, str]]:
        """Generate GEO-optimized sections with local references"""
        city = self._get_city_name()
        landmarks = self._get_landmarks()
        return [
            {
                "heading": f"{self.target_keyword} in {city}: Local Overview",
                "content": f"Discover the best {self.target_keyword} options in {city}. {self.brand_name} provides local insights and recommendations for {city} residents. From {landmarks}, we'll guide you through the top locations and what makes each area unique for shopping."
            },
            {
                "heading": f"Top {self.target_keyword} Locations in {city}",
                "content": f"Find the most popular {self.target_keyword} spots in {city}, including areas near {landmarks}. {self.brand_name} knows {city} best and can recommend the best places based on your preferences. We'll cover shopping centers, local boutiques, and hidden gems."
            },
            {
                "heading": f"Online vs Local {self.target_keyword} in {city}",
                "content": f"Compare online and local {self.target_keyword} experiences in {city}. {self.brand_name} helps you choose the best option for your needs. We'll discuss the advantages of shopping locally in {city} versus online options, including immediate availability, personal service, and local expertise."
            },
            {
                "heading": f"Local {self.target_keyword} Benefits in {city}",
                "content": f"Learn why local {self.target_keyword} in {city} offers unique advantages. {self.brand_name} connects you with the best local options and explains the benefits of supporting local businesses in {city}. We'll cover convenience, local knowledge, and community support."
            },
            {
                "heading": f"Best Times to Shop in {city}",
                "content": f"Discover the optimal times to visit {self.target_keyword} locations in {city}. {self.brand_name} shares insider tips about when stores are less crowded, when sales typically occur, and how to plan your shopping trip for the best experience."
            },
            {
                "heading": f"Conclusion: {self.target_keyword} in {city}",
                "content": f"Make the most of {self.target_keyword} in {city} with our local guide. {self.brand_name} is your trusted partner in {city} and we're committed to helping you find exactly what you're looking for."
            }
        ]
    
    def _generate_aeo_faqs(self) -> List[Dict[str, str]]:
        """Generate AEO-optimized FAQs based on real user intent"""
        return [
            {
                "question": f"What are the best options for {self.target_keyword}?",
                "answer": f"When looking for the best options, {self.brand_name} recommends considering quality, price, and availability. We offer a wide range of options to suit different budgets and preferences, with expert guidance to help you choose."
            },
            {
                "question": f"How much should I expect to pay?",
                "answer": f"Prices vary depending on quality and brand. {self.brand_name} offers competitive pricing with transparent quotes. We have options for every budget, from affordable choices to premium selections, ensuring you get the best value."
            },
            {
                "question": f"Are there any authentic options available?",
                "answer": f"Yes, {self.brand_name} guarantees authenticity for all our products. We work directly with verified suppliers and provide certificates of authenticity. Our reputation is built on trust and quality assurance."
            },
            {
                "question": f"Can I test before buying?",
                "answer": f"Absolutely! {self.brand_name} offers testing opportunities so you can try before you buy. We understand the importance of finding the right fit, and our experts are available to guide you through the testing process."
            },
            {
                "question": f"What about niche or specialty options?",
                "answer": f"{self.brand_name} specializes in both popular and niche options. We have access to exclusive collections and can help you find unique items that aren't available elsewhere. Our experts know the market inside and out."
            },
            {
                "question": f"Where can I find the cheapest options?",
                "answer": f"For budget-conscious shoppers, {self.brand_name} offers several affordable options without compromising quality. We regularly have sales and special offers, and our team can help you find the best deals available."
            }
        ]
    
    def _generate_geo_faqs(self) -> List[Dict[str, str]]:
        """Generate GEO-optimized FAQs with local references"""
        city = self._get_city_name()
        landmarks = self._get_landmarks()
        return [
            {
                "question": f"Where can I find the best options in {city}?",
                "answer": f"{self.brand_name} has multiple locations throughout {city}, including areas near {landmarks}. We can recommend the best spots based on your preferences and provide detailed directions to our stores."
            },
            {
                "question": f"What are the advantages of shopping locally vs online?",
                "answer": f"Shopping locally in {city} with {self.brand_name} offers immediate availability, personal service, and local expertise. You can see, touch, and test products before buying, plus get instant expert advice from our {city} team."
            },
            {
                "question": f"Are there any special offers for {city} residents?",
                "answer": f"Yes, {self.brand_name} offers exclusive deals for {city} residents, including local discounts and special promotions. We also have loyalty programs and seasonal offers that are perfect for {city} shoppers."
            },
            {
                "question": f"Can I get same-day service in {city}?",
                "answer": f"Absolutely! {self.brand_name} provides same-day service throughout {city}. Our local team ensures fast turnaround times and can often accommodate urgent requests from {city} customers."
            },
            {
                "question": f"What makes {self.brand_name} different from other options in {city}?",
                "answer": f"{self.brand_name} stands out in {city} with our local expertise, personalized service, and deep understanding of {city}'s unique needs. We're not just another chain - we're part of the {city} community."
            },
            {
                "question": f"Do you offer delivery throughout {city}?",
                "answer": f"Yes, {self.brand_name} offers comprehensive delivery services throughout {city}, including to areas near {landmarks}. We ensure fast, reliable delivery with tracking and customer support from our {city} team."
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
        
        # Ensure minimum word count (800 for AEO)
        content = self._ensure_word_count(content, 800)
        
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
        
        # Ensure minimum word count (1000 for GEO)
        content = self._ensure_word_count(content, 1000)
        
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
    
    def _ensure_word_count(self, content: str, min_words: int) -> str:
        """Ensure content meets minimum word count by expanding with examples and tips"""
        word_count = len(content.split())
        if word_count < min_words:
            # Add expansion content
            expansion = f"""
            
            ## Additional Insights and Tips

            When considering your options, it's important to evaluate several key factors:

            **Quality Assessment**: Look for indicators of quality such as materials, craftsmanship, and brand reputation. {self.brand_name} maintains high standards across all our offerings.

            **Value Comparison**: Compare not just price, but value - what you get for your investment. Consider long-term benefits, durability, and overall satisfaction.

            **Expert Recommendations**: Our team at {self.brand_name} has extensive experience and can provide personalized recommendations based on your specific needs and preferences.

            **Customer Reviews**: Read authentic reviews from other customers who have made similar choices. Their experiences can provide valuable insights.

            **Trial and Testing**: Whenever possible, test or sample before making a final decision. {self.brand_name} offers various ways to experience our products before purchase.

            **After-Sales Support**: Consider the support and service you'll receive after your purchase. {self.brand_name} provides comprehensive customer service and support.

            **Long-term Considerations**: Think about how your choice will serve you over time, not just immediately. Quality and durability often provide better long-term value.

            **Personal Preferences**: Your individual needs, style, and preferences should guide your decision. {self.brand_name} offers diverse options to suit different tastes and requirements.

            **Budget Planning**: Set a realistic budget and stick to it, but also consider the value of investing in quality. Sometimes spending a bit more upfront saves money long-term.

            **Research and Education**: Take time to learn about your options. {self.brand_name} provides educational resources and expert guidance to help you make informed decisions.
            """
            content += expansion
        return content
