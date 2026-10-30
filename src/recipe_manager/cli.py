"""Command-line entry point for the recipe manager.

Supported commands: ``show``, ``scale``, ``substitute``, ``import``, ``cookbook``.

Not implemented yet: a ``search`` command to find recipes by ingredient or tag, and an
``export`` command to write a formatted report to a file.
"""

import argparse
import io
import sys
from pathlib import Path

from recipe_manager.calories import load_calorie_table
from recipe_manager.cookbook import build_cookbook
from recipe_manager.cookbook_render import render_html, render_markdown
from recipe_manager.models import Recipe
from recipe_manager.parsing import parse_recipe_text
from recipe_manager.report import format_recipe
from recipe_manager.storage import load_recipes
from recipe_manager.substitutions import suggest_substitutions

DEFAULT_CALORIES = Path("data/ingredient_calories.en.csv")
FORMATS = {".md": "md", ".markdown": "md", ".html": "html", ".htm": "html"}


def _find(recipes, title: str):
    for r in recipes:
        if r.title.lower() == title.lower():
            return r
    return None


def cmd_show(args: argparse.Namespace) -> int:
    recipes = load_recipes(Path(args.file))
    for recipe in recipes:
        print(format_recipe(recipe))
    return 0


def cmd_scale(args: argparse.Namespace) -> int:
    recipes = load_recipes(Path(args.file))
    recipe = _find(recipes, args.title)
    if recipe is None:
        print(f"No recipe named {args.title!r}")
        return 1
    print(format_recipe(recipe.scaled_to(args.servings)))
    return 0


def cmd_substitute(args: argparse.Namespace) -> int:
    subs = suggest_substitutions(args.ingredient)
    if not subs:
        print(f"No substitutions known for {args.ingredient!r}")
        return 1
    print(", ".join(subs))
    return 0


def cmd_import(args: argparse.Namespace) -> int:
    recipe = parse_recipe_text(Path(args.file).read_text(encoding="utf-8-sig"))
    print(format_recipe(recipe))
    return 0


def load_sources(paths: list[Path]) -> list[Recipe]:
    """Read ``.json`` collections and ``.txt`` recipes; reject duplicate titles."""
    recipes: list[Recipe] = []
    origin: dict[str, Path] = {}
    for path in paths:
        suffix = path.suffix.lower()
        if suffix == ".json":
            loaded = load_recipes(path)
        elif suffix == ".txt":
            loaded = [parse_recipe_text(path.read_text(encoding="utf-8-sig"))]
        else:
            raise ValueError(f"{path}: unsupported file type (use .json or .txt)")
        for recipe in loaded:
            key = recipe.title.casefold()
            if key in origin:
                raise ValueError(
                    f"recipe {recipe.title!r} appears in both {origin[key]} and {path}"
                )
            origin[key] = path
        recipes += loaded
    return recipes


def _output_format(args: argparse.Namespace) -> str:
    if args.format:
        return args.format
    if args.output is None:
        return "md"
    suffix = Path(args.output).suffix.lower()
    if suffix not in FORMATS:
        raise ValueError(f"cannot tell the format from {args.output!r}; use --format")
    return FORMATS[suffix]


def cmd_cookbook(args: argparse.Namespace) -> int:
    try:
        fmt = _output_format(args)
        recipes = load_sources([Path(f) for f in args.sources])
        table = None
        if args.calories:
            table = load_calorie_table(Path(args.calories))
        elif DEFAULT_CALORIES.exists():
            table = load_calorie_table(DEFAULT_CALORIES)
        else:
            print(f"note: {DEFAULT_CALORIES} not found, no calories shown", file=sys.stderr)
        book = build_cookbook(recipes, args.title, table)
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    text = render_html(book) if fmt == "html" else render_markdown(book)
    if args.output is None:
        # The cookbook contains characters like "≈" that legacy consoles can't encode.
        if isinstance(sys.stdout, io.TextIOWrapper):
            sys.stdout.reconfigure(encoding="utf-8")
        sys.stdout.write(text)
    else:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"Wrote {args.output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="recipes")
    sub = parser.add_subparsers(dest="command", required=True)

    p_show = sub.add_parser("show", help="print all recipes in a JSON file")
    p_show.add_argument("file")
    p_show.set_defaults(func=cmd_show)

    p_scale = sub.add_parser("scale", help="scale a recipe to a serving count")
    p_scale.add_argument("file")
    p_scale.add_argument("title")
    p_scale.add_argument("servings", type=int)
    p_scale.set_defaults(func=cmd_scale)

    p_sub = sub.add_parser("substitute", help="suggest ingredient substitutions")
    p_sub.add_argument("ingredient")
    p_sub.set_defaults(func=cmd_substitute)

    p_imp = sub.add_parser("import", help="import a recipe from a text file")
    p_imp.add_argument("file")
    p_imp.set_defaults(func=cmd_import)

    p_book = sub.add_parser(
        "cookbook", help="write a Markdown or HTML cookbook from recipe files"
    )
    p_book.add_argument("sources", nargs="+", help=".json collections and .txt recipes")
    p_book.add_argument(
        "-o", "--output", help="output file (.md or .html); default: Markdown to stdout"
    )
    p_book.add_argument(
        "--format", choices=["md", "html"], help="override the format from -o"
    )
    p_book.add_argument("--title", default="Cookbook", help="cookbook title")
    p_book.add_argument(
        "--calories",
        help=f"kcal-per-100-g CSV (default: {DEFAULT_CALORIES.as_posix()} if present)",
    )
    p_book.set_defaults(func=cmd_cookbook)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
