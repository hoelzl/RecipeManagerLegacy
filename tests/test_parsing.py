from pathlib import Path

import pytest

from recipe_manager.models import Ingredient, Recipe
from recipe_manager.parsing import parse_amount, parse_ingredient, parse_recipe_text

DATA = Path(__file__).resolve().parents[1] / "data"


@pytest.mark.parametrize(
    ("text", "expected"),
    [("2", 2.0), ("0.5", 0.5), ("1/2", 0.5), ("1 1/2", 1.5), ("3/4", 0.75)],
)
def test_parse_amount(text: str, expected: float) -> None:
    assert parse_amount(text) == expected


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("200 g flour", Ingredient("flour", 200, "g")),
        ("1/2 cup sugar", Ingredient("sugar", 0.5, "cup")),
        ("1 1/2 cups milk", Ingredient("milk", 1.5, "cups")),
        ("3 eggs", Ingredient("eggs", 3, "")),
        ("2 big onions", Ingredient("big onions", 2, "")),
        ("salt to taste", Ingredient("salt to taste", None, "")),
        ("2 tbsp olive oil", Ingredient("olive oil", 2, "tbsp")),
    ],
)
def test_parse_ingredient(line: str, expected: Ingredient) -> None:
    assert parse_ingredient(line) == expected


def test_empty_ingredient_line_is_rejected() -> None:
    with pytest.raises(ValueError, match="empty"):
        parse_ingredient("   ")


def test_sample_pancakes_file_parses() -> None:
    recipe = parse_recipe_text((DATA / "pancakes.txt").read_text(encoding="utf-8"))
    assert recipe.title == "Pancakes"
    assert recipe.servings == 4
    assert recipe.tags == ["breakfast", "sweet"]
    assert recipe.ingredients[1] == Ingredient("sugar", 0.5, "cup")
    assert recipe.ingredients[3] == Ingredient("salt to taste", None, "")
    assert len(recipe.instructions) == 3


def test_byte_order_mark_does_not_hide_the_title() -> None:
    # data/waffles.txt starts with a byte-order mark.
    recipe = parse_recipe_text((DATA / "waffles.txt").read_text(encoding="utf-8"))
    assert recipe.title == "Waffles"


def test_scaling_keeps_unquantified_ingredients() -> None:
    recipe = Recipe("Soup", 2, [Ingredient("salt to taste", None), Ingredient("water", 1, "l")])
    scaled = recipe.scaled_to(4)
    assert scaled.ingredients == [Ingredient("salt to taste", None), Ingredient("water", 2, "l")]
