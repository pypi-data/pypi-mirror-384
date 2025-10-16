from __future__ import annotations
from typing import Optional

from lightningchart.charts import Chart
from lightningchart.ui.axis import Axis
from lightningchart.series import (
    SeriesWithAddDataPoints,
    SeriesWithDataCleaning,
    Series,
    ComponentWithRangePaletteColoring,
    SeriesWithClear,
    SeriesWithDrawOrder,
)
from lightningchart.utils import convert_to_list, convert_color_to_hex
from lightningchart.utils.utils import LegendOptions, build_series_legend_options


class AreaRangeSeries(
    SeriesWithAddDataPoints,
    SeriesWithDataCleaning,
    ComponentWithRangePaletteColoring,
    SeriesWithClear,
    SeriesWithDrawOrder,
):
    """Series for visualizing 2D areas with ranges."""

    def __init__(
            self, 
            chart: Chart, 
            axis_x: Axis = None, 
            axis_y: Axis = None, 
            automatic_color_index: int = None, 
            legend: Optional[LegendOptions] = None,
            ):
        Series.__init__(self, chart)

        legend_options = build_series_legend_options(legend)

        self.instance.send(
            self.id,
            'areaRangeSeries',
            {'chart': self.chart.id, 'axisX': axis_x, 'axisY': axis_y, 'automaticColorIndex': automatic_color_index, 'legend': legend_options if legend_options else None},
        )

    def add_arrays_high_low(
        self,
        high: list[int | float],
        low: list[int | float],
        start: int | float = 0,
        step: int | float = 1,
    ):
        """Add two individual Arrays, one for high values, and another for low values.

        Args:
            high (list[int | float]): List of high values.
            low (list[int | float]): List of low values. Length should be equal to length of high.
            start (int | float): Start index of x-axis.
            step (int | float: The step length for x-axis.

        Returns:
            The instance of the class for fluent interface.
        """
        high = convert_to_list(high)
        low = convert_to_list(low)

        self.instance.send(
            self.id,
            'addArraysHighLow',
            {'high': high, 'low': low, 'step': step, 'start': start},
        )
        return self

    def set_high_fill_color(self, color: any):
        """Set the high area style of the Series.

        Args:
            color (Color): Color of the high area.

        Returns:
            The instance of the class for fluent interface.
        """
        color = convert_color_to_hex(color) if color is not None else None

        self.instance.send(self.id, 'setHighFillStyle', {'color': color})
        return self

    def set_high_stroke(self, thickness: int | float, color: any = None):
        """Set the high stroke style of the Series.

        Args:
            thickness (int | float): Thickness of the high stroke.
            color (Color): Color of the high stroke.

        Returns:
            The instance of the class for fluent interface.
        """
        color = convert_color_to_hex(color) if color is not None else None

        self.instance.send(
            self.id,
            'setHighStrokeStyle',
            {'thickness': thickness, 'color': color},
        )
        return self

    def set_low_fill_color(self, color: any):
        """Set the low area style of the Series.

        Args:
            color (Color): Color of the low area.

        Returns:
            The instance of the class for fluent interface.
        """
        color = convert_color_to_hex(color) if color is not None else None

        self.instance.send(self.id, 'setLowFillStyle', {'color': color})
        return self

    def set_low_stroke(self, thickness: int | float, color: any):
        """Set the low stroke style of the Series.

        Args:
            thickness (int | flaot): Thickness of the low stroke.
            color (Color): Color of the low stroke.

        Returns:
            The instance of the class for fluent interface.
        """
        color = convert_color_to_hex(color) if color is not None else None

        self.instance.send(
            self.id,
            'setLowStrokeStyle',
            {'thickness': thickness, 'color': color},
        )
        return self
