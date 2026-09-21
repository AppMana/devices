"""Join source records. Deliberately do not convert nominal PPI into measured millimetres."""
import json,pathlib,re,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1]; C=ROOT/'.cache'
def slug(s):return re.sub(r'[^a-z0-9]+','-',s.lower().replace('ʀ','r')).strip('-')
def main():
    drawings=json.loads((C/'drawings.json').read_text()); resolution=json.loads((C/'resolutions.json').read_text()); identifiers=json.loads((C/'apple_device_identifiers/devices.json').read_text())
    reviewed={}
    for name in ('reviewed-geometry.json','iphone-reviewed-geometry.json','ipad-reviewed-geometry.json','watch-reviewed-geometry.json','accessory-reviewed-geometry.json'):
        path=ROOT/'scripts'/name
        if path.exists():
            for d in json.loads(path.read_text()):reviewed[d['id']]=d
    records={}
    def blank(id,name):return dict(id=id,name=name,identifiers=[],display=dict(activeMm=None,nativePixels=None,nominalPpi=None,ppi=None,source=None),bodyMm=None,coverGlassMm=None,additionalDimensions=[],features={},profiles=[],frontCameraPartial=None,frontCamera=None,review=dict(status='unreviewed',derivation=None),drawing=None)
    for d in drawings:
        r=blank(d['id'],d['name']);r['drawing']={k:d[k] for k in ('url','sha256','pages')};records[r['id']]=r
    for d in resolution['records']:
        id=slug(d['name']);matches=[r for r in records.values() if slug(r['name'])==id]
        r=matches[0] if len(matches)==1 else records.setdefault(id,blank(id,d['name']))
        r['identifiers']=sorted(set(r['identifiers']+d['identifiers']))
        r['display'].update(nativePixels=d['resolution'],nominalPpi=d['pixelsPerInch'],source=d['specUrl'])
    for name,ids in identifiers.items():
        ids=[ids] if isinstance(ids,str) else ids
        # Overlapping hardware identity is stronger than inconsistent marketing names.
        matches=[r for r in records.values() if set(r['identifiers']) & set(ids)]
        if not matches:matches=[r for r in records.values() if slug(r['name'])==slug(name)]
        if len(matches)==1:r=matches[0]
        elif matches:continue # multiple device variants already covered individually
        else:r=records.setdefault(slug(name),blank(slug(name),name))
        r['identifiers']=sorted(set(r['identifiers']+ids))
    overrides=json.loads((ROOT/'scripts/resolution-overrides.json').read_text())
    for id,d in overrides.items():
        r=records[id]
        for alias in d.get('mergeAliases',[]):
            old=records.pop(alias,None)
            if old:
                assert not old['drawing'], 'Cannot silently discard drawing'
                r['identifiers']=sorted(set(r['identifiers']+old['identifiers']))
                r['display']['nominalPpi']=old['display']['nominalPpi']
        r['identifiers']=sorted(set(r['identifiers']+d['machineIds']))
        r['display'].update(nativePixels=d['resolution'],source=d['sourceURL'],resolutionReview={k:v for k,v in d.items() if k not in ('resolution','machineIds','mergeAliases')})
    for id,d in reviewed.items():
        r=records[id];r['display']['activeMm']=d['activeDisplayMm'];r['review']=dict(status=d['mechanicalStatus'],derivation=d.get('derivation'))
        r['identifiers']=sorted(set(r['identifiers']+d.get('machineIds',[])))
        r['bodyMm']=d.get('bodyMm');r['coverGlassMm']=d.get('coverGlassMm');r['additionalDimensions']=d.get('additionalDimensions',[])
        r['review']['source']=d['drawingUrl'];r['review']['page']=d['sourcePage']
        r['review']['bodyPage']=d.get('bodySourcePage',d['sourcePage'])
        r['review']['bodyDepthDefinition']=d.get('bodyDepthDefinition')
        if d.get('totalDepthIncludingSensorMm') is not None:r['additionalDimensions'].append(dict(feature='body-including-rear-sensor',quantity='depth',value=d['totalDepthIncludingSensorMm'],unit='mm',page=d['totalDepthSourcePage']))
        r['review']['bodyDepthPage']=d.get('bodyDepthSourcePage',d['sourcePage'])
        r['review']['pagesReviewed']=d.get('sourcePagesReviewed',[d['sourcePage']])
        r['review']['ambiguities']=d.get('ambiguities',[])
        r['frontCameraPartial']=d.get('frontCameraPartialPortraitMm')
        r['review']['scope']=d.get('reviewScope','Display/body/glass and explicitly located camera only; other features remain in raw annotations.')
        if d.get('frontCameraPortraitMm'):
            r['frontCamera']=dict(**d['frontCameraPortraitMm'],convention='portrait body centre; +x right, +y up; millimetres',source=d['drawingUrl'],page=d['sourcePage'])
        if id=='ipad-pro-11-inch-m4' and not r['bodyMm']:r['bodyMm']=dict(width=177.51,height=249.70)
        if id=='ipad-pro-13-inch-m4' and not r['bodyMm']:r['bodyMm']=dict(width=215.53,height=281.58)
        if id=='iphone-15-pro-max' and not r['bodyMm']:r['bodyMm']=dict(width=76.73,height=159.86)
        if r['display']['nativePixels'] and r['display']['activeMm']:
            r['display']['ppi']={axis:r['display']['nativePixels'][key]*25.4/r['display']['activeMm'][key] for axis,key in [('x','width'),('y','height')]}
    for filename in ('ipad-feature-review.json','iphone-camera-feature-review.json','watch-feature-review.json','accessory-feature-review.json'):
        path=ROOT/'scripts'/filename
        if not path.exists():continue
        additions=json.loads(path.read_text())
        for d in (additions.values() if isinstance(additions,dict) else additions):
            r=records[d['id']]
            r['features'].update(d.get('features',{}))
            r['review']['ambiguities'].extend(d.get('ambiguities',[]))
            if d.get('frontCameraCenterStatus'):r['review']['frontCameraCenterStatus']=d['frontCameraCenterStatus']
            if d.get('frontCameraCenterDerivation'):r['review']['frontCameraCenterDerivation']=d['frontCameraCenterDerivation']
            r['additionalDimensions'].extend(d.get('additionalDimensions',[]))
            r['profiles'].extend(d.get('profiles',[]))
            r['review']['pagesReviewed']=sorted(set(r['review']['pagesReviewed']+d.get('sourcePagesReviewed',[])))
            if d.get('reviewScope'):r['review']['scope']=d['reviewScope']
    se2=records.get('iphone-se-2nd-generation');se3=records.get('iphone-se-3rd-generation')
    if se2 and se3:
        import copy
        for key in ('bodyMm','coverGlassMm','additionalDimensions','frontCamera','review'):se2[key]=copy.deepcopy(se3[key])
        se2['display']['activeMm']=copy.deepcopy(se3['display']['activeMm'])
        se2['display']['ppi']={axis:se2['display']['nativePixels'][key]*25.4/se2['display']['activeMm'][key] for axis,key in [('x','width'),('y','height')]}
    for r in records.values():
        for d in r['additionalDimensions']+r['profiles']:d.setdefault('source',r['review'].get('source'))
    rows=sorted(records.values(),key=lambda r:r['id'])
    def scalar_count(node):
        if isinstance(node,dict):return int('value' in node)+sum(scalar_count(v) for v in node.values())
        if isinstance(node,list):return sum(scalar_count(v) for v in node)
        return 0
    def profile_count(p):
        if p.get('kind')=='labelled-point-table':return len(p['points'])*len(p['axes'])
        if p.get('kind')=='independent-ordinate-sequence':return len(p['values'])
        return len(p['x'])+len(p['y'])
    table=dict(schemaVersion=1,sources=dict(appleDrawings=dict(url='https://developer.apple.com/accessories/dimensional-drawings/',retrieved='2026-09-21'),deviceKit=resolution['source'],appleIdentifiers=dict(url='https://github.com/clo4/apple_device_identifiers',commit=subprocess.check_output(['git','-C',str(C/'apple_device_identifiers'),'rev-parse','HEAD']).decode().strip(),license='Unlicense')),coverage=dict(devices=len(rows),drawings=len(drawings),reviewedDrawings=sum(bool(r['drawing']) and r['review']['status']!='unreviewed' for r in rows),drawingPages=sum(len(d['pages']) for d in drawings),nativeResolutions=sum(bool(r['display']['nativePixels']) for r in rows),reviewedDisplays=sum(bool(r['display']['activeMm']) for r in rows),reviewedCameras=sum(bool(r['frontCamera']) for r in rows),structuredFeatureRecords=sum(bool(r['features']) for r in rows),namedDimensionMeasurements=sum(len(r['additionalDimensions']) for r in rows),structuredFeatureMeasurements=sum(scalar_count(r['features']) for r in rows),contourOrdinateValues=sum(profile_count(p) for r in rows for p in r['profiles']),note='All current index PDFs are represented; positioned annotations are an extraction aid, not a complete semantic translation. OCR and numerical-token extraction can omit or misread dimensions. Only reviewed fields are used for physical conversions.'),devices=rows)
    (ROOT/'src/device_dimensions/devices.json').write_text(json.dumps(table,indent=2,ensure_ascii=False)+'\n'); print(json.dumps(table['coverage'],indent=2))
if __name__=='__main__':main()
