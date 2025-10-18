from typing import Optional, Tuple
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.offsetbox import OffsetImage, AnnotationBbox


def _pts_to_fig(fig: plt.Figure, x_pts: float, y_pts: float) -> Tuple[float, float]:
    """
    Convert a horizontal and vertical offset expressed in points into figure coordinates
    in the range [0, 1]. This keeps paddings visually consistent across DPIs and sizes.
    """
    w_in, h_in = fig.get_size_inches()
    return (x_pts / 72.0) / w_in, (y_pts / 72.0) / h_in


def _add_logo_bottom_right_aligned_to_source(
    fig: plt.Figure,
    logo_path: str,
    source_bbox_fig,
    pad_right_pts: float = 8.0,
    pad_vert_pts: float = 0.0,
    logo_zoom: float = 1.0,
) -> None:
    """
    Add a PNG logo so that its bottom-right corner aligns with the source text baseline.
    The logo is positioned at the right edge with a right padding in points; the vertical
    anchor is the bottom of the source bbox plus an optional vertical padding.
    """
    img = plt.imread(logo_path)
    padx_fig, pady_fig = _pts_to_fig(fig, pad_right_pts, pad_vert_pts)

    # Anchor coordinate in figure space
    x_anchor = 1.0 - padx_fig
    y_anchor = source_bbox_fig.y0 + pady_fig

    ab = AnnotationBbox(
        OffsetImage(img, zoom=logo_zoom),
        (x_anchor, y_anchor),
        xycoords=fig.transFigure,
        frameon=False,
        box_alignment=(1.0, 0.0),  # align image's bottom-right to the anchor
    )
    fig.add_artist(ab)


def finalise_plot(
    fig: plt.Figure,
    output_path: Optional[str] = None,
    source: Optional[str] = None,
    logo_path: Optional[str] = None,
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
    # These are paddings/size controls; no enforced sizing unless asked for.
    logo_right_pad_pts: float = 8.0,
    logo_vertical_pad_pts: float = 0.0,
    logo_zoom: float = 1.0,
    fig_size: Tuple[int, int] = (12, 7),
    dpi: int = 300,
    divider_gap_pts: float = 10.0,
    enforce_size: bool = False,
) -> None:
    """
    Finalise and save a figure in a BBC-style layout. Titles and subtitles are optional and do
    not change the figure size unless enforce_size is True. If source text is provided, a grey
    divider is drawn at a constant point-based gap above the rendered source text. If a logo is
    provided, it is drawn with its bottom-right corner aligned to the source baseline at the
    bottom-right of the figure, using point-based paddings for consistent spacing.
    """
    if enforce_size:
        fig.set_size_inches(*fig_size)

    if title or subtitle:
        fig.subplots_adjust(top=0.82)

    if title:
        fig.suptitle(title, x=0.05, y=0.99, ha="left")

    if subtitle:
        fig.text(
            0.05, 0.90, subtitle, ha="left", fontsize=17, transform=fig.transFigure
        )

    # Draw source and divider; measure bbox to align the logo
    source_bbox_fig = None
    if source:
        src_text = fig.text(
            0.5,  # center horizontally; change to 0.01 + ha="left" if preferred
            0.012,  # baseline near bottom
            source,
            ha="center",
            va="bottom",
            fontsize=14,
            color="#080808",
            transform=fig.transFigure,
        )

        # Render to get accurate extents
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        bbox_disp = src_text.get_window_extent(renderer=renderer)
        source_bbox_fig = bbox_disp.transformed(fig.transFigure.inverted())

        # Divider a fixed gap above the top of the source bbox
        _, gap_fig_y = _pts_to_fig(fig, 0.0, divider_gap_pts)
        y_divider = source_bbox_fig.y1 + gap_fig_y

        fig.add_artist(
            Line2D(
                [0.0, 1.0],
                [y_divider, y_divider],
                transform=fig.transFigure,
                linewidth=2.0,
                color="#ACA6A6FF",
            )
        )

    # Logo: align bottom-right to the source baseline if we have a source; otherwise bottom-right
    if logo_path:
        if source_bbox_fig is not None:
            _add_logo_bottom_right_aligned_to_source(
                fig,
                logo_path,
                source_bbox_fig,
                pad_right_pts=logo_right_pad_pts,
                pad_vert_pts=logo_vertical_pad_pts,
                logo_zoom=logo_zoom,
            )
        else:
            # No source: place at bottom-right with a sensible baseline (same y as default source)
            _, y_pad = _pts_to_fig(fig, 0.0, logo_vertical_pad_pts)
            x_pad, _ = _pts_to_fig(fig, logo_right_pad_pts, 0.0)
            x_anchor = 1.0 - x_pad
            y_anchor = 0.012 + y_pad
            img = plt.imread(logo_path)
            fig.add_artist(
                AnnotationBbox(
                    OffsetImage(img, zoom=logo_zoom),
                    (x_anchor, y_anchor),
                    xycoords=fig.transFigure,
                    frameon=False,
                    box_alignment=(1.0, 0.0),
                )
            )

    # Save if requested
    if output_path:
        fig.savefig(output_path, dpi=dpi, facecolor="white")
