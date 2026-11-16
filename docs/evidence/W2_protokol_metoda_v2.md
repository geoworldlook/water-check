# Protokół W2: metoda v2 (wygładzanie w czasie, krzywa hipsometryczna, coroczna rekalibracja)

Wersja 1, zapisana 2026-11-16, przed policzeniem metody v2 na latach 2024–2026. Suma kontrolna SHA-256 tego pliku
jest w `watercheck/config.py` (`PROTOCOL_W2_SHA256`); test `python -m watercheck selftest` sprawdza, że plik się nie
zmienił. Protokół W1 i jego wyniki zostają bez zmian.

## 1. Po co

Wynik W1: metoda v1 potwierdziła się na 2 z 7 akwenów. Dwie słabości v1 są opisane w literaturze:

- **Szum pojedynczej sceny** (wiatr, plamka radarowa). Uśrednianie w oknie kilkunastu dni poprawia zgodność
  powierzchni z pomiarem (porównanie Sentinel-1 i Sentinel-2 na 29 zbiornikach z pomiarami, Remote Sensing 2021).
- **Zależność powierzchni od poziomu to krzywa** (hipsometria zbiornika), a nie prosta, i trzeba ją dopasowywać
  na całym dostępnym zakresie poziomów (krzywe poziom–powierzchnia: Busker i in. 2019, Hydrol. Earth Syst. Sci.;
  zbiorniki w Chinach z Sentinel-1, Water Resources Research 2023, doi:10.1029/2023WR036450).

## 2. Metoda v2 (zamrożona)

Wejście jest takie samo jak w v1: powierzchnia wody w scenie (`data/scenes/`), tylko sceny z flagą `ok`.

1. **Wspólna skala torów.** Powierzchnię z każdego toru orbity odejmujemy od średniej toru i dzielimy przez jego
   odchylenie standardowe (statystyki z okresu dopasowania; tor liczy się przy co najmniej 8 scenach).
2. **Wygładzanie przyczynowe.** Mediana tak znormalizowanej powierzchni ze scen z ostatnich 15 dni, wszystkie tory razem.
3. **Krzywa.** Wielomian 2. stopnia poziom = f(powierzchnia wygładzona). Gdy nie jest rosnący w zakresie danych,
   bierzemy prostą. Poza zakresem danych krzywą przedłużamy prostą o nachyleniu z brzegu zakresu.
4. **Coroczna rekalibracja.** Statystyki torów i krzywą dla roku R dopasowujemy na wszystkich latach wcześniejszych
   (od 2022 do R − 1). Do oceny roku R nie wchodzi żaden pomiar z roku R.

Kod: `watercheck/series.py`.

## 3. Jak metoda została wybrana

Eksperyment `notebooks/experiments/W2_wybor_metody.py`, tylko lata kalibracji 2022–2023 (dopasowanie na jednym
roku, ocena na drugim, w obie strony). Porównane okna: 0, 7, 15, 30 dni; krzywe: prosta i wielomian.
Wynik: `docs/evidence/W2_wybor_metody.csv`. Okno 15 dni dało najwięcej akwenów z ρ ≥ 0,7 (3 z 6) i najwyższą
medianę ρ (0,69 wobec 0,64 bez wygładzania). Prosta i wielomian wypadły tak samo; wybieramy wielomian, bo krzywa
hipsometryczna jest w literaturze nieliniowa. Poprawa na latach kalibracji jest umiarkowana i tego się spodziewamy.

## 4. Co jest oceną niezależną, a co nie

- **Lata 2024–2025: ponowna ocena, nie niezależny test.** Wyniki v1 dla tych lat były znane, gdy powstawała v2
  (w szczególności wiedzieliśmy, że prosta z lat 2022–2023 nie obowiązuje na Siemianówce przy niskich stanach).
  Wynik v2 dla tych lat raportujemy z tą uwagą.
- **Sezon 2026: test potwierdzający.** Dopasowanie na latach 2022–2025, ocena na scenach z 2026 roku.
  Dotyczy akwenów z poziomem z wodowskazu za 2026 (Finlandia, Szwecja, Francja; dla Polski danych jeszcze nie ma).
  Wyniki v1 dla 2026 były znane tylko jako pojedyncze liczby ρ; nie posłużyły do wyboru okna ani krzywej.

## 5. Miary i reguły (progi takie same jak w W1)

Na scenach `ok` z poziomem wodowskazu z tego samego dnia:

- **ρ:** korelacja rang Spearmana między wygładzoną powierzchnią a poziomem, wszystkie tory razem.
- **Błąd poziomu:** RMSE różnicy między poziomem z krzywej a poziomem z wodowskazu.
- **Zakres poziomu:** różnica 95. i 5. percentyla poziomu w dniach scen.

Akweny `high` i `medium`: **H-W4** ρ ≥ 0,7; **H-W5** błąd poziomu ≤ 25% zakresu. Werdykt: `confirmed` (obie),
`partly` (jedna), `not confirmed` (żadna), `insufficient` (za mało scen).
Akweny `control`: **H-W6** zmienność wygładzonej powierzchni ≤ 5% średniej powierzchni; werdykt `stable` albo `unstable`.

Wszystkie werdykty raportujemy, także negatywne. Jeśli v2 nie poprawi wyników, piszemy to wprost.

## 6. Znane ograniczenia

- Coroczna rekalibracja wymaga wodowskazu. Metoda pokazuje, jak dobrze radar wypełnia czas między pomiarami
  i jak śledzi zmiany, a nie że może całkiem zastąpić wodowskaz.
- Wygładzanie 15-dniowe opóźnia reakcję na szybkie zmiany poziomu.
- Strome brzegi, małe akweny i roślinność wynurzona ograniczają sygnał niezależnie od metody.
