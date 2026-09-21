export type Profile = {
  feature: string; page: number; source?: string; unit: 'mm'; note?: string;
} & (
  {kind?: undefined; detail: string; coordinateConvention: string; coordinateStatus: 'reviewed-unpaired-ordinates'; x: number[]; y: number[]; sourceRegionPoints?: [number, number, number, number]}
  | {kind: 'labelled-point-table'; axes: ('x' | 'y' | 'z')[]; coordinateSystem: string; points: {label: string; x?: number; y?: number; z?: number}[]}
  | {kind: 'independent-ordinate-sequence'; sequence: string; values: number[]; coordinateSystem: string}
);
export interface Size { width: number; height: number }
export interface Annotation { text: string; bbox: [number, number, number, number]; nearbyTokens: string[]; confidence?: number }
export interface Device {
  id: string; name: string; identifiers: string[];
  display: { activeMm: Size | null; nativePixels: Size | null; nominalPpi: number | null; ppi: {x: number; y: number} | null; source: string | null; resolutionReview?: Record<string, unknown> };
  bodyMm: {width: number | null; height: number | null; depth?: number | null} | null;
  coverGlassMm: Size | null;
  additionalDimensions: {feature: string; quantity: string; value: number; unit: 'mm' | 'degree' | 'percent'; page: number; source?: string; detail?: string; note?: string}[];
  features: Record<string, unknown>;
  profiles: Profile[];
  frontCameraPartial: {x: number | null; y: number | null} | null;
  frontCamera: { x: number; y: number; convention: string; source: string; page: number } | null;
  review: { status: string; derivation: string | null; source?: string; page?: number; bodyPage?: number; bodyDepthPage?: number; bodyDepthDefinition?: string | null; scope?: string; pagesReviewed?: number[]; ambiguities?: string[]; frontCameraCenterStatus?: string; frontCameraCenterDerivation?: string; measurementSources?: {source: string; pages: number[]}[]; audits?: Array<Record<string, unknown>> };
  drawing: { url: string; sha256: string; pages: {page: number; sizePoints: [number, number]; method: string; annotations: Annotation[]}[] } | null;
}
export interface Table { schemaVersion: number; sources: Record<string, unknown>; devices: Device[]; coverage: Record<string, unknown> }
export function getTable(): Table;
export function findDevice(id: string): Device | undefined;
export function pixelsPerInch(device: string | Device): {x: number; y: number};
export function mmToNativePixels(device: string | Device, mm: number, axis?: 'x' | 'y'): number;
export function mmToViewportPixels(device: string | Device, mm: number, viewportWidth: number, orientation?: 'portrait' | 'landscape'): number;
