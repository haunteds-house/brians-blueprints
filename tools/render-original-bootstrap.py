#!/usr/bin/env python3
"""Draw actual original-rework entities, including west priority headers."""
import json
import html
from pathlib import Path
from compact_bootstrap import footprint
ROOT=Path(__file__).resolve().parents[1]
bp=json.loads((ROOT/'brians-bootstrap/original-rework/book/phase-6.json').read_text())['blueprint']
parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="960" viewBox="-32 0 128 96">',
'<title>Original bootstrap rework: development checkpoint, not the completed six-science expansion</title>',
'<rect x="-32" width="128" height="96" fill="#171d24"/>']
for e in bp['entities']:
    n=e['name'];cells=footprint(e);left=min(x for x,y in cells);top=min(y for x,y in cells)
    width=max(x for x,y in cells)-left+1;height=max(y for x,y in cells)-top+1
    color='#bc6754' if 'belt' in n or 'splitter' in n else '#478eb6' if 'assembling-machine' in n else '#a477bb' if n=='chemical-plant' else '#bb9850' if n=='oil-refinery' else '#7aafba' if 'pipe' in n or n=='storage-tank' else '#e1ce5c' if 'electric-pole' in n else '#8d9560'
    text=html.escape(n+(' — '+e['recipe'] if e.get('recipe') else ''))
    parts.append(f'<rect x="{left+.07}" y="{top+.07}" width="{width-.14}" height="{height-.14}" fill="{color}"><title>{text}</title></rect>')
for x in range(-32,97,32):parts.append(f'<path d="M{x},0V96" stroke="#d8e2e9" stroke-width=".12" opacity=".6"/>')
for y in range(0,97,32):parts.append(f'<path d="M-32,{y}H96" stroke="#d8e2e9" stroke-width=".12" opacity=".6"/>')
parts.append('</svg>')
(ROOT/'brians-bootstrap/original-rework/layout.svg').write_text('\n'.join(parts)+'\n')
