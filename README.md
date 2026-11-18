# AmanRoid expert-curated security advisories

This public repository contains the reviewed, Arabic-first security advisory
feed consumed by AmanRoid. It is a static GitHub Pages site: there is no mobile
user account, backend, database, Firebase integration, automated AI agent, or
paid AI service.

- Website: <https://basheeralduwairi.github.io/amanroid-advisories/>
- JSON feed: <https://basheeralduwairi.github.io/amanroid-advisories/advisories.json>
- Country manifest: <https://basheeralduwairi.github.io/amanroid-advisories/countries.json>
- Jordan country feed: <https://basheeralduwairi.github.io/amanroid-advisories/feeds/jo.json>
- Security data manifest: <https://basheeralduwairi.github.io/amanroid-advisories/security/security-data-manifest.json>
- URL indicators: <https://basheeralduwairi.github.io/amanroid-advisories/security/url-indicators.json>
- Official directory manifest: <https://basheeralduwairi.github.io/amanroid-advisories/directory/manifest.json>
- Jordan official directory: <https://basheeralduwairi.github.io/amanroid-advisories/directory/jo.json>
- Emergency guidance manifest: <https://basheeralduwairi.github.io/amanroid-advisories/emergency/manifest.json>
- Schema: `schema.json`

The production feed currently contains only the four Jordan advisories that were
explicitly reviewed and approved. The local candidate file supplied by research
is not copied into this public repository; deferred, rejected, and withdrawn
records remain outside the public feed.

## Multi-country coverage

`countries.json` is a schema-validated public manifest for the 22 supported
Arab countries. Jordan is the only country with active local coverage at
initialization. The other country feeds are valid empty feeds with
`coming_soon` coverage and do not claim that the country is monitored.
`feeds/regional.json` is reserved for expert-reviewed advisories that apply to
more than one country.

## Offline URL security data

The public security directory is deliberately conservative. `url-indicators.json`
currently contains an accurate empty list; no synthetic or unreviewed malicious
domains are published. Future entries require an approved permanent ID, an
HTTPS evidence source, a confidence level, observation and review dates, and an
explicit non-withdrawn approval. `trusted-organizations.json` is a separate
reviewed registry used to prioritize brand-impersonation checks; it does not
declare an official website safe. The mobile app keeps the last-known-good
security data locally and rejects malformed, oversized, stale, withdrawn, or
unapproved indicators.

The Android application consumes the manifest over HTTPS, validates relative
feed paths against this GitHub Pages origin, and keeps separate last-known-good
caches for the manifest, each local country feed, and the regional feed.
`advisories.json` remains unchanged as the backward-compatible Jordan endpoint
for installed versions before multi-country support. Run the synchronization
script whenever the approved Jordan feed changes:

```bash
python3 scripts/sync_country_feeds.py --write --updated-at 2026-11-18T00:00:00Z
python3 scripts/validate_multicountry.py
```

The official directory and emergency datasets follow the same conservative
publication rule. Jordan initially contains only the six organizations already
present in the reviewed trusted-organization registry; phone numbers, email
addresses, application IDs, and social accounts remain empty until each is
independently verified. The other 21 country datasets are valid empty
`coming_soon` documents. The emergency endpoint currently publishes generic
playbook metadata and no unverified contact numbers.

Validate these contracts with:

```bash
python3 scripts/validate_directory.py
python3 scripts/validate_emergency.py
```

## Publication procedure

1. Research the incident manually using official and independently corroborated
   sources. Preserve original URLs, publication dates, and an evidence summary.
2. Keep the candidate JSON outside this repository and run:

   ```bash
   python3 scripts/validate_candidate.py /path/to/candidates.json
   python3 scripts/compare_feed.py /path/to/candidates.json
   ```

3. A cybersecurity expert reviews the exact permanent ID, classification,
   status, dates, recommendations, and sources. The expert must make an
   explicit command-line approval decision; there is no automatic approval.
4. Before publishing, the candidate must contain a real `published_at` UTC
   timestamp and remain a `draft`. Then run, once per approved ID:

   ```bash
   python3 scripts/publish_approved.py \
     --candidates /path/to/candidates.json \
     --approve AMANROID-2026-11-001 \
     --reviewer "Reviewer name"
   python3 scripts/validate_feed.py
   git diff -- advisories.json
   ```

5. Commit the approved feed change and open a pull request. GitHub Actions must
   pass before merging to `main`. The Pages deployment runs only after the
   validation workflow succeeds.

6. To correct an advisory, withdraw it explicitly and preserve the record in a
   non-public editorial log outside the repository:

   ```bash
   python3 scripts/withdraw.py --id AMANROID-2026-11-001 \
     --log /secure/editorial/withdrawn.json --reason "Reason"
   ```

`review_status` must be `approved` for every public record. Draft, rejected, and
withdrawn records never belong in `advisories.json`.

## Validation commands

```bash
python3 -m pip install -r requirements-dev.txt
python3 scripts/validate_feed.py
python3 scripts/validate_multicountry.py
python3 scripts/check_review_due.py
python3 -m unittest discover -s tests -v
```

The validator enforces the JSON Schema, unique permanent IDs, approved-only
publication, bounded strings, UTC chronology, at least one HTTPS source, safe
source URLs, defanged indicators, no executable HTML, and a 1 MiB maximum feed.
All rendered website values are treated as untrusted text.

## Manual review guide

See [`prompts/manual_research_ar.md`](prompts/manual_research_ar.md) and
[`prompts/manual_research_en.md`](prompts/manual_research_en.md). The review
guide distinguishes confirmed Jordan incidents from global threats that may be
relevant to Jordan and prohibits claims unsupported by the sources.
