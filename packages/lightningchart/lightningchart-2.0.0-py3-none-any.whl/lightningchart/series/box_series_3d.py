from __future__ import annotations
from typing import Optional

from lightningchart.charts import Chart
from lightningchart.series import (
    SeriesWithInvalidateData,
    SeriesWith3DShading,
    ComponentWithPaletteColoring,
    Series,
)
from lightningchart.utils.utils import LegendOptions, build_series_legend_options


class BoxSeries3D(SeriesWithInvalidateData, SeriesWith3DShading, ComponentWithPaletteColoring):
    """Series for visualizing 3D boxes."""

    def __init__(self, chart: Chart, automatic_color_index: int = None, legend: Optional[LegendOptions] = None,):
        Series.__init__(self, chart)

        legend_options = build_series_legend_options(legend)
            
        self.instance.send(self.id, 'boxSeries3D', {'chart': self.chart.id, 'automaticColorIndex': automatic_color_index, 'legend': legend_options if legend_options else None})

    def set_rounded_edges(self, roundness: int | float | None):
        """Set rounded edges of Boxes.
        NOTE: Rounded edges result in increased geometry precision, which in turn uses more rendering resources.

        Args:
            roundness: Either a number in range [0, 1] describing the amount of rounding
                or None to disable rounded edges.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setRoundedEdges', {'roundness': roundness})
        return self
