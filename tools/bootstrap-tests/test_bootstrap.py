"""Blueprint contracts; throughput is checked independently by the real engine."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
from fatul import Processor, read_files
from compact_bootstrap import BELTS, DIRECTIONS, footprint, tier

spec = importlib.util.spec_from_file_location('bootstrap', TOOLS / 'build-bootstrap.py')
bootstrap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap)
BOOK = TOOLS.parent / 'brians-bootstrap/book'


def get(name):
    return json.loads((BOOK / name).read_text())['blueprint']


def tunnels(bp):
    es = bp['entities']
    endpoints = {(e['position']['x'], e['position']['y']):e for e in es
                 if 'underground-belt' in e['name']}
    pairs = set()
    for p,e in endpoints.items():
        if e.get('type') != 'input': continue
        d=e.get('direction',0);dx,dy=DIRECTIONS[d]
        for distance in range(1,10):
            q=(p[0]+dx*distance,p[1]+dy*distance)
            other=endpoints.get(q)
            if other and other['name']==e['name'] and other.get('type')=='output' and other.get('direction',0)==d:
                pairs.add((p,q));break
    return endpoints,pairs


class BootstrapBook(unittest.TestCase):
    def test_book_round_trip_and_reference_integrity(self):
        data = read_files(BOOK, False)
        packed = Processor(False).encode(copy.deepcopy(data))
        result = Processor(False, ids_mode='keep').decode(packed)
        self.assertEqual(result['blueprint_book']['label'], data['blueprint_book']['label'])

    def test_book_indices_are_unique(self):
        def check(value):
            entries=value.get('blueprint_book',{}).get('blueprints',[])
            indices=[e['index'] for e in entries]
            self.assertEqual(len(indices),len(set(indices)))
            for entry in entries:check(entry)
        check(read_files(BOOK,False))

    def test_science_capacity_uses_actual_21_second_recipes(self):
        recipes=bootstrap.read('brians-bootstrap/source/science-recipes.json')
        for name,count in bootstrap.SCIENCE.items():
            recipe=recipes[name+'-science-pack']
            self.assertAlmostEqual(count*.75*60*recipe['amount']/recipe['energy'],45)
            self.assertEqual(67200 % int(recipe['energy']*60/.75),0)
            self.assertAlmostEqual(count*.5*60*recipe['amount']/recipe['energy'],30)

    def test_blue_upgrade_changes_only_the_belt_tier(self):
        red=get('phase-6.json');blue=get('phase-7.json')
        self.assertEqual(tier(red,'blue')['entities'],blue['entities'])
        self.assertEqual(red['wires'],blue['wires'])

    def test_all_sciences_share_bootstrap_and_machine_ratio(self):
        bp=get('phase-6.json')
        for name,count in bootstrap.SCIENCE.items():
            machines=[e for e in bp['entities'] if e.get('recipe')==name+'-science-pack']
            self.assertEqual(len(machines),count,name)
            self.assertTrue(all(e['name']=='assembling-machine-2' for e in machines))
        self.assertFalse((BOOK/'phase-7-science-campus.json').exists())
        self.assertFalse((BOOK/'phase-8-infrastructure-mall.json').exists())
        self.assertTrue({'solar-panel','gun-turret','repair-pack','transport-belt'} <=
                        {e.get('recipe') for e in bp['entities']})

    def test_uniform_belt_tiers_in_every_export(self):
        for path in BOOK.rglob('*.json'):
            bp=json.loads(path.read_text()).get('blueprint',{})
            names={e['name'] for e in bp.get('entities',[])}
            present={name for name,values in BELTS.items() if names&set(values)}
            self.assertLessEqual(len(present),1,str(path))
        for stage in range(2,8):
            expected='yellow' if stage<=5 else 'red' if stage<7 else 'blue'
            names={e['name'] for e in get(f'phase-{stage}.json')['entities']}
            self.assertTrue(names&set(BELTS[expected]))

    def test_tunnels_are_paired_short_and_upgrade_without_reconnection(self):
        for stage in range(2,8):
            bp=get(f'phase-{stage}.json');ends,pairs=tunnels(bp)
            paired={p for pair in pairs for p in pair}
            self.assertEqual(set(ends),paired,f'Unpaired tunnel in phase {stage}')
            self.assertTrue(all(abs(a[0]-b[0])+abs(a[1]-b[1])<=5 for a,b in pairs))
            for color in BELTS:
                self.assertEqual(tunnels(tier(bp,color))[1],pairs,f'{stage}/{color}')
            intervals=list(pairs)
            for i,(a,b) in enumerate(intervals):
                for c,d in intervals[:i]:
                    if a[0]==b[0]==c[0]==d[0]:
                        self.assertGreaterEqual(max(min(a[1],b[1]),min(c[1],d[1])),min(max(a[1],b[1]),max(c[1],d[1])))
                    if a[1]==b[1]==c[1]==d[1]:
                        self.assertGreaterEqual(max(min(a[0],b[0]),min(c[0],d[0])),min(max(a[0],b[0]),max(c[0],d[0])))

    def test_phase_geometry_and_retirement(self):
        for stage in range(1,8):
            bp=get(f'phase-{stage}.json')
            cells=set()
            for entity in bp['entities']:
                area=footprint(entity)
                self.assertFalse(cells&area,f'Overlapping entity in phase {stage}: {entity}')
                cells|=area
                self.assertTrue(all(0<=x<160 and 0<=y<128 for x,y in area),entity)
                self.assertFalse(any(k.startswith('_') for k in entity))
            fuels=[e for e in bp['entities'] if e['name'] in {'stone-furnace','steel-furnace','burner-inserter'}]
            self.assertEqual(bool(fuels),stage<5)
            self.assertEqual(bp['snap-to-grid'],{'x':32,'y':32})
            self.assertTrue(bp['absolute-snapping'])

    def test_progression_is_not_a_second_science_factory(self):
        for stage in range(2,7):
            expected={'automation'} if stage==2 else {'automation','logistic','military'} if stage==3 else {'automation','logistic','military','chemical'} if stage<6 else set(bootstrap.SCIENCE)
            current=get(f'phase-{stage}.json')
            for name,count in bootstrap.SCIENCE.items():
                self.assertEqual(sum(e.get('recipe')==name+'-science-pack' for e in current['entities']),count if name in expected else 0)
        final=get('phase-6.json')['entities']
        final_positions={(e['position']['x'],e['position']['y']) for e in final}
        for stage in range(2,6):
            for e in get(f'phase-{stage}.json')['entities']:
                if e['name'] in {'stone-furnace','steel-furnace','burner-inserter','wooden-chest'}:continue
                # The temporary iron/copper cell's electric inserter is retired.
                if e['position']['x']<7 and e['position']['y']>=100:continue
                self.assertIn((e['position']['x'],e['position']['y']),final_positions)

    def test_oil_milestones_and_early_power(self):
        self.assertFalse(any(e['name']=='medium-electric-pole' for e in get('phase-2.json')['entities']))
        self.assertFalse(any(e['name']=='oil-refinery' for e in get('phase-3.json')['entities']))
        recipes={e.get('recipe') for e in get('phase-4.json')['entities']}
        self.assertIn('basic-oil-processing',recipes)
        self.assertFalse(recipes&{'advanced-oil-processing','heavy-oil-cracking','light-oil-cracking','lubricant'})

    def test_user_electric_tile_banks(self):
        for name,count,rows in [('electric-smelting',48,4),('brick-smelting',24,2)]:
            bp=get(f'phase-6-external-resources/{name}.json')
            self.assertEqual(sum(e['name']=='electric-furnace' for e in bp['entities']),count)
            self.assertEqual(sum(e['name']=='medium-electric-pole' for e in bp['entities']),6*rows)
            self.assertFalse(any(e.get('items') for e in bp['entities']))
            self.assertTrue(all(0<=x<40 and 0<=y<32 for e in bp['entities'] for x,y in footprint(e)))
            ends,pairs=tunnels(bp)
            self.assertEqual(set(ends),{p for pair in pairs for p in pair})
            for color in BELTS:self.assertEqual(tunnels(tier(bp,color))[1],pairs)

    def test_scheduled_vanilla_resource_trains(self):
        stations=set()
        for path in (BOOK/'phase-6-external-resources').glob('import-*.json'):
            stops=[e for e in json.loads(path.read_text())['blueprint']['entities'] if e['name']=='train-stop']
            self.assertEqual(len(stops),1);self.assertEqual(stops[0]['manual_trains_limit'],1)
            stations.add(stops[0]['station'])
        self.assertEqual(len(stations),5)
        for path in (BOOK/'phase-6-external-resources').glob('train-*.json'):
            bp=json.loads(path.read_text())['blueprint'];self.assertEqual(len(bp['entities']),4)
            for s in bp['schedules']:
                self.assertEqual(len(s['schedule']['records']),2)
                self.assertIn(s['schedule']['records'][1]['station'],stations)

    def test_launch_batch_mass_balance_and_geometry(self):
        plan=bootstrap.read('brians-bootstrap/launch-plan.json')
        recipes=bootstrap.read('brians-bootstrap/source/launch-recipes.json')
        balance={}
        for cell in plan['cells']:
            balance[cell['product']]=balance.get(cell['product'],0)+cell['target']
            for ingredient in cell['ingredients']:
                if ingredient['type']=='item':
                    balance[ingredient['name']]=balance.get(ingredient['name'],0)-ingredient['amount']
        for name,count in plan['external_items'].items():balance[name]=balance.get(name,0)+count
        for name,count in plan['rocket_load'].items():balance[name]-=count
        self.assertEqual({n:v for n,v in balance.items() if v},
            {'rocket-silo':1,'cargo-landing-pad':1,'space-platform-starter-pack':1})
        self.assertEqual(plan['external_items']['electronic-circuit'],6000)
        self.assertEqual(plan['external_items']['steel-plate'],2345)
        for path,size in [('workshop',32),('launch-pad',32),('research-labs',32)]:
            bp=get(f'first-launch/{path}.json');cells=set()
            for entity in bp['entities']:
                area=footprint(entity)
                self.assertFalse(cells&area,entity);cells|=area
                self.assertTrue(all(0<=x<size and 0<=y<size for x,y in area))
        self.assertEqual(sum(e['name']=='lab' for e in get('first-launch/research-labs.json')['entities']),36)
        planner=bootstrap.read('brians-bootstrap/book/planners/upgrade.json')['upgrade_planner']
        self.assertFalse(any('belt' in m['from']['name'] or 'splitter' in m['from']['name']
                             for m in planner['settings']['mappers']))

    def test_nauvis_only_without_space_logistics(self):
        gated=set(bootstrap.read('brians-bootstrap/source/space-age-gated-recipes.json')['recipes'])
        for path in BOOK.rglob('*.json'):
            bp=json.loads(path.read_text()).get('blueprint',{})
            self.assertFalse(any(e.get('recipe') in gated for e in bp.get('entities',[])),path)
            self.assertFalse(any(e['name'] in {'requester-chest','buffer-chest','active-provider-chest'} for e in bp.get('entities',[])),path)


if __name__=='__main__':unittest.main()
