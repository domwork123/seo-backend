"""
Simple Blog Generator - Let the LLM handle everything naturally
Updated for Railway deployment
"""
import json
from typing import Dict, Any
from datetime import datetime

class SimpleBlogGenerator:
    def __init__(self):
        pass
    
    def generate_blog_post(self, 
                          brand_name: str, 
                          target_keyword: str, 
                          language: str = "en",
                          mode: str = "AEO",
                          context: Dict[str, Any] = None,
                          site_city: str = None) -> Dict[str, Any]:
        """
        Generate a blog post by passing everything to the LLM naturally
        
        Args:
            brand_name: Name of the brand
            target_keyword: Target keyword for SEO
            language: Language code (default: en)
            mode: AEO or GEO (default: AEO)
            context: Additional context from audit data
            site_city: City from site data for AEO posts
            
        Returns:
            Dict containing the generated blog post
        """
        
        # Create the prompt for the LLM
        prompt = self._create_llm_prompt(brand_name, target_keyword, language, mode, context, site_city)
        
        # For now, return a mock response - in real implementation, this would call the LLM
        # The LLM would handle all the language detection, city detection, and content generation
        return self._mock_llm_response(brand_name, target_keyword, language, mode)
    
    def _create_llm_prompt(self, brand_name: str, target_keyword: str, language: str, mode: str, context: Dict, site_city: str) -> str:
        """Create a comprehensive prompt for the LLM"""
        
        ruleset = """
        You are EVIKA's Blog Generator. You must produce a strict JSON object that matches the provided JSON schema.

        RULES:
        1. Use only the context provided. Do not invent facts (addresses, prices, certifications) not present in context.
        2. Language must be {language}. Brand is {brand_name}. Target keyword is {target_keyword}.
        3. Output must be 1000–1200 words (AEO) or 1200–1500 words (GEO).
        4. Heading hierarchy: H2 for sections, H3 for each FAQ item.
        5. Always include: Title, Meta Description (≤160 chars), Intro, Sections, FAQ (≥5 items), Images (≥2), Internal Links (≥2), Article+FAQ JSON-LD.
        6. If mode=GEO, also include LocalBusiness JSON-LD and local landmarks/areas in copy.
        7. Return only JSON that conforms to the schema. No prose.

        AEO RULES:
        - Focus on answerability (clear questions → direct answers)
        - Include People Also Ask-style FAQs (comparison, price, availability, authenticity)
        - Put target keyword in title, intro, one H2, conclusion
        - Keep sentences concise; favor bullets; avoid fluff

        GEO RULES:
        - Mention city and landmarks naturally (detect from target keyword)
        - Compare online vs local store experience; explain benefits of the brand in that city
        - Include LocalBusiness JSON-LD with whatever verified NAP data you have (or leave fields empty/null if unknown—never invent)
        - Suggest Google Maps embed (return the instruction, not an invented embed link)

        LANGUAGE RULES:
        - All output (title, meta, intro, headings, sections, FAQ questions, FAQ answers, image alt text, internal link anchor text, JSON-LD strings) must be entirely in the specified {language}.
        - Exceptions are brand names and URLs. No English sentence structures or words are allowed.
        - Correct locale and diacritics must be used. Generic English intros and headings must be translated.
        - Before final output, detect language of title, intro, and first FAQ question. If not {language}, regenerate with stricter instruction.

        OUTPUT FORMAT:
        Return only JSON with these keys:
        - title
        - meta_description
        - content (full markdown)
        - word_count
        - sections (array of {heading, content})
        - faqs (array of {question, answer})
        - images (array of {alt, src, caption})
        - internal_links (array of {text, url, anchor})
        - json_ld (object with article and optionally local_business)
        - mode
        - target_keyword
        - brand
        - language
        - generated_at
        """
        
        return f"""
        {ruleset}
        
        TASK:
        Generate a {mode} blog post for:
        - Brand: {brand_name}
        - Target Keyword: {target_keyword}
        - Language: {language}
        - Mode: {mode}
        - Context: {json.dumps(context) if context else 'None'}
        - Site City: {site_city or 'None'}
        
        IMPORTANT: 
        - Detect the city from the target keyword naturally
        - Use the correct language throughout
        - Let the LLM figure out everything automatically
        - Don't hardcode anything - let the LLM be smart
        """
    
    def _mock_llm_response(self, brand_name: str, target_keyword: str, language: str, mode: str) -> Dict[str, Any]:
        """Mock response - in real implementation, this would call the actual LLM"""
        
        # This is just a placeholder - the real implementation would call GPT-4 Mini
        # with the prompt and let it generate everything naturally
        
        return {
            "title": f"{target_keyword}: Complete Guide | {brand_name}",
            "meta_description": f"{brand_name} - Išsamus {target_keyword} vadovas. Ekspertų patarimai ir rekomendacijos. Pradėkite dabar!",
            "content": f"# {target_keyword}: Complete Guide\n\nThis would be generated by the LLM naturally...",
            "word_count": 1000,
            "sections": [],
            "faqs": [],
            "images": [],
            "internal_links": [],
            "json_ld": {},
            "mode": mode,
            "target_keyword": target_keyword,
            "brand": brand_name,
            "language": language,
            "generated_at": datetime.now().isoformat()
        }
