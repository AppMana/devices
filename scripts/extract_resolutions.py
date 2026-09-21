import ast,json,re,pathlib,concurrent.futures,urllib.request,time
from bs4 import BeautifulSoup
ROOT=pathlib.Path(__file__).resolve().parents[1]
base=ROOT/'.cache/DeviceKit'
s=(base/'Source/Device.swift.gyb').read_text().split('%{',1)[1].split('}%',1)[0]
tree=ast.parse(s)
records=[]
for node in tree.body:
 if not isinstance(node,ast.Assign) or not isinstance(node.value,ast.List): continue
 category={'iPods':'ipod','iPhones':'iphone','iPads':'ipad','homePods':'homepod','tvs':'appletv','watches':'watch'}.get(node.targets[0].id)
 if not category: continue
 for v in node.value.elts:
  args=[ast.literal_eval(a) for a in v.args]
  url=re.search(r'\]\((https://[^)]+)\)',args[1])
  records.append(dict(id=args[0],name=args[6],identifiers=args[3],category=category,diagonalInches=args[4],sourceScreenRatio=args[5],pixelsPerInch=args[8],specUrl=url.group(1) if url else None,resolution=None,scale=None))
overrides={'appleWatchUltra2':'111832','iPadPro13M5':'125407','appleWatchSeries10_42mm':'121202','appleWatchSeries10_46mm':'121202','appleWatchSeries11_42mm':'125093','appleWatchSeries11_46mm':'125093','appleWatchSE3_40mm':'125094','appleWatchSE3_44mm':'125094','appleWatchUltra3':'125095'}
for r in records:
 if r['id'] in overrides:
  r['upstreamSpecUrl']=r['specUrl'];r['specUrl']='https://support.apple.com/en-us/'+overrides[r['id']]
cache=(ROOT/'.cache/apple-specs');cache.mkdir(exist_ok=True)
pattern=re.compile(r'(\d{3,4})\s*[-‑–]?\s*(?:by|x|×)\s*[-‑–]?\s*(\d{3,4})\s*[-‑–]?\s*(?:pixel|pixels|resolution)',re.I)
def get(r):
 if not r['specUrl']: return r
 try:
  p=cache/(r['id']+'.html')
  if not p.exists() or r['id'] in overrides:
   req=urllib.request.Request(r['specUrl'],headers={'User-Agent':'Mozilla/5.0'})
   with urllib.request.urlopen(req,timeout=35) as f: data=f.read();r['resolvedSpecUrl']=f.url
   p.write_bytes(data)
  text=BeautifulSoup(p.read_text(),'html.parser').get_text(' ',strip=True)
  matches=list(pattern.finditer(text))
  r['resolutionCandidates']=[dict(width=min(int(m[1]),int(m[2])),height=max(int(m[1]),int(m[2])),evidence=text[max(0,m.start()-70):m.end()+60]) for m in matches]
  # First display match on phone/tablet/iPod specifications, not camera/video dimensions.
  if r['category'] in ('iphone','ipad','ipod') and matches:
   m=matches[0];r['resolution']={'width':min(int(m[1]),int(m[2])),'height':max(int(m[1]),int(m[2]))};r['resolutionEvidence']=r['resolutionCandidates'][0]['evidence']
  if r['category']=='watch' and matches:
   size=re.search(r'_(\d+)mm$',r['id'])
   chosen=None
   if len(matches)==1 or 'Ultra' in r['id']:chosen=matches[0]
   elif size:
    mm=size.group(1)
    for m in matches:
     before=text[max(0,m.start()-110):m.start()]
     after=text[m.end():m.end()+15]
     if re.search(r'\('+mm+r'\s*mm\)',after) or re.search(mm+r'\s*mm\s*$',before) or re.search(r'Height:\s*'+mm+r'\s*mm',before):chosen=m;break
   if chosen:
    r['resolution']={'width':min(int(chosen[1]),int(chosen[2])),'height':max(int(chosen[1]),int(chosen[2]))}
    r['resolutionEvidence']=text[max(0,chosen.start()-100):chosen.end()+35]
 except Exception as e:r['fetchError']=str(e)
 return r
with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool: records=list(pool.map(get,records))
out={'source':{'repository':'https://github.com/devicekit/DeviceKit','commit':'9000b09deb528298f493a69cae55663c8d85983e','license':'MIT','licenseText':(base/'LICENSE').read_text(),'file':'Source/Device.swift.gyb'},'retrievedAt':'2026-09-21','records':records}
(ROOT/'.cache/resolutions.json').write_text(json.dumps(out,indent=2)+'\n')
print('records',len(records),'resolved',sum(bool(r['resolution']) for r in records))
for r in records:
 if not r['resolution']:print(r['id'],r.get('fetchError'),r.get('resolutionCandidates'))
