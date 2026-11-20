from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


RANDOM_STATE = 42
ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "processed" / "cepik_model.csv"
RESULTS_PATH = ROOT / "data" / "processed" / "model_results.json"


def main() -> None:
    df = pd.read_csv(DATA_PATH)
    target = "pochodzenie"

    numeric = [
        "pojemnosc-skokowa-silnika",
        "masa-wlasna",
        "pojemnosc_na_mase",
        "masa_log",
        "pojemnosc_log",
        "hub_flotowy",
    ]
    categorical = ["Naped", "marka_normalized", "rejestracja-wojewodztwo"]
    # Wiek, rok produkcji i rok rejestracji są celowo wykluczone:
    # pochodzenie jest zdefiniowane na podstawie wieku, więc ich użycie byłoby wyciekiem.

    X = df[numeric + categorical].copy()
    y = df[target]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    preprocessing = ColumnTransformer([
        ("numeric", StandardScaler(), numeric),
        ("categorical", OneHotEncoder(handle_unknown="ignore"), categorical),
    ])

    models = {
        "dummy_baseline": Pipeline([
            ("preprocess", preprocessing),
            ("model", DummyClassifier(strategy="most_frequent", random_state=RANDOM_STATE)),
        ]),
        "logistic_regression": Pipeline([
            ("preprocess", preprocessing),
            ("model", LogisticRegression(
                max_iter=500,
                random_state=RANDOM_STATE,
                class_weight="balanced",
            )),
        ]),
        "random_forest": Pipeline([
            ("preprocess", preprocessing),
            ("model", RandomForestClassifier(
                n_estimators=80,
                max_depth=12,
                min_samples_leaf=5,
                random_state=RANDOM_STATE,
                n_jobs=-1,
                class_weight="balanced",
            )),
        ]),
    }

    results = {
        "random_state": RANDOM_STATE,
        "validation": "single 80/20 stratified train/test split",
        "train_rows": len(X_train),
        "test_rows": len(X_test),
        "models": {},
    }

    for name, model in models.items():
        model.fit(X_train, y_train)
        prediction = model.predict(X_test)

        probability = None
        if hasattr(model, "predict_proba"):
            try:
                import_index = list(model.classes_).index("Import używany")
                probability = model.predict_proba(X_test)[:, import_index]
            except (AttributeError, ValueError):
                probability = None

        metrics = {
            "accuracy": float(accuracy_score(y_test, prediction)),
            "f1_macro": float(f1_score(y_test, prediction, average="macro")),
            "f1_weighted": float(f1_score(y_test, prediction, average="weighted")),
            "confusion_matrix": confusion_matrix(
                y_test, prediction, labels=sorted(y_test.unique())
            ).tolist(),
            "labels": sorted(y_test.unique()),
        }
        if probability is not None:
            metrics["roc_auc"] = float(
                roc_auc_score((y_test == "Import używany").astype(int), probability)
            )

        results["models"][name] = metrics

    RESULTS_PATH.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
