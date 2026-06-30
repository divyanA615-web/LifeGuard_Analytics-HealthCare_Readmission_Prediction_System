"""Exploratory data analysis – produces a single Markdown style report and a
set of plots under ml/data/processed/plots/.

The script is intentionally lightweight: it's something you can wire into a
DVC stage for drift detection, but it does not block training.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

sys.path.append(str(Path(__file__).resolve().parents[1]))

from ml import DATA_PROCESSED, TARGET_COLUMN  # noqa: E402


def run() -> None:
    df = pd.read_parquet(DATA_PROCESSED / "diabetes_readmission.parquet")
    out_dir = DATA_PROCESSED / "plots"
    out_dir.mkdir(parents=True, exist_ok=True)

    summary = {
        "n": int(len(df)),
        "positives_rate": float(df[TARGET_COLUMN].mean()),
        "missing_rate_per_column": df.isna().mean().round(4).to_dict(),
        "numeric_stats": df.describe().round(2).T.to_dict(),
    }
    (out_dir / "eda_summary.json").write_text(json.dumps(summary, indent=2, default=str))

    fig, ax = plt.subplots(figsize=(8, 4))
    sns.countplot(x=df[TARGET_COLUMN].map({0: "Not Readmitted", 1: "Readmitted <30d"}), ax=ax)
    ax.set_title("Class balance")
    fig.tight_layout()
    fig.savefig(out_dir / "01_class_balance.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4))
    sns.histplot(df["age"], bins=20, kde=True, ax=ax)
    ax.set_title("Age distribution")
    fig.tight_layout()
    fig.savefig(out_dir / "02_age_distribution.png")
    plt.close(fig)

    numeric_cols = [
        "time_in_hospital",
        "num_lab_procedures",
        "num_procedures",
        "num_medications",
        "number_outpatient",
        "number_emergency",
        "number_inpatient",
        "number_diagnoses",
    ]
    corr = df[numeric_cols + [TARGET_COLUMN]].corr()
    fig, ax = plt.subplots(figsize=(9, 7))
    sns.heatmap(corr, vmin=-1, vmax=1, cmap="coolwarm", annot=True, fmt=".2f", ax=ax)
    ax.set_title("Correlation heatmap")
    fig.tight_layout()
    fig.savefig(out_dir / "03_correlation_heatmap.png")
    plt.close(fig)
    print(f"EDA artefacts written to {out_dir}")


if __name__ == "__main__":
    run()
