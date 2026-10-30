# /// script
# requires-python = ">=3.11"
# dependencies = ["fastmcp>=3.4,<4"]
# ///
"""Exercise the deterministic contract of the kitchen MCP service.

Run it with uv's PEP 723 support (no project environment needed):

    uv --no-config run tools/smoke_kitchen_mcp.py
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from fastmcp import Client
from fastmcp.client.transports import StdioTransport

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "tools" / "kitchen_service.py"
EXPECTED_TOOLS = {"list_menu", "get_inventory", "quote_recipe", "reserve_recipe"}


def _payload(result: Any) -> dict[str, Any]:
    if result.is_error:
        raise AssertionError(f"tool call failed: {result.content}")
    if result.structured_content is not None:
        payload = result.structured_content
        if "result" in payload and len(payload) == 1:
            payload = payload["result"]
        if isinstance(payload, dict):
            return payload
    for block in result.content:
        text = getattr(block, "text", None)
        if text:
            payload = json.loads(text)
            if isinstance(payload, dict):
                return payload
    raise AssertionError("tool returned no structured object")


async def _run() -> None:
    # kitchen_service.py is self-contained (PEP 723 + its own sys.path bootstrap),
    # so the launch needs no --from, no PYTHONPATH, and no working directory.
    # --quiet keeps uv's own "Installed N packages" chatter out of the output.
    transport = StdioTransport(
        command="uv",
        args=["--no-config", "--quiet", "run", str(SERVER)],
        cwd=str(ROOT),
    )

    async with Client(transport) as client:
        listed = await client.list_tools()
        tools = {tool.name: tool for tool in listed}
        assert set(tools) == EXPECTED_TOOLS
        annotations = {
            name: tool.annotations.model_dump(exclude_none=True)
            if tool.annotations is not None
            else None
            for name, tool in tools.items()
        }
        for name in ("list_menu", "get_inventory", "quote_recipe"):
            assert annotations[name]["readOnlyHint"] is True
            assert annotations[name]["destructiveHint"] is False
            assert annotations[name]["idempotentHint"] is True
        assert annotations["reserve_recipe"]["readOnlyHint"] is False
        assert annotations["reserve_recipe"]["destructiveHint"] is True
        assert annotations["reserve_recipe"]["idempotentHint"] is True

        menu = _payload(await client.call_tool("list_menu"))
        before = _payload(await client.call_tool("get_inventory"))
        quotes = {
            recipe_id: _payload(
                await client.call_tool(
                    "quote_recipe",
                    {"recipe_id": recipe_id, "servings": 4},
                )
            )
            for recipe_id in menu["recipes"]
        }

        assert quotes["garden-salad"]["available"] is False
        assert before["items"]["lettuce"]["available"] == 3
        assert quotes["garden-salad"]["required"]["lettuce"] == 4
        available = [quote for quote in quotes.values() if quote["available"]]
        assert len(available) >= 2
        chosen = min(available, key=lambda quote: quote["total_cents"])

        arguments = {
            "recipe_id": chosen["recipe_id"],
            "servings": 4,
            "request_id": "workshop-01",
        }
        first = _payload(await client.call_tool("reserve_recipe", arguments))
        after_first = _payload(await client.call_tool("get_inventory"))
        replay = _payload(await client.call_tool("reserve_recipe", arguments))
        after_replay = _payload(await client.call_tool("get_inventory"))

        assert first["reserved"] is True and first["replayed"] is False
        assert replay["reserved"] is True and replay["replayed"] is True
        assert after_replay == after_first
        for ingredient, amount in chosen["required"].items():
            assert (
                before["items"][ingredient]["available"]
                - after_first["items"][ingredient]["available"]
                == amount
            )

        other = next(
            quote for quote in available if quote["recipe_id"] != chosen["recipe_id"]
        )
        conflict = await client.call_tool(
            "reserve_recipe",
            {
                "recipe_id": other["recipe_id"],
                "servings": 4,
                "request_id": "workshop-01",
            },
            raise_on_error=False,
        )
        assert conflict.is_error
        conflict_message = " ".join(
            getattr(block, "text", "") for block in conflict.content
        )
        assert "request_id already used" in conflict_message
        after_conflict = _payload(await client.call_tool("get_inventory"))
        assert after_conflict == after_first

        print(
            json.dumps(
                {
                    "session_id": menu["session_id"],
                    "tools": sorted(tools),
                    "annotations": annotations,
                    "unavailable_quote": quotes["garden-salad"],
                    "selected_quote": chosen,
                    "before": before,
                    "after_first": after_first,
                    "after_conflict": after_conflict,
                    "replay": replay,
                    "conflict_message": conflict_message,
                    "conflict_rejected": True,
                },
                indent=2,
                sort_keys=True,
            )
        )
        print("PASS: kitchen MCP contract holds (conflict rejected as expected)")


if __name__ == "__main__":
    asyncio.run(_run())
