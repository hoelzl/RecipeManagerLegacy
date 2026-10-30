from recipe_manager.analytics import ingredient_count, recipe_titles
from recipe_manager.models import Ingredient, Recipe
from recipe_manager.shopping import unique_ingredient_names


def _recipes() -> list[Recipe]:
    return [
        Recipe("Toast", 1, [Ingredient("Bread", 2), Ingredient("Salt", 1)]),
        Recipe("Soup", 2, [Ingredient("salt", 1), Ingredient("Tomato", 3)]),
    ]


def test_unique_ingredient_names_normalizes_and_sorts():
    assert unique_ingredient_names(_recipes()) == ["bread", "salt", "tomato"]


def test_small_analytics_helpers():
    recipes = _recipes()
    assert ingredient_count(recipes[0]) == 2
    assert recipe_titles(recipes) == ["Toast", "Soup"]
