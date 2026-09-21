import json,math,pathlib
root=pathlib.Path(__file__).resolve().parents[1];table=json.loads((root/'src/device_dimensions/devices.json').read_text())
ids=set(); hardware=set()
for d in table['devices']:
    assert d['id'] not in ids,d['id'];ids.add(d['id'])
    for id in d['identifiers']:
        assert id not in hardware, f'Duplicate hardware ID {id}';hardware.add(id)
    if d['drawing']:
        assert len(d['drawing']['sha256'])==64
        for p in d['drawing']['pages']:
            assert p['page']>=2
            for a in p['annotations']:
                assert len(a['bbox'])==4 and all(math.isfinite(v) for v in a['bbox'])
    for measurement in d['additionalDimensions']:
        assert measurement['unit'] in ('mm','degree'), d['id']
        assert math.isfinite(measurement['value']), d['id']
        assert measurement['page']>=2 and measurement['feature'] and measurement['quantity'], d['id']
        if d['drawing']:assert measurement['page'] in [p['page'] for p in d['drawing']['pages']],d['id']
    for profile in d['profiles']:
        assert profile['unit']=='mm' and profile['coordinateConvention'],d['id']
        assert profile['coordinateStatus']=='reviewed-unpaired-ordinates',d['id']
        assert all(math.isfinite(v) for axis in ('x','y') for v in profile[axis]),d['id']
    def check_features(node):
        if isinstance(node,dict):
            if 'value' in node:
                assert math.isfinite(node['value']) and node['unit'] in ('mm','degrees','degree'),d['id']
                assert node['sourcePage']>=2 and node.get('derivation'),d['id']
            for value in node.values():check_features(value)
        elif isinstance(node,list):
            for value in node:check_features(value)
    check_features(d['features'])
    if d['display']['ppi']:
        for axis,key in [('x','width'),('y','height')]:
            expected=d['display']['nativePixels'][key]*25.4/d['display']['activeMm'][key]
            assert math.isclose(d['display']['ppi'][axis],expected)
assert sum(bool(d['drawing']) for d in table['devices'])==table['coverage']['drawings']==90
print(f'Validated {len(ids)} devices, {len(hardware)} unique hardware identifiers')
