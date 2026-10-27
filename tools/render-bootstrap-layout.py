#!/usr/bin/env python3
"""Render the actual exported entities as a compact layout reference."""
import json
from pathlib import Path
from compact_bootstrap import footprint

ROOT=Path(__file__).resolve().parents[1]
bp=json.loads((ROOT/'brians-bootstrap/book/phase-6.json').read_text())['blueprint']
parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="1024" viewBox="0 0 160 128">',
       '<title>Integrated bootstrap: 160 by 128 tiles, red-belt phase</title>',
       '<rect width="160" height="128" fill="#151a20"/>']
for entity in bp['entities']:
    name=entity['name'];x,y=entity['position']['x'],entity['position']['y']
    if 'belt' in name or 'splitter' in name:
        color='#b65446' if 'underground' not in name else '#ef9368'
    elif 'assembling-machine' in name:color='#4184ac'
    elif name=='chemical-plant':color='#ac6eaf'
    elif name=='oil-refinery':color='#b19a5c'
    elif name=='lab':color='#c1daed'
    elif 'electric-pole' in name:color='#e6d573'
    elif name in {'pipe','pipe-to-ground','storage-tank','pump'}:color='#769aa3'
    elif 'inserter' in name:color='#999644'
    else:color='#9b8470'
    cells=footprint(entity);left=min(p[0] for p in cells);top=min(p[1] for p in cells)
    width=max(p[0] for p in cells)-left+1;height=max(p[1] for p in cells)-top+1
    parts.append(f'<rect x="{left+.08:g}" y="{top+.08:g}" width="{width-.16:g}" height="{height-.16:g}" fill="{color}"/>')
    if entity.get('recipe','').endswith('-science-pack'):
        label={'automation':'R','logistic':'G','military':'M','chemical':'B','production':'P','utility':'Y'}[entity['recipe'].removesuffix('-science-pack')]
        parts.append(f'<text x="{x}" y="{y+.5}" text-anchor="middle" font-family="sans-serif" font-size="1.5" fill="#fff">{label}</text>')
for x in range(0,161,32):parts.append(f'<path d="M{x},0V128" stroke="#d5e0e8" stroke-width=".12" opacity=".6"/>')
for y in range(0,129,32):parts.append(f'<path d="M0,{y}H160" stroke="#d5e0e8" stroke-width=".12" opacity=".6"/>')
parts.append('</svg>')
(ROOT/'brians-bootstrap/layout.svg').write_text('\n'.join(parts)+'\n')
