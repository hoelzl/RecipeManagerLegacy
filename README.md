# RecipeManagerLegacy

The **running example** for the *AI-Assisted Development (Copilot)* course. It is a
small command-line recipe manager: read recipes from JSON, scale them to a different
number of servings, suggest ingredient substitutions, import a recipe from a text
file, and print a formatted report. It also contains small catalog, shopping,
analytics, meal-planning, and pantry modules that give later workshops independent
change surfaces.

It works — mostly. It is deliberately a little *aged*: uneven test coverage, a couple
of long functions that are asking to be refactored, several narrow bugs on paths the
baseline tests miss, and a few obvious feature holes. That is on purpose. Over the
four weeks you will explore it, debug it, test it, refactor it, and extend it with
Copilot. Each implementation workshop names its own module, so keep using one Git
checkout and preserve the work you already reviewed.

## Layout

- `src/recipe_manager/models.py` — `Ingredient` and `Recipe` dataclasses
- `src/recipe_manager/parsing.py` — parse ingredient lines and a small recipe text format
- `src/recipe_manager/storage.py` — load / save recipes as JSON
- `src/recipe_manager/substitutions.py` — suggest ingredient substitutions
- `src/recipe_manager/report.py` — render a recipe as a text report
- `src/recipe_manager/formatting.py` — format amounts and ingredient lines (`7.5 g`, `1 1/2 cups`)
- `src/recipe_manager/calories.py` — estimate calories per serving from a kcal-per-100-g table
- `src/recipe_manager/cookbook.py` — arrange recipes into chapters by first tag
- `src/recipe_manager/cookbook_render.py` — render a cookbook as Markdown or HTML
- `src/recipe_manager/shopping.py` — shopping-list building blocks
- `src/recipe_manager/analytics.py` — small collection metrics
- `src/recipe_manager/meal_plans.py` — meal-plan representation (selection is missing)
- `src/recipe_manager/pantry.py` — check recipes against pantry stock
- `src/recipe_manager/catalog.py` — catalog filtering (general search is missing)
- `src/recipe_manager/exports.py` — stable export rows (serialization is missing)
- `src/recipe_manager/cli.py` — the command-line entry point
- `tests/` — pytest tests (some modules and important boundaries remain uncovered)
- `data/` — sample recipes (`recipes.json`), a deliberately broken file for validation exercises (`broken_recipes.json`), and text recipes (`pancakes.txt`, `waffles.txt`)
- `tools/kitchen_service.py` — simulated live inventory for the MCP workshop

## Commands

```bash
uv sync --extra dev                                 # install with dev tooling
uv run recipes show data/recipes.json               # print all recipes
uv run recipes scale data/recipes.json "Pancakes" 8 # scale a recipe to 8 servings
uv run recipes substitute butter                    # suggest substitutions
uv run recipes import data/pancakes.txt             # import a recipe from text
uv run recipes cookbook data/recipes.json data/waffles.txt -o cookbook.html
                                                    # cookbook as HTML (or .md; stdout if no -o)
uv run tools/check.py                               # full check: lint, types, tests
uv run pytest -q                                    # only the tests
uv run ruff check src tests                         # only lint
uv run mypy src tests                               # only the type-check
```

`recipes cookbook` accepts any mix of `.json` collections and `.txt` recipes. Each
recipe appears once, in the chapter of its first tag (untagged recipes go to
"Other"). Calories come from `data/ingredient_calories.en.csv` when run from the
project folder, or from `--calories FILE`; they are approximate (volumes counted as
water, typical piece weights) and list the ingredients that could not be counted.
Options: `--title`, `--format md|html`. A recipe title that appears in two input
files is an error — `data/recipes.json` and `data/pancakes.txt` both contain
"Pancakes".

The local MCP fixture in `tools/kitchen_service.py` exposes `list_menu`,
`get_inventory`, `quote_recipe`, and `reserve_recipe`. Lettuce is deliberately scarce,
so a four-serving garden salad is unavailable; other stock, prices, the session ID,
and reservations live only in the running process. The server is a self-contained
PEP 723 script — start it with `uv --no-config run tools/kitchen_service.py` —
and you can exercise the complete deterministic contract with:

```bash
uv --no-config run tools/smoke_kitchen_mcp.py
```

## Containers

Two different files, two different jobs:

- **`.devcontainer.example/devcontainer.json`: the environment you *work* in.**
  VS Code opens the project inside a container, so an agent's commands run there
  and can't reach your other files and programs. To use it (Docker Desktop
  required): rename `.devcontainer.example` to `.devcontainer`, then run
  **Dev Containers: Reopen in Container**. The project folder stays writable from
  inside (including `.git`), VS Code forwards your git credentials (and your SSH
  agent, if one is running) and copies your `.gitconfig`, and the network is open, so commit before an agent session and keep secrets
  out of the folder.

  **Give the folder its own Git repository first** (`git init`, then a first
  commit), and open exactly this folder. If the folder sits inside another
  repository (for example a clone of the course materials), Dev Containers
  mounts that repository's **root** into the container, and the agent can reach
  everything in it, not just this project.

  **Windows: `distro mount service ... ubuntu.sock: no such file or directory`.**
  VS Code tries to mount a display socket from your WSL distribution, but Docker
  Desktop is not integrated with that distribution. Either enable it (Docker
  Desktop → Settings → Resources → WSL integration → turn on your distribution →
  Apply & restart), or switch the mount off in your VS Code user settings, since
  this container needs no GUI: `"dev.containers.mountWaylandSocket": false`.
  Then run **Dev Containers: Rebuild and Reopen in Container**.
- **`Dockerfile`: an image that *runs* the app.**

  ```bash
  docker build -t recipes .
  docker run --rm recipes show data/recipes.json
  docker run --rm recipes scale data/recipes.json "Pancakes" 8
  ```

  The image holds only the installed package and the sample data, runs as a
  non-root user, and contains no uv or build tools.

The starter ships `*.example` templates for the agent-configuration artifacts
(`AGENTS.md.example`, `.github/copilot-instructions.md.example`,
`.github/instructions/tests.instructions.md.example`,
`.github/skills/prepare-pr/SKILL.md.example`,
`.github/workflows/copilot-setup-steps.yml.example` for the cloud agent). They are inert until you copy them to
their live names (`cp AGENTS.md.example AGENTS.md`). Workshops that ask you to write
these artifacts yourself use the templates only as fallback and reference; the
deterministic-gates workshop starts from `AGENTS.md.example` directly. Like the code,
the templates are a little aged on purpose: the information-architecture workshop
audits them, so read them as material to improve, not as models to copy.
