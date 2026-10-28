"""Science-priority plate handoff for the original science machinery."""
import math
from compact_bootstrap import footprint,DIRECTIONS,tier
from original_bootstrap_routes import belt_route


def connect(bp,create):
    es=bp['entities'];old_min=(min(e['position']['x'] for e in es),min(e['position']['y'] for e in es))
    # Retire the three isolated plate furnaces in the science pocket. Their output inserters remain in position.
    centers={(1,44),(4,46),(4,51)}
    furnaces=[e for e in es if e['name'] in {'stone-furnace','steel-furnace'} and (e['position']['x'],e['position']['y']) in centers]
    cells=set().union(*(footprint(e) for e in furnaces))
    retired=[]
    for e in list(es):
        remove=e in furnaces
        if 'inserter' in e['name']:
            x,y=e['position']['x'],e['position']['y'];dx,dy=DIRECTIONS[e.get('direction',0)];reach=2 if e['name']=='long-handed-inserter' else 1
            drop=(math.floor(x-dx*reach),math.floor(y-dy*reach))
            if drop in cells:remove=True
        if e['name']=='constant-combinator' and (e['position']['x'],e['position']['y']) in {(0.5,46.5),(0.5,50.5),(1.5,48.5)}:remove=True
        if remove:
            retired.append({'name':e['name'],'position':dict(e['position'])})
            es.remove(e)
    # One header per current science feed. The overflow ends are deliberately
    # exposed to the player's main supply lines rather than fed back into ore.
    ports=[]
    specs=[('iron-plate',(1,43),4),('iron-plate',(4,46),4),('copper-plate',(4,50),4)]
    for index,(item,goal,direction) in enumerate(specs):
        y=3.5+8*index
        es.extend([create('fast-transport-belt',-31.5,y,direction=4),create('fast-transport-belt',-30.5,y,direction=4),
            create('fast-splitter',-29.5,y+.5,direction=4,output_priority='left'),
            create('fast-transport-belt',-28.5,y,direction=4),
            create('fast-transport-belt',-28.5,y+1,direction=4),create('fast-transport-belt',-27.5,y+1,direction=4)])
        # This router uses conservative yellow-safe tunnel spans. Convert the
        # new route to red afterwards, preserving every connection.
        before=len(es)
        belt_route(bp,(-28,int(y)),goal,goal_direction=direction,initial_direction=4,bounds=(-32,0,96,96))
        for e in es[before:]:
            e['name']={'transport-belt':'fast-transport-belt','underground-belt':'fast-underground-belt'}.get(e['name'],e['name'])
        ports.append({'item':item,'input':{'x':-31.5,'y':y},'mall_overflow':{'x':-27.5,'y':y+1},'science_target':{'x':goal[0]+.5,'y':goal[1]+.5}})
    new_min=(min(e['position']['x'] for e in es),min(e['position']['y'] for e in es))
    def rebase(ref):
        x,y=map(float,ref.split(','));return f'{x+old_min[0]-new_min[0]:g},{y+old_min[1]-new_min[1]:g}'
    bp['wires']=[[rebase(a),ac,rebase(b),bc] for a,ac,b,bc in bp.get('wires',[])]
    bp['label']='Original bootstrap — stage 6, science-priority plate imports (development)'
    bp['description']='Original science pocket takes iron/copper plates first from three west import headers. Connect overflow ends to main mall lines. Retire the three replaced science furnaces and their inbound fuel/ore inserters. No ore at these plate ports. Additional sciences, malls and intermediate expansion remain unfinished. Reservation extends one chunk west.'
    return bp,ports,retired
