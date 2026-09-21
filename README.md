# Device dimensions

One JSON catalogue, shared by **`@appmana-public/device-dimensions`** (npm) and **`device-dimensions`** (Python). Physical device measurements, Apple hardware identifiers, native panel resolutions and source provenance for positioning content on real hardware.

The packages are prepared for publication; no registry release or CI configuration is included yet.

```js
import {findDevice, pixelsPerInch, mmToNativePixels} from '@appmana-public/device-dimensions';
const ipad = findDevice('iPad16,5');
console.log(pixelsPerInch(ipad)); // independent x/y PPI from measured active display
console.log(mmToNativePixels(ipad, 25.4)); // one physical inch in native panel pixels
```

```python
from device_dimensions import find_device, pixels_per_inch, mm_to_native_pixels
ipad = find_device('iPad16,5')
print(pixels_per_inch(ipad))
print(mm_to_native_pixels(ipad, 25.4))
```

The JSON export is `@appmana-public/device-dimensions/data`; Python uses `get_table()`. Both ship exactly `src/device_dimensions/devices.json`. No generated duplicate dataset or runtime network request is involved. npm requires Node 20.18+, 22.12+, or a bundler supporting JSON import attributes.

## Coverage and review status

The 2026-09-21 snapshot contains **282 device records, 359 unique hardware identifiers, 129 native panel resolutions, and all 90 PDFs / 259 drawing pages linked by Apple's current dimensional drawing index**. Historical identifier-only records are retained with unavailable physical fields set to `null`.

**This is not yet a complete semantic translation of every drawing.** Sixty-nine active-display rectangles and twenty-two front-camera locations have normalized, reviewed geometry. Remaining drawing content is represented by page-positioned numerical annotations, with nearby short label tokens for review. PDF extraction and OCR can miss annotations, misread digits, and include sheet numbers or other non-dimensional numbers. A raw annotation is deliberately not labelled a millimetre measurement, and is never used by physical conversion APIs. OCR confidence is not a substitute for review. The complete original documents remain linked; PDFs and page imagery are not redistributed.

`review.status`, `review.scope`, `review.derivation`, `review.page` and `review.bodyPage` / `review.bodyDepthPage` explain normalized values and their individual source pages. `drawing.pages[].method` distinguishes PDF text from unreviewed OCR. `bbox` uses **PDF points**, from each page's upper-left origin, and is solely for locating the source annotation. It is not a physical coordinate on the device. Full sheet topology, tolerance associations, feature identities and rotation are not inferred from nearest labels.

Reviewed display and body geometry covers **all 22 iPads and all 27 iPhones on the current drawing index**, plus iPhone SE 2nd generation because the SE drawing explicitly covers both generations. Cover-glass dimensions are normalized for all 27 indexed iPhones. Camera locations cover 20 iPads and both SE generations. The two iPad mini drawings do not unambiguously locate the camera vertically: the nearby 4.38 mm callout identifies the cellular ambient-light sensor, so it is not substituted as camera Y. Other unavailable camera locations remain null, including drawings that specify only a combined sensor keepout region.

All 19 indexed Watch drawings also have active display envelopes, case dimensions and separately labelled total thickness including the rear sensor. All 22 other indexed accessory/computer drawings have some reviewed fields, with explicit review scopes: case dimensions, charger diameters, connector or clearance measurements as available. These are partial reviews, not full translations. Earbud keepout regions are not treated as body envelopes; undimensioned remote heights and case depths remain null. Headset dimensions depend on the documented stowed/worn configuration.

Feature review includes camera/sensor, acoustic, button and connector geometry for 12 iPad models and 10 recent iPhones. Air M2/M3/M4 and iPad A16/10th-generation shared-applicability drawings are explicitly cited per measurement. `features` preserves nested per-measurement provenance and partial contour points; `profiles` preserves separately dimensioned local x/y ordinates, which must not be zipped into polygon points. Keepout cone angles describe accessory clearance, not measured camera field of view. Combined front camera/sensor keepout centres are separate from individual camera centres, which remain unavailable where not dimensioned.

## Coordinate and scale conventions

`display.activeMm` and `nativePixels` are portrait width/height; active display dimensions refer to the full bounding rectangle, not the rounded-corner cutout. Native pixels are panel pixels, not necessarily iOS render-buffer pixels or CSS pixels. PPI is calculated independently for x and y: `nativePixels * 25.4 / activeMm`. Rounded nominal PPI is retained separately from DeviceKit and is **not independently verified**; it is never used to invent physical dimensions. Published drawing precision limits the computed PPI's meaningful precision.

`frontCamera` is in millimetres relative to the **portrait body centre**, +x right and +y up when viewing the screen. It describes the drawing's mechanical camera reference, not experimentally measured entrance-pupil position, lens intrinsics or capture field of view. Display-to-body-centre offsets must be handled separately if a future device has asymmetric margins.

`mmToViewportPixels` / `mm_to_viewport_pixels` assume the supplied viewport spans the full physical display width in the supplied orientation. They are unsuitable for partial windows, split-screen, page zoom, or embedded viewports without separate calibration. Neither DPR nor Safari's user-agent identifies physical hardware reliably. Select a device explicitly or obtain its hardware identifier from a native host.

All conversion helpers throw for missing normalized geometry, invalid numbers or invalid axes. They do not fall back to estimated PPI. `findDevice` returns undefined / None for unknown identity; table and record accessors return isolated copies.

## Sources and reproduction

- [Apple dimensional drawings](https://developer.apple.com/accessories/dimensional-drawings/): each record includes URL and SHA-256. Current index coverage is not historical PDF coverage.
- [DeviceKit](https://github.com/devicekit/DeviceKit/tree/9000b09deb528298f493a69cae55663c8d85983e): pinned MIT source for current identifiers and technical-spec links. Exact native resolutions are extracted from those **Apple support pages**, not calculated from rounded diagonal/PPI values. The iPad Pro 13 M5 source URL is corrected to [Apple 125407](https://support.apple.com/en-us/125407); upstream points at the 11-inch model.
- Explicit Apple resolution overrides in `scripts/resolution-overrides.json` record source derivations for Watch specifications that omit pixels and resolve three marketing-name mismatches.
- [apple_device_identifiers](https://github.com/clo4/apple_device_identifiers): pinned commit in the table, public-domain historical identifiers. DeviceKit identity takes precedence where names differ.

Extraction requires Python 3.10+, BeautifulSoup (`pip install beautifulsoup4`), Poppler (`pdftotext`, `pdftoppm`), and Tesseract. Runtime packages have no third-party dependencies.

```sh
python3 scripts/download_drawings.py
python3 scripts/extract_drawings.py
# Clone source repositories into the ignored cache, using the SHAs in the table:
git clone https://github.com/devicekit/DeviceKit .cache/DeviceKit
git -C .cache/DeviceKit checkout 9000b09deb528298f493a69cae55663c8d85983e
git clone https://github.com/clo4/apple_device_identifiers .cache/apple_device_identifiers
# Check out the appleIdentifiers.commit from the checked-in table before rebuilding.
python3 scripts/extract_resolutions.py
python3 scripts/build_table.py
python3 scripts/validate.py
npm test
PYTHONPATH=src python3 -m unittest discover -s tests
npm pack
python3 -m build
```

Reviewed geometry edits live in the `scripts/*reviewed-geometry.json` source files; the installed runtime has only one catalogue. Review each added field against its source sheet, specify its coordinate convention and derivation, and add a regression fixture before including it in physical conversions. Do not promote OCR annotations automatically. CI integration and registry publication are left to the maintainer.
