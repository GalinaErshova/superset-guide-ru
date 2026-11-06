"""Build the Russian Superset handbook from Markdown and explicit editorial metadata."""
from pathlib import Path
from datetime import date
import csv
import html
import json
import re
import shutil
import markdown

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'dist'
ORIGIN = 'https://superset.galaershova.ru'
REPO = 'https://github.com/GalinaErshova/superset-guide-ru'
CHECKED = '2026-11-06'
STATUS = {'stable': 'Стабильно', 'preview': 'Превью', 'experiment': 'Эксперимент'}
entries = json.loads((ROOT / 'content/catalog.json').read_text(encoding='utf-8'))
updates = json.loads((ROOT / 'content/updates.json').read_text(encoding='utf-8'))
e = html.escape

def write(path, text):
    target = OUT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding='utf-8')

def badge(item):
    return f'<span class="badge {item["status"]}">{STATUS[item["status"]]}</span>'

def fresh(item):
    label = 'Обновлено' if item['updated'] > item['published'] else 'Новое'
    return f'<span class="fresh" data-fresh="{item["updated"]}" hidden>{label}</span>'

for item in entries:
    item.setdefault('status', 'stable')
    item.setdefault('version', '6.1')
    item.setdefault('published', CHECKED)
    item.setdefault('updated', CHECKED)
    item.setdefault('checked', CHECKED)
    raw = (ROOT / 'content' / item['file']).read_text(encoding='utf-8')
    item['title'] = raw.splitlines()[0].removeprefix('# ').strip()
    item['raw'] = raw
    item['url'] = f'/guide/{item["slug"]}/'

by_file = {Path(x['file']).name: x['url'] for x in entries}
for item in entries:
    body = item['raw'].split('\n', 1)[1]
    for name, url in by_file.items():
        body = body.replace(f']({name})', f']({url})')
    # Editors provide trusted Markdown; visitors never supply markup.
    md = markdown.Markdown(extensions=['tables', 'fenced_code', 'toc', 'sane_lists'], extension_configs={'toc': {'permalink': False}})
    item['body'] = md.convert(body)
    item['toc'] = md.toc

def nav(active):
    top = [('','Начало'), ('library','Все материалы'), ('topics','По темам'), ('experiments','Эксперименты'), ('updates','Что нового')]
    links = ''.join(f'<a href="/{slug + "/" if slug else ""}" {"aria-current=page" if active == slug else ""}>{label}</a>' for slug, label in top)
    groups = []
    for group in dict.fromkeys(x['group'] for x in entries):
        items = [x for x in entries if x['group'] == group]
        groups.append(f'<section class="nav-group"><h2>{e(group)}</h2>' + ''.join(f'<a href="{x["url"]}" {"aria-current=page" if active == x["slug"] else ""}>{e(x["title"])}</a>' for x in items) + '</section>')
    return f'<nav aria-label="Основная навигация"><div class="nav-top">{links}</div>{"".join(groups)}</nav>'

def shell(title, desc, body, active='', path='/', toc='', article=None):
    edit = f'{REPO}/edit/codex/superset-guide/content/{article["file"]}' if article else REPO
    return f'''<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)} · Superset по-русски</title><meta name="description" content="{e(desc)}">
<link rel="canonical" href="{ORIGIN}{path}"><meta property="og:title" content="{e(title)} · Superset по-русски"><meta property="og:description" content="{e(desc)}"><meta property="og:type" content="website"><meta property="og:url" content="{ORIGIN}{path}">
<link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/style.css"><link rel="alternate" type="application/atom+xml" title="Обновления справочника" href="/feed.xml"><script src="/app.js" defer></script></head>
<body><a class="skip" href="#main">К содержанию</a>
<header class="topbar"><a class="brand" href="/"><span class="brand-mark" aria-hidden="true">S<span>↗</span></span><span>Superset<small>по-русски</small></span></a><div class="top-caption">Практика для аналитиков</div><a class="top-news" href="/updates/">Что нового</a><button id="menu" aria-controls="sidebar" aria-expanded="false">Меню</button></header>
<div class="layout"><aside id="sidebar" class="sidebar"><form class="search" action="/search/"><label for="q">Поиск по справочнику</label><div class="search-field"><input id="q" type="search" name="q" placeholder="Например, фильтры" autocomplete="off"><button type="submit" aria-label="Найти">↵</button></div></form>{nav(active)}<p class="sidebar-note">Независимый справочник<br>Базовая версия: 6.1</p></aside>
<div class="workspace"><main id="main" tabindex="-1">{body}</main><footer><span>Галина Ершова · Superset по-русски</span><a href="/guide/editorial/">Актуальность и статусы</a><a href="{edit}">Предложить правку</a><a href="/feed.xml">RSS / Atom</a><p>Независимый учебный проект. Apache Superset — продукт Apache Software Foundation.</p></footer></div></div>
<div class="toast" role="status" id="toast" hidden></div></body></html>'''

def row(item, numbered=None):
    num = f'<span class="row-number">{numbered:02}</span>' if numbered else ''
    return f'<a class="material-row" href="{item["url"]}" data-status="{item["status"]}" data-group="{e(item["group"])}">{num}<div><div class="row-meta">{e(item["group"])} · {item["minutes"]} мин {fresh(item)}</div><h3>{e(item["title"])}</h3><p>{e(item["description"])}</p></div><div class="row-end">{badge(item)}<span aria-hidden="true">↗</span></div></a>'

def heading(kicker, title, intro):
    return f'<header class="page-heading"><p class="eyebrow">{kicker}</p><h1>{title}</h1><p class="intro">{intro}</p></header>'

if OUT.exists():
    # Delete only this project's generated output, never a user-supplied path.
    assert OUT.resolve().parent == ROOT.resolve() and OUT.name == 'dist'
    shutil.rmtree(OUT)
OUT.mkdir()
shutil.copytree(ROOT / 'static', OUT, dirs_exist_ok=True)

home = heading('Учебник + справочник', 'От первого графика<br>к понятному дашборду', 'Освойте Apache Superset шаг за шагом. Возвращайтесь за рецептом, когда решаете рабочую задачу.')
home += '''<div class="hero-actions"><a class="button primary" href="/guide/start/">Начать с первого урока <span aria-hidden="true">→</span></a><a class="text-link" href="/library/">Открыть справочник ↗</a></div>
<section class="practice-strip" aria-label="Учебный пример"><div><span class="small-label">Ваш первый проект</span><h2>Продажи: от данных к выводу</h2><p>12 заказов, три месяца, два региона.<br>Один набор данных на весь учебный маршрут.</p><a href="/data/sales.csv" download>Скачать учебный CSV ↓</a></div><div class="mini-chart"><div class="mini-caption">Выручка по месяцам <span>учебные данные, у. е.</span></div><div class="bars"><div><b>44 000</b><span style="height:72%"></span><small>Январь</small></div><div><b>51 000</b><span style="height:84%"></span><small>Февраль</small></div><div><b>61 000</b><span style="height:100%"></span><small>Март</small></div></div></div></section>
<section class="home-section"><div class="section-heading"><h2>Первые шаги</h2><p>От входа в систему до проверенного результата. Устанавливать сервер для начала не нужно.</p></div>'''
home += '<div class="lesson-grid">' + ''.join(f'<a class="lesson" href="{x["url"]}"><span class="lesson-index">{i:02}</span><h3>{e(x["title"])}</h3><p>{e(x["description"])}</p><span class="lesson-time">{x["minutes"]} мин →</span></a>' for i,x in enumerate(entries[:5],1)) + '<a class="lesson continuation" href="/guide/sql-lab/"><span class="lesson-index">06–08</span><h3>SQL, метрики<br>и публикация</h3><p>Продолжите маршрут и подготовьте дашборд к передаче коллегам.</p><span class="lesson-time">Продолжить →</span></a></div></section>'
home += '<section class="home-section"><div class="section-heading"><h2>Справочник по темам</h2><p>Три направления для тех, кто уже делает дашборды.</p></div><div class="topic-links"><a href="/topics/#themes">Темы и палитры <span>Единый стиль дашбордов →</span></a><a href="/topics/#css">Оформление и CSS <span>Композиция и точечные изменения →</span></a><a href="/topics/#ai">AI, MCP и Codex <span>Подключение к вашему стенду →</span></a></div></section>'
home += '<section class="experiment-feature"><div><span class="badge experiment">Эксперимент</span><h2>Попробовать то,<br>что появляется сейчас</h2><p>AI и MCP, сторонние расширения, CSS-кастомизация. С условиями запуска и критериями проверки.</p></div><a class="button secondary" href="/experiments/">В лабораторию →</a></section>'
home += '<section class="home-section"><div class="section-heading"><h2>Что нового</h2><p>Изменения материалов и новости продукта с датами и источниками.</p></div>' + ''.join(f'<a class="update-row" href="/guide/{u["slug"]}/"><time datetime="{u["date"]}">{u["date"][8:10]}.{u["date"][5:7]}.{u["date"][:4]}</time><div><span class="row-meta">{u["type"]}</span><h3>{u["title"]}</h3><p>{u["summary"]}</p></div><span aria-hidden="true">→</span></a>' for u in updates) + '</section>'
write('index.html',shell('Главная','Учебник Apache Superset на русском для аналитиков: первые шаги, справочник, эксперименты и релизы.',home))

for i,item in enumerate(entries):
    meta = f'<div class="article-meta">{badge(item)}{fresh(item)}<span>{e(item["version"])}</span><span>{item["minutes"]} мин</span><span>Сверено {item["checked"]}</span></div>'
    body = f'<div class="breadcrumbs"><a href="/library/">Справочник</a> / {e(item["group"])}</div><header class="article-heading"><h1>{e(item["title"])}</h1><p class="intro">{e(item["description"])}</p>{meta}</header>'
    body += f'<div class="article-grid"><article class="prose">{item["body"]}</article><aside class="toc"><p>На этой странице</p>{item["toc"]}</aside></div>'
    if i < 8:
        previous = f'<a href="{entries[i-1]["url"]}">← Предыдущий урок</a>' if i else '<a href="/">← На главную</a>'
        following = f'<a href="{entries[i+1]["url"]}">Следующий урок →</a>' if i < 7 else '<a href="/library/">Перейти в справочник →</a>'
        body += f'<nav class="lesson-pagination" aria-label="Уроки">{previous}{following}</nav>'
    body += f'<div class="article-end">Опубликовано {item["published"]} · Обновлено {item["updated"]}<br><a href="{REPO}/issues/new">Сообщить об ошибке</a></div>'
    write(f'guide/{item["slug"]}/index.html',shell(item['title'],item['description'],body,active=item['slug'],path=item['url'],article=item))

filters = '<div class="filters"><label>Статус<select id="status-filter"><option value="all">Все статусы</option><option value="stable">Стабильно</option><option value="preview">Превью</option><option value="experiment">Эксперимент</option></select></label><label>Раздел<select id="group-filter"><option value="all">Все разделы</option>' + ''.join(f'<option>{e(g)}</option>' for g in dict.fromkeys(x['group'] for x in entries)) + '</select></label><label class="check"><input id="fresh-filter" type="checkbox">Новое и обновлённое</label></div>'
library = heading('База знаний','Справочник аналитика','Найдите ответ по задаче, разделу или статусу возможности.') + filters + f'<p class="result-count" id="result-count" aria-live="polite">Материалов: {len(entries)}</p><div id="materials">' + ''.join(row(x) for x in entries) + '</div><p id="empty-filter" hidden>В этом сочетании фильтров материалов нет. Выберите другой раздел или все статусы.</p>'
write('library/index.html',shell('Справочник','Все материалы Apache Superset: данные, дашборды, оформление и эксперименты.',library,'library','/library/'))
experiments = heading('Лаборатория','Эксперименты','Проверяйте новые подходы на учебных данных. У каждого сценария есть предпосылки, ограничения и ожидаемый результат.') + '<div class="callout">Здесь есть и официальные инструменты в опытных сценариях, и сторонние проекты. Метка «Эксперимент» не означает, что всё перечисленное включено в Superset.</div>' + ''.join(row(x) for x in entries if x['status']=='experiment')
write('experiments/index.html',shell('Эксперименты','AI, MCP и нестандартная кастомизация Superset: проверяемые пилоты.',experiments,'experiments','/experiments/'))
topic_groups = [
 ('themes','Темы и палитры','Начните со штатной темы, согласуйте цвета категорий и проверьте читаемость.', ['themes','charts','releases']),
 ('css','Оформление и CSS','Сначала композиция и настройки графика. Затем точечные CSS-эксперименты на копии.', ['design','css','troubleshooting']),
 ('ai','AI, MCP и Codex','Подключение помощника к стенду, проверка ответов и опытные расширения.', ['codex','mcp','ai-assistant','nl-explorer'])
]
topics = heading('Тематический справочник','Темы, оформление и AI','От готовых возможностей к опытным сценариям. Выберите направление и двигайтесь по связанным материалам.')
topics += '<div class="topic-jumps">' + ''.join(f'<a href="#{slug}">{title}</a>' for slug,title,_,_ in topic_groups) + '</div>'
for slug,title,intro,slugs in topic_groups:
    topics += f'<section class="home-section" id="{slug}"><div class="section-heading"><h2>{title}</h2><p>{intro}</p></div>' + ''.join(row(next(x for x in entries if x['slug']==s)) for s in slugs) + '</section>'
write('topics/index.html',shell('Тематический справочник','Темы Superset, CSS, оформление дашбордов, AI, MCP и подключение Codex.',topics,'topics','/topics/'))
journal = heading('Журнал изменений','Что нового','Обновления справочника отдельно от дат выпуска Apache Superset.') + '<div class="release-summary"><div><span class="badge stable">Стабильно</span><strong>6.1.0</strong><span>13 мая 2026</span></div><div><span class="badge preview">Превью</span><strong>7.0.0rc2</strong><span>16 октября 2026</span></div><p>Сверено 6 ноября 2026.<br><a href="/guide/releases/">Источники и разбор релизов →</a></p></div>' + ''.join(f'<section class="journal-entry"><time datetime="{u["date"]}">{u["date"]}</time><div><span class="row-meta">{u["type"]}</span><h2><a href="/guide/{u["slug"]}/">{u["title"]}</a></h2><p>{u["summary"]}</p></div></section>' for u in updates) + '<p class="muted">Новые записи публикуются после редакционной проверки. <a href="/feed.xml">Подписаться на ленту Atom</a>.</p>'
write('updates/index.html',shell('Что нового','Новые материалы и релизы Apache Superset на русском.',journal,'updates','/updates/'))
search = heading('Поиск','Найти в справочнике','Поиск по заголовкам и полным текстам. Например: «область фильтра», «SQL», «MCP».') + '<form class="large-search" action="/search/"><label for="search-query">Ваш запрос</label><input id="search-query" name="q" type="search" placeholder="Что хотите узнать?" autocomplete="off"><button class="button primary" type="submit">Найти</button></form><p id="search-status" role="status"></p><div id="search-results"></div><noscript>Для поиска включите JavaScript. Все страницы доступны через <a href="/library/">справочник</a>.</noscript>'
write('search/index.html',shell('Поиск','Полнотекстовый поиск по русскому справочнику Superset.',search,'search','/search/'))
write('404.html',shell('Страница не найдена','Страница не найдена.',heading('404','Страница не найдена','Проверьте адрес или найдите материал в справочнике.')+'<a class="button primary" href="/library/">Открыть справочник →</a>',path='/404.html'))
write('search-index.json',json.dumps([{k:x[k] for k in ('title','description','url','status','group','raw')} for x in entries],ensure_ascii=False))
urls=['/','/library/','/topics/','/experiments/','/updates/','/search/']+[x['url'] for x in entries]
write('sitemap.xml','<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join(f'<url><loc>{ORIGIN}{url}</loc><lastmod>{CHECKED}</lastmod></url>' for url in urls)+'</urlset>')
write('robots.txt',f'User-agent: *\nAllow: /\nSitemap: {ORIGIN}/sitemap.xml\n')
write('feed.xml','<?xml version="1.0" encoding="UTF-8"?><feed xmlns="http://www.w3.org/2005/Atom"><title>Superset по-русски: обновления</title><id>'+ORIGIN+'/</id><link href="'+ORIGIN+'/feed.xml" rel="self"/><link href="'+ORIGIN+'/"/><updated>'+CHECKED+'T12:00:00Z</updated><author><name>Галина Ершова</name></author>'+''.join(f'<entry><title>{e(u["title"])}</title><id>{ORIGIN}/updates/#{u["date"]}-{u["slug"]}</id><link href="{ORIGIN}/guide/{u["slug"]}/"/><updated>{u["date"]}T12:00:00Z</updated><summary>{e(u["summary"])}</summary></entry>' for u in updates)+'</feed>')
print(f'Built {len(entries)} articles and {len(urls)} indexed pages in {OUT}')
