from __future__ import annotations
from typing import Optional


from lightningchart import conf, Themes
from lightningchart.charts import (
    GeneralMethods,
    ChartWithXYZAxis,
    TitleMethods,
    ChartWithSeries,
)
from lightningchart.instance import Instance
from lightningchart.series.point_series_3d import PointSeries3D
from lightningchart.series.line_series_3d import LineSeries3D
from lightningchart.series.point_line_series_3d import PointLineSeries3D
from lightningchart.series.box_series_3d import BoxSeries3D
from lightningchart.series.surface_grid_series import SurfaceGridSeries
from lightningchart.series.surface_scrolling_grid_series import (
    SurfaceScrollingGridSeries,
)
from lightningchart.series.mesh_model_3d import MeshModel3D
from lightningchart.ui import UserInteractions
from lightningchart.utils import convert_color_to_hex
from lightningchart.utils.utils import LegendOptions, apply_post_legend_config, build_legend_config


class Chart3D(GeneralMethods, TitleMethods, ChartWithXYZAxis, ChartWithSeries, UserInteractions):
    """Chart for visualizing data in a 3-dimensional scene, with camera and light source(s)."""

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
        """Create a 3D Chart.

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
            Reference to 3D Chart class.

        Examples:
            Basic chart with simple legend
            >>> chart = lc.Chart3D(
            ...     title='My Chart',
            ...     legend={
            ...         'visible': True,
            ...         'position': 'RightCenter',
            ...         'title': "Data Series"
            ...     }
            ... )

            Styled legend with background and custom entries
            >>> chart = lc.Chart3D(
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
            >>> chart = lc.Chart3D(
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
            'chart3D',
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
            self.instance.send(self.id, 'setTitle', {'title': title})
        ChartWithXYZAxis.__init__(self)
        
        apply_post_legend_config(self, legend)

    
    def set_animation_zoom(self, enabled: bool = True):
        """Set Chart3D zoom animation enabled.
        When enabled, zooming with mouse wheel or trackpad will include a short animation. This is enabled by default.

        Args:
            enabled (bool): Boolean.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setAnimationZoom', {'enabled': enabled})
        return self

    def set_bounding_box(self, x: int | float = 1.0, y: int | float = 1.0, z: int | float = 1.0):
        """Set the dimensions of the Scenes bounding box. The bounding box is a visual reference that all the data of
        the Chart is depicted inside. The Axes of the 3D chart are always positioned along the sides of the bounding
        box.

        Args:
            x (int | float): Relative ratio of x dimension.
            y (int | float): Relative ratio of y dimension.
            z (int | float): Relative ratio of z dimension.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setBoundingBox', {'x': x, 'y': y, 'z': z})
        return self

    def set_bounding_box_stroke(self, thickness: int | float, color: any = None):
        """Set style of 3D bounding box.

        Args:
            thickness (int | float): Thickness of the bounding box.
            color (Color): Color of the bounding box.

        Returns:
            The instance of the class for fluent interface.
        """
        color = convert_color_to_hex(color) if color is not None else None

        self.instance.send(
            self.id,
            'setBoundingBoxStrokeStyle',
            {'thickness': thickness, 'color': color},
        )
        return self

    def add_point_series(
        self,
        automatic_color_index: int = None,
        render_2d: bool = False,
        individual_lookup_values_enabled: bool = False,
        individual_point_color_enabled: bool = False,
        individual_point_size_axis_enabled: bool = False,
        individual_point_size_enabled: bool = False, 
        legend: Optional[LegendOptions] = None,
    ) -> PointSeries3D:
        """Method for adding a new PointSeries3D to the chart. This series type for visualizing a collection of
        { x, y, z } coordinates by different markers.

        Point Series 3D accepts data of form {x,y,z}

        Args:
            automatic_color_index: Optional index to use for automatic coloring of series.
            render_2d (bool): Defines the rendering type of Point Series. When true, points are rendered by 2D markers.
            individual_lookup_values_enabled (bool): Flag that can be used to enable data points value property on
                top of x, y and z. By default, this is disabled.
            individual_point_color_enabled (bool): Flag that can be used to enable data points color property on top of
                x, y and z. By default, this is disabled.
            individual_point_size_axis_enabled (bool): Flag that can be used to enable data points 'sizeAxisX',
                'sizeAxisY' and 'sizeAxisZ' properties on top of x, y and z. By default, this is disabled.
            individual_point_size_enabled (bool): Flag that can be used to enable data points size property on top of
                x, y and z. By default, this is disabled.
            
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
            Basic area range series
            >>> series1 = chart3d.add_point_series()

            Hidden from legend
            >>> series2 = chart3d.add_point_series(show=False)

            Custom legend appearance
            >>> series3 = chart3d.add_point_series(
            ...     text="Temperature Range",
            ...     button_shape='Square',
            ...     button_size=18,
            ...     button_fill_style='#66ccff',
            ...     text_font={'size': 12, 'weight': 'bold'}
            ... )
        """
        series = PointSeries3D(
            chart=self,
            automatic_color_index=automatic_color_index,
            render_2d=render_2d,
            individual_lookup_values_enabled=individual_lookup_values_enabled,
            individual_point_color_enabled=individual_point_color_enabled,
            individual_point_size_axis_enabled=individual_point_size_axis_enabled,
            individual_point_size_enabled=individual_point_size_enabled, 
            legend=legend,
        )
        self.series_list.append(series)
        return series

    def add_line_series(
        self, 
        automatic_color_index: int = None,
        legend: Optional[LegendOptions] = None,
    ) -> LineSeries3D:
        """Method for adding a new LineSeries3D to the chart. This Series type for visualizing a collection of
        { x, y, z } coordinates by a continuous line stroke.

        Line Series 3D accepts data of form {x,y,z}
        Args:
            automatic_color_index: Optional index to use for automatic coloring of series.
            
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
            Basic area range series
            >>> series1 = chart3d.add_line_series()

            Hidden from legend
            >>> series2 = chart3d.add_line_series(show=False)

            Custom legend appearance
            >>> series3 = chart3d.add_line_series(
            ...     text="Temperature Range",
            ...     button_shape='Square',
            ...     button_size=18,
            ...     button_fill_style='#66ccff',
            ...     text_font={'size': 12, 'weight': 'bold'}
            ... )
    
        """
        series = LineSeries3D(chart=self, automatic_color_index=automatic_color_index, legend=legend,)
        self.series_list.append(series)
        return series

    def add_point_line_series(
        self,
        render_2d: bool = False,
        automatic_color_index: int = None,
        individual_lookup_values_enabled: bool = False,
        individual_point_color_enabled: bool = False,
        individual_point_size_axis_enabled: bool = False,
        individual_point_size_enabled: bool = False, 
        legend: Optional[LegendOptions] = None,
    ) -> PointLineSeries3D:
        """Method for adding a new PointLineSeries3D to the chart. This Series type for visualizing a collection of
        { x, y, z } coordinates by a continuous line stroke and markers.
        
        Point Line Series 3D accepts data of form {x,y,z}

        Args:
            automatic_color_index: Optional index to use for automatic coloring of series.
            render_2d (bool): Defines the rendering type of Point Series. When true, points are rendered by 2D markers.
            individual_lookup_values_enabled (bool): Flag that can be used to enable data points value property on
                top of x, y and z. By default, this is disabled.
            individual_point_color_enabled (bool): Flag that can be used to enable data points color property on top of
                x, y and z. By default, this is disabled.
            individual_point_size_axis_enabled (bool): Flag that can be used to enable data points 'sizeAxisX',
                'sizeAxisY' and 'sizeAxisZ' properties on top of x, y and z. By default, this is disabled.
            individual_point_size_enabled (bool): Flag that can be used to enable data points size property on top of
                x, y and z. By default, this is disabled.
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
            Basic area range series
            >>> series1 = chart3d.add_point_line_series()

            Hidden from legend
            >>> series2 = chart3d.add_point_line_series(show=False)

            Custom legend appearance
            >>> series3 = chart3d.add_point_line_series(
            ...     text="Temperature Range",
            ...     button_shape='Square',
            ...     button_size=18,
            ...     button_fill_style='#66ccff',
            ...     text_font={'size': 12, 'weight': 'bold'}
            ... )
        """
        series = PointLineSeries3D(
            chart=self,
            render_2d=render_2d,
            automatic_color_index=automatic_color_index,
            individual_lookup_values_enabled=individual_lookup_values_enabled,
            individual_point_color_enabled=individual_point_color_enabled,
            individual_point_size_axis_enabled=individual_point_size_axis_enabled,
            individual_point_size_enabled=individual_point_size_enabled,
            legend=legend,
        )
        self.series_list.append(series)
        return series

    def add_box_series(self, automatic_color_index: int = None, legend: Optional[LegendOptions] = None,) -> BoxSeries3D:
        """Create Series for visualization of large sets of individually configurable 3D Boxes.

        Box Series 3D accepts data of form { xCenter, yCenter, zCenter, xSize, ySize, zSize}

        Args:
            automatic_color_index: Optional index to use for automatic coloring of series.

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
            >>> series1 = chart3d.add_box_series()

            Hidden from legend
            >>> series2 = chart3d.add_box_series(show=False)

            Custom legend appearance
            >>> series3 = chart3d.add_box_series(
            ...     text="Temperature Range",
            ...     button_shape='Square',
            ...     button_size=18,
            ...     button_fill_style='#66ccff',
            ...     text_font={'size': 12, 'weight': 'bold'}
            ... )     
        """
        series = BoxSeries3D(chart=self, automatic_color_index=automatic_color_index, legend=legend,)
        self.series_list.append(series)
        return series

    def add_surface_grid_series(
        self,
        columns: int,
        rows: int,
        data_order: str = 'columns',
        automatic_color_index: int = None,
        legend: Optional[LegendOptions] = None,
    ) -> SurfaceGridSeries:
        """Add a Series for visualizing a Surface Grid with a _static column and grid count.

        Surface Grid Series accepts data in the form of two-dimensional matrix of correct size that includes
        integers or floats.

        Args:
            automatic_color_index: Optional index to use for automatic coloring of series.
            columns (int): Amount of cells along X axis.
            rows (int): Amount of cells along Y axis.
            data_order (str): "columns" | "rows" - Specify how to interpret surface grid values supplied by user.

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
            Reference to Surface Grid Series class.
            
        Examples:
            Basic area range series
            >>> series1 = chart3d.add_surface_grid_series()

            Hidden from legend
            >>> series2 = chart3d.add_surface_grid_series(show=False)

            Custom legend appearance
            >>> series3 = chart3d.add_surface_grid_series(
            ...     text="Temperature Range",
            ...     button_shape='Square',
            ...     button_size=18,
            ...     button_fill_style='#66ccff',
            ...     text_font={'size': 12, 'weight': 'bold'}
            ... )

        """
        series = SurfaceGridSeries(chart=self, columns=columns, automatic_color_index=automatic_color_index, rows=rows, data_order=data_order, legend=legend,)
        self.series_list.append(series)
        return series

    def add_surface_scrolling_grid_series(
        self,
        columns: int,
        rows: int,
        scroll_dimension: str = 'columns',
        automatic_color_index: int = None,
        legend: Optional[LegendOptions] = None,
    ) -> SurfaceScrollingGridSeries:
        """Add a Series for visualizing a Surface Grid with API for pushing data in a scrolling manner
        (append new data on top of existing data).

        Surface Scrolling Grid Series accepts data in the form of two-dimensional matrix of correct size that includes
        integers or floats.

        Args:
            automatic_color_index: Optional index to use for automatic coloring of series.
            columns (int): Amount of cells along X axis.
            rows (int): Amount of cells along Y axis.
            scroll_dimension (str): "columns" | "rows" - Select scrolling dimension,
                as well as how to interpret grid matrix values supplied by user.

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
            Reference to Surface Scrolling Grid Series class.
            
        Examples:
            Basic area range series
            >>> series1 = chart3d.add_surface_scrolling_grid_series()

            Hidden from legend
            >>> series2 = chart3d.add_surface_scrolling_grid_series(show=False)

            Custom legend appearance
            >>> series3 = chart3d.add_surface_scrolling_grid_series(
            ...     text="Temperature Range",
            ...     button_shape='Square',
            ...     button_size=18,
            ...     button_fill_style='#66ccff',
            ...     text_font={'size': 12, 'weight': 'bold'}
            ... )     
        """
        series = SurfaceScrollingGridSeries(
            chart=self, 
            automatic_color_index=automatic_color_index, 
            columns=columns, 
            rows=rows, 
            scroll_dimension=scroll_dimension, 
            legend=legend,
            )
        
        self.series_list.append(series)
        return series

    def set_camera_automatic_fitting_enabled(self, enabled: bool):
        """Set automatic camera fitting enabled. This is enabled as the default configuration.
        Note that zooming in or out disables it automatically.

        Args:
            enabled (bool): Boolean flag.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setCameraAutomaticFittingEnabled', {'enabled': enabled})
        return self

    def set_camera_location(self, x: int, y: int, z: int):
        """Set the location of camera in World Space, a coordinate system that is not tied to 3D Axes.
        The camera always faces (0, 0, 0) coordinate.
        The light source is always a set distance behind the camera.

        Args:
            x (int): x-coordinate in the range [1, 5]
            y (int): y-coordinate in the range [1, 5]
            z (int): z-coordinate in the range [1, 5]

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setCameraLocation', {'x': x, 'y': y, 'z': z})
        return self

    def add_mesh_model(self, legend: Optional[LegendOptions] = None,):
        """
        3D Series for rendering a 3D object model within a Chart3D.

        Args:            
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
            Reference to Mesh Model Series class.
            
        Examples:
            Basic area range series
            >>> series1 = chart3d.add_mesh_model()

            Hidden from legend
            >>> series2 = chart3d.add_mesh_model(show=False)

            Custom legend appearance
            >>> series3 = chart3d.add_mesh_model(
            ...     text="Temperature Range",
            ...     button_shape='Square',
            ...     button_size=18,
            ...     button_fill_style='#66ccff',
            ...     text_font={'size': 12, 'weight': 'bold'}
            ... )
        """
        mesh_model = MeshModel3D(self, legend=legend,)
        self.series_list.append(mesh_model)
        return mesh_model

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
            Disable all interactions:
            >>> chart.set_user_interactions(None)

            Restore default interactions:
            >>> chart.set_user_interactions()
            ... chart.set_user_interactions({})

            Disable zooming:
            >>> chart.set_user_interactions(
            ...     {
            ...         'zoom': {
            ...             'wheel': {
            ...                 'camera': False,
            ...             },
            ...         },
            ...     }
            ... )
        """
        return super().set_user_interactions(interactions)


class Chart3DDashboard(Chart3D):
    """Class for Chart3D contained in Dashboard."""

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
            'createChart3D',
            {
                'db': dashboard_id,
                'column': column,
                'row': row,
                'colspan': colspan,
                'rowspan': rowspan,
                'legendConfig': legend_config,
            },
        )
        if title:
            self.instance.send(self.id, 'setTitle', {'title': title})
        ChartWithXYZAxis.__init__(self)
        apply_post_legend_config(self, legend)
