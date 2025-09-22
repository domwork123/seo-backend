# audit.py — Full-site audit for AEO/GEO
# Python 3.11+ recommended

import asyncio
import re
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
import extruct
from w3lib.html import get_base_url
import tldextract
from langdetect import detect, LangDetectException

# -----------------------
# CONFIG
# -----------------------
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; EvikaAuditBot/1.0)"}
REQUEST_TIMEOUT = 20.0
MAX_PAGES_DEFAULT = 50          # cap crawl size
CONCURRENCY = 8                 # concurrent fetches
FOLLOW_QUERYSTRING = False      # avoid ?utm= etc.

# -----------------------
# UTILITIES
# -----------------------
def same_domain(base: str, candidate: str) -> bool:
    b = tldextract.extract(base).registered_domain
    c = tldextract.extract(candidate).registered_domain
    return b == c and candidate.startswith(("http://", "https://"))

def strip_fragment(u: str) -> str:
    parsed = urlparse(u)
    if not FOLLOW_QUERYSTRING:
        parsed = parsed._replace(query="")
    return parsed._replace(fragment="").geturl()

def text_content(soup: BeautifulSoup) -> str:
    for tag in soup(["script", "style", "noscript", "template"]):
        tag.decompose()
    return soup.get_text(separator=" ", strip=True)

def to_abs(base: str, src: Optional[str]) -> Optional[str]:
    if not src:
        return None
    return urljoin(base, src)

# -----------------------
# SCHEMA HELPERS
# -----------------------
def collect_schema(html: str, base_url: str) -> List[Dict[str, Any]]:
    try:
        data = extruct.extract(
            html,
            base_url=base_url,
            syntaxes=["json-ld", "microdata", "opengraph", "rdfa"],
            uniform=True
        )
        out: List[Dict[str, Any]] = []
        for key in ("json-ld", "microdata", "opengraph", "rdfa"):
            if key in data and isinstance(data[key], list):
                out.extend(data[key])
        return out
    except Exception:
        return []

def schema_first(items: List[Dict[str, Any]], types: List[str]) -> List[Dict[str, Any]]:
    out = []
    for it in items:
        t = it.get("@type") or it.get("type") or it.get("og:type")
        if isinstance(t, list):
            if any(tt in types for tt in t):
                out.append(it)
        elif isinstance(t, str):
            if t in types:
                out.append(it)
    return out

def extract_postal_address_from_schema(items: List[Dict[str, Any]]) -> Dict[str, Optional[str]]:
    # Look into LocalBusiness/Organization/Person for postalAddress
    targets = schema_first(items, ["LocalBusiness", "Organization", "Person"])
    for node in targets:
        addr = node.get("address")
        if isinstance(addr, dict):
            return {
                "name": node.get("name"),
                "street": addr.get("streetAddress"),
                "city": addr.get("addressLocality"),
                "region": addr.get("addressRegion"),
                "postal_code": addr.get("postalCode"),
                "country": addr.get("addressCountry"),
                "phone": node.get("telephone") or node.get("phone"),
            }
    # Sometimes address is in nested graph/list
    for node in items:
        if isinstance(node, dict):
            addr = node.get("address")
            if isinstance(addr, dict):
                return {
                    "name": node.get("name"),
                    "street": addr.get("streetAddress"),
                    "city": addr.get("addressLocality"),
                    "region": addr.get("addressRegion"),
                    "postal_code": addr.get("postalCode"),
                    "country": addr.get("addressCountry"),
                    "phone": node.get("telephone") or node.get("phone"),
                }
    return {"name": None, "street": None, "city": None, "region": None, "postal_code": None, "country": None, "phone": None}

def extract_faq_from_schema(items: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    out = []
    faq_nodes = schema_first(items, ["FAQPage"])
    for node in faq_nodes:
        ents = node.get("mainEntity") or node.get("mainentity")
        if isinstance(ents, list):
            for q in ents:
                if isinstance(q, dict):
                    name = q.get("name") or q.get("headline")
                    ans = q.get("acceptedAnswer") or q.get("acceptedanswer")
                    if isinstance(ans, dict):
                        atext = ans.get("text") or ans.get("description")
                    else:
                        atext = None
                    if name and atext:
                        out.append({"q": str(name), "a": str(atext)})
    return out

# -----------------------
# FALLBACK NAP (robust intl)
# -----------------------
PHONE_REGEX = re.compile(
    r"(?:\+?\d{1,3}[\s\-\.]?)?(?:\(?\d{2,4}\)?[\s\-\.]?)?\d{3,4}[\s\-\.]?\d{3,4}"
)
ADDRESS_HINTS = [
    "street", "str.", "str", "road", "rd", "ave", "avenue", "blvd", "boulevard",
    "gata", "g.", "gatvė", "ul.", "calle", "straße", "strasse", "rue", "via",
    "postcode", "postal", "zip", "city", "miestas"
]

def fallback_nap(soup: BeautifulSoup, text: str) -> Dict[str, Optional[str]]:
    # phone
    phone = None
    m = PHONE_REGEX.search(text)
    if m:
        phone = m.group(0)

    # crude address: look for lines containing address hints
    address = None
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for ln in lines:
        low = ln.lower()
        if any(h in low for h in ADDRESS_HINTS):
            address = ln
            break

    return {"name": None, "street": None, "city": None, "region": None, "postal_code": None, "country": None, "phone": phone, "raw_address": address}

# -----------------------
# FAQ INFERENCE (when schema missing)
# -----------------------
QUESTION_STARTERS = ("how", "what", "why", "when", "where", "who", "can", "is", "are", "do", "does", "should", "will")

def infer_faq(soup: BeautifulSoup) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    candidates = soup.find_all(["h2", "h3", "strong", "p", "li"])
    for el in candidates:
        q = el.get_text(strip=True)
        if not q:
            continue
        lower = q.lower()
        if "?" in q or lower.startswith(QUESTION_STARTERS):
            # answer: next non-empty sibling or following paragraph
            nxt = el.find_next_sibling()
            ans = None
            while nxt and not ans:
                txt = nxt.get_text(strip=True)
                if txt:
                    ans = txt
                    break
                nxt = nxt.find_next_sibling()
            if ans:
                out.append({"q": q, "a": ans})
            if len(out) >= 20:
                break
    return out

# -----------------------
# PAGE EXTRACTOR
# -----------------------
def extract_page(url: str, html: str) -> Dict[str, Any]:
    soup = BeautifulSoup(html, "lxml")
    base_url = get_base_url(html, url)

    # Title / meta
    title = (soup.title.string or "").strip() if soup.title and soup.title.string else ""
    meta_desc = ""
    mtag = soup.find("meta", attrs={"name": "description"})
    if mtag and mtag.get("content"):
        meta_desc = mtag["content"].strip()

    # canonical
    canonical = None
    ctag = soup.find("link", rel=lambda x: x and "canonical" in x.lower())
    if ctag and ctag.get("href"):
        canonical = to_abs(base_url, ctag["href"])

    # robots meta
    robots_meta = None
    rtag = soup.find("meta", attrs={"name": "robots"})
    if rtag and rtag.get("content"):
        robots_meta = rtag["content"].strip()

    # hreflang
    hreflang: List[Dict[str, str]] = []
    for link in soup.find_all("link", rel="alternate"):
        if link.get("hreflang") and link.get("href"):
            hreflang.append({"lang": link["hreflang"], "url": to_abs(base_url, link["href"])})

    # og / twitter
    og_tags: Dict[str, str] = {}
    tw_tags: Dict[str, str] = {}
    for tag in soup.find_all("meta"):
        prop = tag.get("property") or ""
        name = tag.get("name") or ""
        content = tag.get("content") or ""
        if prop.startswith("og:"):
            og_tags[prop] = content
        if name.startswith("twitter:"):
            tw_tags[name] = content

    # Headings
    h1 = soup.h1.get_text(strip=True) if soup.h1 else ""
    h2 = [h.get_text(strip=True) for h in soup.find_all("h2")]
    h3 = [h.get_text(strip=True) for h in soup.find_all("h3")]

    # Images
    images = []
    for img in soup.find_all("img"):
        src = to_abs(base_url, img.get("src"))
        alt = img.get("alt")
        if src:
            images.append({"src": src, "alt": alt})

    # Schema
    schema_items = collect_schema(html, base_url)

    # FAQ (schema first, then infer)
    faq_schema = extract_faq_from_schema(schema_items)
    faq_inferred = infer_faq(soup) if not faq_schema else []

    # NAP (schema first, then fallback)
    nap = extract_postal_address_from_schema(schema_items)
    if not any([nap.get("street"), nap.get("city"), nap.get("postal_code"), nap.get("country"), nap.get("phone")]):
        # fallback to text/regex
        txt = text_content(soup)
        nap = fallback_nap(soup, txt)

    # Language
    lang = None
    if soup.html and soup.html.get("lang"):
        lang = soup.html.get("lang").lower()
    elif og_tags.get("og:locale"):
        lang = og_tags["og:locale"]
    else:
        snippet = text_content(soup)
        try:
            lang = detect(snippet[:2000])
        except LangDetectException:
            lang = None

    # Word count + main text
    visible_text = text_content(soup)
    word_count = len(visible_text.split())

    return {
        "url": url,
        "title": title,
        "meta": meta_desc,
        "h1": h1,
        "h2": h2,
        "h3": h3,
        "canonical": canonical,
        "robots": robots_meta,
        "hreflang": hreflang,
        "og_tags": og_tags,
        "twitter_tags": tw_tags,
        "images": images,
        "schema": schema_items,
        "faq_schema": faq_schema,
        "faq_inferred": faq_inferred,
        "nap": nap,
        "lang": lang,
        "text": visible_text[:8000],   # keep payload sane
        "word_count": word_count,
    }

# -----------------------
# FETCH + DISCOVERY
# -----------------------
async def fetch_text(client: httpx.AsyncClient, url: str) -> Optional[str]:
    try:
        r = await client.get(url, headers=HEADERS)
        if r.status_code >= 200 and r.status_code < 400:
            return r.text
    except Exception:
        return None
    return None

async def discover_with_sitemap(client: httpx.AsyncClient, base_url: str, cap: int) -> List[str]:
    # Try several common sitemap locations
    roots = [
        "/sitemap.xml", "/sitemap_index.xml", "/sitemap-index.xml",
        "/sitemaps/sitemap.xml"
    ]
    found: List[str] = []
    for p in roots:
        sm_url = urljoin(base_url, p)
        html = await fetch_text(client, sm_url)
        if not html:
            continue
        # XML sitemap
        if "<urlset" in html or "<sitemapindex" in html:
            soup = BeautifulSoup(html, "xml")
            locs = [loc.get_text(strip=True) for loc in soup.find_all("loc")]
            for u in locs:
                if same_domain(base_url, u):
                    found.append(strip_fragment(u))
            if found:
                break
    # cap
    return list(dict.fromkeys(found))[:cap]

async def discover_with_homepage(client: httpx.AsyncClient, base_url: str, cap: int) -> List[str]:
    html = await fetch_text(client, base_url)
    if not html:
        return [base_url]
    soup = BeautifulSoup(html, "lxml")
    links = []
    for a in soup.find_all("a", href=True):
        u = to_abs(base_url, a.get("href"))
        if not u:
            continue
        u = strip_fragment(u)
        if same_domain(base_url, u):
            links.append(u)
    # Always include base
    links.insert(0, base_url)
    # de-dupe + cap
    uniq = list(dict.fromkeys(links))
    return uniq[:cap]

async def discover_pages(base_url: str, max_pages: int) -> List[str]:
    # Normalize base URL
    if not base_url.startswith(("http://", "https://")):
        base_url = "https://" + base_url

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        urls = await discover_with_sitemap(client, base_url, max_pages)
        if not urls:
            urls = await discover_with_homepage(client, base_url, max_pages)
    return urls

async def fetch_and_extract(url: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    try:
        r = await client.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        html = r.text
        return extract_page(url, html)
    except Exception as e:
        return {"url": url, "error": str(e)}

async def audit_site(url: str, max_pages: int = MAX_PAGES_DEFAULT) -> Dict[str, Any]:
    pages = await discover_pages(url, max_pages)
    sem = asyncio.Semaphore(CONCURRENCY)
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        async def bound(u: str):
            async with sem:
                return await fetch_and_extract(u, client)
        results = await asyncio.gather(*[bound(u) for u in pages])

    audited = [r for r in results if "error" not in r]
    errors  = [r for r in results if "error" in r]

    # Aggregate site-level signals (language mix, NAP presence, schema types, duplicates, etc.)
    langs = {}
    schema_types = {}
    for p in audited:
        lg = p.get("lang")
        if lg:
            langs[lg] = langs.get(lg, 0) + 1
        for it in p.get("schema", []):
            t = it.get("@type") or it.get("type") or it.get("og:type")
            if isinstance(t, list):
                for tt in t:
                    schema_types[tt] = schema_types.get(tt, 0) + 1
            elif isinstance(t, str):
                schema_types[t] = schema_types.get(t, 0) + 1

    return {
        "site": url,
        "pages_discovered": len(pages),
        "pages_audited": len(audited),
        "languages_detected": langs,
        "schema_types_detected": schema_types,
        "pages": audited,
        "errors": errors,
    }

