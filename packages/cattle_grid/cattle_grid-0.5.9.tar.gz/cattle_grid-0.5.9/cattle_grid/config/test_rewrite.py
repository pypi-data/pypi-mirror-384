from .rewrite import RewriteConfiguration


def test_from_rules_none():
    config = RewriteConfiguration.from_rules(None)

    assert config.rewrite("method", ["group"]) == "method"


def test_add_new_rules():
    config = RewriteConfiguration.from_rules({})

    assert config.rewrite("method", ["group"]) == "method"

    config.add_rules("group", {"method": "changed"})

    assert config.rewrite("method", ["group"]) == "changed"


def test_add_new_rules_no_overwrite():
    config = RewriteConfiguration.from_rules({"group": {"method": "unchanged"}})

    assert config.rewrite("method", ["group"]) == "unchanged"

    config.add_rules("group", {"method": "changed"})

    assert config.rewrite("method", ["group"]) == "unchanged"
