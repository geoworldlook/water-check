# Changelog

Versions follow semantic versioning (major.minor.patch).

## 1.1.0 - 2026-11-17

- **Registry:** only water bodies with current gauge data (decision D-107). Lago d'Idro removed: its open gauge
  data end on 2025-01-01. Now 9 water bodies in 4 countries, 5,335 scenes. The unused ARPA Lombardia source is removed.
- **Method v2 (protocol W2, decision D-108):** common scale for satellite tracks, 15-day causal median of the area,
  quadratic area-to-level curve, yearly refit on all earlier years (`watercheck/series.py`). The window and the
  curve were chosen on 2022-2023 only (`notebooks/experiments/W2_wybor_metody.py`).
- **Result, reported as measured:** v2 lowers the level error on 5 of 6 water bodies in 2024-2025 (a second look,
  not an independent test). The confirmation year 2026 is negative: 0 confirmed, 2 partly, 3 not confirmed.
  Details in `docs/evidence/W2_wyniki.md`. The W1 verdicts stay the main result.
- **Panel:** two extra rows per water body (method v2) and a short explanation.
- **Self-test:** unit tests for method v2 (no look-ahead in smoothing and in the yearly refit), SHA-256 of protocol W2.

## 1.0.0 - 2026-11-15

First version, built in the GeoWorldLook project standard (decision D-096).

- **Package `watercheck`:** `python -m watercheck run | backfill | render | publish | selftest | settings`.
- **Sources:** Sentinel-1 RTC scenes from a STAC catalogue (Microsoft Planetary Computer), read as a small window
  per water body; daily gauge levels from IMGW-PIB (Poland), SYKE (Finland), SMHI (Sweden), Hub'Eau (France) and
  ARPA Lombardia (Italy).
- **Method:** fixed water zone from the calibration years, Otsu threshold inside the zone, scene flags
  (partial coverage, low contrast), area-to-level line per satellite track.
- **Reconstruction:** 5,691 scenes since 2022 for 10 water bodies; calibration 2022-2023, test 2024-2025, live from 2026.
- **Protocol W1** registered before the test years were computed; results in `docs/evidence/W1_wyniki.md`
  (2 confirmed, 1 partly, 4 not confirmed; 3 control lakes stable).
- **Registry:** 10 active water bodies; Jezioro Lebsko excluded after the run (its rectangle also covered the Baltic Sea).
- **Published result:** panel (one HTML file), data JSON, map points (GeoJSON) with the latest gauge reading and
  radar area, run status in `docs/showcase/`.
- **Automation:** daily incremental run in GitHub Actions; CI with linter, offline end-to-end test and container build.
