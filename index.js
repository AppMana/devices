import table from './src/device_dimensions/devices.json' with { type: 'json' };
/** A fresh copy prevents consumers from mutating the shared catalogue. */
export const getTable = () => structuredClone(table);
export function findDevice(id) {
  const matches = table.devices.filter(d => d.id === id || d.identifiers.includes(id));
  if (matches.length > 1) throw new Error(`Ambiguous hardware identifier: ${id}`);
  return matches.length ? structuredClone(matches[0]) : undefined;
}
function geometry(id) {
  const device = typeof id === 'string' ? findDevice(id) : id;
  if (!device?.display?.activeMm || !device?.display?.nativePixels) throw new Error('Verified physical display and native pixel dimensions required');
  return device.display;
}
export function pixelsPerInch(device) {
  const d = geometry(device);
  return {x: d.nativePixels.width * 25.4 / d.activeMm.width, y: d.nativePixels.height * 25.4 / d.activeMm.height};
}
export function mmToNativePixels(device, mm, axis = 'x') {
  if (!Number.isFinite(mm) || !['x', 'y'].includes(axis)) throw new TypeError('Finite millimetres and x/y axis required');
  return mm * pixelsPerInch(device)[axis] / 25.4;
}
/** Layout viewport width, not DPR, establishes physical scale. Browser zoom must be accounted for by caller. */
export function mmToViewportPixels(device, mm, viewportWidth, orientation = 'portrait') {
  if (!Number.isFinite(mm) || !Number.isFinite(viewportWidth) || viewportWidth <= 0 || !['portrait', 'landscape'].includes(orientation)) throw new TypeError('Invalid physical/viewport geometry');
  const d = geometry(device);
  return mm * viewportWidth / d.activeMm[orientation === 'portrait' ? 'width' : 'height'];
}
