# optimizer.py — language-agnostic auto-fixes using page's own text (EU-ready)
from typing import Dict, Any, List, Union
import re, json
from langdetect import detect, DetectorFactory
DetectorFactory.seed = 0

# ---------------- helpers ----------------

def _first(v):
    if isinstance(v, list):
        for x in v:
            if isinstance(x, str) and x.strip():
                return x.strip()
        return ""
    return v.strip() if isinstance(v, str) else ""

def _title(p): return _first(p.get("title") or p.get("meta_title") or "")
def _desc(p):  return _first(p.get("description") or p.get("meta") or p.get("meta_description") or "")
def _h1(p):
    h1 = p.get("h1")
    if isinstance(h1, str) and h1.strip(): return h1.strip()
    if isinstance(h1, list) and h1: return _first(h1)
    headers = p.get("headers") or {}
    for k in ("h1","H1"):
        v = headers.get(k)
        if isinstance(v, list) and v: return _first(v)
        if isinstance(v, str) and v.strip(): return v.strip()
    return ""

def _wc(p):
    n = p.get("word_count")
    if isinstance(n, (int,float)): return int(n)
    body = p.get("body_text") or p.get("text") or p.get("content") or ""
    return len(str(body).split())

def _shorten_ascii(s: str, n: int) -> str:
    """Trim to n chars; use '...' (ASCII) for ellipsis."""
    if len(s) <= n:
        return s
    # leave room for '...'
    if n >= 3:
        return s[:n-3].rstrip() + "..."
    return s[:n]

def _brand_guess(pages: List[Dict[str,Any]]) -> str:
    # 1) sitename/hostname if present
    for p in pages:
        site = _first(p.get("sitename") or p.get("hostname"))
        if site:
            return site
    # 2) last token of first title
    titles = [_title(p) for p in pages if _title(p)]
    if titles:
        parts = re.split(r"\s*[|\-–]\s*", titles[0])
        if len(parts) > 1:
            return parts[-1].strip()
    return ""

def _normalize_keyword_token(x: Union[str, list, tuple, dict]) -> str:
    """
    Accepts formats like:
      "detailing"
      ["detailing", 16] or [16, "detailing"]
      {"keyword":"detailing"} / {"text":"detailing"} / {"token":"detailing"} / {"word":"detailing"}
    Returns clean string or "".
    """
    if isinstance(x, str):
        return x.strip()
    if isinstance(x, (list, tuple)):
        # choose the string element if present
        for y in x:
            if isinstance(y, str) and y.strip():
                return y.strip()
        return ""
    if isinstance(x, dict):
        for k in ("keyword", "text", "token", "word"):
            v = x.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()
    return ""

def _keywords_norm(p: Dict[str,Any]) -> List[str]:
    raw = p.get("keywords") or []
    out = []
    if isinstance(raw, list):
        for x in raw:
            s = _normalize_keyword_token(x)
            if s:
                out.append(s)
    return out

def _slug_keyword(url: str) -> str:
    # last path segment as keyword-ish
    try:
        path = url.split("://", 1)[-1].split("/", 1)[-1]
        seg = path.strip("/").split("/")[-1]
        seg = seg.replace("-", " ").strip()
        return seg
    except Exception:
        return ""

def _primary_kw(p: Dict[str,Any]) -> str:
    kws = _keywords_norm(p)
    if kws:
        return kws[0]
    url = p.get("url") or ""
    slug = _slug_keyword(url)
    if slug:
        return slug
    t = _title(p)
    if t:
        return re.split(r"\s*[|\-–]\s*", t)[0].strip()
    return ""

def _detect_lang_from_text(text: str) -> str:
    try:
        return detect(text) if text.strip() else ""
    except Exception:
        return ""

def _filename_from_src(src: str) -> str:
    try:
        tail = src.split("?")[0].split("#")[0].rsplit("/", 1)[-1]
        name = tail.rsplit(".", 1)[0]
        name = name.replace("-", " ").replace("_", " ")
        return name.strip()
    except Exception:
        return ""

def _suggest_alt_text(img: Dict[str, Any], primary_kw: str, brand: str, page_h1: str) -> str:
    base = _filename_from_src(str(img.get("src") or ""))
    key = primary_kw or page_h1 or base
    key = key.strip()
    if not key:
        return "Descriptive image of the page topic."
    # Compose concise, readable ALT (ASCII-only kept by not adding special chars)
    if brand and brand.lower() not in key.lower():
        return _shorten_ascii(f"{key} | {brand}", 100)
    return _shorten_ascii(key, 100)

def _needs_slug_improvement(url: str) -> bool:
    try:
        path = url.split("://", 1)[-1].split("/", 1)[-1]
        seg = path.strip("/").split("/")[-1]
        if not seg:
            return False
        # Heuristics: very long, contains query-like tokens, or numeric gibberish
        if len(seg) > 60:
            return True
        if any(tok in seg for tok in ["?", "&", "=", ","]):
            return True
        if sum(ch.isdigit() for ch in seg) > max(6, len(seg) // 3):
            return True
        return False
    except Exception:
        return False

def _slugify(text: str) -> str:
    s = re.sub(r"[^A-Za-z0-9\-\s]", "", text.strip())
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-").lower()
    return s

# ---------- language prompts for FAQ (very small built-in map) ----------
FAQ_PROMPTS = {
    "en": ("What is {x}?", "How much does {x} cost?"),
    "lt": ("Kas yra {x}?", "Kiek kainuoja {x}?"),
    "lv": ("Kas ir {x}?", "Cik maksā {x}?"),
    "et": ("Mis on {x}?", "Kui palju maksab {x}?"),
    "pl": ("Co to jest {x}?", "Ile kosztuje {x}?"),
    "de": ("Was ist {x}?", "Wie viel kostet {x}?"),
    "fr": ("Qu'est-ce que {x} ?", "Combien coûte {x} ?"),
    "es": ("¿Qué es {x}?", "¿Cuánto cuesta {x}?"),
    "it": ("Che cos'è {x}?", "Quanto costa {x}?"),
    "nl": ("Wat is {x}?", "Wat kost {x}?"),
    "pt": ("O que é {x}?", "Quanto custa {x}?"),
    "ro": ("Ce este {x}?", "Cât costă {x}?"),
    "cs": ("Co je {x}?", "Kolik stojí {x}?"),
    "sk": ("Čo je {x}?", "Koľko stojí {x}?"),
    "hu": ("Mi az a {x}?", "Mennyibe kerül a {x}?"),
    "el": ("Τι είναι το {x};", "Πόσο κοστίζει το {x};"),
    "da": ("Hvad er {x}?", "Hvad koster {x}?"),
    "sv": ("Vad är {x}?", "Vad kostar {x}?"),
    "fi": ("Mikä on {x}?", "Kuinka paljon {x} maksaa?"),
    "ie": ("What is {x}?", "How much does {x} cost?"),  # IE=en
    "mt": ("X'inhu {x}?", "Kemm jiswa {x}?"),
    "bg": ("Какво е {x}?", "Колко струва {x}?"),
    "hr": ("Što je {x}?", "Koliko košta {x}?"),
    "sl": ("Kaj je {x}?", "Koliko stane {x}?"),
}

def _faq_prompts_for_lang(lang: str, x: str) -> List[Dict[str,str]]:
    a, b = FAQ_PROMPTS.get(lang[:2], FAQ_PROMPTS["en"])
    return [{"q": a.format(x=x), "a": "Add a concise answer in the site's language."},
            {"q": b.format(x=x), "a": "Add a pricing note and call to action in the site's language."}]

# ---------- builders (ASCII only for safety) ----------

def _make_title(primary_kw: str, brand: str) -> str:
    base = primary_kw.strip() if primary_kw else (brand or "Home")
    if brand and brand.lower() not in base.lower():
        draft = f"{base} | {brand}"
    else:
        draft = base
    return _shorten_ascii(draft, 60)

def _make_meta(existing_desc: str, title_like: str, brand: str) -> str:
    if existing_desc:
        d = existing_desc.strip()
        if len(d) < 50:
            d = (d + " " + title_like).strip()
        return _shorten_ascii(d, 160)
    msg = f"{title_like} - {brand}" if brand else title_like
    if len(msg) < 50:
        msg += "."
    return _shorten_ascii(msg, 160)

def _make_h1(primary_kw: str, title_like: str) -> str:
    h = primary_kw.strip() if primary_kw else re.split(r"\s*[|\-–]\s*", title_like)[0].strip()
    return _shorten_ascii(h, 70)

# ---------------- main optimize ----------------

def optimize_site(audit: Dict[str, Any], limit: int = 10, detail: bool = True) -> Dict[str, Any]:
    pages = audit.get("pages") or [audit]
    # Filter out non-dict pages and ensure all are dictionaries
    pages = [p for p in pages if isinstance(p, dict)]
    pages_sorted = sorted(pages, key=lambda p: _wc(p), reverse=True)
    if limit and limit > 0:
        pages_sorted = pages_sorted[:limit]

    brand = _brand_guess(pages_sorted)
    out = []

    for p in pages_sorted:
        url = p.get("url", "")
        title = _title(p)
        desc  = _desc(p)
        h1    = _h1(p)
        wc    = _wc(p)

        lang = _detect_lang_from_text(f"{title} {desc}") or "en"
        primary_kw = _primary_kw(p)

        # build only when needed; otherwise keep current
        new_title = title if (1 <= len(title) <= 60) else _make_title(primary_kw or title, brand)
        new_meta  = desc  if (50 <= len(desc)  <= 160) else _make_meta(desc, title or new_title, brand)
        new_h1    = h1    if (len(h1) > 0 and len(h1) <= 70) else _make_h1(primary_kw, title or new_title)

        # FAQ (minimal, localized prompts)
        faq = _faq_prompts_for_lang(lang, primary_kw or new_h1 or new_title)
        faq_schema = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {"@type": "Question","name": faq[0]["q"],"acceptedAnswer":{"@type":"Answer","text": faq[0]["a"]}},
                {"@type": "Question","name": faq[1]["q"],"acceptedAnswer":{"@type":"Answer","text": faq[1]["a"]}},
            ],
        }

        # ALT text suggestions for images without alt
        images = p.get("images") or []
        alt_suggestions: List[Dict[str, str]] = []
        for img in images:
            if not (img.get("alt") or "").strip():
                suggestion = _suggest_alt_text(img, primary_kw, brand, new_h1)
                alt_suggestions.append({
                    "src": str(img.get("src") or ""),
                    "suggested_alt": suggestion
                })

        # LocalBusiness schema if NAP hints present
        nap = p.get("nap") or {}
        phone = nap.get("phone") or ""
        address = nap.get("address") or ""
        local_business_schema = None
        if phone or address:
            local_business_schema = {
                "@context": "https://schema.org",
                "@type": "LocalBusiness",
                "name": brand or new_h1 or new_title,
                "telephone": phone or "",
                "address": {"@type": "PostalAddress", "streetAddress": address or ""},
                "url": url,
            }

        # Product schema: heuristic trigger on URL/keywords
        product_schema = None
        blob = (" ".join(_keywords_norm(p)) + " " + (url or "")).lower()
        if any(tok in blob for tok in ["/product", "/products", "product", "shop", "price"]):
            product_schema = {
                "@context": "https://schema.org",
                "@type": "Product",
                "name": primary_kw or new_h1 or new_title,
                "brand": brand or "",
                "description": new_meta,
                "offers": {
                    "@type": "Offer",
                    "priceCurrency": "EUR",
                    "price": "0.00",
                    "availability": "https://schema.org/InStock"
                }
            }

        # Slug suggestion
        slug_suggestion = None
        if _needs_slug_improvement(url):
            base_kw = primary_kw or new_h1 or new_title
            slug_suggestion = _slugify(base_kw)[:80] if base_kw else None

        out.append({
            "url": url,
            "language": lang,
            "word_count": wc,
            "current_title": title,
            "current_meta": desc,
            "current_h1": h1,
            "suggestions": {
                "new_title": new_title,
                "new_meta": new_meta,
                "new_h1": new_h1,
                "faq": faq,
                "faq_schema_jsonld": json.dumps(faq_schema, ensure_ascii=False, indent=2),
                "local_business_schema_jsonld": json.dumps(local_business_schema, ensure_ascii=False, indent=2) if local_business_schema else None,
                "product_schema_jsonld": json.dumps(product_schema, ensure_ascii=False, indent=2) if product_schema else None,
                "alt_text_suggestions": alt_suggestions,
                "slug_suggestion": slug_suggestion,
            },
        })

    # Site-wide Organization schema
    site_schema = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": brand or "",
    }

    return {"brand_guess": brand, "site_schema_jsonld": json.dumps(site_schema, ensure_ascii=False, indent=2), "pages_optimized": out}

