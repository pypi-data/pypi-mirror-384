"""Rich utility functions and availability checking.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""


def _check_rich_available() -> bool:
    """Check if Rich is available by attempting imports."""
    try:
        import importlib.util

        # Check if rich modules are available without importing them
        if (
            importlib.util.find_spec("rich.console") is None
            or importlib.util.find_spec("rich.text") is None
        ):
            return False

        # Check if our rich components are available
        if importlib.util.find_spec("glaip_sdk.rich_components") is None:
            return False

        return True
    except Exception:
        return False


RICH_AVAILABLE = _check_rich_available()
