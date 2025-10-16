from __future__ import annotations
import base64
from datetime import datetime, date, time
from decimal import Decimal
import json
import os
import re
import msgpack
from typing import Any, Dict, Literal, TypedDict, Union
import requests
from lightningchart.themes import CSS_COLOR_NAMES, Color

try:
    import numpy as np
    _HAS_NUMPY = True
except ImportError:
    np = None
    _HAS_NUMPY = False

try:
    import pandas as pd
except ImportError:
    pd = None

def convert_to_list(arg):
    """Converts various data types to a Python list format.
    
    For v8 compatibility, handles Color objects and preserves single values
    when appropriate to avoid asymmetric data issues.

    Args:
        arg: The input object to be converted to a list.

    Returns:
        A Python list containing the converted values from the input,
        or the original value if it should remain as a single value.
    """
    try:
        if arg is None:
            return None
        elif isinstance(arg, list):
            return arg
        elif isinstance(arg, (int, float, str)):
            return [arg]
        elif isinstance(arg, (tuple, set)):
            return list(arg)
        elif isinstance(arg, dict):
            return list(arg.values())
        elif np and isinstance(arg, np.ndarray):
            return arg.tolist()
        elif pd and isinstance(arg, (pd.Series, pd.Index)):
            return arg.tolist()
        elif hasattr(arg, '__class__') and 'Color' in str(type(arg)):
            return arg
        elif hasattr(arg, '__iter__') and not isinstance(arg, (str, bytes)):
            return list(arg)
        else:
            return [arg]
    except TypeError:
        return arg


def convert_to_dict(arg):
    """Converts various data types to a Python dictionary format.

    Args:
        arg: The input object to be converted to a dictionary.

    Returns:
        A Python dictionary containing the converted values from the input.
    """
    try:
        if arg is None:
            return None
        elif isinstance(arg, list):
            for i in range(len(arg)):
                arg[i] = convert_to_dict(arg[i])
            return arg
        elif isinstance(arg, dict):
            return arg
        elif pd and isinstance(arg, pd.DataFrame):
            return arg.to_dict(orient='records')
        elif pd and isinstance(arg, pd.Series):
            return arg.to_dict()
        return dict(arg)
    except TypeError:
        raise TypeError(f'Data type {type(arg)} is not supported.')


def convert_to_matrix(arg):
    """Converts various multidimensional data types to a Python matrix represented as
    a list of lists containing native Python numbers (int or float).

    Args:
        arg: The input object to be converted to a matrix.

    Returns:
        A Python list of lists representing the converted matrix.
    """
    try:
        if arg is None:
            return None
        elif isinstance(arg, list) and all(isinstance(row, list) for row in arg):
            return arg
        elif np and isinstance(arg, np.ndarray):
            return arg.tolist()
        elif pd and isinstance(arg, pd.DataFrame):
            return arg.values.tolist()
        elif isinstance(arg, tuple) and all(isinstance(row, (tuple, list)) for row in arg):
            return [list(row) for row in arg]
        elif hasattr(arg, '__iter__'):
            return [convert_to_matrix(item) for item in arg]
        return [arg]
    except TypeError:
        raise TypeError(f'Data type {type(arg)} is not supported.')


def convert_to_unix_time(arg, str_format: str = None):
    """Convert various datetime formats to Unix timestamp in milliseconds.

    Args:
        arg: The datetime value(s) to convert. Acceptable types include:
            int, float, datetime, pd.Timestamp, np.datetime64, str, or list
        str_format: The expected format of the string date if `arg` is a string and not in ISO format.
            This should follow the Python `datetime.strptime` format codes.

    Returns:
        A Unix timestamp in milliseconds as an integer if a single item was passed, or a list of
        Unix timestamps in milliseconds if a list was passed.
    """
    try:
        if isinstance(arg, list):
            for i in range(len(arg)):
                arg[i] = convert_to_unix_time(arg[i])
            return arg
        if isinstance(arg, (int, float)):
            return arg
        elif isinstance(arg, datetime):
            return int(arg.timestamp() * 1000)
        elif isinstance(arg, pd.Timestamp):
            return int(arg.timestamp() * 1000)
        elif isinstance(arg, np.datetime64):
            return int(arg.astype('datetime64[ms]').astype('int64'))
        elif isinstance(arg, str):
            if str_format:
                return int(datetime.strptime(arg, str_format).timestamp() * 1000)
            else:
                return int(datetime.fromisoformat(arg).timestamp() * 1000)
    except ValueError:
        raise ValueError('Input cannot be converted to a timestamp')


def convert_to_base64(source: str) -> str:
    """
    Converts an image or video file (local or remote) to a Base64 data URI.

    Args:
        source (str): File path or URL. If the source already starts with 'data:', it is returned unchanged.

    Returns:
        str: A data URI in the form 'data:<mime_type>;base64,<base64_data>'.

    Raises:
        FileNotFoundError: If a local file is not found.
        ValueError: If the file extension is unsupported.
    """
    if source.startswith('data:'):
        return source

    if source.startswith('http://') or source.startswith('https://'):
        response = requests.get(source)
        response.raise_for_status()
        data = response.content
        mime_type = response.headers.get('Content-Type')
        if not mime_type:
            lower = source.lower()
            if lower.endswith('.mp4'):
                mime_type = 'video/mp4'
            elif lower.endswith('.webm'):
                mime_type = 'video/webm'
            elif lower.endswith('.gif'):
                mime_type = 'image/gif'
            elif lower.endswith('.jpg') or lower.endswith('.jpeg'):
                mime_type = 'image/jpeg'
            elif lower.endswith('.png'):
                mime_type = 'image/png'
            else:
                raise ValueError('Unsupported file extension for URL: ' + source)
        return f'data:{mime_type};base64,{base64.b64encode(data).decode("utf-8")}'

    if not os.path.exists(source):
        raise FileNotFoundError(f'File not found: {source}')
    with open(source, 'rb') as f:
        data = f.read()
    lower = source.lower()
    if lower.endswith('.mp4'):
        mime_type = 'video/mp4'
    elif lower.endswith('.webm'):
        mime_type = 'video/webm'
    elif lower.endswith('.gif'):
        mime_type = 'image/gif'
    elif lower.endswith('.jpg') or lower.endswith('.jpeg'):
        mime_type = 'image/jpeg'
    elif lower.endswith('.png'):
        mime_type = 'image/png'
    else:
        raise ValueError('Unsupported file extension: ' + source)
    return f'data:{mime_type};base64,{base64.b64encode(data).decode("utf-8")}'


def convert_color_to_hex(color) -> str:
    """
    Convert various color representations to a hex string.
    Supports:
    - Hex strings (6 or 8 characters)
    - CSS color names
    - Integer (0 to 4,294,967,295)
    - RGB tuples/lists (3 or 4 integers in 0-255 range)
    - RGB dicts (keys: 'r', 'g', 'b' and optional 'a')
    - lightningchart.Color objects

    Args:
        color (object): Color representation to convert.

    Returns:
        str: Hex color string in the format '#RRGGBB' or '#RRGGBBAA'.
    """
    HEX_COLOR_RE = re.compile(r'^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$')

    # lightningchart.Color object
    if isinstance(color, Color):
        return color.get_hex()

    # String input (hex or CSS color name)
    if isinstance(color, str):
        lower = color.lower()
        match = HEX_COLOR_RE.match(lower)
        if match:
            hex_value = match.group(1)
            # Keep original length - don't expand 3 or 4 digit hex
            return f'#{hex_value}'
        if lower in CSS_COLOR_NAMES:
            return CSS_COLOR_NAMES[lower]
        raise ValueError('Invalid hex or CSS color string.')

    # Tuple or list input (RGB[A])
    if isinstance(color, (tuple, list)):
        if 3 <= len(color) <= 4 and all(isinstance(v, int) and 0 <= v <= 255 for v in color):
            r, g, b = color[:3]
            a = color[3] if len(color) == 4 else 255
            return f'#{r:02x}{g:02x}{b:02x}{a:02x}'
        raise ValueError('Tuple/list color must have 3 or 4 integers in 0-255 range.')

    # Dict input (r, g, b[, a])
    if isinstance(color, dict):
        r, g, b = color.get('r'), color.get('g'), color.get('b')
        a = color.get('a', 255)
        if all(isinstance(v, int) and 0 <= v <= 255 for v in (r, g, b, a)):
            return f'#{r:02x}{g:02x}{b:02x}{a:02x}'
        raise ValueError('Dict color must have integer r, g, b (and optional a) in 0-255 range.')

    # Integer input
    if isinstance(color, int):
        if 0 <= color <= 0xFFFFFFFF:
            return f'#{color:08x}'
        raise ValueError('Integer color must be in the range 0-4294967295 (0xFFFFFFFF).')

    # Object with r, g, b, (optional a) attributes
    if not isinstance(color, (str, int, list, tuple, dict)):
        if all(hasattr(color, attr) for attr in ('r', 'g', 'b')):
            r = getattr(color, 'r')
            g = getattr(color, 'g')
            b = getattr(color, 'b')
            a = getattr(color, 'a', 255)
            if all(isinstance(v, int) and 0 <= v <= 255 for v in (r, g, b, a)):
                return f'#{r:02x}{g:02x}{b:02x}{a:02x}'

    raise ValueError(
        'Invalid color input. Pass a hex string, CSS color name, 3-4 integers (RGB[A]), dict, or object with get_hex() or r/g/b attributes.'
    )

def build_legend_config(legend=None):
    """
    Build legend configuration from legend dictionary.
    
    Args:
        legend (dict): Legend configuration dictionary
    """
    if legend is None:
        return {'visible': True}
    
    legend_config = {}
    if 'visible' in legend:
        legend_config['visible'] = legend['visible']
    else:
        legend_config['visible'] = True
    
    if 'position' in legend:
        position = legend['position']
        if isinstance(position, str):
            position_map = {
                'RightTop': 0, 'RightCenter': 1, 'RightBottom': 2,
                'LeftTop': 3, 'LeftCenter': 4, 'LeftBottom': 5,
                'TopLeft': 6, 'TopCenter': 7, 'TopRight': 8,
                'BottomLeft': 9, 'BottomCenter': 10, 'BottomRight': 11
            }
            legend_config['position'] = position_map.get(position, position)
        elif hasattr(position, 'value'):
            legend_config['position'] = position.value
        else:
            legend_config['position'] = position
    
    for key in ['title']:
        if key in legend:
            legend_config[key] = legend[key]
    
    if 'title_font' in legend:
        legend_config['titleFont'] = legend['title_font']
    
    bool_mappings = {
        'render_on_top': 'renderOnTop',
        'background_visible': 'backgroundVisible',
        'add_entries_automatically': 'addEntriesAutomatically'
    }
    for python_key, js_key in bool_mappings.items():
        if python_key in legend:
            legend_config[js_key] = legend[python_key]
    
    numeric_mappings = {
        'margin_inner': 'marginInner',
        'entry_margin': 'entryMargin', 
        'auto_hide_threshold': 'autoHideThreshold'
    }
    for python_key, js_key in numeric_mappings.items():
        if python_key in legend:
            legend_config[js_key] = legend[python_key]
    
    if 'padding' in legend:
        legend_config['padding'] = legend['padding']
    if 'margin_outer' in legend:
        legend_config['marginOuter'] = legend['margin_outer']
    
    if 'entries' in legend:
        entries = legend['entries']
        entries_config = {}
        
        for prop in ['text', 'show']:
            if prop in entries:
                entries_config[prop] = entries[prop]
        
        entry_mappings = {
            'button_size': 'buttonSize', 
            'button_rotation': 'buttonRotation',
            'text_font': 'textFont',
            'match_style_exactly': 'matchStyleExactly',
            'lut_length': 'lutLength',
            'lut_thickness': 'lutThickness',
            'lut_display_proportional_steps': 'lutDisplayProportionalSteps'
        }
        for python_key, js_key in entry_mappings.items():
            if python_key in entries:
                entries_config[js_key] = entries[python_key]
        
        legend_config['entries'] = entries_config

    return legend_config


def apply_post_legend_config(chart_instance, legend_config):
    """
    Apply post-initialization legend configurations that require instance methods.
    
    Args:
        chart_instance: Chart instance with legend property
        legend_config (dict): Legend configuration dictionary
    """
    if not legend_config or not hasattr(chart_instance, 'legend'):
        return
        
    options_to_apply = {}
    
    color_mappings = {
        'title_fill_style': 'title_fill_style',
        'background_fill_style': 'background_fill_style'
    }
    for config_key, option_key in color_mappings.items():
        if config_key in legend_config:
            options_to_apply[option_key] = legend_config[config_key]
    
    if 'background_stroke_style' in legend_config:
        options_to_apply['background_stroke_style'] = legend_config['background_stroke_style']
    
    if 'orientation' in legend_config:
            options_to_apply['orientation'] = legend_config['orientation']

    if 'entries' in legend_config:
        entries = legend_config['entries']
        entries_options = {}

        if 'button_shape' in entries:
            entries_options['button_shape'] = entries['button_shape']
        
        entry_color_mappings = {
            'button_fill_style': 'button_fill_style',
            'text_fill_style': 'text_fill_style'
        }
        for config_key, option_key in entry_color_mappings.items():
            if config_key in entries:
                entries_options[option_key] = entries[config_key]
                
        if 'button_stroke_style' in entries:
            entries_options['button_stroke_style'] = entries['button_stroke_style']                
            
        if entries_options:
            options_to_apply['entries'] = entries_options
    
    if options_to_apply and hasattr(chart_instance.legend, 'set_options'):
        chart_instance.legend.set_options(**options_to_apply)
        
def build_series_legend_options(legend=None):
    """
    Build series legend options from dictionary.
    
    Args:
        legend (dict): Legend configuration dictionary
        
    Returns:
        dict: Processed legend options for series, or None if no options
    """
    if not legend:
        return None
        
    legend_options = {}    
    legend_params = {
        'show': 'show',
        'text': 'text',
        'button_shape': 'buttonShape',
        'button_size': 'buttonSize',
        'button_fill_style': 'buttonFillStyle',
        'button_stroke_style': 'buttonStrokeStyle',
        'button_rotation': 'buttonRotation',
        'text_font': 'textFont',
        'text_fill_style': 'textFillStyle',
        'match_style_exactly': 'matchStyleExactly',
        'highlight': 'highlight',
        'lut': 'lut',
        'lut_length': 'lutLength',
        'lut_thickness': 'lutThickness',
        'lut_display_proportional_steps': 'lutDisplayProportionalSteps',
        'lut_step_value_formatter': 'lutStepValueFormatter',
        'events': 'events'
    }
    color_params = {'button_fill_style', 'text_fill_style'}
    
    for kwarg_key, option_key in legend_params.items():
        value = legend.get(kwarg_key)
        if value is not None:
            if kwarg_key in color_params:
                from lightningchart.utils import convert_color_to_hex
                legend_options[option_key] = convert_color_to_hex(value)
            else:
                legend_options[option_key] = value
    return legend_options if legend_options else None


_JS_TYPEDARRAY_MAP = {
    0x11: ("int8", "int8"),
    0x12: ("uint8", "uint8"),
    0x13: ("int16", "int16"),
    0x14: ("uint16", "uint16"),
    0x15: ("int32", "int32"),
    0x16: ("uint32", "uint32"),
    0x17: ("float32", "float32"),
    0x18: ("float64", "float64"),
    0x19: ("uint8", "uint8"),
}

CSS_NAMED_COLORS = {
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "red": (255, 0, 0),
    "lime": (0, 255, 0),
    "blue": (0, 0, 255),
    "fuchsia": (255, 0, 255),
    "magenta": (255, 0, 255),
    "yellow": (255, 255, 0),
    "cyan": (0, 255, 255),
    "aqua": (0, 255, 255),
}

def _ext_to_array(ext: msgpack.ExtType, as_numpy: bool):
    code, data = ext.code, ext.data
    if code not in _JS_TYPEDARRAY_MAP:
        return ext
    _, np_dtype = _JS_TYPEDARRAY_MAP[code]
    if _HAS_NUMPY and as_numpy:
        return np.frombuffer(data, dtype=np_dtype).copy()
    import array as _array
    _pycode = {"int8": "b","uint8": "B","int16": "h","uint16": "H","int32": "i","uint32": "I","float32": "f","float64": "d"}[np_dtype]
    arr = _array.array(_pycode)
    arr.frombytes(data)
    return arr.tolist()
CSS_NAME_BY_RGB = {rgb: name for name, rgb in CSS_NAMED_COLORS.items()}
def _postprocess_readback(
    d,
    *,
    colors: Literal["uint32", "hex", "hex_rgba", "rgb", "html"] | None = None,
):
    """
    colors:
      - "uint32": keep/convert to np.uint32 (or list of ints)
      - "hex": add 'colorsHex' as '#RRGGBB'
      - "hex_rgba": add 'colorsHex' as '#RRGGBBAA'
      - "rgb": add 'colorsRGB' as 'rgb(r, g, b)' or 'rgba(r, g, b, a)'
      - "html": add 'colorsHTML' using exact CSS name if known (alpha==255), else hex/rgb fallback
    """
    cols = d.get("colors")
    if cols is None:
        return d

    try:
        import numpy as np
        u = np.asarray(cols).astype(np.uint32, copy=False)
        r = (u & 0xFF).astype(np.uint32, copy=False)
        g = ((u >> 8) & 0xFF).astype(np.uint32, copy=False)
        b = ((u >> 16) & 0xFF).astype(np.uint32, copy=False)
        a = ((u >> 24) & 0xFF).astype(np.uint32, copy=False)

        if colors == "uint32":
            d["colors"] = u

        if colors in ("hex", "hex_rgba"):
            if colors == "hex_rgba":
                d["colorsHex"] = [f"#{int(rr):02x}{int(gg):02x}{int(bb):02x}{int(aa):02x}"
                                  for rr, gg, bb, aa in zip(r, g, b, a)]
            else:
                d["colorsHex"] = [f"#{int(rr):02x}{int(gg):02x}{int(bb):02x}"
                                  for rr, gg, bb in zip(r, g, b)]

        if colors == "rgb":
            def fmt_rgb(rr, gg, bb, aa):
                return (f"rgb({rr}, {gg}, {bb})"
                        if aa == 255 else
                        f"rgba({rr}, {gg}, {bb}, {aa/255:.3f})")
            d["colorsRGB"] = [fmt_rgb(int(rr), int(gg), int(bb), int(aa))
                              for rr, gg, bb, aa in zip(r, g, b, a)]

        if colors == "html":
            out = []
            for rr, gg, bb, aa in zip(r, g, b, a):
                if aa == 255:
                    name = CSS_NAME_BY_RGB.get((int(rr), int(gg), int(bb)))
                    if name:
                        out.append(name)
                        continue
                    out.append(f"#{int(rr):02x}{int(gg):02x}{int(bb):02x}")
                else:
                    out.append(f"rgba({int(rr)}, {int(gg)}, {int(bb)}, {int(aa)/255:.3f})")
            d["colorsHTML"] = out

    except Exception:
        vals = [int(v) & 0xFFFFFFFF for v in cols]
        def split(u):
            return (u & 0xFF, (u >> 8) & 0xFF, (u >> 16) & 0xFF, (u >> 24) & 0xFF)

        if colors == "uint32":
            d["colors"] = vals

        if colors in ("hex", "hex_rgba"):
            if colors == "hex_rgba":
                d["colorsHex"] = [f"#{r:02x}{g:02x}{b:02x}{a:02x}" for r, g, b, a in map(split, vals)]
            else:
                d["colorsHex"] = [f"#{r:02x}{g:02x}{b:02x}" for r, g, b, _ in map(split, vals)]

        if colors == "rgb":
            def fmt_rgb(r, g, b, a):
                return f"rgb({r}, {g}, {b})" if a == 255 else f"rgba({r}, {g}, {b}, {a/255:.3f})"
            d["colorsRGB"] = [fmt_rgb(*split(u)) for u in vals]

        if colors == "html":
            out = []
            for u in vals:
                r, g, b, a = split(u)
                if a == 255:
                    name = CSS_NAME_BY_RGB.get((r, g, b))
                    out.append(name if name else f"#{r:02x}{g:02x}{b:02x}")
                else:
                    out.append(f"rgba({r}, {g}, {b}, {a/255:.3f})")
            d["colorsHTML"] = out

    return d

def _walk_decode(obj: Any, as_numpy: bool):
    if isinstance(obj, msgpack.ExtType):
        return _ext_to_array(obj, as_numpy)
    if isinstance(obj, dict):
        return {k: _walk_decode(v, as_numpy) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [ _walk_decode(v, as_numpy) for v in obj ]
    return obj

class LegendEntryOptions(TypedDict, total=False):
    """Configuration for legend.set_entry_options() method."""
    show: bool
    text: str
    button_shape: str
    button_size: Union[int, Dict[str, int]]
    button_fill_style: str
    button_stroke_style: Dict[str, Union[int, str]]
    button_rotation: float
    text_font: Dict[str, Union[int, str]]
    text_fill_style: str
    match_style_exactly: bool
    highlight: bool
    lut: Any
    lut_length: int
    lut_thickness: int
    lut_display_proportional_steps: bool
    lut_step_value_formatter: Any

class LegendOptions(TypedDict, total=False):
    """Configuration dictionary for chart legends."""
    visible: bool
    position: Union[str, Dict[str, Union[int, str]]]
    title: str
    title_font: Dict[str, Union[int, str]]
    title_fill_style: str
    orientation: str
    render_on_top: bool
    background_visible: bool
    background_fill_style: str
    background_stroke_style: Dict[str, Union[int, str]]
    padding: Union[int, Dict[str, int]]
    margin_inner: int
    margin_outer: Union[int, Dict[str, int]]
    entry_margin: int
    auto_hide_threshold: float
    add_entries_automatically: bool
    entries: LegendEntryOptions



def convert_for_serialization(obj):
    """Convert numpy/pandas types to JSON/msgpack-serializable types."""
    if isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, (datetime, pd.Timestamp)):
        return int(obj.timestamp() * 1000)
    elif isinstance(obj, np.datetime64):
        return int(obj.astype('datetime64[ms]').astype('int64'))
    elif isinstance(obj, date):
        return int(datetime.combine(obj, time()).timestamp() * 1000)
    elif hasattr(obj, '__class__') and 'Color' in str(type(obj)):
        from lightningchart.utils import convert_color_to_hex
        return convert_color_to_hex(obj)
    return None


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        result = convert_for_serialization(obj)
        if result is not None:
            return result
        return super().default(obj)


def msgpack_default(obj):
    result = convert_for_serialization(obj)
    if result is not None:
        return result
    return obj