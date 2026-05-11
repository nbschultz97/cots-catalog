"""URL → part dict ingester.

Pulls a manufacturer/retailer product page and extracts what it can into
a parts_library schema entry. Three strategies, tried in order:

1. **JSON-LD Product schema** — what Shopify stores ship by default.
   Cleanest extraction; emits name, price, image, sku, weight, etc.
2. **OpenGraph + meta tags** — most modern e-commerce surfaces these
   (``og:title``, ``og:image``, ``product:price:amount``, etc.).
3. **Caller-supplied spec dict** — for pages where neither structured
   path works, the caller passes a parsed spec dict (e.g. extracted by
   an upstream agent via WebFetch) and we normalize it into the schema.

Every returned part carries a ``data_source`` block with
``{url, fetched_at, parser}`` so the catalog is auditable.

Stdlib-only on purpose: ``urllib.request`` + ``html.parser`` + ``json`` +
``re``. No new dependencies.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional

_DEFAULT_UA = (
    "Mozilla/5.0 (compatible; architect-companion-mcp/0.5; "
    "+https://github.com/nbschultz97/cots-catalog)"
)

_JSONLD_RE = re.compile(
    r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.DOTALL | re.IGNORECASE,
)


class _MetaCollector(HTMLParser):
    """Collect ``<meta property|name=... content=...>`` tags."""

    def __init__(self) -> None:
        super().__init__()
        self.meta: Dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: List) -> None:
        if tag.lower() != "meta":
            return
        a = dict(attrs)
        key = a.get("property") or a.get("name")
        val = a.get("content")
        if key and val:
            self.meta[key.lower()] = val


def fetch_html(url: str, *, user_agent: str = _DEFAULT_UA, timeout: float = 20.0) -> str:
    """Pull a URL with a real-browser-ish User-Agent. Returns decoded HTML."""
    req = urllib.request.Request(url, headers={"User-Agent": user_agent, "Accept": "text/html"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
        # Best-effort encoding: respect Content-Type charset, fall back to utf-8.
        charset = resp.headers.get_content_charset() or "utf-8"
        return raw.decode(charset, errors="replace")


def _extract_jsonld_products(html: str) -> List[Dict[str, Any]]:
    """Return a flat list of every JSON-LD Product (or Product graph) found."""
    out: List[Dict[str, Any]] = []
    for match in _JSONLD_RE.finditer(html):
        body = match.group(1).strip()
        try:
            blob = json.loads(body)
        except json.JSONDecodeError:
            continue
        for candidate in _flatten_jsonld(blob):
            t = candidate.get("@type")
            if t == "Product" or (isinstance(t, list) and "Product" in t):
                out.append(candidate)
    return out


def _flatten_jsonld(blob: Any) -> List[Dict[str, Any]]:
    """Walk a JSON-LD graph and yield every dict node."""
    out: List[Dict[str, Any]] = []
    if isinstance(blob, dict):
        out.append(blob)
        for value in blob.values():
            out.extend(_flatten_jsonld(value))
    elif isinstance(blob, list):
        for item in blob:
            out.extend(_flatten_jsonld(item))
    return out


def _extract_meta(html: str) -> Dict[str, str]:
    parser = _MetaCollector()
    parser.feed(html)
    return parser.meta


def _coerce_price(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).replace(",", "").replace("$", "").strip()
    try:
        return float(text)
    except ValueError:
        return None


def _coerce_weight_g(value: Any) -> Optional[float]:
    """Parse weight values like '34g', '0.034 kg', 'Weight 31.8g'."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).lower()
    match = re.search(r"(\d+(?:\.\d+)?)\s*(g|gram|grams|kg|oz)?", text)
    if not match:
        return None
    qty = float(match.group(1))
    unit = (match.group(2) or "g").lower()
    if unit in {"kg"}:
        return qty * 1000.0
    if unit in {"oz"}:
        return qty * 28.3495
    return qty


def from_url(url: str, *, html: Optional[str] = None) -> Dict[str, Any]:
    """Fetch a URL (or use prefetched HTML) and return a partial part dict.

    The dict has the schema-relevant fields that could be extracted, a
    ``_extraction`` block documenting source + parser + missing fields,
    and a top-level ``data_source`` block for catalog provenance.
    """
    if html is None:
        html = fetch_html(url)

    fetched_at = datetime.now(timezone.utc).isoformat()
    products = _extract_jsonld_products(html)
    meta = _extract_meta(html)

    part: Dict[str, Any] = {}
    parser_used = "none"
    missing: List[str] = []

    if products:
        parser_used = "jsonld"
        p = products[0]
        offers = p.get("offers") or {}
        if isinstance(offers, list) and offers:
            offers = offers[0]
        part["name"] = p.get("name")
        part["manufacturer"] = (p.get("brand") or {}).get("name") if isinstance(p.get("brand"), dict) else p.get("brand")
        part["part_number"] = p.get("sku") or p.get("mpn")
        part["cost_usd"] = _coerce_price((offers or {}).get("price"))
        part["weight_g"] = _coerce_weight_g(p.get("weight"))
        if isinstance(p.get("image"), str):
            part["image"] = p["image"]
        elif isinstance(p.get("image"), list) and p["image"]:
            part["image"] = p["image"][0]
        part["description"] = p.get("description")
        availability = (offers or {}).get("availability")
        if availability and "InStock" in availability:
            part["availability"] = "in-stock"
        elif availability and "OutOfStock" in availability:
            part["availability"] = "unavailable"

    if not part.get("name"):
        og_name = meta.get("og:title") or meta.get("twitter:title")
        og_desc = meta.get("og:description") or meta.get("description")
        og_image = meta.get("og:image") or meta.get("twitter:image")
        og_price = meta.get("product:price:amount") or meta.get("og:price:amount")
        if og_name or og_desc or og_image or og_price:
            parser_used = "opengraph" if parser_used == "none" else parser_used
            part.setdefault("name", og_name)
            part.setdefault("description", og_desc)
            part.setdefault("image", og_image)
            if og_price:
                part.setdefault("cost_usd", _coerce_price(og_price))

    for required in ("name", "weight_g", "cost_usd"):
        if part.get(required) is None:
            missing.append(required)

    part["data_source"] = {
        "url": url,
        "fetched_at": fetched_at,
        "parser": parser_used,
    }
    part["_extraction"] = {
        "parser": parser_used,
        "missing_fields": missing,
        "jsonld_products_found": len(products),
        "meta_tag_count": len(meta),
    }
    return part


def from_specs(
    category: str,
    specs: Dict[str, Any],
    *,
    url: Optional[str] = None,
) -> Dict[str, Any]:
    """Normalize a hand-curated spec dict into a parts_library entry.

    Use this when neither JSON-LD nor OpenGraph give enough — pass in
    the fields you collected by other means and let the function shape
    them into the schema, attach provenance, and validate categories.
    """

    from .catalog import PART_CATEGORIES

    if category not in PART_CATEGORIES:
        raise ValueError(
            f"Unknown category '{category}'. Valid: {', '.join(PART_CATEGORIES)}"
        )

    part: Dict[str, Any] = dict(specs)
    part.setdefault("availability", "in-stock")
    if "weight_g" in part:
        part["weight_g"] = _coerce_weight_g(part["weight_g"])
    if "cost_usd" in part:
        part["cost_usd"] = _coerce_price(part["cost_usd"])

    fetched_at = datetime.now(timezone.utc).isoformat()
    part["data_source"] = {
        "url": url,
        "fetched_at": fetched_at,
        "parser": "from_specs",
    }
    return part


def main(argv: Optional[List[str]] = None) -> None:
    """CLI: python -m architect_companion_mcp.ingest <url>."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        prog="architect-companion-ingest",
        description="Ingest a product URL into a parts_library entry (JSON to stdout).",
    )
    parser.add_argument("url", help="Product URL to ingest")
    args = parser.parse_args(argv)

    try:
        part = from_url(args.url)
    except urllib.error.HTTPError as exc:
        print(f"HTTP {exc.code} fetching {args.url}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as exc:
        print(f"URL error fetching {args.url}: {exc.reason}", file=sys.stderr)
        sys.exit(1)

    json.dump(part, sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
