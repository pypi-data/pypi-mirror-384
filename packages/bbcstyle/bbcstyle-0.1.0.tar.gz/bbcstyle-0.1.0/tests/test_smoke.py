"""
Minimal smoke tests to verify that the package imports and, if a theme hook exists,
that calling it does not raise. They are safe to run in CI and locally.
"""

from __future__ import annotations

import importlib
from types import ModuleType
from typing import Callable, Optional


def test_imports() -> None:
    """Import the package without raising."""
    mod: ModuleType = importlib.import_module("bbcstyle")
    assert mod is not None


def test_theme_hook_callable_if_present() -> None:
    """If a theme hook exists, ensure it is callable and does not raise when called."""
    mod: ModuleType = importlib.import_module("bbcstyle")
    hook_name: Optional[str] = next(
        (
            n
            for n in ("set_theme", "use", "apply", "mpl_style", "style")
            if hasattr(mod, n)
        ),
        None,
    )
    if hook_name is None:
        # No public hook yet; acceptable for 0.1.0.
        return
    hook: Callable[[], None] = getattr(mod, hook_name)
    hook()
