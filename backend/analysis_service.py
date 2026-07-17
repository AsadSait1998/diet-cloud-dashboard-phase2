"""Dataset cleaning and aggregation logic shared by Azure Functions and local demo."""

from __future__ import annotations

import csv
import io
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Iterable


ALIASES = {
    "Diet_type": ("Diet_type", "Diet type", "diet_type"),
    "Recipe_name": ("Recipe_name", "Recipe name", "recipe_name"),
    "Cuisine_type": ("Cuisine_type", "Cuisine type", "cuisine_type"),
    "Protein(g)": ("Protein(g)", "Protein (g)", "protein"),
    "Carbs(g)": ("Carbs(g)", "Carbs (g)", "carbs"),
    "Fat(g)": ("Fat(g)", "Fat (g)", "fat"),
}

MACRO_COLUMNS = ("Protein(g)", "Carbs(g)", "Fat(g)")


def _normalized_header(value: str) -> str:
    return "".join(character for character in str(value).casefold() if character.isalnum())


def _display_label(value: Any, fallback: str) -> str:
    cleaned = " ".join(str(value or "").strip().split())
    return cleaned.title() if cleaned else fallback


def _number(value: Any) -> float | None:
    try:
        result = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    if result != result or result in (float("inf"), float("-inf")):
        return None
    return result


def clean_csv_bytes(raw_csv: bytes) -> list[dict[str, Any]]:
    """Decode, validate, normalize, and mean-impute the Diets CSV."""

    text = raw_csv.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise ValueError("The dataset has no header row.")

    normalized_actual = {_normalized_header(name): name for name in reader.fieldnames}
    resolved: dict[str, str] = {}
    missing: list[str] = []
    for canonical, aliases in ALIASES.items():
        actual = next(
            (normalized_actual[_normalized_header(alias)] for alias in aliases if _normalized_header(alias) in normalized_actual),
            None,
        )
        if actual:
            resolved[canonical] = actual
        else:
            missing.append(canonical)
    if missing:
        raise ValueError(f"Dataset is missing required columns: {', '.join(missing)}")

    rows: list[dict[str, Any]] = []
    numeric_values: dict[str, list[float]] = {column: [] for column in MACRO_COLUMNS}
    for source_row in reader:
        row: dict[str, Any] = {
            "Diet_type": _display_label(source_row.get(resolved["Diet_type"]), "Unknown"),
            "Recipe_name": " ".join(
                str(source_row.get(resolved["Recipe_name"]) or "Unknown Recipe").strip().split()
            ),
            "Cuisine_type": _display_label(source_row.get(resolved["Cuisine_type"]), "Unknown"),
        }
        for column in MACRO_COLUMNS:
            value = _number(source_row.get(resolved[column]))
            row[column] = value
            if value is not None:
                numeric_values[column].append(value)
        rows.append(row)

    if not rows:
        raise ValueError("The dataset contains no data rows.")

    means = {
        column: (sum(values) / len(values) if values else 0.0)
        for column, values in numeric_values.items()
    }
    for row in rows:
        for column in MACRO_COLUMNS:
            if row[column] is None:
                row[column] = means[column]
            row[column] = round(float(row[column]), 4)
    return rows


def _average(rows: Iterable[dict[str, Any]], column: str) -> float:
    values = [float(row[column]) for row in rows]
    return round(sum(values) / len(values), 2) if values else 0.0


def _apply_filters(
    rows: list[dict[str, Any]],
    diet_types: list[str] | None,
    cuisine: str | None,
    search: str | None,
) -> list[dict[str, Any]]:
    requested_diets = {value.casefold() for value in (diet_types or []) if value.strip()}
    cuisine_key = (cuisine or "").strip().casefold()
    search_key = (search or "").strip().casefold()

    def matches(row: dict[str, Any]) -> bool:
        if requested_diets and row["Diet_type"].casefold() not in requested_diets:
            return False
        if cuisine_key and row["Cuisine_type"].casefold() != cuisine_key:
            return False
        if search_key:
            searchable = " ".join(
                (row["Recipe_name"], row["Diet_type"], row["Cuisine_type"])
            ).casefold()
            if search_key not in searchable:
                return False
        return True

    return [row for row in rows if matches(row)]


def build_dashboard_payload(
    rows: list[dict[str, Any]],
    *,
    diet_types: list[str] | None = None,
    cuisine: str | None = None,
    search: str | None = None,
    source: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Return compact, browser-ready datasets for dashboard charts and filters."""

    available_diets = sorted({row["Diet_type"] for row in rows})
    available_cuisines = sorted({row["Cuisine_type"] for row in rows})
    filtered = _apply_filters(rows, diet_types, cuisine, search)

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in filtered:
        grouped[row["Diet_type"]].append(row)

    averages = [
        {
            "diet_type": diet,
            "protein_g": _average(diet_rows, "Protein(g)"),
            "carbs_g": _average(diet_rows, "Carbs(g)"),
            "fat_g": _average(diet_rows, "Fat(g)"),
        }
        for diet, diet_rows in sorted(grouped.items())
    ]

    distribution = [
        {"diet_type": diet, "recipe_count": len(diet_rows)}
        for diet, diet_rows in sorted(grouped.items())
    ]

    scatter_points: list[dict[str, Any]] = []
    for diet, diet_rows in sorted(grouped.items()):
        for row in sorted(diet_rows, key=lambda item: item["Protein(g)"], reverse=True)[:30]:
            scatter_points.append(
                {
                    "diet_type": diet,
                    "recipe_name": row["Recipe_name"],
                    "cuisine_type": row["Cuisine_type"],
                    "protein_g": round(row["Protein(g)"], 2),
                    "carbs_g": round(row["Carbs(g)"], 2),
                    "fat_g": round(row["Fat(g)"], 2),
                }
            )

    cuisine_counts = Counter(row["Cuisine_type"] for row in filtered)
    top_cuisines = [
        {"cuisine_type": name, "recipe_count": count}
        for name, count in cuisine_counts.most_common(8)
    ]

    summary = {
        "recipe_count": len(filtered),
        "diet_type_count": len(grouped),
        "average_protein_g": _average(filtered, "Protein(g)"),
        "average_carbs_g": _average(filtered, "Carbs(g)"),
        "average_fat_g": _average(filtered, "Fat(g)"),
    }

    return {
        "summary": summary,
        "filters": {
            "available_diet_types": available_diets,
            "available_cuisines": available_cuisines,
            "applied": {
                "diet_types": diet_types or [],
                "cuisine": cuisine or "",
                "search": search or "",
            },
        },
        "charts": {
            "average_macros_by_diet": averages,
            "recipe_distribution_by_diet": distribution,
            "protein_vs_carbs": scatter_points,
            "top_cuisines": top_cuisines,
        },
        "metadata": {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "source": source or {"storage": "unknown"},
            "records_in_dataset": len(rows),
            "records_after_filtering": len(filtered),
        },
    }

