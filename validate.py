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
        self.meta={}; self.canonical=[]; self.titles=[]; self.ld=[]; self.capture=None
        self.feed(text)
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag=='meta' and (a.get('name') or a.get('property')):
            key=a.get('name') or a['property']
            assert key not in self.meta, f'Duplicate metadata: {key}'
            self.meta[key]=a.get('content','')
        if tag=='link' and a.get('rel')=='canonical':self.canonical.append(a['href'])
        if tag=='title':self.titles.append(''); self.capture='title'
        if tag=='script' and a.get('type')=='application/ld+json':self.ld.append(''); self.capture='json'
        if tag=='html': self.lang=a.get('lang')
        if tag=='h1': self.h1+=1
        if a.get('id'):
            assert a['id'] not in self.ids, f'Duplicate id: {a["id"]}'
            self.ids.add(a['id'])
        if tag in ('a','link','script','img'):
            url=a.get('href') or a.get('src')
            if url:self.refs.append(url)
    def handle_endtag(self, tag):
        if tag in ('title','script'):self.capture=None
    def handle_data(self, data):
        if self.capture=='title':self.titles[-1]+=data
        if self.capture=='json':self.ld[-1]+=data

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
assert len(catalog)==23
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
sitemap=ET.parse(OUT/'sitemap.xml');ET.parse(OUT/'feed.xml')
origin='https://superset.galaershova.ru'
sitemap_urls={x.text for x in sitemap.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')}
titles=set(); descriptions=set(); expected_urls=set()
for file,page in pages.items():
    relative=file.relative_to(OUT).as_posix()
    route='/' + relative.removesuffix('index.html')
    url=origin+route
    assert page.canonical==[url], f'{route}: canonical'
    assert len(page.titles)==1 and page.titles[0] not in titles, f'{route}: title'
    titles.add(page.titles[0])
    description=page.meta['description']
    assert description and description not in descriptions, f'{route}: description'
    descriptions.add(description)
    assert page.meta['og:url']==url and page.meta['og:locale']=='ru_RU'
    assert page.meta['og:title']==page.meta['twitter:title']==page.titles[0]
    assert page.meta['og:description']==page.meta['twitter:description']==description
    if route in ('/search/','/404.html'):
        assert page.meta['robots']=='noindex, follow' and not page.ld
        assert url not in sitemap_urls
        continue
    expected_urls.add(url)
    assert page.meta['robots'].startswith('index, follow')
    assert len(page.ld)==1
    graph=json.loads(page.ld[0])['@graph']
    webpage=next(x for x in graph if x['@type']=='WebPage')
    assert webpage['url']==url and webpage['description']==description
    if route.startswith('/guide/'):
        item=next(x for x in catalog if route==f'/guide/{x["slug"]}/')
        article=next(x for x in graph if x['@type']=='Article')
        assert article['mainEntityOfPage']['@id']==webpage['@id']
        assert article['datePublished']==item.get('published','2026-11-06')
        assert article['dateModified']==page.meta['article:modified_time']
        assert article['dateModified']>=article['datePublished']
        crumbs=next(x for x in graph if x['@type']=='BreadcrumbList')['itemListElement']
        assert [x['position'] for x in crumbs]==[1,2] and crumbs[-1]['item']==url
        assert page.meta['og:type']=='article'
    else:assert page.meta['og:type']=='website'
assert sitemap_urls==expected_urls, 'Sitemap must match indexable canonical pages'
assert not errors, '\n'.join(errors)
print(f'PASS: {len(pages)} pages; all internal links/anchors; 23 articles; search index; CSV totals, months and regions; sitemap and feed.')
print(f'PASS: unique SEO metadata, canonical URLs, social cards, article/breadcrumb JSON-LD, {len(expected_urls)} indexable routes and noindex exclusions.')
