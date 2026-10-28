"""Contracts for implemented original-layout fixes; not a completion claim."""
import json
import sys
import unittest
from pathlib import Path
from collections import deque
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from compact_bootstrap import footprint, transport_graph
from original_bootstrap_balance import calculate
ROOT=Path(__file__).resolve().parents[2]
FOLDER=ROOT/'brians-bootstrap/original-rework'
def bp(stage):return json.loads((FOLDER/f'book/phase-{stage}.json').read_text())['blueprint']

class OriginalRework(unittest.TestCase):
    def test_green_route_reaches_original_science_input(self):
        b=bp(3);es=b['entities'];forward,_=transport_graph(es)
        source=next(i for i,e in enumerate(es) if e['name']=='wooden-chest' and e['position']=={'x':37.5,'y':20.5})
        target=next(i for i,e in enumerate(es) if e.get('recipe')=='logistic-science-pack')
        seen={source};queue=deque([source])
        while queue:
            i=queue.popleft()
            for j in forward[i]:
                if j not in seen:seen.add(j);queue.append(j)
        self.assertIn(target,seen)
        # The native transport fixture additionally verifies actual item flow.
        self.assertTrue(any(e['name']=='inserter' and e['position']=={'x':14.5,'y':44.5} for e in es))
        self.assertEqual(es[target]['position'],{'x':10.5,'y':46.5})

    def test_geometry_and_recipe_preservation(self):
        source=json.loads((ROOT/'brians-bootstrap/source/early-game/phase-#4.json').read_text())['blueprint']
        expected={e['recipe'] for e in source['entities'] if e.get('recipe')} - {'cliff-explosives'}
        for stage in [3,4,5,6]:
            occupied=set()
            for entity in bp(stage)['entities']:
                cells=footprint(entity)
                self.assertFalse(occupied&cells,entity)
                occupied|=cells
            if stage>=4:self.assertTrue(expected <= {e.get('recipe') for e in bp(stage)['entities']})

    def test_red_tier_and_machine_upgrade(self):
        b=bp(5);names={e['name'] for e in b['entities']}
        self.assertFalse(names&{'transport-belt','underground-belt','splitter','assembling-machine-1','inserter','burner-inserter','small-electric-pole','stone-furnace'})
        self.assertTrue({'fast-transport-belt','assembling-machine-2','fast-inserter','medium-electric-pole'}<=names)
        self.assertEqual(len(bp(4)['entities']),len(b['entities']))

    def test_cracking_controls_use_real_tank_signals(self):
        b=bp(4)
        for recipe,fluid,threshold in [('heavy-oil-cracking','heavy-oil',1000),('light-oil-cracking','light-oil',1500)]:
            machine=next(e for e in b['entities'] if e.get('recipe')==recipe)
            control=machine['control_behavior']
            self.assertTrue(control['circuit_enabled'])
            self.assertFalse(control['circuit_read_contents'])
            self.assertEqual(control['circuit_condition']['first_signal']['name'],fluid)
            self.assertEqual(control['circuit_condition']['constant'],threshold)
        self.assertTrue(any(a==bb==2 for _,a,_,bb in b['wires']))

    def test_priority_imports_retire_only_the_science_furnaces(self):
        b=bp(6);ports=json.loads((FOLDER/'priority-imports.json').read_text())
        self.assertEqual([p['item'] for p in ports],['iron-plate','iron-plate','copper-plate'])
        self.assertEqual(sum(e['name']=='fast-splitter' and e['position']['x']<0 and e.get('output_priority')=='left' for e in b['entities']),3)
        centers={(1,44),(4,46),(4,51)}
        self.assertFalse(any('furnace' in e['name'] and (e['position']['x'],e['position']['y']) in centers for e in b['entities']))
        self.assertTrue(any('furnace' in e['name'] and e['position']=={'x':15,'y':37} for e in b['entities']))

    def test_finished_mall_buffers_are_bounded(self):
        b=bp(5)
        maker=next(e for e in b['entities'] if e['position']=={'x':34.5,'y':47.5})
        self.assertEqual(maker['control_behavior']['circuit_condition']['constant'],2)
        self.assertEqual(maker['override_stack_size'],1)
        limits=json.loads((FOLDER/'mall-stock-limits.json').read_text())
        self.assertFalse(any(e['recipe'] in {'electronic-circuit','advanced-circuit','engine-unit','iron-gear-wheel'} for e in limits))

    def test_shared_intermediate_demand(self):
        recipes=json.loads((FOLDER/'recipe-demand-source.json').read_text());report=calculate(recipes)['production']
        for item,rate in [('electronic-circuit',22.5),('advanced-circuit',4.625),('engine-unit',1),('iron-gear-wheel',2.875)]:self.assertAlmostEqual(report[item]['items_per_second'],rate)
        for item in ['automation','logistic','military','chemical','production','utility']:self.assertAlmostEqual(report[item+'-science-pack']['items_per_minute'],45)

if __name__=='__main__':unittest.main()
