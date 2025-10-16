from __future__ import annotations
from typing import Optional

from lightningchart.charts import Chart
from lightningchart.ui.axis import Axis
from lightningchart.series import (
    SeriesWithAddDataPoints,
    SeriesWith2DLines,
    SeriesWith2DPoints,
    SeriesWithAddDataXY,
    SeriesWithIndividualPoint,
    Series,
    PointLineAreaSeries,
    SeriesWithClear,
    SeriesWithDrawOrder,
)
from lightningchart.utils.utils import LegendOptions, build_series_legend_options


class SplineSeries(
    SeriesWithAddDataPoints,
    SeriesWithAddDataXY,
    SeriesWith2DLines,
    SeriesWith2DPoints,
    SeriesWithIndividualPoint,
    PointLineAreaSeries,
    SeriesWithClear,
    SeriesWithDrawOrder,
):
    """Series for visualizing 2D splines."""

    def __init__(
        self,
        chart: Chart,
        resolution: int | float = 20,
        colors: bool = None,
        lookup_values: bool = None,
        ids: bool = None,
        sizes: bool = None,
        rotations: bool = None,
        schema: dict = None,
        strict_mode: bool = None,
        auto_detect_patterns: bool = False,
        allow_data_grouping: bool = None,
        allow_input_modification: bool = None,
        auto_sorting_enabled: bool = None,
        automatic_color_index: int = None,
        includes_nan: bool = None,
        warnings: bool = None,
        axis_x: Axis = None,
        axis_y: Axis = None,
        legend: Optional[LegendOptions] = None,
    ):
        Series.__init__(self, chart)

        if schema:
            processed_schema = {}
            storage_map = {
                'Int8Array': 'Int8Array',
                'Uint8Array': 'Uint8Array', 
                'Int16Array': 'Int16Array',
                'Uint16Array': 'Uint16Array',
                'Int32Array': 'Int32Array',
                'Uint32Array': 'Uint32Array',
                'Uint8ClampedArray': 'Uint8ClampedArray',
                'Float32Array': 'Float32Array',
                'Float64Array': 'Float64Array'
            }
            
            for key, config in schema.items():
                processed_config = {}
                if 'auto' in config:
                    processed_config['auto'] = config['auto']
                if 'pattern' in config:
                    processed_config['pattern'] = config['pattern']
                if 'storage' in config:
                    if config['storage'] in storage_map:
                        processed_config['storage'] = config['storage']
                    else:
                        raise ValueError(f"Invalid storage type: {config['storage']}")
                if 'ensureNoDuplication' in config:
                    processed_config['ensureNoDuplication'] = config['ensureNoDuplication']
                processed_schema[key] = processed_config
            schema = processed_schema

        legend_options = build_series_legend_options(legend)
        if schema is None:
            schema = {'x': {'pattern': 'progressive'}, 'y': {}}
            
        self.instance.send(
            self.id,
            'splineSeries',
            {
                'chart': self.chart.id,
                'resolution': resolution,
                'colors': colors,
                'lookup_values': lookup_values,
                'ids': ids,
                'sizes': sizes,
                'rotations': rotations,
                'schema': schema,
                'strictMode': strict_mode,
                'autoDetectPatterns': auto_detect_patterns,
                'allowDataGrouping': allow_data_grouping,
                'allowInputModification': allow_input_modification,
                'autoSortingEnabled': auto_sorting_enabled,
                'automaticColorIndex': automatic_color_index,
                'includesNaN': includes_nan,
                'warnings': warnings,
                'axisX': axis_x,
                'axisY': axis_y,
                'legend': legend_options if legend_options else None,
            },
        )
