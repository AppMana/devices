export interface Size { width: number; height: number }
export interface Annotation { text: string; bbox: [number, number, number, number]; nearbyTokens: string[]; confidence?: number }
export interface Device {
  id: string; name: string; identifiers: string[];
  display: { activeMm: Size | null; nativePixels: Size | null; nominalPpi: number | null; ppi: {x: number; y: number} | null; source: string | null };
  bodyMm: {width: number; height: number; depth?: number} | null;
  frontCamera: { x: number; y: number; convention: string; source: string; page: number } | null;
  review: { status: string; derivation: string | null };
  drawing: { url: string; sha256: string; pages: {page: number; sizePoints: [number, number]; method: string; annotations: Annotation[]}[] } | null;
}
export interface Table { schemaVersion: number; sources: Record<string, unknown>; devices: Device[]; coverage: Record<string, unknown> }
export function getTable(): Table;
export function findDevice(id: string): Device | undefined;
export function pixelsPerInch(device: string | Device): {x: number; y: number};
export function mmToNativePixels(device: string | Device, mm: number, axis?: 'x' | 'y'): number;
export function mmToViewportPixels(device: string | Device, mm: number, viewportWidth: number, orientation?: 'portrait' | 'landscape'): number;
