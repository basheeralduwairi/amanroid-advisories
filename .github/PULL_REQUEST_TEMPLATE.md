## Expert advisory publication checklist

- [ ] Every record in `advisories.json` has a permanent ID and at least one credible original source.
- [ ] Original publication dates, evidence summaries, and URLs were preserved.
- [ ] Jordan-specific relevance is distinguished from global relevance.
- [ ] Historical or resolved records are not described as active incidents.
- [ ] Every public record has `review_status: approved`.
- [ ] I am the named cybersecurity reviewer, or I have obtained explicit approval from that reviewer.
- [ ] `python scripts/validate_feed.py` and the test suite pass.
- [ ] No credentials, private keys, drafts, rejected records, or personal data are included.

The public feed is deployed only after this pull request is approved and GitHub
Actions validation succeeds. A green CI run alone is not expert approval.
