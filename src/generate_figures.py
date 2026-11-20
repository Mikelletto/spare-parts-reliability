"""Skrypt generujący wykresy do raportu midterm (SVG oraz PNG >= 150 DPI).

Projekt: Check Engine Team - Segmentacja rynków motoryzacyjnych (CEPiK).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "processed" / "cepik_model.csv"
RESULTS_PATH = ROOT / "data" / "processed" / "model_results.json"
FIG_DIR = ROOT / "reports" / "figures"


def setup_style() -> None:
    style_name = "seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default"
    plt.style.use(style_name)
    plt.rcParams["font.sans-serif"] = "DejaVu Sans"
    plt.rcParams["axes.edgecolor"] = "#cccccc"
    plt.rcParams["axes.linewidth"] = 0.8


def generate_figures() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    setup_style()

    print(f"Wczytywanie danych z {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)

    # --- FIG 1: Rozkład wieku i pojemności silnika ---
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), dpi=300)

    sns.histplot(
        data=df[df["wiek_pojazdu"] <= 30],
        x="wiek_pojazdu",
        hue="pochodzenie",
        bins=30,
        kde=True,
        palette={"Import używany": "#d95f02", "Krajowy (Nowy)": "#1b9e77"},
        ax=axes[0],
        multiple="stack",
    )
    axes[0].set_title("Dwumodalny rozkład wieku rejestrowanych pojazdów", fontsize=12, fontweight="bold", pad=10)
    axes[0].set_xlabel("Wiek pojazdu w momencie rejestracji (lata)", fontsize=10)
    axes[0].set_ylabel("Liczba pojazdów w próbie", fontsize=10)
    axes[0].axvline(1.0, color="black", linestyle="--", linewidth=1.5, label="Próg importu (1 rok)")
    axes[0].legend(title="Pochodzenie")

    age_cap = (
        df.groupby("wiek_kategoria")["pojemnosc-skokowa-silnika"]
        .mean()
        .reindex(["0-1", "2-5", "6-10", "11-20", "21+"])
    )
    sns.barplot(
        x=age_cap.index,
        y=age_cap.values,
        hue=age_cap.index,
        palette="Blues_d",
        ax=axes[1],
        legend=False,
    )
    axes[1].set_title("Średnia pojemność skokowa silnika wg grup wiekowych", fontsize=12, fontweight="bold", pad=10)
    axes[1].set_xlabel("Kategoria wieku (lata)", fontsize=10)
    axes[1].set_ylabel("Średnia pojemność silnika (cm³)", fontsize=10)
    for p in axes[1].patches:
        h = p.get_height()
        if not np.isnan(h):
            axes[1].annotate(
                f"{h:.0f} cm³",
                (p.get_x() + p.get_width() / 2.0, h - 150),
                ha="center",
                va="center",
                fontsize=9,
                color="white",
                fontweight="bold",
            )

    plt.tight_layout()
    plt.savefig(FIG_DIR / "fig1_age_distribution.svg", format="svg")
    plt.savefig(FIG_DIR / "fig1_age_distribution.png", dpi=300)
    plt.close()
    print("Zapisano Rysunek 1.")

    # --- FIG 2: Zróżnicowanie regionalne (import i diesel) ---
    fig, axes = plt.subplots(1, 2, figsize=(15, 6), dpi=300)

    reg_stats = (
        df.groupby("rejestracja-wojewodztwo")
        .agg(
            total=("pochodzenie", "count"),
            import_cnt=("pochodzenie", lambda s: (s == "Import używany").sum()),
            diesel_cnt=("Naped", lambda s: (s == "Diesel").sum()),
        )
        .reset_index()
    )
    reg_stats["pct_import"] = 100 * reg_stats["import_cnt"] / reg_stats["total"]
    reg_stats["pct_diesel"] = 100 * reg_stats["diesel_cnt"] / reg_stats["total"]
    reg_stats["is_hub"] = reg_stats["rejestracja-wojewodztwo"].isin(["MAZOWIECKIE", "WIELKOPOLSKIE"])

    reg_sort_import = reg_stats.sort_values("pct_import", ascending=True)
    colors_import = ["#e7298a" if hub else "#386cb0" for hub in reg_sort_import["is_hub"]]

    axes[0].barh(reg_sort_import["rejestracja-wojewodztwo"], reg_sort_import["pct_import"], color=colors_import)
    axes[0].set_title("Udział pojazdów z importu wg województw (%)", fontsize=12, fontweight="bold", pad=10)
    axes[0].set_xlabel("Odsetek aut z importu (%)", fontsize=10)
    axes[0].axvline(df["pochodzenie"].eq("Import używany").mean() * 100, color="red", linestyle="--", label="Średnia krajowa")
    axes[0].legend(loc="lower right")

    reg_sort_diesel = reg_stats.sort_values("pct_diesel", ascending=True)
    colors_diesel = ["#e7298a" if hub else "#7570b3" for hub in reg_sort_diesel["is_hub"]]
    axes[1].barh(reg_sort_diesel["rejestracja-wojewodztwo"], reg_sort_diesel["pct_diesel"], color=colors_diesel)
    axes[1].set_title("Udział silników Diesla wg województw (%)", fontsize=12, fontweight="bold", pad=10)
    axes[1].set_xlabel("Odsetek Diesli (%)", fontsize=10)
    axes[1].axvline(df["Naped"].eq("Diesel").mean() * 100, color="red", linestyle="--", label="Średnia krajowa")
    axes[1].legend(loc="lower right")

    plt.tight_layout()
    plt.savefig(FIG_DIR / "fig2_regional_analysis.svg", format="svg")
    plt.savefig(FIG_DIR / "fig2_regional_analysis.png", dpi=300)
    plt.close()
    print("Zapisano Rysunek 2.")

    # --- FIG 3: Porównanie modeli i macierze pomyłek ---
    with open(RESULTS_PATH, "r", encoding="utf-8") as f:
        results = json.load(f)

    fig = plt.figure(figsize=(15, 5), dpi=300)
    gs = fig.add_gridspec(1, 3, width_ratios=[1.2, 1, 1])
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[0, 2])

    models_names = ["Dummy Baseline", "Regresja Logistyczna", "Random Forest"]
    accs = [
        results["models"]["dummy_baseline"]["accuracy"],
        results["models"]["logistic_regression"]["accuracy"],
        results["models"]["random_forest"]["accuracy"],
    ]
    f1s = [
        results["models"]["dummy_baseline"]["f1_macro"],
        results["models"]["logistic_regression"]["f1_macro"],
        results["models"]["random_forest"]["f1_macro"],
    ]
    rocs = [
        results["models"]["dummy_baseline"]["roc_auc"],
        results["models"]["logistic_regression"]["roc_auc"],
        results["models"]["random_forest"]["roc_auc"],
    ]

    x = np.arange(len(models_names))
    w = 0.25
    ax1.bar(x - w, accs, width=w, label="Accuracy", color="#6baed6")
    ax1.bar(x, f1s, width=w, label="F1 Macro", color="#3182bd")
    ax1.bar(x + w, rocs, width=w, label="ROC-AUC", color="#08519c")
    ax1.set_xticks(x)
    ax1.set_xticklabels(models_names, rotation=15, ha="right", fontsize=9)
    ax1.set_ylim(0, 1.05)
    ax1.set_title("Zestawienie metryk modeli", fontsize=12, fontweight="bold", pad=10)
    ax1.set_ylabel("Wartość metryki", fontsize=10)
    ax1.legend(loc="lower right", fontsize=8)

    for rect in ax1.patches:
        h = rect.get_height()
        if h > 0:
            ax1.annotate(
                f"{h:.2f}",
                (rect.get_x() + rect.get_width() / 2.0, h + 0.02),
                ha="center",
                va="bottom",
                fontsize=8,
            )

    labels = ["Import używany", "Krajowy (Nowy)"]

    cm_lr = np.array(results["models"]["logistic_regression"]["confusion_matrix"])
    cm_lr_norm = cm_lr.astype("float") / cm_lr.sum(axis=1)[:, np.newaxis]
    sns.heatmap(
        cm_lr_norm,
        annot=True,
        fmt=".2%",
        cmap="Blues",
        cbar=False,
        ax=ax2,
        xticklabels=labels,
        yticklabels=labels,
    )
    ax2.set_title("Macierz błędu: Regresja Logistyczna", fontsize=11, fontweight="bold", pad=10)
    ax2.set_xlabel("Przewidziane", fontsize=9)
    ax2.set_ylabel("Rzeczywiste", fontsize=9)

    cm_rf = np.array(results["models"]["random_forest"]["confusion_matrix"])
    cm_rf_norm = cm_rf.astype("float") / cm_rf.sum(axis=1)[:, np.newaxis]
    sns.heatmap(
        cm_rf_norm,
        annot=True,
        fmt=".2%",
        cmap="Greens",
        cbar=False,
        ax=ax3,
        xticklabels=labels,
        yticklabels=labels,
    )
    ax3.set_title("Macierz błędu: Random Forest", fontsize=11, fontweight="bold", pad=10)
    ax3.set_xlabel("Przewidziane", fontsize=9)
    ax3.set_ylabel("Rzeczywiste", fontsize=9)

    plt.tight_layout()
    plt.savefig(FIG_DIR / "fig3_model_evaluation.svg", format="svg")
    plt.savefig(FIG_DIR / "fig3_model_evaluation.png", dpi=300)
    plt.close()
    print("Zapisano Rysunek 3.")


if __name__ == "__main__":
    generate_figures()