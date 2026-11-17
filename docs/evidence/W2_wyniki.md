# W2: wyniki metody v2 (wygładzanie, wspólna krzywa, coroczna rekalibracja)

Przebieg z 2026-11-16, protokół `W2_protokol_metoda_v2.md` (wersja 1, zapisana przed policzeniem v2 na latach
2024–2026). Liczby pochodzą z potoku (`docs/showcase/watercheck_data.json`, pole `v2`), nie z obliczeń poza nim.

## 1. Werdykt

**Metoda v2 zmniejsza błąd poziomu, ale nie poprawia werdyktów. Test potwierdzający na 2026 roku jest negatywny.**

| Okres | Akweny z sygnałem (6) | Akweny kontrolne (3) |
|---|---|---|
| v1, lata 2024–2025 (test W1) | confirmed 2, partly 1, not confirmed 3 | stable 3 |
| v2, lata 2024–2025 (ponowna ocena, nie test niezależny) | confirmed 2, partly 2, not confirmed 2 | stable 3 |
| v2, rok 2026 (test potwierdzający) | confirmed 0, partly 2, not confirmed 3, insufficient 1 | stable 2, insufficient 1 |

Werdykt główny projektu zostaje z protokołu W1. Metoda v2 jest pokazana w panelu jako osobne wiersze.

## 2. Lata 2024–2025: v1 obok v2 (ponowna ocena)

Wyniki v1 dla tych lat były znane, gdy powstawała v2, więc to nie jest test niezależny (protokół, punkt 4).
ρ w v1 to mediana po torach; w v2 to jedna liczba dla wszystkich torów razem.

| Akwen | ρ v1 | ρ v2 | Błąd poziomu v1 | Błąd poziomu v2 | Błąd / zakres v1 | Błąd / zakres v2 | Werdykt v1 | Werdykt v2 |
|---|---|---|---|---|---|---|---|---|
| Lokka (FI) | 0,92 | 0,95 | 19,8 cm | 19,1 cm | 18% | 17% | confirmed | confirmed |
| Porttipahta (FI) | 0,97 | 0,98 | 14,8 cm | 7,2 cm | 15% | 7% | confirmed | confirmed |
| Zbiornik Siemianówka (PL) | 0,96 | 0,95 | 104,0 cm | 66,2 cm | 54% | 34% | partly | partly |
| Vombsjön (SE) | 0,51 | 0,60 | 52,3 cm | 47,4 cm | 27% | 24% | not confirmed | partly |
| Ringsjön (SE) | 0,65 | 0,66 | 26,0 cm | 25,5 cm | 31% | 30% | not confirmed | not confirmed |
| Retenue de la Haute-Vilaine (FR) | 0,49 | 0,02 | 133,3 cm | 143,8 cm | 32% | 34% | not confirmed | not confirmed |

Błąd poziomu spadł na 5 z 6 akwenów. Największa poprawa: Porttipahta (z 14,8 do 7,2 cm) i Siemianówka
(ze 104 do 66 cm). Na Haute-Vilaine v2 jest gorsza.

Akweny kontrolne (zmienność powierzchni, reguła ≤ 5%): Gopło 2,8% (v1: 3,1%), Hjälmaren 0,2% (0,3%),
Bourget 0,3% (0,4%). Wszystkie stabilne.

## 3. Rok 2026: test potwierdzający

Statystyki torów i krzywa dopasowane na latach 2022–2025, ocena na scenach z 2026 roku.

| Akwen | Scen | ρ | Błąd poziomu | Zakres poziomu | Błąd / zakres | H-W4 (ρ ≥ 0,7) | H-W5 (≤ 25%) | Werdykt |
|---|---|---|---|---|---|---|---|---|
| Lokka (FI) | 74 | 0,38 | 17,9 cm | 44,0 cm | 41% | nie | nie | not confirmed |
| Porttipahta (FI) | 86 | 0,74 | 39,9 cm | 46,0 cm | 87% | tak | nie | partly |
| Vombsjön (SE) | 136 | 0,67 | 34,7 cm | 120,2 cm | 29% | nie | nie | not confirmed |
| Ringsjön (SE) | 135 | 0,88 | 20,6 cm | 30,3 cm | 68% | tak | nie | partly |
| Retenue de la Haute-Vilaine (FR) | 69 | −0,39 | 158,6 cm | 367,1 cm | 43% | nie | nie | not confirmed |
| Zbiornik Siemianówka (PL) | 0 | — | — | — | — | — | — | insufficient |

Akweny kontrolne (H-W6): Hjälmaren 0,4% i Bourget 0,3% — stabilne; Gopło — brak poziomów za sezon 2026.

Dla porównania błąd poziomu metody v1 w 2026 roku (prosta z lat 2022–2023, opisowo): Lokka 43,0 cm,
Porttipahta 32,0 cm, Vombsjön 50,3 cm, Ringsjön 36,0 cm, Haute-Vilaine 153,4 cm. Metoda v2 ma mniejszy błąd
na 3 z 5 akwenów. Część tej różnicy daje samo dłuższe dopasowanie (cztery lata zamiast dwóch).

## 4. Co z tego wynika

- **Hipotezy H-W4 i H-W5 nie potwierdziły się w 2026 roku na żadnym akwenie w całości.**
- **W 2026 roku poziom zmieniał się mało.** W Laponii zakres poziomu w dniach scen to 44–46 cm, a w latach
  2024–2025 było to 105–111 cm. Błąd metody na Lokce jest taki sam jak wcześniej (około 18–19 cm), ale przy małym
  zakresie to już 41% zakresu. Radar widzi duże zmiany poziomu, małych nie rozróżnia.
- **Porttipahta 2026: błąd 40 cm.** Kierunek zmian się zgadza (ρ 0,74), wartość poziomu nie. Przyczyny nie znamy.
- **Wygładzanie szkodzi na małym zbiorniku z szybkimi zmianami.** Haute-Vilaine ma 3,6 km² i zakres poziomu
  około 4 m; mediana z 15 dni spóźnia się za zmianami.
- **Vombsjön i Ringsjön:** niewielka poprawa, werdykt bez zmiany w teście potwierdzającym. Brzegi są za strome
  na siatkę 20 m; tego nie naprawi przetwarzanie szeregu.
- **Jeziora kontrolne są stabilne w obu metodach.**

Wniosek: ograniczeniem jest kształt brzegu i wielkość zmian poziomu, a nie sposób przetwarzania szeregu.
Dalsza poprawa wymaga innego pomiaru (kształt brzegu z modelu terenu albo altymetria radarowa), a nie kolejnych
wariantów wygładzania.

## 5. Odstępstwa od protokołu

Brak. Dla Polski nie ma oceny za 2026 rok, bo archiwum poziomów IMGW za sezon 2026 nie jest jeszcze opublikowane
(zapisane w protokole, punkt 4).
