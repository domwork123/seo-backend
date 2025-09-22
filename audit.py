import requests, re
from bs4 import BeautifulSoup
import extruct
from w3lib.html import get_base_url
from urllib.parse import urljoin

def analyze(url: str):
    """Audit a single URL. Returns dict with SEO + AEO/GEO data."""
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "EvikaBot/1.0"})
        html = resp.text
    except Exception as e:
        return {"url": url, "error": f"Fetch failed: {str(e)}"}

    base_url = get_base_url(resp.text, resp.url)
    soup = BeautifulSoup(html, "html.parser")

    # --- BASIC SEO ---
    title = soup.title.string.strip() if soup.title else None
    meta_desc = None
    meta_tag = soup.find("meta", attrs={"name": "description"})
    if meta_tag and meta_tag.get("content"):
        meta_desc = meta_tag["content"].strip()

    h1 = soup.find("h1").get_text(" ", strip=True) if soup.find("h1") else None
    h2s = [h.get_text(" ", strip=True) for h in soup.find_all("h2")[:5]]
    h3s = [h.get_text(" ", strip=True) for h in soup.find_all("h3")[:5]]

    # --- IMAGES ---
    images = []
    for img in soup.find_all("img"):
        src = img.get("src")
        if not src:
            continue
        images.append({
            "src": urljoin(base_url, src),
            "alt": img.get("alt") or None
        })

    # --- SCHEMA (JSON-LD, Microdata, RDFa) ---
    try:
        data = extruct.extract(html, base_url=base_url, syntaxes=["json-ld", "microdata", "rdfa"], uniform=True)
        schema = data.get("json-ld", []) + data.get("microdata", []) + data.get("rdfa", [])
    except Exception as e:
        schema = []

    # --- NAP (Name, Address, Phone) heuristics ---
    text = soup.get_text(" ", strip=True)
    phone = None
    m = re.search(r"(\+?\d[\d\s\-\(\)]{6,})", text)
    if m:
        phone = m.group(1).strip()
    address = None
    if "Street" in text or "St." in text or "Vilnius" in text:
        # crude heuristic — you’ll refine with regex later
        idx = text.find("Vilnius")
        address = text[max(0, idx-50):idx+50]

    nap = {"phone": phone, "address": address}

    return {
        "url": url,
        "title": title,
        "meta": meta_desc,
        "h1": h1,
        "h2": h2s,
        "h3": h3s,
        "images": images,
        "schema": schema,
        "nap": nap,
        "text": text[:5000],  # keep reasonable length
        "word_count": len(text.split())
    }

