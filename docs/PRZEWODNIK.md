# Water Check — przewodnik krok po kroku

Ten dokument prowadzi przez jeden akwen i jedną scenę radarową, od pobrania danych do liczby na panelu.
Przy każdym kroku jest plik z kodem, w którym ten krok się dzieje.

## 1. Co system sprawdza

Radar satelity Sentinel-1 nie mierzy poziomu wody. Widzi powierzchnię: gładka woda odbija sygnał w bok i na obrazie
jest ciemna, a ląd jest jasny. Gdy poziom w płytkim zbiorniku rośnie, woda zalewa brzegi i ciemna plama się powiększa.

Water Check odpowiada na pytanie: czy ta zmiana powierzchni zgadza się z tym, co mierzy wodowskaz na brzegu?

## 2. Jeden akwen od początku do końca

Przykład: Zbiornik Siemianówka (`PL-SIEM`). Kroki są w `watercheck/pipeline.py`, w funkcji `process`.

### Krok 1. Poziom z wodowskazu (`sources/imgw.py`)

- Pobieramy dobowy poziom wody w centymetrach.
- Kontrola jakości odrzuca wartości oczywiście błędne, na przykład zero wpisane zamiast braku danych.
- Wynik: `data/levels/PL-SIEM.csv`.

### Krok 2. Lista scen radarowych (`sources/s1.py`, funkcja `search`)

- Pytamy katalog STAC o wszystkie sceny Sentinel-1 nad prostokątem zbiornika od 2022 roku.
- Zostają tylko miesiące sezonu bez lodu (kolumny `season_from`, `season_to` w rejestrze).

### Krok 3. Odczyt fragmentu sceny (`sources/s1.py`, funkcja `read_db`)

- Scena ma około 250 km szerokości, a my czytamy tylko prostokąt zbiornika. Format COG na to pozwala.
- Wszystkie sceny trafiają na tę samą stałą siatkę (20 m), więc piksele z różnych dni leżą w tym samym miejscu.
- Wartości przeliczamy na decybele. Woda ma około −25 dB, ląd około −14 dB.

### Krok 4. Strefa zbiornika (`core.py`, funkcja `build_zone`)

- Z najwyżej 60 scen z lat 2022–2023 wybieramy piksele, które bywały ciemne. To największy zasięg wody.
- Doliczamy pas brzegu 160 m, żeby w strefie była i woda, i ląd.
- Strefę wyznaczamy raz i zapisujemy w `data/zones/PL-SIEM.npz`.

### Krok 5. Powierzchnia wody w scenie (`core.py`, funkcja `scene_area`)

- Wewnątrz strefy dzielimy piksele na ciemne i jasne progiem Otsu. Próg sam znajduje granicę między dwiema grupami.
- Liczba ciemnych pikseli razy powierzchnia piksela to powierzchnia wody w km².
- Wiatr marszczy wodę i ją rozjaśnia. Gdy różnica woda–ląd jest mniejsza niż 6 dB, scena dostaje flagę `low_contrast`.
- Wynik: jeden wiersz w `data/scenes/PL-SIEM.csv`.

### Krok 6. Powierzchnia → poziom (`core.py`, funkcje `calibrate` i `predict`)

- Satelita przelatuje różnymi torami i patrzy pod różnym kątem. Ten sam zbiornik ma wtedy trochę inną powierzchnię.
- Dlatego dla każdego toru osobno dopasowujemy prostą: poziom = a + b · powierzchnia. Tylko na latach 2022–2023.

### Krok 7. Miary i werdykt (`core.py`, funkcje `evaluate` i `verdict`)

Na latach testowych 2024–2025, których kalibracja nie widziała:

| Miara | Co mówi | Próg |
|---|---|---|
| ρ (korelacja rang) | czy większa powierzchnia idzie w parze z wyższym poziomem | co najmniej 0,7 |
| Błąd poziomu | o ile centymetrów myli się poziom odtworzony z powierzchni | najwyżej 25% zakresu poziomu |
| Zmienność powierzchni | dla jezior kontrolnych: czy radar nie pokazuje zmian, których nie ma | najwyżej 5% |

Werdykt: `confirmed` (oba progi), `partly` (jeden), `not confirmed` (żaden); dla jezior kontrolnych `stable` albo `unstable`.

## 3. Po co są jeziora kontrolne

Jezioro o stromych brzegach prawie nie zmienia powierzchni, nawet gdy poziom się waha. Jeśli radar pokazuje tam duże
zmiany, to znaczy, że metoda sama je wytwarza (wiatr, roślinność, szum). Jezioro kontrolne to test, czy system
nie widzi czegoś, czego nie ma.

## 4. Trzy okresy

| Okres | Lata | Status |
|---|---|---|
| Kalibracja | 2022–2023 | dopasowanie strefy i prostej; wynik opisowy |
| Test | 2024–2025 | werdykt według protokołu W1, zapisanego przed policzeniem tych lat |
| Na żywo | od 2026 | te same reguły, raportowane osobno |

Protokół (`docs/evidence/W1_protokol_powierzchnia_poziom.md`) ma sumę kontrolną w kodzie. Test `selftest` nie przejdzie,
jeśli ktoś zmieni protokół po fakcie.

## 5. Jak sprawdzić, że rozumiesz

Otwórz `data/scenes/PL-SIEM.csv` i `data/levels/PL-SIEM.csv`. Wybierz jeden tor (kolumna `orbit`) i sceny z flagą `ok`
z jednego roku. Narysuj powierzchnię wobec poziomu z tego samego dnia. Punkty powinny układać się wzdłuż rosnącej linii,
tym wyraźniej, im bardziej zmieniał się poziom.
