# Contributing to Architect Companion MCP

Thanks for considering a contribution. Three things make this catalog
useful: **clean code**, **honest data**, and **clear scope**. Please
keep those in mind.

## Quick start (dev setup)

```bash
git clone https://github.com/nbschultz97/cots-catalog.git
cd cots-catalog
python -m venv .venv
.venv\Scripts\activate              # Windows PowerShell
# source .venv/bin/activate         # macOS / Linux
pip install -e ".[dev]"
python -m pytest -q
```

You should see all tests pass before making changes.

## Ways to contribute

### Adding parts to the catalog

The catalog is the heart of the project. Quality matters more than
volume — a small library of authoritative entries beats a thousand
half-filled ones.

**Process:**

1. Find the part on a **manufacturer page** (iFlight, T-Motor, EMAX,
   Lumenier, Happymodel, RadioMaster, BetaFPV, Holybro, Tattu, etc.).
   Do **not** scrape retailers whose ToS forbid automated access.
2. Try the ingester first:
   ```bash
   architect-companion-ingest <manufacturer-product-url>
   ```
3. Hand-fill any fields the parser couldn't extract — `weight_g`, KV,
   voltage range, etc. The `_extraction.missing_fields` list tells you
   what's missing.
4. Add the entry to the right category list in
   `data/parts_library.json`. Every part **must** include:
   - A unique `id` in the form `{category-prefix}-{slug}` (e.g.,
     `motor-iflight-xing2-2207-1750kv`).
   - A `data_source` block: `{url, fetched_at, parser}`.
   - All schema-required fields for that category.
5. Run `python -m pytest -q tests/test_catalog_quality.py`. The test
   will fail if your entry is missing required fields, has a duplicate
   ID, or fails the JSON Schema validation.
6. Open a PR. In the description, include the source URL and a one-line
   reason for the addition.

### Adding compatibility rules

Compatibility rules in `src/architect_companion_mcp/compatibility.py`
are coarse engineering sanity checks, not electrical engineering. New
rules need:

- A clear physical or operational reason (cite the source if it's
  community lore — e.g., "FPV builder rule of thumb that 2200KV+ on
  7\" props burns out").
- Test coverage in `tests/test_server.py` that exercises both the
  positive (rule fires correctly) and negative (rule doesn't false-positive)
  cases.
- A README update under "Known limitations" if the rule introduces a
  new heuristic boundary.

### Adding mission presets

Presets live in `data/preset_*.json` and follow the MissionProject v2
schema. Constraints:

- **Hobby / commercial only.** No military framing, no
  mil-doctrine-coded scenarios. See `data/preset_long_range_relay.json`
  for the tone we want.
- Include realistic team roles, phases, RF environment, and constraints.
- Don't reference real units, customers, or operational locations.

### Adding compute tiers

`COMPUTE_TIERS` in `recommend.py` maps a tier name to a weight and
airframe tag bias. New tiers need to ship with at least one
representative compute platform (Pi, Jetson, RockchipNPU, etc.) — and
the underlying assumption is that the catalog has airframes whose
payload budget can carry the tier weight.

## Scope: what belongs here

**In scope:**

- COTS sUAS parts catalog (FPV, fixed-wing, multirotor, fixed-install).
- Compatibility sanity checks for hobby / commercial builders.
- Mission blueprint stubs (race, freestyle, long-range, mapping, etc.).
- LLM-friendly tooling over the catalog.

**Out of scope:**

- Flight simulation or aerodynamic modeling. The endurance tool is a
  one-line approximation and stays that way.
- Regulatory / airspace / NOTAM checks. Use FAA B4UFLY or your local
  authority.
- Military / defense framing. This project is hobby-marketable, and
  PRs that add military mission types, NSN fields, or doctrine
  references will be redirected.
- Auto-purchasing or retailer integration. Stay catalog-only.

## Code style

- Python 3.9+. Stdlib preferred; new dependencies need justification.
- Type hints on public functions.
- Docstrings explain **why**, not what.
- Tests for any public function with non-trivial behavior.
- No emoji in code or docs unless the user requests it.

## Pull request checklist

- [ ] Tests pass locally: `python -m pytest -q`
- [ ] Catalog quality test passes if you added parts:
      `python -m pytest -q tests/test_catalog_quality.py`
- [ ] New parts have `data_source` provenance.
- [ ] No mil / CUI / customer-identifying language.
- [ ] README / CHANGELOG updated if behavior changed.
- [ ] Commit message uses Conventional Commits (`feat:`, `fix:`,
      `docs:`, `refactor:`, `test:`).

Thanks for helping.
