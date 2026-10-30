import pytest

from recipe_manager.cookbook import build_cookbook, slugify
from recipe_manager.models import Ingredient, Recipe


def _recipe(title: str, *tags: str) -> Recipe:
    return Recipe(title, 2, [Ingredient("flour", 100, "g")], tags=list(tags))


def _layout(recipes: list[Recipe]) -> list[tuple[str, list[str]]]:
    book = build_cookbook(recipes)
    return [(c.name, [e.recipe.title for e in c.entries]) for c in book.chapters]


def test_recipes_are_grouped_by_first_tag_and_sorted() -> None:
    recipes = [
        _recipe("Waffles", "breakfast", "sweet"),
        _recipe("Tomato Soup", "lunch", "vegetarian"),
        _recipe("Pancakes", "breakfast"),
        _recipe("Brownies", "sweet"),
    ]
    assert _layout(recipes) == [
        ("Breakfast", ["Pancakes", "Waffles"]),
        ("Lunch", ["Tomato Soup"]),
        ("Sweet", ["Brownies"]),
    ]


def test_untagged_recipes_go_to_a_final_other_chapter() -> None:
    recipes = [_recipe("Toast"), _recipe("Soup", "dinner"), _recipe("Tea", " ")]
    assert _layout(recipes) == [("Dinner", ["Soup"]), ("Other", ["Tea", "Toast"])]


def test_chapter_tags_are_merged_case_insensitively() -> None:
    recipes = [_recipe("A", "Lunch"), _recipe("B", "lunch")]
    assert _layout(recipes) == [("Lunch", ["A", "B"])]


def test_other_tags_are_kept_on_the_entry() -> None:
    book = build_cookbook([_recipe("Waffles", "breakfast", "sweet")])
    assert book.chapters[0].entries[0].other_tags == ["sweet"]


def test_duplicate_titles_are_rejected() -> None:
    with pytest.raises(ValueError, match="duplicate recipe title: 'pancakes'"):
        build_cookbook([_recipe("Pancakes"), _recipe("pancakes")])


@pytest.mark.parametrize(
    ("text", "expected"),
    [("Tomato Soup", "tomato-soup"), ("Crème brûlée!", "cr-me-br-l-e"), ("???", "section")],
)
def test_slugify(text: str, expected: str) -> None:
    assert slugify(text) == expected


def test_anchors_are_unique_across_chapters_and_recipes() -> None:
    book = build_cookbook([_recipe("Lunch", "lunch")])
    chapter = book.chapters[0]
    assert (chapter.anchor, chapter.entries[0].anchor) == ("lunch", "lunch-2")


def test_calories_are_estimated_only_with_a_table() -> None:
    recipes = [_recipe("Bread", "baking")]
    assert build_cookbook(recipes).chapters[0].entries[0].calories is None
    entry = build_cookbook(recipes, calorie_table={"flour": 364}).chapters[0].entries[0]
    assert entry.calories is not None
    assert entry.calories.kcal == 182
