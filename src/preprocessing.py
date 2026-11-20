from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


RANDOM_STATE = 42
ROOT = Path(__file__).resolve().parents[1]
RAW_DIR_CANDIDATES = (ROOT / "data" / "raw", ROOT / "notebooks" / "data" / "raw")
OUTPUT_DIR = ROOT / "data" / "processed"
MAX_OUTPUT_ROWS = 250_000


def find_raw_files() -> list[Path]:
    raw_files = []
    for directory in RAW_DIR_CANDIDATES:
        raw_files.extend(sorted(directory.glob("*.csv")))
    if not raw_files:
        raise FileNotFoundError(
            "Nie znaleziono plików CSV. Oczekiwano data/raw/*.csv "
            "lub notebooks/data/raw/*.csv."
        )
    return raw_files


def normalize_fuel(value: object) -> str:
    if pd.isna(value) or str(value).strip() == "":
        return "Brak"
    text = str(value).strip().upper()
    if text == "BENZYNA":
        return "Benzyna"
    if text == "OLEJ NAPĘDOWY":
        return "Diesel"
    if text == "ENERGIA ELEKTRYCZNA":
        return "Elektryczny (BEV)"
    if text in {"GAZ ZIEMNY SKROPLONY METAN", "GAZ ZIEMNY SPRĘŻONY METAN",
                "GAZ PŁYNNY PROPAN-BUTAN"}:
        return "Gaz"
    return "Inne"


def add_outlier_flags(df: pd.DataFrame) -> pd.DataFrame:
    for column in ("pojemnosc-skokowa-silnika", "masa-wlasna", "rok-produkcji"):
        mean = df[column].mean()
        std = df[column].std(ddof=0)
        if pd.isna(std) or std == 0:
            df[f"outlier_3sigma_{column}"] = False
        else:
            df[f"outlier_3sigma_{column}"] = (
                (df[column] < mean - 3 * std) | (df[column] > mean + 3 * std)
            )
    return df


def load_and_clean(raw_files: list[Path]) -> tuple[pd.DataFrame, dict]:
    frames = []
    for path in raw_files:
        frames.append(pd.read_csv(path, encoding="utf-8-sig"))
    raw = pd.concat(frames, ignore_index=True)

    audit = {"raw_rows": len(raw), "raw_columns": len(raw.columns)}

    required = [
        "rodzaj-paliwa", "marka", "rok-produkcji",
        "data-pierwszej-rejestracji-w-kraju", "rejestracja-wojewodztwo",
        "rodzaj-pojazdu", "pojemnosc-skokowa-silnika", "masa-wlasna",
    ]
    missing_columns = [column for column in required if column not in raw.columns]
    if missing_columns:
        raise ValueError(f"Brak wymaganych kolumn: {missing_columns}")

    before = len(raw)
    raw = raw.drop_duplicates()
    audit["duplicates_removed"] = before - len(raw)

    df = raw.copy()
    df["data-pierwszej-rejestracji-w-kraju"] = pd.to_datetime(
        df["data-pierwszej-rejestracji-w-kraju"], format="%Y-%m-%d", errors="coerce"
    )
    df["rok_rejestracji"] = df["data-pierwszej-rejestracji-w-kraju"].dt.year
    df["rok-produkcji"] = pd.to_numeric(df["rok-produkcji"], errors="coerce")
    df["pojemnosc-skokowa-silnika"] = pd.to_numeric(
        df["pojemnosc-skokowa-silnika"], errors="coerce"
    )
    df["masa-wlasna"] = pd.to_numeric(df["masa-wlasna"], errors="coerce")

    df = df[df["rodzaj-pojazdu"].astype(str).str.strip().str.upper() == "SAMOCHÓD OSOBOWY"]
    df = df[df["masa-wlasna"].between(500, 3500)]
    df = df[df["pojemnosc-skokowa-silnika"].between(50, 7000)]
    df = df[df["rok-produkcji"].between(1900, 2026)]
    df = df[df["rok_rejestracji"].between(2000, 2026)]

    df["wiek_pojazdu"] = df["rok_rejestracji"] - df["rok-produkcji"]
    df = df[df["wiek_pojazdu"].between(0, 60)]

    df["pochodzenie"] = np.where(df["wiek_pojazdu"] > 1,
                                 "Import używany", "Krajowy (Nowy)")
    df["Naped"] = df["rodzaj-paliwa"].map(normalize_fuel)
    df["marka_normalized"] = df["marka"].fillna("BRAK").astype(str).str.strip().str.upper()

    top_brands = df["marka_normalized"].value_counts().head(30).index
    df["marka_normalized"] = np.where(
        df["marka_normalized"].isin(top_brands), df["marka_normalized"], "INNE"
    )

    df["hub_flotowy"] = df["rejestracja-wojewodztwo"].isin(
        ["MAZOWIECKIE", "WIELKOPOLSKIE"]
    ).astype(int)
    df["wiek_kategoria"] = pd.cut(
        df["wiek_pojazdu"],
        bins=[-1, 1, 5, 10, 20, 60],
        labels=["0-1", "2-5", "6-10", "11-20", "21+"],
    ).astype(str)
    df["pojemnosc_na_mase"] = (
        df["pojemnosc-skokowa-silnika"] / df["masa-wlasna"]
    )
    df["masa_log"] = np.log1p(df["masa-wlasna"])
    df["pojemnosc_log"] = np.log1p(df["pojemnosc-skokowa-silnika"])
    df = add_outlier_flags(df)

    if len(df) > MAX_OUTPUT_ROWS:
        df = df.sample(n=MAX_OUTPUT_ROWS, random_state=RANDOM_STATE)

    audit["clean_rows"] = len(df)
    audit["rows_removed_by_cleaning"] = audit["raw_rows"] - len(df)
    audit["target_distribution"] = df["pochodzenie"].value_counts().to_dict()
    audit["random_state"] = RANDOM_STATE
    return df.reset_index(drop=True), audit


def main() -> None:
    raw_files = find_raw_files()
    df, audit = load_and_clean(raw_files)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_csv = OUTPUT_DIR / "cepik_model.csv"
    df.to_csv(output_csv, index=False, encoding="utf-8-sig")

    audit["output_csv"] = str(output_csv.relative_to(ROOT))
    audit["source_files"] = [str(path.relative_to(ROOT)) for path in raw_files]
    (OUTPUT_DIR / "preprocessing_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Zapisano {len(df)} wierszy do {output_csv}")
    print(json.dumps(audit, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
