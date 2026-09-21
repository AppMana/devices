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
test('all indexed phones and tablets have reviewed physical scale', () => {
 const devices=getTable().devices.filter(d=>d.drawing && /^(ipad|iphone)-/.test(d.id));
 assert.equal(devices.length,49);
 for(const d of devices){
   assert.ok(d.bodyMm.width>d.display.activeMm.width,d.id);
   assert.ok(d.bodyMm.height>d.display.activeMm.height,d.id);
   assert.ok(d.bodyMm.depth>0,d.id);
   for(const axis of ['x','y']) assert.ok(pixelsPerInch(d)[axis]>200 && pixelsPerInch(d)[axis]<500,d.id);
 }
 // Similar names do not imply identical panels, bodies, or camera offsets.
 assert.equal(findDevice('iphone-17').display.activeMm.height,144.79);
 assert.equal(findDevice('iphone-17-pro').display.activeMm.height,144.73);
 assert.equal(findDevice('ipad-10th-generation').display.activeMm.width,158.94);
 assert.equal(findDevice('ipad-mini-6th-generation').frontCamera,null);
 assert.deepEqual(findDevice('iphone-se-2nd-generation').frontCamera,findDevice('iphone-se-3rd-generation').frontCamera);
 assert.equal(findDevice('iphone-se-3rd-generation').frontCamera.x,-10.655);
});

test('reviewed accessory dimensions preserve mechanical meaning and unknowns', () => {
 const t=getTable();assert.equal(t.coverage.reviewedDrawings,90);
 const watches=t.devices.filter(d=>d.drawing && d.id.startsWith('apple-watch-'));
 assert.equal(watches.length,19);
 assert.equal(findDevice('Watch7,13').id,'apple-watch-se-3-40mm');
 assert.equal(findDevice('Watch7,5').id,'apple-watch-ultra-2');
 for(const d of watches) assert.ok(pixelsPerInch(d).x>300 && pixelsPerInch(d).x<350,d.id);
 for(const d of watches){
  assert.ok(d.display.activeMm.width<d.bodyMm.width,d.id);
  assert.ok(d.additionalDimensions.find(v=>v.feature==='body-including-rear-sensor').value>d.bodyMm.depth,d.id);
 }
 assert.equal(findDevice('apple-watch-ultra-3').display.activeMm.width,32.92);
 assert.equal(findDevice('siri-remote-3rd-generation').bodyMm.height,null);
 assert.equal(findDevice('airpods-4').bodyMm,null);
 assert.equal(findDevice('wireless-charging-case-usb-c-for-airpods-4').bodyMm.depth,null);
 assert.equal(findDevice('apple-magsafe-charger').bodyMm.depth,5.30);
 assert.equal(findDevice('apple-magsafe-charger-1-m-and-apple-magsafe-charger-2-m').bodyMm.depth,4.37);
 assert.throws(()=>pixelsPerInch('macbook-neo'));
});

test('feature geometry retains source meaning and separate contour axes', () => {
 const p=findDevice('ipad-pro-13-inch-m4');
 const corner=p.profiles.find(v=>v.detail==='Z');
 assert.equal(corner.coordinateStatus,'reviewed-unpaired-ordinates');
 assert.ok(corner.x.includes(14.68));assert.ok(corner.y.includes(14.62));
 assert.equal(p.additionalDimensions.find(v=>v.feature==='front-camera-keepout' && v.quantity==='included-angle').value,121.01);
 const phone=findDevice('iphone-17');assert.equal(phone.frontCamera,null);
 assert.equal(phone.features.combinedFrontCameraAndSensorsKeepout.dimensions.width.value,20.75);
 assert.equal(findDevice('iphone-17-pro').features.combinedFrontCameraAndSensorsKeepout.dimensions.width.value,19.74);
 assert.equal(phone.review.frontCameraCenterStatus,'not-individually-dimensioned');
});
