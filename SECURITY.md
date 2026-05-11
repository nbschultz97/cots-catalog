# Security policy

## Supported versions

The latest minor release (`0.x`) gets security updates. Older minor
releases do not.

| Version | Supported |
|---------|-----------|
| 0.6.x   | yes       |
| 0.5.x   | no        |
| < 0.5   | no        |

## Reporting a vulnerability

If you find a security issue (path traversal in the ingester, code
execution via crafted catalog data, dependency CVE, etc.), please
**do not** open a public issue.

Instead, email `noah@ceradonsystems.com` with:

- A clear description of the issue.
- Steps to reproduce.
- The impact you believe it has.

You'll get an acknowledgement within 7 days. If the report is valid,
we'll work on a fix and coordinate a public disclosure with you.

## Out of scope

- The compatibility engine is a **sanity-check**, not safety-critical.
  Wrong recommendations are not security vulnerabilities — they're
  data-quality issues, which belong in normal issues / PRs.
- The endurance tool is documented as a hover approximation. Inaccurate
  endurance numbers are not security issues.
- This project is hobby / commercial sUAS — not a regulated medical /
  aviation / defense product. Treat its outputs accordingly.

## Catalog data integrity

Every part in the bundled catalog carries a `data_source` provenance
block (`url`, `fetched_at`, `parser`). If you find an entry with bad
data, please open a regular issue with the corrected values and the
manufacturer URL that supports the correction.
