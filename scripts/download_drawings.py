"""Fetch Apple's current drawing index and cache all linked PDFs for extraction."""
import concurrent.futures, hashlib, html, json, pathlib, re, urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[1]
CACHE=ROOT/'.cache'; CACHE.mkdir(exist_ok=True)
URL='https://developer.apple.com/accessories/dimensional-drawings/'
def fetch(url):
    with urllib.request.urlopen(url, timeout=90) as r:return r.read()
def main():
    page=fetch(URL).decode(); records=[]
    for href,body in dict(re.findall(r'href="([^"]+\.pdf)"[^>]*>(.*?)</a>',page,re.S)).items():
        name=html.unescape(re.search(r'class="device-name">(.*?)</span>',body,re.S)[1].strip())
        records.append(dict(id=pathlib.Path(href).stem,name=name,url='https://developer.apple.com'+href))
    def one(r):
        path=CACHE/(r['id']+'.pdf')
        if not path.exists():path.write_bytes(fetch(r['url']))
        r['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
        return r
    records=list(concurrent.futures.ThreadPoolExecutor(8).map(one,records))
    (CACHE/'index.json').write_text(json.dumps(records,indent=2)+'\n')
    print(f'Cached {len(records)} PDFs')
if __name__=='__main__':main()
