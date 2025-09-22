"""
LLM Ruleset Database - Industry-specific optimization rules
"""

# Industry-specific optimization rules
INDUSTRY_RULES = {
    "ecommerce": {
        "title_template": "Best {product} - {brand} | {location}",
        "meta_template": "Shop {product} at {brand}. {benefit}. Free shipping on orders over $50.",
        "h1_template": "Premium {product} Collection",
        "schema_type": "Product",
        "faq_topics": ["shipping", "returns", "warranty", "sizing"],
        "keywords_focus": ["buy", "shop", "price", "reviews", "quality"]
    },
    
    "saas": {
        "title_template": "{product} - {benefit} | {brand}",
        "meta_template": "{product} helps {target_audience} {benefit}. Start free trial today.",
        "h1_template": "Transform Your {industry} with {product}",
        "schema_type": "SoftwareApplication",
        "faq_topics": ["pricing", "features", "integration", "support", "security"],
        "keywords_focus": ["software", "solution", "automation", "efficiency", "productivity"]
    },
    
    "local_business": {
        "title_template": "{service} in {location} | {brand}",
        "meta_template": "Professional {service} in {location}. {benefit}. Call {phone} for free quote.",
        "h1_template": "{service} Services in {location}",
        "schema_type": "LocalBusiness",
        "faq_topics": ["service_area", "pricing", "availability", "experience", "contact"],
        "keywords_focus": ["near me", "local", "professional", "quality", "reliable"]
    },
    
    "blog": {
        "title_template": "{topic} Guide: {benefit} | {brand}",
        "meta_template": "Learn {topic} with our comprehensive guide. {benefit}. Expert insights included.",
        "h1_template": "Complete {topic} Guide",
        "schema_type": "Article",
        "faq_topics": ["basics", "advanced", "tools", "tips", "resources"],
        "keywords_focus": ["guide", "tutorial", "learn", "tips", "how-to"]
    },
    
    "corporate": {
        "title_template": "{company} - {industry} Solutions",
        "meta_template": "{company} provides {services} for {target_market}. {benefit}. Contact us today.",
        "h1_template": "Leading {industry} Solutions",
        "schema_type": "Organization",
        "faq_topics": ["company", "services", "clients", "contact", "careers"],
        "keywords_focus": ["solutions", "services", "expertise", "experience", "results"]
    }
}

# Content quality rules
CONTENT_RULES = {
    "title_length": {"min": 30, "max": 60},
    "meta_length": {"min": 120, "max": 160},
    "h1_length": {"min": 20, "max": 80},
    "word_count_min": 200,
    "images_alt_required": True,
    "internal_links_min": 3,
    "external_links_max": 5
}

# SEO best practices
SEO_RULES = {
    "title_requirements": [
        "Include primary keyword",
        "Include brand name",
        "Include location if local business",
        "Use action words",
        "Avoid keyword stuffing"
    ],
    "meta_requirements": [
        "Include primary keyword",
        "Include call-to-action",
        "Include benefit or value proposition",
        "Include location if local",
        "Create urgency or interest"
    ],
    "h1_requirements": [
        "Include primary keyword",
        "Be descriptive and clear",
        "Match user intent",
        "Be unique per page",
        "Support the title tag"
    ]
}

# Industry detection keywords
INDUSTRY_DETECTION = {
    "ecommerce": ["shop", "buy", "cart", "checkout", "product", "price", "sale"],
    "saas": ["software", "app", "platform", "dashboard", "api", "integration", "trial"],
    "local_business": ["near me", "local", "service", "contact", "address", "phone"],
    "blog": ["blog", "article", "post", "guide", "tutorial", "tips", "learn"],
    "corporate": ["company", "about", "services", "solutions", "team", "careers"]
}

def detect_industry(content_data):
    """Detect industry based on content analysis"""
    all_text = ""
    for page in content_data.get('pages', []):
        all_text += f" {page.get('title', '')} {page.get('meta', '')} "
        for h1 in page.get('h1', []):
            all_text += f" {h1} "
    
    all_text = all_text.lower()
    
    industry_scores = {}
    for industry, keywords in INDUSTRY_DETECTION.items():
        score = sum(1 for keyword in keywords if keyword in all_text)
        industry_scores[industry] = score
    
    # Return industry with highest score, or 'corporate' as default
    return max(industry_scores, key=industry_scores.get) if max(industry_scores.values()) > 0 else 'corporate'

def get_optimization_rules(industry, content_data):
    """Get specific optimization rules for detected industry"""
    base_rules = INDUSTRY_RULES.get(industry, INDUSTRY_RULES['corporate'])
    
    # Add content-specific rules
    rules = {
        **base_rules,
        "content_rules": CONTENT_RULES,
        "seo_rules": SEO_RULES,
        "detected_industry": industry,
        "site_analysis": {
            "total_pages": len(content_data.get('pages', [])),
            "languages": content_data.get('languages', []),
            "has_contact_info": any('contact' in page.get('url', '').lower() for page in content_data.get('pages', [])),
            "has_products": any('product' in page.get('url', '').lower() for page in content_data.get('pages', []))
        }
    }
    
    return rules
