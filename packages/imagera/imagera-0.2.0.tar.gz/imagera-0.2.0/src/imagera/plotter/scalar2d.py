from __future__ import annotations
import math
from dataclasses import replace
from typing import Optional
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from numpy.typing import NDArray
from imagera.plotter.plot_params import PlotParams
from imagera.plotter.helpers import coerce_label
from imagera.plotter.cmap import resolve_cmap
from imagera.plotter.values_minmax import resolve_limits_from_params

class ScalarField2D:
    def __init__(self, data: NDArray[np.floating], params: Optional[PlotParams] = None, **overrides):
        v = np.asarray(data, dtype=float)
        if v.ndim != 2:
            raise ValueError(f"'data' must be 2D, got shape {v.shape}")
        base = params if params is not None else PlotParams()
        self.params = replace(base, **overrides) if overrides else base
        self.data = v
        self.extent = self.params.extent
        self.v_min: Optional[float] = None
        self.v_max: Optional[float] = None

    def render(self, *,
               annotate_xy: Optional[tuple[float, float]] = None,
               plot_label: Optional[str] = None,
               **overrides) -> np.ndarray:
        """Standalone renderer: builds a Figure, draws, returns RGBA."""
        p = replace(self.params, **overrides)
        use_full_bleed = p.hide_ticks and not p.with_colorbar
        if use_full_bleed:
            fig = plt.figure(figsize=p.size_in, dpi=p.dpi)
            ax = fig.add_axes((0, 0, 1, 1))
        else:
            fig, ax = plt.subplots(figsize=p.size_in, dpi=p.dpi, layout="constrained")
        self.draw(ax, params=p, annotate_xy=annotate_xy, plot_label=plot_label, with_colorbar=p.with_colorbar)
        canvas = FigureCanvas(fig)
        canvas.draw()
        rgba = np.asarray(canvas.buffer_rgba()).copy()
        plt.close(fig)
        return rgba

    def render_into(self, ax, *, norm=None, annotate_xy=None,
                    plot_label=None, with_colorbar=False, **overrides):
        """Inline renderer: draws into an existing Axes and returns AxesImage."""
        p = replace(self.params, **overrides)
        im, cbar = self.draw(ax, params=p, norm=norm, annotate_xy=annotate_xy,
                             plot_label=plot_label, with_colorbar=with_colorbar)
        return im, cbar  # (AxesImage, Optional[Colorbar])

    def draw(self, ax, *, params: PlotParams, norm=None,
             annotate_xy=None, plot_label=None, with_colorbar=False):
        """Draw the image and decorates the axes."""
        extent = self.extent
        if extent is None:
            ny, nx = self.data.shape
            extent = (0.0, float(nx), 0.0, float(ny))

        vmin, vmax = resolve_limits_from_params(self.data, params.v_min, params.v_max)

        cmap, norm = resolve_cmap(
            params.cmap,
            values=self.data,
            vmin=vmin,
            vmax=vmax,
            use_levels=params.use_levels,
            n_levels=params.n_levels,
        )
        im = ax.imshow(
            self.data,
            extent=extent,
            origin="lower",
            aspect="equal",
            cmap=cmap,
            norm=norm,
            interpolation=params.interpolation
        )

        cbar = None
        if with_colorbar:
            cbar = ax.figure.colorbar(im, ax=ax, pad=0.02)
            lbl = coerce_label(params.value_label)
            if lbl is not None:
                cbar.set_label(lbl)

        xlbl = coerce_label(params.x_label); ylbl = coerce_label(params.y_label)
        if xlbl: ax.set_xlabel(xlbl)
        if ylbl: ax.set_ylabel(ylbl)

        if params.hide_ticks:
            ax.set_xticks([]); ax.set_yticks([])

        if annotate_xy is not None:
            ax.set_xlabel(f"({annotate_xy[0]:.3g}, {annotate_xy[1]:.3g})", labelpad=2, fontsize=9)

        title = plot_label if plot_label is not None else params.plot_label
        if title:
            ax.set_title(str(title))

        if params.show_grid and (params.grid_pitch is not None and params.grid_pitch > 0):
            xmin, xmax, ymin, ymax = extent
            pitch = float(params.grid_pitch)
            def first_tick(a, step): return math.ceil(a/step)*step
            x0 = first_tick(xmin, pitch); y0 = first_tick(ymin, pitch)
            xs = np.arange(x0, xmax + 1e-12, pitch)
            ys = np.arange(y0, ymax + 1e-12, pitch)
            ax.vlines(xs, ymin, ymax, colors=params.grid_color, linewidth=0.5, alpha=1.0, zorder=5)
            ax.hlines(ys, xmin, xmax, colors=params.grid_color, linewidth=0.5, alpha=1.0, zorder=5)

        return im, cbar