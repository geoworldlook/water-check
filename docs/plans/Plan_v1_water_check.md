# Plan v1 — Water Check

Status: WDROŻONY 2026-11-15 (kroki W1–W7), decyzje D-096, D-097, D-099, D-100, D-103, D-104.

## 1. Pytanie i odbiorca

Czy radar Sentinel-1 widzi zmiany poziomu wody w zbiorniku? Radar mierzy powierzchnię wody, więc sprawdzamy, czy
zmiana powierzchni idzie w parze ze zmianą poziomu z wodowskazu i z jakim błędem da się odtworzyć poziom.
Odbiorca: gospodarka wodna, energetyka wodna, osoby budujące usługi z danych satelitarnych.

## 2. Zasady

- **Prosto:** jedna strefa akwenu, jeden próg, jedna prosta na tor orbity.
- **Automatycznie:** przebieg codzienny w GitHub Actions, przyrostowy, bez komputera autora.
- **Modułowo:** `waterbodies.csv`, `sources/`, `core.py`, `publish.py`. Nowy kraj to nowy plik w `sources/`.
- **Od 2022 (D-097):** 2022–2023 kalibracja, 2024–2025 test według protokołu zapisanego wcześniej, od 2026 na żywo.

## 3. Kroki i kryteria akceptacji

| Krok | Co | Kryterium akceptacji | Stan |
|---|---|---|---|
| W1 | Rejestr akwenów i wodowskazów | każdy akwen ma źródło poziomu z historią od 2022 | zrobione: 10 akwenów (Łebsko usunięte, D-104) |
| W2 | Źródła poziomu: IMGW, SYKE, SMHI, Hub'Eau, ARPA Lombardia | dobowy szereg dla każdego akwenu | zrobione (Lombardia do 2025-01-01) |
| W3 | Czytnik Sentinel-1 i powierzchnia wody | odczyt fragmentu sceny na stałą siatkę; test bez sieci | zrobione |
| W4 | Protokół zapisany; kalibracja 2022–2023; test 2024–2025 | wyniki H-W1–H-W3, także negatywne | zrobione: 2 confirmed, 1 partly, 4 not confirmed; 3 stable |
| W5 | Panel i dane do publikacji | panel otwiera się bez serwera | zrobione |
| W6 | Automat: Docker, GitHub Actions, alarm, CI | kolejne przebiegi bez ręcznej poprawki | w toku od 2026-11-15 |
| W7 | README (EN), dokumentacja (PL), przewodnik, wersja 1.0.0 | README pozwala uruchomić projekt jednym poleceniem | zrobione |

## 4. Decyzje

- **D-096:** Water Check jest projektem nr 4.
- **D-097:** podział lat: kalibracja, test, na żywo.
- **D-099:** Sentinel-1 RTC z Planetary Computer, pasmo VH; zapas: Copernicus Data Space.
- **D-100:** stan potoku w repozytorium (`data/`), wynik w `docs/showcase/`, przebieg w GitHub Actions.
- **D-103:** przebieg codzienny i przyrostowy zamiast tygodniowego: odczyty wodowskazów są świeże każdego dnia.
- **D-104:** Jezioro Łebsko usunięte z rejestru po przebiegu, bo prostokąt objął Bałtyk.

## 5. Ryzyka

- Metoda potwierdziła się tylko na dużych, płytkich zbiornikach. To wynik, nie błąd wdrożenia.
- Planetary Computer może zmienić zasady dostępu. Zapas: Copernicus Data Space albo własne przetwarzanie scen.
- API wodowskazów zmieniają format (IMGW zmieniał układ pliku co rok). Stąd jeden plik na źródło i testy formatów.
