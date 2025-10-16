from __future__ import annotations
from typing import Optional


from lightningchart import conf, Themes
from lightningchart.charts import GeneralMethods, TitleMethods, Chart
from lightningchart.instance import Instance
from lightningchart.utils import convert_to_dict, convert_color_to_hex
from lightningchart.ui import UserInteractions
from lightningchart.utils.utils import LegendOptions, apply_post_legend_config, build_legend_config


class TreeMapChart(GeneralMethods, TitleMethods, UserInteractions):
    """TreeMap Chart for visualizing hierarchical data."""

    def __init__(
        self,
        data: list[dict] = None,
        theme: Themes = Themes.Light,
        theme_scale: float = 1.0,
        title: str = None,
        license: str = None,
        license_information: str = None,
        html_text_rendering: bool = True,
        legend: Optional[LegendOptions] = None,
    ):
        """A TreeMapChart with optional data and configurations.

        Args:
            data (list[dict]): Initial data for the TreeMap.
            theme (Themes): Chart theme (Themes.Light, Themes.DarkGold, etc.).
            theme_scale (float): Scale factor for fonts, ticks, padding (default: 1.0).
            title (str): Chart title.
            license (str): License key.
            license_information (str): License information.
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
            Reference to TreeMapChart class.

        Examples:
            Basic chart with simple legend
            >>> chart = lc.TreeMapChart(
            ...     title='My Chart',
            ...     legend={
            ...         'visible': True,
            ...         'position': 'RightCenter',
            ...         'title': "Data Series"
            ...     }
            ... )

            Styled legend with background and custom entries
            >>> chart = lc.TreeMapChart(
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
            >>> chart = lc.TreeMapChart(
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
            'treeMapChart',
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
        if data:
            self.set_data(data)
        apply_post_legend_config(self, legend)  
    

    def set_data(self, data: list[dict]):
        """Set data for the TreeMap chart.

        Args:
            data: Array of objects with category and value properties.

        Returns:
            The instance of the class for fluent interface.
        """
        data = convert_to_dict(data)

        self.instance.send(self.id, 'setData', {'data': data})
        return self

    def set_displayed_levels_count(self, level: int):
        """Set the amount of levels of children nodes to display.

        Args:
            level: Amount of levels to display.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setDisplayedLevelsCount', {'level': level})
        return self

    def set_header_font(
        self,
        size: int | float,
        family: str = 'Segoe UI, -apple-system, Verdana, Helvetica',
        style: str = 'normal',
        weight: str = 'normal',
    ):
        """Set the header font for the TreeMap chart.

        Args:
            size (int | float): CSS font size. For example, 16.
            family (str): CSS font family. For example, 'Arial, Helvetica, sans-serif'.
            weight (str): CSS font weight. For example, 'bold'.
            style (str): CSS font style. For example, 'italic'

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(
            self.id,
            'setHeaderFont',
            {'family': family, 'size': size, 'weight': weight, 'style': style},
        )
        return self

    def set_init_path_button_text(self, text: str):
        """Set the text for the back button that returns to the 1st level of Nodes.

        Args:
            text: Text for the button.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setInitPathButtonText', {'text': text})
        return self

    def set_animation_highlight(self, enabled: bool):
        """Set component highlight animations enabled or not.

        Args:
            enabled: Boolean flag.

        Returns:
            The instance of the class for fluent interface.
        """
        """Set component highlight animations enabled or not."""
        self.instance.send(self.id, 'setAnimationHighlight', {'enabled': enabled})
        return self

    def set_animation_values(self, enabled: bool, speed_multiplier: float = 1):
        """Enable/disable animation of Nodes positions.

        Args:
            enabled: Boolean flag.
            speed_multiplier: Optional multiplier for category animation speed. 1 matches default speed.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(
            self.id,
            'setAnimationValues',
            {'enabled': enabled, 'speedMultiplier': speed_multiplier},
        )
        return self

    def set_node_coloring(
        self,
        steps: list[dict],
        look_up_property: str = 'value',
        interpolate: bool = True,
        percentage_values: bool = False,
    ):
        """Set the color of the nodes.

        Args:
            steps (list[dict]): List of {"value": number, "color": Color} dictionaries.
            interpolate (bool): Enables automatic linear interpolation between color steps.
            look_up_property (str): "value" | "x" | "y" | "z"
            percentage_values (bool): Whether values represent percentages or explicit values.

        Returns:
            The instance of the class for fluent interface.
        """
        for i in steps:
            if 'color' in i:
                i['color'] = convert_color_to_hex(i['color'])

        self.instance.send(
            self.id,
            'setNodeColoring',
            {
                'steps': steps,
                'lookUpProperty': look_up_property,
                'interpolate': interpolate,
                'percentageValues': percentage_values,
            },
        )
        return self

    def set_path_label_color(self, color: any):
        """Set Color of the path labels.

        Args:
            color: Color value.

        Returns:
            The instance of the class for fluent interface.
        """
        color = convert_color_to_hex(color) if color is not None else None

        self.instance.send(self.id, 'setPathLabelFillStyle', {'color': color})
        return self

    def set_path_label_font(
        self,
        size: int | float,
        family: str = 'Segoe UI, -apple-system, Verdana, Helvetica',
        style: str = 'normal',
        weight: str = 'normal',
    ):
        """Set Font of the path labels.

        Args:
            size (int | float): CSS font size. For example, 16.
            family (str): CSS font family. For example, 'Arial, Helvetica, sans-serif'.
            weight (str): CSS font weight. For example, 'bold'.
            style (str): CSS font style. For example, 'italic'

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(
            self.id,
            'setPathLabelFont',
            {'family': family, 'size': size, 'weight': weight, 'style': style},
        )
        return self

    def set_header_color(self, color: any):
        """Set the color of the node labels.

        Args:
            color: Color value

        Returns:
            The instance of the class for fluent interface.
        """
        color = convert_color_to_hex(color) if color is not None else None

        self.instance.send(self.id, 'setHeaderFillStyle', {'color': color})
        return self

    def set_label_font(
        self,
        size: int | float,
        family: str = 'Segoe UI, -apple-system, Verdana, Helvetica',
        style: str = 'normal',
        weight: str = 'normal',
    ):
        """Set the font of the node labels.

        Args:
            size (int | float): CSS font size. For example, 16.
            family (str): CSS font family. For example, 'Arial, Helvetica, sans-serif'.
            weight (str): CSS font weight. For example, 'bold'.
            style (str): CSS font style. For example, 'italic'

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(
            self.id,
            'setLabelFont',
            {'family': family, 'size': size, 'weight': weight, 'style': style},
        )
        return self

    def set_label_color(self, color: any):
        """Set the color of the node labels.

        Args:
            color: Color value.

        Returns:
            The instance of the class for fluent interface.
        """
        color = convert_color_to_hex(color) if color is not None else None

        self.instance.send(self.id, 'setLabelFillStyle', {'color': color})
        return self

    def set_node_border_style(self, thickness: int | float, color: any = None):
        """Set the line style of the node labels.

        Args:
            thickness (int | float): Thickness of the border.
            color (Color): Color of the border.

        Returns:
            The instance of the class for fluent interface.
        """
        color = convert_color_to_hex(color) if color is not None else None

        self.instance.send(
            self.id,
            'setNodeBorderStyle',
            {'thickness': thickness, 'color': color},
        )
        return self

    def set_node_effect(self, enabled: bool):
        """Set theme effect enabled on component or disabled.

        Args:
            enabled: Boolean flag.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setNodeEffect', {'enabled': enabled})
        return self

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

    def set_user_interactions(self, interactions=...):
        """Configure user interactions from a set of preset options.

        Args:
            interactions (dict or None):
                - `None`: disable all interactions
                - `{}` or no argument: restore default interactions
                - `dict`: configure specific interactions

        Examples:
            # Disable all interactions:
            >>> chart.set_user_interactions(None)

            # Restore default interactions:
            >>> chart.set_user_interactions()
            >>> chart.set_user_interactions({})
        """
        return super().set_user_interactions(interactions)
