# audit.py
import httpx
import re
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import extruct
from w3lib.html import get_base_url

# -------------------
# Single page analyzer
# -------------------
async def analyze_page(url: str) -> dict:
    async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
        resp = await client.get(url)
        html = resp.text

    soup = BeautifulSoup(html, "lxml")

    # Title + meta
    title = soup.title.string.strip() if soup.title else None
    meta = None
    desc = soup.find("meta", attrs={"name": "description"})
    if desc and desc.get("content"):
        meta = desc["content"]

    # Headings
    h1 = soup.h1.get_text(strip=True) if soup.h1 else None
    h2 = [h.get_text(strip=True) for h in soup.find_all("h2")]
    h3 = [h.get_text(strip=True) for h in soup.find_all("h3")]

    # Images
    images = []
    for img in soup.find_all("img"):
        images.append({
            "src": urljoin(url, img.get("src")),
            "alt": img.get("alt")
        })

    # Schema.org extraction
    base_url = get_base_url(html, url)
    data = extruct.extract(
        html,
        base_url=base_url,
        syntaxes=["json-ld", "microdata", "opengraph"],
        uniform=True
    )

    # FAQs (from schema + text fallback)
    faqs = []
    if "json-ld" in data:
        for block in data["json-ld"]:
            if block.get("@type") in ["FAQPage", "QAPage"]:
                for qa in block.get("mainEntity", []):
                    if qa.get("@type") == "Question":
                        q = qa.get("name")
                        a = None
                        answers = qa.get("acceptedAnswer") or qa.get("suggestedAnswer")
                        if isinstance(answers, list) and answers:
                            a = answers[0].get("text")
                        elif isinstance(answers, dict):
                            a = answers.get("text")
                        faqs.append({"q": q, "a": a})

    # Simple text fallback: detect lines like Q: ... A: ...
    text = soup.get_text(separator=" ", strip=True)
    q_matches = re.findall(r"(?:Q:|Question:)\s*(.+?)\s*(?:A:|Answer:)\s*(.+?)(?=Q:|$)", text, re.I | re.S)
    for q, a in q_matches:
        faqs.append({"q": q.strip(), "a": a.strip()})

    # Phone/address detection
    phone_match = re.search(r"(\+370\d{8}|\+\d{10,15})", html)
    address_match = re.search(r"(Vilnius|Kaunas|Klaipėda|Lithuania|Netherlands)", html, re.I)

    return {
        "url": url,
        "title": title,
        "meta": meta,
        "h1": h1,
        "h2": h2,
        "h3": h3,
        "images": images,
        "schema": data,
        "faq": faqs,
        "nap": {
            "phone": phone_match.group(0) if phone_match else None,
            "address": address_match.group(0) if address_match else None,
        },
        "word_count": len(text.split()),
    }

# -------------------
# Site crawler
# -------------------
async def audit_site(url: str, max_pages: int = 50) -> dict:
    visited, to_visit, pages = set(), [url], []

    while to_visit and len(visited) < max_pages:
        current = to_visit.pop(0)
        if current in visited:
            continue
        try:
            page_result = await analyze_page(current)
            pages.append(page_result)
            visited.add(current)

            # collect internal links for crawl
            async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
                resp = await client.get(current)
                soup = BeautifulSoup(resp.text, "lxml")
                for a in soup.find_all("a", href=True):
                    href = urljoin(current, a["href"])
                    if urlparse(href).netloc == urlparse(url).netloc:
                        if href not in visited and href not in to_visit:
                            to_visit.append(href)
        except Exception as e:
            pages.append({"url": current, "error": str(e)})

    return {
        "url": url,
        "pages_discovered": len(pages),
        "pages": pages,
    }

