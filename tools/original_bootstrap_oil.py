"""Controlled cracking connected to the original refinery's actual networks."""
import json
import math
from compact_bootstrap import FluidRouter


def balance(bp,root,create,power_wires):
    snapshot=json.loads((root/'brians-bootstrap/original-rework/original-fluid-topology.json').read_text())
    segment_names={1:'crude-oil',2:'crude-oil',6:'water',10:'petroleum-gas',11:'heavy-oil',12:'light-oil'}
    labels={}
    for node in snapshot['nodes']:
        if node['name'] in {'pipe','pipe-to-ground','storage-tank'}:
            segment=node['storages'][0].get('segment')
            labels[(math.floor(node['position']['x']),math.floor(node['position']['y']))]=segment_names.get(segment,'network-'+str(segment))
    es=bp['entities']
    original_min=(min(e['position']['x'] for e in es),min(e['position']['y'] for e in es))
    original_pipes={(math.floor(e['position']['x']),math.floor(e['position']['y'])) for e in es if e['name']=='pipe'}
    poles=[(72.5,y) for y in (52.5,60.5,68.5,76.5)]+[(x,76.5) for x in (64.5,56.5,48.5,40.5,32.5)]
    for x,y in poles:es.append(create('medium-electric-pole',x,y))
    for recipe,x,signal,threshold in [('heavy-oil-cracking',32.5,'heavy-oil',1000),('light-oil-cracking',48.5,'light-oil',1500)]:
        es.append(create('chemical-plant',x,80.5,recipe=recipe,control_behavior={'circuit_enabled':True,'circuit_read_contents':False,'circuit_read_ingredients':False,'circuit_condition':{'comparator':'>','constant':threshold,'first_signal':{'name':signal,'type':'fluid'}}}))
    # The original plastic plant was supplied only by the basic refinery.
    # Free its second petroleum inlet and connect it to the balanced network.
    plastic_output=next(e for e in es if e['name'] in {'inserter','fast-inserter'} and e['position']=={'x':54.5,'y':4.5})
    plastic_output['position']['y']=5.5
    old_pole=next(e for e in es if 'electric-pole' in e['name'] and e['position']=={'x':54.5,'y':5.5})
    old_pole['name']='medium-electric-pole';old_pole['position']={'x':56.5,'y':4.5}
    for name,x,d in [('pipe-to-ground',54.5,12),('pipe-to-ground',60.5,4)]:
        es.append(create(name,x,4.5,direction=d));labels[(math.floor(x),4)]='petroleum-gas'
    # Move the basic refinery enough to expose a real pipe connection between
    # its output and both petroleum consumers; consumer fluidboxes do not
    # transmit petroleum backwards to the shared network.
    basic=next(e for e in es if e.get('recipe')=='basic-oil-processing')
    basic['position']['x']+=8
    es.extend([create('medium-electric-pole',62.5,2.5),create('medium-electric-pole',68.5,5.5),
               create('pipe-to-ground',54.5,6.5,direction=12),create('pipe-to-ground',60.5,6.5,direction=4),
               create('pipe',61.5,6.5),create('pipe',61.5,5.5)])
    for point in [(54,6),(60,6),(61,6),(61,5)]:labels[point]='petroleum-gas'
    targets=[('crude-oil',(67.5,7.5)),('petroleum-gas',(61.5,4.5)),('water',(31.5,78.5)),('heavy-oil',(33.5,78.5)),('light-oil',(31.5,82.5)),
             ('water',(47.5,78.5)),('light-oil',(49.5,78.5)),('petroleum-gas',(47.5,82.5))]
    connected={}
    for e in es:
        if e['name']=='pipe':
            p=(math.floor(e['position']['x']),math.floor(e['position']['y']))
            if p in original_pipes:connected.setdefault(labels.get(p,'other'),set()).add(p)
    for fluid,(x,y) in targets:
        es.append(create('pipe',x,y));labels[(math.floor(x),math.floor(y))]=fluid
    router=FluidRouter(es,labels,create,bounds=(96,96))
    ordinary={(math.floor(e['position']['x']),math.floor(e['position']['y'])) for e in es if e['name']=='pipe'}
    for fluid,target in targets:
        goal=tuple(map(math.floor,target))
        candidates=sorted((p for p in connected.get(fluid,set()) if p!=goal),key=lambda p:abs(p[0]-goal[0])+abs(p[1]-goal[1]))
        for point in candidates:
            try:
                placed=router.route((point[0]+.5,point[1]+.5),target,fluid)
                ordinary.update(p for p,(name,_) in placed.items() if name=='pipe')
                connected.setdefault(fluid,set()).update(p for p,(name,_) in placed.items() if name=='pipe')
                break
            except ValueError:continue
        else:raise ValueError('No accessible '+fluid+' branch for '+str(target))
    old=[w for w in bp.get('wires',[]) if w[1]!=5]
    power_wires(bp)
    minx=min(e['position']['x'] for e in es);miny=min(e['position']['y'] for e in es)
    def rebase(value):
        x,y=map(float,value.split(','));return f'{x+original_min[0]-minx:g},{y+original_min[1]-miny:g}'
    old=[[rebase(a),ac,rebase(b),bc] for a,ac,b,bc in old]
    def ref(x,y):return f'{x-minx:g},{y-miny:g}'
    green=[[a,2,b,2] for a,_,b,_ in bp['wires']]
    green.extend([[ref(36.5,53.5),2,ref(34.5,50.5),2],
                  [ref(38.5,56.5),2,ref(34.5,50.5),2],
                  [ref(32.5,80.5),2,ref(32.5,76.5),2],
                  [ref(48.5,80.5),2,ref(48.5,76.5),2]])
    bp['wires'].extend(old+green)
    return bp
