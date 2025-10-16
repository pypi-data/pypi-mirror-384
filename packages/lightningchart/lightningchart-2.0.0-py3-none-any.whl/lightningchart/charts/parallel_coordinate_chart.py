from typing import Optional
from lightningchart import Themes, conf
from lightningchart.series.parallel_coordinate_series import ParallelCoordinateSeries
from lightningchart.charts import ChartWithSeries, TitleMethods, GeneralMethods
from lightningchart.instance import Instance
from lightningchart.ui.axis import GenericAxis
from lightningchart.ui import UserInteractions
from lightningchart.utils import convert_color_to_hex
import uuid

from lightningchart.utils.utils import LegendOptions, apply_post_legend_config, build_legend_config


class ParallelCoordinateChart(ChartWithSeries, TitleMethods, GeneralMethods, UserInteractions):
    """Chart for visualizing data in a parallel coordinate system."""

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
        """Initialize a Parallel Coordinate Chart with a theme and optional title.

        Args:
            theme (Themes): Theme for the chart. Defaults to `Themes.White`.
            title (str, optional): Title of the chart. Defaults to None.
            license (str): License key.
            theme_scale: To up or downscale font sizes as well as tick lengths, element paddings, etc. to make font sizes sit in nicely.
            html_text_rendering: Can be enabled for sharper text display where required with drawback of weaker performance.
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
            Reference to ParallelCoordinateChart class.

        Examples:
            Basic chart with simple legend
            >>> chart = lc.ParallelCoordinateChart(
            ...     title='My Chart',
            ...     legend={
            ...         'visible': True,
            ...         'position': 'RightCenter',
            ...         'title': "Data Series"
            ...     }
            ... )

            Styled legend with background and custom entries
            >>> chart = lc.ParallelCoordinateChart(
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
            >>> chart = lc.ParallelCoordinateChart(
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
        super().__init__(instance)
        self.theme = theme
        self.axes = []
        self.series_list = []

        legend_config = build_legend_config(legend)
        self.instance.send(
            self.id,
            'ParallelCoordinateChart',
            {
                'theme': theme.value,
                'scaleTheme': theme_scale,
                'license': license or conf.LICENSE_KEY,
                'licenseInformation': license_information or conf.LICENSE_INFORMATION,
                'htmlTextRendering': html_text_rendering,
                'visible': legend,
                'legendConfig': legend_config,
            },
        )

        if title:
            self.set_title(title)
        apply_post_legend_config(self, legend)      
    
    def set_axes(self, axes: list):
        """Set axes of the parallel coordinate chart as a list of strings.

        Args:
            axes (list): List of axis names or identifiers.

        Returns:
            The instance of the chart for fluent interface.
        """
        self.axes = axes
        self.instance.send(self.id, 'setAxes', {'axes': axes})
        return self

    def get_axis(self, axis_key: str):
        """Retrieve a specific axis by its name or ID.

        Args:
            axis_key (str): The key or name of the axis.

        Returns:
            The corresponding axis object.

        Raises:
            ValueError: If the axis with the given key is not found.
        """

        if axis_key in self.axes:
            axis_name = axis_key
        else:
            raise ValueError(f"Axis with key '{axis_key}' not found.")

        return ParallelCoordinateAxis(self, axis_name)

    def add_series(self, theme: Themes = Themes.Light,  name: str = None):
        """Add a new data series to the chart.            

        Returns:
            The created series instance.

        
        """
        series = ParallelCoordinateSeries(self)
        self.series_list.append(series)
        return series

    def get_series(self) -> list[ParallelCoordinateSeries]:
        """Get all data series in the chart.

        Returns:
            A list of all series in the chart.
        """
        return self.series_list

    def set_lut(self, axis_key: str, interpolate: bool, steps: list):
        """Configure series coloring by a Value-Color Table (LUT) based on a specific axis.

        Args:
            axis_key (str): The key of the axis for which to apply LUT.
            interpolate (bool): Whether to interpolate between LUT steps.
            steps (list): List of LUT steps, each with a value and color.

        Returns:
            The instance of the chart for fluent interface.
        """
        for step in steps:
            step['color'] = convert_color_to_hex(step['color'])

        lut_config = {'interpolate': interpolate, 'steps': steps}
        self.instance.send(self.id, 'setParallelAxisLUT', {'axisId': axis_key, 'lut': lut_config})
        return self

    def set_spline(self, enabled: bool):
        """Enable or disable spline interpolation for the chart.

        Args:
            enabled (bool): True to enable spline interpolation, False to disable.

        Returns:
            The instance of the chart for fluent interface.
        """
        self.instance.send(self.id, 'setSpline', {'enabled': enabled})
        return self

    def set_series_stroke_thickness(self, thickness: int | float):
        """Set the thickness of series lines.

        Args:
            thickness (int | float): Thickness of the lines in pixels.

        Returns:
            The instance of the chart for fluent interface.
        """
        self.instance.send(self.id, 'setSeriesStrokeThickness', {'thickness': thickness})
        return self

    def set_highlight_on_hover(self, state: bool):
        """Enable or disable highlight on hover for series.

        Args:
            state (bool): True to enable highlight on hover, False to disable.

        Returns:
            The instance of the chart for fluent interface.
        """
        self.instance.send(self.id, 'setSeriesHighlightOnHover', {'state': state})
        return self

    def set_unselected_series_color(self, color: any):
        """Set the color for unselected series.

        Args:
            Color: Color to apply to unselected series.

        Returns:
            The instance of the chart for fluent interface.
        """
        color = convert_color_to_hex(color) if color is not None else None

        self.instance.send(self.id, 'setUnselectedSeriesColor', {'color': color})
        return self

    def set_user_interactions(self, interactions=...):
        """Configure user interactions from a set of preset options.

        Args:
            interactions (dict or None):
                - `None`: disable all interactions
                - `{}` or no argument: restore default interactions
                - `dict`: configure specific interactions

        Examples:
            ## Disable all interactions:
            >>> chart.set_user_interactions(None)

            ## Restore default interactions:
            >>> chart.set_user_interactions()
            ... chart.set_user_interactions({})

            ## Remove select range selector interactions
            >>> chart.set_user_interactions(
            ...     {
            ...         'rangeSelectors': {
            ...             'create': {
            ...                 'doubleClickAxis': True,
            ...             },
            ...             'dispose': {
            ...                 'doubleClick': True,
            ...             },
            ...         },
            ...     }
            ... )
        """
        return super().set_user_interactions(interactions)


class ParallelCoordinateAxis(GenericAxis):
    def __init__(self, chart, axis_key):
        """Initialize a parallel coordinate axis.

        Args:
            chart (ParallelCoordinateChart): The parent chart.
            axis_key (str): The identifier or name of the axis.
        """
        self.chart = chart
        self.axis_key = axis_key
        self.instance = Instance()
        self.id = str(uuid.uuid4()).split('-')[0]

    def add_range_selector(self):
        """Add a range selector to this axis.

        Returns:
            The created range selector object.
        """
        selector_id = str(uuid.uuid4()).split('-')[0]
        self.chart.instance.send(
            self.chart.id,
            'addRangeSelector',
            {'axisId': self.axis_key, 'selectorId': selector_id},
        )
        return ParallelCoordinateAxisRangeSelector(self.chart, self.axis_key, selector_id)

    def set_title(self, title: str):
        """Set the title for the axis.

        Args:
            title (str): Title text for the axis.

        Returns:
            The instance of the axis for fluent interface.
        """
        self.chart.instance.send(
            self.chart.id,
            'setParallelAxisTitle',
            {'axisId': self.axis_key, 'title': title},
        )
        self.title = title
        return self

    def set_visible(self, visible: bool):
        """Set the visibility of the axis.

        Args:
            visible (bool): True to make the axis visible, False to hide.

        Returns:
            The instance of the axis for fluent interface.
        """
        self.chart.instance.send(
            self.chart.id,
            'setParallelAxisVisibility',
            {'axisId': self.axis_key, 'visible': visible},
        )
        return self

    def get_title(self) -> str:
        """Retrieve the title of the axis.

        Returns:
            str: The title of the axis.
        """
        return self.title

    def set_palette_stroke(self, thickness: int | float, interpolate: bool, steps: list):
        """Set the stroke style of the axis with a palette.

        Args:
            thickness (int | float): Thickness of the stroke in pixels.
            interpolate (bool): Whether to interpolate between palette steps.
            steps (list): List of palette steps, each containing value and color.

        Returns:
            The instance of the axis for fluent interface.
        """
        for step in steps:
            step['color'] = convert_color_to_hex(step['color'])
        self.chart.instance.send(
            self.chart.id,
            'setParallelAxisStrokeStyle',
            {
                'axisId': self.axis_key,
                'thickness': thickness,
                'lut': {'interpolate': interpolate, 'steps': steps},
            },
        )
        return self

    def set_solid_stroke(self, thickness: int | float, color: any = None):
        """Set a solid stroke style for the axis.

        Args:
            thickness (int | float): Thickness of the stroke in pixels.
            color: Solid color for the stroke.

        Returns:
            The instance of the axis for fluent interface.
        """
        color = convert_color_to_hex(color) if color is not None else None

        self.chart.instance.send(
            self.chart.id,
            'setSolidStroke',
            {'axisId': self.axis_key, 'thickness': thickness, 'color': color},
        )
        return self

    def set_tick_strategy(self, strategy: str, time_origin: int | float = None, utc: bool = False):
        """Set the tick strategy for the axis.

        Args:
            strategy (str): Tick strategy ("Empty", "Numeric", "DateTime", "Time").
            time_origin (int | float, optional): Time origin for the strategy. Defaults to None.
            utc (bool, optional): Whether to use UTC for DateTime strategy. Defaults to False.

        Returns:
            The instance of the axis for fluent interface.
        """
        strategies = ('Empty', 'Numeric', 'DateTime', 'Time')
        if strategy not in strategies:
            raise ValueError(f"Expected strategy to be one of {strategies}, but got '{strategy}'.")

        self.chart.instance.send(
            self.chart.id,
            'setParellelAxisTickStrategy',
            {
                'strategy': strategy,
                'axisId': self.axis_key,
                'timeOrigin': time_origin,
                'utc': utc,
            },
        )
        return self


class ParallelCoordinateAxisRangeSelector:
    def __init__(self, chart, axis_key, selector_id):
        """Initialize a range selector for a parallel coordinate axis.

        Args:
            chart (ParallelCoordinateChart): The parent chart.
            axis_key (str): The key or name of the axis.
            selector_id (str): Unique identifier for the selector.
        """
        self.chart = chart
        self.axis_key = axis_key
        self.selector_id = selector_id

    def set_interval(self, a: float, b: float, stop_axis_after: bool = False, animate: bool = False):
        """Set the range interval for the selector.

        Args:
            a (float): Start of the interval.
            b (float): End of the interval.
            stop_axis_after (bool, optional): Stop axis after the range. Defaults to False.
            animate (bool, optional): Animate the range update. Defaults to False.

        Returns:
            The instance of the selector for fluent interface.
        """
        self.chart.instance.send(
            self.chart.id,
            'setRangeSelectorInterval',
            {
                'selectorId': self.selector_id,
                'axisId': self.axis_key,
                'start': a,
                'end': b,
                'stop': stop_axis_after,
                'animate': animate,
            },
        )
        return self

    def dispose(self):
        """Remove the range selector permanently.

        Returns:
            The instance of the class for fluent interface.
        """
        self.chart.instance.send(
            self.chart.id,
            'dispose',
            {
                'selectorId': self.selector_id,
            },
        )
        return self


class ParallelCoordinateChartDashboard(ParallelCoordinateChart):
    """Class for ParallelCoordinateChart contained in Dashboard."""

    def __init__(
        self,
        instance: Instance,
        dashboard_id: str,
        column: int,
        row: int,
        colspan: int,
        rowspan: int,
        legend: Optional[LegendOptions] = None,
    ):
        super().__init__()
        self.instance = instance
        legend_config = build_legend_config(legend)
        self.instance.send(
            self.id,
            'createParallelCoordinateChart',
            {
                'db': dashboard_id,
                'column': column,
                'row': row,
                'colspan': colspan,
                'rowspan': rowspan,
                'legendConfig': legend_config,
            },
        )
        apply_post_legend_config(self, legend)
