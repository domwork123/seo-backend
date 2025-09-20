# scoring.py — Europe-ready, language/GEO aware, multi-page scoring (ASCII messages)
from typing import Dict, Any, List, Tuple
from collections import Counter
from langdetect import detect, DetectorFactory
import re, json, tldextract

DetectorFactory.seed = 0  # stable language detection

EU_TLD_TO_COUNTRY = {
    "at":"Austria","be":"Belgium","bg":"Bulgaria","hr":"Croatia","cy":"Cyprus","cz":"Czechia",
    "dk":"Denmark","ee":"Estonia","fi":"Finland","fr":"France","de":"Germany","gr":"Greece",
    "hu":"Hungary","ie":"Ireland","it":"Italy","lv":"Latvia","lt":"Lithuania","lu":"Luxembourg",
    "mt":"Malta","nl":"Netherlands","pl":"Poland","pt":"Portugal","ro":"Romania","sk":"Slovakia",
    "si":"Slovenia","es":"Spain","se":"Sweden","gb":"United Kingdom"
}

# capitals + a few big cities per country (lowercased)
EU_CITY_SET = set(map(str.lower, [
    "vienna","linz","graz","brussels","antwerp","sofia","plovdiv","zagreb","split",
    "nicosia","prague","brno","copenhagen","aarhus","tallinn","helsinki","tampere",
    "paris","lyon","marseille","berlin","munich","hamburg","athens","thessaloniki",
    "budapest","dublin","rome","milan","naples","riga","vilnius","kaunas","luxembourg",
    "valletta","amsterdam","rotterdam","eindhoven","warsaw","krakow","wroclaw","lisbon","porto",
    "bucharest","cluj","bratislava","kosice","ljubljana","madrid","barcelona","valencia",
    "stockholm","gothenburg","malmo","london","manchester","birmingham"
]))

# ---------------- helpers ----------------
def _safe_list(x): return x if isinstance(x, list) else ([] if x is None else [x])

def _first_text(v):
    if isinstance(v, list):
        for x in v:
            if isinstance(x, str) and x.strip(): return x.strip()
        return ""
    return v.strip() if isinstance(v, str) else ""

def _get_h1(page: Dict[str, Any]) -> str:
    headers = page.get("headers") or {}
    h1 = page.get("h1")
    if isinstance(h1, str) and h1.strip(): return h1.strip()
    if isinstance(h1, list) and h1: return _first_text(h1)
    for key in ("h1", "H1"):
        v = headers.get(key)
        if isinstance(v, list) and v: return _first_text(v)
        if isinstance(v, str) and v.strip(): return v.strip()
    return ""

def _word_count(page: Dict[str, Any]) -> int:
    wc = page.get("word_count")
    if isinstance(wc, (int, float)): return int(wc)
    body = page.get("body_text") or page.get("text") or page.get("content") or ""
    return len(str(body).split())

def _title(page: Dict[str, Any]) -> str:
    return _first_text(page.get("title") or page.get("meta_title") or "")

def _meta_desc(page: Dict[str, Any]) -> str:
    return _first_text(page.get("description") or page.get("meta") or page.get("meta_description") or "")

def _warnings(page: Dict[str, Any]) -> List[str]:
    return [str(w) for w in page.get("warnings", [])]

def _keywords(page: Dict[str, Any]) -> List[str]:
    kws = page.get("keywords") or []
    return [k for k in kws if isinstance(k, str)]

def _is_https(url: str) -> bool:
    return bool(url) and url.lower().startswith("https://")

def _alt_missing(warns: List[str]) -> bool:
    s = " | ".join(warns).lower()
    return any(p in s for p in ["missing alt","image missing alt","img missing alt"])

def _og_missing(warns: List[str]) -> Tuple[bool,bool,bool]:
    s = " | ".join(warns).lower()
    return ("missing og:title" in s, "missing og:description" in s, "missing og:image" in s)

def _viewport_missing(warns: List[str]) -> bool:
    s = " | ".join(warns).lower()
    return "missing viewport" in s or "no viewport" in s

def _links_guess(page: Dict[str, Any]) -> int:
    for k in ("internal_links","internal_links_count","links_count"):
        v = page.get(k)
        if isinstance(v, int): return v
    return sum(1 for w in _warnings(page) if "anchor" in w.lower())

def _detect_language(page: Dict[str, Any]) -> str:
    blob = " ".join([
        _title(page), _meta_desc(page), " ".join(_keywords(page))
    ]).strip()
    if not blob: return ""
    try:
        return detect(blob)
    except Exception:
        return ""

def _tld_country(url: str) -> str:
    try:
        ext = tldextract.extract(url or "")
        tld = (ext.suffix or "").split(".")[-1].lower()
        return EU_TLD_TO_COUNTRY.get(tld, "")
    except Exception:
        return ""

def _location_present(page: Dict[str, Any]) -> Tuple[bool, str, str]:
    title = _title(page)
    desc  = _meta_desc(page)
    kwstr = " ".join(_keywords(page))
    text = f"{title} {desc} {kwstr}".lower()

    city = next((c for c in EU_CITY_SET if c in text), "")
    country = _tld_country(page.get("url") or "")
    has_geo = bool(city or country)
    return has_geo, city, country

def _schema_text(page: Dict[str, Any], audit: Dict[str, Any]) -> str:
    cand = (
        page.get("schema") or page.get("schema_json") or
        audit.get("schema") or audit.get("schema_json") or
        page.get("raw_head") or audit.get("raw_head") or ""
    )
    return json.dumps(cand) if isinstance(cand, (dict, list)) else str(cand)

def _has_jsonld_types(schema_txt: str, types: List[str]) -> bool:
    s = schema_txt
    return any(f'"@type":"{t}"' in s or f'"@type": "{t}"' in s for t in types)

# --------------- page scoring ---------------
def _score_single_page(page: Dict[str, Any], audit: Dict[str, Any]) -> Tuple[int,int,List[str],List[str],Dict[str,str]]:
    seo, ai = 0, 0
    seo_tasks, ai_tasks = [], []

    url = page.get("url") or ""
    title = _title(page)
    meta  = _meta_desc(page)
    h1    = _get_h1(page)
    wc    = _word_count(page)
    warns = _warnings(page)
    https = _is_https(url)
    schema_txt = _schema_text(page, audit)
    links_guess = _links_guess(page)
    og_title_miss, og_desc_miss, og_img_miss = _og_missing(warns)

    # metadata
    lang = _detect_language(page)
    has_geo, city, country = _location_present(page)

    # ---------- SEO ----------
    if 1 <= len(title) <= 60: seo += 5
    else: seo_tasks.append("Fix title: include main keyword, keep <=60 chars.")

    if h1 and len(h1) <= 70: seo += 5
    else: seo_tasks.append("Add/shorten H1 and include main keyword.")

    if 50 <= len(meta) <= 160: seo += 5
    else: seo_tasks.append("Fix meta description: 50-160 chars, include keyword + city.")

    if wc >= 500: seo += 5
    else: seo_tasks.append(f"Add more copy (>=500 words). Current: ~{wc} words.")

    if links_guess >= 3: seo += 5
    else: seo_tasks.append("Add >=3 internal links to relevant pages.")

    if https: seo += 5
    else: seo_tasks.append("Enable HTTPS (redirect http -> https).")

    if _viewport_missing(warns):
        seo_tasks.append("Make page mobile-friendly (viewport, responsive css).")
    else:
        seo += 5

    if _alt_missing(warns):
        seo_tasks.append("Add descriptive ALT text to images.")
    else:
        seo += 5

    if not og_title_miss and not og_desc_miss and not og_img_miss:
        seo += 5
    else:
        missing = []
        if og_title_miss: missing.append("og:title")
        if og_desc_miss:  missing.append("og:description")
        if og_img_miss:   missing.append("og:image")
        seo_tasks.append(f"Add Open Graph meta tags ({', '.join(missing)}).")

    # ---------- AI / AEO + GEO ----------
    if wc >= 600 and h1:
        ai += 5
    else:
        ai_tasks.append("Add clear Q&A/FAQ or summary answers near the top.")

    has_ctx = '"@context"' in schema_txt
    has_type = '"@type"' in schema_txt
    if has_ctx and has_type:
        ai += 5
    else:
        ai_tasks.append("Add JSON-LD with @context and @type.")

    if _has_jsonld_types(schema_txt, ["FAQPage", "HowTo", "Article", "Service", "Product"]):
        ai += 5
    else:
        ai_tasks.append("Add relevant schema (FAQPage/HowTo/Service/Product/Article).")

    if has_geo:
        ai += 5
    else:
        ai_tasks.append("Mention your city/region in Title, H1, and copy.")

    # NAP/Maps inference (weak)
    if "map" in " ".join(warns).lower():
        ai_tasks.append("Embed Google Maps pin on contact/hero area.")
    else:
        if not og_img_miss and has_geo:
            ai += 5
        else:
            ai_tasks.append("Embed Google Maps pin and ensure NAP (name, address, phone) is visible.")

    # Reviews
    blob = " ".join(_keywords(page) + warns).lower()
    if any(tok in blob for tok in ["review","reviews","testimonials","★★★★★","bewertung","avis","opinie","recensies","reseñas"]):
        ai += 5
    else:
        ai_tasks.append("Show 2-3 short customer reviews/testimonials with stars.")

    if not (og_title_miss or og_desc_miss):
        ai += 5
    else:
        if og_title_miss or og_desc_miss:
            ai_tasks.append("Add OG title/description for better previews/snippets.")

    meta_out = {"language": lang or "", "city": city or "", "country": country or ""}
    return seo, ai, seo_tasks, ai_tasks, meta_out

# --------------- site-level scoring (weighted) ---------------
def score_website(audit: Dict[str, Any], detail: bool = False) -> Dict[str, Any]:
    """Takes a full audit dict (with pages[]) and returns aggregated SEO + AI scores."""
    if not isinstance(audit, dict):
        return {"error": "Invalid audit: expected dict"}

    pages: List[Dict[str, Any]] = audit.get("pages") or []
    if not pages:
        if "url" in audit:  # single page fallback
            pages = [audit]
        else:
            return {"error": "Audit has no pages"}

    total_wc = 0
    weighted_seo = 0.0
    weighted_ai = 0.0
    seo_task_counter = Counter()
    ai_task_counter = Counter()
    pages_details: List[Dict[str, Any]] = []
    langs = Counter()
    cities = Counter()
    countries = Counter()

    for page in pages:
        try:
            seo, ai, seo_tasks, ai_tasks, meta = _score_single_page(page, audit)
        except Exception:
            continue

        wc = _word_count(page)
        w = wc if wc > 0 else 1
        total_wc += w
        weighted_seo += seo * w
        weighted_ai += ai * w
        for t in seo_tasks: seo_task_counter[t] += 1
        for t in ai_tasks: ai_task_counter[t] += 1
        if meta["language"]: langs[meta["language"]] += 1
        if meta["city"]: cities[meta["city"]] += 1
        if meta["country"]: countries[meta["country"]] += 1

        if detail:
            pages_details.append({
                "url": page.get("url", ""),
                "title": _title(page),
                "word_count": wc,
                "seo_score_page": seo,
                "ai_score_page": ai,
                "language": meta["language"],
                "city": meta["city"],
                "country": meta["country"],
                "top_seo_tasks": seo_tasks[:3],
                "top_ai_tasks": ai_tasks[:3],
            })

    if total_wc == 0:
        total_wc = len(pages) or 1

    seo_score = int(round(weighted_seo / total_wc))
    ai_score = int(round(weighted_ai / total_wc))
    combined = int(round((seo_score + ai_score) / 2))

    top_seo_tasks = [f"{t} (x{c})" for t, c in seo_task_counter.most_common(25)]
    top_ai_tasks = [f"{t} (x{c})" for t, c in ai_task_counter.most_common(25)]

    result = {
        "seo_score": seo_score,
        "ai_score": ai_score,
        "combined_score": combined,
        "pages_evaluated": len(pages),
        "detected_languages": dict(langs),
        "detected_cities": dict(cities),
        "detected_countries": dict(countries),
        "seo_tasks": top_seo_tasks,
        "ai_tasks": top_ai_tasks
    }
    if detail:
        result["pages_detail"] = pages_details
    return result

