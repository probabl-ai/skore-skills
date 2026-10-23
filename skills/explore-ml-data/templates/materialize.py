"""Agent-only materialize. Copy to scratch/data_analysis/materialize.py.

Do not commit. This is the only EDA run. Do not execute
``data_analysis/data_analysis.py`` and do not ``notebook convert``
or ``cells run`` it. Replace the ``<ANALYSIS>`` block with that
file's loads, ``TableReport.html_snippet`` writes, and figure or HTML
saves, same paths. One load per family. Bind ``FAMILIES`` as
``(slug, raw)`` and ``FRAME`` to the pandas frame that contains
every target (the first family when there is no target).
Leave the tail. It writes ``<slug>.json``
(``plot_distributions=False``) and ``extras.json``.
"""

import json

import matplotlib

matplotlib.use("Agg")

import pandas as pd
import seaborn as sns
import skrub

from <pkg> import PROJECT_ROOT

TARGETS = <TARGETS>  # list of column names; [] when there is no target
TASKS = <TASKS>  # parallel list: classification | regression

analysis = PROJECT_ROOT / "data_analysis"
analysis.mkdir(parents=True, exist_ok=True)
out = PROJECT_ROOT / "scratch" / "data_analysis"
out.mkdir(parents=True, exist_ok=True)

# <ANALYSIS>
FAMILIES = [
    ("<slug>", <LOAD_RAW_DATA>),
]
FRAME = None
for slug, raw in FAMILIES:
    frame = raw.to_pandas() if hasattr(raw, "to_pandas") else raw
    report = skrub.TableReport(raw, title=slug, verbose=0)
    (analysis / f"data_analysis_{slug}.html").write_text(
        report.html_snippet(), encoding="utf-8"
    )
    holds_targets = not TARGETS or all(column in frame.columns for column in TARGETS)
    if FRAME is None and holds_targets:
        FRAME = frame
# Figure and extra HTML saves from the human file, same paths.
# </ANALYSIS>

report_html_names = {f"data_analysis_{slug}.html" for slug, _raw in FAMILIES}
table_rows: list[dict] = []

for slug, raw in FAMILIES:
    frame = raw.to_pandas() if hasattr(raw, "to_pandas") else raw
    report = skrub.TableReport(
        raw, title=slug, verbose=0, plot_distributions=False
    )
    (out / f"{slug}.json").write_text(report.json(), encoding="utf-8")
    n_dup = int(frame.duplicated().sum())
    n_rows = int(len(frame))
    has_target = bool(TARGETS) and all(column in frame.columns for column in TARGETS)
    table_rows.append(
        {
            "slug": slug,
            "n_rows": n_rows,
            "n_duplicate_rows": n_dup,
            "duplicate_rate": n_dup / n_rows if n_rows else 0.0,
            "has_target": has_target,
        }
    )

if FRAME is None:
    _, raw0 = FAMILIES[0]
    FRAME = raw0.to_pandas() if hasattr(raw0, "to_pandas") else raw0

pngs = sorted(p.name for p in analysis.glob("*.png"))
htmls = sorted(
    p.name
    for p in analysis.glob("*.html")
    if p.name not in report_html_names and not p.name.endswith(".nb.html")
)


def _number(value: object) -> float | None:
    if value is None or pd.isna(value):
        return None
    return float(value)


target_rows: list[dict] = []
present = [column for column in TARGETS if column in FRAME.columns]
for column, task in zip(TARGETS, TASKS, strict=True):
    if column not in FRAME.columns:
        continue
    series = FRAME[column]
    observed = series.dropna()
    record: dict = {
        "column": column,
        "task": task,
        "missing_count": int(series.isna().sum()),
        "missing_rate": float(series.isna().mean()) if len(series) else 0.0,
        "skew": None,
        "scale": None,
        "class_counts": None,
        "feature_target_corr": [],
        "leakage_flags": [],
    }
    if task == "classification":
        record["class_counts"] = {
            str(key): int(value)
            for key, value in series.value_counts(dropna=False).items()
        }
    if pd.api.types.is_numeric_dtype(series) and not observed.empty:
        record["skew"] = _number(observed.skew()) if len(observed) > 1 else None
        record["scale"] = {
            "min": _number(observed.min()),
            "max": _number(observed.max()),
            "mean": _number(observed.mean()),
            "std": _number(observed.std()) if len(observed) > 1 else None,
        }
        others = FRAME.drop(columns=present, errors="ignore").select_dtypes("number")
        if not others.empty:
            corr = others.corrwith(series).abs().sort_values(ascending=False)
            record["feature_target_corr"] = [
                {"column": feature, "abs_pearson": float(val)}
                for feature, val in corr.items()
                if pd.notna(val)
            ][:20]
            record["leakage_flags"] = [
                f"{row['column']} abs(Pearson) vs {column} = {row['abs_pearson']:.3f}"
                for row in record["feature_target_corr"]
                if row["abs_pearson"] >= 0.99
            ]
    if task == "classification":
        features = FRAME.drop(columns=present, errors="ignore")
        for feature in features.columns:
            rates = FRAME.groupby(series, dropna=False)[feature].apply(
                lambda values: values.isna().mean()
            )
            if rates.max() - rates.min() >= 0.5:
                record["leakage_flags"].append(
                    f"{feature} null rate differs by class: {rates.to_dict()}"
                )
    target_rows.append(record)

target_target_corr: list[dict] = []
numeric_targets = [
    column
    for column in present
    if pd.api.types.is_numeric_dtype(FRAME[column])
]
if len(numeric_targets) >= 2:
    corr = FRAME[numeric_targets].corr()
    for index, left in enumerate(numeric_targets):
        for right in numeric_targets[index + 1 :]:
            value = _number(corr.loc[left, right])
            if value is not None:
                target_target_corr.append(
                    {"left": left, "right": right, "pearson": value}
                )

extras: dict = {
    "tables": table_rows,
    "n_rows": table_rows[0]["n_rows"] if table_rows else 0,
    "n_duplicate_rows": table_rows[0]["n_duplicate_rows"] if table_rows else 0,
    "duplicate_rate": table_rows[0]["duplicate_rate"] if table_rows else 0.0,
    "targets": target_rows,
    "complete_target_rows": (
        int(FRAME[present].notna().all(axis=1).sum()) if present else None
    ),
    "target_target_corr": target_target_corr,
    "pngs": pngs,
    "htmls": htmls,
}

(out / "extras.json").write_text(
    json.dumps(extras, default=str), encoding="utf-8"
)
