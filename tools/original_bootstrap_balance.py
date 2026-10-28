"""Recipe demand calculation for the original-layout extension.

Normal quality, no productivity, 45 science/min; mall reserves are additional.
"""
import json
import math
from collections import defaultdict
from pathlib import Path

SCIENCES={'automation':5,'logistic':6,'military':5,'chemical':12,'production':7,'utility':7}
RAW={'iron-plate','copper-plate','steel-plate','stone-brick','stone','coal','water','crude-oil','petroleum-gas','light-oil','heavy-oil'}


def calculate(recipes):
    flows=defaultdict(float)
    def demand(name,rate,ancestors=()):
        flows[name]+=rate
        if name in RAW:return
        if name in ancestors:raise ValueError('Cyclic production dependency: '+name)
        recipe=recipes[name]
        product=next(p for p in recipe['products'] if p['name']==name)
        crafts=rate/product.get('amount',1)
        for ingredient in recipe['ingredients']:
            demand(ingredient['name'],crafts*ingredient['amount'],ancestors+(name,))
    for science in SCIENCES:demand(science+'-science-pack',45/60)
    result={}
    for name,rate in sorted(flows.items()):
        row={'items_per_second':round(rate,8),'items_per_minute':round(rate*60,8)}
        if name not in RAW:
            r=recipes[name];amount=next(p['amount'] for p in r['products'] if p['name']==name)
            speed=1 if name in {'plastic-bar','sulfur','battery','explosives','lubricant','sulfuric-acid'} else .75
            row['machines_at_nominal_speed']=round(rate*r['energy']/amount/speed,8)
            row['minimum_whole_machines']=math.ceil(row['machines_at_nominal_speed']-1e-8)
            row['crafting_speed_used']=speed
        result[name]=row
    return {'target_science_per_minute':45,'normal_quality':True,'productivity':0,
        'boundary':'Imports plates, steel, brick, coal, stone and named fluids; acid/lubricant crafting included; crude refining and oil balancing sized separately. Mall production is additional.',
        'production':result}


def main():
    root=Path(__file__).resolve().parents[1]
    snapshot=root/'brians-bootstrap/original-rework/recipe-demand-source.json'
    game_data=root.parent/'factorio/script-output/bootstrap-prototypes.json'
    # Refresh from installed official data when available; checked-in snapshot
    # supports machines without a Factorio installation.
    data=json.loads(game_data.read_text())['recipes'] if game_data.exists() else json.loads(snapshot.read_text())
    report=calculate(data)
    destination=root/'brians-bootstrap/original-rework'
    (destination/'science-demand.json').write_text(json.dumps(report,indent=2)+'\n')
    # Ship only the recipes used by this calculation, so rebuilding the report
    # does not depend on a local game installation or an unversioned dump.
    used={n:data[n] for n in report['production'] if n not in RAW}
    (destination/'recipe-demand-source.json').write_text(json.dumps(used,indent=2)+'\n')
    print('Calculated complete six-science demand, excluding finite mall stockpiles.')


if __name__=='__main__':main()
