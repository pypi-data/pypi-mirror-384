from __future__ import annotations
from typing import Optional


from lightningchart import conf, Themes
from lightningchart.charts import GeneralMethods, TitleMethods, Chart
from lightningchart.instance import Instance
from lightningchart.series import ComponentWithPaletteColoring
from lightningchart.utils import convert_to_dict, convert_color_to_hex
from lightningchart.utils.utils import LegendOptions, apply_post_legend_config, build_legend_config


class MapChart(GeneralMethods, TitleMethods, ComponentWithPaletteColoring):
    def __init__(
        self,
        map_type: str = 'World',
        theme: Themes = Themes.Light,
        theme_scale: float = 1.0,
        title: str = None,
        license: str = None,
        license_information: str = None,
        html_text_rendering: bool = True,
        legend: Optional[LegendOptions] = None,
    ):
        """Chart class for visualizing a Map of a selected part of the world. Defaults to the entire world.

        Args:
            map_type (str): "Africa" | "Asia" | "Australia" | "Canada" | "Europe" | "NorthAmerica" | "SouthAmerica" | "USA" | "World" |
                    "NorthAmerica" | "SouthAmerica" | "USA" | "World"
            theme (Themes): Overall theme of the chart.
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
            Reference to MapChart class.

        Examples:
            >>> Basic chart with simple legend
            ... chart = lc.MapChart(
            ... title='My Chart',
            ... legend={
            ... 'visible': True,
            ... 'position': 'RightCenter',
            ... 'title': "Data Series"
            ... }
            ... )

            >>> Styled legend with background and custom entries
            ... chart = lc.MapChart(
            ... title='Styled Chart',
            ... legend={
            ... 'visible': True,
            ... 'position': 'RightCenter',
            ... 'background_visible': True,
            ... 'background_fill_style': "#e01212",
            ... 'background_stroke_style': {'thickness': 3, 'color': '#003300'},
            ... 'entries': {
            ... 'button_shape': 'Circle',
            ... 'button_size': 20,
            ... 'text_font': {'size': 16},
            ... 'text_fill_style': "#000080"
            ... }
            ... }
            ... )

            >>> Custom positioned legend
            ... chart = lc.MapChart(
            ... title='Custom Legend',
            ... legend={
            ... 'position': 'RightCenter',
            ... 'orientation': 'Horizontal',
            ... 'render_on_top': True,
            ... 'padding': 15,
            ... 'margin_inner': 10
            ... }
            ... )
        """
        map_types = (
            'Africa',
            'Asia',
            'Australia',
            'Canada',
            'Europe',
            'NorthAmerica',
            'SouthAmerica',
            'USA',
            'World',
        )
        if map_type not in map_types:
            raise ValueError(f"Expected map_type to be one of {map_types}, but got '{map_type}'.")

        instance = Instance()
        Chart.__init__(self, instance)

        
        legend_config = build_legend_config(legend)

        self.instance.send(
            self.id,
            'mapChart',
            {
                'mapType': map_type,
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
    
    
    def invalidate_region_values(self, region_values: list[dict]):
        """Invalidate numeric values associated with each region of the Map.

        Args:
            region_values (list[dict]): List of {"ISO_A3": string, "value": number} dictionaries.

        Returns:
            The instance of the class for fluent interface.
        """
        region_values = convert_to_dict(region_values)

        self.instance.send(self.id, 'invalidateRegionValues', {'values': region_values})
        return self

    def set_highlight_on_hover(self, enabled: bool):
        """Set highlight on mouse hover enabled or disabled.

        Args:
            enabled (bool): Boolean flag.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setHighlightOnHover', {'enabled': enabled})
        return self

    def set_outlier_region_color(self, color: any):
        """Set color of outlier regions (parts of map that are visible, but not interactable with active map type).

        Args:
            color (Color): Color of outlier regions.

        Returns:
            The instance of the class for fluent interface.
        """
        color = convert_color_to_hex(color) if color is not None else None

        self.instance.send(self.id, 'setOutlierRegionFillStyle', {'color': color})
        return self

    def set_outlier_region_stroke(self, thickness: int | float, color: any = None):
        """Set stroke of outlier regions (parts of map that are visible, but not interactable with active map type).

        Args:
            thickness (int | float): Thickness of the stroke.
            color (Color): Color of the stroke.

        Returns:
            The instance of the class for fluent interface.
        """
        color = convert_color_to_hex(color) if color is not None else None

        self.instance.send(
            self.id,
            'setOutlierRegionStrokeStyle',
            {'thickness': thickness, 'color': color},
        )
        return self

    def set_separate_region_color(self, color: any):
        """Set color of separate regions, which are visual components surrounding areas such as Alaska and Hawaii.

        Args:
            color (Color): Color of separate regions.

        Returns:
            The instance of the class for fluent interface.
        """
        color = convert_color_to_hex(color) if color is not None else None

        self.instance.send(self.id, 'setSeparateRegionFillStyle', {'color': color})
        return self

    def set_separate_region_stroke(self, thickness: int | float, color: any = None):
        """Set stroke of Separate regions, which are visual components surrounding areas such as Alaska and Hawaii.

        Args:
            thickness (int | float): Thickness of the stroke.
            color (Color): Color of the stroke.

        Returns:
            The instance of the class for fluent interface.
        """
        color = convert_color_to_hex(color) if color is not None else None

        self.instance.send(
            self.id,
            'setSeparateRegionStrokeStyle',
            {'thickness': thickness, 'color': color},
        )
        return self

    def set_stroke(self, thickness: int | float, color: any = None):
        """Set Stroke style of Map regions.

        Args:
            thickness (int | float): Thickness of the stroke.
            color (Color): Color of the stroke.

        Returns:
            The instance of the class for fluent interface.
        """
        color = convert_color_to_hex(color) if color is not None else None

        self.instance.send(
            self.id,
            'setStrokeStyle',
            {'thickness': thickness, 'color': color},
        )
        return self


class MapChartDashboard(MapChart):
    def __init__(
        self,
        instance: Instance,
        dashboard_id: str,
        column: int,
        row: int,
        colspan: int,
        rowspan: int,
        map_type: str= 'World',
        legend: Optional[LegendOptions] = None,
    ):
        Chart.__init__(self, instance)
        legend_config = build_legend_config(legend)
        self.instance.send(
            self.id,
            'createMapChart',
            {
                'db': dashboard_id,
                'column': column,
                'row': row,
                'colspan': colspan,
                'rowspan': rowspan,
                'type': map_type,
                'legendConfig': legend_config,
            },
        )
        apply_post_legend_config(self, legend)
