#!/usr/bin/env python3
"""Restore original phased geometry as the source for the incremental rework.

This baseline is deliberately separate from the rejected redesign. It is not
an export of the completed six-science expansion.
"""
import copy
import json
from pathlib import Path
from fatul import Processor, read_files, to_pretty_json
from original_bootstrap_routes import automate_green
from original_bootstrap_buffers import bound
from compact_bootstrap import tier

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'brians-bootstrap/source/early-game'
DEST=ROOT/'brians-bootstrap/original-rework'
VERSION=(2<<48)|(1<<32)|(23<<16)
OFFSETS=[(1,47),(4,43),(4,14),(4,4)]
TARGET={'automation':5,'logistic':6,'military':5,'chemical':12,'production':7,'utility':7}


def build():
    folder=DEST/'book';folder.mkdir(parents=True,exist_ok=True)
    for i,(dx,dy) in enumerate(OFFSETS,1):
        data=copy.deepcopy(json.loads((SOURCE/f'phase-#{i}.json').read_text()))
        bp=data['blueprint'];data['index']=i-1
        bp['entities']=[e for e in bp['entities'] if e.get('recipe')!='cliff-explosives']
        for e in bp['entities']:
            e['position']['x']+=dx;e['position']['y']+=dy
        for key in ['shift_x','shift_y']:bp.pop(key,None)
        bp.update(version=VERSION,label=f'Original bootstrap — stage {i} (rework baseline)')
        bp['snap-to-grid']={'x':32,'y':32};bp['absolute-snapping']=True
        bp['position-relative-to-grid']={'x':0,'y':0}
        if i==3:automate_green(bp)
        if i==4:
            from original_bootstrap_oil import balance
            from importlib.util import spec_from_file_location, module_from_spec
            spec=spec_from_file_location('bootstrap_primitives',ROOT/'tools/build-bootstrap.py')
            primitives=module_from_spec(spec);spec.loader.exec_module(primitives)
            balance(bp,ROOT,primitives.e,primitives.power_wires)
            bp=tier(bp,'red');data['blueprint']=bp
        bound(bp)
        bp['description']='Original production/mall geometry. Incomplete rework baseline: missing science extensions, mall additions and unweaving. Not a finished blueprint release.'
        (folder/f'phase-{i}.json').write_text(to_pretty_json(data,compact=True)+'\n')
    final=copy.deepcopy(data);final['index']=4;bp=final['blueprint']
    upgrades={'assembling-machine-1':'assembling-machine-2','inserter':'fast-inserter',
        'burner-inserter':'fast-inserter','small-electric-pole':'medium-electric-pole',
        'stone-furnace':'steel-furnace'}
    for entity in bp['entities']:
        entity['name']=upgrades.get(entity['name'],entity['name'])
    limits=bound(bp)
    (DEST/'mall-stock-limits.json').write_text(json.dumps(limits,indent=2)+'\n')
    bp['label']='Original bootstrap — stage 5, tier 2 development'
    bp['description']='Red belts throughout, assembler 2s, fast inserters, medium poles and steel furnaces. Early science plate-feed replacement, additional sciences/malls and capacity expansion remain unfinished.'
    (folder/'phase-5.json').write_text(to_pretty_json(final,compact=True)+'\n')
    imported=copy.deepcopy(final);imported['index']=5
    from original_bootstrap_imports import connect
    imported['blueprint'],ports,retired=connect(imported['blueprint'],primitives.e)
    (folder/'phase-6.json').write_text(to_pretty_json(imported,compact=True)+'\n')
    (DEST/'retired-science-feeds.json').write_text(json.dumps(retired,indent=2)+'\n')
    (DEST/'priority-imports.json').write_text(json.dumps(ports,indent=2)+'\n')
    planner={'index':6,'upgrade_planner':{'item':'upgrade-planner','version':VERSION,
        'label':'Tier 2 — red belts, assembler 2s, fast inserters and medium poles',
        'settings':{'mappers':[{'index':i,'from':{'type':'entity','name':old},'to':{'type':'entity','name':new}} for i,(old,new) in enumerate({**upgrades,'transport-belt':'fast-transport-belt','underground-belt':'fast-underground-belt','splitter':'fast-splitter'}.items())]}}}
    (folder/'tier-2.json').write_text(to_pretty_json(planner,compact=True)+'\n')
    meta={'blueprint_book':{'item':'blueprint-book','label':'Original bootstrap rework — INCOMPLETE baseline','version':VERSION,'active_index':0}}
    (folder/'_metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    # Coordinate references are relative to the entity minima. Translation
    # preserves original copper/circuit-wire references without remapping.
    encoded=Processor(False).encode(read_files(folder,False))
    roundtrip=Processor(False,ids_mode='keep').decode(encoded)
    assert len(roundtrip['blueprint_book']['blueprints'])==7
    (DEST/'development-book.txt').write_text(encoded+'\n')
    baseline=json.loads((folder/'phase-4.json').read_text())['blueprint']
    counts={name:sum(e.get('recipe')==name+'-science-pack' for e in baseline['entities']) for name in TARGET}
    audit={'status':'incomplete original-geometry baseline','original_science_machines':counts,'required_science_machines':TARGET,'mall_recipes':sorted({e['recipe'] for e in baseline['entities'] if e.get('recipe') and not e['recipe'].endswith('-science-pack')}),'implemented':['Automatic Phase-3 inserter delivery','Controlled heavy/light cracking and shared basic/advanced petroleum','Bounded finished mall stock','Tier-2 machines and uniform red belts','Priority science iron/copper imports replacing isolated furnaces'],'remaining':['Connect and scale all six science chains','Add belt-fed concrete, defense, electric-furnace and nuclear mall recipes','Expand shared intermediates and finish science-priority allocations','Connect main mall overflow and external smelting/steel imports','Verify whole-factory science throughput and progression']}
    (DEST/'routing-audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    print('Built six original-layout development stages plus tier-2 planner; codec round trip passed.')


if __name__=='__main__':build()
