from __future__ import annotations
from typing import Optional
import uuid


from lightningchart import conf, Themes, charts
from lightningchart.charts import GeneralMethods, TitleMethods, Chart
from lightningchart.instance import Instance
from lightningchart.series import Series
from lightningchart.ui.axis import SpiderChartAxis
from lightningchart.utils import convert_to_dict, convert_color_to_hex
from lightningchart.utils.utils import LegendOptions, apply_post_legend_config, build_legend_config


class SpiderChart(GeneralMethods, TitleMethods, SpiderChartAxis):
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
        """Chart for visualizing data in a radial form as dissected by named axes.

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
            Reference to SpiderChart class.

        Examples:
            Basic chart with simple legend
            >>> chart = lc.SpiderChart(
            ...     title='My Chart',
            ...     legend={
            ...         'visible': True,
            ...         'position': 'RightCenter',
            ...         'title': "Data Series"
            ...     }
            ... )

            Styled legend with background and custom entries
            >>> chart = lc.SpiderChart(
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
            >>> chart = lc.SpiderChart(
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
        Chart.__init__(self, instance)
        
        legend_config = build_legend_config(legend)

        self.instance.send(
            self.id,
            'spiderChart',
            {
                'theme': theme.value,
                'scaleTheme': theme_scale,
                'license': license or conf.LICENSE_KEY,
                'licenseInformation': license_information or conf.LICENSE_INFORMATION,
                'htmlTextRendering': html_text_rendering,
                'legendConfig': legend_config,
            },
        )
        if title:
            self.set_title(title)
        apply_post_legend_config(self, legend) 

    
    def add_series(self):
        """Adds a new SpiderSeries to the SpiderChart.

        Returns:
            SpiderSeries instance.
        """
        return SpiderSeries(self)

    def set_web_mode(self, mode: str = 'circle'):
        """Set mode of SpiderCharts web and background.

        Args:
            mode: "circle" | "normal"

        Returns:
            The instance of the class for fluent interface.
        """
        mode = 1 if mode == 'circle' else 0
        self.instance.send(self.id, 'setWebMode', {'mode': mode})
        return self

    def set_series_background_effect(self, enabled: bool = True):
        """Set theme effect enabled on component or disabled.

        Args:
            enabled (bool): Theme effect enabled.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setSeriesBackgroundEffect', {'enabled': enabled})
        return self

    def set_web_count(self, count: int):
        """Set count of 'webs' displayed.

        Args:
            count (int): Count of web lines.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setWebCount', {'count': count})
        return self

    def set_web_style(self, thickness: int | float, color: any = None):
        """Set style of spider charts webs as LineStyle.

        Args:
            thickness (int | float): Thickness of the web lines.
            color (Color): Color of the web.

        Returns:
            The instance of the class for fluent interface.
        """
        color = convert_color_to_hex(color) if color is not None else None

        self.instance.send(self.id, 'setWebStyle', {'thickness': thickness, 'color': color})
        return self


class SpiderChartDashboard(SpiderChart):
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
        Chart.__init__(self, instance)
        legend_config = build_legend_config(legend)
        self.instance.send(
            self.id,
            'createSpiderChart',
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


class SpiderSeries(Series):
    def __init__(self, chart: charts.Chart):
        self.chart = chart
        self.instance = chart.instance
        self.id = str(uuid.uuid4()).split('-')[0]
        self.instance.send(self.id, 'addSpiderSeries', {'chart': self.chart.id})

    def add_points(self, points: list[dict[str, int | float]]):
        """Adds an arbitrary amount of SpiderPoints to the Series.

        Args:
            points (str): List of SpiderPoints as {'axis': string, 'value': number}

        Returns:
            The instance of the class for fluent interface.
        """
        points = convert_to_dict(points)

        self.instance.send(self.id, 'addPoints', {'points': points})
        return self

    def set_fill_color(self, color: any):
        """Set color of the polygon that represents the shape of the Series.

        Args:
            color (Color): Color of the polygon.

        Returns:
            The instance of the class for fluent interface.
        """
        color = convert_color_to_hex(color) if color is not None else None

        self.instance.send(self.id, 'setSolidFillStyle', {'color': color})
        return self

    def set_point_color(self, color: any):
        """Set color of the series points.

        Args:
            color (Color): Color of the points.

        Returns:
            The instance of the class for fluent interface.
        """

        color = convert_color_to_hex(color) if color is not None else None

        self.instance.send(self.id, 'setPointFillStyle', {'color': color})
        return self

    def set_line_color(self, color: any):
        """Set the series polygon line color.

        Args:
            color (Color): Color of the lines.

        Returns:
            The instance of the class for fluent interface.
        """
        color = convert_color_to_hex(color) if color is not None else None

        self.instance.send(self.id, 'setLineFillStyle', {'color': color})
        return self

    def set_line_thickness(self, thickness: int):
        """Set the series polygon line thickness.

        Args:
            thickness (int): Thickness of the lines.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setLineThickness', {'width': thickness})
        return self

    def set_point_size(self, size: int | float):
        """Set size of point in pixels

        Args:
            size (int | float): Size of point in pixels.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setPoint2DSize', {'size': size})
        return self
