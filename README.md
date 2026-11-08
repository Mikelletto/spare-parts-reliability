# Koncepcja – rewizja po EDA

**Data:** 8 listopada 2026
**Status:** wersja robocza. Wnioski oznaczone *do weryfikacji* wymagają potwierdzenia na pełnym pobraniu danych.

## 1. Stan wyjściowy

Pierwotne pytanie z raportu: jak zróżnicowane są regionalne rynki motoryzacyjne w Polsce pod względem wieku pojazdów, napędu i udziału importu oraz jak przypisać pakiety asortymentowe do profili województw (K-Means, 3 klastry). Dodatkowo: klasyfikator „import vs salon”.

## 2. Co pokazała EDA

- **Próbka, nie populacja.** API zwraca maks. 500 rekordów na zapytanie (województwo × okres, strona 1). Porównania regionalne są przez to obciążone limitem.
- **Kolumny puste w 100%:** właściciel, emisja CO2, moc netto, paliwa alternatywne. Wykluczone z analiz.
- **Braki:** `rodzaj-paliwa` 8,3%, `pojemnosc-skokowa-silnika` 9,4%, `marka` 2,7%.
- **Duży ubytek przy czyszczeniu:** 23 000 → 15 900 rekordów (output `Untitled23`). Które reguły tną najwięcej, nie jest jeszcze wiadome.
- **Jedno nieudane zapytanie:** DOLNOŚLĄSKIE 2025 (uszkodzony JSON).
- **Flaga importu to przybliżenie:** `wiek > 1 rok` nie jest informacją o pochodzeniu pojazdu.
- **Rejestracja w województwie nie oddaje miejsca sprzedaży.** Huby poleasingowe (MAZOWIECKIE, WIELKOPOLSKIE) zniekształcają obraz.

## 3. Rewizja pytań badawczych

| # | Pytanie pierwotne | Pytanie po rewizji | Uzasadnienie |
|---|---|---|---|
| Q1 | Jak różnią się rynki regionalne (wiek, napęd, import)? | Ten sam kierunek, ale jako opis z przedziałami ufności i zastrzeżeniem o próbie. | Po EDA stwierdzono, że dane pozwalają na opis próbki, a nie na wnioski o populacji bez pełnego pobrania. |
| Q2 | Klasteryzacja 16 województw w 3 profile (K-Means). | Segmenty na poziomie pojazdów (wiek, pojemność, masa, napęd) w obrębie województw. Województwa opisywane udziałami segmentów. | Po EDA stwierdzono, że 14–15 obserwacji to za mało na stabilny K-Means. Klasteryzacja pojazdów daje ~12 tys. obserwacji. *Do weryfikacji: stabilność klastrów (bootstrap, wiele seedów).* |
| Q3 | Klasyfikator „import vs salon”. | Ten sam cel, ale bez zmiennych wiekowych w cechach. | Po przeglądzie kodu stwierdzono ryzyko wycieku danych: etykieta jest funkcją `wiek_pojazdu`, więc `wiek_pojazdu`, `rok-produkcji` i `rok_rejestracji` musiałyby zostać wykluczone. Inaczej model odtworzy próg. |

## 4. Zmienne: obiecujące i pomijane

| Zmienna | Decyzja | Uzasadnienie |
|---|---|---|
| `pochodzenie` | Cel (Q3) | Etykieta z progu wieku. Traktować jako przybliżenie. |
| `wiek_pojazdu` | Opis (Q1, Q2). **Wykluczona z cech Q3.** | Obiecująca w opisie. Wyciek w klasyfikatorze. |
| `pojemnosc-skokowa-silnika` | Obiecująca | Ciągła, braki 9,4%. |
| `masa-wlasna` | Obiecująca | Ciągła. Pomocna przy segmentacji. |
| `Naped` (z `rodzaj-paliwa`) | Obiecująca | Diesel / Benzyna / BEV. Kategorię `Inne` trzeba rozbić po obsłudze braków. |
| `marka` | Obiecująca z zastrzeżeniem | Wymaga normalizacji nazw. Wysoka kardynalność – grupować. |
| `rejestracja-wojewodztwo` | Obiecująca | Podstawa analiz regionalnych. Hub flotowy jako flaga. |
| `rok-produkcji`, `rok_rejestracji` | Pomijane jako cechy | Redundantne z wiekiem, wyciek w Q3. |
| `model` | Pomijana | Wysoka kardynalność, mało czasu na inżynierię cech. |
| `wlasciciel-wojewodztwo`, `poziom-emisji-co2`, `moc-netto-silnika`, paliwa alternatywne | Pominięte | 100% braków w próbce. |
| `udzial_importu`, `udzial_diesla` | Agregaty do opisu regionów | Nie są cechami modelu. |

## 5. Dodatkowe dane

| Dane | Potrzebne do | Realność przed Spotkaniem 5 | Uwagi |
|---|---|---|---|
| Pełne pobranie z CEPiK (paginacja) | Wszystkich pytań | **Wysoka, jeśli API obsługuje paginację** | Wymaga sprawdzenia dokumentacji API. Priorytet nr 1. |
| Liczba ludności / pojazdów wg województw (GUS BDL) | Normalizacja (pojazdów na 1000 mieszkańców) | Wysoka | Dane publiczne. Sprawdzić granularność i lata 2023–2025. |
| Sprzedaż nowych samochodów wg województw | Udział nowych vs używanych | Niska–średnia | Może wymagać danych branżowych. Nie zakładać dostępności. |

## 6. Dobór metod

- **Q1 (opis):** statystyki opisowe, udziały z przedziałami ufności (bootstrap lub przedziały Wilsona dla proporcji), testy różnic między województwami z korektą na wielokrotne porównania.
- **Q2 (segmenty):** K-Means na poziomie pojazdów po standaryzacji, z oceną stabilności (wiele seedów, silhouette). Alternatywa: GMM. Dla samych województw – tylko opis, bez klasteryzacji.
- **Q3 (klasyfikacja):** regresja logistyczna jako punkt odniesienia, następnie gradient boosting (LightGBM lub XGBoost). Podział z uwzględnieniem województwa. Metryki: PR-AUC i ROC-AUC, przy niezbalansowanej klasie także kalibracja. *Do weryfikacji: proporcje klas.*

## 7. Harmonogram (do uzupełnienia)

| Etap | Termin | Właściciel |
|---|---|---|
| Pełne pobranie CEPiK (paginacja) | Tydzień 1 | Do przypisania |
| Dane referencyjne (GUS) | Tydzień 1 | Do przypisania |
| EDA na pełnych danych, aktualizacja tego dokumentu | Tydzień 2 | Zespół |
| Modele Q2 i Q3 | Tydzień 2–3 | Do przypisania |
| Spotkanie 5 | Data do potwierdzenia | Zespół |

## 8. Otwarte decyzje

1. Czy zachować K-Means na województwach po wykluczeniu hubów (mała próba), czy przejść na sam opis.
2. Czy zostaje próg 1 roku dla importu, czy testujemy alternatywną definicję.
3. Kto zdobywa dane referencyjne i sprawdza paginację API.

## Historia zmian

- **8 listopada 2026** – pierwsza rewizja po EDA (wersja robocza).
