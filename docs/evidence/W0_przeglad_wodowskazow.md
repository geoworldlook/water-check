# W0: przegląd wodowskazów i próba eksploracyjna

Zapis z 2026-11-14, przed protokołem W1. Wyniki z tego dokumentu są eksploracyjne.

## 1. Źródła poziomu wody

| Kraj | Źródło | Dostęp | Historia od 2022 | Uwagi |
|---|---|---|---|---|
| Polska | IMGW-PIB: archiwum dobowe i API | otwarte, bez klucza | tak (do X 2025) | archiwum roku bieżącego z opóźnieniem; układ pliku zmienia się co rok |
| Finlandia | SYKE, API OData | otwarte, bez klucza | tak | |
| Szwecja | SMHI, pliki CSV | otwarte, bez klucza | tak | pojedyncze zera zamiast braku danych (odrzuca je kontrola jakości) |
| Francja | Hub'Eau, API hydrométrie | otwarte, bez klucza | tak | wielkość HIXnJ: najwyższy stan w dobie |
| Włochy | ARPA Lombardia, API Socrata | otwarte, bez klucza | do 2025-01-01 | zbiór „Livello idrometrico dal 2021” nie ma nowszych danych |
| Szwajcaria | BAFU | dane bieżące | nie potwierdzono | odłożone |
| Norwegia | NVE HydAPI | wymaga darmowego klucza | — | odłożone |

Nie znaleźliśmy otwartego źródła poziomów dla dużych polskich zbiorników zaporowych (Jeziorsko, Solina, Turawa, Nysa).
Wody Polskie publikują komunikaty, a nie dane do pobrania.

## 2. Sceny radarowe

- Sentinel-1 RTC z Microsoft Planetary Computer: katalog STAC, pliki COG, żeton dostępu wydawany bez konta.
- Scena z tego samego dnia jest zwykle dostępna po kilku godzinach.
- Odczyt prostokąta akwenu trwa około sekundy.

## 3. Próba eksploracyjna (rok 2022, sezon bez lodu)

| Miejsce | Scen | Zakres poziomu | ρ (powierzchnia wobec poziomu) | Błąd odtworzonego poziomu |
|---|---|---|---|---|
| Zbiornik Siemianówka (PL), IV–X | 50 | 44 cm | 0,44 | 12 cm |
| Lokka (FI), VI–X | 37 | 46 cm | 0,67 | 10 cm |

- Najprostsza metoda (stały próg −24 dB na całym prostokącie) dała ρ około 0,2 i została odrzucona.
- Metoda z próby (strefa akwenu, próg Otsu w strefie, odrzucenie scen o małym kontraście) weszła do protokołu W1.
- Przed protokołem nie oglądaliśmy żadnej sceny z lat 2024–2026 ani żadnej sceny innych akwenów.

## 4. Dobór akwenów i klas

Klasę `expected` (high, medium, control) wpisaliśmy do rejestru przed liczeniem, na podstawie kształtu brzegów
i zakresu poziomu z 2022 roku: płytkie zbiorniki o dużym zakresie jako `high` albo `medium`, jeziora o stromych
brzegach albo małym zakresie jako `control`. Wynik pokazał, że sam zakres poziomu nie wystarcza: Vombsjön (zakres 2 m)
ma brzegi za strome na siatkę 20 m.
