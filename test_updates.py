"""Regression checks for future editorial changes in an isolated fixture."""
from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='superset-update-check-', dir=root.parent) as temp:
    fixture=Path(temp)
    shutil.copy(root/'build.py',fixture/'build.py')
    for folder in ('content','static'):
        shutil.copytree(root/folder,fixture/folder)
    def read(name):return json.loads((fixture/'content'/name).read_text(encoding='utf-8'))
    def write(name,value):(fixture/'content'/name).write_text(json.dumps(value,ensure_ascii=False),encoding='utf-8')
    catalog=read('catalog.json')
    catalog[0]['updated']='2027-01-03'
    catalog[0]['checked']='2027-01-03'
    write('catalog.json',catalog)
    journal=read('updates.json')
    journal.append({'date':'2027-01-04','type':'Материалы','title':'Регрессионная проверка','summary':'Только в тестовой копии','slug':'start'})
    write('updates.json',journal)
    releases=read('releases.json')
    releases['checked']='2027-01-05'
    releases['items'][0].update(version='test-stable',published='2027-01-02')
    write('releases.json',releases)
    subprocess.run([sys.executable,str(fixture/'build.py')],cwd=fixture,check=True,capture_output=True)
    atom={'a':'http://www.w3.org/2005/Atom'}
    feed=ET.parse(fixture/'dist/feed.xml')
    assert feed.find('a:updated',atom).text.startswith('2027-01-04')
    assert feed.find('a:entry/a:title',atom).text=='Регрессионная проверка'
    sm={'s':'http://www.sitemaps.org/schemas/sitemap/0.9'}
    urls=ET.parse(fixture/'dist/sitemap.xml').findall('s:url',sm)
    dates={u.find('s:loc',sm).text:u.find('s:lastmod',sm).text for u in urls}
    assert dates['https://superset.galaershova.ru/guide/start/']=='2027-01-03'
    assert dates['https://superset.galaershova.ru/guide/data/']=='2026-11-06'
    assert dates['https://superset.galaershova.ru/updates/']=='2027-01-05'
    for name in ('updates/index.html','guide/releases/index.html'):
        text=(fixture/'dist'/name).read_text(encoding='utf-8')
        assert 'test-stable' in text and '02.01.2027' in text and '05.01.2027' in text
    index=json.loads((fixture/'dist/search-index.json').read_text(encoding='utf-8'))
    release=next(x for x in index if x['url']=='/guide/releases/')
    assert 'test-stable' in release['raw'] and '{{release_' not in release['raw']
print('PASS: future article dates, independent sitemap dates, sorted Atom, shared release data and searchable release versions.')
