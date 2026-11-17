# Water Check — stan i plan

Stan na 2026-11-17, wersja 1.1.0. Jedna strona do orientacji; szczegóły w dokumentach z §6.

**Najważniejszy wynik (lata testowe 2024–2025, protokół W1):** powierzchnia wody z radaru Sentinel-1 idzie za poziomem
z wodowskazu na 2 z 6 akwenów, na których spodziewaliśmy się sygnału (Lokka i Porttipahta w Laponii: ρ 0,92 i 0,97,
błąd poziomu 20 i 15 cm przy zakresie około 1 m). Jeden akwen potwierdzony częściowo (Siemianówka), trzy
niepotwierdzone. Wszystkie 3 jeziora kontrolne są stabilne.

**Metoda v2 (protokół W2):** mniejszy błąd poziomu na 5 z 6 akwenów w latach 2024–2025 (ponowna ocena), ale test
potwierdzający na 2026 roku jest negatywny (0 confirmed, 2 partly, 3 not confirmed). Werdykt główny zostaje z W1.

**Przepływ danych (jedno zdanie):** poziomy z wodowskazów (4 sieci krajowe) i sceny Sentinel-1 → codziennie automat
w GitHub Actions → małe pliki w repozytorium → panel publiczny (GitHub Pages) i punkty mapy dla strony geoworldlook.

**Cel:** pokazać, gdzie radar może zastąpić wodowskaz, a gdzie nie. Nie podajemy objętości wody ani prognoz.

## 1. Wersja 1.1.0 — produkt

- **Panel (EN):** 9 akwenów w 4 krajach (Polska, Finlandia, Szwecja, Francja). Mapa, ostatni poziom
  z wodowskazu, ostatnia powierzchnia z radaru, werdykt, wykres poziomu i powierzchni od 2022, wykres powierzchnia–poziom,
  osobne wiersze metody v2.
- **Rejestr:** tylko akweny z bieżącymi odczytami wodowskazu (D-107).
- **Automat:** przebieg dwa razy dziennie (07:20 i 15:20 UTC) w GitHub Actions; liczy tylko nowe sceny; przy błędzie zgłoszenie
  w repozytorium, które pierwszy udany przebieg sam zamyka.
- **Rekonstrukcja:** 5335 scen od 2022 roku w sezonach bez lodu.
- **Kod:** pakiet `watercheck`, test bez sieci, CI (linter, test, budowa obrazu Dockera).

## 2. Co jest sprawdzone

| Co | Wynik | Status |
|---|---|---|
| Lokka, Porttipahta (FI): powierzchnia wobec poziomu | ρ 0,92 i 0,97; błąd 20 i 15 cm (18% i 15% zakresu) | confirmed (W1) |
| Zbiornik Siemianówka (PL) | ρ 0,96, ale błąd poziomu 104 cm (54% zakresu) | partly (W1) |
| Vombsjön, Ringsjön (SE), Haute-Vilaine (FR) | ρ 0,49–0,65; błąd 27–32% zakresu | not confirmed (W1) |
| Jeziora kontrolne: Gopło, Hjälmaren, Bourget | zmienność powierzchni 3,1%, 0,3%, 0,4% | stable (W1) |
| Rok 2026 na żywo: Lokka, Porttipahta | ρ 0,47 i 0,51 | opisowy |
| Metoda v2, lata 2024–2025 | błąd poziomu mniejszy na 5 z 6 akwenów (Porttipahta 15 → 7 cm, Siemianówka 104 → 66 cm); confirmed 2, partly 2, not confirmed 2 | ponowna ocena (W2) |
| Metoda v2, rok 2026 | confirmed 0, partly 2 (Porttipahta, Ringsjön), not confirmed 3; kontrolne stabilne | **niepotwierdzone (W2)** |

## 3. Czego nie mówimy (granice)

- Radar nie mierzy poziomu. Poziom odtwarzamy z powierzchni prostą dopasowaną na latach 2022–2023.
- Metoda działa na dużych, płytkich zbiornikach. Strome brzegi, małe akweny i trzciny dają słaby sygnał.
- Zimą (lód) nie ma wyniku.
- Prosta powierzchnia → poziom zawodzi, gdy późniejsze lata wychodzą poza zakres z kalibracji (Siemianówka).
- Błąd poziomu to około 20 cm nawet na najlepszych akwenach. Małych zmian poziomu (rok 2026 w Laponii) radar nie rozróżnia.
- Metoda v2 wymaga wodowskazu do corocznej rekalibracji, więc nie zastępuje pomiaru na miejscu.
- Dla Polski nie ma wyniku na żywo za 2026, bo IMGW publikuje archiwum poziomów z opóźnieniem.

## 4. Decyzje

- **D-096:** Water Check jest projektem nr 4 w standardzie GeoWorldLook.
- **D-097:** lata 2022–2023 to kalibracja (opisowo), 2024–2025 test według protokołu zapisanego wcześniej, od 2026 na żywo.
- **D-099:** sceny Sentinel-1 RTC z Planetary Computer, pasmo VH, strefa akwenu z lat kalibracji, próg Otsu.
- **D-100:** system działa w GitHub Actions; stan potoku w `data/`, wynik w `docs/showcase/`.
- **D-103:** przebieg jest codzienny i przyrostowy (świeże odczyty wodowskazów każdego dnia; scena liczona raz).
- **D-104:** Jezioro Łebsko usunięte z rejestru po przebiegu (prostokąt objął Bałtyk); decyzja z powierzchni strefy, nie z wyniku.
- **D-107:** rejestr zawiera tylko akweny z bieżącymi odczytami wodowskazu. Lago d'Idro usunięte (zbiór ARPA Lombardia
  kończy się 2025-01-01); jego wynik testu zostaje w `W1_wyniki.md`.
- **D-108:** metoda v2 (wygładzanie, wspólna krzywa, coroczna rekalibracja) jest drugą, równoległą oceną według
  protokołu W2. Werdykt główny zostaje z W1. Wynik v2 raportujemy także wtedy, gdy jest negatywny.

## 5. Dalej (propozycje do decyzji autora)

| Co | Uwagi |
|---|---|
| Kształt brzegu z modelu terenu albo altymetria radarowa jako drugi pomiar | nowy protokół; samo przetwarzanie szeregu już nie pomaga (W2) |
| Więcej dużych, płytkich zbiorników | tam metoda działa; każdy z klasą `expected` wpisaną przed liczeniem |
| Wodowskazy dla Szwajcarii i Norwegii | Szwajcaria: brak otwartej historii; Norwegia: potrzebny darmowy klucz NVE |
| Własne przetwarzanie radaru jako źródło zapasowe | gdyby Planetary Computer zmienił zasady dostępu |

## 6. Gdzie co jest

| Temat | Dokument |
|---|---|
| Kod i moduły | `docs/ARCHITEKTURA.md` |
| Przejście przez jeden akwen i jedną scenę | `docs/PRZEWODNIK.md` |
| Uruchomienie i co robić przy błędzie | `docs/URUCHOMIENIE_LOKALNE.md` |
| Protokół i wyniki testu | `docs/evidence/W1_protokol_powierzchnia_poziom.md`, `docs/evidence/W1_wyniki.md` |
| Metoda v2: protokół, wybór, wyniki | `docs/evidence/W2_protokol_metoda_v2.md`, `W2_wybor_metody.csv`, `W2_wyniki.md` |
| Przegląd wodowskazów i próba eksploracyjna | `docs/evidence/W0_przeglad_wodowskazow.md` |
| Plan wdrożenia | `docs/plans/Plan_v1_water_check.md` |
| Zmiany wersji | `CHANGELOG.md` |
