from recipe_manager.catalog import recipes_with_tag
from recipe_manager.exports import export_rows
from recipe_manager.meal_plans import PlannedMeal, plan_titles
from recipe_manager.models import Ingredient, Recipe
from recipe_manager.pantry import can_cook, missing_ingredients


def _recipe() -> Recipe:
    return Recipe(
        "Soup",
        2,
        [Ingredient("tomato", 3), Ingredient("salt", 1)],
        tags=["Dinner", "vegetarian"],
    )


def test_recipes_with_tag_is_case_insensitive():
    recipe = _recipe()
    assert recipes_with_tag([recipe], "dinner") == [recipe]


def test_plan_titles_preserves_plan_order():
    recipe = _recipe()
    meals = [PlannedMeal("Monday", recipe), PlannedMeal("Friday", recipe)]
    assert plan_titles(meals) == ["Monday: Soup", "Friday: Soup"]


def test_export_rows_are_json_ready_and_ordered():
    recipe = _recipe()
    assert export_rows([recipe]) == [{"title": "Soup", "servings": 2}]


def test_pantry_reports_an_absent_ingredient():
    recipe = _recipe()
    pantry = {"tomato": 10}
    assert missing_ingredients(recipe, pantry) == ["salt"]
    assert not can_cook(recipe, pantry)


def test_unquantified_ingredient_does_not_block_cooking():
    recipe = Recipe("Tea", 1, [Ingredient("water as needed", None)])
    assert missing_ingredients(recipe, {}) == []
    assert can_cook(recipe, {})
