"""Estimate calories per serving from a kcal-per-100-g table.

The estimate is approximate: volumes are converted as if they were water
(1 ml = 1 g), and counted items use typical weights. Ingredients that cannot be
converted or are missing from the table are reported, not guessed.
"""

import csv
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from recipe_manager.models import Ingredient, Recipe

# Grams per unit. Volumes assume the density of water.
GRAMS_PER_UNIT = {
    "g": 1.0,
    "kg": 1000.0,
    "mg": 0.001,
    "ml": 1.0,
    "cl": 10.0,
    "dl": 100.0,
    "l": 1000.0,
    "tsp": 5.0,
    "tbsp": 15.0,
    "cup": 240.0,
    "oz": 28.35,
    "lb": 453.6,
    "pinch": 0.5,
    "clove": 5.0,
    "slice": 30.0,
}

# Typical weight in grams of one counted item (amount without a unit).
GRAMS_PER_PIECE = {
    "egg": 50.0,
    "onion": 110.0,
    "tomato": 120.0,
    "potato": 170.0,
    "carrot": 60.0,
    "banana": 120.0,
    "apple": 180.0,
    "lemon": 100.0,
}


@dataclass
class CalorieEstimate:
    kcal: int
    not_counted: list[str] = field(default_factory=list)


def load_calorie_table(path: Path) -> dict[str, float]:
    """Read a two-column CSV (ingredient, kcal per 100 g) into a lowercase dict."""
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = csv.reader(f)
        next(rows, None)  # header
        return {name.strip().lower(): float(kcal) for name, kcal in rows}


def _variants(word: str) -> list[str]:
    """``word`` plus its likely singular and plural forms."""
    word = word.strip().lower()
    forms = [word, word + "s", word + "es"]
    if word.endswith("es"):
        forms.append(word[:-2])
    if word.endswith("s"):
        forms.append(word[:-1])
    return forms


def _lookup(table: Mapping[str, float], word: str) -> float | None:
    for form in _variants(word):
        if form in table:
            return table[form]
    return None


def grams(ingredient: Ingredient) -> float | None:
    """Weight of ``ingredient`` in grams, or ``None`` if it cannot be converted."""
    if ingredient.amount is None:
        return None
    if ingredient.unit:
        per_unit = _lookup(GRAMS_PER_UNIT, ingredient.unit)
    else:
        per_unit = _lookup(GRAMS_PER_PIECE, ingredient.name)
    return None if per_unit is None else ingredient.amount * per_unit


def estimate_per_serving(recipe: Recipe, table: Mapping[str, float]) -> CalorieEstimate:
    """Sum the calories of all convertible ingredients and divide by servings."""
    total = 0.0
    not_counted = []
    for ingredient in recipe.ingredients:
        weight = grams(ingredient)
        kcal_per_100g = _lookup(table, ingredient.name)
        if weight is None or kcal_per_100g is None:
            not_counted.append(ingredient.name)
        else:
            total += weight * kcal_per_100g / 100
    return CalorieEstimate(round(total / recipe.servings), not_counted)
