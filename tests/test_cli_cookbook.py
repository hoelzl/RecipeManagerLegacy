import json
from pathlib import Path

import pytest

from recipe_manager.cli import main

DATA = Path(__file__).resolve().parents[1] / "data"
CALORIES = DATA / "ingredient_calories.en.csv"


def _run(*args: str | Path) -> int:
    return main(["cookbook", *map(str, args)])


def test_html_from_json_and_text_sources(tmp_path: Path) -> None:
    out = tmp_path / "book.html"
    code = _run(
        DATA / "recipes.json", DATA / "waffles.txt", "-o", out, "--calories", CALORIES
    )
    assert code == 0
    page = out.read_text(encoding="utf-8")
    assert page.startswith("<!doctype html>")
    for title in ("Pancakes", "Tomato Soup", "Waffles"):
        assert f"<h3>{title}</h3>" in page
    assert "kcal per serving" in page


def test_markdown_to_stdout_by_default(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert _run(DATA / "recipes.json", "--title", "Family", "--calories", CALORIES) == 0
    text = capsys.readouterr().out
    assert text.startswith("# Family\n")
    assert "## Breakfast" in text


def test_format_option_overrides_the_extension(tmp_path: Path) -> None:
    out = tmp_path / "book.txt"
    assert _run(DATA / "recipes.json", "-o", out, "--format", "html") == 0
    assert out.read_text(encoding="utf-8").startswith("<!doctype html>")


def test_unknown_output_extension_is_an_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert _run(DATA / "recipes.json", "-o", tmp_path / "book.pdf") == 1
    assert "use --format" in capsys.readouterr().err


def test_unsupported_source_type_is_an_error(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert _run(CALORIES) == 1
    assert "unsupported file type" in capsys.readouterr().err


def test_duplicate_title_names_both_files(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    other = tmp_path / "more.json"
    other.write_text(
        json.dumps([{"title": "pancakes", "servings": 1, "ingredients": []}]),
        encoding="utf-8",
    )
    assert _run(DATA / "recipes.json", other) == 1
    err = capsys.readouterr().err
    assert "recipes.json" in err
    assert "more.json" in err


def test_broken_json_is_reported(capsys: pytest.CaptureFixture[str]) -> None:
    assert _run(DATA / "broken_recipes.json") == 1
    assert "missing servings" in capsys.readouterr().err


def test_sample_pancakes_text_imports(tmp_path: Path) -> None:
    out = tmp_path / "book.md"
    assert _run(DATA / "pancakes.txt", "-o", out, "--calories", CALORIES) == 0
    text = out.read_text(encoding="utf-8")
    assert "- 1/2 cup sugar" in text
    assert "not counted: salt to taste" in text
