import matplotlib as mpl


def bbc_theme(font_family: str = "DejaVu Sans") -> None:
    """Apply the BBC theme via Matplotlib rcParams; integrates with Seaborn if available."""
    base_color = "#222222"
    grid_color = "#cbcbcb"

    rc = {
        "font.family": font_family,
        "axes.titlesize": 20,
        "axes.titleweight": "bold",
        "axes.titlecolor": base_color,
        "axes.labelsize": 0,
        "xtick.labelsize": 18,
        "ytick.labelsize": 18,
        "text.color": base_color,
        "figure.titlesize": 24,
        "figure.titleweight": "bold",
        "axes.edgecolor": "none",
        "axes.grid": True,
        "axes.axisbelow": True,
        "axes.prop_cycle": mpl.cycler(
            color=[
                "#007f7f",
                "#b55b49",
                "#e0a43b",
                "#76a7bf",
                "#8b63b7",
                "#6a7a3d",
                "#ff7f0e",
                "#2ca02c",
                "#d62728",
                "#9467bd",
            ]
        ),
        "grid.color": grid_color,
        "grid.linestyle": "-",
        "grid.linewidth": 1,
        "xtick.bottom": False,
        "xtick.top": False,
        "ytick.left": False,
        "ytick.right": False,
        "legend.frameon": False,
        "legend.loc": "upper center",
        "legend.framealpha": 0,
        "legend.fontsize": 18,
    }
    mpl.rcParams.update(rc)

    try:
        import seaborn as sns  # type: ignore

        sns.set_style("whitegrid", rc=rc)
    except Exception:
        pass
