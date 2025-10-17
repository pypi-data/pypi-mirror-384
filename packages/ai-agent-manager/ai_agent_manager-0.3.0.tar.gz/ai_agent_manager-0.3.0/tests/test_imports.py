"""Smoke tests to verify basic package structure."""


def test_package_import():
    """Test that the package can be imported."""
    import ai_configurator
    assert ai_configurator is not None


def test_models_exist():
    """Test that models module exists."""
    from ai_configurator import models
    assert models is not None


def test_services_exist():
    """Test that services module exists."""
    from ai_configurator import services
    assert services is not None


def test_tui_exists():
    """Test that TUI module exists."""
    from ai_configurator import tui
    assert tui is not None
