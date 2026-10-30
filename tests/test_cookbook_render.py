import re

import pytest

from recipe_manager.calories import CalorieEstimate
from recipe_manager.cookbook import Cookbook, build_cookbook
from recipe_manager.cookbook_render import calorie_line, render_html, render_markdown
from recipe_manager.models import Ingredient, Recipe


def _book() -> Cookbook:
    recipes = [
        Recipe(
            "Pancakes",
            4,
            [Ingredient("flour", 200, "g"), Ingredient("eggs", 2)],
            tags=["breakfast", "sweet"],
            instructions=["Mix.", "Fry."],
        ),
        Recipe("Fish & <Chips>", 2, [Ingredient("salt to taste", None)]),
    ]
    return build_cookbook(recipes, "My *Book*", {"flour": 364, "eggs": 155})


@pytest.mark.parametrize(
    ("estimate", "count", "expected"),
    [
        (None, 2, None),
        (CalorieEstimate(281), 4, "≈ 281 kcal per serving (approx.)"),
        (
            CalorieEstimate(44, ["salt"]),
            2,
            "≈ 44 kcal per serving (approx.; not counted: salt)",
        ),
        (CalorieEstimate(0, ["salt"]), 1, "Calories: not available"),
    ],
)
def test_calorie_line(
    estimate: CalorieEstimate | None, count: int, expected: str | None
) -> None:
    assert calorie_line(estimate, count) == expected


def test_markdown_contains_toc_chapters_and_recipe() -> None:
    text = render_markdown(_book())
    assert text.startswith("# My \\*Book\\*\n")
    assert "- [Breakfast](#breakfast)\n  - [Pancakes](#pancakes)\n" in text
    assert "## Other" in text
    assert "*Serves 4 · also: sweet*" in text
    assert "≈ 221 kcal per serving (approx.)" in text  # (728 + 155) / 4
    assert "- 200 g flour\n- 2 eggs\n" in text
    assert "1. Mix.\n2. Fry.\n" in text
    assert "### Fish & \\<Chips\\>" in text


def test_every_markdown_link_has_an_anchor() -> None:
    text = render_markdown(_book())
    links = set(re.findall(r"\]\(#([^)]+)\)", text))
    anchors = set(re.findall(r'<a id="([^"]+)"></a>', text))
    assert links
    assert links <= anchors


def test_html_is_a_self_contained_escaped_page() -> None:
    page = render_html(_book())
    assert page.startswith("<!doctype html>")
    assert '<meta charset="utf-8">' in page
    assert "<title>My *Book*</title>" in page
    assert "Fish &amp; &lt;Chips&gt;" in page
    assert "<Chips>" not in page
    assert "break-before: page" in page
    assert not re.search(r'(src|href)="(https?:)?//', page)


def test_every_html_link_has_a_target() -> None:
    page = render_html(_book())
    links = set(re.findall(r'href="#([^"]+)"', page))
    ids = set(re.findall(r'id="([^"]+)"', page))
    assert links
    assert links <= ids
