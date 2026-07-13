# tracking

Phase 3. Provider-agnostic parcel tracking.

`provider.py` defines the `TrackingProvider` interface (`register` /
`update` / `remove`) that every concrete integration implements:

- 17TRACK
- AfterShip
- TrackingMore
- Ship24
- Direct carrier APIs (DHL, UPS, DPD, GLS, ...)

The active provider is selected in `config.yaml`; the rest of the
application depends only on the interface, never a specific vendor.

Also planned for this phase: modular regex-based tracking-number detectors
per carrier (DHL, DHL Express, Deutsche Post, UPS, DPD, GLS, Hermes, FedEx,
USPS, Cainiao, YunExpress, Amazon Logistics, Royal Mail, PostNL, ...), each
implemented as an independent, pluggable matcher.
