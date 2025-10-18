from .finalise_plot import finalise_plot  # or wherever it lives
from .theme import bbc_theme as set_theme


def use() -> None:
    """Apply the BBC theme globally (alias to set_theme)."""
    set_theme()


__all__ = ["finalise_plot", "set_theme", "use"]
