/* Notify only: never interrupt editing or clear stored work. */
(() => {
  const current=window.NIPPO_ASSET_VERSION?.version;if(!current)return;
  let busy=false,notice;
  async function check(){
    if(busy||notice||document.hidden)return;busy=true;
    try{
      const response=await fetch('ui-version.json?fresh='+Date.now(),{cache:'no-store'});
      if(!response.ok)return;const latest=await response.json();
      if(!latest.version||latest.version===current)return;
      notice=document.createElement('div');notice.setAttribute('role','status');
      notice.style.cssText='position:fixed;bottom:5rem;right:1rem;z-index:80;padding:.7rem;background:var(--panel);border:1px solid var(--line);border-radius:.5rem;box-shadow:var(--shadow)';
      notice.append('UI update available. ');const button=document.createElement('button');button.textContent='Reload';notice.append(button);
      button.onclick=()=>{
        if(document.querySelector('.edit-form')){alert('Please save or cancel the open editor before reloading. Your saved local edits will remain.');return;}
        const url=new URL(location.href);url.searchParams.set('ui',latest.version);location.assign(url.href);
      };document.body.append(notice);
    }catch{}finally{busy=false;}
  }
  document.addEventListener('visibilitychange',check);setInterval(check,300000);check();
})();
