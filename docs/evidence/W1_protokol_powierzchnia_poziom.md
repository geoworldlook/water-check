# Protokół W1: czy powierzchnia wody z Sentinel-1 idzie w parze z poziomem z wodowskazu

Wersja 1, zapisana 2026-11-14, przed policzeniem lat testowych. Suma kontrolna SHA-256 tego pliku jest w
`watercheck/config.py` (`PROTOCOL_SHA256`); test `python -m watercheck selftest` sprawdza, że plik się nie zmienił.
Zmiana reguł oznacza nową wersję protokołu, a wynik poprzedniej wersji zostaje w repozytorium.

## 1. Pytanie

Radar Sentinel-1 widzi powierzchnię wody, a nie jej poziom. Pytamy, czy na danym akwenie zmiana powierzchni
wyznaczona z radaru zgadza się ze zmianą poziomu zmierzoną wodowskazem i z jakim błędem da się z powierzchni
odtworzyć poziom.

## 2. Dane

- **Radar:** Sentinel-1 RTC (pasmo VH, skorygowane o teren), katalog Microsoft Planetary Computer. Wszystkie sceny
  nad akwenem w miesiącach sezonu bez lodu zapisanych w rejestrze (`season_from`–`season_to`).
- **Poziom:** dobowy poziom wody z wodowskazu wskazanego w rejestrze (IMGW, SYKE, SMHI, Hub'Eau, ARPA Lombardia),
  po kontroli jakości (odrzucenie wartości oddalonych od mediany o więcej niż 6 rozstępów ćwiartkowych, nie mniej niż 100 cm).
- **Rejestr akwenów:** `watercheck/waterbodies.csv` w wersji z commita tego protokołu, razem z kolumną `expected`
  (high, medium, control). Klasa `expected` została przypisana przed liczeniem, na podstawie kształtu brzegów
  i zakresu poziomu.

## 3. Okresy

| Okres | Lata | Do czego służy |
|---|---|---|
| Kalibracja | 2022–2023 | strefa akwenu i prosta powierzchnia → poziom |
| Test | 2024–2025 | werdykt według punktu 6 |
| Na żywo | od 2026 | te same reguły; raportowane osobno |

## 4. Metoda

1. **Siatka.** Stała siatka UTM akwenu o rozdzielczości z rejestru (10, 20 albo 40 m).
2. **Strefa akwenu.** Z najwyżej 60 scen z lat kalibracji: piksele, których 10. percentyl w czasie jest poniżej −22 dB,
   trzy największe spójne obszary, powiększone o pas brzegu 160 m. Rdzeń wody: mediana w czasie poniżej −22 dB.
3. **Woda w scenie.** Próg Otsu na wartościach VH wewnątrz strefy; piksele poniżej progu to woda.
4. **Sceny odrzucane.** Pokrycie siatki poniżej 98% (`partial`) albo różnica średniej lądu i wody w strefie mniejsza
   niż 6 dB (`low_contrast`: wiatr, deszcz, lód).
5. **Powierzchnia → poziom.** Dla każdego toru orbity osobno prosta `poziom = a + b · powierzchnia`, dopasowana na
   scenach z lat kalibracji (co najmniej 8 scen na tor).

## 5. Miary (na scenach `ok` z poziomem wodowskazu z tego samego dnia)

- **ρ:** korelacja rang Spearmana między powierzchnią a poziomem, liczona osobno dla każdego toru z co najmniej
  8 scenami w okresie; wynik akwenu to mediana po torach.
- **Błąd poziomu:** RMSE różnicy między poziomem odtworzonym z powierzchni a poziomem z wodowskazu, wszystkie tory razem.
- **Zakres poziomu:** różnica 95. i 5. percentyla poziomu w dniach scen.
- **Zmienność powierzchni:** odchylenie standardowe powierzchni dzielone przez średnią, mediana po torach.

## 6. Hipotezy i reguły decyzji (lata testu 2024–2025)

Dla akwenów z klasą `high` i `medium`:

- **H-W1.** ρ ≥ 0,7.
- **H-W2.** Błąd poziomu nie przekracza 25% zakresu poziomu.

Werdykt akwenu: `confirmed` (obie spełnione), `partly` (jedna), `not confirmed` (żadna).

Dla akwenów z klasą `control` (brzegi strome albo mały zakres poziomu):

- **H-W3.** Zmienność powierzchni nie przekracza 5%. Werdykt: `stable` albo `unstable`.

Gdy brakuje danych do miary (mniej niż 8 scen na każdym torze albo brak poziomu), werdykt to `insufficient`.
Wszystkie werdykty raportujemy, także negatywne.

## 7. Co już widzieliśmy przed zapisaniem protokołu

- Próba eksploracyjna z 2026-11-14 na scenach z 2022 roku: Zbiornik Siemianówka (ρ 0,44, błąd 12 cm przy zakresie
  44 cm) i Lokka (ρ 0,67, błąd 10 cm przy zakresie 46 cm). Progi w punkcie 6 zostały wybrane ze znajomością tego wyniku.
- Najprostsza metoda (stały próg na całym prostokącie) dała ρ około 0,2 i została odrzucona.
- Dla pozostałych akwenów nie oglądaliśmy żadnej sceny. Żadna scena z lat 2024–2026 nie była oglądana.

## 8. Znane ograniczenia

- Zimą (lód, śnieg) nie ma wyniku; sezon jest zapisany w rejestrze, nie wyznaczany z temperatury.
- Wiatr rozjaśnia wodę; część scen odpada, a część słabszych epizodów może przejść próg kontrastu.
- Roślinność wynurzona (trzciny) wygląda w radarze jak ląd.
- Małe akweny i zalesione brzegi dają słaby sygnał.
- Prosta powierzchnia → poziom nie musi być dobrym opisem zbiornika o zmiennym kształcie dna.
- IMGW publikuje archiwum poziomów z opóźnieniem: za 2026 rok jest tylko bieżący stan z API.
- Zbiór ARPA Lombardia kończy się 2025-01-01, więc dla Lago d'Idro rok testowy to tylko 2024.
