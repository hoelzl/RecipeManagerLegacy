import json
from pathlib import Path

import pytest

from recipe_manager.models import Ingredient, Recipe
from recipe_manager.storage import load_recipes, save_recipes

DATA = Path(__file__).resolve().parents[1] / "data"


def test_round_trip_keeps_every_field(tmp_path: Path) -> None:
    recipe = Recipe(
        "Tea",
        1,
        [Ingredient("water", 250, "ml"), Ingredient("sugar", None)],
        tags=["drink"],
        instructions=["Boil the water.", "Steep."],
    )
    path = tmp_path / "recipes.json"
    save_recipes([recipe], path)
    assert load_recipes(path) == [recipe]


def test_sample_data_keeps_tags_and_instructions() -> None:
    pancakes = load_recipes(DATA / "recipes.json")[0]
    assert pancakes.tags == ["breakfast", "sweet"]
    assert pancakes.instructions[0] == "Mix the dry ingredients."


def test_optional_fields_default_to_empty(tmp_path: Path) -> None:
    path = tmp_path / "recipes.json"
    path.write_text(
        json.dumps([{"title": "Toast", "servings": 1, "ingredients": [{"name": "bread"}]}]),
        encoding="utf-8",
    )
    [toast] = load_recipes(path)
    assert toast.tags == [] and toast.instructions == []
    assert toast.ingredients == [Ingredient("bread", None, "")]


def test_byte_order_mark_is_accepted(tmp_path: Path) -> None:
    path = tmp_path / "recipes.json"
    path.write_text(
        json.dumps([{"title": "Toast", "servings": 1, "ingredients": []}]),
        encoding="utf-8-sig",
    )
    assert load_recipes(path)[0].title == "Toast"


def test_missing_field_names_file_and_recipe() -> None:
    with pytest.raises(ValueError, match=r"recipe #2 \('Omelette'\): missing servings"):
        load_recipes(DATA / "broken_recipes.json")


def test_top_level_must_be_a_list(tmp_path: Path) -> None:
    path = tmp_path / "recipes.json"
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="expected a list"):
        load_recipes(path)
