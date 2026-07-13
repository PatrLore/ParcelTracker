# tracking

Provider-agnostic parcel tracking. A standalone, database-free Python
package - see `docs/architecture.md`.

## Contents

- `carriers.py` (implemented) - modular, regex-based tracking-number
  detection: DHL, DHL Express, Deutsche Post, UPS, DPD, GLS, Hermes, FedEx,
  USPS, Cainiao, YunExpress, Amazon Logistics, Royal Mail, PostNL. Used by
  `importer`'s merchant parsers since Phase 2 to guess a shipment's carrier
  from its tracking number.
- `provider.py` (interface only, Phase 3) - `TrackingProvider`
  (`register()` / `update()` / `remove()`) that every concrete tracking
  backend will implement:
  - 17TRACK
  - AfterShip
  - TrackingMore
  - Ship24
  - Direct carrier APIs

  The active provider will be selected in `config.yaml`; the rest of the
  application will depend only on the interface, never a specific vendor.

## Adding a carrier

Add one entry to `CARRIER_PATTERNS` (and to `_DETECTION_ORDER`, to resolve
ambiguity against overlapping digit-length formats) in `carriers.py`.

## Tests

```bash
cd tracking && ../backend/.venv/bin/pytest
```
