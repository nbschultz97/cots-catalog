"""Walk through the ingester end-to-end.

Three paths:

1. from_url() against a JSON-LD-equipped manufacturer page (Shopify).
2. from_url() against a page with only OpenGraph meta tags.
3. from_specs() for pages where the parser can't pull enough structure.

The third path is what you'll use most often — manufacturer pages vary
wildly, and hand-curating the spec dict beats fragile regex.
"""

import json

from architect_companion_mcp.ingest import from_specs, from_url

JSONLD_HTML = """
<html>
<head>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "Example 5\\\" Race Motor",
  "brand": {"@type": "Brand", "name": "ExampleCorp"},
  "sku": "EX-2207-2400KV",
  "offers": {"@type": "Offer", "price": "23.99", "availability": "https://schema.org/InStock"}
}
</script>
</head>
<body></body>
</html>
"""


def main() -> None:
    print("# 1. JSON-LD path")
    print("-" * 60)
    part = from_url("https://example.com/motor", html=JSONLD_HTML)
    print(json.dumps(part, indent=2, default=str))
    print()

    print("# 2. from_specs() — hand-curated spec dict")
    print("-" * 60)
    motor = from_specs(
        category="motors",
        specs={
            "id": "motor-example-2207-2400kv",
            "name": "Example 2207 2400KV",
            "size": "2207",
            "kv": 2400,
            "weight_g": "32g",
            "cost_usd": "$23.99",
            "max_thrust_g": 2050,
            "voltage_range": {"min_v": 11.1, "max_v": 22.2},
            "prop_size_range": "5 inch",
            "manufacturer": "ExampleCorp",
            "part_number": "EX-2207-2400KV",
            "tags": ["multi-rotor", "5-inch", "race", "example"],
        },
        url="https://example.com/motor-spec-page",
    )
    print(json.dumps(motor, indent=2, default=str))
    print()

    print("# Tip: missing fields in from_url() output show up in `_extraction.missing_fields`.")
    print("# Hand-fill those, then drop the `_extraction` key, then append to parts_library.json.")


if __name__ == "__main__":
    main()
