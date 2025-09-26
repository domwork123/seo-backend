# Query Analysis for AI Visibility Testing
import openai
import json
import re
import os
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
from scrapingbee_integration import fetch_with_scrapingbee
import asyncio

class QueryAnalyzer:
    """Analyze how brands appear in AI query responses"""
    
    def __init__(self):
        # Get OpenAI API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        self.openai_client = openai.OpenAI(api_key=api_key)
    
    async def analyze_website_queries(self, url: str, queries: List[str] = None) -> Dict[str, Any]:
        """
        Main function to analyze website query visibility
        
        Args:
            url: Website URL to analyze
            queries: Optional list of custom queries
            
        Returns:
            Dict with analysis results
        """
        try:
            # Step 1: Crawl website and extract context
            print(f"DEBUG: Starting query analysis for {url}")
            context = await self._extract_website_context(url)
            print(f"DEBUG: Extracted context: {context}")
            
            # Step 2: Generate queries if none provided
            if not queries:
                queries = await self._generate_queries(context)
                print(f"DEBUG: Generated {len(queries)} queries")
            
            # Step 3: Analyze query visibility
            results = []
            for query in queries:
                print(f"DEBUG: Analyzing query: {query}")
                analysis = await self._analyze_query_visibility(query, context)
                results.append(analysis)
            
            return {
                "success": True,
                "url": url,
                "context": context,
                "queries_analyzed": len(queries),
                "results": results
            }
            
        except Exception as e:
            print(f"DEBUG: Query analysis error: {e}")
            return {
                "success": False,
                "error": str(e),
                "url": url
            }
    
    async def _extract_website_context(self, url: str) -> Dict[str, Any]:
        """Extract brand context from website using ScrapingBee"""
        try:
            # Fetch homepage first
            homepage_result = fetch_with_scrapingbee(url)
            if homepage_result['status'] != 'success':
                raise Exception(f"Failed to fetch homepage: {homepage_result.get('error')}")
            
            homepage_html = homepage_result['html']
            soup = BeautifulSoup(homepage_html, 'html.parser')
            
            # Extract basic brand info
            brand_name = self._extract_brand_name(soup)
            description = self._extract_description(soup)
            industry = self._extract_industry(soup, brand_name)
            
            # Crawl additional pages for more context
            additional_context = await self._crawl_additional_pages(url, soup)
            
            return {
                "brand_name": brand_name,
                "description": description,
                "industry": industry,
                "products": additional_context.get("products", []),
                "location": additional_context.get("location", ""),
                "faq_topics": additional_context.get("faq_topics", [])
            }
            
        except Exception as e:
            print(f"DEBUG: Context extraction error: {e}")
            return {
                "brand_name": "Unknown",
                "description": "",
                "industry": "Unknown",
                "products": [],
                "location": "",
                "faq_topics": []
            }
    
    def _extract_brand_name(self, soup: BeautifulSoup) -> str:
        """Extract brand name from various sources"""
        # Try og:site_name first
        og_site = soup.find('meta', property='og:site_name')
        if og_site and og_site.get('content'):
            return og_site['content'].strip()
        
        # Try title tag
        title = soup.find('title')
        if title:
            title_text = title.get_text().strip()
            # Remove common suffixes
            for suffix in [' - Home', ' | Home', ' - Official', ' | Official']:
                if title_text.endswith(suffix):
                    title_text = title_text[:-len(suffix)]
            return title_text
        
        # Try organization schema
        org_schema = soup.find('script', type='application/ld+json')
        if org_schema:
            try:
                schema_data = json.loads(org_schema.string)
                if isinstance(schema_data, dict) and schema_data.get('@type') == 'Organization':
                    return schema_data.get('name', '')
            except:
                pass
        
        return "Unknown Brand"
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract website description"""
        # Try meta description first
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'].strip()
        
        # Try og:description
        og_desc = soup.find('meta', property='og:description')
        if og_desc and og_desc.get('content'):
            return og_desc['content'].strip()
        
        # Try first paragraph
        first_p = soup.find('p')
        if first_p:
            return first_p.get_text().strip()[:200]
        
        return ""
    
    def _extract_industry(self, soup: BeautifulSoup, brand_name: str) -> str:
        """Extract industry/niche from content"""
        # Look for industry keywords in content
        content_text = soup.get_text().lower()
        
        industry_keywords = {
            'perfume': ['perfume', 'fragrance', 'scent', 'eau de toilette', 'cologne'],
            'fashion': ['fashion', 'clothing', 'apparel', 'style'],
            'beauty': ['beauty', 'cosmetics', 'makeup', 'skincare'],
            'technology': ['software', 'app', 'tech', 'digital', 'platform'],
            'ecommerce': ['shop', 'store', 'buy', 'purchase', 'online'],
            'subscription': ['subscription', 'monthly', 'recurring', 'membership']
        }
        
        for industry, keywords in industry_keywords.items():
            if any(keyword in content_text for keyword in keywords):
                return industry
        
        return "General"
    
    async def _crawl_additional_pages(self, base_url: str, homepage_soup: BeautifulSoup) -> Dict[str, Any]:
        """Crawl additional pages to extract more context"""
        try:
            # Extract internal links
            internal_links = self._extract_internal_links(homepage_soup, base_url)
            
            products = []
            location = ""
            faq_topics = []
            
            # Crawl up to 5 additional pages
            pages_to_crawl = internal_links[:5]
            
            for link in pages_to_crawl:
                try:
                    result = fetch_with_scrapingbee(link)
                    if result['status'] == 'success':
                        page_soup = BeautifulSoup(result['html'], 'html.parser')
                        
                        # Extract products from product pages
                        if any(keyword in link.lower() for keyword in ['product', 'shop', 'catalog']):
                            page_products = self._extract_products(page_soup)
                            products.extend(page_products)
                        
                        # Extract location from contact/about pages
                        if any(keyword in link.lower() for keyword in ['contact', 'about', 'location']):
                            page_location = self._extract_location(page_soup)
                            if page_location:
                                location = page_location
                        
                        # Extract FAQ topics
                        page_faqs = self._extract_faq_topics(page_soup)
                        faq_topics.extend(page_faqs)
                        
                except Exception as e:
                    print(f"DEBUG: Error crawling {link}: {e}")
                    continue
            
            return {
                "products": list(set(products))[:10],  # Remove duplicates, limit to 10
                "location": location,
                "faq_topics": list(set(faq_topics))[:5]  # Remove duplicates, limit to 5
            }
            
        except Exception as e:
            print(f"DEBUG: Additional crawling error: {e}")
            return {"products": [], "location": "", "faq_topics": []}
    
    def _extract_internal_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract internal links from page"""
        from urllib.parse import urljoin, urlparse
        
        base_domain = urlparse(base_url).netloc
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(base_url, href)
            
            # Check if it's an internal link
            if urlparse(full_url).netloc == base_domain:
                links.append(full_url)
        
        return links
    
    def _extract_products(self, soup: BeautifulSoup) -> List[str]:
        """Extract product names from page"""
        products = []
        
        # Look for product names in headings
        for heading in soup.find_all(['h1', 'h2', 'h3']):
            text = heading.get_text().strip()
            if text and len(text) < 100:  # Reasonable product name length
                products.append(text)
        
        # Look for product schema
        product_schemas = soup.find_all('script', type='application/ld+json')
        for schema in product_schemas:
            try:
                data = json.loads(schema.string)
                if isinstance(data, dict) and data.get('@type') == 'Product':
                    if data.get('name'):
                        products.append(data['name'])
            except:
                pass
        
        return products
    
    def _extract_location(self, soup: BeautifulSoup) -> str:
        """Extract location information"""
        # Look for address in text
        text = soup.get_text()
        
        # Look for country names
        countries = ['Lithuania', 'Latvia', 'Estonia', 'Poland', 'Germany', 'France', 'UK', 'USA']
        for country in countries:
            if country.lower() in text.lower():
                return country
        
        # Look for location schema
        location_schemas = soup.find_all('script', type='application/ld+json')
        for schema in location_schemas:
            try:
                data = json.loads(schema.string)
                if isinstance(data, dict):
                    if data.get('@type') == 'LocalBusiness' and data.get('address'):
                        address = data['address']
                        if isinstance(address, dict):
                            return address.get('addressCountry', '')
                        elif isinstance(address, str):
                            return address
            except:
                pass
        
        return ""
    
    def _extract_faq_topics(self, soup: BeautifulSoup) -> List[str]:
        """Extract FAQ topics from page"""
        faq_topics = []
        
        # Look for headings with question marks
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4']):
            text = heading.get_text().strip()
            if '?' in text:
                # Clean up the question
                topic = text.replace('?', '').strip()
                if len(topic) > 5 and len(topic) < 100:
                    faq_topics.append(topic)
        
        # Look for FAQ schema
        faq_schemas = soup.find_all('script', type='application/ld+json')
        for schema in faq_schemas:
            try:
                data = json.loads(schema.string)
                if isinstance(data, dict) and data.get('@type') == 'FAQPage':
                    main_entity = data.get('mainEntity', [])
                    if isinstance(main_entity, list):
                        for item in main_entity:
                            if isinstance(item, dict) and item.get('name'):
                                faq_topics.append(item['name'])
            except:
                pass
        
        return faq_topics
    
    async def _generate_queries(self, context: Dict[str, Any]) -> List[str]:
        """Generate relevant queries based on website context"""
        try:
            brand_name = context.get('brand_name', 'Unknown')
            industry = context.get('industry', 'Unknown')
            products = context.get('products', [])
            location = context.get('location', '')
            
            # Create prompt for query generation
            prompt = f"""
            Generate 5 realistic customer queries about this business:
            
            Brand: {brand_name}
            Industry: {industry}
            Products: {', '.join(products[:3]) if products else 'Not specified'}
            Location: {location if location else 'Not specified'}
            
            Generate queries in these categories:
            1. Direct brand query (e.g., "What is {brand_name}?")
            2. Industry query (e.g., "Best {industry} in {location}")
            3. Product query (e.g., "Where to buy [product] in {location}")
            4. Comparison query (e.g., "{brand_name} vs [competitor]")
            5. Trust/quality query (e.g., "Is {brand_name} trustworthy?")
            
            Return only the 5 queries as a JSON array of strings.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that generates realistic customer queries for businesses."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            # Parse the response
            content = response.choices[0].message.content.strip()
            
            # Try to extract JSON array
            if content.startswith('[') and content.endswith(']'):
                queries = json.loads(content)
                if isinstance(queries, list) and len(queries) == 5:
                    return queries
            
            # Fallback: extract queries from text
            lines = content.split('\n')
            queries = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('-'):
                    # Clean up the query
                    query = line.replace('"', '').replace("'", '').strip()
                    if query and len(query) > 10:
                        queries.append(query)
            
            return queries[:5] if queries else self._get_default_queries(brand_name, industry)
            
        except Exception as e:
            print(f"DEBUG: Query generation error: {e}")
            return self._get_default_queries(context.get('brand_name', 'Unknown'), context.get('industry', 'Unknown'))
    
    def _get_default_queries(self, brand_name: str, industry: str) -> List[str]:
        """Get default queries if generation fails"""
        return [
            f"What is {brand_name}?",
            f"Is {brand_name} trustworthy?",
            f"Best {industry} companies",
            f"How does {brand_name} work?",
            f"{brand_name} reviews"
        ]
    
    async def _analyze_query_visibility(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze how a brand appears in AI query responses"""
        try:
            brand_name = context.get('brand_name', 'Unknown')
            
            # Get AI response to the query
            ai_response = await self._get_ai_response(query)
            
            # Analyze the response
            brand_mentioned = self._check_brand_mention(ai_response, brand_name)
            competitors = self._extract_competitors(ai_response, brand_name)
            
            # Generate recommendation
            recommendation = self._generate_recommendation(
                query, brand_mentioned, competitors, brand_name, context
            )
            
            return {
                "query": query,
                "ai_answer": ai_response,
                "brand_mentioned": brand_mentioned,
                "competitors_mentioned": competitors,
                "recommendation": recommendation
            }
            
        except Exception as e:
            print(f"DEBUG: Query analysis error for '{query}': {e}")
            return {
                "query": query,
                "ai_answer": f"Error analyzing query: {str(e)}",
                "brand_mentioned": False,
                "competitors_mentioned": [],
                "recommendation": "Error in analysis"
            }
    
    async def _get_ai_response(self, query: str) -> str:
        """Get AI response to a query"""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that provides accurate, unbiased information. Answer questions based on your knowledge."},
                    {"role": "user", "content": query}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"DEBUG: AI response error: {e}")
            return f"Error getting AI response: {str(e)}"
    
    def _check_brand_mention(self, response: str, brand_name: str) -> bool:
        """Check if brand is mentioned in the response"""
        response_lower = response.lower()
        brand_lower = brand_name.lower()
        
        # Check for exact brand name
        if brand_lower in response_lower:
            return True
        
        # Check for partial matches (useful for longer brand names)
        brand_words = brand_lower.split()
        if len(brand_words) > 1:
            # Check if most words from brand name are present
            matches = sum(1 for word in brand_words if word in response_lower)
            if matches >= len(brand_words) * 0.7:  # 70% of words match
                return True
        
        return False
    
    def _extract_competitors(self, response: str, brand_name: str) -> List[str]:
        """Extract competitor brand names from response"""
        # Common competitor patterns
        competitor_patterns = [
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',  # Capitalized words
            r'\b[A-Z]{2,}\b',  # Acronyms
        ]
        
        competitors = []
        response_lower = response.lower()
        brand_lower = brand_name.lower()
        
        # Extract potential brand names
        for pattern in competitor_patterns:
            matches = re.findall(pattern, response)
            for match in matches:
                match_lower = match.lower()
                # Filter out the target brand and common words
                if (match_lower != brand_lower and 
                    match_lower not in ['the', 'and', 'or', 'but', 'for', 'with', 'by'] and
                    len(match) > 2):
                    competitors.append(match)
        
        # Remove duplicates and limit
        return list(set(competitors))[:5]
    
    def _generate_recommendation(self, query: str, brand_mentioned: bool, 
                               competitors: List[str], brand_name: str, 
                               context: Dict[str, Any]) -> str:
        """Generate actionable recommendation based on analysis"""
        
        if brand_mentioned and not competitors:
            return "No action needed - brand is well represented."
        
        elif brand_mentioned and competitors:
            return f"Brand is mentioned but competitors dominate. Create comparison content: 'Why {brand_name} > {competitors[0]}'."
        
        elif not brand_mentioned and competitors:
            return f"Brand missing from answer. Create FAQ schema and blog content targeting: '{query}'."
        
        else:
            # Brand not mentioned, no competitors either
            return f"Brand not visible. Create comprehensive content strategy targeting: '{query}' with FAQ schema and blog posts."

# Standalone function for the endpoint
async def analyze_query_visibility(url: str, queries: List[str] = None) -> Dict[str, Any]:
    """Standalone function for query visibility analysis"""
    analyzer = QueryAnalyzer()
    return await analyzer.analyze_website_queries(url, queries)
