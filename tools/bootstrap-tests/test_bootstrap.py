"""Blueprint contract checks; sustained throughput is a separate engine test."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
from fatul import Processor, read_files

spec = importlib.util.spec_from_file_location('bootstrap', TOOLS / 'build-bootstrap.py')
bootstrap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap)
BOOK = TOOLS.parent / 'brians-bootstrap/book'


def get(name):
    return json.loads((BOOK / name).read_text())['blueprint']


class BootstrapBook(unittest.TestCase):
    def test_book_round_trip_and_reference_integrity(self):
        data = read_files(BOOK, False)
        packed = Processor(False).encode(copy.deepcopy(data))
        result = Processor(False, ids_mode='keep').decode(packed)
        self.assertEqual(result['blueprint_book']['label'], data['blueprint_book']['label'])

    def test_science_counts_and_external_smelting(self):
        bp = get('phase-7-science-campus.json')
        for name, count in bootstrap.SCIENCE.items():
            machines = [e for e in bp['entities'] if e.get('recipe') == name + '-science-pack']
            self.assertEqual(len(machines), count, name)
            self.assertTrue(all(e['name'] == 'assembling-machine-2' for e in machines))
        self.assertFalse(any(e['name'] in {'stone-furnace', 'steel-furnace'} for e in bp['entities']))

    def test_starter_overlay_alignment(self):
        phases = [get(f'phase-{i}.json') for i in range(1, 6)]
        def positions(bp, name):
            return {tuple(e['position'].values()) for e in bp['entities'] if e['name'] == name}
        self.assertTrue(positions(phases[0], 'stone-furnace') <= positions(phases[1], 'stone-furnace'))
        gears = [{tuple(e['position'].values()) for e in bp['entities']
                  if e.get('recipe') == 'iron-gear-wheel'} for bp in phases[1:]]
        self.assertTrue(gears[0] <= gears[1])
        self.assertTrue(gears[1] <= gears[2])
        self.assertEqual(gears[2], gears[3])

    def test_tier_upgrade_preserves_braided_tunnels(self):
        old, new = get('phase-4.json'), get('phase-5.json')
        self.assertFalse(any(e['name'] in {'assembling-machine-1', 'transport-belt',
            'splitter', 'inserter'} for e in new['entities']))
        def tunnels(bp):
            return [(e['name'], e['position'], e.get('type')) for e in bp['entities']
                    if 'underground-belt' in e['name']]
        self.assertEqual(tunnels(old), tunnels(new))

    def test_external_bank(self):
        bp = get('phase-6-external-resources/electric-smelting.json')
        self.assertEqual(sum(e['name'] == 'electric-furnace' for e in bp['entities']), 48)
        self.assertFalse(any(e['name'] in {'stone-furnace', 'steel-furnace', 'burner-inserter'}
                             for e in bp['entities']))
        self.assertTrue(all(0 <= e['position']['x'] < 32 and 0 <= e['position']['y'] < 128
                            for e in bp['entities']))

    def test_brick_bank_and_batch_power(self):
        bp = get('phase-6-external-resources/brick-smelting.json')
        self.assertEqual(sum(e['name'] == 'electric-furnace' for e in bp['entities']), 24)
        self.assertTrue(all(0 <= e['position']['x'] < 32 and 0 <= e['position']['y'] < 64
                            for e in bp['entities']))
        cell = get('early-support/solar-panel.json')
        self.assertEqual(sum(e['name'] == 'small-electric-pole' for e in cell['entities']), 2)
        self.assertTrue(cell.get('wires'))
        self.assertTrue(all(e.get('direction') == 0 for e in cell['entities']
                            if e['name'] == 'inserter'))

    def test_vanilla_imports_and_scheduled_trains(self):
        names = set()
        for path in (BOOK / 'phase-6-external-resources').glob('import-*.json'):
            bp = json.loads(path.read_text())['blueprint']
            stops = [e for e in bp['entities'] if e['name'] == 'train-stop']
            self.assertEqual(len(stops), 1)
            self.assertEqual(stops[0]['manual_trains_limit'], 1)
            names.add(stops[0]['station'])
        self.assertEqual(len(names), 5)
        for path in (BOOK / 'phase-6-external-resources').glob('train-*.json'):
            bp = json.loads(path.read_text())['blueprint']
            self.assertEqual(len(bp['entities']), 4)
            for s in bp['schedules']:
                self.assertEqual(len(s['schedule']['records']), 2)
                self.assertNotIn('interrupts', s['schedule'])
                self.assertIn(s['schedule']['records'][1]['station'], names)

    def test_no_space_logistics_entities_in_nauvis_mall(self):
        bp = get('phase-8-infrastructure-mall.json')
        self.assertFalse(any(e['name'] in {'requester-chest', 'buffer-chest',
            'active-provider-chest'} for e in bp['entities']))
        recipes = {e.get('recipe') for e in bp['entities']}
        self.assertTrue({'concrete', 'refined-concrete', 'gun-turret',
            'laser-turret', 'flamethrower-turret', 'nuclear-reactor', 'electric-furnace'} <= recipes)
        self.assertFalse(recipes & set(bootstrap.read(
            'brians-bootstrap/source/space-age-gated-recipes.json')['recipes']))

    def test_chunk_grid(self):
        for name in ['phase-5.json', 'phase-7-science-campus.json',
                'phase-8-infrastructure-mall.json',
                'phase-6-external-resources/electric-smelting.json']:
            bp = get(name)
            self.assertEqual(bp['snap-to-grid'], {'x': 32, 'y': 32})
            self.assertTrue(bp['absolute-snapping'])


if __name__ == '__main__':
    unittest.main()
