# bbcstyle
[![PyPI version](https://img.shields.io/pypi/v/bbcstyle.svg)](https://pypi.org/project/bbcstyle/)
![Python versions](https://img.shields.io/pypi/pyversions/bbcstyle.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-informational.svg)

bbcstyle is a lightweight Python package that applies a BBC News-inspired visual theme to Matplotlib and Seaborn plots. It helps you create clean, publication-ready charts with consistent typography, minimalist gridlines, and optional source annotations or logos. Inspired by the R package [`bbplot`](https://github.com/bbc/bbplot)  but tailored for Python, this theme is ideal for reports, dashboards, and data journalism.


<img src="assets/front_page.png" alt="BBC style" width="800"/>


## Quick start

### 1. Install the package
```bash
 pip install bbcstyle
```
### 2. Enable the theme
Call the theme hook **once** at the start of your script/notebook:
```python
import bbcstyle as bbc

bbc.set_theme()
```
### 3. Finish figures with the finaliser
After you build your Matplotlib figure, call `finalise_pot` to add the BBC-style framing (title, subtitle, divider abot the source, and optional logo) and to save it if you provide a path.

### Example A - line chart:
```python
import matplotlib.pyplot as plt
import numpy as np
import bbcstyle as bbc
from bbcstyle import finalise_plot

bbc.set_theme()

x = np.arange(0, 24)
fig, ax = plt.subplots(figsize=(9, 5), dpi=150)

ax.plot(x, np.cumsum(np.random.normal(0, 0.8, size=x.size)), linewidth=2, label="North")
ax.plot(x, np.cumsum(np.random.normal(0, 0.8, size=x.size)), linewidth=2, label="South")
ax.plot(x, np.cumsum(np.random.normal(0, 0.8, size=x.size)), linewidth=2, label="East")
ax.plot(x, np.cumsum(np.random.normal(0, 0.8, size=x.size)), linewidth=2, label="West")

ax.legend(frameon=False, ncols=2)
ax.spines[["top", "right"]].set_visible(False)
ax.set_xlabel("Hour")
ax.set_ylabel("Index")

finalise_plot(
    fig=fig,
    title="Regional index over the day",
    subtitle="Synthetic data, 24 hours",
    source="Source: Example data",
    logo_path=None,                    # e.g. "assets/bbc_logo.png"
    output_path="out/line_chart.png",  # omit to skip saving
    dpi=300,
)
```
### Example B - bar chart using theme colors
The theme defines the color cycle in axes.prop_cycle. Use it directly so bars follow the theme palette.

```python
import matplotlib.pyplot as plt
import bbcstyle as bbc
from bbcstyle import finalise_plot

bbc.set_theme()

cats = ["A", "B", "C", "D", "E"]
vals = [5, 7, 3, 6, 4]

# Pull colors from the active theme cycle
colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]

fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
ax.bar(cats, vals, color=colors[: len(cats)])

ax.spines[["top", "right"]].set_visible(False)
ax.set_xlabel("Category")
ax.set_ylabel("Value")

finalise_plot(
    fig=fig,
    title="Example: Bar Chart",
    subtitle="Five categories coloured by the theme",
    source="Source: Example data",
    logo_path=None,
    output_path="out/bar_chart.png",
    dpi=300,
)
```
### Notes
- Call `bbc.set_theme()` **before** creating figures so rcParams apply to everything you draw.
- finalise_plot:
    * Keeps your figure size unless you pass `enforce_size=True`.
    * Places a divider a fixed distance (in points) **above** the source line.
    * If `logo_path` and `source` are provided, the logo is anchored **bottom-right**, aligned to the source baseline.

- Avoid `plt.tight_layout()` after `finalise_plot`; the finaliser manages margins for title/subtitle/source.

## Gallery
`examples/gallery/01_bar_chart.py`

<img src="examples/gallery/out/bar_chart.png" alt="BBC style" width="600"/>

<br><br>

`examples/gallery/02_line_chart.py`

<img src="examples/gallery/out/line_chart.png" alt="BBC style" width="600"/>
<br><br>

`examples/gallery/03_scatter_plot.py`

<img src="examples/gallery/out/scatter.png" alt="BBC style" width="600"/>
<br><br>

`examples/gallery/04_histograms.py`

<img src="examples/gallery/out/histograms.png" alt="BBC style" width="600"/>
<br><br>

`examples/gallery/05_bubble_scatter.py`

<img src="examples/gallery/out/bubble_scatter.png" alt="BBC style" width="600"/>
<br><br>

Run them to generate PNGs in `examples/gallery/out/`.

## License

This project is licensed under the MIT License. See [LICENSE](./LICENSE) for details.

> **Note:** “BBC” is a trademark of the British Broadcasting Corporation. This project is not affiliated with, endorsed by, or sponsored by the BBC. “BBC-inspired” refers to the general look & feel of certain public graphics.

## Issues & support

Found a bug or have a feature request? Please open an issue and include:
- a **minimal code snippet** that reproduces the problem
- your **Python**, **Matplotlib**, and **Seaborn** versions, plus OS
- what you **expected** vs what you **observed**, and any screenshots

See [bug report](./.github/ISSUE_TEMPLATE/bug_report.md) and [feature request](./.github/ISSUE_TEMPLATE/feature_request.md) for details.

## Contributing

Contributions are welcome! A good first PR is often:
- a small fix to styling defaults,
- an additional **gallery** example in `examples/gallery/`,
- or a doc improvement.

See [contributing](./docs/CONTRIBUTING.md) for details.

### Quick dev setup:

```bash
python -m venv .venv && source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .
python -m pip install -U pytest ruff pre-commit
pre-commit install
pytest -q
```

### Guidelines
Open an issue before large changes.
Keep examples pure-Python (no notebooks) and save images to examples/gallery/out/.
Run ruff and the pre-commit hooks; keep PRs focused and small.
Add or update a test when changing behavior.
See [contributing](./docs/CONTRIBUTING.md) for details.

## Code of Conduct
We follow the [Contributor Covenant](./docs/CODE_OF_CONDUCT.md). By participating, you agree to uphold this standard.

## Authorship & credits
Created and maintained by Alessandro Tomassini (@ale-tom).
Thanks to contributors and the broader visualization community for inspiration. Any similarities to BBC graphics are purely stylistic; this project is independent of the BBC.

## Citation
If this package helps your work, please cite it:
```bibtex
@software{bbcstyle,
  title   = {bbcstyle: BBC-inspired theme for Matplotlib/Seaborn},
  author  = {Alessandro Tomassini},
  year    = {2025},
  version = {0.1.0},
  url     = {https://github.com/ale-tom/bbcstyle}
}
```
