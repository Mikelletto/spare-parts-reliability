# Plan pozyskiwania danych – Check Engine Team

**Projekt:** Segmentacja i profilowanie regionalnych rynków motoryzacyjnych w Polsce
**Ostatnia aktualizacja:** 22 listopada 2026

## Źródła danych

| Źródło / URL / API | Format | Metoda pobrania | Kto odpowiada | Termin (próbka) |
|---|---|---|---|---|
| CEPiK – pojazdy: `https://api.cepik.gov.pl/pojazdy` | JSON | `requests` (sesja z retry, adapter TLS `SECLEVEL=1`, `verify=False`), 48 zapytań (województwo × okres), `limit=500`, strona 1 | Do przypisania | Próbka zrealizowana (23 000 rekordów). Pełne pobranie z paginacją: przed Spotkaniem 4. |
| GUS BDL – ludność i liczba pojazdów wg województw: `https://bdl.stat.gov.pl/api/v1` | JSON | `requests` (REST), normalizacja na 1000 mieszkańców. *Do weryfikacji: wymagany klucz API.* | Do przypisania | Przed Spotkaniem 4 (do potwierdzenia). |
| Sprzedaż nowych samochodów wg województw (dane branżowe, opcjonalnie) | CSV / PDF | Ręczne pobranie, bez API. *Niepewna dostępność.* | Do przypisania | Do ustalenia. Jeśli niedostępne, pomijamy. |

## Źródła, których nie planujemy

- **Scraping stron ogłoszeniowych** – nie jest planowany. Wszystkie źródła to oficjalne API lub dane publiczne, więc nie wymaga to sprawdzania `robots.txt` ani warunków użytkowania.

## Ograniczenia i ryzyka

- **Próbka CEPiK:** maks. 500 rekordów na zapytanie (województwo × okres, strona 1). Nie jest pełną populacją. Wnioski regionalne trzeba opisywać jako próbkę, dopóki nie zostanie wdrożona paginacja.
- **Nieudane zapytanie:** DOLNOŚLĄSKIE 2025 (uszkodzony JSON). Do ponowienia przy pełnym pobraniu.
- **Brak danych zastępczych:** pobieranie kończy się błędem, jeśli liczba rekordów jest poniżej progu (5 000). Dane syntetyczne nie są używane.

## Historia zmian

- **22 listopada 2026** – pierwsza wersja planu pozyskiwania danych.
