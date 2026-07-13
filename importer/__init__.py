"""IMAP email import pipeline.

Connects to configured mailboxes (IMAP IDLE + polling fallback via
``imap_client``), and hands raw messages to the pluggable merchant parsers in
``importer.parsers`` for shipment/order detection. Contains no database or
web-framework dependency - the backend's ``EmailIngestionService`` is what
persists the results.
"""
