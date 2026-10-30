from pathlib import Path

import pytest

from recipe_manager.calories import (
    CalorieEstimate,
    estimate_per_serving,
    grams,
    load_calorie_table,
)
from recipe_manager.models import Ingredient, Recipe

DATA = Path(__file__).resolve().parents[1] / "data"
TABLE = {"flour": 364, "milk": 42, "eggs": 155, "sugar": 387, "onion": 40}


def test_load_sample_table() -> None:
    table = load_calorie_table(DATA / "ingredient_calories.en.csv")
    assert table["flour"] == 364
    assert table["coconut oil"] == 862


@pytest.mark.parametrize(
    ("ingredient", "expected"),
    [
        (Ingredient("flour", 200, "g"), 200),
        (Ingredient("milk", 0.5, "l"), 500),
        (Ingredient("sugar", 2, "tbsp"), 30),
        (Ingredient("milk", 1, "cups"), 240),
        (Ingredient("eggs", 2), 100),
        (Ingredient("onion", 1), 110),
        (Ingredient("baguette", 1), None),
        (Ingredient("salt to taste", None), None),
        (Ingredient("flour", 1, "handful"), None),
    ],
)
def test_grams(ingredient: Ingredient, expected: float | None) -> None:
    assert grams(ingredient) == expected


def test_pancakes_per_serving() -> None:
    recipe = Recipe(
        "Pancakes",
        4,
        [
            Ingredient("flour", 200, "g"),  # 728 kcal
            Ingredient("milk", 300, "ml"),  # 126 kcal
            Ingredient("eggs", 2),  # 155 kcal
            Ingredient("sugar", 30, "g"),  # 116.1 kcal
        ],
    )
    assert estimate_per_serving(recipe, TABLE) == CalorieEstimate(281, [])


def test_unknown_and_unquantified_ingredients_are_listed() -> None:
    recipe = Recipe(
        "Soup",
        1,
        [
            Ingredient("onion", 1),
            Ingredient("dragonfruit", 100, "g"),
            Ingredient("salt to taste", None),
        ],
    )
    assert estimate_per_serving(recipe, TABLE) == CalorieEstimate(
        44, ["dragonfruit", "salt to taste"]
    )


def test_singular_name_matches_plural_table_entry() -> None:
    recipe = Recipe("Egg", 1, [Ingredient("egg", 1)])
    assert estimate_per_serving(recipe, TABLE).kcal == 78
