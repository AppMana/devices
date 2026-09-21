"""Join source records. Deliberately do not convert nominal PPI into measured millimetres."""
import json,pathlib,re,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1]; C=ROOT/'.cache'
def slug(s):return re.sub(r'[^a-z0-9]+','-',s.lower().replace('ʀ','r')).strip('-')
def main():
    drawings=json.loads((C/'drawings.json').read_text()); resolution=json.loads((C/'resolutions.json').read_text()); identifiers=json.loads((C/'apple_device_identifiers/devices.json').read_text())
    reviewed={d['id']:d for d in json.loads((ROOT/'scripts/reviewed-geometry.json').read_text())}
    records={}
    def blank(id,name):return dict(id=id,name=name,identifiers=[],display=dict(activeMm=None,nativePixels=None,nominalPpi=None,ppi=None,source=None),bodyMm=None,frontCamera=None,review=dict(status='unreviewed',derivation=None),drawing=None)
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
    for id,d in reviewed.items():
        r=records[id];r['display']['activeMm']=d['activeDisplayMm'];r['review']=dict(status=d['mechanicalStatus'],derivation=d.get('derivation'))
        r['identifiers']=sorted(set(r['identifiers']+d.get('machineIds',[])))
        if d.get('frontCameraPortraitMm'):
            r['frontCamera']=dict(**d['frontCameraPortraitMm'],convention='portrait body centre; +x right, +y up; millimetres',source=d['drawingUrl'],page=d['sourcePage'])
        if id=='ipad-pro-11-inch-m4':r['bodyMm']=dict(width=177.51,height=249.70)
        if id=='ipad-pro-13-inch-m4':r['bodyMm']=dict(width=215.53,height=281.58)
        if id=='iphone-15-pro-max':r['bodyMm']=dict(width=76.73,height=159.86)
        if r['display']['nativePixels']:
            r['display']['ppi']={axis:r['display']['nativePixels'][key]*25.4/r['display']['activeMm'][key] for axis,key in [('x','width'),('y','height')]}
    rows=sorted(records.values(),key=lambda r:r['id'])
    table=dict(schemaVersion=1,sources=dict(appleDrawings=dict(url='https://developer.apple.com/accessories/dimensional-drawings/',retrieved='2026-09-21'),deviceKit=resolution['source'],appleIdentifiers=dict(url='https://github.com/clo4/apple_device_identifiers',commit=subprocess.check_output(['git','-C',str(C/'apple_device_identifiers'),'rev-parse','HEAD']).decode().strip(),license='Unlicense')),coverage=dict(devices=len(rows),drawings=len(drawings),drawingPages=sum(len(d['pages']) for d in drawings),nativeResolutions=sum(bool(r['display']['nativePixels']) for r in rows),reviewedDisplays=sum(bool(r['display']['activeMm']) for r in rows),reviewedCameras=sum(bool(r['frontCamera']) for r in rows),note='All current index PDFs are represented; positioned annotations are an extraction aid, not a complete semantic translation. OCR and numerical-token extraction can omit or misread dimensions. Only reviewed fields are used for physical conversions.'),devices=rows)
    (ROOT/'src/device_dimensions/devices.json').write_text(json.dumps(table,indent=2,ensure_ascii=False)+'\n'); print(json.dumps(table['coverage'],indent=2))
if __name__=='__main__':main()
