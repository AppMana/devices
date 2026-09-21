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
 assert.equal(findDevice('iphone-se-3rd-generation').frontCamera.x,-10.645);
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
 assert.equal(findDevice('iphone-16e').features.connectorKeepout.dimensions.endRadius.value,3.25);
 assert.equal(findDevice('iphone-17e').features.connectorKeepout.dimensions.endRadius.value,3.30);
 const air=findDevice('ipad-air-11-inch-m2').additionalDimensions.find(v=>v.feature==='rear-camera-lens');
 assert.equal(air.value,9.85);assert.ok(air.source.endsWith('ipad-air-11-inch-m4.pdf'));
 assert.equal(findDevice('ipad-a16').features.generalDrawingTolerances.dimensions.twoDecimals.value,.1);
});

test('generation-specific imaging clearances and magnetic datums are preserved', () => {
 const dim=(id,feature,quantity)=>findDevice(id).additionalDimensions.find(d=>d.feature===feature && d.quantity===quantity).value;
 assert.equal(dim('ipad-pro-11-inch-4th-generation','infrared-camera-keepout','included-angle'),85);
 assert.equal(dim('ipad-pro-12.9-inch-6th-generation','infrared-camera-keepout','included-angle'),95);
 assert.equal(dim('ipad-pro-11-inch-3rd-generation','rear-flash-aperture','diameter'),4);
 assert.equal(dim('ipad-pro-11-inch-4th-generation','rear-flash-aperture','diameter'),3.75);
 assert.equal(dim('ipad-8th-generation','front-camera-aperture','diameter'),2.45);
 const magnetic=findDevice('ipad-pro-13-inch-m4').features.magnetDetail;
 assert.equal(magnetic.leftEdgeMagnets.length,12);
 assert.equal(magnetic.leftEdgeMagnets[0].center.x.value,-102.11);
 assert.equal(magnetic.leftEdgeMagnets[2].center.x.value,-101.83);
 assert.equal(magnetic.magneticKeepouts.rightMagnetExclusion.yMin.value,106.04);
 assert.match(magnetic.coordinateConvention,/smart-connector pin/);
});

test('magnet tables retain irregular positions and polarity column conventions', () => {
 const detail=findDevice('ipad-pro-11-inch-m4').features.magnetDetail;
 const magnet=label=>detail.otherMagnetsAndShunt.find(m=>m.label===label);
 assert.equal(magnet('BV4-11').center.x.value,-29.98);
 assert.equal(magnet('BV4-12').center.x.value,-29.23);
 assert.equal(magnet('BV2-13').center.x.value,33.37);
 assert.equal(magnet('PM-FH-1').center.y,null);
 const air=findDevice('ipad-air-11-inch-m2').features.magnetDetail;
 const a=label=>air.magnets.find(m=>m.label===label);
 assert.equal(a('BV1-11').polarityTowardSurface,'N');
 assert.equal(a('BV1-11').polarityTowardInside,'S');
 assert.equal(a('SP-CH-1').center.x,null);
 assert.equal(a('PM-FH-1').center.y.value,136.51);
 assert.ok(a('PM-FH-1').center.y.source.endsWith('ipad-air-11-inch-m4.pdf'));
});

test('Watch tables preserve paired local axes independently of unpaired profiles', () => {
 const p=findDevice('apple-watch-series-10-42mm').profiles;
 const side=p.find(p=>p.feature==='case-side-contour');
 assert.equal(side.kind,'labelled-point-table');
 assert.deepEqual(side.axes,['y','z']);
 assert.deepEqual(side.points[0],{label:'S-A',y:6.83,z:9.7});
 const old=findDevice('apple-watch-se-3-40mm').profiles[0];
 assert.equal(old.kind,'independent-ordinate-sequence');
 assert.equal(old.points,undefined);
 const table=getTable();assert.ok(table.coverage.contourOrdinateValues>2000);
});


test('magnetic segment boundaries remain distinct from centers and revisions', () => {
 const a=findDevice('ipad-8th-generation').features.magneticMounting;
 const b=findDevice('ipad-9th-generation').features.magneticMounting;
 assert.equal(a.coverFlap.segments.length,10);
 assert.equal(b.spine.leftSegments.length,12);
 assert.equal(a.coverFlap.segments[0].xMin.value,-47.38);
 assert.equal(b.coverFlap.segments[0].xMin.value,-47.37);
 assert.equal(a.coverFlap.yMin,null);
 assert.equal(a.coverFlap.polarityFacing,'cover glass');
 assert.equal(a.spine.polarityFacing,'outside of product');
 assert.equal(a.sensors.hallEffect1.x.value,-113.41);
 const dims=findDevice('ipad-air-5th-generation').additionalDimensions;
 assert.equal(dims.find(x=>x.feature==='volume-buttons' && x.quantity==='width').value,2.56);
 assert.equal(dims.find(x=>x.feature==='volume-buttons' && x.quantity==='gap-between-buttons').value,2);
});

test('mechanical datums distinguish edges, gaps and control centers', () => {
 const measure=(id,feature,quantity)=>findDevice(id).additionalDimensions.find(x=>x.feature===feature&&x.quantity===quantity)?.value;
 assert.equal(measure('ipad-8th-generation','home-button','center-from-bottom'),10.06);
 assert.equal(measure('ipad-8th-generation','home-button','diameter'),undefined);
 assert.equal(measure('ipad-8th-generation','display-active-area','side-margin'),9.28);
 assert.equal(measure('ipad-a16','volume-buttons','width'),2.56);
 assert.equal(measure('ipad-a16','volume-buttons','gap-between-buttons'),2);
 assert.equal(measure('ipad-a16','sleep-wake-button','right-end-from-right'),15.15);
 assert.equal(measure('ipad-air-11-inch-m4','inductive-charger-window','section-width'),3.11);
 assert.equal(measure('ipad-air-11-inch-m4','volume-button','section-nearest-edge-to-cover-glass'),1.81);
});
