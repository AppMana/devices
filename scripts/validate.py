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
    if d['display']['ppi']:
        for axis,key in [('x','width'),('y','height')]:
            expected=d['display']['nativePixels'][key]*25.4/d['display']['activeMm'][key]
            assert math.isclose(d['display']['ppi'][axis],expected)
assert sum(bool(d['drawing']) for d in table['devices'])==table['coverage']['drawings']==90
print(f'Validated {len(ids)} devices, {len(hardware)} unique hardware identifiers')
