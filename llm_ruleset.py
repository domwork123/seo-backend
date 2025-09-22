"""
Professional LLM Ruleset for Website Optimization
Based on comprehensive guidelines for multi-sector website coverage
"""

# Core optimization categories with detailed guidelines
OPTIMIZATION_CATEGORIES = {
    "SEO": {
        "focus": "Search Engine Optimization - improving visibility on search engines",
        "key_elements": [
            "Unique, descriptive title tags with relevant keywords",
            "Meta descriptions incorporating keywords for better CTR",
            "Proper heading structure (H1, H2, H3) with keyword hierarchy",
            "Content optimized around user intent, not just keywords",
            "E-E-A-T principles (Experience, Expertise, Authoritativeness, Trustworthiness)",
            "Technical SEO: robots.txt, XML sitemap, crawlability"
        ],
        "priority": "High",
        "standards": ["Google Search Essentials", "E-E-A-T Guidelines"]
    },
    
    "AEO": {
        "focus": "Answer Engine Optimization - voice assistants and featured snippets",
        "key_elements": [
            "Question-and-answer format content",
            "Structured data (Schema.org) implementation",
            "FAQPage, HowTo, Product schemas",
            "Concise, factual answers for common questions",
            "FAQ sections with proper markup",
            "Content that satisfies queries outright"
        ],
        "priority": "High",
        "standards": ["Schema.org", "Google Rich Results"]
    },
    
    "GEO": {
        "focus": "Geographic Optimization - location-based and international searches",
        "key_elements": [
            "Hreflang tags for multilingual sites",
            "LocalBusiness schema with NAP consistency",
            "Location-specific landing pages",
            "Google Business Profile optimization",
            "Geographic keywords in content",
            "Proper ISO language-country codes"
        ],
        "priority": "Medium",
        "standards": ["Google My Business", "Hreflang Best Practices"]
    },
    
    "Accessibility": {
        "focus": "WCAG 2.1 compliance for inclusive design",
        "key_elements": [
            "Descriptive alt text for all meaningful images",
            "Proper form labels and ARIA labels",
            "Logical heading order and semantic HTML",
            "Color contrast ratio of at least 4.5:1",
            "Keyboard navigation support",
            "Video captions and transcripts"
        ],
        "priority": "High",
        "standards": ["WCAG 2.1", "ADA Compliance"]
    },
    
    "Technical": {
        "focus": "Behind-the-scenes optimizations for crawlability and indexing",
        "key_elements": [
            "Well-configured robots.txt file",
            "XML sitemap submission to search engines",
            "Canonical tags for duplicate content",
            "HTTPS implementation",
            "Clean URLs without excessive parameters",
            "Proper 301 redirects, no broken links"
        ],
        "priority": "High",
        "standards": ["Google Search Console", "Technical SEO Best Practices"]
    },
    
    "Performance": {
        "focus": "Core Web Vitals optimization for speed and responsiveness",
        "key_elements": [
            "LCP under 2.5 seconds",
            "FID/INP under 100ms",
            "CLS below 0.1",
            "Image compression and lazy loading",
            "Minified and deferred JS/CSS",
            "CDN implementation and browser caching"
        ],
        "priority": "High",
        "standards": ["Core Web Vitals", "Google PageSpeed Insights"]
    },
    
    "UX": {
        "focus": "User Experience optimization for engagement and conversion",
        "key_elements": [
            "Mobile-friendly responsive design",
            "Clear navigation structure",
            "Readable content with proper formatting",
            "Minimal pop-ups and interstitials",
            "Fast page load times",
            "Logical content structure"
        ],
        "priority": "High",
        "standards": ["Mobile-First Indexing", "UX Best Practices"]
    },
    
    "Conversions": {
        "focus": "Conversion Rate Optimization for business goals",
        "key_elements": [
            "Clear, compelling CTAs",
            "Single primary CTA per page",
            "Simplified checkout process",
            "Trust signals and security badges",
            "Strategic form placement",
            "A/B testing implementation"
        ],
        "priority": "Medium",
        "standards": ["CRO Best Practices", "Conversion Optimization"]
    },
    
    "Content": {
        "focus": "High-quality, engaging content for SEO and user satisfaction",
        "key_elements": [
            "Substantive, unique content meeting user intent",
            "Natural keyword integration without stuffing",
            "E-E-A-T demonstration in YMYL topics",
            "Structured formatting with headings and lists",
            "Internal linking between related content",
            "Regular content updates and freshness"
        ],
        "priority": "High",
        "standards": ["Google Helpful Content", "E-E-A-T Guidelines"]
    }
}

# Industry-specific optimization templates
INDUSTRY_TEMPLATES = {
    "ecommerce": {
        "title_template": "Best {product} - {brand} | {location}",
        "meta_template": "Shop {product} at {brand}. {benefit}. Free shipping on orders over $50.",
        "h1_template": "Premium {product} Collection",
        "schema_type": "Product",
        "faq_topics": ["shipping", "returns", "warranty", "sizing", "payment"],
        "keywords_focus": ["buy", "shop", "price", "reviews", "quality", "best"]
    },
    
    "saas": {
        "title_template": "{product} - {benefit} | {brand}",
        "meta_template": "{product} helps {target_audience} {benefit}. Start free trial today.",
        "h1_template": "Transform Your {industry} with {product}",
        "schema_type": "SoftwareApplication",
        "faq_topics": ["pricing", "features", "integration", "support", "security", "trial"],
        "keywords_focus": ["software", "solution", "automation", "efficiency", "productivity", "platform"]
    },
    
    "local_business": {
        "title_template": "{service} in {location} | {brand}",
        "meta_template": "Professional {service} in {location}. {benefit}. Call {phone} for free quote.",
        "h1_template": "{service} Services in {location}",
        "schema_type": "LocalBusiness",
        "faq_topics": ["service_area", "pricing", "availability", "experience", "contact", "hours"],
        "keywords_focus": ["near me", "local", "professional", "quality", "reliable", "service"]
    },
    
    "blog": {
        "title_template": "{topic} Guide: {benefit} | {brand}",
        "meta_template": "Learn {topic} with our comprehensive guide. {benefit}. Expert insights included.",
        "h1_template": "Complete {topic} Guide",
        "schema_type": "Article",
        "faq_topics": ["basics", "advanced", "tools", "tips", "resources", "tutorials"],
        "keywords_focus": ["guide", "tutorial", "learn", "tips", "how-to", "expert"]
    },
    
    "corporate": {
        "title_template": "{company} - {industry} Solutions",
        "meta_template": "{company} provides {services} for {target_market}. {benefit}. Contact us today.",
        "h1_template": "Leading {industry} Solutions",
        "schema_type": "Organization",
        "faq_topics": ["company", "services", "clients", "contact", "careers", "expertise"],
        "keywords_focus": ["solutions", "services", "expertise", "experience", "results", "professional"]
    }
}

# User expertise levels and communication styles
USER_EXPERTISE_LEVELS = {
    "non_technical": {
        "tone": "Simple, clear language with minimal jargon",
        "explanations": "Plain-language recommendations with actionable steps",
        "technical_detail": "Basic implementation guidance",
        "examples": "Real-world analogies and simple instructions"
    },
    
    "technical": {
        "tone": "Professional with appropriate technical depth",
        "explanations": "Detailed technical guidance with code examples",
        "technical_detail": "Advanced implementation with best practices",
        "examples": "Code snippets, technical specifications, and advanced techniques"
    },
    
    "expert": {
        "tone": "Advanced professional with industry insights",
        "explanations": "Comprehensive technical analysis with strategic recommendations",
        "technical_detail": "Enterprise-level implementation with optimization strategies",
        "examples": "Advanced code examples, performance metrics, and strategic frameworks"
    }
}

# Risk management for recommendations
RISK_LEVELS = {
    "safe": {
        "description": "Proven, low-risk optimizations with predictable positive outcomes",
        "examples": [
            "Improving title tags and meta descriptions",
            "Adding alt text to images",
            "Fixing broken links",
            "Implementing basic structured data",
            "Optimizing page load speed"
        ],
        "implementation": "Immediate implementation recommended"
    },
    
    "moderate": {
        "description": "Evidence-based optimizations with some testing recommended",
        "examples": [
            "A/B testing new page layouts",
            "Implementing advanced structured data",
            "Content strategy changes",
            "Navigation structure modifications"
        ],
        "implementation": "Test on small sections first"
    },
    
    "bold": {
        "description": "Experimental or cutting-edge strategies with high potential ROI",
        "examples": [
            "AI-driven content personalization",
            "Experimental A/B tests on major pages",
            "Cutting-edge technology adoption",
            "Creative marketing tactics"
        ],
        "implementation": "Clearly marked as experimental with risk assessment"
    }
}

# Priority matrix for optimization recommendations
PRIORITY_MATRIX = {
    "high_impact_low_effort": {
        "priority": "Critical",
        "examples": [
            "Fixing missing meta descriptions",
            "Adding alt text to images",
            "Enabling compression",
            "Fixing broken links",
            "Adding basic structured data"
        ],
        "roi": "Immediate significant improvement"
    },
    
    "high_impact_high_effort": {
        "priority": "Strategic",
        "examples": [
            "Complete site redesign",
            "Content strategy overhaul",
            "Technical architecture changes",
            "Advanced performance optimization"
        ],
        "roi": "Long-term major improvement"
    },
    
    "low_impact_low_effort": {
        "priority": "Quick Wins",
        "examples": [
            "Minor content updates",
            "Small design improvements",
            "Basic schema additions",
            "Simple navigation tweaks"
        ],
        "roi": "Incremental improvement"
    },
    
    "low_impact_high_effort": {
        "priority": "Avoid",
        "examples": [
            "Complex features with minimal benefit",
            "Over-optimization of minor elements",
            "Unnecessary technical complexity"
        ],
        "roi": "Poor return on investment"
    }
}

# Standards and compliance requirements
COMPLIANCE_STANDARDS = {
    "google_guidelines": [
        "Google Search Essentials compliance",
        "E-E-A-T principles implementation",
        "People-first content approach",
        "No black-hat techniques",
        "Mobile-first indexing optimization"
    ],
    
    "accessibility": [
        "WCAG 2.1 AA compliance",
        "ADA compliance for applicable industries",
        "Screen reader compatibility",
        "Keyboard navigation support",
        "Color contrast requirements"
    ],
    
    "technical": [
        "Schema.org specifications",
        "Core Web Vitals thresholds",
        "HTTP/2+ implementation",
        "Security best practices",
        "Performance optimization standards"
    ],
    
    "industry_specific": [
        "Privacy regulations (GDPR, CCPA)",
        "Healthcare compliance (HIPAA)",
        "Financial regulations (PCI DSS)",
        "Government accessibility requirements"
    ]
}

def get_optimization_guidelines(industry, user_expertise, risk_tolerance="safe"):
    """
    Get comprehensive optimization guidelines based on industry, user expertise, and risk tolerance
    """
    industry_template = INDUSTRY_TEMPLATES.get(industry, INDUSTRY_TEMPLATES["corporate"])
    user_style = USER_EXPERTISE_LEVELS.get(user_expertise, USER_EXPERTISE_LEVELS["non_technical"])
    risk_level = RISK_LEVELS.get(risk_tolerance, RISK_LEVELS["safe"])
    
    return {
        "industry_template": industry_template,
        "user_communication": user_style,
        "risk_management": risk_level,
        "optimization_categories": OPTIMIZATION_CATEGORIES,
        "priority_matrix": PRIORITY_MATRIX,
        "compliance_standards": COMPLIANCE_STANDARDS
    }

def detect_industry_from_content(content_data):
    """
    Detect industry based on content analysis
    """
    all_text = ""
    for page in content_data.get('pages', []):
        all_text += f" {page.get('title', '')} {page.get('meta', '')} "
        for h1 in page.get('h1', []):
            all_text += f" {h1} "
    
    all_text = all_text.lower()
    
    # Industry detection keywords
    industry_keywords = {
        "ecommerce": ["shop", "buy", "cart", "checkout", "product", "price", "sale", "store"],
        "saas": ["software", "app", "platform", "dashboard", "api", "integration", "trial", "subscription"],
        "local_business": ["near me", "local", "service", "contact", "address", "phone", "location"],
        "blog": ["blog", "article", "post", "guide", "tutorial", "tips", "learn", "how-to"],
        "corporate": ["company", "about", "services", "solutions", "team", "careers", "business"]
    }
    
    industry_scores = {}
    for industry, keywords in industry_keywords.items():
        score = sum(1 for keyword in keywords if keyword in all_text)
        industry_scores[industry] = score
    
    # Return industry with highest score, or 'corporate' as default
    return max(industry_scores, key=industry_scores.get) if max(industry_scores.values()) > 0 else 'corporate'

def prioritize_recommendations(recommendations):
    """
    Prioritize recommendations based on impact/effort matrix
    """
    prioritized = {
        "critical": [],
        "high": [],
        "medium": [],
        "low": []
    }
    
    for rec in recommendations:
        impact = rec.get('impact', 'medium')
        effort = rec.get('effort', 'medium')
        
        if impact == 'high' and effort == 'low':
            prioritized['critical'].append(rec)
        elif impact == 'high' and effort == 'high':
            prioritized['high'].append(rec)
        elif impact == 'low' and effort == 'low':
            prioritized['medium'].append(rec)
        else:
            prioritized['low'].append(rec)
    
    return prioritized
