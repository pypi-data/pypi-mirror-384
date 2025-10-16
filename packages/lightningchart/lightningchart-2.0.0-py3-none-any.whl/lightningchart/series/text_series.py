from __future__ import annotations

from typing import Optional
import uuid
from lightningchart.series import Series, SeriesWithClear, SeriesWithDrawOrder
from lightningchart.ui.axis import Axis
from lightningchart.utils import convert_color_to_hex
from lightningchart.utils.utils import LegendOptions, build_series_legend_options


class TextSeries(SeriesWithClear, SeriesWithDrawOrder, Series):
    """Series that lets user draw large numbers of individual Text objects in a ChartXY."""

    def __init__(
        self,
        chart,
        automatic_color_index: int = None,
        axis_x: Axis = None,
        axis_y: Axis = None,
        legend: Optional[LegendOptions] = None
    ):        
        Series.__init__(self, chart)
        legend_options = build_series_legend_options(legend)

        self.instance.send(
            self.id,
            'addTextSeries',
            {
                'chart': self.chart.id,
                'automaticColorIndex': automatic_color_index,
                'axisX': axis_x,
                'axisY': axis_y,
                'legend': legend_options if legend_options else None
            },
        )

    def add(
        self,
        x: int | float,
        y: int | float,
        text: str = "",
        alignment_x: float = 0,
        alignment_y: float = 1,
    ):
        """Add new text figure to the series.

        Args:
            x: X coordinate for text location.
            y: Y coordinate for text location. 
            text: Text content to display.
            alignment_x: X alignment.
            alignment_y: Y alignment.

        Returns:
            TextFigure instance.
        """
        text_figure = TextFigure(
            self, 
            {
                'x': x,
                'y': y, 
                'text': text,
                'alignmentX': alignment_x,
                'alignmentY': alignment_y
            }
        )
        return text_figure
    
    def set_highlight_on_hover(self, enabled: bool):
        """Set highlight on mouse hover enabled or disabled.

        Args:
            enabled: Boolean flag.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setHighlightOnHover', {'enabled': enabled})
        return self
    
    def set_auto_scrolling_enabled(self, enabled: bool):
        """Set whether series is taken into account with automatic scrolling and fitting.

        Args:
            enabled: Boolean flag.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setAutoScrollingEnabled', {'enabled': enabled})
        return self

    def set_clipping(self, enabled: bool):
        """Configure whether series rendering should be clipped to axes area.

        Args:
            enabled: Boolean flag.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setClipping', {'enabled': enabled})
        return self

class TextFigure:
    """Class representing a visual text figure in the TextSeries."""

    def __init__(self, series: TextSeries, options: dict):
        self.series = series
        self.options = options
        self.instance = series.instance
        self.id = str(uuid.uuid4())
        self.instance.send(
            self.id,
            'addTextFigure',
            {'series': self.series.id, 'options': options},
        )

    def set_text(self, text: str):
        """Set text content.

        Args:
            text: Text content to display.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setText', {'text': text})
        return self

    def set_location(self, x: int | float, y: int | float):
        """Set text location.

        Args:
            x: X coordinate.
            y: Y coordinate.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setLocation', {'x': x, 'y': y})
        return self

    def set_alignment(self, x: float, y: float):
        """Set text alignment.

        Args:
            x: X alignment (0-1).
            y: Y alignment (0-1).

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setAlignment', {'x': x, 'y': y})
        return self
    
    def set_font(
        self,
        size: int | float,
        family: str = 'Segoe UI, -apple-system, Verdana, Helvetica',
    ):
        """Set the font style of the text.

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
            'setFont',
            {'family': family, 'size': size},
        )
        return self

    def set_color(self, color: any):
        """Set text color.

        Args:
            color: Color object or hex string.

        Returns:
            The instance of the class for fluent interface.
        """
        color_hex = convert_color_to_hex(color)
        self.instance.send(self.id, 'setTextColor', {'color': color_hex})
        return self
    
    def get_bounding_box(self):
        """Get bounding box of text figure in axis coordinates.

        Returns:
            Bounding box information.
        """
        result = self.instance.get(self.id, 'getBoundingBox', {})
        return result

    def get_size_pixels(self):
        """Get text size as pixels.

        Returns:
            Text size in pixels.
        """
        result = self.instance.get(self.id, 'getSizePixels', {})
        return result
    
    def get_draggable(self) -> bool:
        """Get whether series is draggable.

        Returns:
            Boolean indicating if series is draggable.
        """
        result = self.instance.get(self.id, 'getDraggable', {})
        return result

    def set_margin(self, *args, **kwargs):
        """Set margin around the object in pixels.

        Usage:
            - `set_margin(5)`: Sets uniform margin for all sides (integer or float).
            - `set_margin(left=10, top=15)`: Sets margin for specific sides only.
            - `set_margin(left=10, top=15, right=20, bottom=25)`: Fully define margin for all sides.

        Args:
            *args: A single numeric value (int or float) for uniform margin on all sides.
            **kwargs: Optional named arguments to specify margin for individual sides:
                - `left` (int or float): Margin for the left side.
                - `right` (int or float): Margin for the right side.
                - `top` (int or float): Margin for the top side.
                - `bottom` (int or float): Margin for the bottom side.

        Returns:
            The instance of the class for fluent interface.
        """
        if len(args) == 1 and isinstance(args[0], (int, float)):
            margin = args[0]
        elif kwargs:
            margin = {}
            for key in ['left', 'right', 'bottom', 'top']:
                if key in kwargs:
                    margin[key] = kwargs[key]
        else:
            raise ValueError(
                'Invalid arguments. Use one of the following formats:\n'
                '- set_margin(5): Uniform margin for all sides.\n'
                '- set_margin(left=10, top=15): Specify individual sides.\n'
                '- set_margin(left=10, top=15, right=20, bottom=25): Full margin definition.'
            )

        self.instance.send(self.id, 'setMargin', {'margin': margin})
        return self
    