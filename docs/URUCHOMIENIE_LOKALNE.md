# Water Check — uruchomienie

Water Check działa sam: GitHub Actions uruchamia przebieg dwa razy dziennie (07:20 i 15:20 UTC) i sam publikuje panel.
Ta instrukcja jest potrzebna tylko wtedy, gdy chcesz uruchomić coś ręcznie.

## 1. Jedno polecenie

Z folderu `GeoWorldLook` na pulpicie:

```bash
scripts\gwl.cmd water-check test
```

```bash
scripts\gwl.cmd water-check run
```

`test` sprawdza kod bez sieci (około minuty). `run` robi to samo co automat: dopisuje nowe poziomy z wodowskazów,
liczy powierzchnię wody dla nowych scen radarowych i przelicza panel.

## 2. Wszystkie polecenia

| Polecenie | Co robi |
|---|---|
| `python -m watercheck run` | przebieg przyrostowy (tylko nowe sceny) |
| `python -m watercheck run --only PL-SIEM FI-LOKK` | to samo dla wybranych akwenów |
| `python -m watercheck backfill` | rekonstrukcja od 2022 od zera (około 2 godzin; szybciej w kilku procesach z `--only`) |
| `python -m watercheck render` | panel z zapisanych plików, bez sieci |
| `python -m watercheck publish` | commit i push `data/` oraz `docs/showcase/` |
| `python -m watercheck selftest` | testy bez sieci |
| `python -m watercheck settings` | ustawienia i stan ostatniego przebiegu |

Środowisko: conda `watercheck` (`environment.yml`). Na tym komputerze polecenia uruchamiaj przez `gwl` albo
`conda run -n watercheck ...`; sam `python.exe` ze środowiska bez aktywacji kończy obliczenia bez komunikatu.

## 3. Gdzie są wyniki

- Panel publiczny: https://geoworldlook.github.io/water-check/showcase/watercheck_panel.html
- Panel na dysku: `projects/water-check/docs/showcase/watercheck_panel.html` (otwiera się bez serwera)
- Stan ostatniego przebiegu lokalnego: `projects/water-check/data/logs/last_run.json`
- Historia przebiegów automatu: zakładka Actions w repozytorium, zadanie `monitor`

## 4. Gdy coś nie działa

| Objaw | Co to znaczy | Co zrobić |
|---|---|---|
| W panelu napis „Not updated in the last run” | jeden akwen nie odświeżył się (np. API wodowskazu nie odpowiadało) | poczekać do następnego przebiegu |
| Kod wyjścia 2, napis „bramka jakości” | błąd w więcej niż 40% akwenów; panel celowo bez zmian | sprawdzić log; zwykle to chwilowy brak sieci |
| Zgłoszenie „Monitor run failed” w repozytorium | przebieg automatu się nie udał | zwykle nic: następny udany przebieg sam zamknie zgłoszenie; gdy wisi dłużej niż dobę, otworzyć log z linku |
| Odczyt scen kończy się błędem dostępu | usługa Planetary Computer zmieniła zasady dostępu | przejść na Copernicus Data Space (nowy plik w `sources/`) |
| Zimą nie przybywa scen | to normalne: poza sezonem bez lodu sceny nie są liczone | nic; poziomy z wodowskazów dopisują się dalej |

## 5. Nowy akwen

1. Dopisz wiersz do `watercheck/waterbodies.csv`: prostokąt, rozdzielczość, sezon, wodowskaz i jego źródło, klasa `expected`.
2. Uruchom `python -m watercheck run --only <ID>`. Pierwszy przebieg wyznaczy strefę z lat 2022–2023 i policzy wszystkie sceny.
3. Klasę `expected` wpisz przed liczeniem. Nowy akwen nie zmienia werdyktów już policzonych.
