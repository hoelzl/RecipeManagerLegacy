from recipe_manager.models import Ingredient, Recipe


def _pancakes() -> Recipe:
    return Recipe(
        title="Pancakes",
        servings=4,
        ingredients=[
            Ingredient("flour", 200, "g"),
            Ingredient("milk", 300, "ml"),
        ],
    )


def test_scaling_up_doubles_amounts():
    scaled = _pancakes().scaled_to(8)
    assert scaled.servings == 8
    assert scaled.ingredients[0].amount == 400
    assert scaled.ingredients[1].amount == 600


def test_scaling_down_halves_amounts():
    scaled = _pancakes().scaled_to(2)
    assert scaled.ingredients[0].amount == 100


# NOTE: parsing.py, storage.py and report.py have no tests yet; the feature modules
# have only narrow happy-path coverage.
