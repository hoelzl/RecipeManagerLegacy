from concurrent.futures import ThreadPoolExecutor

import pytest

from recipe_manager.kitchen_ops import KitchenState


def _kitchen() -> KitchenState:
    return KitchenState(
        session_id="test-session",
        menu={"soup": {"tomato": 2}, "salad": {"tomato": 1}},
        stock={"tomato": 10},
        price_cents={"tomato": 50},
    )


def _available(kitchen: KitchenState) -> int:
    return kitchen.get_inventory()["items"]["tomato"]["available"]


def test_quote_is_read_only():
    kitchen = _kitchen()
    quote = kitchen.quote("soup", 2)
    assert quote["required"] == {"tomato": 4}
    assert quote["total_cents"] == 200
    assert _available(kitchen) == 10


def test_exact_request_retry_replays_without_second_decrement():
    kitchen = _kitchen()
    first = kitchen.reserve("soup", 2, "request-1")
    after_first = _available(kitchen)
    replay = kitchen.reserve("soup", 2, "request-1")

    assert first["reserved"] and not first["replayed"]
    assert replay["reserved"] and replay["replayed"]
    assert after_first == 6
    assert _available(kitchen) == after_first


def test_request_id_reuse_with_different_payload_is_rejected():
    kitchen = _kitchen()
    kitchen.reserve("soup", 1, "request-1")

    with pytest.raises(ValueError, match="different recipe or serving count"):
        kitchen.reserve("salad", 1, "request-1")
    with pytest.raises(ValueError, match="different recipe or serving count"):
        kitchen.reserve("soup", 2, "request-1")


def test_distinct_request_ids_create_distinct_reservations():
    kitchen = _kitchen()
    kitchen.reserve("salad", 1, "request-1")
    kitchen.reserve("salad", 1, "request-2")
    assert _available(kitchen) == 8


def test_concurrent_same_key_decrements_stock_once():
    kitchen = _kitchen()
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(
            pool.map(lambda _: kitchen.reserve("soup", 2, "shared-key"), range(8))
        )

    assert sum(not result["replayed"] for result in results) == 1
    assert all(result["reserved"] for result in results)
    assert _available(kitchen) == 6


def test_concurrent_distinct_keys_cannot_oversubscribe_stock():
    kitchen = _kitchen()
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(
            pool.map(
                lambda index: kitchen.reserve("soup", 2, f"request-{index}"),
                range(8),
            )
        )

    assert sum(result["reserved"] for result in results) == 2
    assert _available(kitchen) == 2
