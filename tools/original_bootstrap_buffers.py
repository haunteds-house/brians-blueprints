"""Bound finished mall stock without limiting belt-fed science intermediates."""
import math
from compact_bootstrap import footprint,DIRECTIONS

SHARED={'iron-gear-wheel','copper-cable','electronic-circuit','advanced-circuit','engine-unit',
        'electric-engine-unit','processing-unit','flying-robot-frame','battery','sulfur','plastic-bar'}
LIMITS={'transport-belt':200,'fast-transport-belt':200,'underground-belt':50,
    'fast-underground-belt':50,'splitter':50,'fast-splitter':50,'locomotive':2,
    'cargo-wagon':4,'fluid-wagon':2,'roboport':5,'oil-refinery':5,'pumpjack':10,
    'storage-tank':10,'assembling-machine-1':20,'assembling-machine-2':20,
    'stone-wall':200,'firearm-magazine':400,'piercing-rounds-magazine':400,
    'rail':400,'rail-signal':100,'rail-chain-signal':100,'solar-panel':100,'accumulator':100}


def bound(bp):
    es=bp['entities'];owners={p:e for e in es for p in footprint(e)}
    minx=min(e['position']['x'] for e in es);miny=min(e['position']['y'] for e in es)
    def ref(e):return f"{e['position']['x']-minx:g},{e['position']['y']-miny:g}"
    result=[]
    for ins in es:
        if 'inserter' not in ins['name']:continue
        x,y=ins['position']['x'],ins['position']['y'];dx,dy=DIRECTIONS[ins.get('direction',0)];reach=2 if ins['name']=='long-handed-inserter' else 1
        source=owners.get((math.floor(x+dx*reach),math.floor(y+dy*reach)),{})
        target=owners.get((math.floor(x-dx*reach),math.floor(y-dy*reach)),{})
        recipe=source.get('recipe','')
        if not recipe or recipe in SHARED or recipe.endswith('-science-pack') or target.get('name') not in {'wooden-chest','iron-chest','steel-chest'}:continue
        limit=LIMITS.get(recipe,50);target['bar']=1;ins['override_stack_size']=1
        ins['control_behavior']={'circuit_enabled':True,'circuit_condition':{'comparator':'<','constant':limit,'first_signal':{'name':recipe,'type':'item'}}}
        wire=[ref(ins),1,ref(target),1]
        if wire not in bp.setdefault('wires',[]):bp['wires'].append(wire)
        result.append({'recipe':recipe,'maximum_requested':limit,'position':target['position']})
    for e in es:
        if e['name']=='wooden-chest' and e['position']=={'x':13.5,'y':44.5}:e['bar']=1
    return result
