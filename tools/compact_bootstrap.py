"""Integrated, uniform-tier bootstrap geometry and routing.

Fluid crossings use ordinary perpendicular underground pipes. Belt tiers never
encode routing: every phase has one belt tier, including all tunnel endpoints.
"""
import copy
import heapq
from functools import lru_cache
import itertools
import json
import math
from pathlib import Path

DIRECTIONS = {0: (0, -1), 4: (1, 0), 8: (0, 1), 12: (-1, 0)}
BELTS = {
    'yellow': ('transport-belt', 'underground-belt', 'splitter'),
    'red': ('fast-transport-belt', 'fast-underground-belt', 'fast-splitter'),
    'blue': ('express-transport-belt', 'express-underground-belt', 'express-splitter')}


def tier(bp, name):
    bp = copy.deepcopy(bp)
    for entity in bp['entities']:
        for index in range(3):
            if entity['name'] in {values[index] for values in BELTS.values()}:
                entity['name'] = BELTS[name][index]
                break
    return bp


def footprint(entity):
    name = entity['name']
    w = h = 1
    if name in {'assembling-machine-1', 'assembling-machine-2', 'assembling-machine-3',
                'chemical-plant', 'electric-furnace', 'lab', 'storage-tank'}:
        w = h = 3
    elif name == 'oil-refinery': w = h = 5
    elif name == 'rocket-silo': w = h = 9
    elif name == 'cargo-landing-pad': w = h = 8
    elif name in {'stone-furnace', 'steel-furnace', 'big-electric-pole'}: w = h = 2
    elif 'splitter' in name: w, h = 2, 1
    elif name == 'pump': w, h = 1, 2
    if entity.get('direction', 0) in {4, 12}: w, h = h, w
    x, y = entity['position']['x'], entity['position']['y']
    return {(xx, yy) for xx in range(math.floor(x-w/2+.01), math.ceil(x+w/2-.01))
            for yy in range(math.floor(y-h/2+.01), math.ceil(y+h/2-.01))}


class FluidRouter:
    """Route pipes around buildings and keep unrelated fluid segments apart."""
    def __init__(self, entities, labels, create, bounds=(160,128)):
        self.entities, self.create = entities, create
        self.bounds = bounds
        self.labels = dict(labels)
        self.solids, self.pipes, self.moat = set(), {}, set()
        for entity in entities:
            point = (math.floor(entity['position']['x']), math.floor(entity['position']['y']))
            if entity['name'] in {'pipe', 'pipe-to-ground', 'storage-tank'}:
                self.pipes[point] = self.labels.get(point, 'other')
                if entity['name'] == 'storage-tank': self.solids |= footprint(entity)
            else:
                cells = footprint(entity)
                self.solids |= cells
                if entity['name'] in {'chemical-plant', 'oil-refinery', 'pump'}:
                    self.moat |= {(x+dx, y+dy) for x, y in cells
                                  for dx, dy in [(0,0), *DIRECTIONS.values()]}
        self.tunnels = []
        endpoints = {(math.floor(t['position']['x']), math.floor(t['position']['y'])):t
                     for t in entities if t['name'] == 'pipe-to-ground'}
        for (x, y), entity in endpoints.items():
            # Pipe-to-ground direction is the open side, opposite its tunnel.
            d = (entity.get('direction', 0) + 8) % 16
            dx, dy = DIRECTIONS[d]
            for distance in range(1, 11):
                other = endpoints.get((x+dx*distance, y+dy*distance))
                if other and other.get('direction', 0) == d:
                    self.tunnels.append(((x, y), (x+dx*distance, y+dy*distance)))
                    break

    def tunnel_clear(self, a, b):
        for c, d in self.tunnels:
            if a[0] == b[0] == c[0] == d[0]:
                if max(min(a[1],b[1]),min(c[1],d[1])) <= min(max(a[1],b[1]),max(c[1],d[1])): return False
            if a[1] == b[1] == c[1] == d[1]:
                if max(min(a[0],b[0]),min(c[0],d[0])) <= min(max(a[0],b[0]),max(c[0],d[0])): return False
        return True

    def route(self, start, goal, fluid):
        start, goal = tuple(map(math.floor,start)), tuple(map(math.floor,goal))
        @lru_cache(None)
        def free(p, underground=False):
            if not (0 <= p[0] < self.bounds[0] and 0 <= p[1] < self.bounds[1]): return False
            if p in {start, goal}: return not underground
            if p in self.solids or p in self.moat: return False
            if p in self.pipes: return False
            if not underground:
                for dx, dy in DIRECTIONS.values():
                    q=(p[0]+dx,p[1]+dy)
                    if q in self.pipes and self.pipes[q] != fluid: return False
            return True
        serial=itertools.count()
        queue=[(0,next(serial),start)]
        costs={start:0}; previous={}
        def push(point, cost, parent, action):
            if cost >= costs.get(point,float('inf')): return
            costs[point]=cost;previous[point]=(parent,action)
            distance=(abs(goal[0]-point[0])+abs(goal[1]-point[1]))*.25
            heapq.heappush(queue,(cost+distance,next(serial),point))
        visited=set()
        clear=lru_cache(None)(self.tunnel_clear)
        while queue:
            _,_,p=heapq.heappop(queue)
            if p in visited: continue
            visited.add(p)
            if p==goal:break
            used={start};cursor=p
            while cursor in previous:
                cursor,action=previous[cursor]
                if action[0]=='pipe':used.add(action[1])
                else:used.update(action[1:4])
            for direction,(dx,dy) in DIRECTIONS.items():
                q=(p[0]+dx,p[1]+dy)
                if q not in used and free(q):push(q,costs[p]+1,p,('pipe',q))
                if q in used or q in self.pipes or not free(q,True): continue
                for n in range(2,11):
                    end=(q[0]+n*dx,q[1]+n*dy)
                    after=(end[0]+dx,end[1]+dy)
                    if end in used or after in used or end in self.pipes or not free(end,True) or not free(after):continue
                    if not clear(q,end):continue
                    push(after,costs[p]+3+n*.25,p,('tunnel',q,end,after,direction))
        else:
            near=[(v['name'],v['position']) for v in self.entities if any(abs(v['position']['x']-q[0]-.5)<3 and abs(v['position']['y']-q[1]-.5)<3 for q in [start,goal])]
            raise ValueError(f'No fluid route for {fluid}: {start} -> {goal}; nearby={near}')
        steps=[];p=goal
        while p!=start:
            p,action=previous[p];steps.append(action)
        steps.reverse()
        placements={start:('pipe',0)}
        new_tunnels=[]
        def place(point,value):
            if point in placements:
                raise ValueError('Fluid route crosses itself at '+str(point))
            placements[point]=value
        for action in steps:
            if action[0]=='pipe':place(action[1],('pipe',0))
            else:
                _,a,b,c,d=action
                place(a,('pipe-to-ground',(d+8)%16))
                place(b,('pipe-to-ground',d))
                place(c,('pipe',0))
                new_tunnels.append((a,b))
        assert placements[start][0]=='pipe' and placements[goal][0]=='pipe', 'Fluid port overwritten by a tunnel'
        self.tunnels.extend(new_tunnels)
        for point,(name,direction) in placements.items():
            if point in self.pipes:continue
            self.entities.append(self.create(name,point[0]+.5,point[1]+.5,
                                            **({'direction':direction} if name=='pipe-to-ground' else {})))
            self.pipes[point]=fluid
        return placements


def compact(reference, root, create, power_wires, early_cell):
    """Keep all six sciences at one anchor in a five-by-four-chunk bootstrap."""
    bp=tier(unweave(reference),'red')
    es=bp['entities']
    # Discard the old campus's outlying auxiliary refinery and long pipe tails.
    es[:]=[e for e in es if e['position']['y']<128 and e['position']['x']<160
           and not (e['name']=='bulk-inserter' and e['position']['x']>=106 and e['position']['y']>=104)
           and not (e['name']=='pipe-to-ground' and (e['position']['x'],e['position']['y']) in {(19.5,124.5),(78.5,121.5)})
           and not (e['name']=='medium-electric-pole' and e['position']['x']==44.5
                    and e['position']['y']>=127)]
    # Crude import storage is unnecessary in the bootstrap: its train station
    # already buffers the fluid. Retain the upper inlet connection as a pipe.
    for entity in list(es):
        if entity['name']=='storage-tank' and entity['position']['y']==127.5:
            x=entity['position']['x']
            es.remove(entity)
            # All four source tanks had their open top corner to the west.
            es.append(create('pipe',x+(1 if entity.get('direction',0)==4 else -1),126.5))
    # The original first-smelting cell stays inside the shared reservation.
    # It is retired at the red-belt/external-smelting handoff.
    for old in json.loads((root/'brians-bootstrap/source/early-game/phase-#1.json').read_text())['blueprint']['entities']:
        if old['name']=='constant-combinator': continue
        entity=copy.deepcopy(old)
        entity['position']['x']+=1
        entity['position']['y']+=102
        entity['_starter_only']=True
        es.append(entity)
    # Small construction/defense production belongs to the bootstrap itself.
    # Batch supplies do not consume the science belts while the player is away.
    mall_recipes=['transport-belt','underground-belt','splitter','inserter','small-electric-pole',
                  'gun-turret','firearm-magazine','stone-wall','repair-pack','solar-panel']
    centers=[(x,y) for y in (108.5,120.5) for x in (111.5,117.5,123.5,147.5,153.5)]
    for recipe,(x,y) in zip(mall_recipes,centers):
        cell=early_cell(recipe,recipe,0)['blueprint']
        for entity in cell['entities']:
            entity=copy.deepcopy(entity)
            entity['_construction_bay']=True
            entity['position']['x']+=x-8.5;entity['position']['y']+=y-8.5
            if entity['name']=='assembling-machine-2':entity['name']='assembling-machine-1'
            cells=footprint(entity)
            es[:]=[old for old in es if not ('electric-pole' in old['name'] and footprint(old)&cells)]
            es.append(entity)
    # Refinery headroom stays inside the bootstrap, beside the construction bay.
    es.append(create('oil-refinery',136.5,116.5,recipe='basic-oil-processing'))
    # Static segment membership was inspected with the official 2.1 engine on
    # the unchanged source layout. It prevents joining a water/acid/oil line.
    labels={(math.floor(v['x']),math.floor(v['y'])):v['fluid'] for v in
            json.loads((root/'brians-bootstrap/source/science-fluid-segments.json').read_text())}
    es.extend([create('pipe-to-ground',78.5,121.5,direction=0),
               create('pipe-to-ground',78.5,126.5,direction=8),
               create('pipe',78.5,127.5)])
    for point in [(78,121),(78,126),(78,127)]: labels[point]='petroleum-gas'
    # Reserve both external inlets before routing either fluid, so one route
    # cannot pass through the neighbour of a not-yet-placed inlet.
    es.extend([create('pipe',.5,97.5),create('pipe',.5,99.5),
               create('pipe',138.5,113.5),create('pipe',138.5,112.5),create('pipe',138.5,111.5)])
    for point in [(138,113),(138,112),(138,111)]:labels[point]='petroleum-gas'
    labels[(0,97)]='water';labels[(0,99)]='crude-oil'
    router=FluidRouter(es,labels,create)
    for fluid,start,end in [
        ('water',(.5,97.5),(7.5,123.5)),
        ('crude-oil',(.5,99.5),(33.5,125.5)),
        ('crude-oil',(137.5,119.5),(75.5,125.5)),
        ('petroleum-gas',(138.5,111.5),(78.5,127.5))]:
        router.route(start,end,fluid)
    bp['label']='Bootstrap — all six sciences, red belts'
    bp['description']='Integrated 160x128 bootstrap. One placement anchor for all six science chains and the construction/defense bay. All belts, splitters and underground belts are red; routing never depends on different belt tiers. Keep red belts through launch; blue is optional later. 5/6/5/12/7/7 science assemblers. See README.md for phases, external plate imports and commissioning.'
    return small_power(bp,create,power_wires)


def furnace_bank(root, create, power_wires, aligned, rows=4, belt_tier='red'):
    """User's 6x8 electric tile: six copies per row, no module dependency."""
    source=json.loads((root/'brians-bootstrap/source/user-smelting/electric-furnace-tile.json').read_text())['blueprint']
    es=[]
    for row in range(rows):
        for column in range(6):
            for old in source['entities']:
                entity=copy.deepcopy(old)
                entity.pop('entity_number',None);entity.pop('items',None)
                if entity['name']=='bulk-inserter':entity['name']='fast-inserter'
                if entity['name']=='turbo-underground-belt':entity['name']=BELTS[belt_tier][1]
                entity['position']['x']+=6*column
                entity['position']['y']+=8*row+2
                # Close the outer edges with ordinary belts. The interior
                # tunnels span five tiles and remain valid at yellow/red/blue.
                x,y=old['position']['x'],old['position']['y']
                if entity['name']==BELTS[belt_tier][1] and (
                        (column==0 and (x,y) in {(4.5,.5),(.5,4.5)}) or
                        (column==5 and (x,y) in {(5.5,.5),(1.5,4.5)})):
                    entity['name']=BELTS[belt_tier][0];entity.pop('type',None)
                es.append(entity)
        y=8*row+2.5
        # One descending red input manifold serves all four short rows.
        es.append(create(BELTS[belt_tier][2],39,y,direction=8))
        es.extend([create(BELTS[belt_tier][0],38.5,y+1,direction=12),
                   create(BELTS[belt_tier][0],37.5,y+1,direction=12),
                   create(BELTS[belt_tier][0],36.5,y+1,direction=0),
                   create(BELTS[belt_tier][0],36.5,y,direction=12)])
    for y in range(rows*8):
        if y not in {2+8*j for j in range(rows)}:
            es.append(create(BELTS[belt_tier][0],39.5,y+.5,direction=8))
    return aligned(power_wires({'item':'blueprint','version':source['version'],
        'label':f'User electric-furnace stack — {rows*12}, {belt_tier}',
        'icons':[{'index':1,'signal':{'name':'electric-furnace'}}],
        'description':f'64x32 reservation; actual belt-and-furnace footprint 40x{rows*8}. '
            f'{rows*12} furnaces based on the supplied 6x8 repeating electric tile. '
            'No modules or mixed belt tiers. Input (39.5,0.5), southbound. '
            'Four westbound row outputs at (0.5,6.5+8*n); two for the brick bank. '
            'Keep these separate or merge with splitters without overloading one lane.',
        'entities':es}))


def small_power(bp, create, power_wires):
    """A pole plan that works before medium poles, with no moved later poles."""
    es=bp['entities'];control=[w for w in bp.get('wires',[]) if w[1]!=5]
    es[:]=[t for t in es if 'electric-pole' not in t['name']]
    occupied=set().union(*(footprint(t) for t in es))
    consumers=[t for t in es if t['name'] in {'assembling-machine-1','assembling-machine-2',
        'assembling-machine-3','chemical-plant','oil-refinery','lab','electric-furnace',
        'inserter','fast-inserter','bulk-inserter','long-handed-inserter','pump'}]
    candidates={}
    for i,entity in enumerate(consumers):
        for x,y in footprint(entity):
            for xx in range(max(0,x-2),min(160,x+3)):
                for yy in range(max(0,y-2),min(128,y+3)):
                    if (xx,yy) not in occupied:
                        candidates.setdefault((xx,yy),set()).add(i)
    uncovered=set(range(len(consumers)))
    heap=[(-len(v),p) for p,v in candidates.items()];heapq.heapify(heap)
    selected={(1,1)}
    while uncovered:
        if not heap:break
        score,p=heapq.heappop(heap);covers=candidates[p]&uncovered
        if not covers:continue
        if len(covers)<-score:
            heapq.heappush(heap,(-len(covers),p));continue
        selected.add(p);uncovered-=covers
    medium=set()
    for i in sorted(uncovered):
        choices=[]
        for x,y in footprint(consumers[i]):
            for xx in range(max(0,x-3),min(160,x+4)):
                for yy in range(max(0,y-3),min(128,y+4)):
                    if (xx,yy) not in occupied:
                        covers={j for j in uncovered if any(abs(px-xx)<=3 and abs(py-yy)<=3 for px,py in footprint(consumers[j]))}
                        choices.append((-len(covers),(xx,yy),covers))
        if i not in uncovered:continue
        if not choices:raise ValueError('No pole position even with medium poles')
        _,p,covers=min(choices,key=lambda v:(v[0],v[1]))
        medium.add(p);selected.add(p);uncovered-=covers
    # Wires may cross buildings; only the poles themselves need free cells.
    while True:
        points=sorted(selected);parents=list(range(len(points)))
        def root(i):
            while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
            return i
        for i,a in enumerate(points):
            for j,b in enumerate(points[:i]):
                if math.dist(a,b)<=7.5:parents[root(i)]=root(j)
        if len({root(i) for i in range(len(points))})==1:break
        _,a,b=min((math.dist(a,b),a,b) for i,a in enumerate(points)
                  for j,b in enumerate(points[:i]) if root(i)!=root(j))
        distance=math.dist(a,b)
        ideal=(a[0]+(b[0]-a[0])*min(6,distance/2)/distance,
               a[1]+(b[1]-a[1])*min(6,distance/2)/distance)
        choices=[(math.dist(p,ideal)+math.dist(p,b)*.05,p)
                 for x in range(max(0,a[0]-7),min(160,a[0]+8))
                 for y in range(max(0,a[1]-7),min(128,a[1]+8))
                 if (p:=(x,y)) not in occupied|selected and math.dist(a,p)<=7.5
                 and math.dist(p,b)<distance]
        if not choices:raise ValueError(f'Cannot bridge poles {a}, {b}')
        selected.add(min(choices)[1])
    es.extend(create('medium-electric-pole' if (x,y) in medium else 'small-electric-pole',x+.5,y+.5) for x,y in sorted(selected))
    power_wires(bp);bp['wires'].extend(control)
    return bp


def transport_graph(entities):
    owners={p:i for i,t in enumerate(entities) for p in footprint(t)}
    forward={i:set() for i in range(len(entities))}
    def add(i,p):
        j=owners.get(p)
        if j is not None and j!=i and ('belt' in entities[j]['name'] or 'splitter' in entities[j]['name']):forward[i].add(j)
    endpoints={(math.floor(t['position']['x']),math.floor(t['position']['y'])):i
               for i,t in enumerate(entities) if 'underground-belt' in t['name']}
    for i,t in enumerate(entities):
        name=t['name'];x,y=map(math.floor,(t['position']['x'],t['position']['y']))
        d=t.get('direction',0);dx,dy=DIRECTIONS.get(d,(0,0))
        if 'underground-belt' in name and t.get('type')=='input':
            for distance in range(1,{'underground-belt':5,'fast-underground-belt':7,'express-underground-belt':9}.get(name,5)+1):
                j=endpoints.get((x+distance*dx,y+distance*dy))
                if j is not None and entities[j].get('type')=='output' and entities[j].get('direction',0)==d:
                    forward[i].add(j);break
        elif 'belt' in name: add(i,(x+dx,y+dy))
        elif 'splitter' in name:
            for xx,yy in footprint(t):add(i,(xx+dx,yy+dy))
        elif 'inserter' in name:
            reach=2 if name=='long-handed-inserter' else 1
            pickup=owners.get((x+dx*reach,y+dy*reach))
            if pickup is not None and pickup!=i:forward[pickup].add(i)
            drop=owners.get((x-dx*reach,y-dy*reach))
            if drop is not None and drop!=i:forward[i].add(drop)
    reverse={i:set() for i in forward}
    for i,targets in forward.items():
        for j in targets:reverse[j].add(i)
    return forward,reverse


def phases(full, root, create, power_wires):
    """Select connected production chains, all at their final positions."""
    entities=full['entities'];forward,reverse=transport_graph(entities)
    recipes=json.loads((root/'brians-bootstrap/source/recipe-dependencies.json').read_text())
    # A small checked-in recipe dependency snapshot replaces runtime game data
    # when building the book on a machine without Factorio installed.
    # Caller writes/ships this snapshot before distributing the generator.
    output=[]
    for stage,sciences in [(2,{'automation'}),(3,{'automation','logistic','military'}),
            (4,{'automation','logistic','military','chemical'}),
            (5,{'automation','logistic','military','chemical'}),
            (6,{'automation','logistic','military','chemical','production','utility'})]:
        needed={s+'-science-pack' for s in sciences}
        while True:
            new=set(needed)
            for name in needed:
                for ingredient in recipes.get(name,{}).get('ingredients',[]):
                    if ingredient['name'] in recipes:new.add(ingredient['name'])
            if new==needed:break
            needed=new
        excluded=set()
        for recipe,cap in [('electronic-circuit',2 if stage==3 else 4),('advanced-circuit',12)]:
            if stage>=6: continue
            choices=sorted((i for i,t in enumerate(entities) if t.get('recipe')==recipe),key=lambda i:(entities[i]['position']['y'],entities[i]['position']['x']))
            excluded.update(choices[cap:])
        active={i for i,t in enumerate(entities) if t.get('recipe') in {s+'-science-pack' for s in sciences}}
        # Trace the actual transport graph, not rectangular crops: this keeps
        # both ends of every tunnel and the producers feeding the selected rows.
        stack=list(active)
        while stack:
            i=stack.pop()
            for j in reverse[i]:
                t=entities[j]
                if j in excluded:continue
                if t.get('recipe') and t['recipe'] not in needed:continue
                if j not in active:active.add(j);stack.append(j)
        stack=[i for i in active if entities[i].get('recipe','').endswith('-science-pack')]
        while stack:
            i=stack.pop()
            for j in forward[i]:
                if entities[j].get('recipe') or entities[j]['name']=='lab':
                    active.add(j);continue
                if j not in active:active.add(j);stack.append(j)
        # The construction bay is present from green onward. It is explicitly
        # batch-fed, with no hidden logistics-system prerequisite.
        if stage>=3:
            active|={i for i,t in enumerate(entities) if t.get('_construction_bay')}
        if stage>=4:
            active|={i for i,t in enumerate(entities) if t['name'] in {'pipe','pipe-to-ground','pump','storage-tank','chemical-plant','oil-refinery'}}
        if stage==4: active-={i for i,t in enumerate(entities) if t.get('recipe') in {'light-oil-cracking','heavy-oil-cracking','lubricant'}}
        if stage<5: active|={i for i,t in enumerate(entities) if t.get('_starter_only')}
        else: active-={i for i,t in enumerate(entities) if t.get('_starter_only')}
        if stage==6:active={i for i,t in enumerate(entities) if not t.get('_starter_only')}
        # Include both ends even where an inserter taps a tunnel's entrance.
        endpoints={(t['position']['x'],t['position']['y']):i for i,t in enumerate(entities) if 'underground-belt' in t['name']}
        for i,t in enumerate(entities):
            if 'underground-belt' not in t['name'] or t.get('type')!='input':continue
            x,y=t['position']['x'],t['position']['y'];dx,dy=DIRECTIONS[t.get('direction',0)]
            for distance in range(1,6):
                j=endpoints.get((x+dx*distance,y+dy*distance))
                if j is not None and entities[j].get('type')=='output' and entities[j].get('direction',0)==t.get('direction',0):
                    if i in active or j in active:active|={i,j}
                    break
        # Prune the full pole tree to the consumers in this phase. Pole
        # positions remain fixed; later phases only add/upgrade entities.
        min_x=min(t['position']['x'] for t in entities);min_y=min(t['position']['y'] for t in entities)
        ref_to_i={f"{t['position']['x']-min_x:g},{t['position']['y']-min_y:g}":i for i,t in enumerate(entities)}
        pole_neighbors={i:set() for i,t in enumerate(entities) if 'electric-pole' in t['name']}
        for a,ac,b,bc in full.get('wires',[]):
            if ac==bc==5:
                ai,bi=ref_to_i[a],ref_to_i[b];pole_neighbors[ai].add(bi);pole_neighbors[bi].add(ai)
        consumers={i for i in active if entities[i]['name'] not in {'pipe','pipe-to-ground'} and
                   ('inserter' in entities[i]['name'] or entities[i]['name'] in {'assembling-machine-2','lab','oil-refinery','chemical-plant','pump'})}
        required=set()
        for i in consumers:
            cells=footprint(entities[i])
            for p in pole_neighbors:
                x,y=map(math.floor,entities[p]['position'].values())
                if any(abs(xx-x)<=(3 if entities[p]['name']=='medium-electric-pole' else 2) and abs(yy-y)<=(3 if entities[p]['name']=='medium-electric-pole' else 2) for xx,yy in cells):required.add(p);break
        inlet=next(i for i in pole_neighbors if entities[i]['position']=={'x':1.5,'y':1.5})
        required.add(inlet)
        keep=set(pole_neighbors);degrees={i:len(v) for i,v in pole_neighbors.items()}
        leaves=[i for i in keep if degrees[i]<=1 and i not in required]
        while leaves:
            i=leaves.pop()
            if i not in keep:continue
            keep.remove(i)
            for j in pole_neighbors[i]&keep:
                degrees[j]-=1
                if degrees[j]<=1 and j not in required:leaves.append(j)
        active|=keep
        bp=copy.deepcopy(full);bp['entities']=[copy.deepcopy(t) for i,t in enumerate(entities) if i in active]
        # Keep original minimum coordinates so coordinate wire references do
        # not drift when a phase omits a northern/western belt.
        phase_min_x=min(t['position']['x'] for t in bp['entities']);phase_min_y=min(t['position']['y'] for t in bp['entities'])
        def ref(i):return f"{entities[i]['position']['x']-phase_min_x:g},{entities[i]['position']['y']-phase_min_y:g}"
        bp['wires']=[[ref(ref_to_i[a]),ac,ref(ref_to_i[b]),bc] for a,ac,b,bc in full.get('wires',[])
                     if ref_to_i[a] in active and ref_to_i[b] in active]
        bp=tier(bp,'yellow' if stage<=5 else 'red')
        for t in bp['entities']:
            t.pop('_starter_only',None)
            t.pop('_construction_bay',None)
            if stage==2 and t['name']=='medium-electric-pole':t['name']='small-electric-pole'
            if stage<5 and t['name'] in {'fast-inserter','bulk-inserter'}:t['name']='inserter'
            elif stage>=5 and t['name']=='inserter':t['name']='fast-inserter'
            if stage<5 and t['name']=='assembling-machine-2':t['name']='assembling-machine-1'
            elif stage>=5 and t['name']=='assembling-machine-1':t['name']='assembling-machine-2'
            if stage==4 and t.get('recipe')=='advanced-oil-processing':t['recipe']='basic-oil-processing'
        bp['label']=f'Phase {stage} — '+{2:'Automation',3:'Green and military',4:'Basic oil and blue science',5:'Launch research — assembler 2s and advanced oil',6:'Postlaunch — all six Nauvis sciences'}[stage]
        bp['description']='Same 160x128 anchor. Phase 5: upgrade assemblers/inserters, keep yellow belts and launch using the first-launch sub-book. Phase 6: after launch, apply yellow-to-red belt planner and add purple/yellow chains. Phase 7: optional blue belts. No separate science campus. See LAUNCH.md and setup/retirement instructions.'
        output.append((stage,bp))
    blue=tier(output[-1][1],'blue');blue['label']='Phase 7 — Optional postlaunch blue belts'
    output.append((7,blue))
    return output


def unweave(bp):
    bp=copy.deepcopy(bp);es=bp['entities'];matched=set()
    by_position={(t['position']['x'],t['position']['y']):i for i,t in enumerate(es)
                 if 'underground-belt' in t['name']}
    for i,t in enumerate(es):
        if 'underground-belt' not in t['name'] or t.get('type')!='input': continue
        x,y=t['position']['x'],t['position']['y'];d=t.get('direction',0);dx,dy=DIRECTIONS[d]
        for distance in range(1,6):
            j=by_position.get((x+dx*distance,y+dy*distance))
            if j is None: continue
            other=es[j]
            if other['name']==t['name'] and other.get('type')=='output' and other.get('direction',0)==d:
                matched|={i,j};break
    for i,t in enumerate(es):
        if 'underground-belt' in t['name'] and i not in matched:
            t['name']=next(values[0] for values in BELTS.values() if values[1]==t['name'])
            t.pop('type',None)
    return bp
