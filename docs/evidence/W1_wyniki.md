# W1: wyniki testu powierzchnia wody (Sentinel-1) wobec poziomu z wodowskazu

Przebieg z 2026-11-15, protokół `W1_protokol_powierzchnia_poziom.md` (wersja 1, commit sprzed policzenia lat testowych).
Liczby pochodzą z potoku (`docs/showcase/watercheck_data.json`), nie z obliczeń poza nim.

## 1. Werdykt

Lata testowe 2024–2025, 10 akwenów, 5691 scen od 2022 roku.

- **Akweny z oczekiwanym sygnałem (7):** potwierdzone 2, częściowo 1, niepotwierdzone 4.
- **Akweny kontrolne (3):** stabilne 3.

## 2. Akweny z oczekiwanym sygnałem

| Akwen | Klasa | Scen | Torów | ρ | Błąd poziomu | Zakres poziomu | Błąd / zakres | H-W1 (ρ ≥ 0,7) | H-W2 (≤ 25%) | Werdykt |
|---|---|---|---|---|---|---|---|---|---|---|
| Lokka (FI) | high | 96 | 3 | 0,92 | 19,8 cm | 111,0 cm | 18% | tak | tak | confirmed |
| Porttipahta (FI) | high | 131 | 5 | 0,97 | 14,8 cm | 102,0 cm | 15% | tak | tak | confirmed |
| Zbiornik Siemianówka (PL) | medium | 123 | 3 | 0,96 | 104,0 cm | 192,6 cm | 54% | tak | nie | partly |
| Vombsjön (SE) | high | 205 | 4 | 0,51 | 52,3 cm | 195,4 cm | 27% | nie | nie | not confirmed |
| Ringsjön (SE) | medium | 197 | 4 | 0,65 | 26,0 cm | 84,8 cm | 31% | nie | nie | not confirmed |
| Retenue de la Haute-Vilaine (FR) | medium | 94 | 2 | 0,49 | 133,3 cm | 418,0 cm | 32% | nie | nie | not confirmed |
| Lago d'Idro (IT) | medium | 50 | 3 | 0,50 | 44,1 cm | 109,2 cm | 40% | nie | nie | not confirmed |

## 3. Akweny kontrolne (H-W3: zmienność powierzchni ≤ 5%)

| Akwen | Scen | Zmienność powierzchni | Powierzchnia min–max | Werdykt |
|---|---|---|---|---|
| Jezioro Gopło (PL) | 135 | 3,1% | 19,8–23,1 km² | stable |
| Hjälmaren (SE) | 135 | 0,3% | 465,5–475,1 km² | stable |
| Lac du Bourget (FR) | 144 | 0,4% | 36,5–44,3 km² | stable |

## 4. Pozostałe okresy (opisowo)

| Akwen | ρ kalibracja 2022–2023 | ρ na żywo 2026 | Scen 2026 |
|---|---|---|---|
| Lokka | 0,89 | 0,47 | 74 |
| Porttipahta | 0,88 | 0,51 | 86 |
| Zbiornik Siemianówka | 0,69 | — | 0 |
| Vombsjön | 0,50 | 0,55 | 136 |
| Ringsjön | 0,84 | 0,78 | 135 |
| Retenue de la Haute-Vilaine | 0,39 | −0,07 | 69 |
| Lago d'Idro | 0,58 | — | 0 |

## 5. Co z tego wynika

- **Metoda działa na dużych, płytkich zbiornikach.** W Laponii powierzchnia zmienia się o dziesiątki km², a błąd
  odtworzonego poziomu to 15–20 cm przy zakresie około 1 m.
- **Siemianówka: kierunek zmian tak, wartość poziomu nie.** Powierzchnia idzie za poziomem (ρ 0,96), ale prosta
  dopasowana na latach 2022–2023, gdy poziom zmieniał się mało, nie obowiązuje przy dużych zmianach z lat 2024–2025.
- **Vombsjön nie potwierdził klasy „high”.** Zakres poziomu to 2 m, ale brzegi są za strome na siatkę 20 m.
- **Jeziora kontrolne są stabilne.** Metoda nie wytwarza zmian tam, gdzie ich nie ma.
- **Rok 2026 w Laponii jest słabszy** (ρ 0,47 i 0,51). Jeden sezon to za mało, żeby wskazać przyczynę.

## 6. Odstępstwa od protokołu

1. **Jezioro Łebsko usunięte z rejestru po przebiegu.** Prostokąt akwenu objął też Bałtyk: strefa wody miała
   133,6 km² przy jeziorze o powierzchni 71 km². Decyzja wynika z powierzchni strefy, nie z wyniku (akwen miał werdykt
   `stable`, więc usunięcie nie poprawia bilansu). Liczba akwenów kontrolnych spadła z 4 do 3.
2. **Lago d'Idro:** rok testowy to tylko 2024 (zbiór ARPA Lombardia kończy się 2025-01-01). Zapisane w protokole, punkt 8.
3. **Polska:** brak wyniku na żywo za 2026, bo IMGW nie opublikował jeszcze archiwum poziomów. Zapisane w protokole, punkt 8.

4. **Lago d'Idro usunięte z rejestru 2026-11-16 (D-107).** Zbiór poziomów ARPA Lombardia kończy się 2025-01-01,
   więc akwen nie miał bieżących odczytów. Jego wynik testu (not confirmed) zostaje w tym pliku. Bilans akwenów
   z sygnałem w rejestrze po usunięciu: 6 (confirmed 2, partly 1, not confirmed 3).

## 7. Dane przebiegu

| Akwen | Strefa | Scen razem | ok | niski kontrast | niepełne |
|---|---|---|---|---|---|
| Zbiornik Siemianówka | 25,6 km² | 524 | 298 | 27 | 159 |
| Jezioro Gopło | 33,6 km² | 530 | 317 | 1 | 91 |
| Lokka | 367,4 km² | 872 | 229 | 25 | 569 |
| Porttipahta | 212,0 km² | 797 | 312 | 3 | 372 |
| Vombsjön | 15,8 km² | 478 | 478 | 0 | 0 |
| Ringsjön | 46,7 km² | 478 | 478 | 0 | 0 |
| Hjälmaren | 524,0 km² | 822 | 305 | 0 | 436 |
| Retenue de la Haute-Vilaine | 3,6 km² | 352 | 232 | 0 | 120 |
| Lac du Bourget | 51,5 km² | 482 | 357 | 0 | 125 |
| Lago d'Idro | 14,6 km² | 356 | 356 | 0 | 0 |

Pozostałe sceny do sumy „razem” w ogóle nie pokrywają strefy akwenu (flaga `no_zone`: Siemianówka 40, Gopło 121,
Lokka 49, Porttipahta 110, Hjälmaren 81). Do miar wchodzą tylko sceny `ok` z poziomem wodowskazu z tego samego dnia.
Jedna scena nad Haute-Vilaine nie dała się odczytać (błąd okna) i nie ma jej w tabeli.
