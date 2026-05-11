from __future__ import annotations

import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
os.environ.setdefault("ARCHITECT_DATA_DIR", str(REPO_ROOT / "data"))

from architect_companion_mcp.ingest import (
    _coerce_price,
    _coerce_weight_g,
    _extract_jsonld_products,
    _extract_meta,
    from_specs,
    from_url,
)

JSONLD_FIXTURE = """
<html>
<head>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "Test 2207 Motor",
  "brand": {"@type": "Brand", "name": "TestBrand"},
  "sku": "TB-2207-1900",
  "description": "A test motor.",
  "image": ["https://example.com/motor.jpg"],
  "offers": {
    "@type": "Offer",
    "price": "23.99",
    "priceCurrency": "USD",
    "availability": "https://schema.org/InStock"
  }
}
</script>
<meta property="og:title" content="Test 2207 Motor">
<meta property="og:image" content="https://example.com/motor.jpg">
</head>
<body>Stub</body>
</html>
"""

META_ONLY_FIXTURE = """
<html>
<head>
<meta property="og:title" content="OpenGraph-only Receiver">
<meta property="og:description" content="ELRS receiver.">
<meta property="og:image" content="https://example.com/rx.jpg">
<meta property="product:price:amount" content="18.99">
</head>
<body></body>
</html>
"""

NO_STRUCTURED_FIXTURE = """
<html><body><p>Plain HTML, no structure.</p></body></html>
"""


def test_coerce_weight_g_handles_grams_and_kg():
    assert _coerce_weight_g("34g") == 34.0
    assert _coerce_weight_g("0.034 kg") == pytest.approx(34.0)
    assert _coerce_weight_g("Weight: 31.8g") == 31.8
    assert _coerce_weight_g(45) == 45.0
    assert _coerce_weight_g(None) is None


def test_coerce_price_strips_currency():
    assert _coerce_price("$23.99") == 23.99
    assert _coerce_price("1,299.00") == 1299.0
    assert _coerce_price(None) is None
    assert _coerce_price("not-a-price") is None


def test_extract_jsonld_finds_product():
    products = _extract_jsonld_products(JSONLD_FIXTURE)
    assert len(products) == 1
    assert products[0]["name"] == "Test 2207 Motor"
    assert products[0]["offers"]["price"] == "23.99"


def test_extract_meta_collects_og():
    meta = _extract_meta(META_ONLY_FIXTURE)
    assert meta["og:title"] == "OpenGraph-only Receiver"
    assert meta["product:price:amount"] == "18.99"


def test_from_url_jsonld_path():
    part = from_url("https://example.com/motor", html=JSONLD_FIXTURE)
    assert part["name"] == "Test 2207 Motor"
    assert part["manufacturer"] == "TestBrand"
    assert part["part_number"] == "TB-2207-1900"
    assert part["cost_usd"] == 23.99
    assert part["availability"] == "in-stock"
    assert part["data_source"]["parser"] == "jsonld"
    assert part["data_source"]["url"] == "https://example.com/motor"


def test_from_url_falls_back_to_opengraph():
    part = from_url("https://example.com/rx", html=META_ONLY_FIXTURE)
    assert part["name"] == "OpenGraph-only Receiver"
    assert part["cost_usd"] == 18.99
    assert part["data_source"]["parser"] in {"opengraph", "jsonld"}  # jsonld misses, then og fills
    assert part["_extraction"]["jsonld_products_found"] == 0


def test_from_url_reports_missing_fields_when_no_structure():
    part = from_url("https://example.com/blank", html=NO_STRUCTURED_FIXTURE)
    assert "weight_g" in part["_extraction"]["missing_fields"]
    assert "cost_usd" in part["_extraction"]["missing_fields"]
    assert part["data_source"]["parser"] == "none"


def test_from_specs_normalizes_and_attaches_provenance():
    part = from_specs(
        "motors",
        {
            "id": "motor-test-2207-1900",
            "name": "Test Motor",
            "weight_g": "32g",
            "cost_usd": "$24.99",
            "kv": 1900,
        },
        url="https://example.com/motor",
    )
    assert part["weight_g"] == 32.0
    assert part["cost_usd"] == 24.99
    assert part["data_source"]["parser"] == "from_specs"
    assert part["data_source"]["url"] == "https://example.com/motor"
    assert part["availability"] == "in-stock"


def test_from_specs_rejects_bad_category():
    with pytest.raises(ValueError):
        from_specs("widgets", {"name": "junk"})
