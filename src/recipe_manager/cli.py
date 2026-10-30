"""Command-line entry point for the recipe manager.

Supported commands: ``show``, ``scale``, ``substitute``, ``import``.

Not implemented yet: a ``search`` command to find recipes by ingredient or tag, and an
``export`` command to write a formatted report to a file.
"""

import argparse
from pathlib import Path

from recipe_manager.parsing import parse_recipe_text
from recipe_manager.report import format_recipe
from recipe_manager.storage import load_recipes
from recipe_manager.substitutions import suggest_substitutions


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

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
