from __future__ import annotations
import uuid
from lightningchart.utils import convert_color_to_hex
from lightningchart.utils.utils import LegendEntryOptions, LegendOptions
from typing  import Unpack

class Legend:
    """Legend property accessor for chart legends."""
    
    def __init__(self, chart, is_user_legend=False):       
        self.chart = chart
        self.instance = chart.instance
        self.chart_id = chart.id
        self.id = None
        self._tracked_entries = []
        self.is_user_legend = is_user_legend

    def _get_target_id(self):
        """Get the correct ID to use for operations."""
        return self.id if (self.is_user_legend and self.id) else self.chart_id

    def set_options(self, **kwargs: Unpack[LegendOptions]):
        """Set legend options.
        
        Args:
            visible (bool): Whether legend should be visible
            position: Legend position (LegendPosition enum or custom position dict)
            title (str): Legend title
            title_font (dict): Title font settings
            title_fill_style: Title color/fill style
            orientation: Legend orientation
            render_on_top (bool): Whether to render legend on top of chart
            background_visible (bool): Whether background should be visible
            background_fill_style: Background fill style
            background_stroke_style: Background stroke style
            padding: Legend content padding
            margin_inner: Margin from chart to legend
            margin_outer: Margin from legend to chart edge. marginOuter might only be visible with certain positions or when the legend is at chart edges.
            entry_margin: Margin between legend entries
            auto_hide_threshold (float): Auto-hide threshold (0.0-1.0)
            add_entries_automatically (bool): Whether to add entries automatically
            entries (dict): Default entry options
        
        Returns:
            The chart instance for fluent interface.
        
        Examples:
            Basic chart with simple legend
            >>> chart.legend.set_options(
            ...     visible=True,
            ...     title='My Legend',
            ...     position={'x': 200, 'y': 300, 'origin': 'LeftTop'},                
            ...     orientation='Horizontal',
            ... )

            Styled legend with background and custom entries
            >>> chart.legend.set_options(
            ...     visible=True,
            ...     title='My Legend',
            ...     background_visible=True,
            ...     background_fill_style="#E08585",
            ...     background_stroke_style={'thickness': 2, 'color': "#F054D3"},
            ...     entries={
            ...         'button_shape': 'Triangle',
            ...         'button_size': 20,
            ...         'button_fill_style': '#00FF00',
            ...         'button_stroke_style': {'thickness': 5, 'color': '#000000'},                    
            ...     }
            ... )
        """
        options = {}
        
        orientation_map = {
            'Horizontal': 'Horizontal',
            'Vertical': 'Vertical'
        }

        if 'visible' in kwargs:
            options['visible'] = kwargs['visible']
        if 'position' in kwargs:
            position = kwargs['position']
            if isinstance(position, str):
                options['position'] = position
            elif hasattr(position, 'value'):
                options['position'] = position.value
            else:
                options['position'] = position
        if 'title' in kwargs:
            options['title'] = kwargs['title']
        if 'title_font' in kwargs:
            options['titleFont'] = kwargs['title_font']
        if 'title_fill_style' in kwargs:
            options['titleFillStyle'] = convert_color_to_hex(kwargs['title_fill_style'])
        if 'orientation' in kwargs:
            orientation = kwargs['orientation']
            if isinstance(orientation, str):
                options['orientation'] = orientation_map.get(orientation, orientation)
            elif hasattr(orientation, 'value'):
                options['orientation'] = orientation.value
            else:
                options['orientation'] = orientation
        if 'render_on_top' in kwargs:
            options['renderOnTop'] = kwargs['render_on_top']
            
        if 'background_visible' in kwargs:
            options['backgroundVisible'] = kwargs['background_visible']
        if 'background_fill_style' in kwargs:
            options['backgroundFillStyle'] = convert_color_to_hex(kwargs['background_fill_style'])
        if 'background_stroke_style' in kwargs:
            stroke = kwargs['background_stroke_style']
            if isinstance(stroke, dict) and 'color' in stroke:
                stroke = {**stroke, 'color': convert_color_to_hex(stroke['color'])}
            options['backgroundStrokeStyle'] = stroke
            
        if 'padding' in kwargs:
            options['padding'] = kwargs['padding']
        if 'margin_inner' in kwargs:
            options['marginInner'] = kwargs['margin_inner']
        if 'margin_outer' in kwargs:
            options['marginOuter'] = kwargs['margin_outer']
        if 'entry_margin' in kwargs:
            options['entryMargin'] = kwargs['entry_margin']
        if 'auto_hide_threshold' in kwargs:
            options['autoHideThreshold'] = kwargs['auto_hide_threshold']
        if 'add_entries_automatically' in kwargs:
            options['addEntriesAutomatically'] = kwargs['add_entries_automatically']
            
        if 'entries' in kwargs:
            entries_options = {}
            entries = kwargs['entries']
            
            if 'button_shape' in entries:
                entries_options['buttonShape'] = entries['button_shape']
            if 'button_size' in entries:
                entries_options['buttonSize'] = entries['button_size']
            if 'button_fill_style' in entries:
                entries_options['buttonFillStyle'] = convert_color_to_hex(entries['button_fill_style'])
            if 'button_stroke_style' in entries:
                bs = entries['button_stroke_style']
                if isinstance(bs, dict) and 'color' in bs:
                    bs = {**bs, 'color': convert_color_to_hex(bs['color'])}
                entries_options['buttonStrokeStyle'] = bs
            if 'button_rotation' in entries:
                entries_options['buttonRotation'] = entries['button_rotation']
            if 'text' in entries:
                entries_options['text'] = entries['text']
            if 'text_font' in entries:
                entries_options['textFont'] = entries['text_font']
            if 'text_fill_style' in entries:
                entries_options['textFillStyle'] = convert_color_to_hex(entries['text_fill_style'])
            if 'show' in entries:
                entries_options['show'] = entries['show']
            if 'match_style_exactly' in entries:
                entries_options['matchStyleExactly'] = entries['match_style_exactly']
                
            if 'lut_length' in entries:
                entries_options['lutLength'] = entries['lut_length']
            if 'lut_thickness' in entries:
                entries_options['lutThickness'] = entries['lut_thickness']
            if 'lut_display_proportional_steps' in entries:
                entries_options['lutDisplayProportionalSteps'] = entries['lut_display_proportional_steps']
                
            options['entries'] = entries_options

        self.instance.send(self._get_target_id(), 'setLegendOptions', {'options': options})
        return self.chart

    def set_entry_options(self, component, **kwargs: Unpack[LegendEntryOptions]):
        """Set options for specific legend entry.
        
        Args:
            component: The series/component to configure
            show (bool): Whether to show entry
            text (str): Entry text
            button_shape (str): 'Arrow', 'Diamond', 'Plus', 'Triangle', 'Circle', 'Square', 'Cross', 'Minus' and 'Star'.
            button_size (int | dict): Size in pixels or {'x': 20, 'y': 15}.
            button_fill_style: Button fill style
            button_stroke_style: Button stroke style
            button_rotation: Button rotation in degrees
            text_font (dict): Text font settings
            text_fill_style: Text fill style
            match_style_exactly (bool): Whether to match component style exactly
            highlight (bool): Whether highlighting on hover is enabled.
            lut: LUT element (None to disable)
            lut_length: LUT length in pixels
            lut_thickness: LUT thickness in pixels
            lut_display_proportional_steps (bool): LUT step display mode
            lut_step_value_formatter: Callback function for LUT value formatting.
        
        Returns:
            The chart instance for fluent interface.

        Examples:
            Configure individual entries
            >>> chart.legend.set_entry_options(
            ...     series, 
            ...     text="Primary Data",
            ...     button_size=5,
            ...     show=True
            ... )

            Custome legend entries
            >>> chart.legend.set_entry_options(
            ...     series,
            ...     show=True,
            ...     text="Series A — Custom",
            ...     button_shape='Triangle',
            ...     button_size=25,
            ...     button_fill_style="#CB5B15",
            ...     button_stroke_style={'thickness': 3, 'color': '#003300'},
            ...     button_rotation=45,
            ...     text_font={'size': 18, 'style': 'italic'},
            ...     text_fill_style='#0000FF',
            ...     match_style_exactly=False,
            ... )
        """
        options = {}
        
        if 'show' in kwargs:
            options['show'] = kwargs['show']
        if 'text' in kwargs:
            options['text'] = kwargs['text']
        if 'button_shape' in kwargs:
            options['buttonShape'] = kwargs['button_shape']
        if 'button_size' in kwargs:
            options['buttonSize'] = kwargs['button_size']
        if 'button_fill_style' in kwargs:
            options['buttonFillStyle'] = convert_color_to_hex(kwargs['button_fill_style'])
        if 'button_stroke_style' in kwargs:
            bs = kwargs['button_stroke_style']
            if isinstance(bs, dict) and 'color' in bs:
                bs = {**bs, 'color': convert_color_to_hex(bs['color'])}
            options['buttonStrokeStyle'] = bs
        if 'button_rotation' in kwargs:
            options['buttonRotation'] = kwargs['button_rotation']
        if 'text_font' in kwargs:
            options['textFont'] = kwargs['text_font']
        if 'text_fill_style' in kwargs:
            options['textFillStyle'] = convert_color_to_hex(kwargs['text_fill_style'])
        if 'match_style_exactly' in kwargs:
            options['matchStyleExactly'] = kwargs['match_style_exactly']
        if 'lut' in kwargs:
            options['lut'] = kwargs['lut']
        if 'lut_length' in kwargs:
            options['lutLength'] = kwargs['lut_length']
        if 'lut_thickness' in kwargs:
            options['lutThickness'] = kwargs['lut_thickness']
        if 'lut_display_proportional_steps' in kwargs:
            options['lutDisplayProportionalSteps'] = kwargs['lut_display_proportional_steps']

        entry_id = component.id
        if not any(e['component_id'] == entry_id for e in self._tracked_entries):
            self._tracked_entries.append({'component_id': entry_id, 'component': component})

        self.instance.send(self._get_target_id(), 'setLegendEntryOptions',
                           {'component': component.id, 'options': options})
        return self.chart

    def get_options(self):
        """Get current legend options."""
        return self.instance.get(self._get_target_id(), 'getLegendOptions', {})

    def get_entry_options(self, component):
        """Get options for specific entry."""
        return self.instance.get(self._get_target_id(), 'getLegendEntryOptions', {'component': component.id})

    def add(self, component, options: LegendEntryOptions=None) :
        """Add standalone legend entry.
        
        Args:
            component: The series/component to configure
            options (dict): Legend entry options            
            
        Examples:
            Add standalone legend entry
            >>> legend = chart.add_legend()
            ... series = chart.add_line_series()
            ... legend.add(
            ...     component=series,
            ...     options={
            ...     'text': 'Series A',
            ...     'button_shape': 'Triangle',
            ...     'button_fill_style': '#00FF00'
            ... })
        """
        options = options or {}
        component_id = component.id if component is not None else None
        converted_options = {}
        if 'text' in options:
            converted_options['text'] = options['text']
        if 'button_shape' in options:
            converted_options['buttonShape'] = options['button_shape']
        if 'button_size' in options:
            converted_options['buttonSize'] = options['button_size']
        if 'button_fill_style' in options:
            converted_options['buttonFillStyle'] = convert_color_to_hex(options['button_fill_style'])
        if 'button_stroke_style' in options:
            converted_options['buttonStrokeStyle'] = options['button_stroke_style']
        if 'button_rotation' in options:
            converted_options['buttonRotation'] = options['button_rotation']
        if 'text_font' in options:
            converted_options['textFont'] = options['text_font']
        if 'text_fill_style' in options:
            converted_options['textFillStyle'] = convert_color_to_hex(options['text_fill_style'])
        if 'show' in options:
            converted_options['show'] = options['show']
        if 'match_style_exactly' in options:
            converted_options['matchStyleExactly'] = options['match_style_exactly']
        if 'highlight' in options:
            converted_options['highlight'] = options['highlight']
        if 'lut' in options:
            converted_options['lut'] = options['lut']
        if 'lut_length' in options:
            converted_options['lutLength'] = options['lut_length']
        if 'lut_thickness' in options:
            converted_options['lutThickness'] = options['lut_thickness']
        if 'lut_display_proportional_steps' in options:
            converted_options['lutDisplayProportionalSteps'] = options['lut_display_proportional_steps']
            
        entry_id = str(uuid.uuid4())
        message = {            
            'component': component_id, 
            'options': converted_options,
            'entryId': entry_id,
        }            
            
        self.instance.send(self._get_target_id(), 'legendAdd', message)       
        return {'type': 'standalone_entry', 'id': entry_id}

    def remove(self, component):
        """Remove component from legend."""
        if isinstance(component, dict) and component.get('type') == 'standalone_entry':
            self.instance.send(self._get_target_id(), 'legendRemove', {'entryId': component['id']})
        else:
            self.instance.send(self._get_target_id(), 'legendRemove', {'component': component.id})
        return self.chart

    def clear(self):
        """Clear all legend entries."""
        self.instance.send(self._get_target_id(), 'legendClear', {})
        return self.chart
    
    def dispose(self):
        """Permanently destroy the legend.
        
        Returns:
            The chart instance for fluent interface.
        """
        self.instance.send(self._get_target_id(), 'legendDispose', {})
        return self.chart

    def get_entries(self):
        """Get tracked legend entries."""
        return self._tracked_entries


