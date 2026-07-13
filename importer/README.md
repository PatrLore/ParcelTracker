# importer

IMAP-based ingestion of shipping-confirmation emails. A standalone,
database-free Python package - see `docs/architecture.md` for how the
backend integrates it.

## Contents

- `imap_client.py` - `ImapMailbox`: connects to any IMAP4rev1 server
  (Gmail, Outlook/Exchange, GMX, WEB.DE, Yahoo, ...), `fetch_since(uid)` for
  polling, `idle_check(...)` for IMAP IDLE (client-level support; not yet
  wired into a background runner - see `docs/roadmap.md`).
- `emails.py` - `RawEmail`, the mailbox-agnostic representation of a fetched
  message.
- `parsers/` - pluggable `MerchantParser` plugins, auto-discovered by
  `parsers/registry.py`. Currently: Amazon, eBay, Otto, MediaMarkt, Saturn,
  IKEA, Temu, Kaufland, AliExpress, Decathlon, Zalando, Alternate.

## Adding a merchant

Add a new module to `parsers/`, subclassing
`parsers._regex_parser.RegexMerchantParser` (sender-domain + regex driven -
see any existing parser) or `parsers.base.MerchantParser` directly for
unusual formats. No other file changes - the registry discovers it via
`pkgutil`.

## Tests

```bash
cd importer && ../backend/.venv/bin/pytest
```

Multiple mailboxes/multiple users are modeled by the backend's
`MailAccount` model (one row per connected mailbox); this package itself
has no notion of "users" - it only knows how to talk to one mailbox at a
time.
