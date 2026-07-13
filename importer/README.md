# importer

Phase 2. IMAP-based ingestion of shipping-confirmation emails.

Planned scope:

- IMAP IDLE with polling fallback, for Gmail, Outlook/Exchange, GMX, WEB.DE,
  Yahoo and generic IMAP servers.
- Multiple mailboxes and multiple users, each with its own folder rules.
- A pluggable merchant-parser registry (see the `merchants/` sub-package,
  added in Phase 2) so new senders (Amazon, eBay, Otto, Zalando, ...) can be
  supported by dropping in a new parser module - no changes to the core
  import loop.
- Persists ingested messages via the backend's `Email` model and hands
  detected shipments to the `tracking` package.
