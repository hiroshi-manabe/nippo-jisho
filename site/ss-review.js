'use strict';
let data, choices, group=0; const size=40;
const $=id=>document.getElementById(id);
const esc=s=>s.replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function persist(){localStorage.setItem(`nippo-ss:${data.baseline}`,JSON.stringify(choices));status();}
function status(){$('status').textContent=`${choices.filter(Boolean).length} two-long-s / ${choices.length} total`;}
function render(){
 $('page').value=group;$('grid').innerHTML='';
 data.items.slice(group*size,(group+1)*size).forEach((item,j)=>{
  const i=group*size+j, card=document.createElement('article');card.className=`tile ${choices[i]?'checked':''}`;
  const text=esc(item.text.slice(0,item.position))+'<mark>ſſ</mark>'+esc(item.text.slice(item.position+2));
  card.innerHTML=`<label><input type="checkbox" data-index="${i}" ${choices[i]?'checked':''}> ${esc(item.id)} · keep ſſ <small>(AI: ${item.two_long?'ſſ':'ß'})</small></label><img src="${item.image}" loading="lazy" alt="Scan ${esc(item.id)}"><div>${text}</div><details><summary>Enlarge with surrounding lines</summary><div class="image-window"><img src="${item.image.replace('.webp','-context.webp')}" loading="lazy" alt="Enlarged scan with context"></div><a href="index.html#f${item.leaf}" target="_blank">Main review</a> · <a href="https://gallica.bnf.fr/ark:/12148/bpt6k852354j/f${item.leaf}.item" target="_blank">Full scan</a></details>`;
  card.querySelector('input').addEventListener('change',e=>{choices[i]=e.target.checked;card.classList.toggle('checked',choices[i]);persist();});
  card.querySelector('input').addEventListener('keydown',e=>{
   const d={ArrowDown:1,ArrowRight:1,ArrowUp:-1,ArrowLeft:-1}[e.key];if(!d)return;e.preventDefault();
   const k=Math.max(0,Math.min(choices.length-1,i+d));group=Math.floor(k/size);render();document.querySelector(`[data-index="${k}"]`).focus();
  });$('grid').append(card);
 });status();
}
fetch('assets/ss-review/candidates.json').then(r=>{if(!r.ok)throw Error('Cannot load candidates');return r.json();}).then(d=>{
 data=d;const saved=localStorage.getItem(`nippo-ss:${d.baseline}`);choices=saved?JSON.parse(saved):d.items.map(x=>x.two_long);
 if(!Array.isArray(choices)||choices.length!==d.items.length||choices.some(x=>typeof x!=='boolean'))throw Error('Invalid saved choices; no data was discarded.');
 for(let i=0;i<Math.ceil(choices.length/size);i++){$('page').add(new Option(`${i*size+1}–${Math.min((i+1)*size,choices.length)}`,i));}
 $('page').onchange=()=>{group=Number($('page').value);render();};
 $('prev').onclick=()=>{group=Math.max(0,group-1);render();};$('next').onclick=()=>{group=Math.min(Math.ceil(choices.length/size)-1,group+1);render();};
 $('issue').href='https://github.com/hiroshi-manabe/nippo-jisho/issues/new?title='+encodeURIComponent('[f1–f200] Italic double-s review');
 $('copy').onclick=()=>{
  const payload=JSON.stringify({format:'nippo-italic-ss-review',version:1,baseline:d.baseline,total:d.items.length,default:'ß',keep:choices.flatMap((v,i)=>v?[i]:[])});
  $('payload').value=payload;$('export').hidden=false;
  if(navigator.clipboard)navigator.clipboard.writeText(payload).then(()=>{$('status').textContent='Copied — paste into the Issue.';}).catch(()=>{$('payload').focus();$('payload').select();});
  else{$('payload').focus();$('payload').select();}
 };render();
}).catch(e=>{$('status').textContent=e.message;});
