import pytest

from recipe_manager.formatting import format_amount, format_ingredient
from recipe_manager.models import Ingredient, Recipe
from recipe_manager.report import format_recipe


@pytest.mark.parametrize(
    ("amount", "expected"),
    [
        (None, ""),
        (200, "200"),
        (200.0, "200"),
        (7.5, "7.5"),
        (333.3333, "333"),
        (12.345, "12.3"),
        (0.3333, "0.33"),
        (0, "0"),
    ],
)
def test_format_amount_as_decimal(amount: float | None, expected: str) -> None:
    assert format_amount(amount) == expected


@pytest.mark.parametrize(
    ("amount", "expected"),
    [
        (0.5, "1/2"),
        (1.5, "1 1/2"),
        (2 / 3, "2/3"),
        (0.25, "1/4"),
        (3.0, "3"),
        (2.999, "3"),
        (0.4, "0.4"),
    ],
)
def test_format_amount_as_fraction(amount: float, expected: str) -> None:
    assert format_amount(amount, fractions=True) == expected


@pytest.mark.parametrize(
    ("ingredient", "expected"),
    [
        (Ingredient("flour", 200, "g"), "200 g flour"),
        (Ingredient("sugar", 7.5, "g"), "7.5 g sugar"),
        (Ingredient("eggs", 0.5), "1/2 eggs"),
        (Ingredient("eggs", 1.5), "1 1/2 eggs"),
        (Ingredient("milk", 1.5, "cups"), "1 1/2 cups milk"),
        (Ingredient("salt to taste", None), "salt to taste"),
    ],
)
def test_format_ingredient(ingredient: Ingredient, expected: str) -> None:
    assert format_ingredient(ingredient) == expected


def test_format_recipe_layout() -> None:
    recipe = Recipe(
        "Pancakes",
        4,
        [Ingredient("flour", 200, "g"), Ingredient("eggs", 2)],
        tags=["breakfast"],
        instructions=["Mix.", "Fry."],
    )
    assert format_recipe(recipe) == (
        "========================================\n"
        "Pancakes (serves 4)\n"
        "========================================\n"
        "tags: breakfast\n"
        "\n"
        "Ingredients:\n"
        "  - 200 g flour\n"
        "  - 2 eggs\n"
        "\n"
        "Instructions:\n"
        "  1. Mix.\n"
        "  2. Fry.\n"
    )


def test_scaled_report_keeps_fractional_pieces() -> None:
    recipe = Recipe("Pancakes", 4, [Ingredient("eggs", 2)])
    assert "  - 1/2 eggs\n" in format_recipe(recipe.scaled_to(1))
