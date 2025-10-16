from __future__ import annotations
from typing import Optional

from lightningchart.charts import Chart
from lightningchart.ui.axis import Axis
from lightningchart.series import (
    ComponentWithPaletteColoring,
    SeriesWithWireframe,
    SeriesWithPixelInterpolation,
    SeriesWithDataCleaning,
    SeriesWithAddIntensityValues,
    Series,
    SeriesWithClear,
    SeriesWithDrawOrder,
)
from lightningchart.utils.utils import LegendOptions, build_series_legend_options


class HeatmapScrollingGridSeries(
    ComponentWithPaletteColoring,
    SeriesWithWireframe,
    SeriesWithPixelInterpolation,
    SeriesWithDataCleaning,
    SeriesWithAddIntensityValues,
    SeriesWithClear,
    SeriesWithDrawOrder,
    Series,
):
    """Series for visualizing 2D heatmap data in a grid with automatic scrolling features."""

    def __init__(
        self,
        chart: Chart,
        resolution: int,
        scroll_dimension: str = 'columns',
        automatic_color_index: int = None,
        heatmap_data_type: str = 'intensity',
        axis_x: Axis = None,
        axis_y: Axis = None,
        legend: Optional[LegendOptions] = None,
    ):
        Series.__init__(self, chart)

        legend_options = build_series_legend_options(legend)

        self.instance.send(
            self.id,
            'heatmapScrollingGridSeries',
            {
                'chart': self.chart.id,
                'scrollDimension': scroll_dimension,
                'automaticColorIndex': automatic_color_index,
                'heatmapDataType': heatmap_data_type,
                'resolution': resolution,
                'axisX': axis_x,
                'axisY': axis_y,
                'legend': legend_options if legend_options else None,
            },
        )

    def set_start(self, x: int | float, y: int | float):
        """Set start coordinate of Heatmap on its X and Y axis where the first heatmap sample will be positioned

        Args:
            x: x-coordinate.
            y: y-coordinate.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setStartXY', {'x': x, 'y': y})
        return self

    def set_step(self, x: int | float, y: int | float):
        """Set Step between each consecutive heatmap value on the X and Y Axes.

        Args:
            x: x-coordinate.
            y: y-coordinate.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setStepXY', {'x': x, 'y': y})
        return self
