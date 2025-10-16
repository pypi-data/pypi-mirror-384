from __future__ import annotations
from typing import Optional

from lightningchart.charts import Chart
from lightningchart.series import (
    ComponentWithPaletteColoring,
    SeriesWithWireframe,
    SeriesWithIntensityInterpolation,
    SeriesWithCull,
    SeriesWithAddValues,
    SeriesWith3DShading,
    Series,
    SeriesWithClear,
)
from lightningchart.utils.utils import LegendOptions, build_series_legend_options


class SurfaceScrollingGridSeries(
    ComponentWithPaletteColoring,
    SeriesWithWireframe,
    SeriesWithIntensityInterpolation,
    SeriesWithCull,
    SeriesWithAddValues,
    SeriesWith3DShading,
    SeriesWithClear,
):
    """Series for visualizing 3D surface data in a grid with automatic scrolling features."""

    def __init__(
        self,
        chart: Chart,
        columns: int,
        rows: int,
        scroll_dimension: str = 'columns',
        automatic_color_index: int = None,
        legend: Optional[LegendOptions] = None,  
    ):
        Series.__init__(self, chart)

        legend_options = build_series_legend_options(legend)

        self.instance.send(
            self.id,
            'surfaceScrollingGridSeries',
            {
                'chart': self.chart.id,
                'automaticColorIndex': automatic_color_index,
                'columns': columns,
                'rows': rows,
                'scrollDimension': scroll_dimension,
                'legend': legend_options if legend_options else None
            },
        )

    def set_start(self, x: int | float, z: int | float):
        """Set start coordinate of surface on its X and Z axis where the first surface sample will be positioned

        Args:
            x: x-coordinate.
            z: z-coordinate.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setStartXZ', {'x': x, 'z': z})
        return self

    def set_step(self, x: int | float, z: int | float):
        """Set Step between each consecutive surface value on the X and Z Axes.

        Args:
            x: x-coordinate.
            z: z-coordinate.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setStepXZ', {'x': x, 'z': z})
        return self
