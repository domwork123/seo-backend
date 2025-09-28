"""Utility for generating AEO/GEO-optimized blog posts with an LLM backend."""

from __future__ import annotations

import json
import os
from datetime import datetime
from textwrap import dedent
from typing import Any, Dict, Optional

from langdetect import DetectorFactory, detect

DetectorFactory.seed = 0

try:  # pragma: no cover - import guard mirrors existing modules
    from openai import OpenAI
except ImportError:  # pragma: no cover - environments without OpenAI SDK
    OpenAI = None  # type: ignore


class SimpleBlogGenerator:
    """Generate long-form blog posts by delegating to an LLM.

    The generator builds a prescriptive prompt, calls the configured LLM, and
    validates the response against the expected schema.  When an LLM response is
    unavailable or malformed, a deterministic mock payload is returned to keep
    downstream flows resilient.
    """

    _DEFAULT_MODEL = os.getenv("BLOG_POST_LLM_MODEL", "gpt-4o-mini")

    def __init__(self, client: Optional[Any] = None) -> None:
        api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")

        if client is not None:
            self._client = client
        elif OpenAI and api_key:
            self._client = OpenAI(api_key=api_key)
        else:
            self._client = None

    def generate_blog_post(self,
                          brand_name: str,
                          target_keyword: str,
                          language: str = "en",
                          mode: str = "AEO",
                          context: Optional[Dict[str, Any]] = None,
                          site_city: str = None,
                          site_id: Optional[str] = None,
                          supabase_client = None) -> Dict[str, Any]:
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
        
        resolved_language = self._resolve_language(language, target_keyword, context)
        
        # Fetch comprehensive data from Supabase
        supabase_context = self._fetch_supabase_data(site_id, supabase_client) if site_id and supabase_client else {}
        
        # Merge context with Supabase data
        enhanced_context = {**(context or {}), **supabase_context}
        print(f"🔍 Enhanced context keys: {list(enhanced_context.keys())}")
        print(f"🔍 Context type: {type(context)}")
        print(f"🔍 Supabase context type: {type(supabase_context)}")
        
        prompt = self._create_llm_prompt(
            brand_name=brand_name,
            target_keyword=target_keyword,
            language=resolved_language,
            mode=mode,
            context=enhanced_context,
            site_city=site_city,
        )

        if not self._client:
            return self._mock_llm_response(brand_name, target_keyword, resolved_language, mode)

        try:
            response = self._client.chat.completions.create(
                model=self._DEFAULT_MODEL,
                temperature=0.2,
                max_tokens=4_000,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are EVIKA's specialised blog generation agent."
                            " Follow every rule precisely and always return JSON."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
            )

            raw_output = response.choices[0].message.content or ""
            print(f"🔍 Raw LLM output: {raw_output[:200]}...")
            parsed_output = self._parse_llm_response(raw_output)
            print(f"🔍 Parsed output keys: {list(parsed_output.keys())}")
            validated_output = self._coerce_response_structure(
                parsed_output,
                brand_name=brand_name,
                target_keyword=target_keyword,
                language=resolved_language,
                mode=mode,
            )
            return validated_output
        except Exception as exc:  # pragma: no cover - defensive logging path
            print(f"⚠️ LLM blog generation failed, using mock response: {exc}")
            return self._mock_llm_response(brand_name, target_keyword, resolved_language, mode)

    def _create_llm_prompt(self, brand_name: str, target_keyword: str, language: str, mode: str,
                           context: Optional[Dict[str, Any]], site_city: Optional[str]) -> str:
        """Create a comprehensive prompt for the LLM"""

        safe_context = self._serialise_context(context)
        ruleset = dedent(
            f"""
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
        )

        task = dedent(
            f"""
        TASK:
        Generate a {mode} blog post for:
        - Brand: {brand_name}
        - Target Keyword: {target_keyword}
        - Language: {language}
        - Mode: {mode}
        - Context: {safe_context}
        - Site City: {site_city or 'None'}

        IMPORTANT:
        - Detect the city from the target keyword naturally
        - Use the correct language throughout
        - Let the LLM figure out everything automatically
        - Don't hardcode anything - let the LLM be smart
        """
        )

        return f"{ruleset}\n\n{task}".strip()

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

    def _parse_llm_response(self, raw_output: str) -> Dict[str, Any]:
        """Extract JSON from the raw LLM output."""

        if not raw_output:
            raise ValueError("Empty response from LLM")

        cleaned = raw_output.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            # Remove potential language hint like ```json
            cleaned = cleaned.split("\n", 1)[-1]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Attempt to locate first JSON object boundaries
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1 and end > start:
                snippet = cleaned[start:end + 1]
                return json.loads(snippet)
            raise

    def _coerce_response_structure(
        self,
        response: Dict[str, Any],
        *,
        brand_name: str,
        target_keyword: str,
        language: str,
        mode: str,
    ) -> Dict[str, Any]:
        """Ensure the response matches the schema the API expects."""

        required_list_fields = {
            "sections": list,
            "faqs": list,
            "images": list,
            "internal_links": list,
        }

        if not isinstance(response, dict):
            raise ValueError("LLM response is not a JSON object")

        response.setdefault("title", f"{target_keyword} | {brand_name}")
        response.setdefault("meta_description", "")
        response.setdefault("content", "")
        response.setdefault("word_count", 0)
        response.setdefault("json_ld", {})

        for field, expected_type in required_list_fields.items():
            value = response.get(field)
            if not isinstance(value, expected_type):
                response[field] = []

        try:
            response["word_count"] = int(response.get("word_count", 0))
        except Exception:
            response["word_count"] = 0

        response["mode"] = mode
        response["target_keyword"] = target_keyword
        response["brand"] = brand_name
        response["language"] = language
        response.setdefault("generated_at", datetime.now().isoformat())

        return response

    def _resolve_language(self, language: Optional[str], target_keyword: str,
                           context: Optional[Dict[str, Any]]) -> str:
        """Pick the best language code based on inputs and detection heuristics."""

        candidates = [language, self._detect_language(target_keyword)]

        if context:
            context_lang = context.get("language") or context.get("lang")
            if isinstance(context_lang, str):
                candidates.append(context_lang)

            # Sample textual signals for detection
            for key in ("title", "description", "summary"):
                text = context.get(key)
                if isinstance(text, str):
                    candidates.append(self._detect_language(text))

        for candidate in candidates:
            if isinstance(candidate, str) and candidate:
                return candidate

        return "en"

    @staticmethod
    def _detect_language(text: Optional[str]) -> str:
        if not text or not text.strip():
            return ""
        try:
            return detect(text)
        except Exception:
            return ""

    def _fetch_supabase_data(self, site_id: str, supabase_client) -> Dict[str, Any]:
        """Fetch comprehensive data from Supabase for better blog generation"""
        
        if not site_id or not supabase_client:
            return {}
        
        try:
            # Fetch site information
            site_data = {}
            try:
                site_result = supabase_client.table("sites").select("*").eq("id", site_id).execute()
                if site_result.data and len(site_result.data) > 0:
                    site_data = site_result.data[0]
            except Exception as e:
                print(f"⚠️ Could not fetch site data: {e}")
            
            # Fetch pages data
            pages_data = []
            try:
                pages_result = supabase_client.table("pages").select("*").eq("site_id", site_id).limit(10).execute()
                if pages_result.data:
                    pages_data = pages_result.data
            except Exception as e:
                print(f"⚠️ Could not fetch pages data: {e}")
            
            # Fetch audit data
            audit_data = {}
            try:
                audit_result = supabase_client.table("audits").select("*").eq("site_id", site_id).order("created_at", desc=True).limit(1).execute()
                if audit_result.data and len(audit_result.data) > 0:
                    audit_data = audit_result.data[0]
            except Exception as e:
                print(f"⚠️ Could not fetch audit data: {e}")
            
            # Compile comprehensive context
            context = {
                "site_info": {
                    "brand_name": site_data.get("brand_name", ""),
                    "description": site_data.get("description", ""),
                    "location": site_data.get("location", ""),
                    "industry": site_data.get("industry", ""),
                    "language": site_data.get("language", ""),
                    "url": site_data.get("url", "")
                },
                "pages": pages_data,
                "audit_data": {
                    "faqs": audit_data.get("faqs", []),
                    "schema": audit_data.get("schema", {}),
                    "competitors": audit_data.get("competitors", []),
                    "geo_signals": audit_data.get("geo_signals", {}),
                    "alt_text_issues": audit_data.get("alt_text", [])
                },
                "extracted_content": {
                    "titles": [page.get("title", "") for page in pages_data if page.get("title")],
                    "descriptions": [page.get("meta_description", "") for page in pages_data if page.get("meta_description")],
                    "headings": self._extract_headings_from_pages(pages_data),
                    "products_services": self._extract_products_from_pages(pages_data)
                }
            }
            
            print(f"📊 Fetched comprehensive Supabase data for site {site_id}")
            return context
            
        except Exception as e:
            print(f"❌ Error fetching Supabase data: {e}")
            return {}
    
    def _extract_headings_from_pages(self, pages_data: list) -> list:
        """Extract headings from pages data"""
        headings = []
        for page in pages_data:
            if page.get("raw_text"):
                # Simple extraction of potential headings (lines starting with # or all caps)
                text_lines = page["raw_text"].split('\n')
                for line in text_lines[:20]:  # Check first 20 lines
                    line = line.strip()
                    if line.startswith('#') or (len(line) > 10 and line.isupper()):
                        headings.append(line)
        return headings[:10]  # Limit to 10 headings
    
    def _extract_products_from_pages(self, pages_data: list) -> list:
        """Extract potential products/services from pages data"""
        products = []
        for page in pages_data:
            if page.get("raw_text"):
                # Look for common product/service indicators
                text = page["raw_text"].lower()
                if any(keyword in text for keyword in ["produktas", "paslauga", "prekė", "tarnyba", "produktai", "paslaugos"]):
                    # Extract potential product names (simplified)
                    lines = page["raw_text"].split('\n')
                    for line in lines[:10]:
                        if any(keyword in line.lower() for keyword in ["produktas", "paslauga", "prekė"]):
                            products.append(line.strip())
        return products[:5]  # Limit to 5 products

    @staticmethod
    def _serialise_context(context: Optional[Dict[str, Any]]) -> str:
        if not context:
            return "None"

        try:
            payload = json.dumps(context, ensure_ascii=False)
            if len(payload) > 1_500:
                payload = payload[:1_500] + "…"
            return payload
        except Exception:
            return "Context serialization failed"