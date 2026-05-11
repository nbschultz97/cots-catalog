# Adding parts

```bash
architect-companion-ingest https://radiomasterrc.com/products/rp1-expresslrs-2-4ghz-nano-receiver
```

The ingester emits a JSON part dict to stdout. Three parsers, tried in
order:

1. **JSON-LD Product schema** — what Shopify stores ship by default.
2. **OpenGraph meta tags** — fallback for non-Shopify storefronts.
3. **`from_specs()`** — pass a hand-curated dict for everything else.

## Adding to the bundled catalog

1. Run the ingester on the manufacturer URL.
2. Inspect `_extraction.missing_fields` — fill those by hand.
3. Drop the `_extraction` key.
4. Append to the right category in `data/parts_library.json`.
5. Run `python -m pytest -q tests/test_catalog_quality.py` to verify.
6. PR with the source URL in the description.

## ToS note

Target manufacturer pages (T-Motor, iFlight, EMAX, Lumenier, RadioMaster,
BetaFPV, Holybro, Tattu, Caddx, Foxeer, RunCam, Walksnail). Do not point
the ingester at retailers whose terms forbid automated access.
