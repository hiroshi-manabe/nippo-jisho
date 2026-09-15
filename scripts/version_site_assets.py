"""Content-version local UI assets after the static build is complete."""
import hashlib
import json
import re


def version_assets(output):
    assets={p.relative_to(output).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()[:20]
            for p in output.rglob('*') if p.is_file() and
            (p.suffix in ('.js','.css') or '/assets/alignment/' in p.as_posix())}
    pages={p.relative_to(output).as_posix():p.read_text() for p in output.rglob('*.html')}
    # Keep data hashes for cache busting, but do not announce background
    # alignment generation (or reference-content edits) as a UI upgrade.
    ui_assets={name:value for name,value in assets.items()
               if name.endswith(('.js','.css'))}
    version=hashlib.sha256(json.dumps({'assets':ui_assets,'html':pages.get('index.html','')},sort_keys=True).encode()).hexdigest()[:20]
    manifest={'version':version,'assets':assets}
    (output/'ui-version.json').write_text(json.dumps(manifest,sort_keys=True)+'\n')
    for relative,content in pages.items():
        path=output/relative
        def replace(match):
            url=match[2]
            if ':' in url or url.startswith(('/', '#')):return match[0]
            target=(path.parent/url).resolve()
            try:key=target.relative_to(output.resolve()).as_posix()
            except ValueError:return match[0]
            return f'{match[1]}="{url}?v={assets[key]}"' if key in assets else match[0]
        content=re.sub(r'(src|href)="([^"?]+)"',replace,content)
        if relative=='index.html':
            content=content.replace('</head>', '<script>window.NIPPO_ASSET_VERSION='+json.dumps(manifest).replace('<','\\u003c')+';</script></head>')
        path.write_text(content)
