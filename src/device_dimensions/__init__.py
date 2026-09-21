"""Physical display conversions using the same JSON table as the npm distribution."""
from importlib.resources import files
import copy
import json
import math

_TABLE = json.loads(files(__package__).joinpath('devices.json').read_text(encoding='utf8'))

def get_table() -> dict:
    return copy.deepcopy(_TABLE)

def find_device(identifier: str) -> dict | None:
    matches = [d for d in _TABLE['devices'] if d['id'] == identifier or identifier in d['identifiers']]
    if len(matches) > 1:
        raise ValueError(f'Ambiguous hardware identifier: {identifier}')
    return copy.deepcopy(matches[0]) if matches else None

def _geometry(device: str | dict) -> dict:
    d = find_device(device) if isinstance(device, str) else device
    if not d or not d['display']['activeMm'] or not d['display']['nativePixels']:
        raise ValueError('Verified physical display and native pixel dimensions required')
    return d['display']

def pixels_per_inch(device: str | dict) -> dict[str, float]:
    d = _geometry(device)
    return {axis: d['nativePixels'][dimension] * 25.4 / d['activeMm'][dimension] for axis, dimension in [('x', 'width'), ('y', 'height')]}

def mm_to_native_pixels(device: str | dict, mm: float, axis: str = 'x') -> float:
    if not math.isfinite(mm) or axis not in ('x', 'y'):
        raise ValueError('Finite millimetres and x/y axis required')
    return mm * pixels_per_inch(device)[axis] / 25.4

def mm_to_viewport_pixels(device: str | dict, mm: float, viewport_width: float, orientation: str = 'portrait') -> float:
    if not math.isfinite(mm) or not math.isfinite(viewport_width) or viewport_width <= 0 or orientation not in ('portrait', 'landscape'):
        raise ValueError('Invalid physical/viewport geometry')
    d = _geometry(device)
    return mm * viewport_width / d['activeMm']['width' if orientation == 'portrait' else 'height']
