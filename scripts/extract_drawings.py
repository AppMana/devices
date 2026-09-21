"""Extract positioned numerical annotations; never infer their physical meaning from proximity."""
import concurrent.futures,csv,io,json,pathlib,re,subprocess,xml.etree.ElementTree as ET
ROOT=pathlib.Path(__file__).resolve().parents[1]; CACHE=ROOT/'.cache'
NUMBER=re.compile(r'^[±+−-]?(?:\d*\.\d+|\d+)(?:°|mm|MM)?$')
NS={'p':'http://www.w3.org/1999/xhtml'}
def run(*args):return subprocess.check_output(args).decode()
def extract(r):
    pdf=CACHE/(r['id']+'.pdf'); xml=ET.fromstring(run('pdftotext','-bbox-layout',str(pdf),'-'))
    pages=[]
    for i,p in enumerate(xml.findall('.//p:page',NS),1):
        if i==1:continue # legal cover, not a drawing
        words=[dict(text=w.text or '',bbox=[float(w.attrib[k]) for k in ('xMin','yMin','xMax','yMax')]) for w in p.findall('.//p:word',NS)]
        numbers=[w for w in words if NUMBER.fullmatch(w['text'])]
        method='pdf-text'; confidence=None
        if len(numbers)<10:
            stem=CACHE/f"{r['id']}-{i}"; tsv=pathlib.Path(str(stem)+'.tsv')
            if not tsv.exists():
                subprocess.run(['pdftoppm','-f',str(i),'-l',str(i),'-scale-to','3300','-singlefile','-png',str(pdf),str(stem)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                subprocess.run(['tesseract',str(stem)+'.png',str(stem),'--psm','11','tsv'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                pathlib.Path(str(stem)+'.png').unlink()
            # TSV coordinates mapped back to PDF page points (long edge 3300 px).
            scale=max(float(p.attrib['width']),float(p.attrib['height']))/3300
            words=[]
            for row in csv.DictReader(io.StringIO(tsv.read_text()),delimiter='\t',quoting=csv.QUOTE_NONE):
                if row['text'].strip():
                    x,y,w,h=[int(row[k])*scale for k in ('left','top','width','height')]
                    words.append(dict(text=row['text'],bbox=[round(v,3) for v in (x,y,x+w,y+h)],confidence=float(row['conf'])))
            numbers=[w for w in words if NUMBER.fullmatch(w['text'])];method='ocr-unreviewed'
        # Short local labels aid reviewing a measurement without distributing full PDF prose.
        for n in numbers:
            x,y,xx,yy=n['bbox'];near=[w['text'] for w in words if w is not n and abs(w['bbox'][1]-y)<8 and abs(w['bbox'][0]-x)<80 and len(w['text'])<35]
            n['nearbyTokens']=near[:8]
        pages.append(dict(page=i,sizePoints=[float(p.attrib['width']),float(p.attrib['height'])],method=method,annotations=numbers))
    return dict(**r,pages=pages)
def main():
    records=json.loads((CACHE/'index.json').read_text())
    results=list(concurrent.futures.ThreadPoolExecutor(4).map(extract,records))
    (CACHE/'drawings.json').write_text(json.dumps(results,indent=2)+'\n')
    print('Extracted',len(results),'drawings',sum(len(r['pages']) for r in results),'pages')
if __name__=='__main__':main()
