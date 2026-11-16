# Water Check — architektura (wersja 1.0)

Opis kodu w pakiecie `watercheck/`. Stan projektu i wyniki: `docs/STAN_I_PLAN.md`; zmiany wersji: `CHANGELOG.md`.

## 1. Przepływ

```text
wodowskazy (IMGW, SYKE, SMHI, Hub'Eau, ARPA Lombardia) ─┐
                                                        ├─▶ data/ (małe pliki, stan potoku) ─▶ miary ─▶ docs/showcase/
Sentinel-1 RTC (Planetary Computer, katalog STAC) ──────┘                                              │
                                                                            GitHub Pages (panel) ◀─────┘
```

Przebieg uruchamia GitHub Actions dwa razy dziennie (07:20 i 15:20 UTC) (`.github/workflows/monitor.yml`). Przebieg jest przyrostowy:
scena policzona raz nie jest pobierana ponownie, więc zwykły dzień to kilka minut. Po przebiegu automat zapisuje
zmiany w `data/` i `docs/showcase/` do repozytorium. To samo polecenie działa lokalnie: `gwl water-check run`.

## 2. Moduły

| Moduł | Odpowiedzialność |
|---|---|
| `waterbodies.csv` | Rejestr akwenów: prostokąt, rozdzielczość siatki, sezon bez lodu, wodowskaz i jego źródło, klasa `expected` |
| `sources/s1.py` | Sceny Sentinel-1 RTC: wyszukiwanie w katalogu STAC, stała siatka UTM akwenu, odczyt fragmentu sceny (pasmo VH, dB) |
| `sources/imgw.py`, `syke.py`, `smhi.py`, `hubeau.py`, `lombardia.py` | Dobowy poziom wody z jednego źródła; wspólna kontrola jakości w `sources/__init__.py` |
| `core.py` | Strefa akwenu, próg Otsu, powierzchnia wody, flagi scen, prosta powierzchnia → poziom, miary i werdykt |
| `pipeline.py` | Aktualizacja plików stanu akwenu, miary, bramka jakości; `run` i `render` |
| `publish.py` | Panel HTML (dane w środku pliku), dane JSON, punkty mapy (GeoJSON), stan przebiegu |
| `selftest.py` | Test bez sieci: testy jednostkowe, kontrola rejestru i protokołu, cały potok na syntetycznym jeziorze |
| `config.py` | Ustawienia w jednym miejscu; wartości metody pochodzą z protokołu W1 |

Nowy kraj to nowy plik w `sources/` z funkcją `daily(station_id, start, end)` i nowe wiersze w `waterbodies.csv`.

## 3. Pliki stanu (jeden zestaw na akwen)

| Plik | Zawartość |
|---|---|
| `data/levels/<id>.csv` | date, level_cm |
| `data/scenes/<id>.csv` | scene, date, orbit, platform, valid, area_km2, thr_db, contrast_db, core_db, flag |
| `data/zones/<id>.npz` | strefa akwenu i rdzeń wody na stałej siatce, wyznaczone raz z lat 2022–2023 |

Flagi scen: `ok`, `partial` (scena nie pokrywa akwenu), `low_contrast` (wiatr, deszcz, lód), `no_zone`.
Do miar wchodzą tylko sceny `ok` z poziomem wodowskazu z tego samego dnia.

## 4. Bramka jakości

Publikacja jest wstrzymana (kod wyjścia 2, panel bez zmian), gdy aktualizacja nie powiodła się dla więcej niż 40% akwenów.
Pojedynczy akwen z błędem nie zatrzymuje pozostałych; jego identyfikator pojawia się w panelu jako nieodświeżony.
Każdy nieudany przebieg w GitHub Actions zakłada zgłoszenie (issue) albo dopisuje komentarz do otwartego.
Pierwszy udany przebieg sam zamyka to zgłoszenie z komentarzem.

## 5. Wynik (`docs/showcase/`)

| Plik | Dla kogo |
|---|---|
| `watercheck_panel.html` | panel publiczny (GitHub Pages); działa też otwarty z dysku |
| `watercheck_data.json` | te same dane dla notatnika na blog |
| `map_points.geojson` | punkty dla mapy na stronie geoworldlook (ostatni poziom, ostatnia powierzchnia, werdykt) |
| `status.json` | stan ostatniego przebiegu i podsumowanie werdyktów |

## 6. Testy

`python -m watercheck selftest` (około minuty, bez sieci): próg Otsu, flagi, okresy, kalibracja po torach, werdykty,
cztery układy pliku archiwum IMGW, kontrola jakości poziomu, suma kontrolna protokołu, cały potok na syntetycznym
jeziorze (rekonstrukcja, przebieg przyrostowy bez ponownego odczytu scen, bramka jakości).
CI uruchamia linter, ten test oraz budowę obrazu Dockera przy każdej zmianie kodu.

## 7. Uwaga o szybkości

Odczyt jednej sceny trwa około sekundy. Równoległe wątki w jednym procesie spowalniały odczyt kilkukrotnie,
dlatego sceny czytamy po kolei. Pełną rekonstrukcję można przyspieszyć, uruchamiając kilka procesów z rozłącznymi
listami akwenów (`--only ID ...`).
