# Słownik zmiennych – Check Engine Team

**Projekt:** Segmentacja i profilowanie regionalnych rynków motoryzacyjnych w Polsce
**Notebook:** `notebooks/eda.ipynb`
**Źródło danych:** publiczne API CEPiK (`https://api.cepik.gov.pl/pojazdy`), zapytania per województwo i okres (typ daty 1 – data pierwszej rejestracji)
**Ostatnia aktualizacja:** 8 listopada 2026

## Konwencje

- **Typ** – typ kolumny w DataFrame po wczytaniu i konwersji w notebooku (nie typ z JSON API). Kolumny liczbowe, w których mogą występować braki, są `float64` (po `to_numeric(errors="coerce")`), a nie `int64`.
- **Źródło** – `CEPiK API` oznacza pole zwracane przez API bez zmian. `wyliczona` oznacza zmienną utworzoną w notebooku, z podaniem reguły.
- **Braki** – odsetki z próbki surowej (23 000 rekordów, output `Untitled23`) lub „do zmierzenia” – wartość uzupełniana po pierwszym uruchomieniu (patrz `docs/jakosc_danych.md`).

---

## Zmienne pobierane z API (dane surowe)

| Nazwa kolumny | Typ | Opis | Wartości / jednostka | Źródło |
|---|---|---|---|---|
| `rodzaj-pojazdu` | object | Kategoria pojazdu wg ewidencji CEPiK. Używana do filtra. | Używamy wyłącznie `SAMOCHÓD OSOBOWY`. Pozostałe kategorie (np. ciągniki, motocykle) są odrzucane. | CEPiK API |
| `rodzaj-paliwa` | object | Rodzaj paliwa podstawowego. Podstawa kategorii `Naped`. | Np. `BENZYNA`, `OLEJ NAPĘDOWY`, `ENERGIA ELEKTRYCZNA`. Braki: 1 900 z 23 000 (8,3%). | CEPiK API |
| `marka` | object | Marka pojazdu. | Tekst wielkimi literami, np. `VOLKSWAGEN`, `TOYOTA`. Braki: 625 (2,7%). Niespójne warianty, np. `RENAULT/CARPOL`, `MAN/MAN TRUCK`. | CEPiK API |
| `rok-produkcji` | float64 | Rok produkcji pojazdu. Składnik `wiek_pojazdu`. | Rok, format `YYYY`. Konwertowany z `to_numeric(errors="coerce")`. | CEPiK API |
| `data-pierwszej-rejestracji-w-kraju` | datetime64 | Data pierwszej rejestracji pojazdu w Polsce. Źródło roku rejestracji. | `YYYY-MM-DD`. Konwersja `to_datetime(errors="coerce")`. Format surowy do potwierdzenia po pobraniu (patrz jakość danych). | CEPiK API |
| `rejestracja-wojewodztwo` | object | Województwo rejestracji pojazdu. Podstawa analiz regionalnych. | 16 nazw województw, wielkie litery, np. `MAZOWIECKIE`. Gdy pole puste, uzupełniana nazwą z pobieranego województwa. | CEPiK API |
| `pojemnosc-skokowa-silnika` | float64 | Pojemność skokowa silnika. | cm³; po filtrze 50–7000. Braki: 2 167 (9,4%). | CEPiK API |
| `masa-wlasna` | float64 | Masa własna pojazdu. Służy do odrzucania anomalii. | kg; po filtrze 500–3500. | CEPiK API |

### Zmienne pobierane, ale nieużywane w analizie

Te pola są w zapytaniu (`REQUIRED_COLS`), ale nie wchodzą do obliczeń. Nie należy ich opisywać w raporcie jako zmiennych analitycznych.

| Nazwa kolumny | Powód wykluczenia |
|---|---|
| `wlasciciel-wojewodztwo` | 100% braków w próbce. Zastąpione przez `rejestracja-wojewodztwo`. |
| `poziom-emisji-co2` | 100% braków w próbce. |
| `moc-netto-silnika` | 100% braków w próbce. |
| `rodzaj-pierwszego-paliwa-alternatywnego`, `rodzaj-drugiego-paliwa-alternatywnego` | 100% braków. Hybrydy nie są rozpoznawalne. Raport używa nazwy `rodzaj-paliwa-alternatywnego`, co nie zgadza się z API – do poprawy w raporcie. |
| `model` | Pobierana, nieużywana w obecnych analizach. Braki 10 rekordów (0,04%). |

---

## Zmienne wyliczone w notebooku (`notebooks/eda.ipynb`, sekcja 4)

| Nazwa kolumny | Typ | Opis | Wartości / jednostka | Źródło |
|---|---|---|---|---|
| `rok_rejestracji` | float64 | Rok pierwszej rejestracji w Polsce. | Rok, `YYYY`. Wyliczona jako `data-pierwszej-rejestracji-w-kraju.dt.year`. Braki po błędnej dacie. | wyliczona |
| `wiek_pojazdu` | float64 | Wiek pojazdu w chwili pierwszej rejestracji w Polsce. | Lata. Wzór: `rok_rejestracji − rok-produkcji`. Po filtrze 0–60. | wyliczona |
| `pochodzenie` | object | Flaga pochodzenia pojazdu. Oparta na progu wieku z raportu. | `Import używany` (wiek > 1 rok), `Krajowy (Nowy)` (wiek ≤ 1 rok). Założenie progu niezwalidowane. | wyliczona |
| `Naped` | object | Uproszczona kategoria napędu z `rodzaj-paliwa`. | `Benzyna`, `Diesel`, `Elektryczny (BEV)`, `Inne`. Brak paliwa trafia do `Inne` (do zmiany – patrz jakość danych). | wyliczona |
| `woj` | object | Kopia `rejestracja-wojewodztwo` do grupowania. | Te same 16 wartości co województwo rejestracji. | wyliczona |

### Agregaty regionalne (sekcja 9 notebooka)

| Nazwa kolumny | Typ | Opis | Wartości / jednostka | Źródło |
|---|---|---|---|---|
| `n` | int64 | Liczba pojazdów w województwie po czyszczeniu. Województwa z `n < 100` są pomijane. | Liczba sztuk. | wyliczona |
| `udzial_importu` | float64 | Odsetek pojazdów z flagą `Import używany` w województwie. | % (0–100). | wyliczona |
| `udzial_diesla` | float64 | Odsetek pojazdów z napędem `Diesel` w województwie. | % (0–100). | wyliczona |

---

## Historia zmian

- **8 listopada 2026** – utworzenie słownika. Zmienne z API: 8 używanych oraz 5 pobieranych i nieużywanych. Zmienne wyliczone: 5 oraz 3 agregaty regionalne.
- **8 listopada 2026** – usunięto z notebooka `moc-netto-silnika` i `poziom-emisji-co2` z analiz (100% braków). Słownik to odzwierciedla.

## Jak aktualizować

Przy każdej nowej zmiennej w analizie dopisz wiersz do odpowiedniej tabeli (z API albo wyliczonej), podając typ, opis, wartości/jednostkę i źródło. Jeśli zmienna usunięta, przenieś ją do sekcji „nieużywane” z powodem zamiast kasować wiersz.
