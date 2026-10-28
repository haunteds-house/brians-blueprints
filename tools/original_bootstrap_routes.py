"""Physical routing fixes to the original bootstrap, without moving its mall."""
import heapq
import math
from compact_bootstrap import footprint, DIRECTIONS


def belt_route(bp,start,goal,goal_direction=12,initial_direction=-1,bounds=(0,0,96,96)):
    entities=bp['entities']
    occupied=set().union(*(footprint(e) for e in entities))
    existing={(math.floor(e['position']['x']),math.floor(e['position']['y'])):e for e in entities}
    tunnels=[]
    for p,e in existing.items():
        if 'underground-belt' not in e['name'] or e.get('type')!='input':continue
        dx,dy=DIRECTIONS[e.get('direction',0)]
        for distance in range(1,8):
            q=p[0]+dx*distance,p[1]+dy*distance;o=existing.get(q,{})
            if o.get('name')==e['name'] and o.get('type')=='output' and o.get('direction',0)==e.get('direction',0):tunnels.append((p,q));break
    def free(p):
        if not (bounds[0]<=p[0]<bounds[2] and bounds[1]<=p[1]<bounds[3]) or p in occupied:return False
        if p==goal:return True
        for d,(dx,dy) in DIRECTIONS.items():
            e=existing.get((p[0]-dx,p[1]-dy),{})
            if 'transport-belt' in e.get('name','') and e.get('direction',0)==d:return False
        return True
    def clear(a,b):
        for c,d in tunnels:
            if a[0]==b[0]==c[0]==d[0] and max(min(a[1],b[1]),min(c[1],d[1]))<min(max(a[1],b[1]),max(c[1],d[1])):return False
            if a[1]==b[1]==c[1]==d[1] and max(min(a[0],b[0]),min(c[0],d[0]))<min(max(a[0],b[0]),max(c[0],d[0])):return False
        return True
    initial=(start,initial_direction)
    queue=[(0,initial)];cost={initial:0};prev={};finished=None
    while queue:
        _,state=heapq.heappop(queue);p,incoming=state
        if p==goal:finished=state;break
        used=set();ancestor=state
        while ancestor in prev:
            ancestor,action=prev[ancestor]
            used.add(action[1])
            if action[0]=='tunnel':used.add(action[2])
        for direction,(dx,dy) in DIRECTIONS.items():
            options=[(1,(p[0]+dx,p[1]+dy),('surface',p,direction))]
            if incoming==direction:
                for length in range(2,6):
                    out=(p[0]+dx*length,p[1]+dy*length);n=(out[0]+dx,out[1]+dy)
                    if out not in used and free(out) and clear(p,out):options.append((length+4,n,('tunnel',p,out,direction)))
            for step,n,action in options:
                if n in used or not free(n):continue
                next_state=(n,direction);value=cost[state]+step
                if value>=cost.get(next_state,float('inf')):continue
                cost[next_state]=value;prev[next_state]=(state,action)
                heapq.heappush(queue,(value+abs(n[0]-goal[0])+abs(n[1]-goal[1]),next_state))
    if finished is None:raise ValueError(f'No belt route: {start} -> {goal}')
    actions=[];state=finished
    while state!=initial:state,action=prev[state];actions.append(action)
    actions.reverse();placed={}
    def put(p,name,direction,kind=None):
        if p in placed:raise ValueError('Route crosses itself')
        e={'name':name,'position':{'x':p[0]+.5,'y':p[1]+.5},'direction':direction}
        if kind:e['type']=kind
        placed[p]=e
    for action in actions:
        if action[0]=='surface':put(action[1],'transport-belt',action[2])
        else:
            _,a,b,d=action;put(a,'underground-belt',d,'input');put(b,'underground-belt',d,'output')
    put(goal,'transport-belt',goal_direction)
    entities.extend(placed.values())
    return len(placed)


def automate_green(bp):
    # Both phases share a science-input chest. Phase 4's local inserter
    # assembler already supplies it through the dedicated science belt.
    es=bp['entities']
    if any(e.get('recipe')=='inserter' and e['position']=={'x':16.5,'y':42.5} for e in es):return 0
    es[:]=[e for e in es if not (e['name']=='constant-combinator' and e['position']=={'x':14.5,'y':44.5})]
    count=belt_route(bp,(37,22),(15,44))
    es.extend([{'name':'inserter','direction':0,'position':{'x':37.5,'y':21.5}},
               {'name':'inserter','direction':4,'position':{'x':14.5,'y':44.5}}])
    return count

