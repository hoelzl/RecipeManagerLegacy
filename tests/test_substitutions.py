from recipe_manager.substitutions import suggest_substitutions


def test_known_ingredient_has_substitutes():
    assert "margarine" in suggest_substitutions("butter")


def test_lookup_is_case_insensitive():
    assert suggest_substitutions("Butter") == suggest_substitutions("butter")


def test_unknown_ingredient_returns_empty():
    assert suggest_substitutions("dragonfruit") == []
