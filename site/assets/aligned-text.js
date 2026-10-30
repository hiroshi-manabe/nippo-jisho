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
    .aligned-scan text{paint-order:stroke fill;stroke:white;stroke-width:1px;stroke-linejoin:round}
  `;document.head.append(css);
  const ns='http://www.w3.org/2000/svg';
  function wordSegments(row){
    const segments=[];
    let current=null,index=0;
    // Per-character mappings can differ slightly through numerical fitting.
    // Keep genuinely displaced scan fragments separate, even inside a word.
    const sameMapping=(a,b)=>['origin','dx','dy'].every(key=>
      a[key].every((value,i)=>Math.abs(value-b[key][i])<(key==='origin'?1:.01)));
    for(const run of row.runs)for(const character of run.text){
      const i=index++,a=row.alignment[i],m=row.scan_mappings?.[i]||row.scan_mapping;
      if(!a||!m){current=null;continue;}
      const space=/\s/u.test(character),left=a.left*row.image_width/100,right=(a.left+a.width)*row.image_width/100;
      if(space||!current||!sameMapping(current.m,m)){
        current={m,left,right,space,characters:[]};segments.push(current);
      }else{current.left=Math.min(current.left,left);current.right=Math.max(current.right,right);}
      current.characters.push({character,typeface:run.typeface,uncertain:a.kind==='uncertain'});
      if(space)current=null;
    }
    return segments;
  }
  function wordSpacing(targetWidth,naturalWidth,characters,fontSize){
    const gaps=Array.from(characters).filter(c=>! /\p{M}/u.test(c)).length-1;
    if(gaps<1||naturalWidth<=0)return 0;
    // Small spacing adjustments only: never stretch the letterforms to fit.
    const limit=fontSize*.06;
    return Math.max(-limit,Math.min(limit,(targetWidth-naturalWidth)/gaps));
  }
  function apply(){
    document.querySelectorAll('.alignment-unavailable').forEach(label=>label.hidden=!prefs.enabled);
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
      for(const {t,m,px,width,space} of panel._glyphs){
        t.setAttribute('letter-spacing','0');
        if(!space)t.setAttribute('letter-spacing',wordSpacing(width,t.getComputedTextLength(),t.textContent,prefs.size));
        const x=m.origin[0]+m.dx[0]*(px+prefs.horizontal)+m.dy[0]*(35+prefs.vertical)-cx;
        const y=m.origin[1]+m.dx[1]*(px+prefs.horizontal)+m.dy[1]*(35+prefs.vertical)-cy;
        t.setAttribute('transform',`matrix(${m.dx[0]} ${m.dx[1]} ${m.dy[0]} ${m.dy[1]} ${x} ${y})`);
      }
    });
  }
  function save(){try{localStorage.setItem(key,JSON.stringify(prefs));}catch{}apply();}
  function controls(list,data){
    if(list.querySelector('.aligned-controls'))return;
    const bar=document.createElement('div');bar.className='aligned-controls';
    bar.innerHTML='<label><input type="checkbox" data-setting="enabled">Aligned baseline text</label><details><summary>Display settings</summary><small>Saved in this browser. Text is a baseline snapshot, not your local edits. Positions are mapped onto the ordinary scan. ␣ shows a space.</small></details>';
    const details=bar.querySelector('details');
    const usable=data.rows.filter(r=>r.scan_mappings||r.scan_mapping).length;
    bar.querySelector('label').append(` · ${usable}/${data.rows.length}`);
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
    if(!page||!list||!window.NIPPO_ASSET_VERSION?.assets['assets/alignment/'+page.page_id+'.json'])return;
    const id=page.page_id;
    const asset='assets/alignment/'+id+'.json',version=window.NIPPO_ASSET_VERSION?.assets[asset];
    if(!cache.has(id))cache.set(id,fetch(asset+(version?'?v='+version:'')).then(r=>{if(!r.ok)throw Error(r.status);return r.json();}).catch(()=>null));
    const data=await cache.get(id);if(!data||!list.isConnected||state.currentPage!==page)return;
    const current=new Map(page.zones.flatMap(z=>z.lines).map(l=>[l.id,l.runs]));
    // Reject stale text or typeface snapshots, even if local edits exist.
    if(data.rows.some(r=>JSON.stringify(current.get(r.id))!==JSON.stringify(r.runs)))return;
    controls(list,data);
    for(const row of data.rows){
      const article=[...list.querySelectorAll('.line-row')].find(a=>a.dataset.line===row.id);
      if(article&&!row.scan_mappings&&!row.scan_mapping){
        if(!article.querySelector('.alignment-unavailable')){
          const label=document.createElement('small');label.className='alignment-unavailable';label.textContent='Alignment unavailable';label.style.cssText='color:var(--muted);padding:.3rem .8rem';article.append(label);
        }
        continue;
      }
      if(!article||article.querySelector('.aligned-panel'))continue;
      const panel=document.createElement('div');panel.className='aligned-panel';panel._glyphs=[];const scan=document.createElement('div');scan.className='aligned-scan';panel.append(scan);
      const svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox',`0 0 ${row.image_width} 48`);svg.setAttribute('aria-hidden','true');const g=document.createElementNS(ns,'g');svg.append(g);scan.append(svg);
      for(const segment of wordSegments(row)){
        const {m,left,right,space,characters}=segment;
        const t=document.createElementNS(ns,'text');
        t.setAttribute('text-anchor',space?'middle':'start');
        t.setAttribute('font-family',space?'Arial,sans-serif':'Georgia,serif');
        if(space){t.textContent='␣';t.setAttribute('fill','#006bff');}
        else{
          // Normal proportional layout within the word; preserve mixed fonts
          // and uncertainty colors without assigning character positions.
          let span=null,style='';
          for(const item of characters){
            const nextStyle=item.typeface+':'+item.uncertain;
            if(!span||style!==nextStyle){
              span=document.createElementNS(ns,'tspan');style=nextStyle;
              span.setAttribute('font-style',item.typeface==='italic'?'italic':'normal');
              span.setAttribute('fill',item.uncertain?'#c04400':'#006bff');t.append(span);
            }
            span.textContent+=item.character;
          }
        }
        g.append(t);panel._glyphs.push({t,m,px:space?(left+right)/2:left,width:right-left,space});panel._factor=Math.hypot(...m.dy);
      }
      article.querySelector('.line-crop').after(panel);
    }
    apply();
  }
  new MutationObserver(()=>{if(pending)return;pending=true;requestAnimationFrame(()=>{pending=false;mount();});}).observe(document.querySelector('#page-content'),{childList:true,subtree:true});
  window.addEventListener('resize',apply);mount();
  document.addEventListener('click',e=>{if(e.target.closest('.context-toggle,.line-crop'))requestAnimationFrame(apply);});
})();
