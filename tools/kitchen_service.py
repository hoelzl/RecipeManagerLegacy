# /// script
# requires-python = ">=3.11"
# dependencies = ["fastmcp>=3.4,<4"]
# ///
"""A tiny stateful MCP kitchen service.

The menu and the scarce items are static, but other stock and prices are generated
when the server starts and live only in that process. Reading this file cannot reveal
current stock or perform a reservation; clients must use the MCP tools.

Built with the standalone ``fastmcp`` package (3.x). The official ``mcp`` SDK 2.x
offers the same decorator model under the name ``MCPServer``. The pin stays below 4:
FastMCP 4 changed its API, and this service is written against 3.x.

Self-contained (PEP 723): start it from anywhere with

    uv --no-config run tools/kitchen_service.py
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from secrets import randbelow, token_hex

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.server.middleware import Middleware, MiddlewareContext

from recipe_manager.kitchen_ops import Inventory, KitchenState, Menu, Quote, Reservation

mcp = FastMCP("kitchenOps")

# The client chat shows its own tool-call trace; this log is the server's side of
# the story. Stdio servers may not print to stdout (that channel is the protocol),
# so the log goes to stderr and to `kitchen-calls.log` in the project folder.
# Whether a client shows a server's stderr depends on the client and on which
# process runs the server; the file is there either way.
CALL_LOG = Path(__file__).resolve().parents[1] / "kitchen-calls.log"
_log = logging.getLogger("kitchenOps")
_log.setLevel(logging.INFO)
_log.propagate = False  # keep fastmcp's root-level config from doubling the lines
_log.addHandler(logging.StreamHandler())  # stderr, default format
_file_log = logging.FileHandler(CALL_LOG, encoding="utf-8")
_file_log.setFormatter(logging.Formatter("%(asctime)s %(message)s", "%Y-%m-%d %H:%M:%S"))
_log.addHandler(_file_log)


class ToolCallLog(Middleware):
    """Log every tool call (arguments, success, expected failures)."""

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        name = context.message.name
        args = ", ".join(
            f"{key}={value!r}" for key, value in (context.message.arguments or {}).items()
        )
        _log.info("call %s(%s)", name, args)
        try:
            result = await call_next(context)
        except Exception as error:
            _log.info("fail %s: %s", name, error)
            raise
        _log.info("done %s", name)
        return result


mcp.add_middleware(ToolCallLog())

_MENU = {
    "tomato-soup": {"tomato": 3, "salt": 1},
    "pancakes": {"flour": 2, "milk": 1, "egg": 2},
    "garden-salad": {"lettuce": 1, "tomato": 2, "oil": 1},
}
_SESSION_ID = token_hex(4)
_STOCK = {
    ingredient: 3 if ingredient == "lettuce" else 20 + randbelow(21)
    for requirements in _MENU.values()
    for ingredient in requirements
}
_PRICE_CENTS = {ingredient: 40 + randbelow(261) for ingredient in _STOCK}
_STATE = KitchenState(
    session_id=_SESSION_ID,
    menu=_MENU,
    stock=_STOCK,
    price_cents=_PRICE_CENTS,
)
_READ_ONLY = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": False,
}
_RESERVATION = {
    "readOnlyHint": False,
    "destructiveHint": True,
    "idempotentHint": True,
    "openWorldHint": False,
}


@mcp.tool(annotations=_READ_ONLY)
def list_menu() -> Menu:
    """List recipe IDs and per-serving ingredient requirements."""
    return _STATE.list_menu()


@mcp.tool(annotations=_READ_ONLY)
def get_inventory() -> Inventory:
    """Return current stock and unit prices for this server session."""
    return _STATE.get_inventory()


@mcp.tool(annotations=_READ_ONLY)
def quote_recipe(recipe_id: str, servings: int) -> Quote:
    """Quote a recipe against current inventory without changing stock."""
    return _STATE.quote(recipe_id, servings)


@mcp.tool(annotations=_RESERVATION)
def reserve_recipe(recipe_id: str, servings: int, request_id: str) -> Reservation:
    """Reserve once; exact retries replay, conflicting request IDs fail."""
    try:
        return _STATE.reserve(recipe_id, servings, request_id)
    except ValueError as error:
        # An expected client error: the message reaches the agent as the tool
        # result; the server log stays free of a traceback.
        raise ToolError(str(error), log_level=logging.INFO) from error


if __name__ == "__main__":
    # One line per start: a restarted server has new stock, prices and session.
    _log.info("start session %s (log: %s)", _SESSION_ID, CALL_LOG)
    # Quiet start: no banner (which also skips the update check) and no INFO
    # log lines from fastmcp itself. Warnings and errors still reach stderr.
    mcp.run(show_banner=False, log_level="WARNING")
