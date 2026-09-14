/* Optional display-only baseline snapshot. Never reads or writes edit drafts. */
(() => {
  const defaults={enabled:false,size:26,vertical:40,horizontal:0,opacity:100};
  const key='nippo-aligned-text-settings-v1';
  let prefs={...defaults};
  try { const saved=JSON.parse(localStorage.getItem(key)||'{}');
    prefs.enabled=saved.enabled===true;
    for(const [k,min,max] of [['size',12,32],['vertical',-40,40],['horizontal',-12,12],['opacity',0,100]])
      if(Number.isFinite(saved[k])) prefs[k]=Math.max(min,Math.min(max,saved[k]));
  } catch {}
  const cache=new Map(); let pending=false;
  const css=document.createElement('style');css.textContent=`
    .aligned-controls{padding:.6rem;border:1px solid var(--line);margin-bottom:.7rem;background:var(--panel)}
    .aligned-controls label{font-size:.85rem;display:inline-flex;gap:.4rem;align-items:center;margin-right:1rem}
    .aligned-controls details{margin-top:.4rem}.aligned-controls summary{cursor:pointer;font-size:.8rem}
    .aligned-controls input[type=range]{width:100px}.aligned-controls small{display:block;color:var(--muted);margin:.4rem 0}
    .line-row{position:relative}.aligned-panel{display:none;position:absolute;pointer-events:none}
    .aligned-active>.aligned-panel{display:block}.aligned-scan{position:relative;width:100%;height:100%}
    .aligned-scan img{display:block;width:100%}.aligned-scan svg{position:absolute;inset:0;width:100%;height:100%;overflow:visible;pointer-events:none}
  `;document.head.append(css);
  const ns='http://www.w3.org/2000/svg';
  function apply(){
    document.querySelectorAll('.aligned-panel').forEach(panel=>{
      panel.parentElement.classList.toggle('aligned-active',prefs.enabled);
      const scan=panel.firstChild,svg=scan.querySelector('svg'),g=svg.firstChild;
      svg.style.opacity=prefs.opacity/100;g.setAttribute('font-size',prefs.size);
      const article=panel.parentElement,crop=article.querySelector('.line-crop');
      const expanded=article.querySelector('.context-toggle')?.getAttribute('aria-expanded')==='true';
      const [cx,cy,w,h]=JSON.parse(expanded?crop.dataset.context:crop.dataset.crop);
      const scale=crop.getBoundingClientRect().width/w;
      const factor=panel._factor||2;
      crop.style.marginTop=prefs.enabled?(8+Math.max(0,-prefs.vertical)*scale*factor)+'px':'';
      crop.style.marginBottom=prefs.enabled?(8+Math.max(0,prefs.vertical+prefs.size*.25)*scale*factor)+'px':'';
      panel.style.left=crop.offsetLeft+'px';panel.style.top=crop.offsetTop+'px';panel.style.width=crop.offsetWidth+'px';panel.style.height=crop.offsetHeight+'px';
      svg.setAttribute('viewBox',`0 0 ${w} ${h}`);
      for(const {t,m,px} of panel._glyphs){
        const x=m.origin[0]+m.dx[0]*(px+prefs.horizontal)+m.dy[0]*(35+prefs.vertical)-cx;
        const y=m.origin[1]+m.dx[1]*(px+prefs.horizontal)+m.dy[1]*(35+prefs.vertical)-cy;
        t.setAttribute('transform',`matrix(${m.dx[0]} ${m.dx[1]} ${m.dy[0]} ${m.dy[1]} ${x} ${y})`);
      }
    });
  }
  function save(){try{localStorage.setItem(key,JSON.stringify(prefs));}catch{}apply();}
  function controls(list){
    if(list.querySelector('.aligned-controls'))return;
    const bar=document.createElement('div');bar.className='aligned-controls';
    bar.innerHTML='<label><input type="checkbox" data-setting="enabled">Aligned baseline text</label><details><summary>Display settings</summary><small>Saved in this browser. Text is a baseline snapshot, not your local edits. Positions are mapped onto the ordinary scan. ␣ shows a space.</small></details>';
    const details=bar.querySelector('details');
    for(const [name,label,min,max] of [['size','Size',12,32],['vertical','Above ↔ below',-40,40],['horizontal','Left/right',-12,12],['opacity','Opacity',0,100]]){
      const l=document.createElement('label');l.textContent=label;const input=document.createElement('input');input.type='range';input.min=min;input.max=max;input.dataset.setting=name;l.append(input);details.append(l);
    }
    const reset=document.createElement('button');reset.type='button';reset.textContent='Reset defaults';details.append(reset);
    function sync(){bar.querySelectorAll('input').forEach(i=>i.type==='checkbox'?i.checked=prefs.enabled:i.value=prefs[i.dataset.setting]);}
    reset.onclick=()=>{prefs={...defaults};sync();save();};
    bar.oninput=e=>{const i=e.target;if(!i.dataset.setting)return;prefs[i.dataset.setting]=i.type==='checkbox'?i.checked:Number(i.value);save();};
    sync();list.prepend(bar);
  }
  async function mount(){
    const page=state.currentPage,list=document.querySelector('#page-content .line-list');
    if(!page||!list||page.page_id!=='bnf-f0230')return;
    const id=page.page_id;
    const asset='assets/alignment/'+id+'.json',version=window.NIPPO_ASSET_VERSION?.assets[asset];
    if(!cache.has(id))cache.set(id,fetch(asset+(version?'?v='+version:'')).then(r=>{if(!r.ok)throw Error(r.status);return r.json();}).catch(()=>null));
    const data=await cache.get(id);if(!data||!list.isConnected||state.currentPage!==page)return;
    const current=new Map(page.zones.flatMap(z=>z.lines).map(l=>[l.id,l.runs]));
    // Reject stale text or typeface snapshots, even if local edits exist.
    if(data.rows.some(r=>JSON.stringify(current.get(r.id))!==JSON.stringify(r.runs)))return;
    controls(list);const maxWidth=Math.max(...data.rows.map(r=>r.image_width||0));
    for(const row of data.rows){
      if(!row.scan_mappings&&!row.scan_mapping)continue;
      const article=[...list.querySelectorAll('.line-row')].find(a=>a.dataset.line===row.id);
      if(!article||article.querySelector('.aligned-panel'))continue;
      const panel=document.createElement('div');panel.className='aligned-panel';panel._glyphs=[];const scan=document.createElement('div');scan.className='aligned-scan';panel.append(scan);
      const svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox',`0 0 ${row.image_width} 48`);svg.setAttribute('aria-hidden','true');const g=document.createElementNS(ns,'g');svg.append(g);scan.append(svg);
      let n=0;for(const run of row.runs)for(const char of run.text){const i=n++,a=row.alignment[i],space=/\s/.test(char),m=row.scan_mappings?.[i]||row.scan_mapping;if(!m)continue;
        let start=i,end=i+1;if(a.kind==='uncertain'){while(start>0&&JSON.stringify(row.alignment[start-1])===JSON.stringify(a))start--;while(end<row.alignment.length&&JSON.stringify(row.alignment[end])===JSON.stringify(a))end++;}
        const t=document.createElementNS(ns,'text');t.textContent=space?'␣':char;t.setAttribute('text-anchor','middle');t.setAttribute('font-family',space?'Arial,sans-serif':'Georgia,serif');t.setAttribute('font-style',!space&&run.typeface==='italic'?'italic':'normal');t.setAttribute('fill',a.kind==='uncertain'?'#c04400':'#006bff');if(space){t.setAttribute('textLength',Math.max(3,a.width*row.image_width/100*.8));t.setAttribute('lengthAdjust','spacingAndGlyphs');}g.append(t);panel._glyphs.push({t,m,px:(a.left+a.width*(i-start+.5)/(end-start))*row.image_width/100});panel._factor=Math.hypot(...m.dy);
      }
      article.querySelector('.line-crop').after(panel);
    }
    apply();
  }
  new MutationObserver(()=>{if(pending)return;pending=true;requestAnimationFrame(()=>{pending=false;mount();});}).observe(document.querySelector('#page-content'),{childList:true,subtree:true});
  window.addEventListener('resize',apply);mount();
  document.addEventListener('click',e=>{if(e.target.closest('.context-toggle,.line-crop'))requestAnimationFrame(apply);});
})();
