"""Verify generated routes, anchors, editorial metadata and reproducible lesson data."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
from datetime import date
from collections import defaultdict
import csv
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'dist'
class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(); self.refs=[]; self.ids=set(); self.h1=0; self.lang=None
        self.feed(text)
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag=='html': self.lang=a.get('lang')
        if tag=='h1': self.h1+=1
        if a.get('id'):
            assert a['id'] not in self.ids, f'Duplicate id: {a["id"]}'
            self.ids.add(a['id'])
        if tag in ('a','link','script','img'):
            url=a.get('href') or a.get('src')
            if url:self.refs.append(url)

pages={p:Page(p.read_text(encoding='utf-8')) for p in OUT.rglob('*.html')}
errors=[]
for file,page in pages.items():
    if page.h1!=1 or page.lang!='ru':errors.append(f'{file}: heading/language')
    for url in page.refs:
        split=urlsplit(url)
        if split.scheme or split.netloc:continue
        if not split.path:target=file
        elif split.path.startswith('/'):target=OUT/unquote(split.path).lstrip('/')
        else:target=file.parent/unquote(split.path)
        if target.is_dir():target=target/'index.html'
        target=target.resolve()
        if not target.is_file():errors.append(f'{file.relative_to(OUT)}: missing {url}')
        elif split.fragment and target in pages and unquote(split.fragment) not in pages[target].ids:
            errors.append(f'{file.relative_to(OUT)}: missing anchor {url}')
catalog=json.loads((ROOT/'content/catalog.json').read_text(encoding='utf-8'))
assert len({x['slug'] for x in catalog})==len(catalog)
assert len(catalog)==22
for item in catalog:
    assert item.get('status','stable') in ('stable','preview','experiment')
    for key in ('published','updated','checked'):
        if key in item:date.fromisoformat(item[key])
    if 'published' in item and 'updated' in item:assert item['updated']>=item['published']
index=json.loads((OUT/'search-index.json').read_text(encoding='utf-8'))
assert len(index)==len(catalog)
assert all(len(x['raw'])>500 for x in index)
with (OUT/'data/sales.csv').open(encoding='utf-8',newline='') as stream:rows=list(csv.DictReader(stream))
assert len(rows)==len({r['order_id'] for r in rows})==12
assert sum(int(r['revenue']) for r in rows)==156000
assert sum(int(r['cost']) for r in rows)==98000
monthly=defaultdict(int);regions=defaultdict(int)
for r in rows:
    monthly[r['order_date'][:7]]+=int(r['revenue'])
    regions[r['region']]+=int(r['revenue'])
assert dict(monthly)=={'2026-01':44000,'2026-02':51000,'2026-03':61000}
assert dict(regions)=={'North':73000,'South':83000}
ET.parse(OUT/'sitemap.xml');ET.parse(OUT/'feed.xml')
assert not errors, '\n'.join(errors)
print(f'PASS: {len(pages)} pages; all internal links/anchors; 22 articles; search index; CSV totals, months and regions; sitemap and feed.')
