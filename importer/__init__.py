"""IMAP email import pipeline (Phase 2).

Will connect to configured mailboxes (IMAP IDLE + polling fallback), watch
folders across multiple users/mailboxes, and hand raw messages to the
``tracking``/merchant parser plugins for shipment detection.
"""
