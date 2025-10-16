from __future__ import annotations
from typing import Optional


from lightningchart import conf, Themes
from lightningchart.charts import (
    GeneralMethods,
    TitleMethods,
    ChartWithLUT,
    ChartWithLabelStyling,
    Chart,
)
from lightningchart.instance import Instance
from lightningchart.utils import convert_to_dict, convert_color_to_hex
from lightningchart.utils.utils import LegendOptions, apply_post_legend_config, build_legend_config


class PieChart(GeneralMethods, TitleMethods, ChartWithLUT, ChartWithLabelStyling):
    """Visualizes proportions and percentages between categories, by dividing a circle into proportional segments."""

    def __init__(
        self,
        data: list[dict[str, int | float]] = None,
        inner_radius: int | float = None,
        title: str = None,
        theme: Themes = Themes.Light,
        theme_scale: float = 1.0,
        labels_inside_slices: bool = False,
        license: str = None,
        license_information: str = None,
        html_text_rendering: bool = True,
        legend: Optional[LegendOptions] = None,
    ):
        """Visualizes proportions and percentages between categories, by dividing a circle into proportional segments.

        Args:
            data (list[dict[str, int | float]]): List of {name, value} slices.
            inner_radius (int | float): Inner radius as a percentage of outer radius [0, 100].
            title (str): Title of the chart.
            theme (Themes): Theme of the chart.
            labels_inside_slices (bool): If true, the labels are inside pie slices. If false, the labels are on the
                sides of the slices.
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
            Reference to PieChart class.

        Examples:
            Basic chart with simple legend
            >>> chart = lc.PieChart(
            ...     title='My Chart',
            ...     legend={
            ...         'visible': True,
            ...         'position': 'RightCenter',
            ...         'title': "Data Series"
            ...     }
            ... )

            Styled legend with background and custom entries
            >>> chart = lc.PieChart(
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
            >>> chart = lc.PieChart(
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
            'pieChart',
            {
                'theme': theme.value,
                'scaleTheme': theme_scale,
                'labelsInsideSlices': labels_inside_slices,
                'license': license or conf.LICENSE_KEY,
                'licenseInformation': license_information or conf.LICENSE_INFORMATION,
                'htmlTextRendering': html_text_rendering,
                'legendConfig': legend_config,
            },
        )
        if title:
            self.set_title(title)
        if inner_radius:
            self.set_inner_radius(inner_radius)
        if data:
            self.add_slices(data)
        apply_post_legend_config(self, legend)   
    
    def add_slice(self, name: str, value: int | float):
        """Add new Slice to the Pie Chart.

        Args:
            name (str): Initial name for Slice as string.
            value (int | float): Initial value for Slice as number.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'addSlice', {'name': name, 'value': value})
        return self

    def add_slices(self, slices: list[dict[str, int | float]]):
        """This method is used for the adding multiple slices in the funnel chart.

        Args:
            slices (list[dict[int | float, int | float]]): List of slices {name, value}.

        Returns:
            The instance of the class for fluent interface.
        """
        slices = convert_to_dict(slices)

        self.instance.send(self.id, 'addSlices', {'slices': slices})
        return self

    def set_inner_radius(self, radius: int | float):
        """Set inner radius of Pie Chart.
        This method can be used to style the Pie Chart as a "Donut Chart", with the center being hollow.

        Args:
            radius (int | float): Inner radius as a percentage of outer radius [0, 100]

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setInnerRadius', {'radius': radius})
        return self

    def set_slice_stroke(self, thickness: int | float, color: any = None):
        """Set stroke style of Pie Slices border.

        Args:
            thickness (int | float): Thickness of the slice border.
            color (Color): Color of the slice border.

        Returns:
            The instance of the class for fluent interface.
        """
        color = convert_color_to_hex(color) if color is not None else None

        self.instance.send(
            self.id,
            'setSliceStrokeStyle',
            {'thickness': thickness, 'color': color},
        )
        return self

    def set_multiple_slice_explosion(self, enabled: bool):
        """Set if it is allowed for multiple Slices to be 'exploded' at the same time or not.
        When a Slice is exploded, it is drawn differently from non-exploded state,
        usually slightly "pushed away" from the center of Pie Chart.

        Args:
            enabled (bool): Is behavior allowed as boolean flag.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setMultipleSliceExplosion', {'enabled': enabled})
        return self

    def set_slice_explosion_offset(self, offset: int | float):
        """Set offset of exploded Slices in pixels.

        Args:
            offset (int | float): Offset of exploded Slices in pixels

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setSliceExplosionOffset', {'offset': offset})
        return self

    def set_label_connector_end_length(self, length: int | float):
        """Set horizontal length of connector line before connecting to label.

        Args:
            length (int | float): Length of the connector line before connecting to label.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setLabelConnectorEndLength', {'length': length})
        return self

    def set_label_connector_gap_start(self, gap: int | float):
        """Set gap between slice and connector line start.

        Args:
            gap (int | float): Gap as pixels.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setLabelConnectorGapStart', {'gap': gap})
        return self

    def set_label_slice_offset(self, offset: int | float):
        """Set distance between slice and label (includes explosion offset), this points to reference position of label,
        so not necessarily the nearest corner.

        Args:
            offset (int | float): Length as pixels.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setLabelSliceOffset', {'offset': offset})
        return self


class PieChartDashboard(PieChart):
    def __init__(
        self,
        instance: Instance,
        dashboard_id: str,
        column: int,
        row: int,
        colspan: int,
        rowspan: int,
        labelsInsideSlices: bool = False,
        legend: Optional[LegendOptions] = None,
    ):
        Chart.__init__(self, instance)
        legend_config = build_legend_config(legend)
        self.instance.send(
            self.id,
            'createPieChart',
            {
                'db': dashboard_id,
                'column': column,
                'row': row,
                'colspan': colspan,
                'rowspan': rowspan,
                'labelsInsideSlices': labelsInsideSlices,
                'legendConfig': legend_config,
            },
        )
        apply_post_legend_config(self, legend)
