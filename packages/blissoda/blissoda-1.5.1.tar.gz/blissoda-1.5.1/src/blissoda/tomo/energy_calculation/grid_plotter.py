from __future__ import annotations

from typing import Iterable
from typing import Mapping
from typing import Optional
from typing import Sequence

import numpy as np

from ...flint import WithFlintAccess
from ...flint import capture_errors


class GridPlot(WithFlintAccess):
    """Keep a named Flint grid tab alive and easy to update"""

    def __init__(
        self, unique_name: str = "grid-plot", window_title: str = "Energy Calculation"
    ) -> None:
        super().__init__()
        self._unique_name = unique_name
        self._window_title = window_title
        self._rows = 0
        self._cols = 0

    def _container(self, *, select: bool = True):
        return self._flint_client.get_plot(
            "grid",
            name=self._window_title,
            unique_name=self._unique_name,
            selected=select,
        )

    @staticmethod
    def _as_float_array(a) -> np.ndarray:
        return (
            np.asarray(a, dtype=float) if a is not None else np.array([], dtype=float)
        )

    @staticmethod
    def _clean_plot(p) -> None:
        clean = getattr(p, "clean_data", None)
        if callable(clean):
            clean()

    @staticmethod
    def _set_plot_labels(
        p, *, title: Optional[str], xlabel: Optional[str], ylabel: Optional[str]
    ) -> None:
        if title is not None:
            p.title = title
        if xlabel is not None:
            p.xlabel = xlabel
        if ylabel is not None:
            p.ylabel = ylabel

    @staticmethod
    def _add_curve(
        p,
        x: np.ndarray,
        y: np.ndarray,
        *,
        legend: str,
        color: Optional[str] = None,
        linewidth: Optional[float] = None,
    ) -> None:
        kwargs = {"legend": legend}
        if color is not None:
            kwargs["color"] = color
        if linewidth is not None:
            kwargs["linewidth"] = linewidth
        p.add_curve(x, y, **kwargs)

    @capture_errors
    def clear(self) -> None:
        """Clear all known cells."""
        if not (self._rows and self._cols):
            return
        cont = self._container(select=False)
        for r in range(self._rows):
            for c in range(self._cols):
                p = cont.get_plot("curve", row=r, col=c)
                self._clean_plot(p)

    @capture_errors
    def set_layout(self, rows: int, cols: int) -> None:
        """Remember target grid size and pre-create visible cells."""
        rows, cols = max(1, int(rows)), max(1, int(cols))
        self._rows, self._cols = rows, cols
        cont = self._container(select=True)
        for r in range(rows):
            for c in range(cols):
                p = cont.get_plot("curve", row=r, col=c)
                self._clean_plot(p)

    @capture_errors
    def set_cell(
        self,
        row: int,
        col: int,
        *,
        x,
        series: Sequence[Mapping],
        title: Optional[str] = None,
        xlabel: Optional[str] = None,
        ylabel: Optional[str] = None,
    ) -> None:
        """Update a single cell (row, col) with one or more curves."""
        r, c = int(row), int(col)
        cont = self._container(select=True)
        plot = cont.get_plot("curve", row=r, col=c)
        self._clean_plot(plot)

        self._set_plot_labels(plot, title=title, xlabel=xlabel, ylabel=ylabel)

        x_arr = None if x is None else self._as_float_array(x)
        for s in series or []:
            y = s.get("y")
            if y is None:
                continue
            y_arr = self._as_float_array(y)

            if x_arr is None:
                xx = np.arange(y_arr.size, dtype=float)
            else:
                n = min(x_arr.size, y_arr.size)
                if n == 0:
                    continue
                xx = x_arr[:n]
                y_arr = y_arr[:n]

            self._add_curve(
                plot,
                xx,
                y_arr,
                legend=s.get("label", "series"),
                color=s.get("color"),
                linewidth=s.get("linewidth"),
            )

        self._rows = max(self._rows, r + 1)
        self._cols = max(self._cols, c + 1)

    @capture_errors
    def set_cells(self, batch: Iterable[Mapping]) -> None:
        """Batch update: iterable of dicts accepted by set_cell."""
        for item in batch:
            d = dict(item)
            self.set_cell(
                int(d.get("row", 0)),
                int(d.get("col", 0)),
                x=d.get("x"),
                series=d.get("series") or (),
                title=d.get("title"),
                xlabel=d.get("xlabel"),
                ylabel=d.get("ylabel"),
            )
