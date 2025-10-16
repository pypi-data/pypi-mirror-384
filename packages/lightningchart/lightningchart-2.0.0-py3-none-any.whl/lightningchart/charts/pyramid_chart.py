from __future__ import annotations
from typing import Optional


from lightningchart import conf, Themes
from lightningchart.charts import (
    FunnelPyramidLabelConnctorMethods,
    GeneralMethods,
    TitleMethods,
    ChartWithLUT,
    Chart,
    ChartWithLabelStyling,
)
from lightningchart.instance import Instance
from lightningchart.utils import convert_to_dict, convert_color_to_hex
from lightningchart.utils.utils import LegendOptions, apply_post_legend_config, build_legend_config


class PyramidChart(GeneralMethods, TitleMethods, ChartWithLUT, ChartWithLabelStyling, FunnelPyramidLabelConnctorMethods):
    """Visualizes proportions and percentages between categories, by dividing a pyramid into proportional segments."""

    def __init__(
        self,
        data: list[dict[str, int | float]] = None,
        slice_mode: str = 'height',
        labels_inside: bool = False,
        theme: Themes = Themes.Light,
        theme_scale: float = 1.0,
        title: str = None,
        license: str = None,
        license_information: str = None,
        html_text_rendering: bool = True,
        legend: Optional[LegendOptions] = None,
    ):
        """Visualizes proportions and percentages between categories, by dividing a pyramid into proportional segments.

        Args:
            data (list[dict[str, int | float]]): List of {name, value} slices.
            slice_mode (str): "width" | "height"
            labels_inside: If True, labels are placed inside slices. If False, labels are on sides (default).
            theme (Themes): Theme of the chart.
            title (str): Title of the chart.
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
            Reference to PyramidChart class.

        Examples:
            Basic chart with simple legend
            >>> chart = lc.PyramidChart(
            ...     title='My Chart',
            ...     legend={
            ...         'visible': True,
            ...         'position': 'RightCenter',
            ...         'title': "Data Series"
            ...     }
            ... )

            Styled legend with background and custom entries
            >>> chart = lc.PyramidChart(
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
            >>> chart = lc.PyramidChart(
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
            'pyramidChart',
            {
                'theme': theme.value,
                'scaleTheme': theme_scale,
                'labelsInside': labels_inside,
                'license': license or conf.LICENSE_KEY,
                'licenseInformation': license_information or conf.LICENSE_INFORMATION,
                'htmlTextRendering': html_text_rendering,
                'legendConfig': legend_config,
            },
        )
        self.set_slice_mode(slice_mode)
        if title:
            self.set_title(title)
        if data:
            self.add_slices(data)
        apply_post_legend_config(self, legend) 
    
    def add_slice(self, name: str, value: int | float):
        """This method is used for the adding slices in the pyramid chart.

        Args:
            name (str): Pyramid slice title.
            value (int | float): Pyramid slice value.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'addSlice', {'name': name, 'value': value})
        return self

    def add_slices(self, slices: list[dict[str, int | float]]):
        """This method is used for the adding multiple slices in the pyramid chart.

        Args:
            slices (list[dict[str, int | float]]): Array of {name, value} slices.

        Returns:
            The instance of the class for fluent interface.
        """
        slices = convert_to_dict(slices)

        self.instance.send(self.id, 'addSlices', {'slices': slices})
        return self

    def set_neck_width(self, width: int | float):
        """Set Pyramid Neck Width.

        Args:
            width (int | float): Pyramid Neck Width range from 0 to 100.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setNeckWidth', {'width': width})
        return self

    def set_slice_mode(self, mode: str = 'height'):
        """Set PyramidSliceMode. Can be used to select between different drawing approaches for Slices.

        Args:
            mode (str): "height" | "width"

        Returns:
            The instance of the class for fluent interface.
        """
        slice_modes = ('height', 'width')
        if mode not in slice_modes:
            raise ValueError(f"Expected mode to be one of {slice_modes}, but got '{mode}'.")

        mode_number = 1
        if mode == 'height':
            mode_number = 0
        self.instance.send(self.id, 'setSliceMode', {'mode': mode_number})
        return self

    def set_slice_gap(self, gap: int | float):
        """Set gap between Slice / start of label connector, and end of label connector / Label.

        Args:
            gap (int | float): Gap as pixels. Clamped between [0, 20] !

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setSliceGap', {'gap': gap})
        return self

    def set_slice_stroke(self, thickness: int | float, color: any = None):
        """Set stroke style of Pyramid Slices border.

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

    def set_label_side(self, side: str = 'left'):
        """Set the side where label should display.

        Args:
            side: "left" | "right"

        Returns:
            The instance of the class for fluent interface.
        """
        label_sides = ('left', 'right')
        if side not in label_sides:
            raise ValueError(f"Expected side to be one of {label_sides}, but got '{side}'.")

        self.instance.send(self.id, 'setLabelSide', {'side': side})
        return self


class PyramidChartDashboard(PyramidChart):
    def __init__(
        self,
        instance: Instance,
        dashboard_id: str,
        column: int,
        row: int,
        colspan: int,
        rowspan: int,
        labelsInside: bool = False,
        legend: Optional[LegendOptions] = None,
    ):
        Chart.__init__(self, instance)
        legend_config = build_legend_config(legend)
        self.instance.send(
            self.id,
            'createPyramidChart',
            {
                'db': dashboard_id,
                'column': column,
                'row': row,
                'colspan': colspan,
                'rowspan': rowspan,
                'labelsInside': labelsInside,
                'legendConfig': legend_config,
            },
        )
        apply_post_legend_config(self, legend)
