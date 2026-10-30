"""Render a :class:`~recipe_manager.cookbook.Cookbook` as Markdown or HTML."""

import re
from html import escape

from recipe_manager.calories import CalorieEstimate
from recipe_manager.cookbook import Cookbook, Entry
from recipe_manager.formatting import format_ingredient


def calorie_line(estimate: CalorieEstimate | None, ingredient_count: int) -> str | None:
    """``"≈ 281 kcal per serving (approx.)"``, with uncounted ingredients listed."""
    if estimate is None:
        return None
    if len(estimate.not_counted) == ingredient_count:
        return "Calories: not available"
    line = f"≈ {estimate.kcal} kcal per serving (approx."
    if estimate.not_counted:
        line += "; not counted: " + ", ".join(estimate.not_counted)
    return line + ")"


def _details(entry: Entry) -> str:
    details = f"Serves {entry.recipe.servings}"
    if entry.other_tags:
        details += " · also: " + ", ".join(entry.other_tags)
    return details


# --- Markdown ---------------------------------------------------------------


def _md(text: str) -> str:
    """Escape characters that Markdown would treat as formatting."""
    return re.sub(r"([\\`*_\[\]<>#|])", r"\\\1", text)


def render_markdown(book: Cookbook) -> str:
    lines = [f"# {_md(book.title)}", "", "## Contents", ""]
    for chapter in book.chapters:
        lines.append(f"- [{_md(chapter.name)}](#{chapter.anchor})")
        lines += [
            f"  - [{_md(e.recipe.title)}](#{e.anchor})" for e in chapter.entries
        ]
    for chapter in book.chapters:
        lines += ["", f'<a id="{chapter.anchor}"></a>', "", f"## {_md(chapter.name)}"]
        for entry in chapter.entries:
            lines += _markdown_entry(entry)
    return "\n".join(lines) + "\n"


def _markdown_entry(entry: Entry) -> list[str]:
    recipe = entry.recipe
    lines = ["", f'<a id="{entry.anchor}"></a>', "", f"### {_md(recipe.title)}", ""]
    lines.append(f"*{_md(_details(entry))}*")
    calories = calorie_line(entry.calories, len(recipe.ingredients))
    if calories:
        lines += ["", _md(calories)]
    lines += ["", "**Ingredients**", ""]
    lines += [f"- {_md(format_ingredient(i))}" for i in recipe.ingredients]
    if recipe.instructions:
        lines += ["", "**Instructions**", ""]
        lines += [f"{n}. {_md(step)}" for n, step in enumerate(recipe.instructions, 1)]
    return lines


# --- HTML -------------------------------------------------------------------

STYLE = """
:root { --text: #222; --muted: #666; --accent: #a4462b; --rule: #ddd; --bg: #fff; }
@media (prefers-color-scheme: dark) {
  :root { --text: #eee; --muted: #aaa; --accent: #f08a62; --rule: #444; --bg: #1b1b1b; }
}
body { font-family: Georgia, "Times New Roman", serif; color: var(--text);
       background: var(--bg); max-width: 42rem; margin: 2rem auto; padding: 0 1rem;
       line-height: 1.5; }
h1 { text-align: center; font-size: 2.4rem; margin-bottom: 2rem; }
h2 { color: var(--accent); border-bottom: 2px solid var(--accent); padding-bottom: .2rem; }
h3 { margin-bottom: .2rem; }
a { color: var(--accent); }
nav ul { list-style: none; padding-left: 0; }
nav ul ul { padding-left: 1.5rem; }
.details, .calories { color: var(--muted); margin: 0 0 .5rem; }
.recipe { border-bottom: 1px solid var(--rule); padding-bottom: 1rem; }
.recipe:last-child { border-bottom: none; }
@media print {
  :root { --text: #000; --muted: #444; --accent: #000; --bg: #fff; }
  body { margin: 0; max-width: none; }
  nav a { text-decoration: none; }
  .chapter { break-before: page; }
  .recipe { break-inside: avoid; }
}
"""


def render_html(book: Cookbook) -> str:
    title = escape(book.title)
    parts = [
        "<!doctype html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{title}</title>",
        f"<style>{STYLE}</style>",
        "</head>",
        "<body>",
        f"<h1>{title}</h1>",
        '<nav><h2>Contents</h2><ul>',
    ]
    for chapter in book.chapters:
        parts.append(f'<li><a href="#{chapter.anchor}">{escape(chapter.name)}</a><ul>')
        parts += [
            f'<li><a href="#{e.anchor}">{escape(e.recipe.title)}</a></li>'
            for e in chapter.entries
        ]
        parts.append("</ul></li>")
    parts.append("</ul></nav>")
    for chapter in book.chapters:
        parts.append(f'<section class="chapter" id="{chapter.anchor}">')
        parts.append(f"<h2>{escape(chapter.name)}</h2>")
        for entry in chapter.entries:
            parts += _html_entry(entry)
        parts.append("</section>")
    parts += ["</body>", "</html>"]
    return "\n".join(parts) + "\n"


def _html_entry(entry: Entry) -> list[str]:
    recipe = entry.recipe
    parts = [
        f'<article class="recipe" id="{entry.anchor}">',
        f"<h3>{escape(recipe.title)}</h3>",
        f'<p class="details">{escape(_details(entry))}</p>',
    ]
    calories = calorie_line(entry.calories, len(recipe.ingredients))
    if calories:
        parts.append(f'<p class="calories">{escape(calories)}</p>')
    parts.append("<h4>Ingredients</h4><ul>")
    parts += [f"<li>{escape(format_ingredient(i))}</li>" for i in recipe.ingredients]
    parts.append("</ul>")
    if recipe.instructions:
        parts.append("<h4>Instructions</h4><ol>")
        parts += [f"<li>{escape(step)}</li>" for step in recipe.instructions]
        parts.append("</ol>")
    parts.append("</article>")
    return parts
