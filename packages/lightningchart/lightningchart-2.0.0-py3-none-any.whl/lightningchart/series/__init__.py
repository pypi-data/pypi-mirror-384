from __future__ import annotations

import uuid
from lightningchart import charts
from lightningchart.utils import convert_to_list, convert_to_dict, convert_to_matrix, convert_to_base64, convert_color_to_hex
from lightningchart.utils.utils import _postprocess_readback, _walk_decode


class Series:
    def __init__(self, chart: charts.Chart):
        self.chart = chart
        self.instance = chart.instance
        self.id = str(uuid.uuid4()).split('-')[0]

    def dispose(self):
        """Permanently destroy the component."""
        self.instance.send(self.id, 'dispose')

    def set_visible(self, visible: bool):
        """Set element visibility.

        Args:
            visible (bool): true when element should be visible and false when element should be hidden.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setVisible', {'visible': visible})
        return self

    def set_highlight(self, highlight: bool | int | float):
        """
        Set state of component highlighting.

        Args:
            highlight (bool | int | float): Boolean or number between 0 and 1, where 1 is fully highlighted.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setHighlight', {'highlight': highlight})
        return self

    def set_name(self, name: str):
        """Sets the name of the Component updating attached LegendBox entries.

        Args:
            name (str): Name of the component.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setName', {'name': name})
        return self

    def set_effect(self, enabled: bool):
        """Set theme effect enabled on component or disabled.

        Args:
            enabled: Boolean flag.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setEffect', {'enabled': enabled})
        return self

    def set_cursor_enabled(self, enabled: bool):
        """Configure whether cursors should pick on this particular series or not.

        Args:
            enabled (bool): Boolean flag.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setCursorEnabled', {'enabled': enabled})
        return self

    def set_pointer_events(self, enabled: bool):
        """Set whether element can be target of pointer events or not.
        Disabling pointer events means that the objects below this component can be interacted through it.

        Args:
            enabled (bool): Specifies state of mouse interactions.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setPointerEvents', {'enabled': enabled})
        return self


class SeriesWithoutCursorEnabel:
    def dispose(self):
        """Permanently destroy the component."""
        self.instance.send(self.id, 'dispose')

    def set_visible(self, visible: bool):
        """Set element visibility.

        Args:
            visible (bool): true when element should be visible and false when element should be hidden.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setVisible', {'visible': visible})
        return self

    def set_highlight(self, highlight: bool | int | float):
        """
        Set state of component highlighting.

        Args:
            highlight (bool | int | float): Boolean or number between 0 and 1, where 1 is fully highlighted.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setHighlight', {'highlight': highlight})
        return self

    def set_name(self, name: str):
        """Sets the name of the Component updating attached LegendBox entries.

        Args:
            name (str): Name of the component.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setName', {'name': name})
        return self

    def set_effect(self, enabled: bool):
        """Set theme effect enabled on component or disabled.

        Args:
            enabled: Boolean flag.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setEffect', {'enabled': enabled})
        return self


class ComponentWithPaletteColoring:
    def set_palette_coloring(
        self,
        steps: list[dict],
        look_up_property: str = 'value',
        interpolate: bool = True,
        percentage_values: bool = False,
    ):
        """Define a palette for dynamically looked up fill coloring in the series.

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
            'setPalettedFillStyle',
            {
                'steps': steps,
                'lookUpProperty': look_up_property,
                'interpolate': interpolate,
                'percentageValues': percentage_values,
            },
        )
        return self

    def set_color(self, color: any):
        """Set a color fill for the series.

        Args:
            color (Color): Color of the series.

        Returns:
            The instance of the class for fluent interface.
        """
        color = convert_color_to_hex(color) if color is not None else None

        self.instance.send(self.id, 'setSolidFillStyle', {'color': color})
        return self

    def set_empty_color_fill(self):
        """Set empty color fill for the series.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setEmptyFillStyle', {})
        return self


class ComponentWithPointPaletteColoring:
    def set_palette_point_coloring(
        self,
        steps: list[dict[str, any]],
        look_up_property: str = 'value',
        interpolate: bool = True,
        percentage_values: bool = False,
    ):
        """Define a palette for dynamically looked up fill coloring in the series.

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
            'setPalettedPointFillStyle',
            {
                'steps': steps,
                'lookUpProperty': look_up_property,
                'interpolate': interpolate,
                'percentageValues': percentage_values,
            },
        )
        return self


class ComponentWithLinePaletteColoring:
    def set_palette_line_coloring(
        self,
        steps: list[dict],
        look_up_property: str = 'value',
        interpolate: bool = True,
        percentage_values: bool = False,
    ):
        """Define a palette for dynamically looked up fill coloring in the series.

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
            'setPalettedStrokeStyle',
            {
                'steps': steps,
                'lookUpProperty': look_up_property,
                'interpolate': interpolate,
                'percentageValues': percentage_values,
            },
        )
        return self

class ComponentWithRangePaletteColoring:
    def set_low_palette_coloring(
        self,
        steps: list[dict[str, any]],
        look_up_property: str = 'value',
        interpolate: bool = True,
        percentage_values: bool = False,
    ):
        """Define a palette for dynamically looked up fill coloring in the series.

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
            'setLowPalettedFillStyle',
            {
                'steps': steps,
                'lookUpProperty': look_up_property,
                'interpolate': interpolate,
                'percentageValues': percentage_values,
            },
        )
        return self

    def set_high_palette_coloring(
        self,
        steps: list[dict[str, any]],
        look_up_property: str = 'value',
        interpolate: bool = True,
        percentage_values: bool = False,
    ):
        """Define a palette for dynamically looked up fill coloring in the series.

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
            'setHighPalettedFillStyle',
            {
                'steps': steps,
                'lookUpProperty': look_up_property,
                'interpolate': interpolate,
                'percentageValues': percentage_values,
            },
        )
        return self


class PointLineAreaSeries(Series, ComponentWithPointPaletteColoring, ComponentWithLinePaletteColoring):
    def append_json(
            self, 
            data_array, 
            whitelist=None, 
            blacklist=None, 
            start=None, 
            step=None
            ):
        """Add several samples from dictionaries/JSON objects.
        
        Args:
            data_array: Array of dictionaries representing samples
            whitelist: Optional list of property names to include.
            blacklist: Optional list of property names to exclude.
            start: Optional start index.
            step: Optional step value.

        Examples:
            Basic x/y coordinates
            >>>  series = chart.add_point_series()
            ...  data = [
            ...      {"x": 0, "y": 10},
            ...      {"x": 1, "y": 15},
            ...      {"x": 2, "y": 12}
            ...  ]
            ...  series.append_json(data)
            
            Per-point colors and sizes (requires data mapping)
            >>>  series = chart.add_point_series(colors=True, sizes=True)
            ...  series.set_individual_point_color_enabled(True)
            ...  series.set_data_mapping({
            ...      'x': 'timestamp',
            ...      'y': 'temperature',
            ...      'color': 'color',
            ...      'size': 'size'
            ...  })
            ...  data = [
            ...      {"timestamp": 0, "temperature": 20, "color": "#ff0000", "size": 15},
            ...      {"timestamp": 1, "temperature": 25, "color": "#00ff00", "size": 18},
            ...      {"timestamp": 2, "temperature": 22, "color": "#0000ff", "size": 12}
            ...  ]
            ...  series.append_json(data)
            
            Using custom property names with mapping
            >>>  series = chart.add_point_series()
            ...  series.set_data_mapping({'x': 'time', 'y': 'value'})
            ...  data = [
            ...      {"time": 1000, "value": 42, "label": "Point A"},
            ...     {"time": 2000, "value": 55, "label": "Point B"}
            ...  ]
            ...  series.append_json(data)
            
            Using whitelist to include only specific properties
            >>>  series = chart.add_point_series()
            ...  data = [
            ...      {"x": 0, "y": 10, "unwanted": 999, "spam": "ignore"},
            ...      {"x": 1, "y": 15, "unwanted": 888, "spam": "ignore"}
            ...  ]
            ...  series.append_json(data, whitelist=['x', 'y'])
            
            Using blacklist to exclude unwanted properties
            >>>  series = chart.add_point_series()
            ...  data = [
            ...      {"x": 0, "y": 10, "debug_info": "test", "internal_id": 123},
            ...      {"x": 1, "y": 15, "debug_info": "test", "internal_id": 456}
            ...  ]
            ...  series.append_json(data, blacklist=['debug_info', 'internal_id'])
            
            Using start/step for automatic indexing
            >>>  series = chart.add_point_series()
            ...  series.set_data_mapping({'x': 'index', 'y': 'value'})
            ...  data = [
            ...      {"value": 10},
            ...      {"value": 15},
            ...      {"value": 12}
            ...  ]
            Auto-generate x values: 100, 105, 110
            >>>  series.append_json(data, start=100, step=5)
        """
        data_array = convert_to_dict(data_array)
        processed_array = []
        for item in data_array:
            processed_item = {}
            for key, value in item.items():
                if key.lower() == 'color' and value is not None:
                    processed_item[key] = convert_color_to_hex(value)
                else:
                    processed_item[key] = value
            processed_array.append(processed_item)
        self.instance.send(self.id, 'appendJSON', {
            'array': processed_array,
            'whitelist': whitelist,
            'blacklist': blacklist, 
            'start': start,
            'step': step
        })

    def set_data_mapping(self, mapping):
        """Set data mapping for x, y coordinates. Data mapping specifies how data properties of the schema should be used.
        
        Args:
            mapping: Dict like {'x': 'timestamp', 'y': 'value'}
        """
        self.instance.send(self.id, 'setDataMapping', convert_to_dict(mapping))
        return self


    def append_sample(
        self,
        sample: dict = None,
        x: int | float | str = None,
        y: int | float = None,
        lookup_value: int | float = None,
        id: int | float = None,
        size: int | float = None,
        rotation: int | float = None,
        color: str = None,
        blacklist: list[str] = None,
        whitelist: list[str] = None,
        start: int | float = None,
        step: int | float = None,
    ):
        """Add one sample to data set.

        Args:
            sample (dict): Sample data as dictionary (e.g., {'x': 0, 'y': 10})
            x (int | float | str): Single x value
            y (int | float): Single y value  
            lookup_value (int | float): Single lookup value
            id (int | float): Single id
            size (int | float): Single size value
            rotation (int | float): Single rotation value
            color (str): Single HEX color value
            blacklist (list[str]): Properties to exclude
            whitelist (list[str]): Properties to include only
            start (int | float): Starting value for auto-increment
            step (int | float): Step value for auto-increment

        Examples:
            Individual parameters:
            >>>  series.append_sample(x=0, y=10, color='#ff0000', size=15, rotation=45, lookup_value=0.8, id=1)
            
            Dictionary format:
            >>>  series.append_sample({'x': 1, 'y': 15, 'color': '#00ff00', 'size': 20, 'rotation': 90, 'lookupValue': 0.6, 'id': 2})
            
            Mixed format (dict + individual):
            >>>  series.append_sample({'x': 2, 'y': 12}, color='#0000ff', size=10)
            
            hitelist filtering (only include specified properties):
            >>>  series.append_sample(
            ...      {'x': 3, 'y': 18, 'color': '#ffff00', 'size': 25, 'extraData': 999},
            ...      whitelist=['x', 'y', 'color']
            ...  )
            
            Blacklist filtering (exclude specified properties):
            >>>  series.append_sample(
            ...      {'x': 4, 'y': 8, 'color': '#ff00ff', 'size': 30, 'rotation': 180},
            ...      blacklist=['size']
            ...  )
            
            Auto-increment with start/step:
            >>>  series = chart.add_point_series(
            ...  schema={
            ...          'x': {'auto': True, 'pattern': 'progressive'},  # Auto-increment x
            ...           'temperature': {}
            ...       }
            ...   )
            ...   series.set_data_mapping({'x': 'x', 'y': 'temperature'})            
            ...   series.append_sample({'temperature': 25}, start=5, step=0.5)
        """
        if sample is None:
            sample = {}
            if x is not None: 
                sample['x'] = x
            if y is not None: 
                sample['y'] = y
            if lookup_value is not None: 
                sample['lookupValue'] = lookup_value
            if id is not None: 
                sample['id'] = id
            if size is not None: 
                sample['size'] = size
            if rotation is not None: 
                sample['rotation'] = rotation
            if color is not None: 
                sample['color'] = color

        if 'color' in sample and sample['color'] is not None:
                sample['color'] = convert_color_to_hex(sample['color'])
        
        opts = {}
        if blacklist is not None: 
            opts['blacklist'] = blacklist
        if whitelist is not None: 
            opts['whitelist'] = whitelist  
        if start is not None: 
            opts['start'] = start
        if step is not None: 
            opts['step'] = step
        
        payload = {'sample': sample}
        if opts: 
            payload['opts'] = opts
        
        self.instance.send(self.id, 'appendSample', payload)
        return self
    
    
    def append_samples(
        self,
        samples: dict = None,
        count: int | float = None,
        offset: int | float = None,
        offset_colors: int | float = None,
        offset_ids: int | float = None,
        offset_lookup_values: int | float = None,
        offset_rotations: int | float = None,
        offset_sizes: int | float = None,
        start: int | float = None,
        step: int | float = None,
        **kwargs
    ):
        """Add a list of samples to data set.
        
        Args:
            samples (dict): Dictionary of data properties (e.g., {'xValues': [...], 'yValues': [...]})
            count (int | float): Number of samples to read from input arrays
            offset (int | float): Start reading from this index in input arrays
            offset_colors (int | float): Start reading colors from this index
            offset_ids (int | float): Start reading ids from this index
            offset_lookup_values (int | float): Start reading lookup values from this index
            offset_rotations (int | float): Start reading rotations from this index
            offset_sizes (int | float): Start reading sizes from this index
            start (int | float): Starting X value for progressive data
            step (int | float): X increment for progressive data
            **kwargs: Multiple parameter formats supported:
            
                Coordinates: x, y, x_values, y_values
                Colors: color, colors  
                Sizes: size, sizes
                Rotations: rotation, rotations
                Lookup values: lookup, lookup_value, lookup_values
                IDs: ids
        
        Returns:
            The instance for fluent interface.
        
        Examples:
            Basic usage with coordinate arrays:
            >>>  series.append_samples({
            ...      'xValues': [0, 1, 2], 
            ...      'yValues': [10, 15, 12]
            ...  })
            
            With color array (must match data length):
            >>>  series.append_samples({
            ...      'xValues': [0, 1, 2], 
            ...      'yValues': [10, 15, 12],
            ...      'colors': ['#ff0000', '#00ff00', '#0000ff']
            ...  })
            
            Progressive data (automatic X values):
            >>>  series.append_samples(
            ...      {'yValues': [10, 15, 12]},
            ...      start=0, step=1
            ...  )
            
            Multiple symmetric properties:
            >>>  series.append_samples({
            ...      'xValues': [0, 1, 2],
            ...      'yValues': [10, 15, 12],
            ...      'sizes': [5, 8, 6],
            ...      'ids': [100, 101, 102]
            ...  })

            Single color for all points:
            >>>  series.append_samples({
            ...      'x': [0, 1, 2], 
            ...      'y': [0, 10, 5],
            ...      'colors': '#ff0000'
            ...  })

            Using list:
            >>>  series.append_samples(
            ...      x = [0, 1, 2], 
            ...      y=[10, 15, 12],
            ...      colors=['#ff0000', '#00ff00', '#0000ff']
            ...  )

            With rotations and lookup values:
            >>>  series.append_samples({
            ...      'xValues': [0, 1, 2, 3],
            ...      'yValues': [10, 15, 12, 18],
            ...      'rotations': [0, 45, 90, 135],
            ...      'lookupValues': [0.1, 0.5, 0.8, 0.3]
            ...  })
            
            Using offset to slice arrays:
            >>>  series.append_samples(samples={
            ...      'xValues': [0, 1, 2, 3, 4, 5],
            ...      'yValues': [10, 15, 12, 18, 20, 25]
            ...  }, offset=2, count=3)  # Uses elements [2,3,4]
            
            Different offsets for different properties:
            >>>  series.append_samples({
            ...      'xValues': [0, 1, 2, 3, 4, 5],
            ...      'yValues': [10, 15, 12, 18, 20, 25],
            ...      'colors': [(255, 0, 0), "#00ff00", "#0000ff", "yellow", '#ff00ff'],
            ...      'sizes': [5, 8, 6, 10, 12, 7]
            ...  }, offset=1, offsetColors=0, offsetSizes=2, count=3)    # Uses x[1:4], y[1:4], colors[0:3], sizes[2:5]

            Using offsets:
            >>>  series.append_samples(x=[0,1,2,3,4], y=[10,15,12,18,20],
            ...                       colors=['#ff0000','#00ff00','#0000ff','#ffff00'],
            ...                       offset=1, count=3, offset_colors=0)
            """
        
        if samples is None:
            samples = {}
            kw_aliases = {
                'x_values': 'x', 'y_values': 'y',
                'lookup_values': 'lookupValues', 'ids': 'ids',
                'sizes': 'sizes', 'rotations': 'rotations', 'colors': 'colors',
                'x': 'x', 'y': 'y',
                'color': 'colors', 'size': 'sizes', 'rotation': 'rotations',
                'lookup': 'lookupValues', 'lookup_value': 'lookupValues',
            }
            for old_name, new_name in kw_aliases.items():
                if old_name in kwargs and kwargs[old_name] is not None:
                    samples[new_name] = kwargs[old_name]
        else:
            dict_aliases = {
                'xValues': 'x', 'yValues': 'y',
                'lookupValues': 'lookupValues', 'ids': 'ids',
                'sizes': 'sizes', 'rotations': 'rotations', 'colors': 'colors',
                'x_values': 'x', 'y_values': 'y',
                'lookup_values': 'lookupValues',
            }
            normalized = {}
            for k, v in samples.items():
                if k in ('x', 'y') and v is not None:
                    normalized[k] = v
            for k, v in samples.items():
                if v is None:
                    continue
                target = dict_aliases.get(k, k)
                if target in ('x', 'y') and target in normalized:
                    continue
                normalized[target] = v
            samples = normalized

        processed_samples = {}
        for key, value in samples.items():
            if value is not None:
                if any(prop in key.lower() for prop in ['color', 'fill', 'stroke']):
                    if isinstance(value, list):
                        processed_samples[key] = [convert_color_to_hex(c) for c in value]
                    else:
                        processed_samples[key] = convert_color_to_hex(value)
                else:
                    processed_samples[key] = convert_to_list(value) if isinstance(value, (list, tuple)) else value
            else:
                processed_samples[key] = value

        opts = {}
        opt_params = {
            'count': count, 'offset': offset, 'start': start, 'step': step,
            'offsetColors': offset_colors, 'offsetIds': offset_ids,
            'offsetLookupValues': offset_lookup_values, 'offsetRotations': offset_rotations,
            'offsetSizes': offset_sizes
        }
        for key, value in opt_params.items():
            if value is not None:
                opts[key] = value

        payload = {'samples': processed_samples}
        if opts:
            payload['opts'] = opts

        self.instance.send(self.id, 'appendSamples', payload)
        return self

    def set_samples(
            self, 
            samples: dict = None, 
            count: int | float = None, 
            offset: int | float = None, 
            start: int | float = None, 
            step: int | float = None, 
            **kwargs):
        """Re-specify all values in the data set. This is a convenience method that is fundamentally equal to:

        series.clear().append_samples( ... )

        Args:  
            samples (dict): Dictionary of data properties (e.g., {'xValues': [...], 'yValues': [...]})          
            start (int | float):
            step (int | float):
            count (int | float):
            offset (int | float):
            **kwargs: Multiple parameter formats supported:
                x_values (list[int | float]): List of x values.
                y_values (list[int | float]): List of y values.
                lookup_values (list[int | float]): List of lookup values.
                ids (list[int | float]): List of ids.
                sizes (list[int | float]): List of size values.
                rotations (list[int | float]): List of rotation values.
                colors (list[str]): List of HEX strings (NOT COLOR OBJECTS!)


        Returns:
            The instance of the class for fluent interface.

        Example:
            With count and offset:            
            >>> series.set_samples(
            ...     samples={
            ...         'xValues': [0, 1, 2, 3, 4, 5, 6],  # 7 values
            ...         'yValues': [5, 10, 15, 20, 25, 30, 35],
            ...         'colors': ["#aa0000", "#00aa00", "#0000aa", "#aaaa00", "#aa00aa", "#00aaaa", "#aaaaaa"]
            ...     },
            ...     offset=1,  # Skip first value
            ...     count=4    # Use only 4 values after offset
            ... )
        """
        if samples is None:
            samples = {}
            old_params = {
                'x_values': 'xValues', 'y_values': 'yValues',
                'lookup_values': 'lookupValues', 'ids': 'ids',
                'sizes': 'sizes', 'rotations': 'rotations', 'colors': 'colors'
            }
            for old_name, new_name in old_params.items():
                if old_name in kwargs and kwargs[old_name] is not None:
                    samples[new_name] = kwargs[old_name]
        processed_samples = {}
        for key, value in samples.items():
            if key == 'colors' and value is not None:
                processed_samples[key] = [convert_color_to_hex(c) for c in convert_to_list(value)]
            else:
                processed_samples[key] = convert_to_list(value) if value is not None else value
        payload = {'samples': processed_samples}
        opts = {}
        for key, value in {'count': count, 'offset': offset, 'start': start, 'step': step}.items():
            if value is not None:
                opts[key] = value        
        if opts:
            payload['opts'] = opts
        self.instance.send(self.id, 'setSamples', payload)
        return self
    
    def alter_samples(
        self, 
        index: int | float,
        samples: dict = None, 
        count: int | float = None, 
        offset: int | float = None, 
        start: int | float = None, 
        step: int | float = None, 
        **kwargs
        ):
        """Alter existing samples in the data set. This method also supports automatically appending samples when
        attempting to alter samples that don't exist in data set.

        This method alters existing samples by referencing sample indexes. This simply refers to an incrementing counter
        of when each sample was first introduced. For example, 0 refers to first sample that was added to data set.
        When data cleaning is enabled, sample indexes do NOT shift. They always point to unique samples, even if old
        samples are removed.

        Args:  
            index: First altered sample index.
            samples (dict): Dictionary of data properties (e.g., {'xValues': [...], 'yValues': [...]})
            count (int | float): Number of samples to process
            offset (int | float): Start reading from this index in input arrays
            start (int | float): Starting X value for progressive data
            step (int | float): X increment for progressive data
            **kwargs: Multiple parameter formats supported:
                x_values (list[int | float]): List of x values.
                y_values (list[int | float]): List of y values.
                lookup_values (list[int | float]): List of lookup values.
                ids (list[int | float]): List of ids.
                sizes (list[int | float]): List of size values.
                rotations (list[int | float]): List of rotation values.
                colors (list[str]): List of HEX strings (NOT COLOR OBJECTS!)

        Returns:
            The instance of the class for fluent interface.

        Example:
            Altering samples starting from index 1:            
                >>> series.alter_samples(
                ...     index=1,  # Start from second sample (index 1)
                ...     y_values=[20, 25],  # Change y values of samples at index 1 and 2
                ...     colors=["#00ffff", "#ffaa00"]  # Change colors of samples at index 1 and 2
                ... )
        """
        if samples is None:
            samples = {}
            old_params = {
                'x_values': 'xValues', 'y_values': 'yValues',
                'lookup_values': 'lookupValues', 'ids': 'ids',
                'sizes': 'sizes', 'rotations': 'rotations', 'colors': 'colors'
            }
            for old_name, new_name in old_params.items():
                if old_name in kwargs and kwargs[old_name] is not None:
                    samples[new_name] = kwargs[old_name]

        processed_samples = {}
        for key, value in samples.items():
            if key == 'colors' and value is not None:
                processed_samples[key] = [convert_color_to_hex(c) for c in convert_to_list(value)]
            else:
                processed_samples[key] = convert_to_list(value) if value is not None else value

        payload = {'index': index, 'samples': processed_samples}
        
        opts = {}
        for key, value in {'count': count, 'offset': offset, 'start': start, 'step': step}.items():
            if value is not None:
                opts[key] = value
        
        if opts:
            payload['opts'] = opts

        self.instance.send(self.id, 'alterSamplesStartingFrom', payload)
        return self
    
    def alter_samples_by_match(
        self,
        match_key: str,
        match_values: list[int | float],
        x_values: list[int | float | str] = None,
        y_values: list[int | float] = None,
        colors: list[str] = None,
        ids: list[int | float] = None,
        lookup_values: list[int | float] = None,
        rotations: list[int | float] = None,
        sizes: list[int | float] = None,
    ):
        """Alter existing samples by matching any property key and values.
        
        Args:
            match_key: Property to match against (e.g. "x_values", "ids", "lookup_values")
            match_values: Values to match for sample selection
            ids_to_alter (list[int | float]): List of ids to alter.
            x_values (list[int | float]): List of x values.
            y_values (list[int | float]): List of y values.
            colors (list[str]): List of HEX strings (NOT COLOR OBJECTS!)
            ids (list[int | float]): List of ids.
            lookup_values (list[int | float]): List of lookup values.
            rotations (list[int | float]): List of rotation values.
            sizes (list[int | float]): List of size values.

        Returns:
            The instance of the class for fluent interface.

        Altering samples:            
            >>> series.alter_samples_by_match(
            ...     match_key="ids",
            ...     match_values=[101, 103],
            ...     y_values=[20, 5],
            ... )
        """
        payload = {
            'matchKey': match_key,
            'matchValues': convert_to_list(match_values)
        }
        
        if x_values is not None: 
            payload['xValues'] = convert_to_list(x_values)
        if y_values is not None: 
            payload['yValues'] = convert_to_list(y_values)
        if colors is not None: 
            payload['colors'] = [convert_color_to_hex(c) for c in convert_to_list(colors)]
        if ids is not None: 
            payload['ids'] = convert_to_list(ids)
        if lookup_values is not None: 
            payload['lookupValues'] = convert_to_list(lookup_values)
        if rotations is not None: 
            payload['rotations'] = convert_to_list(rotations)
        if sizes is not None: 
            payload['sizes'] = convert_to_list(sizes)
        
        self.instance.send(self.id, 'alterSamplesByMatch', payload)
        return self

    def set_max_sample_count(self, max_sample_count: int, automatic: bool = True):
        """All real-time use cases (where data points are pushed in periodically) must define a "max sample count".
        This allocates the required amount of memory beforehand, which is crucial to get the best performance.

        Args:
            max_sample_count (int): After this sample count is reached, the oldest samples will start dropping out.
            automatic (bool): If true, the chart will first allocate only small amount of memory, and progressively
                increase memory allocation as samples come in until eventually limiting to max_sample_count.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setMaxSampleCount', {'max': max_sample_count, 'auto': automatic})
        return self

    def set_curve_preprocessing(self, type: str, step: str = None, resolution: int | float = 20):
        """Set curve preprocessing mode.

        Args:
            type: "step" | "spline" |
            step: "before" | "middle" | "after"
            resolution: Number of interpolated coordinates between two real data points.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(
            self.id,
            'setCurvePreprocessing',
            {
                'type': type,
                'step': step,
                'resolution': resolution,
            },
        )
        return self

    def read_back(
        self,
        only_in_range: dict | None = None,
        as_numpy: bool = True,
        colors: str | None = None,      
        palette_steps: bool = False,  
    ):
        """Read back the current contents of the data set.

        Args:
            only_in_range : dict | None, default None
                Filter by X-range (progressive axis).
                Format: {'start': <x_min>, 'end': <x_max>}.
            as_numpy : bool, default True
                If True, TypedArrays are decoded to NumPy arrays; otherwise Python lists.
            colors : {"uint32","hex","hex_rgba","rgb","html"} | None, default None
                If not None, request per-point colors :
                - "uint32": keep/convert to np.uint32 (packed RGBA as in LCJS).
                - "hex": add `colorsHex` as "#RRGGBB".
                - "hex_rgba": add `colorsHex` as "#RRGGBBAA".
                - "rgb": add `colorsRGB` as "rgb(...)" or "rgba(...)".
                - "html": add `colorsHTML` using a CSS name if exact (alpha==255), else hex/rgba fallback.
                Tip:
                    With paletted (dynamic) coloring, per-point colors don’t exist natively.
            palette_steps : bool, default False
                If True, return a palette summary (the LUT *step* colors and their threshold values)
                instead of per-point colors (useful when you defined a few discrete colors and only want
                that range description).
        Examples:
            Read only X in [0, 100]
            >>> data = series.read_back(only_in_range={'start': 0, 'end': 100})

            Read visible X-range (if your wrapper exposes get_interval())
            xmin, xmax = chart.get_default_x_axis().get_interval()
            data = series.read_back(only_in_range={'start': xmin, 'end': xmax})

            Get per-point colors as HTML color names/values
            >>> data = series.read_back(colors="html")

            Get only the LUT step colors (no per-point array)
            >>> data = series.read_back(palette_steps=True)

        Returns:
            dict with xValues, yValues, colors, sizes, rotations, lookupValues, iSampleFirst, paletteSteps, paletteInterpolate and lookUpProperty
            where all TypedArrays are decoded to NumPy arrays (or lists).
        """
        args = {}
        if only_in_range is not None:
            args["onlyInRange"] = only_in_range
        if palette_steps:
            args["paletteStepsOnly"] = True
        if colors is not None:
            args["materializeColors"] = "uint32"

        result = self.instance.get(self.id, "readBack", args)
        res = _walk_decode(result, as_numpy)
        return _postprocess_readback(res, colors=colors)

class SeriesWithAddDataPoints(Series):
    def add_dict_data(self, data: dict[str, int | float] | list[dict[str, int | float]]):
        """Append a single datapoint or list of datapoints into the series.

        Args:
            data (dict[str, int | float] | list[dict[str, int | float]]): List of datapoints or a single datapoint.

        Examples:
            Single 2D point
            >>> series.add_dict_data({"x": 0, "y": 10})
            
            Multiple 2D points
            >>> series.add_dict_data([
            ...     {"x": 0, "y": 10},
            ...     {"x": 1, "y": 15}
            ... ])

        Returns:
            The instance of the class for fluent interface.
        """
        if isinstance(data, dict):
            data = [data]
        processed_data = []
        for item in data:
            processed_item = {}
            for key, value in item.items():
                processed_item[key] = value
            processed_data.append(processed_item)

        self.instance.send(self.id, 'addDictData', {'data': processed_data})
        return self


class SeriesWithAddDataXY(Series):
    def add(self, *args: object, **kwargs: object):
        """Add xy-data to the series. Can be used in two ways:

        * ```series.add(x, y)```, where x and y are lists containing numbers.
        * ```series.add(data)```, where data is array of dictionaries with x and y keys.

        Additional parameters:
            colors: List of colors for each point
            sizes: List of sizes for each point
            rotations: List of rotations for each point
            ids: List of IDs for each point
            lookup_values: List of lookup values for each point


        Examples:
            Basic coordinate lists
            >>> series.add([0, 1, 2], [10, 15, 12])
            
            Using kwargs
            >>> series5.add(
            ...     x=[0, 1, 2, 3], 
            ...     y=[10, 15, 12, 18],
            ...     colors=['#ff0000', '#00ff00', '#0000ff', '#ffff00'],
            ...     sizes=[5, 10, 15, 8],
            ...     rotations=[0, 45, 90, 135],
            ...     ids=[100, 101, 102, 103],
            ...     lookup_values=[0.1, 0.5, 0.8, 0.3]
            ... )
            
            JSON data with colors
            >>> json_data = [
            ...     {"x": 0, "y": 10, "color": "#ff0000", "size": 15},
            ...     {"x": 1, "y": 15, "color": "#00ff00", "size": 20},
            ...     {"x": 2, "y": 12, "color": "#0000ff", "size": 18},
            ...     {"x": 3, "y": 18, "color": "#ffff00", "size": 12}
            ... ]
            ... series7.add(json_data)

            Different color formats
            >>> series9.add(
            ...     x=[0, 1, 2, 3, 4], 
            ...     y=[10, 15, 12, 18, 14],
            ...     colors=[
            ...         '#ff0000',           # Hex string
            ...         'red',               # CSS color name  
            ...         (0, 255, 0),         # RGB tuple
            ...         {'r': 0, 'g': 0, 'b': 255},  # RGB dict
            ...         16777215             # Integer
            ...     ]
            ... )

        Returns:
            The instance of the class for fluent interface.
        """
        x = []
        y = []
        data = []

        if len(kwargs) > 0:
            if 'x' in kwargs:
                x = kwargs['x']
            if 'y' in kwargs:
                y = kwargs['y']
            if 'data' in kwargs:
                data = kwargs['data']
        elif len(args) == 2:
            x = args[0]
            y = args[1]
        elif len(args) == 1:
            data = args[0]

        x = convert_to_list(x)
        y = convert_to_list(y)

        if x or y:
            samples = {'x': x, 'y': y}
            property_map = {
                'colors': 'colors',
                'sizes': 'sizes', 
                'size': 'sizes',
                'rotations': 'rotations',
                'rotation': 'rotations',
                'ids': 'ids',
                'lookup_values': 'lookupValues',
                'lookup': 'lookupValues'
            }
            
            for kwarg_key, sample_key in property_map.items():
                if kwarg_key in kwargs and kwargs[kwarg_key] is not None:
                    if sample_key == 'colors':
                        processed_colors = [convert_color_to_hex(c) for c in convert_to_list(kwargs[kwarg_key])]
                        samples['colors'] = processed_colors
                    else:
                        samples[sample_key] = convert_to_list(kwargs[kwarg_key])            
            self.instance.send(self.id, 'appendSamples', {'samples': samples})            
        if data:
            processed_array = []
            for item in data:
                processed_item = {}
                for key, value in item.items():
                    if key.lower() == 'color' and value is not None:
                        processed_item[key] = convert_color_to_hex(value)
                    else:
                        processed_item[key] = value
                processed_array.append(processed_item)
            
            self.instance.send(self.id, 'appendJSON', {'array': processed_array})
        return self

class SeriesWithAddDataXYZ(Series):
    def add(self, *args, **kwargs):
        """Add xyz-data to the series. Can be used in two ways:

        *  ```series.add(x, y, z)```, where x, y, and z are lists containing numbers.

        * ```series.add(data)```, where data is array of dictionaries with x, y, and z keys with numerical values.

        Returns:
            The instance of the class for fluent interface.
        """
        x = []
        y = []
        z = []
        data = []

        if len(kwargs) > 0:
            if 'x' in kwargs:
                x = kwargs['x']
            if 'y' in kwargs:
                y = kwargs['y']
            if 'z' in kwargs:
                z = kwargs['z']
            if 'data' in kwargs:
                data = kwargs['data']
        elif len(args) == 3:
            x = args[0]
            y = args[1]
            z = args[2]
        elif len(args) == 1:
            data = args[0]

        x = convert_to_list(x)
        y = convert_to_list(y)
        z = convert_to_list(z)

        if x or y or z:
            self.instance.send(self.id, 'addDataXYZ', {'x': x, 'y': y, 'z': z})
        if data:
            self.instance.send(self.id, 'addData', {'data': data})
        return self


class SeriesWithDataCleaning(Series):
    def enable_data_cleaning(self, enabled: bool):
        """Enable automatic data cleaning for series.

        Args:
            enabled (bool): If true, automatic data cleaning is performed.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setDataCleaning', {'enabled': enabled})
        return self


class SeriesWithAddValues(Series):
    def add_values(
        self,
        y_values: list[list[int | float]] = None,
        intensity_values: list[list[int | float]] = None,
    ):
        """Append values to the Surface Scrolling Grid Series.

        The series type can contain between 1 and 2 different data sets (Y values and Intensity values).
        This same method is used for managing both types of data;

        Args:
            y_values (list[list[int | float]]): a number matrix.
            intensity_values (list[list[int | float]]): a number matrix.

        Returns:
            The instance of the class for fluent interface.
        """
        y_values = convert_to_matrix(y_values)
        intensity_values = convert_to_matrix(intensity_values)

        self.instance.send(
            self.id,
            'addValues',
            {'yValues': y_values, 'intensityValues': intensity_values},
        )
        return self


class SeriesWithInvalidateIntensity(Series):
    def invalidate_intensity_values(
        self,
        data: list[list[int | float]],
        column_index: int = None,
        row_index: int = None,
        sample_index: int = None,
    ):
        """Invalidate range of surface intensity values starting from first column and row.

        Args:
            data (list[list[int | float]]): a number matrix.
            column_index (int): Index of first invalidated column.
            row_index (int): Index of first invalidated row.
            sample_index (int): The location along scrolling dimension is identified by a sample index.
                Sample index 0 would reference the first sample in the heatmap, whereas 1 the second sample.

        Returns:
            The instance of the class for fluent interface.
        """
        data = convert_to_matrix(data)

        self.instance.send(
            self.id,
            'invalidateIntensityValues',
            {
                'data': data,
                'column': column_index,
                'row': row_index,
                'iSample': sample_index,
            },
        )
        return self


class SeriesWithAddIntensityValues(Series):
    def add_intensity_values(self, new_data_points: list[list[int | float]]):
        """Push a Matrix of intensity values into the Heatmap grid. Each value describes one cell in the grid.

        Args:
            new_data_points (list[list[int | float]]): a number matrix.

        Returns:
            The instance of the class for fluent interface.
        """
        new_data_points = convert_to_matrix(new_data_points)

        self.instance.send(self.id, 'addIntensityValues', {'data': new_data_points})
        return self


class SeriesWithInvalidateData(Series):
    def add(self, data: dict[str, int | float] | list[dict[str, int | float]]):
        """Method for invalidating Box data. Accepts an Array of BoxDataCentered objects.
        Properties that must be defined for each NEW Box:

        "xCenter", "yCenter", "zCenter" | coordinates of Box in Axis values.

        "xSize", "ySize", "zSize" | size of Box in Axis values.

        Args:
            data (dict[str, int | float] | list[dict[str, int | float]]): List of BoxDataCentered objects.

        Returns:
            The instance of the class for fluent interface.
        """
        data = convert_to_dict(data)
        self.instance.send(self.id, 'invalidateData', {'data': data})
        return self


class SeriesWithAddArray(Series):
    def add_array_x(self, array: list[int | float]):
        """Append new data points into the series by only supplying X coordinates.

        Args:
            array (list[int | float]): List of numbers | Pandas DataFrame column | NumPy array

        Returns:
            The instance of the class for fluent interface.
        """
        array = convert_to_list(array)

        self.instance.send(self.id, 'addArrayX', {'array': array})
        return self

    def add_array_y(self, array: list[int | float]):
        """Append new data points into the series by only supplying Y coordinates.

        Args:
            array (list[int | float]): List of numbers | Pandas DataFrame column | NumPy array

        Returns:
            The instance of the class for fluent interface.
        """
        array = convert_to_list(array)

        self.instance.send(self.id, 'addArrayY', {'array': array})
        return self

    def add_arrays_xy(self, array_x: list[int | float], array_y: list[int | float]):
        """Append new data points into the series by supplying X and Y coordinates in two separated arrays.

        Args:
            array_x (list[int | float]): List of numbers | Pandas DataFrame column | NumPy array
            array_y (list[int | float]): List of numbers | Pandas DataFrame column | NumPy array

        Returns:
            The instance of the class for fluent interface.
        """
        array_x = convert_to_list(array_x)
        array_y = convert_to_list(array_y)

        self.instance.send(self.id, 'addArraysXY', {'arrayX': array_x, 'arrayY': array_y})
        return self


class SeriesWithIndividualPoint(Series):
    def set_individual_point_color_enabled(self, enabled: bool):
        """Enable or disable individual point color attributes.
        When enabled, each added data point can be associated with a color attribute.

        Args:
            enabled (bool): Individual point values enabled or disabled.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setIndividualPointColorEnabled', {'enabled': enabled})
        return self


class SeriesWith2DPoints(Series):
    def set_point_shape(self, shape: str = 'circle'):
        """Set shape of displayed points.

        Args:
            shape (str): "arrow" | "circle" | "cross" | "diamond" | "minus" | "plus" | "square" | "star" | "triangle"

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setPointShape', {'shape': shape})
        return self

    def set_point_color(self, color: any):
        """Set the color of all 2D datapoints within a series.

        Args:
            color (Color): The color of the points.

        Returns:
            The instance of the class for fluent interface.
        """
        color = convert_color_to_hex(color) if color is not None else None

        self.instance.send(self.id, 'setPointFillStyle', {'color': color})
        return self

    def set_point_size(self, size: int | float):
        """Set the size of all 2D datapoints within a series.

        Args:
            size (int | float): Size of a single datapoint in pixels.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setPoint2DSize', {'size': size})
        return self

    def set_point_rotation(self, degrees: int | float):
        """Set the rotation of all 2D datapoints within a series.

        Args:
            degrees (int | float): Rotation in degrees.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setPointRotation', {'angle': degrees})
        return self
    
    def set_point_stroke_style(self, style: str, thickness: int | float, color: any = None):
        """Configure stroke style for line drawn around edges of the points.

        Args:
            style (str): "solid" | "dashed" | "empty"
            thickness (int | float): Thickness of the connector line.
            color (Color): Color of the connector line.

        Returns:
            The instance of the class for fluent interface.
        """
        color = convert_color_to_hex(color) if color is not None else None

        styles = ('solid', 'dashed', 'empty')
        if style not in styles:
            raise ValueError(f"Expected sorter to be one of {styles}, but got '{style}'.")

        self.instance.send(
            self.id,
            'setPointStrokeStyle',
            {'style': style, 'thickness': thickness, 'color': color},
        )
        return self


class SeriesWith3DPoints(Series):
    def set_point_color(self, color: any):
        """Set the color of all 2D datapoints within a series.

        Args:
            color (Color): Color of the points.

        Returns:
            The instance of the class for fluent interface.
        """
        color = convert_color_to_hex(color) if color is not None else None

        self.instance.send(self.id, 'setPoint3DFillStyle', {'color': color})
        return self

    def set_point_size(self, size: int | float):
        """Set the size of all 3D datapoints within a series.

        Args:
            size (int | float): Size of a single datapoint.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setPoint3DSize', {'size': size})
        return self

    def set_point_shape(self, shape: str = 'sphere'):
        """Set the shape of all 3D datapoints within a series.

        Args:
            shape (str): "cube" | "sphere"

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setPoint3DShape', {'shape': shape})
        return self

    def set_palette_point_colors(
        self,
        steps: list[dict],
        look_up_property: str = 'value',
        interpolate: bool = True,
        percentage_values: bool = False,
    ):
        """Define a palette for dynamically looked up fill coloring for the points.

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
            'setPoint3DPalettedFillStyle',
            {
                'steps': steps,
                'lookUpProperty': look_up_property,
                'interpolate': interpolate,
                'percentageValues': percentage_values,
            },
        )
        return self


class SeriesWith2DLines(Series):
    def set_line_color(self, color: any):
        """Set the color of a 2D line series.

        Args:
            color (Color): The color of the line.

        Returns:
            The instance of the class for fluent interface.
        """
        color = convert_color_to_hex(color) if color is not None else None

        self.instance.send(self.id, 'setLineFillStyle', {'color': color})
        return self

    def set_line_thickness(self, thickness: int | float):
        """Set the thickness of a 2D line series.

        Args:
            thickness (int | float): Thickness of the line. Use -1 thickness to enable primitive line rendering.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setLineThickness', {'width': thickness})
        return self

    def set_dashed(
        self,
        pattern: str = 'Dashed',
        thickness: int | float = None,
        color: any = None,
    ):
        """Change the line stroke style to dashed line.

        Args:
            pattern (str): "DashDotted" | "Dashed" | "DashedEqual" | "DashedLoose" | "Dotted" | "DottedDense"
            thickness (int | float): Thickness of the line. Use -1 thickness to enable primitive line rendering.
            color (Color): The color of the line (optional).

        Returns:
            The instance of the class for fluent interface.
        """
        color = convert_color_to_hex(color) if color is not None else None

        self.instance.send(
            self.id,
            'setDashedStroke',
            {'pattern': pattern, 'thickness': thickness, 'color': color},
        )
        return self


class SeriesWith3DLines(Series):
    def set_line_color(self, color: any):
        """Set the color of a 3D line series.

        Args:
            color (Color): The color of the line.

        Returns:
            The instance of the class for fluent interface.
        """
        color = convert_color_to_hex(color) if color is not None else None

        self.instance.send(self.id, 'setLineFillStyle', {'color': color})
        return self

    def set_line_thickness(self, thickness: int | float):
        """Set the thickness of a 3D line series.

        Args:
            thickness (int | float): Thickness of the line. Use -1 thickness to enable primitive line rendering.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setLineThickness', {'width': thickness})
        return self


class SeriesWithWireframe(Series):
    def set_wireframe_stroke(self, thickness: int | float, color: any = None):
        """Set the style of wireframe of the series.

        Args:
            thickness (int | float): Thickness of the wireframe.
            color (Color): Color of the wireframe.

        Returns:
            The instance of the class for fluent interface.
        """
        color = convert_color_to_hex(color) if color is not None else None

        self.instance.send(
            self.id,
            'setWireframeStyle',
            {'thickness': thickness, 'color': color},
        )
        return self

    def hide_wireframe(self):
        """Hide the wireframe.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setEmptyWireframeStyle', {})
        return self


class SeriesWithInvalidateHeight(Series):
    def invalidate_height_map(
        self,
        data: list[list[int | float]],
        column_index: int = None,
        row_index: int = None,
    ):
        """Invalidate range of surface height values starting from first column and row.
        These values correspond to coordinates along the Y axis.

        Args:
            data (list[list[int | float]]): a number matrix of height values.
            column_index (int): Index of the first column to be validated.
            row_index (int): Index of the first row to be validated.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(
            self.id,
            'invalidateHeightMap',
            {'data': data, 'column': column_index, 'row': row_index},
        )
        return self


class SeriesWithIntensityInterpolation(Series):
    def set_intensity_interpolation(self, enabled: bool):
        """Set surface intensity interpolation mode.

        Args:
            enabled (bool): If True, each pixel is colored based on a bi-linearly interpolated
                intensity value based on the 4 closest real intensity values.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setIntensityInterpolation', {'enabled': enabled})
        return self


class SeriesWithPixelInterpolation(Series):
    def set_pixel_interpolation(self, enabled: bool):
        """Set pixel interpolation mode.

         Args:
            enabled (bool): If True, each pixel is colored individually by bilinear interpolation.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setPixelInterpolationMode', {'enabled': enabled})
        return self


class SeriesWithCull(Series):
    def set_cull_mode(self, mode: str = 'disabled'):
        """Set culling of the series.

        Args:
            mode (str): "disabled" | "cull-back" | "cull-front"

        Returns:
            The instance of the class for fluent interface.
        """
        cull_modes = ('disabled', 'cull-back', 'cull-front')
        if mode not in cull_modes:
            raise ValueError(f"Expected mode to be one of {cull_modes}, but got '{mode}'.")

        self.instance.send(self.id, 'setCullMode', {'mode': mode})
        return self


class SeriesWith3DShading(Series):
    def set_depth_test_enabled(self, enabled: bool):
        """Set 3D depth test enabled for this series. By default, this is enabled,
        meaning that any series that is rendered after this series and is behind this series will not be rendered.
        Can be disabled to alter 3D rendering behavior.

        Args:
            enabled (bool): Depth test enabled?

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setDepthTestEnabled', {'enabled': enabled})
        return self

    def set_color_shading_style(
        self,
        phong_shading: bool = True,
        specular_reflection: float = 0.5,
        specular_color: any = '#ffffff',
    ):
        """Set Color Shading Style for series.

        Args:
            phong_shading (bool): If True, use Phong shading style. If False, use simple shading style.
            specular_reflection (float): Controls specular reflection strength. Value ranges from 0 to 1.
                Default is 0.1.
            specular_color (Color): Specular highlight color.

        Returns:
            The instance of the class for fluent interface.
        """
        specular_color = convert_color_to_hex(specular_color) if specular_color is not None else None

        self.instance.send(
            self.id,
            'setColorShadingStyle',
            {
                'phongShading': phong_shading,
                'specularReflection': specular_reflection,
                'specularColor': specular_color,
            },
        )
        return self


class RectangleSeriesStyle(Series):
    def set_image_style(
        self,
        source: str,
        fit_mode: str = 'Stretch',
        surrounding_color=None,
        source_missing_color=None,
    ):
        """
        Set the series background image.

        Args:
            source (str): The image source. This can be:
                - A URL (remote image).
                - A local file path.
                - An already Base64-encoded image string.
            fit_mode (str, optional): Fit mode for the image. Options:
                - "Stretch" (default)
                - "Fill"
                - "Fit"
                - "Tile"
                - "Center"
            surrounding_color (Color, optional): Color for areas outside the image.
            source_missing_color (Color, optional): Color when the image fails to load.

        Returns:
            self: The instance of the class for method chaining.

        Raises:
            ValueError: If the source is invalid.

        Example:
            >>> series.set_rectangle_image_style("D:/path/to/local_image.png")
            >>> series.set_rectangle_image_style("https://example.com/image.jpg")
        """
        if not source:
            raise ValueError('Image source is required.')
        if not source.startswith('data:'):
            source = convert_to_base64(source)
        args = {
            'source': source,
            'fitMode': fit_mode,
            'surroundingColor': convert_color_to_hex(surrounding_color) if surrounding_color else None,
            'sourceMissingColor': convert_color_to_hex(source_missing_color) if source_missing_color else None,
        }
        self.instance.send(self.id, 'setRectangleImageStyle', args)
        return self

    def set_video_style(
        self,
        video_source: str,
        fit_mode: str = 'Stretch',
        surrounding_color: any = None,
        source_missing_color: any = None,
    ):
        """
        Sets the series background to a video by updating the area fill style.

        Args:
            video_source (str): Path to the video file (MP4 or WEBM).
            fit_mode (str): Fit mode ('Stretch', 'Fill', 'Fit', etc.).
            surrounding_color (Color, optional): Color for areas outside the video.
            source_missing_color (Color, optional): Color when video fails to load.

        Returns:
            self: The instance of the class for method chaining.

        Example:
            >>> series.set_rectangle_video_style("D:/path/to/local_video.mp4")
            >>> series.set_rectangle_video_style("https://example.com/video.mp4")
        """
        surrounding_color = convert_color_to_hex(surrounding_color) if surrounding_color is not None else None
        source_missing_color = convert_color_to_hex(source_missing_color) if source_missing_color is not None else None

        if not video_source:
            raise ValueError('Video source is required.')
        video_data_uri = convert_to_base64(video_source)
        args = {
            'videoSource': video_data_uri,
            'fitMode': fit_mode,
            'surroundingColor': surrounding_color if surrounding_color else None,
            'sourceMissingColor': source_missing_color if source_missing_color else None,
        }
        self.instance.send(self.id, 'setRectangleVideoStyle', args)
        return self


class PointSeriesStyle(Series):
    def set_point_image_style(self, source: str):
        """
        Set the point fill style of the Series with an image.

        Args:
            source (str): The source of the image, either a file path or a URL.

        Returns:
            self: The Series instance for fluent interface.

        Example:
            >>> series.set_point_image_style("D:/path/to/local_image.png")
            >>> series.set_point_image_style("https://example.com/image.jpg")
        """
        base64_image = convert_to_base64(source)
        args = {'fillStyle': {'source': base64_image}}
        self.instance.send(self.id, 'setPointImageStyle', args)
        return self
    
    def set_custom_point_shape(self, source: str):
        """
        Set a custom shape for the Series points using an image.

        Args:
            source (str): The source of the image, either a file path or a URL.

        Returns:
            self: The Series instance for a fluent interface.

        Example:
            >>> series.set_custom_point_shape("D:/path/to/local_image.png")
            >>> series.set_custom_point_shape("https://example.com/icon.png")
        """
        base64_image = convert_to_base64(source)
        args = {
            'fillStyle': {'source': base64_image},
            'chartId': self.chart.id 
        }
        self.instance.send(self.id, 'setPointCustomShape', args)
        return self

    def set_point_video_style(
        self,
        video_source: str,
        fit_mode: str = 'Fit',
        surrounding_color: any = None,
        source_missing_color: any = None,
    ):
        """
        Sets the point fill style of a series to a video using a Base64-encoded video as the source.

        Args:
            video_source (str): Path to the video file (MP4 or WEBM).
            fit_mode (str): How the video should Fit ('Fit', 'Stretch', 'Fill', etc.).
            surrounding_color (Color, optional): Color for areas outside the video.
            source_missing_color (Color, optional): Color when video fails to load.

        Returns:
            The instance of the class for method chaining.

        Example:
            >>> series.set_point_video_style("D:/path/to/local_video.mp4")
            >>> series.set_point_video_style("https://example.com/video.mp4")
        """
        surrounding_color = convert_color_to_hex(surrounding_color) if surrounding_color is not None else None
        source_missing_color = convert_color_to_hex(source_missing_color) if source_missing_color is not None else None

        if not video_source:
            raise ValueError('Video source is required.')
        video_data_uri = convert_to_base64(video_source)
        args = {
            'videoSource': video_data_uri,
            'fitMode': fit_mode,
            'surroundingColor': surrounding_color if surrounding_color else None,
            'sourceMissingColor': source_missing_color if source_missing_color else None,
        }
        self.instance.send(self.id, 'setPointVideoStyle', args)
        return self


class PolarPointStyle(Series):
    def set_point_image_style(
        self,
        source: str,
        fit_mode: str = 'Stretch',
        surrounding_color=None,
        source_missing_color=None,
    ):
        """
        Set point fill style of the Series with polar coordinates.

        Args:
            source (str): The source of the image (local file or URL).
            fit_mode (str): How the video should Fit ('Fit', 'Stretch', 'Fill', etc.).
            surrounding_color (Color, optional): Color for areas outside the video.
            source_missing_color (Color, optional): Color when video fails to load.

        Returns:
            self: The instance for fluent interface.

        Examples:
            >>> series.set_point_image_style("D:/path/image.png", )
            >>> series.set_point_image_style("https://example.com/image.jpg")
        """
        base64_image = convert_to_base64(source)
        args = {
            'fillStyle': {
                'source': base64_image,
                'fitMode': fit_mode,
                'surroundingColor': convert_color_to_hex(surrounding_color) if surrounding_color else None,
                'sourceMissingColor': convert_color_to_hex(source_missing_color) if source_missing_color else None,
            }
        }
        self.instance.send(self.id, 'setPolarPointImageStyle', args)
        return self


    def set_custom_point_shape(self, source: str):
        """
        Set a custom shape for the Series points using an image.

        Args:
            source (str): The source of the image, either a file path or a URL.

        Returns:
            self: The Series instance for a fluent interface.

        Example:
            >>> series.set_custom_point_shape("D:/path/to/local_image.png")
            >>> series.set_custom_point_shape("https://example.com/icon.png")
        """
        base64_image = convert_to_base64(source)
        args = {'fillStyle': {'source': base64_image}, 'chartId': self.chart.id}
        self.instance.send(self.id, 'setPolarPointCustomShape', args)
        return self

    def set_point_video_style(
        self,
        video_source: str,
        fit_mode: str = 'Fit',
        surrounding_color: any = None,
        source_missing_color: any = None,
    ):
        """
        Sets the polar point fill style to a video using a Base64-encoded video as the source.

        Args:
            video_source (str): Path to the video file (MP4 or WEBM) or a URL.
            fit_mode (str): How the video should Fit ('Fit', 'Stretch', 'Fill', etc.).
            surrounding_color (Color, optional): Color for areas outside the video.
            source_missing_color (Color, optional): Color when video fails to load.

        Returns:
            self: The instance for fluent interfacing.

        Example:
            >>> series.set_point_video_style("D:/path/to/local_video.mp4")
            >>> series.set_point_video_style("https://example.com/video.mp4")
        """
        surrounding_color = convert_color_to_hex(surrounding_color) if surrounding_color is not None else None
        source_missing_color = convert_color_to_hex(source_missing_color) if source_missing_color is not None else None

        if not video_source:
            raise ValueError('Video source is required.')

        video_data_uri = convert_to_base64(video_source)
        args = {
            'videoSource': video_data_uri,
            'fitMode': fit_mode,
            'surroundingColor': surrounding_color if surrounding_color else None,
            'sourceMissingColor': source_missing_color if source_missing_color else None,
        }
        self.instance.send(self.id, 'setPolarPointVideoStyle', args)
        return self


class SeriesWithClear:
    def clear(self):
        """Clear all previously pushed data points from the series.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'clear')
        return self


class SeriesWithDrawOrder:
    def set_draw_order(self, index: int | float):
        """Configure draw order of the series. The drawing order of series inside same chart can be configured by
        configuring their draw order index. This is a simple number that indicates which series is drawn first,
        and which last. The values can be any number, even a decimal. Higher number results in series being drawn
        closer to the top. By default, each series is assigned a running counter starting from 0 and increasing by 1
        for each series.

        Args:
            index (int | float): The draw order index.

        Returns:
            The instance of the class for fluent interface.
        """
        self.instance.send(self.id, 'setDrawOrder', {'index': index})
        return self
    
class FigureSeries:
    def set_highlight_on_hover(self, enabled: bool, highlight_mode: str = None):
        """Set highlight on mouse hover enabled or disabled.

        Args:
            enabled: Boolean flag to enable/disable highlighting.
            highlight_mode: Specific highlight behavior. Options:
                - 'noHighlighting': No highlighting on user interaction
                - 'onHover': Entire series highlights on hover  
                - 'onHoverIndividual': Only specific figure highlights (for figure series)

        Examples:
            Simple enable/disable
            >>> series.set_highlight_on_hover(enabled=True)
            >>> series.set_highlight_on_hover(enabled=False)
            
            Specific highlight modes
            >>> series.set_highlight_on_hover(enabled=True, highlight_mode='onHoverIndividual')
            >>> series.set_highlight_on_hover(enabled=True, highlight_mode='noHighlighting')

        Returns:
            The instance of the class for fluent interface.
        """
        if not enabled:
            self.instance.send(self.id, 'setFigureHighlightOnHover', {'HighlightModes': 'noHighlighting'})
        elif highlight_mode:
            self.instance.send(self.id, 'setFigureHighlightOnHover', {'HighlightModes': highlight_mode})
        else:
            self.instance.send(self.id, 'setFigureHighlightOnHover', {'enabled': True})
        return self

