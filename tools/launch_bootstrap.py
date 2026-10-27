"""Finite first-launch workshop, built before the six-science expansion."""
import json

# IDs remain stable so the checklist and native courier fixture share ports.
CELLS = [
    ('processing-unit', 140), ('processing-unit', 140),
    ('electric-engine-unit', 100), ('electric-engine-unit', 100),
    ('low-density-structure', 50), ('concrete', 1200),
    ('solid-fuel-from-light-oil', 500), ('rocket-fuel', 50),
    ('copper-cable', 1200), ('space-platform-foundation', 60),
    ('space-platform-starter-pack', 1), ('rocket-silo', 1),
    ('cargo-landing-pad', 1),
]


def build(root, create, power_wires, aligned, version):
    recipes = json.loads((root/'brians-bootstrap/source/launch-recipes.json').read_text())
    es, cells = [], []
    for i, (recipe, target) in enumerate(CELLS):
        x, y = 4.5 + (i % 4)*8, 4.5 + (i // 4)*8
        machine = 'chemical-plant' if recipe.startswith('solid-fuel-') else 'assembling-machine-2'
        es.extend([create(machine,x,y,recipe=recipe,direction=4),
                   create('steel-chest',x,y-3),create('fast-inserter',x,y-2,direction=0),
                   create('steel-chest',x,y+3),create('fast-inserter',x,y+2,direction=0)])
        fluid = next((a for a in recipes[recipe]['ingredients'] if a['type']=='fluid'), None)
        port = None
        if fluid:
            fy = y-1 if machine=='chemical-plant' else y
            es.extend([create('pipe',x+2,fy), create('pipe',x+3,fy)])
            port = {'x':x+3,'y':fy,'fluid':fluid['name']}
        product = recipes[recipe]['products'][0]
        crafts = target // product['amount']
        assert crafts * product['amount'] == target
        cells.append({'id':i,'recipe':recipe,'product':product['name'],'target':target,
                      'machine':{'x':x,'y':y},'input':{'x':x,'y':y-3},
                      'output':{'x':x,'y':y+3},'fluid_port':port,
                      'ingredients':[{**a,'amount':a['amount']*crafts} for a in recipes[recipe]['ingredients']]})
    # Each medium pole covers its assembler and both inserters. Eight-tile
    # spacing joins the compact four-column grid without bridging poles.
    for i in range(len(CELLS)):
        es.append(create('medium-electric-pole',2.5+8*(i%4),4.5+8*(i//4)))
    bp=aligned(power_wires({'item':'blueprint','version':version,
        'label':'Phase 5b — First-launch batch workshop (32x32)',
        'description':'Separate one-chunk annex. Finite batches; north steel chests take ingredients, south chests collect output. Transfer intermediates between cells manually. Seven east pipe ports: acid at (7.5,4.5)/(15.5,4.5), lubricant (23.5,4.5)/(31.5,4.5), plus water (15.5,12.5) and light oil (23.5,11.5)/(31.5,12.5). See LAUNCH.md for exact batches, unlock order and launch procedure. No purple/yellow science, modules, bots or blue belts needed. Power inlet (2.5,4.5).',
        'entities':es}))
    # A reusable manual-load pad: put exactly 50 of each rocket ingredient in
    # the west chest. Starter pack goes directly in rocket cargo via silo UI.
    pad=aligned(power_wires({'item':'blueprint','version':version,
        'label':'Phase 5c — First rocket and landing pad (32x32)',
        'description':'Build only after crafting the silo and landing pad. West chest (4.5,10.5): 50 processing units, 50 low-density structures, 50 rocket fuel. Inserter feeds silo. Put one starter pack into rocket cargo, select New platform, name it and launch. External power inlet (4.5,8.5). Reserve rocket clearance; later use this pad for repeated launches.',
        'entities':[create('rocket-silo',10.5,10.5,recipe='rocket-part'),
            create('steel-chest',4.5,10.5),create('fast-inserter',5.5,10.5,direction=12),
            create('medium-electric-pole',4.5,8.5),create('cargo-landing-pad',26,26)]}))
    produced={c['product'] for c in cells}
    raw={}
    fluids={}
    for c in cells:
        for a in c['ingredients']:
            if a['type']=='fluid':fluids[a['name']]=fluids.get(a['name'],0)+a['amount']
            elif a['name'] not in produced:raw[a['name']]=raw.get(a['name'],0)+a['amount']
    plan={'power_inlet':{'x':2.5,'y':4.5},'cells':cells,'external_items':raw,'fluid_consumption':fluids,
          'rocket_load':{'processing-unit':50,'low-density-structure':50,'rocket-fuel':50},
          'cargo':{'space-platform-starter-pack':1},
          'note':'Finite recipe consumption; fluids need additional pipe fill. Workshop construction, external power/oil/smelting and science inputs are extra.'}
    return bp,pad,plan


def research_annex(create, power_wires, aligned, version):
    es=[]
    for row in range(6):
        for col in range(6):
            x,y=4.5+5*col,4.5+5*row
            es.extend([create('lab',x,y),create('wooden-chest',x,y-3),
                       create('fast-inserter',x,y-2,direction=0),
                       create('medium-electric-pole',x+2,y)])
    return aligned(power_wires({'item':'blueprint','version':version,
        'label':'First launch — 36-lab research annex (32x32)',
        'description':'One separate chunk. Each lab takes science from its north wooden chest via a fast inserter. For silo research put 28 automation, 28 logistic and 28 chemical packs in EACH of the 36 chests (1008 of each total). Supplies at least 36 research units/min for a 60s technology without research-speed bonuses; about 28 minutes plus loading. Existing nine labs can help, for 45 total. Power inlet (6.5,4.5); 2.16 MW active lab demand plus inserters. Select Rocket Silo after prerequisites. Reuse after launch or remove when belt-fed labs expand.',
        'entities':es}))
