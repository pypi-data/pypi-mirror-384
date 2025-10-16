from __future__ import annotations
from typing import Optional

from lightningchart import conf, Themes
from lightningchart.charts import GeneralMethods, Chart
from lightningchart.charts.bar_chart import BarChartDashboard
from lightningchart.charts.chart_3d import Chart3D, Chart3DDashboard
from lightningchart.charts.chart_xy import ChartXY, ChartXYDashboard
from lightningchart.charts.funnel_chart import FunnelChart, FunnelChartDashboard
from lightningchart.charts.gauge_chart import GaugeChart, GaugeChartDashboard
from lightningchart.charts.map_chart import MapChartDashboard
from lightningchart.charts.parallel_coordinate_chart import (
    ParallelCoordinateChartDashboard,
)
from lightningchart.charts.pie_chart import PieChart, PieChartDashboard
from lightningchart.charts.polar_chart import PolarChartDashboard
from lightningchart.charts.pyramid_chart import PyramidChart, PyramidChartDashboard
from lightningchart.charts.spider_chart import SpiderChartDashboard
from lightningchart.charts.zoom_band_chart import ZoomBandChart
from lightningchart.instance import Instance
from lightningchart.utils.utils import LegendOptions


class Dashboard(GeneralMethods):
    """Dashboard is a tool for rendering multiple charts in the same view."""

    def __init__(
        self,
        columns: int,
        rows: int,
        theme: Themes = Themes.Light,
        license: str = None,
        license_information: str = None,
    ):
        """Create a dashboard, i.e., a tool for rendering multiple charts in the same view.

        Args:
            columns (int): The amount of columns in the dashboard.
            rows (int): The amount of rows in the dashboard.
            theme (Themes): Theme of the chart.
            license (str): License key.
        """
        instance = Instance()
        Chart.__init__(self, instance)
        self.charts = []
        self.columns = columns
        self.rows = rows
        instance.send(
            self.id,
            'dashboard',
            {
                'columns': columns,
                'rows': rows,
                'theme': theme.value,
                'license': license or conf.LICENSE_KEY,
                'licenseInformation': license_information or conf.LICENSE_INFORMATION,
            },
        )

    def ChartXY(
        self,
        column_index: int,
        row_index: int,
        column_span: int = 1,
        row_span: int = 1,
        title: str = None,
        legend: Optional[LegendOptions] = None,
    ) -> ChartXY:
        """Create a XY Chart on the dashboard.

        Args:
            column_index (int): Column index of the dashboard where the chart will be located.
            row_index (int): Row index of the dashboard where the chart will be located.
            column_span (int): How many columns the chart will take (X width). Default = 1.
            row_span (int): How many rows the chart will take (Y height). Default = 1.
            title (str): The title of the chart.
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
        Reference to the XY Chart.
        """
        return ChartXYDashboard(
            instance=self.instance,
            dashboard_id=self.id,
            column=column_index,
            row=row_index,
            colspan=column_span,
            rowspan=row_span,
            title=title,
            legend=legend,
        )

    def Chart3D(
        self,
        column_index: int,
        row_index: int,
        column_span: int = 1,
        row_span: int = 1,
        title: str = None,
        legend: Optional[LegendOptions] = None,
    ) -> Chart3D:
        """Create a 3D chart on the dashboard.

        Args:
            column_index (int): Column index of the dashboard where the chart will be located.
            row_index (int): Row index of the dashboard where the chart will be located.
            column_span (int): How many columns the chart will take (X width). Default = 1.
            row_span (int): How many rows the chart will take (Y height). Default = 1.
            title (str): The title of the chart.
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
            Reference to the 3D Chart.
        """
        return Chart3DDashboard(
            instance=self.instance,
            dashboard_id=self.id,
            column=column_index,
            row=row_index,
            colspan=column_span,
            rowspan=row_span,
            title=title,
            legend=legend,
        )

    def ZoomBandChart(
        self,
        chart: ChartXY,
        column_index: int,
        row_index: int,
        column_span: int = 1,
        row_span: int = 1,
        axis_type: 'str' = 'linear',
        orientation: str = 'x',
        use_shared_value_axis: bool = False,
    ) -> ZoomBandChart:
        """Create a Zoom Band Chart on the dashboard.

        Args:
            chart (ChartXY): Reference to XY Chart which the Zoom Band Chart will use.
            column_index (int): Column index of the dashboard where the chart will be located.
            row_index (int): Row index of the dashboard where the chart will be located.
            column_span (int): How many columns the chart will take (X width). Default = 1.
            row_span (int): How many rows the chart will take (Y height). Default = 1.

        Returns:
            Reference to the Zoom Band Chart.
        """
        return ZoomBandChart(
            instance=self.instance,
            dashboard_id=self.id,
            chart_id=chart.id,
            column_index=column_index,
            column_span=column_span,
            row_index=row_index,
            row_span=row_span,
            axis_type=axis_type,
            orientation=orientation,
            use_shared_value_axis=use_shared_value_axis,
        )

    def PieChart(
            self, 
            column_index: int, 
            row_index: int, 
            column_span: int = 1, 
            row_span: int = 1, 
            labels_inside_slices: bool = False,
            legend: Optional[LegendOptions] = None,
        ) -> PieChart:
        """Create a Pie Chart on the dashboard.

        Args:
            column_index (int): Column index of the dashboard where the chart will be located.
            row_index (int): Row index of the dashboard where the chart will be located.
            column_span (int): How many columns the chart will take (X width). Default = 1.
            row_span (int): How many rows the chart will take (Y height). Default = 1.
            title (str): The title of the chart.
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
            Reference to the Pie Chart.
        """
        return PieChartDashboard(
            instance=self.instance,
            dashboard_id=self.id,
            column=column_index,
            row=row_index,
            colspan=column_span,
            rowspan=row_span,
            labelsInsideSlices=labels_inside_slices,
            legend=legend,
        )

    def GaugeChart(
            self, 
            column_index: int, 
            row_index: int, 
            column_span: int = 1, 
            row_span: int = 1
        ) -> GaugeChart:
        """Create a Gauge Chart on the dashboard.

        Args:
            column_index (int): Column index of the dashboard where the chart will be located.
            row_index (int): Row index of the dashboard where the chart will be located.
            column_span (int): How many columns the chart will take (X width). Default = 1.
            row_span (int): How many rows the chart will take (Y height). Default = 1.
            
        Returns:
            Reference to the Gauge Chart.
        """
        return GaugeChartDashboard(
            instance=self.instance,
            dashboard_id=self.id,
            column=column_index,
            row=row_index,
            colspan=column_span,
            rowspan=row_span,
        )

    def FunnelChart(
            self, 
            column_index: int, 
            row_index: int, 
            column_span: int = 1, 
            row_span: int = 1, 
            labels_inside: bool = False,
            legend: Optional[LegendOptions] = None,
        ) -> FunnelChart:
        """Create a Funnel Chart on the dashboard.

        Args:
            column_index (int): Column index of the dashboard where the chart will be located.
            row_index (int): Row index of the dashboard where the chart will be located.
            column_span (int): How many columns the chart will take (X width). Default = 1.
            row_span (int): How many rows the chart will take (Y height). Default = 1.
            labels_inside: If True, labels are placed inside slices. If False, labels are on sides (default).
            Args:
            column_index (int): Column index of the dashboard where the chart will be located.
            row_index (int): Row index of the dashboard where the chart will be located.
            column_span (int): How many columns the chart will take (X width). Default = 1.
            row_span (int): How many rows the chart will take (Y height). Default = 1.
            title (str): The title of the chart.
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
            Reference to the Funnel Chart.
        """
        return FunnelChartDashboard(
            instance=self.instance,
            dashboard_id=self.id,
            column=column_index,
            row=row_index,
            colspan=column_span,
            rowspan=row_span,
            labelsInside=labels_inside,
            legend=legend,
        )

    def PyramidChart(
            self, 
            column_index: int, 
            row_index: int, 
            column_span: int = 1, 
            row_span: int = 1, 
            labels_inside: bool = False,
            legend: Optional[LegendOptions] = None,
        ) -> PyramidChart:
        """Create a Pyramid Chart on the dashboard.

        Args:
            column_index (int): Column index of the dashboard where the chart will be located.
            row_index (int): Row index of the dashboard where the chart will be located.
            column_span (int): How many columns the chart will take (X width). Default = 1.
            row_span (int): How many rows the chart will take (Y height). Default = 1.
            title (str): The title of the chart.
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
            Reference to the Pyramid Chart.
        """
        return PyramidChartDashboard(
            instance=self.instance,
            dashboard_id=self.id,
            column=column_index,
            row=row_index,
            colspan=column_span,
            rowspan=row_span,
            labelsInside=labels_inside,
            legend=legend,
        )

    def PolarChart(
            self, 
            column_index: int, 
            row_index: int, 
            column_span: int = 1, 
            row_span: int = 1,
            legend: Optional[LegendOptions] = None,
        ) -> PolarChartDashboard:
        """Create a Polar Chart on the dashboard.

        Args:
            column_index (int): Column index of the dashboard where the chart will be located.
            row_index (int): Row index of the dashboard where the chart will be located.
            column_span (int): How many columns the chart will take (X width). Default = 1.
            row_span (int): How many rows the chart will take (Y height). Default = 1.
            title (str): The title of the chart.
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
            Reference to the Polar Chart.
        """
        polar_chart = PolarChartDashboard(
            instance=self.instance,
            dashboard_id=self.id,
            column=column_index,
            row=row_index,
            colspan=column_span,
            rowspan=row_span,
            legend=legend,
        )
        self.charts.append(polar_chart)
        return polar_chart

    def BarChart(
        self,
        column_index: int,
        row_index: int,
        column_span: int = 1,
        row_span: int = 1,
        vertical: bool = True,
        axis_type: str = 'linear',
        axis_base: int = 10,
        legend: Optional[LegendOptions] = None,
    ):
        """Create a Bar Chart on the dashboard.

       Args:
            column_index (int): Column index of the dashboard where the chart will be located.
            row_index (int): Row index of the dashboard where the chart will be located.
            column_span (int): How many columns the chart will take (X width). Default = 1.
            row_span (int): How many rows the chart will take (Y height). Default = 1.
            title (str): The title of the chart.
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
            Reference to the Bar Chart.
        """
        return BarChartDashboard(
            instance=self.instance,
            dashboard_id=self.id,
            column=column_index,
            row=row_index,
            colspan=column_span,
            rowspan=row_span,
            vertical=vertical,
            axis_type=axis_type,
            axis_base=axis_base,
            legend=legend,
        )

    def SpiderChart(
            self, 
            column_index: int, 
            row_index: int, 
            column_span: int = 1, 
            row_span: int = 1,
            legend: Optional[LegendOptions] = None,
        ):
        """Create a Spider Chart on the dashboard.

        Args:
            column_index (int): Column index of the dashboard where the chart will be located.
            row_index (int): Row index of the dashboard where the chart will be located.
            column_span (int): How many columns the chart will take (X width). Default = 1.
            row_span (int): How many rows the chart will take (Y height). Default = 1.
            title (str): The title of the chart.
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
            Reference to the Spider Chart
        """
        return SpiderChartDashboard(
            instance=self.instance,
            dashboard_id=self.id,
            column=column_index,
            row=row_index,
            colspan=column_span,
            rowspan=row_span,
            legend=legend,
        )

    def MapChart(
            self, 
            column_index: int, 
            row_index: int, 
            column_span: int = 1, 
            row_span: int = 1, 
            map_type: str='World',
            legend: Optional[LegendOptions] = None,
        ):
        """Create a Map Chart on the dashboard.

        Args:
            column_index (int): Column index of the dashboard where the chart will be located.
            row_index (int): Row index of the dashboard where the chart will be located.
            column_span (int): How many columns the chart will take (X width). Default = 1.
            row_span (int): How many rows the chart will take (Y height). Default = 1.
            title (str): The title of the chart.
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
            Reference to the Map Chart
        """
        return MapChartDashboard(
            instance=self.instance,
            dashboard_id=self.id,
            column=column_index,
            row=row_index,
            colspan=column_span,
            rowspan=row_span,
            map_type=map_type,
            legend=legend,
        )

    def ParallelCoordinateChart(
            self, 
            column_index: int, 
            row_index: int, 
            column_span: int = 1, 
            row_span: int = 1,
            legend: Optional[LegendOptions] = None,          
            ):
        """Create a Parallel Coordinates Chart on the dashboard.

        Args:
            column_index (int): Column index of the dashboard where the chart will be located.
            row_index (int): Row index of the dashboard where the chart will be located.
            column_span (int): How many columns the chart will take (X width). Default = 1.
            row_span (int): How many rows the chart will take (Y height). Default = 1.
            title (str): The title of the chart.
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
            Reference to the Parallel Coordinates Chart
        """
        return ParallelCoordinateChartDashboard(
            instance=self.instance,
            dashboard_id=self.id,
            column=column_index,
            row=row_index,
            colspan=column_span,
            rowspan=row_span,
            legend=legend,
        )
