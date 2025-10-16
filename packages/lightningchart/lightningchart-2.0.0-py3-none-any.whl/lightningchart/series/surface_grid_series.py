from __future__ import annotations
from typing import Optional

from lightningchart.charts import Chart
from lightningchart.series import (
    ComponentWithPaletteColoring,
    SeriesWithInvalidateIntensity,
    SeriesWithWireframe,
    SeriesWithInvalidateHeight,
    SeriesWithIntensityInterpolation,
    SeriesWithCull,
    SeriesWith3DShading,
    Series,
    SeriesWithClear,
)
from lightningchart.utils.utils import LegendOptions, build_series_legend_options


class SurfaceGridSeries(
    ComponentWithPaletteColoring,
    SeriesWithInvalidateIntensity,
    SeriesWithWireframe,
    SeriesWithInvalidateHeight,
    SeriesWithIntensityInterpolation,
    SeriesWithCull,
    SeriesWith3DShading,
    SeriesWithClear,
):
    """Series for visualizing 3D surface data in a grid."""

    def __init__(
        self,
        chart: Chart,
        columns: int,
        rows: int,
        data_order: str = 'columns',
        automatic_color_index: int = None,
        legend: Optional[LegendOptions] = None,  
    ):
        Series.__init__(self, chart)

        legend_options = build_series_legend_options(legend)
            
        self.columns = columns
        self.rows = rows
        self.instance.send(
            self.id,
            'surfaceGridSeries',
            {
                'chart': self.chart.id,
                'automaticColorIndex': automatic_color_index,
                'columns': columns,
                'rows': rows,
                'dataOrder': data_order,
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

    def set_end(self, x: int | float, z: int | float):
        """Set end coordinate of surface on its X and Z axis where the last surface sample will be positioned.

        Args:
            x: x-coordinate.
            z: z-coordinate.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setEndXZ', {'x': x, 'z': z})
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
