# Raport jakości danych – Check Engine Team

**Projekt:** Segmentacja i profilowanie regionalnych rynków motoryzacyjnych w Polsce
**Źródło:** publiczne API CEPiK (`https://api.cepik.gov.pl/pojazdy`), 16 województw, okresy 2023–2025
**Ostatnia aktualizacja:** 8 listopada 2026

## Legenda

- **Zakres** – udział rekordów (lub kolumn) dotkniętych problemem. Wartości z outputu `Untitled23` (próbka 23 000 rekordów) są podane wprost. Wartości oznaczone *do zmierzenia* będą uzupełnione po pierwszym uruchomieniu notebooka `notebooks/eda.ipynb` (sekcja wskazana w kolumnie *Planowane działanie*).
- **Kto** – osoba odpowiedzialna. *Do przypisania* oznacza, że zespół jeszcze nie ustalił właściciela.
- **[DONE]** – problem rozwiązany w kodzie lub obejście wdrożone. Pozycja zostaje w raporcie jako historia.

---

## Zbiór A: Surowa próbka API CEPiK (`data/raw/cepik_raw.csv`)

| Problem | Zakres | Planowane działanie | Kto |
|---|---|---|---|
| Kolumny puste w 100%: `wlasciciel-wojewodztwo`, `poziom-emisji-co2`, `moc-netto-silnika`, `rodzaj-pierwszego-paliwa-alternatywnego`, `rodzaj-drugiego-paliwa-alternatywnego` | 5 kolumn, 23 000 / 23 000 rekordów | Wykluczyć z analiz i modelowania. Właściciela zastąpić `rejestracja-wojewodztwo`. Zgłosić do CEPiK, że pola są zwracane puste. | Do przypisania |
| Braki w `rodzaj-paliwa` | 1 900 rekordów (8,3%) | Osobna kategoria `BRAK`, a nie wrzucanie do `Inne`, bo `Inne` zawiera też prawdziwe inne paliwa. Notebook: sekcja 4. | Do przypisania |
| Braki w `pojemnosc-skokowa-silnika` | 2 167 rekordów (9,4%) | Usunięcie rekordów. Imputacja medianą byłaby błędna, bo pojemność jest zmienną kluczową. Obsłużone przez filtr zakresu w sekcji 4. | Zespół |
| Braki w `marka` | 625 rekordów (2,7%) | Usunięcie z analiz marek. Pozostałe analizy bez zmian. | Do przypisania |
| Braki w `model` | 10 rekordów (0,04%) | Bez działania, nieistotne dla wniosków. | Zespół |
| Ograniczona próbka: maks. 500 rekordów na zapytanie (województwo × okres, strona 1) | 48 zapytań, maks. 24 000 rekordów. Rozkład nie jest populacją. | Pełne pobranie z paginacją. Wymaga sprawdzenia struktury odpowiedzi API (linki do kolejnych stron) w dokumentacji CEPiK. Do czasu wdrożenia – każdą analizę regionalną opisywać jako próbkę. | Do przypisania |
| Nieudane zapytanie: DOLNOŚLĄSKIE 2025 zwróciło uszkodzony JSON | 1 z 48 zapytań (ok. 500 rekordów, 2%) | Notebook zapisuje log pobierania. Ponowić zapytanie lub uzupełnić przy pełnym pobieraniu. | Do przypisania |
| Generator danych zastępczych w `Untitled23` podmieniał dane losowymi, gdy API zwróciło za mało rekordów | Cały zbiór w wariancie generatora | [DONE] Usunięty. Notebook zgłasza błąd, jeśli pobrano mniej niż 5 000 rekordów. Dane zawsze z API. | Zespół |
| Niespójne nazwy marek, np. `RENAULT/CARPOL`, `RENAULT/MOTOWEKTOR`, `MAN/MAN TRUCK`, `DAIMLERCHRYSLER` | Zakres do zmierzenia (liczba unikalnych wartości `marka`) | Słownik normalizacji marek (mapowanie wariantów na jedną nazwę). Notebook: sekcja 7. | Do przypisania |
| Brak klucza unikalnego rekordu – nie wiadomo, czy w zbiorze są duplikaty | Do zmierzenia (`df_raw.duplicated()` na wybranym kluczu) | Zdefiniować klucz (np. kombinacja pól identyfikujących pojazd) i sprawdzić duplikaty. Usunąć po dacie pobrania. | Zespół |
| Niezgodny format daty `data-pierwszej-rejestracji-w-kraju`. Parsowanie `pd.to_datetime(errors="coerce")` bez `format=` zamienia błędne wartości w `NaT` po cichu | Do zmierzenia (liczba `NaT` przed filtrem wieku) | Zweryfikować format na pierwszym pobraniu. Użyć `pd.to_datetime(..., format=...)` i logować liczbę `NaT`, zamiast je gubić w filtrze. Notebook: sekcja 4. | Do przypisania |

---

## Zbiór B: Dane oczyszczone (`data/processed/pojazdy_clean.csv`)

| Problem | Zakres | Planowane działanie | Kto |
|---|---|---|---|
| Utrata rekordów w czyszczeniu | `Untitled23`: 23 000 → 15 900 (−30,9%). Nasz pipeline: do zmierzenia. | Logować liczbę odrzuconych rekordów dla każdej reguły osobno, żeby wiedzieć, która reguła tnie najwięcej. | Zespół |
| Outliery > 3σ w pojemności, masie i mocy netto | Do zmierzenia (sekcja 6 notebooka) | Zbadać źródło (błędy urzędowe czy prawdziwe pojazdy). Oznaczyć flagą `outlier_3sigma`, a nie usuwać automatycznie. | Do przypisania |
| Flaga importu opiera się na założeniu: wiek > 1 rok = import. Próg nieprzetestowany | 100% kolumny `pochodzenie` | Zweryfikować na próbce ręcznie (np. sprawdzić rekordy z wiekiem 2 lata) lub przetestować alternatywny próg. Wyniki traktować jako przybliżenie. | Do przypisania |
| Rejestracja w województwie nie oddaje miejsca sprzedaży. Huby flotowe (poleasingowe): MAZOWIECKIE, WIELKOPOLSKIE | 2 z 16 województw (raport) | Dodać flagę `hub_flotowy` i wykluczyć te regiony z klasteryzacji (zgodnie z planem K-Means). | Do przypisania |
| Hybrydy nierozpoznawalne: pole alternatywnego paliwa puste, hybrydy trafiają do benzyny lub diesla | 100% pola alternatywnego (patrz Zbiór A) | Wnioski o napędach ograniczyć do kategorii benzyna / diesel / elektryczny. Nie raportować udziału hybryd. | Zespół |
| Nazwa pola w raporcie nie zgadza się z API: raport `rodzaj-paliwa-alternatywnego`, API `rodzaj-pierwszego-paliwa-alternatywnego` | Dokumentacja | Poprawić nazwy w raporcie końcowym. | Do przypisania |
| Zbyt małe próby regionalne do klasteryzacji K-Means (ok. 14–15 województw po wykluczeniu hubów) | 14–15 obserwacji | Traktować wynik 3 klastrów jako wstępny. Przy niskiej stabilności zmniejszyć liczbę klastrów lub porównać z podziałem ręcznym. | Do przypisania |
| Dane nie są pełną populacją (patrz Zbiór A) – wnioski regionalne mogą być obciążone limitem próbkowania | Wszystkie województwa | Przed wnioskami końcowymi wykonać pełne pobranie lub jawnie zastrzec w raporcie. | Do przypisania |
| Brak właściciela pojazdu (`wlasciciel-wojewodztwo` 100% pusta) | 100% rekordów | [DONE] Obejście: analizy na `rejestracja-wojewodztwo`. Ograniczenie opisane w raporcie. | Zespół |
| Kategoria pojazdu: pozostawione tylko SAMOCHÓD OSOBOWY (usunięte autobusy, ciężarówki, motocykle) | Cały zbiór | [DONE] Filtr w notebooku, sekcja 4. | Zespół |
| Masa poza zakresem 500–3500 kg (np. pojazdy > 30 t oznaczone jako osobowe) | Do zmierzenia | [DONE] Odrzucone przez filtr masy. | Zespół |
| Literówki w pojemności silnika (np. 1 cm³) | Do zmierzenia | [DONE] Filtr zakresu 50–7000 cm³ (sekcja 4 notebooka). Poprzednia wersja filtru (> 0) nie łapała tych wartości – poprawione 8 listopada 2026. | Zespół |
| Ujemny wiek pojazdu (błąd dat w bazie) | Do zmierzenia | [DONE] Usunięte przez filtr wieku 0–60 lat. | Zespół |

---

## Historia zmian

- **8 listopada 2026** – utworzenie raportu. Zbiór A: problemy z pobierania i braki na podstawie outputu `Untitled23`. Zbiór B: problemy z czyszczeniem i założeniami analitycznymi.
- **8 listopada 2026** – poprawiony filtr pojemności silnika (odrzuca wartości poniżej 50 cm³). Oznaczony jako [DONE].
- **8 listopada 2026** – usunięty generator danych zastępczych z pobierania. Oznaczony jako [DONE].

## Otwarte pytania do zespołu

1. Kto jest właścicielem poszczególnych pozycji? Kolumna *Kto* ma obecnie wartości „do przypisania”.
2. Jak zdefiniować klucz unikalny rekordu CEPiK, żeby sprawdzić duplikaty?
3. Czy zespół ma dostęp do dokumentacji API CEPiK opisującej paginację?
