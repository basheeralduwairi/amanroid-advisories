# Flutter integration contract

AmanRoid reads the public feed at:

`https://basheeralduwairi.github.io/amanroid-advisories/advisories.json`

The contract is intentionally static and read-only. The mobile application does
not authenticate, upload scan results, send device identifiers, or require a
dedicated backend.

## Feed acceptance

The client accepts `schema_version: 1`, Arabic (`language: ar`), Jordan
(`country: JO`), and only `review_status: approved` advisories. Each advisory
has a permanent ID, UTC dates, enumerated category/severity/status/confidence,
at least one HTTPS source, defanged indicators, prevention guidance, and victim
actions. The client rejects malformed JSON, duplicate IDs, unsupported schema
versions, unsafe URLs, executable markup, invalid chronology, and responses
larger than 1 MiB.

## Retrieval behavior

Flutter uses a bounded HTTPS request with a 20-second response timeout and
conditional `If-None-Match`/`If-Modified-Since` headers when available. A 304
uses the validated cache. A 200 response is parsed and validated completely
before replacing the native last-known-good cache. Concurrent refresh calls
share one request. Failed requests retain cached advisories with an explicit
stale/error state; no cache is treated as an honest empty/error state, not as
proof that no threats exist.

`updated_at` is the feed publication timestamp. AmanRoid separately records the
local `lastSuccessfulAt` retrieval timestamp. Historical, resolved, and overdue
records remain visibly labelled and are not described as active merely because
they are cached.

## Source links and privacy

Feed text is rendered as plain text. Source links are opened only after an
explicit user action and native allowlist validation; the app never
automatically follows a URL from the feed. Private keys, enrollment signatures,
scan results, and personal data never enter this request or cache.
