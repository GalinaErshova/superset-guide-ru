'use strict';
const labels = {stable: 'Стабильно', preview: 'Превью', experiment: 'Эксперимент'};
const recent = value => {
  const age = Date.now() - Date.parse(value + 'T00:00:00Z');
  return Number.isFinite(age) && age >= 0 && age < 30 * 86400000;
};
document.querySelectorAll('[data-fresh]').forEach(el => {el.hidden = !recent(el.dataset.fresh);});
const menu = document.querySelector('#menu');
const sidebar = document.querySelector('#sidebar');
const closeMenu = () => {sidebar.classList.remove('open'); menu.setAttribute('aria-expanded', 'false');};
menu.addEventListener('click', () => {
  const open = sidebar.classList.toggle('open');
  menu.setAttribute('aria-expanded', String(open));
  if(open) sidebar.querySelector('input').focus();
});
document.addEventListener('keydown', event => {
  if(event.key === 'Escape' && sidebar.classList.contains('open')) {closeMenu();menu.focus();}
});
document.addEventListener('click', event => {if(!sidebar.contains(event.target) && !menu.contains(event.target)) closeMenu();});
const filterControls = ['#status-filter','#group-filter','#fresh-filter'].map(s=>document.querySelector(s));
function filterMaterials() {
  const [status,group,fresh] = filterControls;
  let count = 0;
  document.querySelectorAll('#materials .material-row').forEach(row=>{
    const stamp = row.querySelector('[data-fresh]');
    const show = (status.value==='all'||row.dataset.status===status.value) && (group.value==='all'||row.dataset.group===group.value) && (!fresh.checked||(stamp&&recent(stamp.dataset.fresh)));
    row.hidden = !show;
    if(show) count++;
  });
  document.querySelector('#result-count').textContent = `Материалов: ${count}`;
  document.querySelector('#empty-filter').hidden = count > 0;
}
filterControls.filter(Boolean).forEach(control=>control.addEventListener('change',filterMaterials));
document.querySelectorAll('.prose pre').forEach(pre=>{
  const button=document.createElement('button'); button.className='copy-code';button.textContent='Копировать';button.type='button';
  const code=pre.querySelector('code').textContent;
  button.addEventListener('click',async()=>{
    try {await navigator.clipboard.writeText(code);button.textContent='Скопировано';}
    catch {button.textContent='Выделите текст и скопируйте';}
    setTimeout(()=>{button.textContent='Копировать';},2500);
  });pre.append(button);
});
const normalize = text => text.toLocaleLowerCase('ru').replaceAll('ё','е');
const queryInput = document.querySelector('#search-query');
if(queryInput) {
  let indexPromise;
  let generation=0;
  const status=document.querySelector('#search-status');
  const results=document.querySelector('#search-results');
  async function search(query) {
    const request=++generation;
    results.replaceChildren();
    const terms=normalize(query.trim()).split(/\s+/).filter(Boolean);
    if(!terms.length){status.textContent='Введите слово или несколько слов.';return;}
    status.textContent='Ищем в материалах…';
    try {
      if(!indexPromise) indexPromise=fetch('/search-index.json').then(r=>{if(!r.ok)throw new Error('index');return r.json();}).catch(err=>{indexPromise=null;throw err;});
      const index=await indexPromise;
      if(request!==generation)return;
      const hits=index.map(item=>{
        const title=normalize(item.title), desc=normalize(item.description), full=normalize(item.raw);
        return {...item,score:terms.every(t=>(title+' '+desc+' '+full).includes(t))?terms.reduce((n,t)=>n+(title.includes(t)?10:0)+(desc.includes(t)?4:0)+1,0):0};
      }).filter(x=>x.score>0).sort((a,b)=>b.score-a.score);
      status.textContent=hits.length?`Найдено материалов: ${hits.length}`:'Ничего не найдено. Попробуйте более короткий запрос: «фильтр», «метрик», «MCP».';
      hits.forEach(hit=>{
        const link=document.createElement('a');link.className='search-hit';link.href=hit.url;
        const meta=document.createElement('span');meta.className='row-meta';meta.textContent=`${hit.group} · ${labels[hit.status]}`;
        const title=document.createElement('h2');title.textContent=hit.title;
        const desc=document.createElement('p');desc.textContent=hit.description;
        link.append(meta,title,desc);results.append(link);
      });
    }catch {if(request===generation)status.textContent='Не удалось загрузить поиск. Обновите страницу или откройте справочник через меню.';}
  }
  queryInput.value=new URLSearchParams(location.search).get('q')||'';
  search(queryInput.value);
  document.querySelector('.large-search').addEventListener('submit',event=>{
    event.preventDefault();const url=new URL(location.href);url.searchParams.set('q',queryInput.value);history.pushState({},'',url);search(queryInput.value);
  });
  window.addEventListener('popstate',()=>{queryInput.value=new URLSearchParams(location.search).get('q')||'';search(queryInput.value);});
}
