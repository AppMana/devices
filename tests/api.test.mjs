import test from 'node:test';
import assert from 'node:assert/strict';
import {findDevice, getTable, pixelsPerInch, mmToNativePixels, mmToViewportPixels} from '../index.js';
test('native pixels use measured dimensions rather than rounded marketing PPI', () => {
 const d=findDevice('iPad16,5');
 assert.equal(d.id,'ipad-pro-13-inch-m4');
 assert.ok(Math.abs(mmToNativePixels(d,199.14)-2064)<1e-9);
 assert.ok(Math.abs(pixelsPerInch(d).x-263.260018)<0.00001);
 assert.equal(mmToViewportPixels(d,199.14,1032),1032);
 assert.equal(mmToViewportPixels(d,265.19,1376,'landscape'),1376);
});
test('unknown geometry fails explicitly', () => {
 assert.equal(findDevice('unknown'),undefined);
 assert.throws(()=>pixelsPerInch('iphone-4'));
 assert.throws(()=>mmToNativePixels('iPad16,5',NaN));
 assert.throws(()=>mmToViewportPixels('iPad16,5',25.4,0));
});
test('X and XR remain distinct; returned records do not mutate dataset', () => {
 assert.deepEqual(findDevice('iPhone10,3').display.nativePixels,{width:1125,height:2436});
 assert.deepEqual(findDevice('iPhone11,8').display.nativePixels,{width:828,height:1792});
 const d=findDevice('iPad16,5');d.display.activeMm.width=1;
 assert.equal(findDevice('iPad16,5').display.activeMm.width,199.14);
 const t=getTable();t.devices.length=0;assert.ok(getTable().devices.length>200);
});
