"""Expand a frozen, compact italic double-s review into ordinary corrections."""
from collections import defaultdict


def expand(payload, manifest):
    if (payload.get('format') != 'nippo-italic-ss-review' or
            payload.get('version') != 1 or payload.get('default') != 'ß' or
            payload.get('baseline') != manifest['baseline'] or
            payload.get('total') != len(manifest['items'])):
        raise ValueError('Italic double-s review does not match the frozen candidate set.')
    keep = payload.get('keep')
    if (not isinstance(keep, list) or
            any(type(i) is not int or not 0 <= i < len(manifest['items']) for i in keep) or
            len(keep) != len(set(keep))):
        raise ValueError('keep must contain distinct valid zero-based candidate indexes.')
    grouped = defaultdict(list)
    for i, item in enumerate(manifest['items']):
        if not 1 <= item['leaf'] <= 200:
            raise ValueError('Candidate outside f1–f200.')
        if i not in keep:
            grouped[(item['leaf'], item['line'])].append(item)
    pages = defaultdict(list)
    for (leaf, line), items in grouped.items():
        before = items[0]['text']
        after = before
        for item in sorted(items, key=lambda x: x['position'], reverse=True):
            pos = item['position']
            if item['text'] != before or before[pos:pos+2] != 'ſſ':
                raise ValueError('Invalid frozen occurrence position.')
            after = after[:pos] + 'ß' + after[pos+2:]
        pages[leaf].append(dict(line=line, before=before, after=after))
    if not pages:
        raise ValueError('All candidates retained: no transcription changes to apply.')
    return dict(schema=4, pages=[dict(schema=3, page=f'f{leaf}',
        base_commit=manifest['commit'],
        base_transcription_version=manifest['page_versions'][str(leaf)],
        changes=changes) for leaf, changes in sorted(pages.items())])
