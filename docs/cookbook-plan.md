# Plan: Cookbook export

Goal: a new command that turns the recipes in the manager into a cookbook, as
Markdown or as a self-contained HTML page.

```bash
uv run recipes cookbook data/recipes.json data/waffles.txt -o cookbook.html
uv run recipes cookbook data/recipes.json -o cookbook.md --title "Family Recipes"
uv run recipes cookbook data/recipes.json            # Markdown to stdout
```

## Decisions (from the interview)

| Topic | Decision |
|---|---|
| Formats | Markdown and HTML |
| Integration | New CLI command `cookbook` + new modules, with tests |
| Structure | Chapters by tag; each recipe appears once, under its **first** tag; untagged recipes go to an "Other" chapter |
| Sources | Any mix of `.json` collections and `.txt` recipes |
| Extras | Table of contents; estimated calories per serving |
| Calories | Built-in unit→gram table + per-piece weights; unconvertible ingredients listed as "not counted"; totals marked "approx." |
| Language | English (headings, `ingredient_calories.en.csv`) |
| HTML | One file, inline CSS, print-friendly (chapter = new printed page), no external assets |
| CLI | Format from `-o` extension (`.md`/`.html`), `--format` overrides, no `-o` → Markdown on stdout, optional `--title` |
| Bug fixes | Fix what the cookbook touches (loader, text import, amount formatting); leave pantry and scale validation for later |

## Defaults I chose (say if you want them different)

- Chapter order: alphabetical by tag, "Other" last. Recipes inside a chapter: alphabetical by title.
- Default title: "Cookbook". The remaining tags of a recipe are shown under its heading.
- Two recipes with the same title (case-insensitive) from different sources: error with both file names, rather than silently picking one.
- Calories are shown **per serving**, rounded to whole kcal, e.g. `≈ 410 kcal per serving (not counted: salt)`.
- Ingredient names are matched case-insensitively against the CSV, also trying the singular/plural form (`egg` ↔ `eggs`).

## Steps

Each step ends with `uv run tools/check.py` green and its own commit.

### 1. Loader keeps all fields — `storage.py`
- `load_recipes` also reads `tags` and `instructions` (default: empty lists if absent).
- Read with `encoding="utf-8-sig"` so a BOM does not break anything.
- Missing required keys (`title`, `servings`, `ingredients`) raise a `ValueError` naming the file and the recipe position, instead of a raw `KeyError`.
- Tests: round trip `save_recipes` → `load_recipes` keeps everything; `data/broken_recipes.json` gives a readable error.

### 2. Text import handles the documented format — `parsing.py`, `models.py`, `cli.py`
- Amounts: integers, decimals, fractions (`1/2`), mixed numbers (`1 1/2`).
- Lines without a leading amount (`salt to taste`) become an ingredient with `amount=None` (the pantry module already expects `None`). `Ingredient.amount` becomes `float | None`; `scaled_to` leaves `None` unchanged.
- `cmd_import` reads with `utf-8-sig` (fixes the empty Waffles title).
- Tests: every line from `data/pancakes.txt`, BOM input, `scaled_to` with `None` amounts.

### 3. Correct amount formatting — new `formatting.py`, refactor `report.py`
- `format_amount(x)`: drop `.0`, round to at most 2 decimals, show common fractions where natural (`0.5` → `1/2`); `None` → empty string.
- `format_ingredient(ing)`: `"200 g flour"`, `"1 1/2 eggs"`, `"salt to taste"`. No naive pluralisation: names are kept as written (data already says `eggs`).
- `report.format_recipe` uses these helpers (fixes `0 eggss`); existing output otherwise unchanged.
- Tests: table-driven cases for amounts and ingredients, including scaled fractions.

### 4. Calorie estimation — new `calories.py`
- `load_calorie_table(path) -> dict[str, float]` from `ingredient_calories.en.csv` (kcal per 100 g).
- Unit table: `g` 1, `kg` 1000, `ml` 1, `l` 1000, `tsp` 5, `tbsp` 15, `cup` 240 (grams, assuming water density).
- Piece weights for counted items: egg 50 g, onion 110 g, banana 120 g, apple 180 g, lemon 100 g, garlic (clove) 5 g; easy to extend.
- `estimate_per_serving(recipe, table) -> CalorieEstimate(kcal: int, not_counted: list[str])`. Ingredients without amount, unknown unit, or missing in the CSV go to `not_counted`.
- The default CSV path is located relative to the package's data folder, overridable with `--calories PATH`.
- Tests: Pancakes by hand (flour 200 g, milk 300 ml, 2 eggs, sugar 30 g → per serving), unknown ingredient, `None` amount.

### 5. Cookbook model — new `cookbook.py`
- `build_cookbook(recipes, title) -> Cookbook` with `chapters: list[Chapter(name, recipes)]`, applying the grouping and ordering rules above.
- `slugify(text)` for stable, unique anchors (`tomato-soup`, a `-2` suffix on collision).
- Pure data, no formatting — so both renderers share it and it is easy to test.
- Tests: grouping by first tag, "Other" chapter, ordering, duplicate-title error, slug collisions.

### 6. Renderers — `cookbook_markdown.py`, `cookbook_html.py` (or one module with two functions)
- Both render: title, table of contents (chapters → recipes, linked by anchor), per recipe: heading, serves N, other tags, calories line, ingredients list, numbered instructions.
- HTML: `<!doctype html>`, `<meta charset="utf-8">`, inline `<style>`, every text value escaped with `html.escape`, `@media print { .chapter { break-before: page; } }`.
- Tests: snapshot-style checks on small fixture recipes (TOC links resolve to existing anchors; HTML escaping of `<` and `&`; untagged recipe lands in "Other").

### 7. CLI command — `cli.py`
- `recipes cookbook SOURCES... [-o FILE] [--format md|html] [--title TEXT] [--calories CSV]`.
- Sources dispatched by extension: `.json` → `load_recipes`, `.txt` → `parse_recipe_text`; anything else → error message and exit code 1.
- Without `-o`, Markdown goes to stdout; with `-o`, writes UTF-8 and prints the path.
- Tests: `main([...])` end to end with `tmp_path`, unknown extension, format from extension vs `--format`.

### 8. Docs
- README: new command in "Commands", new modules in "Layout".
- Generate `cookbook.md` / `cookbook.html` from the sample data once and look at them (including print preview of the HTML).

## Out of scope (for later)
- Pantry off-by-one (`<=`), rejecting zero/negative servings in `scale`, a German cookbook, PDF output, an ingredient index, scaling the whole cookbook to N servings.

## Risks
- Calorie numbers are rough (ml ≈ g, cup sizes, piece weights) — the output says "approx." and lists what was not counted.
- Making `Ingredient.amount` optional touches every user of `amount` (`report`, `pantry`, `models.scaled_to`, `storage`); mypy will point them out.
