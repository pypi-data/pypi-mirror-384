from __future__ import annotations
from typing import Optional

from lightningchart.charts import Chart
from lightningchart.series import (
    SeriesWithAddDataPoints,
    SeriesWithAddDataXYZ,
    SeriesWith3DPoints,
    SeriesWith3DLines,
    SeriesWith3DShading,
    Series,
    ComponentWithLinePaletteColoring,
    SeriesWithClear,
)
from lightningchart.utils.utils import LegendOptions, build_series_legend_options


class PointLineSeries3D(
    SeriesWithAddDataPoints,
    SeriesWithAddDataXYZ,
    SeriesWith3DPoints,
    SeriesWith3DLines,
    SeriesWith3DShading,
    ComponentWithLinePaletteColoring,
    SeriesWithClear,
):
    """Series for visualizing 3D lines with datapoints."""

    def __init__(
        self,
        chart: Chart,
        render_2d: bool = False,
        automatic_color_index: int = None,
        individual_lookup_values_enabled: bool = False,
        individual_point_color_enabled: bool = False,
        individual_point_size_axis_enabled: bool = False,
        individual_point_size_enabled: bool = False, 
        legend: Optional[LegendOptions] = None,
    ):
        Series.__init__(self, chart)

        legend_options = build_series_legend_options(legend)


        self.instance.send(
            self.id,
            'pointLineSeries3D',
            {
                'chart': self.chart.id,
                'automaticColorIndex': automatic_color_index,
                'individualLookupValuesEnabled': individual_lookup_values_enabled,
                'individualPointColorEnabled': individual_point_color_enabled,
                'individualPointSizeAxisEnabled': individual_point_size_axis_enabled,
                'individualPointSizeEnabled': individual_point_size_enabled,
                'type': render_2d,
                'legend': legend_options if legend_options else None
            },
        )
