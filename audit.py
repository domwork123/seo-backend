# audit.py
import asyncio
import httpx
import re
from urllib.parse import urljoin, urlparse, urldefrag
from bs4 import BeautifulSoup
from w3lib.html import get_base_url
import tldextract
import json
from typing import List, Dict, Any, Set, Tuple, Optional
import lxml.html
import lxml.etree
import extruct

DEFAULT_TIMEOUT = 15
MAX_CONCURRENCY = 8
IMG_HEAD_LIMIT = 20      # HEAD at most N images per page for bytes
LINK_CHECK_LIMIT = 100   # HEAD/GET at most N internal links per page

_phone_re = re.compile(r"(?:\+\d{1,3}\s?)?(?:\(?\d{1,4}\)?[\s.-]?)\d{3,4}[\s.-]?\d{3,4}")
# simple address words common in EU languages (very rough, just to surface something)
_address_hint_re = re.compile(r"\b(street|str\.|ul\.|avenue|ave\.|road|rd\.|g\.)\b|\b(Vilnius|Kaunas|Rīga|Riga|Tallinn|Warsaw|Warszawa|Kraków|Praha|Praague|Berlin|Munich|Paris|Lyon|Madrid|Barcelona|Lisboa|Lisbon|Roma|Milano|Amsterdam|Rotterdam|Brussels|Antwerpen)\b", re.I)

_question_re = re.compile(r"^\s*(who|what|when|where|why|how|can|does|do|is|are|should|which|kada|kaip|kodėl|kas|ar|kur)\b.*\?\s*$", re.I)
_q_prefix_re = re.compile(r"^\s*(Q:|Question:|FAQ:)", re.I)
_a_prefix_re = re.compile(r"^\s*(A:|Answer:)", re.I)

HEADERS = {
    "User-Agent": "AscentIQAuditBot/1.0 (+https://tryevika.com; contact: audit@tryevika.com)"
}

def _norm(u: str) -> str:
    return urldefrag(u.strip())[0]

def _same_site(seed: str, other: str) -> bool:
    a, b = tldextract.extract(seed), tldextract.extract(other)
    return (a.domain, a.suffix) == (b.domain, b.suffix)

async def _fetch(client: httpx.AsyncClient, url: str, method: str = "GET", **kw):
    try:
        if method == "GET":
            return await client.get(url, **kw)
        else:
            return await client.head(url, **kw)
    except Exception:
        return None

async def _get_sitemap_urls(client: httpx.AsyncClient, root: str) -> List[str]:
    urls = set()
    for path in ("/sitemap.xml", "/sitemap_index.xml"):
        resp = await _fetch(client, urljoin(root, path))
        if resp and resp.status_code == 200 and "xml" in resp.headers.get("content-type", ""):
            try:
                tree = lxml.etree.fromstring(resp.content)
            except Exception:
                continue
            # handle index + urlset
            locs = tree.findall(".//{*}loc")
            for loc in locs:
                if loc.text:
                    u = _norm(urljoin(root, loc.text))
                    if _same_site(root, u):
                        urls.add(u)
            # If it was an index, locs may point to more sitemaps
            # already added above
            break
    return list(urls)

def _extract_schema(html: str, url: str) -> Dict[str, Any]:
    try:
        data = extruct.extract(
            html,
            base_url=url,
            syntaxes=["json-ld", "microdata", "opengraph", "rdfa"],
            errors="ignore",
        )
        # keep lightweight
        return {
            "json_ld": data.get("json-ld", []),
            "microdata": data.get("microdata", []),
            "opengraph": data.get("opengraph", []),
            "rdfa": data.get("rdfa", []),
        }
    except Exception:
        return {"json_ld": [], "microdata": [], "opengraph": [], "rdfa": []}

def _extract_meta(soup: BeautifulSoup) -> Tuple[Optional[str], Optional[str]]:
    title = (soup.title.string or "").strip() if soup.title and soup.title.string else None
    desc = None
    md = soup.find("meta", attrs={"name": "description"})
    if md and md.get("content"):
        desc = md["content"].strip()
    return title, desc

def _get_text(soup: BeautifulSoup) -> str:
    for tag in soup(["script", "style", "noscript", "template"]):
        tag.extract()
    return soup.get_text(" ", strip=True)

def _extract_headings(soup: BeautifulSoup) -> Tuple[List[str], List[str], List[str]]:
    h1 = [t.get_text(strip=True) for t in soup.find_all("h1")]
    h2 = [t.get_text(strip=True) for t in soup.find_all("h2")]
    h3 = [t.get_text(strip=True) for t in soup.find_all("h3")]
    return h1, h2, h3

def _extract_lang(soup: BeautifulSoup) -> Optional[str]:
    html = soup.find("html")
    if html and html.get("lang"):
        return html["lang"].strip()
    return None

def _extract_canonical_robots_hreflang(soup: BeautifulSoup) -> Tuple[Optional[str], Optional[str], List[Dict[str, str]]]:
    canonical = None
    mr = None
    hreflang = []
    for l in soup.find_all("link"):
        rel = " ".join((l.get("rel") or [])).lower()
        if "canonical" in rel and l.get("href"):
            canonical = l["href"].strip()
        if l.get("rel") and "alternate" in [r.lower() for r in l["rel"]] and l.get("hreflang") and l.get("href"):
            hreflang.append({"hreflang": l["hreflang"], "href": l["href"].strip()})
    meta_robots = soup.find("meta", attrs={"name": re.compile(r"robots", re.I)})
    if meta_robots and meta_robots.get("content"):
        mr = meta_robots["content"].strip()
    return canonical, mr, hreflang

def _extract_images(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    out = []
    for img in soup.find_all("img"):
        out.append({
            "src": img.get("src") or "",
            "alt": (img.get("alt") or "").strip(),
            "loading": (img.get("loading") or "").strip().lower(),
            "width": img.get("width"),
            "height": img.get("height"),
        })
    return out

def _extract_links(soup: BeautifulSoup, base: str, seed: str) -> Tuple[List[str], List[str]]:
    internal, external = [], []
    for a in soup.find_all("a", href=True):
        href = _norm(urljoin(base, a["href"]))
        if href.startswith("mailto:") or href.startswith("tel:") or href.startswith("javascript:"):
            continue
        if _same_site(seed, href):
            internal.append(href)
        else:
            external.append(href)
    # de-dup
    internal = list(dict.fromkeys(internal))
    external = list(dict.fromkeys(external))
    return internal, external

def _faq_from_headings(h2: List[str], h3: List[str], all_text: str) -> List[Dict[str, str]]:
    faqs = []
    # Q? pattern in headings
    for h in (h2 + h3):
        if _question_re.search(h) or _q_prefix_re.search(h):
            faqs.append({"question": h, "answer": ""})
    # Q:/A: pairs in text
    lines = [ln.strip() for ln in all_text.splitlines() if ln.strip()]
    for i, ln in enumerate(lines):
        if _q_prefix_re.search(ln) or _question_re.search(ln):
            # capture next non-empty as answer if prefixed with A: or just next line
            ans = ""
            if i + 1 < len(lines):
                nxt = lines[i + 1]
                if _a_prefix_re.search(nxt):
                    ans = _a_prefix_re.sub("", nxt).strip()
                else:
                    ans = nxt.strip()
            q = _q_prefix_re.sub("", ln).strip()
            faqs.append({"question": q, "answer": ans})
    # de-dup by question text
    seen = set()
    uniq = []
    for item in faqs:
        q = item["question"]
        if q and q.lower() not in seen:
            seen.add(q.lower())
            uniq.append(item)
    return uniq[:25]

async def _head_image_bytes(client: httpx.AsyncClient, srcs: List[str]) -> Dict[str, Optional[int]]:
    out = {}
    tasks = []
    for s in srcs[:IMG_HEAD_LIMIT]:
        tasks.append(_fetch(client, s, method="HEAD", headers=HEADERS, timeout=DEFAULT_TIMEOUT))
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    for s, resp in zip(srcs[:IMG_HEAD_LIMIT], responses):
        size = None
        if hasattr(resp, "headers"):
            cl = resp.headers.get("content-length")
            if cl and cl.isdigit():
                size = int(cl)
        out[s] = size
    return out

async def _check_links(client: httpx.AsyncClient, links: List[str]) -> Dict[str, int]:
    out = {}
    tasks = []
    for u in links[:LINK_CHECK_LIMIT]:
        tasks.append(_fetch(client, u, method="HEAD", headers=HEADERS, timeout=DEFAULT_TIMEOUT))
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    for u, resp in zip(links[:LINK_CHECK_LIMIT], responses):
        code = None
        if hasattr(resp, "status_code"):
            code = resp.status_code
        out[u] = code
    return out

async def _read_robots(client: httpx.AsyncClient, root: str) -> Dict[str, Any]:
    robots_url = urljoin(root, "/robots.txt")
    resp = await _fetch(client, robots_url)
    rules = {"raw": "", "disallow": [], "sitemaps": []}
    if resp and resp.status_code == 200:
        body = resp.text
        rules["raw"] = body
        for line in body.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.lower().startswith("disallow:"):
                rules["disallow"].append(line.split(":", 1)[1].strip())
            if line.lower().startswith("sitemap:"):
                rules["sitemaps"].append(line.split(":", 1)[1].strip())
    return rules

def _is_blocked_by_robots(path: str, disallow_rules: List[str]) -> bool:
    # naive path-startswith matcher
    for rule in disallow_rules:
        if not rule:
            continue
        if path.startswith(rule):
            return True
    return False

async def analyze_page(client: httpx.AsyncClient, url: str, seed: str) -> Dict[str, Any]:
    resp = await _fetch(client, url, headers=HEADERS, timeout=DEFAULT_TIMEOUT)
    status = resp.status_code if resp else None
    headers = dict(resp.headers) if resp else {}
    html = resp.text if (resp and resp.text) else ""
    base = get_base_url(html, url)
    soup = BeautifulSoup(html, "lxml")

    title, meta = _extract_meta(soup)
    h1, h2, h3 = _extract_headings(soup)
    lang = _extract_lang(soup)
    canonical, meta_robots, hreflang = _extract_canonical_robots_hreflang(soup)
    schema = _extract_schema(html, url)

    images = _extract_images(soup)
    internal_links, external_links = _extract_links(soup, base, seed)
    text = _get_text(soup)
    word_count = len(text.split())

    # FAQ heuristics
    faq = _faq_from_headings(h2, h3, text)

    # performance-ish: html bytes + image bytes (HEAD)
    html_bytes = len(html.encode("utf-8"))
    img_srcs = [urljoin(base, i["src"]) for i in images if i.get("src")]
    img_bytes_map = await _head_image_bytes(client, img_srcs)
    for img in images:
        src_abs = urljoin(base, img.get("src") or "")
        img["bytes"] = img_bytes_map.get(src_abs)

    # link health (internal)
    link_status = await _check_links(client, internal_links)
    broken_internal = [u for u, code in link_status.items() if code and code >= 400]

    # accessibility: missing alt
    missing_alt = sum(1 for i in images if not i.get("alt"))

    # header X-Robots-Tag
    x_robots_tag = headers.get("x-robots-tag")

    # NAP (very rough)
    phone = None
    addr = None
    m = _phone_re.search(html)
    if m:
        phone = m.group(0)
    if _address_hint_re.search(html):
        # try to capture a reasonably sized window around match
        addr = _address_hint_re.search(html).group(0)

    page = {
        "url": url,
        "status": status,
        "title": title,
        "meta": meta,
        "h1": h1,
        "h2": h2,
        "h3": h3,
        "lang": lang,
        "canonical": canonical,
        "meta_robots": meta_robots,
        "x_robots_tag": x_robots_tag,
        "hreflang": hreflang,
        "images": images,
        "links": {
            "internal": internal_links,
            "external": external_links,
            "broken_internal": broken_internal,
        },
        "schema": schema,
        "faq": faq,
        "nap": {"phone": phone, "address": addr},
        "a11y": {"images_missing_alt": missing_alt},
        "performance_hints": {
            "html_bytes": html_bytes,
            "images_total_bytes_sampled": sum([b or 0 for b in img_bytes_map.values()]),
            "images_with_lazy": sum(1 for i in images if i.get("loading") == "lazy"),
            "images_missing_dimensions": sum(1 for i in images if not (i.get("width") and i.get("height"))),
        },
        "word_count": word_count,
        "headers": {k.lower(): v for k, v in headers.items() if k.lower().startswith("content-") or k.lower().startswith("x-robots")},
    }
    return page

async def audit_site(seed_url: str, max_pages: int = 50) -> Dict[str, Any]:
    try:
        seed_url = _norm(seed_url)
        parsed = urlparse(seed_url)
        root = f"{parsed.scheme}://{parsed.netloc}"
        visited: Set[str] = set()
        queue: List[str] = []

        async with httpx.AsyncClient(follow_redirects=True, timeout=DEFAULT_TIMEOUT, headers=HEADERS) as client:
        # robots
        robots = await _read_robots(client, root)
        disallow = robots.get("disallow", [])

        # sitemap
        sm_urls = await _get_sitemap_urls(client, root)
        # if empty, start from homepage
        if not sm_urls:
            sm_urls = [seed_url]

        # keep only same-site, http(s)
        seeds = []
        for u in sm_urls:
            pu = urlparse(u)
            if pu.scheme in ("http", "https") and _same_site(seed_url, u):
                seeds.append(_norm(u))
        queue.extend(list(dict.fromkeys(seeds)))

        pages: List[Dict[str, Any]] = []
        broken_site_links: Set[str] = set()

        sem = asyncio.Semaphore(MAX_CONCURRENCY)

        async def _worker():
            while queue and len(visited) < max_pages:
                url = queue.pop(0)
                if url in visited:
                    continue
                visited.add(url)
                # skip obviously blocked paths (naive)
                path = urlparse(url).path or "/"
                if _is_blocked_by_robots(path, disallow):
                    pages.append({"url": url, "status": None, "blocked_by_robots": True})
                    continue

                async with sem:
                    page = await analyze_page(client, url, seed_url)
                    pages.append(page)

                    # enqueue new internal links (from page) if we didn't start from sitemap-only scenario
                    for nxt in page.get("links", {}).get("internal", []):
                        if len(visited) + len(queue) >= max_pages:
                            break
                        if nxt not in visited and nxt not in queue and _same_site(seed_url, nxt):
                            queue.append(nxt)

                    # accumulate broken links
                    for b in page.get("links", {}).get("broken_internal", []):
                        broken_site_links.add(b)

        workers = [asyncio.create_task(_worker()) for _ in range(min(MAX_CONCURRENCY, 4))]
        await asyncio.gather(*workers)

    # site-level rollups
    discovered = len(pages)
    langs = list({p.get("lang") for p in pages if p.get("lang")})
    canonicals = sum(1 for p in pages if p.get("canonical"))
    pages_with_index_noindex = {
        "index": sum(1 for p in pages if p.get("meta_robots") and "index" in p["meta_robots"].lower()),
        "noindex": sum(1 for p in pages if p.get("meta_robots") and "noindex" in p["meta_robots"].lower()),
    }
    pages_blocked_by_robots = sum(1 for p in pages if p.get("blocked_by_robots"))

    # site-wide hreflang map
    hreflang_pairs = []
    for p in pages:
        for h in p.get("hreflang", []):
            hreflang_pairs.append({"page": p["url"], "hreflang": h["hreflang"], "href": h["href"]})
    # simple a11y: total missing alt
    total_missing_alt = sum(p.get("a11y", {}).get("images_missing_alt", 0) for p in pages if p.get("a11y"))

    audit = {
        "url": seed_url,
        "pages_discovered": discovered,
        "languages": langs,
        "pages_with_canonical": canonicals,
        "robots": robots,
        "pages_blocked_by_robots": pages_blocked_by_robots,
        "meta_robots_summary": pages_with_index_noindex,
        "broken_internal_links_unique": sorted(list(broken_site_links)),
        "a11y_summary": {"images_missing_alt_total": total_missing_alt},
        "pages": pages,
    }
    return audit
    
    except Exception as e:
        print(f"DEBUG: Audit failed for {seed_url}: {e}")
        # Return minimal audit data to prevent complete failure
        return {
            "url": seed_url,
            "pages_discovered": 1,
            "languages": ["en"],
            "pages_with_canonical": 0,
            "robots": {"raw": "", "disallow": [], "sitemaps": []},
            "pages_blocked_by_robots": 0,
            "meta_robots_summary": {"index": 0, "noindex": 0},
            "broken_internal_links_unique": [],
            "a11y_summary": {"images_missing_alt_total": 0},
            "pages": [{
                "url": seed_url,
                "status": 200,
                "title": "",
                "meta": "",
                "h1": [],
                "h2": [],
                "h3": [],
                "lang": "en",
                "canonical": seed_url,
                "meta_robots": None,
                "x_robots_tag": None,
                "hreflang": [],
                "images": [],
                "links": {"internal": [], "external": [], "broken_internal": []},
                "schema": {"json_ld": [], "microdata": [], "opengraph": [], "rdfa": []},
                "faq": [],
                "nap": {"phone": "", "address": ""},
                "a11y": {"images_missing_alt": 0},
                "performance_hints": {"html_bytes": 0, "images_total_bytes_sampled": 0, "images_with_lazy": 0, "images_missing_dimensions": 0},
                "word_count": 0,
                "headers": {}
            }],
            "error": f"Audit failed: {str(e)}"
        }

