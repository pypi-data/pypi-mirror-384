from __future__ import annotations
from typing import Optional

from lightningchart import conf, Themes
from lightningchart.charts import (
    GeneralMethods,
    TitleMethods,
    ChartWithXYAxis,
    ChartWithSeries,
    BackgroundChartStyle,
)
from lightningchart.instance import Instance
from lightningchart.series.point_series import PointSeries
from lightningchart.series.line_series import LineSeries
from lightningchart.series.point_line_series import PointLineSeries
from lightningchart.series.spline_series import SplineSeries
from lightningchart.series.area_series import AreaSeries
from lightningchart.series.area_range_series import AreaRangeSeries
from lightningchart.series.step_series import StepSeries
from lightningchart.series.heatmap_grid_series import HeatmapGridSeries
from lightningchart.series.heatmap_scrolling_grid_series import (
    HeatmapScrollingGridSeries,
)
from lightningchart.series.box_series import BoxSeries
from lightningchart.series.ellipse_series import EllipseSeries
from lightningchart.series.rectangle_series import RectangleSeries
from lightningchart.series.polygon_series import PolygonSeries
from lightningchart.series.segment_series import SegmentSeries
from lightningchart.series.text_series import TextSeries
from lightningchart.ui.axis import Axis, UserInteractions
from lightningchart.utils.utils import LegendOptions, apply_post_legend_config, build_legend_config



def get_axis_id(x_axis: Axis = None, y_axis: Axis = None):
    x_id = None
    y_id = None
    if x_axis:
        x_id = x_axis.id
    if y_axis:
        y_id = y_axis.id
    return x_id, y_id


class ChartXY(
    GeneralMethods,
    TitleMethods,
    ChartWithXYAxis,
    ChartWithSeries,
    BackgroundChartStyle,
    UserInteractions,
):
    """Chart type for visualizing data between two dimensions, X and Y."""

    def __init__(
        self,
        theme: Themes = Themes.Light,
        theme_scale: float = 1.0,
        title: str = None,
        license: str = None,
        license_information: str = None,
        html_text_rendering: bool = True,
        legend: Optional[LegendOptions] = None,
    ):
        """Create a XY Chart.

        Args:
            theme (Themes): Chart theme (Themes.Light, Themes.DarkGold, etc.).
            theme_scale (float): Scale factor for fonts, ticks, padding (default: 1.0).
            title (str): Chart title.
            license (str): License key.
            html_text_rendering (bool): Sharper text display with performance cost.
            legend (dict): Legend configuration dictionary with the following options:
                visible (bool): Show/hide legend.
                position: Position (LegendPosition.TopRight, RightCenter, etc.).
                title (str): Legend title text.
                title_font (dict): Title font settings
                title_fill_style: Title color/fill style
                orientation: Horizontal or Vertical orientation.
                render_on_top (bool): Render above chart (default: False).
                background_visible (bool): Show legend background.
                background_fill_style (str): Background color ("#ff0000").
                background_stroke_style (dict): Border style {'thickness': 2, 'color': '#000'}.
                padding (int | dict): Padding around legend content.
                margin_inner (int): Space between chart and legend.
                margin_outer (int): Space from legend to chart edge.
                entry_margin (int): Space between legend entries.
                auto_hide_threshold (float): Auto-hide when legend takes >X of chart (0.0-1.0).
                add_entries_automatically (bool): Auto-add series to legend.
                entries (dict): Default styling for all legend entries with options:
                    button_shape (str): 'Arrow', 'Diamond', 'Plus', 'Triangle', 'Circle', 'Square', 'Cross', 'Minus' and 'Star'.
                    button_size (int | dict): Size in pixels or {'x': 20, 'y': 15}.
                    button_fill_style (str): Button color ("#ff0000").
                    button_stroke_style (dict): Button border {'thickness': 1, 'color': '#000'}.
                    button_rotation (float): Button rotation in degrees.
                    text (str): Override default series name.
                    text_font (dict): Font settings {'size': 16, 'family': 'Arial', 'weight': 'bold'}.
                    text_fill_style (str): Text color ("#000000").
                    show (bool): Show/hide this entry.
                    match_style_exactly (bool): Match series style exactly vs simplified.
                    highlight (bool): Whether highlighting on hover is enabled.
                    lut: LUT element for legends (None to disable).
                    lut_length (int): LUT bar length for heatmap legends.
                    lut_thickness (int): LUT bar thickness for heatmap legends.
                    lut_display_proportional_steps (bool): LUT step display mode.
                    lut_step_value_formatter: Callback function for LUT value formatting.

        Returns:
            Reference to ChartXY class.

        Examples:
            Basic chart with simple legend
            >>> chart = lc.ChartXY(
            ...     title='My Chart',
            ...     legend={
            ...         'visible': True,
            ...         'position': 'RightCenter',
            ...         'title': "Data Series"
            ...     }
            ... )

            Styled legend with background and custom entries
            >>> chart = lc.ChartXY(
            ...     title='Styled Chart',
            ...     legend={
            ...         'visible': True,
            ...         'position': 'RightCenter',
            ...         'background_visible': True,
            ...         'background_fill_style': "#e01212",
            ...         'background_stroke_style': {'thickness': 3, 'color': '#003300'},
            ...         'entries': {
            ...             'button_shape': 'Circle',
            ...             'button_size': 20,
            ...             'text_font': {'size': 16},
            ...             'text_fill_style': "#000080"
            ...         }
            ...     }
            ... )

            Custom positioned legend
            >>> chart = lc.ChartXY(
            ...     title='Custom Legend',
            ...     legend={
            ...         'position': 'RightCenter',
            ...         'orientation': 'Horizontal',
            ...         'render_on_top': True,
            ...         'padding': 15,
            ...         'margin_inner': 10
            ...     }
            ... )
        """
        instance = Instance()
        ChartWithSeries.__init__(self, instance)     
        
        legend_config = build_legend_config(legend)

        self.instance.send(
            self.id,
            'chartXY',
            {
                'theme': theme.value,
                'scaleTheme': theme_scale,
                'license': license or conf.LICENSE_KEY,
                'licenseInformation': license_information or conf.LICENSE_INFORMATION,
                'htmlTextRendering': html_text_rendering,
                'title': title,
                'legendConfig': legend_config,
            },
        )
        ChartWithXYAxis.__init__(self)        
        apply_post_legend_config(self, legend)      

    def set_title_position(self, position: str = 'center-top'):
        """Set position of XY Chart title.

        Args:
            position (str): "right-top" | "left-top" | "right-bottom" | "left-bottom" | "center-top" |
                "center-bottom" | "series-center-top" | "series-right-top" | "series-left-top" |
                "series-center-bottom" | "series-right-bottom" | "series-left-bottom"

        Returns:
            The instance of the class for fluent interface.
        """
        title_positions = (
            'right-top',
            'left-top',
            'right-bottom',
            'left-bottom',
            'center-top',
            'center-bottom',
            'series-center-top',
            'series-right-top',
            'series-left-top',
            'series-center-bottom',
            'series-right-bottom',
            'series-left-bottom',
        )
        if position not in title_positions:
            raise ValueError(f"Expected position to be one of {title_positions}, but got '{position}'.")

        self.instance.send(self.id, 'setTitlePosition', {'position': position})
        return self

    def add_x_axis(
        self,
        stack_index: int = None,
        parallel_index: int = None,
        opposite: bool = False,
        axis_type: str = None,
        base: int = None,
    ) -> Axis:
        """Add a new X Axis to the Chart.

        Args:
            stack_index (int): Axis index in same plane as the Axis direction.
            parallel_index (int): Axis index in direction parallel to axis.
            opposite (bool): Specify Axis position in chart. Default is bottom for X Axes, and left for Y Axes.
                Setting to true will result in the opposite side (top for X Axes, right for Y Axes).
            axis_type (str): "linear" | "linear-highPrecision" | "logarithmic"
            base (int): Specification of Logarithmic Base number (e.g. 10, 2, natural log). Defaults to 10 if omitted.
        Returns:
            Reference to Axis class.
        """
        return Axis(self, 'x', stack_index, parallel_index, opposite, axis_type, base)

    def add_y_axis(
        self,
        stack_index: int = None,
        parallel_index: int = None,
        opposite: bool = None,
        axis_type: str = None,
        base: int = None,
    ) -> Axis:
        """Add a new Y Axis to the Chart.

        Args:
            stack_index (int): Axis index in same plane as the Axis direction.
            parallel_index (int): Axis index in direction parallel to axis.
            opposite (bool): Specify Axis position in chart. Default is bottom for X Axes, and left for Y Axes.
                Setting to true will result in the opposite side (top for X Axes, right for Y Axes).
            axis_type (str): "linear" | "linear-highPrecision" | "logarithmic"
            base (int): Specification of Logarithmic Base number (e.g. 10, 2, natural log). Defaults to 10 if omitted.
        Returns:
            Reference to Axis class.
        """
        return Axis(self, 'y', stack_index, parallel_index, opposite, axis_type, base)

    def set_cursor_mode(self, mode: str):
        """Set chart Cursor behavior.

        Args:
            mode (str): "disabled" | "show-all" | "show-all-interpolated" | "show-nearest" |
                "show-nearest-interpolated" | "show-pointed" | "show-pointed-interpolated"

        Returns:
            The instance of the class for fluent interface.
        """
        cursor_modes = (
            'disabled',
            'show-all',
            'show-all-interpolated',
            'show-nearest',
            'show-nearest-interpolated',
            'show-pointed',
            'show-pointed-interpolated',
        )
        if mode not in cursor_modes:
            raise ValueError(f"Expected mode to be one of {cursor_modes}, but got '{mode}'.")

        self.instance.send(self.id, 'setCursorMode', {'mode': mode})
        return self

    def add_point_series(
        self,
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
        x_axis: Axis = None,
        y_axis: Axis = None,
        legend: Optional[LegendOptions] = None,
    ) -> PointSeries:
        """Method for adding a new PointSeries to the chart. This series type visualizes a list of Points
        (pair of X and Y coordinates), with configurable markers over each coordinate.

        Args:
            schema (dict): Define data properties and their configurations:
            - auto: bool or {'start': int, 'step': int} for auto-indexing
            - pattern: 'progressive' | 'regressive' | None
            - storage: TypedArray constructor name ('Float32Array', 'Int32Array', etc.)
            - ensureNoDuplication: bool
            strict_mode (bool): Enable strict schema validation and configuration requirements.
            auto_detect_patterns (bool): Enable/disable automatic pattern detection.
            allow_input_modification (bool): Allow DataSetXY to modify input arrays.
            warnings (bool): Enable/disable data set warnings.
            colors (bool): If true, the DataSetXY should allocate for Color property to be included for every sample.
                This can be used to adjust data visualization to use per sample colors. Defaults to false.
            lookup_values (bool): Flag that can be used to enable data points value property on top
                of x and y. Disabled by default.
            ids (bool): If true, user supplied ID property is allocated to be included for every sample.
                Defaults to false.
            sizes (bool): If true, user supplied individual point size properties are allocated. This means that points
                can have individual sizes,rather than each point having same size. Defaults to false.
            rotations (bool): If true, user supplied individual point rotation properties are allocated.
                This means that points can have individual rotations, rather than each point having same rotation.
                Defaults to false.
            auto_sorting_enabled (bool): Controls whether automatic sorting of data according to active data_pattern is
                enabled or disabled. If data_pattern is any kind of progressive pattern, then input data can be
                automatically sorted to remain in that progressive order. This can be useful when data is arriving in
                the application asynchronously, and it can't be guaranteed that it arrives in the correct order.
                Please note that auto sorting only sorts by BATCH, not by SAMPLE. For example, if you supply batches of
                for example 10 samples at a time, auto sorting is capable of identifying the scenario where a newer
                batch arrives before one that should be displayed first. However, auto sorting is not capable of sorting
                any samples that are in wrong order within a BATCH. This is intentional due to effects on performance,
                and since its not a realistic need scenario. Defaults to true.
            allow_data_grouping: Optional flag that can be used to disable automatic grouping of progressive data
                that is packed very tightly together.
            automatic_color_index: Optional index to use for automatic coloring of series.
            includes_nan: Optional flag that can be used to inform that data set will not include NaN values.
                By default, it is assumed that the data provided might include NaN values.
                This results in extra processing to properly handle NaN values.
            x_axis (Axis): Optional non-default X Axis to attach series to.
            y_axis (Axis): Optional non-default Y Axis to attach series to.
            x_axis (Axis): Deprecated, use axis_x.
            y_axis (Axis): Deprecated, use axis_y.

            legend (dict): Legend configuration dictionary with the following options:
                show (bool): Whether to show this series in legend (default: True).
                text (str): Custom text for legend entry.
                button_shape (str): Button shape ('Circle', 'Square', 'Triangle', 'Diamond', 
                    'Plus', 'Cross', 'Minus', 'Star', 'Arrow').
                button_size (int | dict): Button size in pixels or {'x': width, 'y': height}.
                button_fill_style (str): Button color ("#ff0000").
                button_stroke_style (dict): Button border {'thickness': 2, 'color': '#000'}.
                button_rotation (float): Button rotation in degrees.
                text_font (dict): Text font settings {'size': 12, 'family': 'Arial', 'weight': 'bold'}.
                text_fill_style (str): Text color ("#000000").
                match_style_exactly (bool): Whether button should match series style exactly.
                highlight (bool): Whether highlighting on hover is enabled.
                lut: LUT element for legends (None to disable).
                lut_length (int): LUT bar length in pixels.
                lut_thickness (int): LUT bar thickness in pixels.
                lut_display_proportional_steps (bool): LUT step display mode.
                lut_step_value_formatter: Callback function for LUT value formatting.

        Returns:
            Reference to Point Series class.
        
        Examples:
            Hidden from legend
            >>> series = chart.add_point_series(show=False)

            Custom series
            >>> series = chart.add_point_series(
            ...     sizes=True,
            ...     rotations=True,
            ...     lookup_values=True,
            ...     colors=True
            ... ).set_individual_point_color_enabled(True)

            Custom auto-indexing with start/step
            >>> series = chart.add_point_series(
            ...     schema={
            ...         'time': {'auto': {'start': 1000, 'step': 5}},
            ...         'temperature': {}
            ...     }
            ... )
            ... series.set_data_mapping({'x': 'time', 'y': 'temperature'})
            ... series.append_samples(samples={'temperature': y_values})

            Progressive data pattern
            >>> series = chart.add_point_series(
            ...     schema={
            ...         'timestamps': {'pattern': 'progressive'},
            ...         'values': {'pattern': None}
            ...     }
            ... )
            ... series.set_data_mapping({'x': 'timestamps', 'y': 'values'})
            ... series.append_samples(samples={'timestamps': x_values, 'values': y_values})
            
            Custom legend appearance
            >>> series = chart.add_point_series(
            ...     legend=
            ...     {
            ...         'show': True,
            ...         'button_shape': 'Triangle',
            ...         'text': 'Series A',
            ...         'text_font': {'size': 20, 'style': 'bold'},
            ...         'text_fill_style': '#0000FF',
            ...     }
            ... )
        """
        axis_x_id, axis_y_id = get_axis_id(axis_x or x_axis, axis_y or y_axis)
        series = PointSeries(
            chart=self,
            colors=colors,
            lookup_values=lookup_values,
            ids=ids,
            sizes=sizes,
            rotations=rotations,            
            schema=schema,
            strict_mode=strict_mode,
            auto_detect_patterns=auto_detect_patterns,
            allow_input_modification=allow_input_modification,
            warnings=warnings,
            auto_sorting_enabled=auto_sorting_enabled,
            allow_data_grouping=allow_data_grouping,
            automatic_color_index=automatic_color_index,
            includes_nan=includes_nan,
            axis_x=axis_x_id,
            axis_y=axis_y_id,
            legend=legend,
        )
        self.series_list.append(series)
        return series

    def add_line_series(
        self,
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
        x_axis: Axis = None,
        y_axis: Axis = None,
        legend: Optional[LegendOptions] = None,
    ) -> LineSeries:
        """Method for adding a new LineSeries to the chart. This series type visualizes a list of Points
        (pair of X and Y coordinates), with a continuous stroke.

        Args:
            schema (dict): Define data properties and their configurations:
            - auto: bool or {'start': int, 'step': int} for auto-indexing
            - pattern: 'progressive' | 'regressive' | None
            - storage: TypedArray constructor name ('Float32Array', 'Int32Array', etc.)
            - ensureNoDuplication: bool
            strict_mode (bool): Enable strict schema validation and configuration requirements.
            auto_detect_patterns (bool): Enable/disable automatic pattern detection.
            allow_input_modification (bool): Allow DataSetXY to modify input arrays.
            warnings (bool): Enable/disable data set warnings.
            colors (bool): If true, the DataSetXY should allocate for Color property to be included for every sample.
                This can be used to adjust data visualization to use per sample colors. Defaults to false.
            lookup_values (bool): Flag that can be used to enable data points value property on top
                of x and y. Disabled by default.
            ids (bool): If true, user supplied ID property is allocated to be included for every sample.
                Defaults to false.
            sizes (bool): If true, user supplied individual point size properties are allocated. This means that points
                can have individual sizes,rather than each point having same size. Defaults to false.
            rotations (bool): If true, user supplied individual point rotation properties are allocated.
                This means that points can have individual rotations, rather than each point having same rotation.
                Defaults to false.
            auto_sorting_enabled (bool): Controls whether automatic sorting of data according to active data_pattern is
                enabled or disabled. If data_pattern is any kind of progressive pattern, then input data can be
                automatically sorted to remain in that progressive order. This can be useful when data is arriving in
                the application asynchronously, and it can't be guaranteed that it arrives in the correct order.
                Please note that auto sorting only sorts by BATCH, not by SAMPLE. For example, if you supply batches of
                for example 10 samples at a time, auto sorting is capable of identifying the scenario where a newer
                batch arrives before one that should be displayed first. However, auto sorting is not capable of sorting
                any samples that are in wrong order within a BATCH. This is intentional due to effects on performance,
                and since its not a realistic need scenario. Defaults to true.
            allow_data_grouping: Optional flag that can be used to disable automatic grouping of progressive data
                that is packed very tightly together.
            automatic_color_index: Optional index to use for automatic coloring of series.
            includes_nan: Optional flag that can be used to inform that data set will not include NaN values.
                By default, it is assumed that the data provided might include NaN values.
                This results in extra processing to properly handle NaN values.
            x_axis (Axis): Optional non-default X Axis to attach series to.
            y_axis (Axis): Optional non-default Y Axis to attach series to.
            x_axis (Axis): Deprecated, use axis_x.
            y_axis (Axis): Deprecated, use axis_y.

            legend (dict): Legend configuration dictionary with the following options:
                show (bool): Whether to show this series in legend (default: True).
                text (str): Custom text for legend entry.
                button_shape (str): Button shape ('Circle', 'Square', 'Triangle', 'Diamond', 
                    'Plus', 'Cross', 'Minus', 'Star', 'Arrow').
                button_size (int | dict): Button size in pixels or {'x': width, 'y': height}.
                button_fill_style (str): Button color ("#ff0000").
                button_stroke_style (dict): Button border {'thickness': 2, 'color': '#000'}.
                button_rotation (float): Button rotation in degrees.
                text_font (dict): Text font settings {'size': 12, 'family': 'Arial', 'weight': 'bold'}.
                text_fill_style (str): Text color ("#000000").
                match_style_exactly (bool): Whether button should match series style exactly.
                highlight (bool): Whether highlighting on hover is enabled.
                lut: LUT element for legends (None to disable).
                lut_length (int): LUT bar length in pixels.
                lut_thickness (int): LUT bar thickness in pixels.
                lut_display_proportional_steps (bool): LUT step display mode.
                lut_step_value_formatter: Callback function for LUT value formatting.
        Returns:
            Reference to Line Series class.

        Examples:
        Basic series (shows in legend by default)
            >>> series = chart.add_line_series()

        Custom series
            >>> series = chart.add_line_series(
            ...     sizes=True,
            ...     rotations=True,
            ...     lookup_values=True,
            ...     colors=True
            ... )

        Custom auto-indexing with start/step
            >>> series = chart.add_line_series(
            ...     schema={
            ...         'time': {'auto': {'start': 1000, 'step': 5}},
            ...         'temperature': {}
            ...     }
            ... )
            ... series.set_data_mapping({'x': 'time', 'y': 'temperature'})
            ... series.append_samples(samples={'temperature': y_values})

        Progressive data pattern
            >>> series = chart.add_line_series(
            ...     schema={
            ...         'timestamps': {'pattern': 'progressive'},
            ...         'values': {'pattern': None}
            ...     }
            ... )
            ... series.set_data_mapping({'x': 'timestamps', 'y': 'values'})
            ... series.append_samples(samples={'timestamps': x_values, 'values': y_values})
        
        Hidden from legend
            >>> series = chart.add_line_series(show=False)
        
        Custom legend appearance
            >>> series = chart.add_line_series(
            ...     legend=
            ...     {
            ...         'show': True,
            ...         'button_shape': 'Triangle',
            ...         'text': 'Series A',
            ...         'text_font': {'size': 20, 'style': 'bold'},
            ...         'text_fill_style': '#0000FF',
            ...     }
            ... )
        """
        axis_x_id, axis_y_id = get_axis_id(axis_x or x_axis, axis_y or y_axis)
        series = LineSeries(
            chart=self,
            colors=colors,
            lookup_values=lookup_values,
            ids=ids,
            sizes=sizes,
            rotations=rotations,            
            schema=schema,
            strict_mode=strict_mode,
            auto_detect_patterns=auto_detect_patterns,
            allow_input_modification=allow_input_modification,
            warnings=warnings,
            auto_sorting_enabled=auto_sorting_enabled,
            allow_data_grouping=allow_data_grouping,
            automatic_color_index=automatic_color_index,
            includes_nan=includes_nan,
            axis_x=axis_x_id,
            axis_y=axis_y_id,
            legend=legend,
        )
        self.series_list.append(series)
        return series

    def add_point_line_series(
        self,
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
        x_axis: Axis = None,
        y_axis: Axis = None,
        legend: Optional[LegendOptions] = None,
    ) -> PointLineSeries:
        """Method for adding a new PointLineSeries to the chart. This series type visualizes a list of Points
        (pair of X and Y coordinates), with a continuous stroke and configurable markers over each coordinate.

        Args:
            schema (dict): Define data properties and their configurations:
            - auto: bool or {'start': int, 'step': int} for auto-indexing
            - pattern: 'progressive' | 'regressive' | None
            - storage: TypedArray constructor name ('Float32Array', 'Int32Array', etc.)
            - ensureNoDuplication: bool
            strict_mode (bool): Enable strict schema validation and configuration requirements.
            auto_detect_patterns (bool): Enable/disable automatic pattern detection.
            allow_input_modification (bool): Allow DataSetXY to modify input arrays.
            warnings (bool): Enable/disable data set warnings.
            colors (bool): If true, the DataSetXY should allocate for Color property to be included for every sample.
                This can be used to adjust data visualization to use per sample colors. Defaults to false.
            lookup_values (bool): Flag that can be used to enable data points value property on top
                of x and y. Disabled by default.
            ids (bool): If true, user supplied ID property is allocated to be included for every sample.
                Defaults to false.
            sizes (bool): If true, user supplied individual point size properties are allocated. This means that points
                can have individual sizes,rather than each point having same size. Defaults to false.
            rotations (bool): If true, user supplied individual point rotation properties are allocated.
                This means that points can have individual rotations, rather than each point having same rotation.
                Defaults to false.
            auto_sorting_enabled (bool): Controls whether automatic sorting of data according to active data_pattern is
                enabled or disabled. If data_pattern is any kind of progressive pattern, then input data can be
                automatically sorted to remain in that progressive order. This can be useful when data is arriving in
                the application asynchronously, and it can't be guaranteed that it arrives in the correct order.
                Please note that auto sorting only sorts by BATCH, not by SAMPLE. For example, if you supply batches of
                for example 10 samples at a time, auto sorting is capable of identifying the scenario where a newer
                batch arrives before one that should be displayed first. However, auto sorting is not capable of sorting
                any samples that are in wrong order within a BATCH. This is intentional due to effects on performance,
                and since its not a realistic need scenario. Defaults to true.
            allow_data_grouping: Optional flag that can be used to disable automatic grouping of progressive data
                that is packed very tightly together.
            automatic_color_index: Optional index to use for automatic coloring of series.
            includes_nan: Optional flag that can be used to inform that data set will not include NaN values.
                By default, it is assumed that the data provided might include NaN values.
                This results in extra processing to properly handle NaN values.
            x_axis (Axis): Optional non-default X Axis to attach series to.
            y_axis (Axis): Optional non-default Y Axis to attach series to.
            x_axis (Axis): Deprecated, use axis_x.
            y_axis (Axis): Deprecated, use axis_y.

        
        legend (dict): Legend configuration dictionary with the following options:
                show (bool): Whether to show this series in legend (default: True).
                text (str): Custom text for legend entry.
                button_shape (str): Button shape ('Circle', 'Square', 'Triangle', 'Diamond', 
                    'Plus', 'Cross', 'Minus', 'Star', 'Arrow').
                button_size (int | dict): Button size in pixels or {'x': width, 'y': height}.
                button_fill_style (str): Button color ("#ff0000").
                button_stroke_style (dict): Button border {'thickness': 2, 'color': '#000'}.
                button_rotation (float): Button rotation in degrees.
                text_font (dict): Text font settings {'size': 12, 'family': 'Arial', 'weight': 'bold'}.
                text_fill_style (str): Text color ("#000000").
                match_style_exactly (bool): Whether button should match series style exactly.
                highlight (bool): Whether highlighting on hover is enabled.
                lut: LUT element for legends (None to disable).
                lut_length (int): LUT bar length in pixels.
                lut_thickness (int): LUT bar thickness in pixels.
                lut_display_proportional_steps (bool): LUT step display mode.
                lut_step_value_formatter: Callback function for LUT value formatting.

        Returns:
            Reference to Point Line Series class.

        Examples:
        Basic series (shows in legend by default)
            >>> series = chart.add_point_line_series()

        Custom series
            >>> series = chart.add_point_line_series(
            ...     sizes=True,
            ...     rotations=True,
            ...     lookup_values=True,
            ...     colors=True
            ... )

        Custom auto-indexing with start/step
            >>> series = chart.add_point_line_series(
            ...     schema={
            ...         'time': {'auto': {'start': 1000, 'step': 5}},
            ...         'temperature': {}
            ...     }
            ... )
            ... series.set_data_mapping({'x': 'time', 'y': 'temperature'})
            ... series.append_samples(samples={'temperature': y_values})

        Progressive data pattern
            >>> series = chart.add_point_line_series(
            ...     schema={
            ...         'timestamps': {'pattern': 'progressive'},
            ...         'values': {'pattern': None}
            ...     }
            ... )
            ... series.set_data_mapping({'x': 'timestamps', 'y': 'values'})
            ... series.append_samples(samples={'timestamps': x_values, 'values': y_values})

        Custom series
            >>> series = chart.add_line_series(
            ...     legend=
            ...     {
            ...         'show': True,
            ...         'button_shape': 'Triangle',
            ...         'text': 'Series A',
            ...         'text_font': {'size': 20, 'style': 'bold'},
            ...         'text_fill_style': '#0000FF',
            ...     }
            ... )
        """
        axis_x_id, axis_y_id = get_axis_id(axis_x or x_axis, axis_y or y_axis)
        series = PointLineSeries(
            chart=self,
            colors=colors,
            lookup_values=lookup_values,
            ids=ids,
            sizes=sizes,
            rotations=rotations,            
            schema=schema,
            strict_mode=strict_mode,
            auto_detect_patterns=auto_detect_patterns,
            allow_input_modification=allow_input_modification,
            warnings=warnings,
            auto_sorting_enabled=auto_sorting_enabled,
            allow_data_grouping=allow_data_grouping,
            automatic_color_index=automatic_color_index,
            includes_nan=includes_nan,
            axis_x=axis_x_id,
            axis_y=axis_y_id,
            legend=legend,
        )
        self.series_list.append(series)
        return series

    def add_spline_series(
        self,
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
        x_axis: Axis = None,
        y_axis: Axis = None,
        legend: Optional[LegendOptions] = None,
    ) -> SplineSeries:
        """Method for adding a new SplineSeries to the chart. This series type visualizes a list of Points
        (pair of X and Y coordinates), with a smoothed curve stroke + point markers over each data point.

        Args:
            resolution (int | float): Number of interpolated coordinates between two real data points.
            schema (dict): Define data properties and their configurations:
            - auto: bool or {'start': int, 'step': int} for auto-indexing
            - pattern: 'progressive' | 'regressive' | None
            - storage: TypedArray constructor name ('Float32Array', 'Int32Array', etc.)
            - ensureNoDuplication: bool
            strict_mode (bool): Enable strict schema validation and configuration requirements.
            auto_detect_patterns (bool): Enable/disable automatic pattern detection.
            allow_input_modification (bool): Allow DataSetXY to modify input arrays.
            warnings (bool): Enable/disable data set warnings.
            colors (bool): If true, the DataSetXY should allocate for Color property to be included for every sample.
                This can be used to adjust data visualization to use per sample colors. Defaults to false.
            lookup_values (bool): Flag that can be used to enable data points value property on top
                of x and y. Disabled by default.
            ids (bool): If true, user supplied ID property is allocated to be included for every sample.
                Defaults to false.
            sizes (bool): If true, user supplied individual point size properties are allocated. This means that points
                can have individual sizes,rather than each point having same size. Defaults to false.
            rotations (bool): If true, user supplied individual point rotation properties are allocated.
                This means that points can have individual rotations, rather than each point having same rotation.
                Defaults to false.
            auto_sorting_enabled (bool): Controls whether automatic sorting of data according to active data_pattern is
                enabled or disabled. If data_pattern is any kind of progressive pattern, then input data can be
                automatically sorted to remain in that progressive order. This can be useful when data is arriving in
                the application asynchronously, and it can't be guaranteed that it arrives in the correct order.
                Please note that auto sorting only sorts by BATCH, not by SAMPLE. For example, if you supply batches of
                for example 10 samples at a time, auto sorting is capable of identifying the scenario where a newer
                batch arrives before one that should be displayed first. However, auto sorting is not capable of sorting
                any samples that are in wrong order within a BATCH. This is intentional due to effects on performance,
                and since its not a realistic need scenario. Defaults to true.
            allow_data_grouping: Optional flag that can be used to disable automatic grouping of progressive data
                that is packed very tightly together.
            automatic_color_index: Optional index to use for automatic coloring of series.
            includes_nan: Optional flag that can be used to inform that data set will not include NaN values.
                By default, it is assumed that the data provided might include NaN values.
                This results in extra processing to properly handle NaN values.
            x_axis (Axis): Optional non-default X Axis to attach series to.
            y_axis (Axis): Optional non-default Y Axis to attach series to.
            x_axis (Axis): Deprecated, use axis_x.
            y_axis (Axis): Deprecated, use axis_y.

            legend (dict): Legend configuration dictionary with the following options:
                show (bool): Whether to show this series in legend (default: True).
                text (str): Custom text for legend entry.
                button_shape (str): Button shape ('Circle', 'Square', 'Triangle', 'Diamond', 
                    'Plus', 'Cross', 'Minus', 'Star', 'Arrow').
                button_size (int | dict): Button size in pixels or {'x': width, 'y': height}.
                button_fill_style (str): Button color ("#ff0000").
                button_stroke_style (dict): Button border {'thickness': 2, 'color': '#000'}.
                button_rotation (float): Button rotation in degrees.
                text_font (dict): Text font settings {'size': 12, 'family': 'Arial', 'weight': 'bold'}.
                text_fill_style (str): Text color ("#000000").
                match_style_exactly (bool): Whether button should match series style exactly.
                highlight (bool): Whether highlighting on hover is enabled.
                lut: LUT element for legends (None to disable).
                lut_length (int): LUT bar length in pixels.
                lut_thickness (int): LUT bar thickness in pixels.
                lut_display_proportional_steps (bool): LUT step display mode.
                lut_step_value_formatter: Callback function for LUT value formatting.

        Returns:
            Reference to Spline Series class.
        
        Examples:
        Basic series (shows in legend by default)
            >>> series = chart.add_spline_series()
        
        Custom series
            >>> series = chart.add_spline_series(
            ...     sizes=True,
            ...     rotations=True,
            ...     lookup_values=True,
            ...     colors=True
            ... )

        Custom auto-indexing with start/step
            >>> series = chart.add_spline_series(
            ...     schema={
            ...         'time': {'auto': {'start': 1000, 'step': 5}},
            ...         'temperature': {}
            ...     }
            ... )
            ... series.set_data_mapping({'x': 'time', 'y': 'temperature'})
            ... series.append_samples(samples={'temperature': y_values})

        Progressive data pattern
            >>> series = chart.add_spline_series(
            ...     schema={
            ...         'timestamps': {'pattern': 'progressive'},
            ...         'values': {'pattern': None}
            ...     }
            ... )
            ... series.set_data_mapping({'x': 'timestamps', 'y': 'values'})
            ... series.append_samples(samples={'timestamps': x_values, 'values': y_values})
        
        Hidden from legend
            >>> series = chart.add_spline_series(show=False)
        
        Custom legend appearance
            >>> series = chart.add_spline_series(
            ...     legend=
            ...     {
            ...         'show': True,
            ...         'button_shape': 'Triangle',
            ...         'text': 'Series A',
            ...         'text_font': {'size': 20, 'style': 'bold'},
            ...         'text_fill_style': '#0000FF',
            ...     }
            ... )
        """
        axis_x_id, axis_y_id = get_axis_id(axis_x or x_axis, axis_y or y_axis)
        series = SplineSeries(
            chart=self,
            resolution=resolution,
            colors=colors,
            lookup_values=lookup_values,
            ids=ids,
            sizes=sizes,
            rotations=rotations,            
            schema=schema,
            strict_mode=strict_mode,
            auto_detect_patterns=auto_detect_patterns,
            allow_input_modification=allow_input_modification,
            warnings=warnings,
            auto_sorting_enabled=auto_sorting_enabled,
            allow_data_grouping=allow_data_grouping,
            automatic_color_index=automatic_color_index,
            includes_nan=includes_nan,
            axis_x=axis_x_id,
            axis_y=axis_y_id,
            legend=legend,
        )
        self.series_list.append(series)
        return series

    def add_step_series(
        self,
        step_mode: str = 'middle',
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
        x_axis: Axis = None,
        y_axis: Axis = None,
        legend: Optional[LegendOptions] = None,
    ) -> StepSeries:
        """Method for adding a new StepSeries to the chart. This series type visualizes a list of Points
        (pair of X and Y coordinates), with a stepped stroke + point markers over each data point.

        Args:
            step_mode (str): "after" | "before" | "middle"
            schema (dict): Define data properties and their configurations:
            - auto: bool or {'start': int, 'step': int} for auto-indexing
            - pattern: 'progressive' | 'regressive' | None
            - storage: TypedArray constructor name ('Float32Array', 'Int32Array', etc.)
            - ensureNoDuplication: bool
            strict_mode (bool): Enable strict schema validation and configuration requirements.
            auto_detect_patterns (bool): Enable/disable automatic pattern detection.
            allow_input_modification (bool): Allow DataSetXY to modify input arrays.
            warnings (bool): Enable/disable data set warnings.
            colors (bool): If true, the DataSetXY should allocate for Color property to be included for every sample.
                This can be used to adjust data visualization to use per sample colors. Defaults to false.
            lookup_values (bool): Flag that can be used to enable data points value property on top
                of x and y. Disabled by default.
            ids (bool): If true, user supplied ID property is allocated to be included for every sample.
                Defaults to false.
            sizes (bool): If true, user supplied individual point size properties are allocated. This means that points
                can have individual sizes,rather than each point having same size. Defaults to false.
            rotations (bool): If true, user supplied individual point rotation properties are allocated.
                This means that points can have individual rotations, rather than each point having same rotation.
                Defaults to false.
            auto_sorting_enabled (bool): Controls whether automatic sorting of data according to active data_pattern is
                enabled or disabled. If data_pattern is any kind of progressive pattern, then input data can be
                automatically sorted to remain in that progressive order. This can be useful when data is arriving in
                the application asynchronously, and it can't be guaranteed that it arrives in the correct order.
                Please note that auto sorting only sorts by BATCH, not by SAMPLE. For example, if you supply batches of
                for example 10 samples at a time, auto sorting is capable of identifying the scenario where a newer
                batch arrives before one that should be displayed first. However, auto sorting is not capable of sorting
                any samples that are in wrong order within a BATCH. This is intentional due to effects on performance,
                and since its not a realistic need scenario. Defaults to true.
            allow_data_grouping: Optional flag that can be used to disable automatic grouping of progressive data
                that is packed very tightly together.
            automatic_color_index: Optional index to use for automatic coloring of series.
            includes_nan: Optional flag that can be used to inform that data set will not include NaN values.
                By default, it is assumed that the data provided might include NaN values.
                This results in extra processing to properly handle NaN values.
            x_axis (Axis): Optional non-default X Axis to attach series to.
            y_axis (Axis): Optional non-default Y Axis to attach series to.
            x_axis (Axis): Deprecated, use axis_x.
            y_axis (Axis): Deprecated, use axis_y.

            legend (dict): Legend configuration dictionary with the following options:
                show (bool): Whether to show this series in legend (default: True).
                text (str): Custom text for legend entry.
                button_shape (str): Button shape ('Circle', 'Square', 'Triangle', 'Diamond', 
                    'Plus', 'Cross', 'Minus', 'Star', 'Arrow').
                button_size (int | dict): Button size in pixels or {'x': width, 'y': height}.
                button_fill_style (str): Button color ("#ff0000").
                button_stroke_style (dict): Button border {'thickness': 2, 'color': '#000'}.
                button_rotation (float): Button rotation in degrees.
                text_font (dict): Text font settings {'size': 12, 'family': 'Arial', 'weight': 'bold'}.
                text_fill_style (str): Text color ("#000000").
                match_style_exactly (bool): Whether button should match series style exactly.
                highlight (bool): Whether highlighting on hover is enabled.
                lut: LUT element for legends (None to disable).
                lut_length (int): LUT bar length in pixels.
                lut_thickness (int): LUT bar thickness in pixels.
                lut_display_proportional_steps (bool): LUT step display mode.
                lut_step_value_formatter: Callback function for LUT value formatting.

        Returns:
            Reference to Step Series class.

        Examples:
        Basic series (shows in legend by default)
            >>> series = chart.add_step_series()

        Custom series
            >>> series = chart.add_step_series(
            ...     sizes=True,
            ...     rotations=True,
            ...     lookup_values=True,
            ...     colors=True
            ... )

        Custom auto-indexing with start/step
            >>> series = chart.add_step_series(
            ...     schema={
            ...         'time': {'auto': {'start': 1000, 'step': 5}},
            ...         'temperature': {}
            ...     }
            ... )
            ... series.set_data_mapping({'x': 'time', 'y': 'temperature'})
            ... series.append_samples(samples={'temperature': y_values})

        Progressive data pattern
            >>> series = chart.add_step_series(
            ...     schema={
            ...         'timestamps': {'pattern': 'progressive'},
            ...         'values': {'pattern': None}
            ...     }
            ... )
            ... series.set_data_mapping({'x': 'timestamps', 'y': 'values'})
            ... series.append_samples(samples={'timestamps': x_values, 'values': y_values})
        
        Hidden from legend
            >>> series = chart.add_step_series(show=False)
        
        Custom legend appearance
            >>> series = chart.add_step_series(
            ...     legend=
            ...     {
            ...         'show': True,
            ...         'button_shape': 'Triangle',
            ...         'text': 'Series A',
            ...         'text_font': {'size': 20, 'style': 'bold'},
            ...         'text_fill_style': '#0000FF',
            ...     }
            ... )
        """
        axis_x_id, axis_y_id = get_axis_id(axis_x or x_axis, axis_y or y_axis)
        series = StepSeries(
            chart=self,
            step_mode=step_mode,
            colors=colors,
            lookup_values=lookup_values,
            ids=ids,
            sizes=sizes,
            rotations=rotations,            
            schema=schema,
            strict_mode=strict_mode,
            auto_detect_patterns=auto_detect_patterns,
            allow_input_modification=allow_input_modification,
            warnings=warnings,
            auto_sorting_enabled=auto_sorting_enabled,
            allow_data_grouping=allow_data_grouping,
            automatic_color_index=automatic_color_index,
            includes_nan=includes_nan,
            axis_x=axis_x_id,
            axis_y=axis_y_id,
            legend=legend,
        )
        self.series_list.append(series)
        return series

    def add_area_series(
        self,
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
        x_axis: Axis = None,
        y_axis: Axis = None,
        legend: Optional[LegendOptions] = None,
    ) -> AreaSeries:
        """Method for adding a new AreaSeries to the chart. This series type is used for visualizing area from
        user-supplied curve data.

        Args:
            schema (dict): Define data properties and their configurations:
            - auto: bool or {'start': int, 'step': int} for auto-indexing
            - pattern: 'progressive' | 'regressive' | None
            - storage: TypedArray constructor name ('Float32Array', 'Int32Array', etc.)
            - ensureNoDuplication: bool
            strict_mode (bool): Enable strict schema validation and configuration requirements.
            auto_detect_patterns (bool): Enable/disable automatic pattern detection.
            allow_input_modification (bool): Allow DataSetXY to modify input arrays.
            warnings (bool): Enable/disable data set warnings.
            colors (bool): If true, the DataSetXY should allocate for Color property to be included for every sample.
                This can be used to adjust data visualization to use per sample colors. Defaults to false.
            lookup_values (bool): Flag that can be used to enable data points value property on top
                of x and y. Disabled by default.
            ids (bool): If true, user supplied ID property is allocated to be included for every sample.
                Defaults to false.
            sizes (bool): If true, user supplied individual point size properties are allocated. This means that points
                can have individual sizes,rather than each point having same size. Defaults to false.
            rotations (bool): If true, user supplied individual point rotation properties are allocated.
                This means that points can have individual rotations, rather than each point having same rotation.
                Defaults to false.
            auto_sorting_enabled (bool): Controls whether automatic sorting of data according to active data_pattern is
                enabled or disabled. If data_pattern is any kind of progressive pattern, then input data can be
                automatically sorted to remain in that progressive order. This can be useful when data is arriving in
                the application asynchronously, and it can't be guaranteed that it arrives in the correct order.
                Please note that auto sorting only sorts by BATCH, not by SAMPLE. For example, if you supply batches of
                for example 10 samples at a time, auto sorting is capable of identifying the scenario where a newer
                batch arrives before one that should be displayed first. However, auto sorting is not capable of sorting
                any samples that are in wrong order within a BATCH. This is intentional due to effects on performance,
                and since its not a realistic need scenario. Defaults to true.
            allow_data_grouping: Optional flag that can be used to disable automatic grouping of progressive data
                that is packed very tightly together.
            automatic_color_index: Optional index to use for automatic coloring of series.
            includes_nan: Optional flag that can be used to inform that data set will not include NaN values.
                By default, it is assumed that the data provided might include NaN values.
                This results in extra processing to properly handle NaN values.
            x_axis (Axis): Optional non-default X Axis to attach series to.
            y_axis (Axis): Optional non-default Y Axis to attach series to.
            x_axis (Axis): Deprecated, use axis_x.
            y_axis (Axis): Deprecated, use axis_y.

           legend (dict): Legend configuration dictionary with the following options:
                show (bool): Whether to show this series in legend (default: True).
                text (str): Custom text for legend entry.
                button_shape (str): Button shape ('Circle', 'Square', 'Triangle', 'Diamond', 
                    'Plus', 'Cross', 'Minus', 'Star', 'Arrow').
                button_size (int | dict): Button size in pixels or {'x': width, 'y': height}.
                button_fill_style (str): Button color ("#ff0000").
                button_stroke_style (dict): Button border {'thickness': 2, 'color': '#000'}.
                button_rotation (float): Button rotation in degrees.
                text_font (dict): Text font settings {'size': 12, 'family': 'Arial', 'weight': 'bold'}.
                text_fill_style (str): Text color ("#000000").
                match_style_exactly (bool): Whether button should match series style exactly.
                highlight (bool): Whether highlighting on hover is enabled.
                lut: LUT element for legends (None to disable).
                lut_length (int): LUT bar length in pixels.
                lut_thickness (int): LUT bar thickness in pixels.
                lut_display_proportional_steps (bool): LUT step display mode.
                lut_step_value_formatter: Callback function for LUT value formatting.

        Returns:
            Reference to Area Series class.

        Examples:
        Basic series (shows in legend by default)
            >>> series = chart.add_area_series()

        Custom series
            >>> series = chart.add_area_series(
            ...     sizes=True,
            ...     rotations=True,
            ...     lookup_values=True,
            ...     colors=True
            ... )

        Custom auto-indexing with start/step
            >>> series = chart.add_area_series(
            ...     schema={
            ...         'time': {'auto': {'start': 1000, 'step': 5}},
            ...         'temperature': {}
            ...     }
            ... )
            ... series.set_data_mapping({'x': 'time', 'y': 'temperature'})
            ... series.append_samples(samples={'temperature': y_values})

        Progressive data pattern
            >>> series = chart.add_area_series(
            ...     schema={
            ...         'timestamps': {'pattern': 'progressive'},
            ...         'values': {'pattern': None}
            ...     }
            ... )
            ... series.set_data_mapping({'x': 'timestamps', 'y': 'values'})
            ... series.append_samples(samples={'timestamps': x_values, 'values': y_values})
        
        Hidden from legend
            >>> series = chart.add_area_series(show=False)
        
        Custom legend appearance
            >>> series = chart.add_area_series(
            ...     legend=
            ...     {
            ...         'show': True,
            ...         'button_shape': 'Triangle',
            ...         'text': 'Series A',
            ...         'text_font': {'size': 20, 'style': 'bold'},
            ...         'text_fill_style': '#0000FF',
            ...     }
            ... )
        """
        axis_x_id, axis_y_id = get_axis_id(axis_x or x_axis, axis_y or y_axis)
        series = AreaSeries(
            chart=self,
            colors=colors,
            lookup_values=lookup_values,
            ids=ids,
            sizes=sizes,
            rotations=rotations,            
            schema=schema,
            strict_mode=strict_mode,
            auto_detect_patterns=auto_detect_patterns,
            allow_input_modification=allow_input_modification,
            warnings=warnings,
            auto_sorting_enabled=auto_sorting_enabled,
            allow_data_grouping=allow_data_grouping,
            automatic_color_index=automatic_color_index,
            includes_nan=includes_nan,
            axis_x=axis_x_id,
            axis_y=axis_y_id,
            legend=legend,
        )
        self.series_list.append(series)
        return series

    def add_area_range_series(
        self, 
        automatic_color_index: int = None,
        axis_x: Axis = None,
        axis_y: Axis = None,
        x_axis: Axis = None,
        y_axis: Axis = None,
        legend: Optional[LegendOptions] = None,
    ) -> AreaRangeSeries:
        """Method for adding a new AreaRangeSeries to the chart.
        This series type is used for visualizing bands of data between two curves of data.

        Area Range Series accepts data of form {position, low, high}

        Args:
            automatic_color_index: Optional index to use for automatic coloring of series.
            x_axis (Axis): Optional non-default X Axis to attach series to.
            y_axis (Axis): Optional non-default Y Axis to attach series to.
            x_axis (Axis): Deprecated, use axis_x.
            y_axis (Axis): Deprecated, use axis_y.
            
            legend (dict): Legend configuration dictionary with the following options:
                show (bool): Whether to show this series in legend (default: True).
                text (str): Custom text for legend entry.
                button_shape (str): Button shape ('Circle', 'Square', 'Triangle', 'Diamond', 
                    'Plus', 'Cross', 'Minus', 'Star', 'Arrow').
                button_size (int | dict): Button size in pixels or {'x': width, 'y': height}.
                button_fill_style (str): Button color ("#ff0000").
                button_stroke_style (dict): Button border {'thickness': 2, 'color': '#000'}.
                button_rotation (float): Button rotation in degrees.
                text_font (dict): Text font settings {'size': 12, 'family': 'Arial', 'weight': 'bold'}.
                text_fill_style (str): Text color ("#000000").
                match_style_exactly (bool): Whether button should match series style exactly.
                highlight (bool): Whether highlighting on hover is enabled.
                lut: LUT element for legends (None to disable).
                lut_length (int): LUT bar length in pixels.
                lut_thickness (int): LUT bar thickness in pixels.
                lut_display_proportional_steps (bool): LUT step display mode.
                lut_step_value_formatter: Callback function for LUT value formatting.

        Returns:
            Reference to Area Range Series class.
            
        Examples:
            Basic area range series
            >>>     series = chart.add_area_range_series()
            
            Hidden from legend
            >>>     series = chart.add_area_range_series(show=False)
            
            Custom legend appearance
            >>>     series = chart.add_area_range_series(
            ...     legend=
            ...     {
            ...         'show': True,
            ...         'button_shape': 'Triangle',
            ...         'text': 'Series A',
            ...         'text_font': {'size': 20, 'style': 'bold'},
            ...         'text_fill_style': '#0000FF',
            ...     }
            ... )
        """
        axis_x_id, axis_y_id = get_axis_id(axis_x or x_axis, axis_y or y_axis)
        series = AreaRangeSeries(
            chart=self, 
            automatic_color_index=automatic_color_index,
            axis_x=axis_x_id,
            axis_y=axis_y_id, 
            legend=legend,)
        self.series_list.append(series)
        return series

    def add_heatmap_grid_series(
        self,
        columns: int,
        rows: int,
        data_order: str = 'columns',
        automatic_color_index: int = None,
        heatmap_data_type: str = 'intensity',
        axis_x: Axis = None,
        axis_y: Axis = None,
        x_axis: Axis = None,
        y_axis: Axis = None,
        legend: Optional[LegendOptions] = None,
    ) -> HeatmapGridSeries:
        """Add a Series for visualizing a Heatmap Grid with a _static column and grid count.

        Heatmap Grid Series accepts data in the form of two-dimensional matrix of correct size that includes
        integers or floats.

        Args:
            automatic_color_index: Optional index to use for automatic coloring of series.
            heatmap_data_type: Selection of format in which heatmap values are supplied.
                'intensity' | numeric value that can be colored with an associated color look up table. Defaults to 'intensity'.
            columns (int): Amount of columns (values on X Axis).
            rows (int): Amount of rows (values on Y Axis).
            data_order (str): "columns" | "rows" - Specify how to interpret grid matrix values supplied by user.
            x_axis (Axis): Optional non-default X Axis to attach series to.
            y_axis (Axis): Optional non-default Y Axis to attach series to.
            x_axis (Axis): Deprecated, use axis_x.
            y_axis (Axis): Deprecated, use axis_y.

            legend (dict): Legend configuration dictionary with the following options:
                show (bool): Whether to show this series in legend (default: True).
                text (str): Custom text for legend entry.
                button_shape (str): Button shape ('Circle', 'Square', 'Triangle', 'Diamond', 
                    'Plus', 'Cross', 'Minus', 'Star', 'Arrow').
                button_size (int | dict): Button size in pixels or {'x': width, 'y': height}.
                button_fill_style (str): Button color ("#ff0000").
                button_stroke_style (dict): Button border {'thickness': 2, 'color': '#000'}.
                button_rotation (float): Button rotation in degrees.
                text_font (dict): Text font settings {'size': 12, 'family': 'Arial', 'weight': 'bold'}.
                text_fill_style (str): Text color ("#000000").
                match_style_exactly (bool): Whether button should match series style exactly.
                highlight (bool): Whether highlighting on hover is enabled.
                lut: LUT element for legends (None to disable).
                lut_length (int): LUT bar length in pixels.
                lut_thickness (int): LUT bar thickness in pixels.
                lut_display_proportional_steps (bool): LUT step display mode.
                lut_step_value_formatter: Callback function for LUT value formatting.

        Returns:
            Reference to Heatmap Grid Series class.
            
        Examples:
            Basic area range series
            >>>     series = chart.add_heatmap_grid_series()
            
            Hidden from legend
            >>>     series = chart.add_heatmap_grid_series(show=False)
            
            Custom legend appearance
            >>>     series = chart.add_heatmap_grid_series(
            ...     legend=
            ...     {
            ...         'show': True,
            ...         'button_shape': 'Triangle',
            ...         'text': 'Series A',
            ...         'text_font': {'size': 20, 'style': 'bold'},
            ...         'text_fill_style': '#0000FF',
            ...     }
            ... )
        """
        axis_x_id, axis_y_id = get_axis_id(axis_x or x_axis, axis_y or y_axis)
        series = HeatmapGridSeries(
            chart=self,
            automatic_color_index=automatic_color_index,
            heatmap_data_type=heatmap_data_type,
            columns=columns,
            rows=rows,
            data_order=data_order,
            axis_x=axis_x_id,
            axis_y=axis_y_id,
            legend=legend,
        )
        self.series_list.append(series)
        return series

    def add_heatmap_scrolling_grid_series(
        self,
        resolution: int,
        scroll_dimension: str = 'columns',
        automatic_color_index: int = None,
        heatmap_data_type: str = 'intensity',
        axis_x: Axis = None,
        axis_y: Axis = None,
        x_axis: Axis = None,
        y_axis: Axis = None,
        legend: Optional[LegendOptions] = None,
    ) -> HeatmapScrollingGridSeries:
        """Add a Series for visualizing a Heatmap Grid, with API for pushing data in a scrolling manner
        (append new data on top of existing data).

        Heatmap Scrolling Grid Series accepts data in the form of two-dimensional matrix of correct size that includes
        integers or floats.

        Args:
            automatic_color_index: Optional index to use for automatic coloring of series.
            heatmap_data_type: Selection of format in which heatmap values are supplied.
                'intensity' | numeric value that can be colored with an associated color look up table. Defaults to 'intensity'.
            resolution (int): Static amount of columns (cells on X Axis) OR rows (cells on Y Axis).
            scroll_dimension (str): "columns" | "rows" -
                Select scrolling dimension, as well as how to interpret grid matrix values supplied by user.
            x_axis (Axis): Optional non-default X Axis to attach series to.
            y_axis (Axis): Optional non-default Y Axis to attach series to.
            x_axis (Axis): Deprecated, use axis_x.
            y_axis (Axis): Deprecated, use axis_y.
            legend (dict): Legend configuration dictionary with the following options:
                show (bool): Whether to show this series in legend (default: True).
                text (str): Custom text for legend entry.
                button_shape (str): Button shape ('Circle', 'Square', 'Triangle', 'Diamond', 
                    'Plus', 'Cross', 'Minus', 'Star', 'Arrow').
                button_size (int | dict): Button size in pixels or {'x': width, 'y': height}.
                button_fill_style (str): Button color ("#ff0000").
                button_stroke_style (dict): Button border {'thickness': 2, 'color': '#000'}.
                button_rotation (float): Button rotation in degrees.
                text_font (dict): Text font settings {'size': 12, 'family': 'Arial', 'weight': 'bold'}.
                text_fill_style (str): Text color ("#000000").
                match_style_exactly (bool): Whether button should match series style exactly.
                highlight (bool): Whether highlighting on hover is enabled.
                lut: LUT element for legends (None to disable).
                lut_length (int): LUT bar length in pixels.
                lut_thickness (int): LUT bar thickness in pixels.
                lut_display_proportional_steps (bool): LUT step display mode.
                lut_step_value_formatter: Callback function for LUT value formatting.

        Returns:
            Reference to Heatmap Scrolling Grid Series class.
        """
        axis_x_id, axis_y_id = get_axis_id(axis_x or x_axis, axis_y or y_axis)
        series = HeatmapScrollingGridSeries(
            chart=self,
            resolution=resolution,
            scroll_dimension=scroll_dimension,
            automatic_color_index=automatic_color_index,
            heatmap_data_type=heatmap_data_type,
            axis_x=axis_x_id,
            axis_y=axis_y_id,
            legend=legend,
        )
        self.series_list.append(series)
        return series

    def add_box_series(
            self, 
            automatic_color_index: int = None,
            dimension_strategy: str = None,
            axis_x: Axis = None,
            axis_y: Axis = None,
            x_axis: Axis = None,
            y_axis: Axis = None, 
            legend: Optional[LegendOptions] = None,) -> BoxSeries:
        """

        Args:
            automatic_color_index: Optional index to use for automatic coloring of series.
            dimension_strategy: DimensionStrategy Strategy used for selecting between vertical and horizontal Box Series.
            x_axis (Axis): Optional non-default X Axis to attach series to.
            y_axis (Axis): Optional non-default Y Axis to attach series to.
            x_axis (Axis): Deprecated, use axis_x.
            y_axis (Axis): Deprecated, use axis_y. 
            legend (dict): Legend configuration dictionary with the following options:
                show (bool): Whether to show this series in legend (default: True).
                text (str): Custom text for legend entry.
                button_shape (str): Button shape ('Circle', 'Square', 'Triangle', 'Diamond', 
                    'Plus', 'Cross', 'Minus', 'Star', 'Arrow').
                button_size (int | dict): Button size in pixels or {'x': width, 'y': height}.
                button_fill_style (str): Button color ("#ff0000").
                button_stroke_style (dict): Button border {'thickness': 2, 'color': '#000'}.
                button_rotation (float): Button rotation in degrees.
                text_font (dict): Text font settings {'size': 12, 'family': 'Arial', 'weight': 'bold'}.
                text_fill_style (str): Text color ("#000000").
                match_style_exactly (bool): Whether button should match series style exactly.
                highlight (bool): Whether highlighting on hover is enabled.
                lut: LUT element for legends (None to disable).
                lut_length (int): LUT bar length in pixels.
                lut_thickness (int): LUT bar thickness in pixels.
                lut_display_proportional_steps (bool): LUT step display mode.
                lut_step_value_formatter: Callback function for LUT value formatting.

        Returns:
            Reference to Box Series class.
            
        Examples:
            Basic area range series
            >>>     series = chart.add_box_series()
            
            Hidden from legend
            >>>     series = chart.add_box_series(show=False)

            Horizontal box series
            >>>     series = chart.add_box_series(dimension_strategy='horizontal')
            
            Custom legend appearance
            >>>     series = chart.add_box_series(
            ...     legend=
            ...     {
            ...         'show': True,
            ...         'button_shape': 'Triangle',
            ...         'text': 'Series A',
            ...         'text_font': {'size': 20, 'style': 'bold'},
            ...         'text_fill_style': '#0000FF',
            ...     }
            ... )      
        """
        axis_x_id, axis_y_id = get_axis_id(axis_x or x_axis, axis_y or y_axis)
        if dimension_strategy is not None:
            key = str(dimension_strategy).strip().lower()
            dimension_strategy = key
        series = BoxSeries(
            chart=self, 
            axis_x=axis_x_id, 
            axis_y=axis_y_id, 
            dimension_strategy=dimension_strategy, 
            automatic_color_index=automatic_color_index, 
            legend=legend,
            )
        self.series_list.append(series)
        return series

    def pan(self, x: int | float, y: int | float):
        """Method pans axes by pixels.

        Args:
            x (int | float): Amount to pan X in pixels.
            y (int | float): Amount to pan Y in pixels.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'pan', {'x': x, 'y': y})
        return self

    def zoom(self, location: tuple[int, int], amount: tuple[int, int]):
        """Method pans axes by pixels.

        Args:
            location (tuple[int, int]): Origin location for zooming as viewport pixels
            amount (tuple[int, int]): Amount to zoom X/Y in pixels

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(
            self.id,
            'zoom',
            {
                'location': {'x': location[0], 'y': location[1]},
                'amount': {'x': amount[0], 'y': amount[1]},
            },
        )
        return self

    def set_cursor_enabled_during_axis_animation(self, enabled: bool):
        """Disable/Enable Cursor during Axis Animations. Axis Animations are Axis Scale changes that are animated,
        such as Zooming and Scrolling done by using API (such as Axis.setInterval)
        or by using the mouse to click & drag on the Chart.

        Args:
            enabled (bool): Boolean value to enable or disable Cursor during Axis Animations.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setCursorEnabledDuringAxisAnimation', {'enabled': enabled})
        return self

    def add_ellipse_series(
        self,
        automatic_color_index: int = None,
        axis_x: Axis = None,
        axis_y: Axis = None,
        x_axis: Axis = None,
        y_axis: Axis = None, 
        legend: Optional[LegendOptions] = None,
    ):
        """Add an EllipseFigure to the Chart

        Args:
            automatic_color_index: Optional index to use for automatic coloring of series.
            x_axis (Axis): Optional non-default X Axis to attach series to.
            y_axis (Axis): Optional non-default Y Axis to attach series to.
            x_axis (Axis): Deprecated, use axis_x.
            y_axis (Axis): Deprecated, use axis_y.
            legend (dict): Legend configuration dictionary with the following options:
                show (bool): Whether to show this series in legend (default: True).
                text (str): Custom text for legend entry.
                button_shape (str): Button shape ('Circle', 'Square', 'Triangle', 'Diamond', 
                    'Plus', 'Cross', 'Minus', 'Star', 'Arrow').
                button_size (int | dict): Button size in pixels or {'x': width, 'y': height}.
                button_fill_style (str): Button color ("#ff0000").
                button_stroke_style (dict): Button border {'thickness': 2, 'color': '#000'}.
                button_rotation (float): Button rotation in degrees.
                text_font (dict): Text font settings {'size': 12, 'family': 'Arial', 'weight': 'bold'}.
                text_fill_style (str): Text color ("#000000").
                match_style_exactly (bool): Whether button should match series style exactly.
                highlight (bool): Whether highlighting on hover is enabled.
                lut: LUT element for legends (None to disable).
                lut_length (int): LUT bar length in pixels.
                lut_thickness (int): LUT bar thickness in pixels.
                lut_display_proportional_steps (bool): LUT step display mode.
                lut_step_value_formatter: Callback function for LUT value formatting.

        Returns:
            Reference to Ellipse Series class.
            
        Examples:
            Basic area range series
            >>>     series = chart.add_ellipse_series()
            
            Hidden from legend
            >>>     series = chart.add_ellipse_series(show=False)
            
            Custom legend appearance
            >>>     series = chart.add_ellipse_series(
            ...     legend=
            ...     {
            ...         'show': True,
            ...         'button_shape': 'Triangle',
            ...         'text': 'Series A',
            ...         'text_font': {'size': 20, 'style': 'bold'},
            ...         'text_fill_style': '#0000FF',
            ...     }
            ... )          
        """
        axis_x_id, axis_y_id = get_axis_id(axis_x or x_axis, axis_y or y_axis)
        ellipse_series = EllipseSeries(
            self,
            automatic_color_index=automatic_color_index,
            axis_x=axis_x_id,
            axis_y=axis_y_id,
            legend=legend,
        )
        self.series_list.append(ellipse_series)
        return ellipse_series

    def add_rectangle_series(
        self,
        automatic_color_index: int = None,
        axis_x: Axis = None,
        axis_y: Axis = None,
        x_axis: Axis = None,
        y_axis: Axis = None, 
        legend: Optional[LegendOptions] = None,
    ):
        """Add an RectangleFigure to the Chart.
        Args:
            automatic_color_index: Optional index to use for automatic coloring of series.
            x_axis (Axis): Optional non-default X Axis to attach series to.
            y_axis (Axis): Optional non-default Y Axis to attach series to.
            x_axis (Axis): Deprecated, use axis_x.
            y_axis (Axis): Deprecated, use axis_y.
            legend (dict): Legend configuration dictionary with the following options:
                show (bool): Whether to show this series in legend (default: True).
                text (str): Custom text for legend entry.
                button_shape (str): Button shape ('Circle', 'Square', 'Triangle', 'Diamond', 
                    'Plus', 'Cross', 'Minus', 'Star', 'Arrow').
                button_size (int | dict): Button size in pixels or {'x': width, 'y': height}.
                button_fill_style (str): Button color ("#ff0000").
                button_stroke_style (dict): Button border {'thickness': 2, 'color': '#000'}.
                button_rotation (float): Button rotation in degrees.
                text_font (dict): Text font settings {'size': 12, 'family': 'Arial', 'weight': 'bold'}.
                text_fill_style (str): Text color ("#000000").
                match_style_exactly (bool): Whether button should match series style exactly.
                highlight (bool): Whether highlighting on hover is enabled.
                lut: LUT element for legends (None to disable).
                lut_length (int): LUT bar length in pixels.
                lut_thickness (int): LUT bar thickness in pixels.
                lut_display_proportional_steps (bool): LUT step display mode.
                lut_step_value_formatter: Callback function for LUT value formatting.

        Returns:
            Reference to Rectangle Series class.
            
        Examples:
            Basic area range series
            >>>     series = chart.add_rectangle_series()
            
            Hidden from legend
            >>>     series = chart.add_rectangle_series(show=False)
            
            Custom legend appearance
            >>>     series = chart.add_rectangle_series(
            ...     legend=
            ...     {
            ...         'show': True,
            ...         'button_shape': 'Triangle',
            ...         'text': 'Series A',
            ...         'text_font': {'size': 20, 'style': 'bold'},
            ...         'text_fill_style': '#0000FF',
            ...     }
            ... )        
        """
        axis_x_id, axis_y_id = get_axis_id(axis_x or x_axis, axis_y or y_axis)
        rectangle_series = RectangleSeries(
            self,
            automatic_color_index=automatic_color_index,
            axis_x=axis_x_id,
            axis_y=axis_y_id,
            legend=legend,
        )
        self.series_list.append(rectangle_series)
        return rectangle_series

    def add_polygon_series(
        self,
        automatic_color_index: int = None,
        axis_x: Axis = None,
        axis_y: Axis = None,
        x_axis: Axis = None,
        y_axis: Axis = None, 
        legend: Optional[LegendOptions] = None,
    ):
        """Add an PolygonFigure to the Chart.

        Args:
            automatic_color_index: Optional index to use for automatic coloring of series.
            x_axis (Axis): Optional non-default X Axis to attach series to.
            y_axis (Axis): Optional non-default Y Axis to attach series to.
            x_axis (Axis): Deprecated, use axis_x.
            y_axis (Axis): Deprecated, use axis_y.
        legend (dict): Legend configuration dictionary with the following options:
                show (bool): Whether to show this series in legend (default: True).
                text (str): Custom text for legend entry.
                button_shape (str): Button shape ('Circle', 'Square', 'Triangle', 'Diamond', 
                    'Plus', 'Cross', 'Minus', 'Star', 'Arrow').
                button_size (int | dict): Button size in pixels or {'x': width, 'y': height}.
                button_fill_style (str): Button color ("#ff0000").
                button_stroke_style (dict): Button border {'thickness': 2, 'color': '#000'}.
                button_rotation (float): Button rotation in degrees.
                text_font (dict): Text font settings {'size': 12, 'family': 'Arial', 'weight': 'bold'}.
                text_fill_style (str): Text color ("#000000").
                match_style_exactly (bool): Whether button should match series style exactly.
                highlight (bool): Whether highlighting on hover is enabled.
                lut: LUT element for legends (None to disable).
                lut_length (int): LUT bar length in pixels.
                lut_thickness (int): LUT bar thickness in pixels.
                lut_display_proportional_steps (bool): LUT step display mode.
                lut_step_value_formatter: Callback function for LUT value formatting.

        Returns:
            Reference to Polygon Series class.
            
        Examples:
            Basic area range series
            >>>     series = chart.add_polygon_series()
            
            Hidden from legend
            >>>     series = chart.add_polygon_series(show=False)
            
            Custom legend appearance
            >>>     series = chart.add_polygon_series(
            ...     legend=
            ...     {
            ...         'show': True,
            ...         'button_shape': 'Triangle',
            ...         'text': 'Series A',
            ...         'text_font': {'size': 20, 'style': 'bold'},
            ...         'text_fill_style': '#0000FF',
            ...     }
            ... )          
        """
        axis_x_id, axis_y_id = get_axis_id(axis_x or x_axis, axis_y or y_axis)
        polygon_series = PolygonSeries(
            self,
            automatic_color_index=automatic_color_index,
            axis_x=axis_x_id,
            axis_y=axis_y_id,
            legend=legend,
        )
        self.series_list.append(polygon_series)
        return polygon_series

    def add_segment_series(
        self,
        automatic_color_index: int = None,
        axis_x: Axis = None,
        axis_y: Axis = None,
        x_axis: Axis = None,
        y_axis: Axis = None,
        legend: Optional[LegendOptions] = None,
    ):
        """Add an SegmentFigure to the Chart.

        Args:
            automatic_color_index: Optional index to use for automatic coloring of series.
            x_axis (Axis): Optional non-default X Axis to attach series to.
            y_axis (Axis): Optional non-default Y Axis to attach series to.
            x_axis (Axis): Deprecated, use axis_x.
            y_axis (Axis): Deprecated, use axis_y.
            legend (dict): Legend configuration dictionary with the following options:
                show (bool): Whether to show this series in legend (default: True).
                text (str): Custom text for legend entry.
                button_shape (str): Button shape ('Circle', 'Square', 'Triangle', 'Diamond', 
                    'Plus', 'Cross', 'Minus', 'Star', 'Arrow').
                button_size (int | dict): Button size in pixels or {'x': width, 'y': height}.
                button_fill_style (str): Button color ("#ff0000").
                button_stroke_style (dict): Button border {'thickness': 2, 'color': '#000'}.
                button_rotation (float): Button rotation in degrees.
                text_font (dict): Text font settings {'size': 12, 'family': 'Arial', 'weight': 'bold'}.
                text_fill_style (str): Text color ("#000000").
                match_style_exactly (bool): Whether button should match series style exactly.
                highlight (bool): Whether highlighting on hover is enabled.
                lut: LUT element for legends (None to disable).
                lut_length (int): LUT bar length in pixels.
                lut_thickness (int): LUT bar thickness in pixels.
                lut_display_proportional_steps (bool): LUT step display mode.
                lut_step_value_formatter: Callback function for LUT value formatting.
        Returns:
            Reference to Segment Series class.
            
        Examples:
            Basic area range series
            >>>     series = chart.add_segment_series()
            
            Hidden from legend
            >>>     series = chart.add_segment_series(show=False)
            
            Custom legend appearance
            >>>     series = chart.add_segment_series(
            ...     legend=
            ...     {
            ...         'show': True,
            ...         'button_shape': 'Triangle',
            ...         'text': 'Series A',
            ...         'text_font': {'size': 20, 'style': 'bold'},
            ...         'text_fill_style': '#0000FF',
            ...     }
            ... )         
        """
        axis_x_id, axis_y_id = get_axis_id(axis_x or x_axis, axis_y or y_axis)
        segment_series = SegmentSeries(
            self,
            automatic_color_index=automatic_color_index,
            axis_x=axis_x_id,
            axis_y=axis_y_id, 
            legend=legend,
        )
        self.series_list.append(segment_series)
        return segment_series

    def set_user_interactions(self, interactions=...):
        """Configure user interactions from a set of preset options for XY charts.

        Args:
            interactions (dict or None):
                - `None`: disable all interactions
                - `{}` or no argument: restore default interactions
                - `dict`: configure specific interactions

        Returns:
            ChartXY: Reference to the chart object for method chaining.

        Examples:
            # Disable all interactions:
            >>> chart.set_user_interactions(None)

            # Restore default interactions:
            >>> chart.set_user_interactions()
            ... chart.set_user_interactions({})

            # Configure specific interactions:
            >>> chart.set_user_interactions({
            ...     'pan': {
            ...         'lmb': {'drag': True},
            ...         'rmb': False,
            ...     },
            ...     'rectangleZoom': {
            ...         'lmb': False,
            ...         'rmb': {'drag': True},
            ...     },
            ... })
        """
        return super().set_user_interactions(interactions)
    
    def add_text_series(
        self,
        automatic_color_index: int = None,
        axis_x: Axis = None,
        axis_y: Axis = None,
        x_axis: Axis = None,
        y_axis: Axis = None,
        legend: Optional[LegendOptions] = None,
    ):
        """Add a TextSeries to the Chart for displaying individual text objects.

        Args:
            automatic_color_index: Optional index to use for automatic coloring of series.
            x_axis (Axis): Optional non-default X Axis to attach series to.
            y_axis (Axis): Optional non-default Y Axis to attach series to.
            x_axis (Axis): Deprecated, use axis_x.
            y_axis (Axis): Deprecated, use axis_y.
            legend (dict): Legend configuration dictionary with the following options:
                show (bool): Whether to show this series in legend (default: True).
                text (str): Custom text for legend entry.
                button_shape (str): Button shape ('Circle', 'Square', 'Triangle', 'Diamond', 
                    'Plus', 'Cross', 'Minus', 'Star', 'Arrow').
                button_size (int | dict): Button size in pixels or {'x': width, 'y': height}.
                button_fill_style (str): Button color ("#ff0000").
                button_stroke_style (dict): Button border {'thickness': 2, 'color': '#000'}.
                button_rotation (float): Button rotation in degrees.
                text_font (dict): Text font settings {'size': 12, 'family': 'Arial', 'weight': 'bold'}.
                text_fill_style (str): Text color ("#000000").
                match_style_exactly (bool): Whether button should match series style exactly.
                highlight (bool): Whether highlighting on hover is enabled.
                lut: LUT element for legends (None to disable).
                lut_length (int): LUT bar length in pixels.
                lut_thickness (int): LUT bar thickness in pixels.
                lut_display_proportional_steps (bool): LUT step display mode.
                lut_step_value_formatter: Callback function for LUT value formatting.

        Returns:
            Reference to Text Series class.
        """
        axis_x_id, axis_y_id = get_axis_id(axis_x or x_axis, axis_y or y_axis)
        text_series = TextSeries(
            self,
            automatic_color_index=automatic_color_index,
            axis_x=axis_x_id,
            axis_y=axis_y_id,
            legend=legend,
        )
        self.series_list.append(text_series)
        return text_series   

class ChartXYDashboard(ChartXY):
    """Class for ChartXY contained in Dashboard."""

    def __init__(
        self,
        instance: Instance,
        dashboard_id: str,
        column: int,
        row: int,
        colspan: int,
        rowspan: int,
        title: str = None,
        legend: Optional[LegendOptions] = None,
    ):
        ChartWithSeries.__init__(self, instance)
        legend_config = build_legend_config(legend)
        self.instance.send(
            self.id,
            'createChartXY',
            {
                'db': dashboard_id,
                'column': column,
                'row': row,
                'colspan': colspan,
                'rowspan': rowspan,
                'title': title,
                'legendConfig': legend_config,
            },
        )
        if title:
            self.instance.send(self.id, 'setTitle', {'title': title})
        ChartWithXYAxis.__init__(self)
        apply_post_legend_config(self, legend)
