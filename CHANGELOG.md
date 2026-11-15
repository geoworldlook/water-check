# Changelog

Versions follow semantic versioning (major.minor.patch).

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
