#!/usr/bin/env python3
"""Build one staged, chunk-aligned Space Age bootstrap and resource modules."""
import base64
import copy
import json
import math
from pathlib import Path
import sys
import zlib

from fatul import to_pretty_json

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'brians-bootstrap/book'
VERSION = (2 << 48) | (1 << 32) | (23 << 16)
SCIENCE = {'automation': 5, 'logistic': 6, 'military': 5,
           'chemical': 12, 'production': 7, 'utility': 7}
TIERS = {'transport-belt': 'fast-transport-belt',
         'splitter': 'fast-splitter', 'assembling-machine-1': 'assembling-machine-2',
         'inserter': 'fast-inserter'}


def read(path):
    return json.loads((ROOT / path).read_text())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(to_pretty_json(value, compact=True) + '\n')


def move(bp, dx, dy):
    """Translate FaTul coordinate references as well as entity positions."""
    bp = copy.deepcopy(bp)
    for e in bp.get('entities', []):
        e['position']['x'] += dx
        e['position']['y'] += dy
    # FaTul's top-level wire/schedule coordinates are relative to the minimum
    # entity position. A uniform translation leaves those references unchanged.
    for t in bp.get('tiles', []):
        t['position']['x'] += dx
        t['position']['y'] += dy
    bp.pop('shift_x', None)
    bp.pop('shift_y', None)
    bp['version'] = VERSION
    return bp


def aligned(bp):
    bp['snap-to-grid'] = {'x': 32, 'y': 32}
    bp['absolute-snapping'] = True
    bp['position-relative-to-grid'] = {'x': 0, 'y': 0}
    return bp


def metadata(label, index=0):
    return {'index': index, 'blueprint_book': {'item': 'blueprint-book',
            'label': label, 'version': VERSION, 'active_index': 0}}


def save_bp(folder, filename, bp, index):
    write(folder / (filename + '.json'), {'index': index, 'blueprint': bp})


def upgrade(bp):
    bp = copy.deepcopy(bp)
    for e in bp['entities']:
        e['name'] = TIERS.get(e['name'], e['name'])
    return bp


def power_wires(bp):
    """Connect the poles explicitly; construction must not rely on auto-wire."""
    es = bp['entities']
    poles = [t for t in es if t['name'] in {'small-electric-pole',
                                          'medium-electric-pole', 'big-electric-pole'}]
    reach = {'small-electric-pole': 7.5, 'medium-electric-pole': 9, 'big-electric-pole': 32}
    parent = list(range(len(poles)))
    degree = [0] * len(poles)
    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    edges = []
    for i, a in enumerate(poles):
        for j, b in enumerate(poles[:i]):
            d = math.hypot(a['position']['x'] - b['position']['x'],
                           a['position']['y'] - b['position']['y'])
            if d <= min(reach[a['name']], reach[b['name']]):
                edges.append((d, i, j))
    min_x = min(t['position']['x'] for t in es)
    min_y = min(t['position']['y'] for t in es)
    def ref(t):
        return f"{t['position']['x'] - min_x:g},{t['position']['y'] - min_y:g}"
    wires = []
    for _, i, j in sorted(edges):
        a, b = root(i), root(j)
        if a != b and degree[i] < 5 and degree[j] < 5:
            parent[a] = b
            degree[i] += 1
            degree[j] += 1
            wires.append([ref(poles[i]), 5, ref(poles[j]), 5])
    if poles and len({root(i) for i in range(len(poles))}) != 1:
        raise ValueError(f"Disconnected power grid in {bp.get('label', 'blueprint')}")
    bp['wires'] = wires
    return bp


def e(name, x, y, **extra):
    return {'name': name, 'position': {'x': x, 'y': y}, **extra}


def icon(item):
    return [{'index': 1, 'signal': {'name': item}}]


def early_cell(recipe, label, index):
    """Small chest-fed early batch production; no locked logistics chests."""
    bp = {'item': 'blueprint', 'label': label, 'version': VERSION,
          'icons': icon(recipe), 'entities': [
              e('assembling-machine-1' if recipe in {'gun-turret', 'gate', 'solar-panel'}
                else 'assembling-machine-2',
                8.5, 8.5, recipe=recipe, direction=4),
              e('iron-chest', 8.5, 5.5),
              e('inserter', 8.5, 6.5, direction=0),
              e('wooden-chest', 8.5, 11.5, bar=1),
              e('inserter', 8.5, 10.5, direction=0),
              e('small-electric-pole', 6.5, 6.5),
              e('small-electric-pole', 6.5, 10.5)],
          'description': 'Early batch production: put recipe ingredients in '
          'the north chest; take output from the south chest. One stack output '
          'limit. Place separately on the chunk grid; replace with the belt-fed '
          'infrastructure mall later. Fluid recipes: connect water to the east '
          'pipe. These are batch cells; feed ingredients manually or connect '
          'your own input belts, not requester-chest automation.'}
    if recipe in {'concrete', 'refined-concrete'}:
        bp['entities'].extend([e('pipe', 10.5, 8.5), e('pipe', 11.5, 8.5)])
    return {'index': index, 'blueprint': aligned(power_wires(bp))}


def uranium_processing():
    es = []
    for y in range(28):
        es.append(e('transport-belt', 10.5, y + .5, direction=8))
    for j in range(4):
        y = 7.5 + 6 * j
        es.extend([e('centrifuge', 7.5, y, recipe='uranium-processing'),
                   e('fast-inserter', 9.5, y, direction=4),
                   e('medium-electric-pole', 7.5, y - 3)])
        for dy, isotope in [(0, 'uranium-238'), (1, 'uranium-235')]:
            es.extend([e('steel-chest', 4.5, y + dy),
                e('fast-inserter', 5.5, y + dy, direction=4, use_filters=True,
                  filters=[{'name': isotope, 'quality': 'normal',
                            'comparator': '=', 'index': 1}])])
    return aligned(power_wires({'item': 'blueprint', 'version': VERSION,
        'label': 'Uranium processing — four centrifuges',
        'description': '32x32 module. Feed uranium ore at (10.5,0.5), southbound. '
            'U-238 and U-235 leave through separate filtered inserters into '
            'steel chests. Connect power. Mine actual uranium ore to unlock '
            'the recipe first. Does not require Kovarex. Outputs are random; '
            'stockpile fuel before relying on nuclear generation.',
        'icons': icon('uranium-235'), 'entities': es}))


def science_reference():
    bp = read('self-building-factory/book/science-research-(45-spm,-from-raw).json')['blueprint']
    # Preserve the production and oil district, not its railway/fuel smelting.
    excluded = {'train-stop', 'straight-rail', 'half-diagonal-rail', 'curved-rail-a',
                'curved-rail-b', 'rail-signal', 'rail-chain-signal', 'steel-furnace',
                'roboport', 'cargo-landing-pad', 'radar', 'small-lamp',
                'constant-combinator', 'arithmetic-combinator',
                'decider-combinator', 'selector-combinator'}
    es = []
    # These tanks belonged to product export stations. Keeping 125k of acid
    # storage in a starter starves batteries while the shared fluid segment
    # fills. Preserve the connection corners with compact pipe links instead.
    pipe_tanks = {(82.5, 198.5), (147.5, 198.5), (152.5, 192.5),
                  (152.5, 195.5), (160.5, 193.5), (160.5, 197.5)}
    keep_science = {}
    for name, count in SCIENCE.items():
        machines = sorted((t for t in bp['entities']
                           if t.get('recipe') == name + '-science-pack'),
                          key=lambda t: (t['position']['x'], t['position']['y']))
        keep_science[name] = {tuple(t['position'].values()) for t in machines[:count]}
        assert len(keep_science[name]) == count
    for src in bp['entities']:
        x, y = src['position']['x'], src['position']['y']
        if not (60 <= x < 224 and 80 <= y < 208) or src['name'] in excluded:
            continue
        entity = copy.deepcopy(src)
        recipe = entity.get('recipe', '')
        if entity['name'] == 'storage-tank' and (x, y) in pipe_tanks:
            corners = [(1, -1), (0, -1), (0, 0), (0, 1), (-1, 1)] \
                if entity.get('direction', 0) == 4 else \
                [(-1, -1), (0, -1), (0, 0), (0, 1), (1, 1)]
            es.extend(e('pipe', x + dx, y + dy) for dx, dy in corners)
            continue
        if entity['name'] == 'iron-chest' and x in {209.5, 214.5}:
            continue
        if entity.get('use_filters') and any(
                f.get('name') == 'copper-ore' for f in entity.get('filters', [])):
            continue
        if recipe in {'lab', 'productivity-module-2'}:
            continue
        if entity['name'] == 'iron-chest' and y >= 184:
            continue  # obsolete product-export buffers, not science intermediates
        if recipe.endswith('-science-pack'):
            key = recipe.removesuffix('-science-pack')
            if tuple(entity['position'].values()) not in keep_science[key]:
                continue
        # Remove old station/export control dependencies and construction requests.
        if entity['name'] != 'pump':
            entity.pop('control_behavior', None)
        if recipe == 'lubricant':
            entity['control_behavior'] = {
                'circuit_enabled': True,
                'circuit_condition': {'comparator': '<', 'constant': 1000,
                    'first_signal': {'name': 'lubricant', 'type': 'fluid'}}}
        if entity['name'] in {'iron-chest', 'passive-provider-chest', 'storage-chest'}:
            entity['bar'] = 1
        entity.pop('items', None)
        es.append(entity)
    bp = {'item': 'blueprint', 'label': 'Six-science campus — external smelting',
          'version': VERSION, 'entities': es,
          'icons': icon('utility-science-pack'),
          'description': '192x160 reserved area. 5/6/5/12/7/7 assembler 2s. '
          '45/45/45/45/45/45 packs/min machine capacity before modules. '
          'Supply marked plate, steel, brick, stone, coal, water and crude-oil '
          'ports. This is a separate district: retire the starter science and '
          'smelting after commissioning it. See PORTS.md; do not feed ore to '
          'plate ports. Research advanced oil processing and inserter capacity '
          'before commissioning; add purple/yellow machines as unlocked.'}
    # Preserve all tunnels crossing the crop boundary by exposing their end as
    # an ordinary belt, rather than leaving an unpaired underground output.
    ports = [
        (60.5, 80.5, 'steel-plate', 8),
        (62.5, 80.5, 'iron-plate', 8), (63.5, 80.5, 'iron-plate', 8),
        (64.5, 80.5, 'iron-plate', 8), (65.5, 80.5, 'iron-plate', 8),
        (64.5, 91.5, 'iron-plate', 4), (64.5, 92.5, 'iron-plate', 4),
        (64.5, 93.5, 'steel-plate', 4), (64.5, 127.5, 'coal', 4),
        (79.5, 83.5, 'coal', 8), (145.5, 83.5, 'stone', 8),
        (168.5, 83.5, 'stone-brick', 8),
        (175.5, 80.5, 'copper-plate', 8), (176.5, 80.5, 'copper-plate', 8),
        (177.5, 80.5, 'copper-plate', 8), (178.5, 80.5, 'copper-plate', 8)]
    for x, y, item, direction in ports:
        old = next(t for t in es if t['position'] == {'x': x, 'y': y})
        old['name'] = 'fast-transport-belt'
        old['direction'] = direction
        old.pop('type', None)
    # Extend the two connected raw-fluid networks into the empty southern
    # corridor, giving the district honest external interfaces. Test these
    # pipes, never inject fluid into individual crafting machines.
    es.extend([e('pipe-to-ground', 79.5, 204.5, direction=0),
               e('pipe-to-ground', 79.5, 210.5, direction=8)])
    for y in range(131, 138):
        es.append(e('pipe', 79.5, y + 80.5))
    for x in range(19):
        es.append(e('pipe', x + 60.5, 217.5))
    for y in range(129, 144):
        es.append(e('pipe', 91.5, y + 80.5))
    for x in range(31):
        es.append(e('pipe', x + 60.5, 223.5))
    # One basic refinery supplies petroleum headroom without adding another
    # heavy/light loop. The eight advanced refineries alone are slightly below
    # the unmoduled six-science demand once lubricant is reserved.
    es.append(e('oil-refinery', 100.5, 223.5, recipe='basic-oil-processing'))
    es.extend([e('pipe-to-ground', 138.5, 201.5, direction=0),
               e('pipe-to-ground', 138.5, 210.5, direction=8)])
    for y in range(131, 135):
        es.append(e('pipe', 138.5, y + 80.5))
    for x in range(42, 78):
        es.append(e('pipe', x + 60.5, 214.5))
    for y in range(135, 141):
        es.append(e('pipe', 102.5, y + 80.5))
    for y in range(144, 152):
        es.append(e('pipe', 91.5, y + 80.5))
    for x in range(32, 42):
        es.append(e('pipe', x + 60.5, 231.5))
    for y in range(146, 151):
        es.append(e('pipe', 101.5, y + 80.5))
    for y in [127.5, 135.5, 143.5]:
        es.append(e('medium-electric-pole', 104.5, y + 80))
    es.append(e('medium-electric-pole', 107.5, 201.5))
    # Campus local coordinates are independent of the old city's anchor.
    # This source geometry is normalized and made uniform-tier by compact().
    power_wires(bp)
    min_x = min(t['position']['x'] for t in es)
    min_y = min(t['position']['y'] for t in es)
    def wire_ref(x, y):
        assert any(t['position'] == {'x': x, 'y': y} for t in es)
        return f'{x - min_x:g},{y - min_y:g}'
    # Small working reserves, rather than filling 25k tanks before science can
    # use the heavy oil. The heavy supply pump already has the <1000 condition.
    bp['wires'].extend([
        [wire_ref(86.5, 197.5), 1, wire_ref(89, 196.5), 1],
        [wire_ref(82.5, 201.5), 1, wire_ref(86.5, 200.5), 1]])
    bp = aligned(move(bp, -60, -80))
    return bp, [(x - 60, y - 80, item, d) for x, y, item, d in ports]


def source_train_book():
    s = (ROOT / 'LTN Style Train System Blueprint.txt').read_text().strip()
    return json.loads(zlib.decompress(base64.b64decode(s[1:])))


def flatten(data):
    if 'blueprint' in data:
        yield data['blueprint']
    for entry in data.get('blueprint_book', {}).get('blueprints', []):
        yield from flatten(entry)


def import_stations():
    from fatul import Processor
    # Decode the reference through FaTul so wires/schedules can be moved safely.
    raw = source_train_book()
    codec = Processor(False, ids_mode='refs')
    codec.process_ids(raw, to_abs_ids=False)
    templates = list(flatten(raw))
    cargo = next(b for b in templates if len(b['entities']) == 120
                 and any('Unload' in t.get('station', '') for t in b['entities']))
    fluid = next(b for b in templates if len(b['entities']) == 101
                 and any('Unload' in t.get('station', '') for t in b['entities']))
    for i, resource in enumerate(['iron-ore', 'copper-ore', 'coal', 'stone', 'crude-oil']):
        bp = copy.deepcopy(fluid if resource == 'crude-oil' else cargo)
        # Shift by an even number of tiles to preserve Factorio's rail parity.
        min_x = min(t['position']['x'] for t in bp['entities'])
        min_y = min(t['position']['y'] for t in bp['entities'])
        bp = move(bp, -2 * math.floor(min_x / 2), -2 * math.floor(min_y / 2))
        bp['label'] = 'Import — ' + resource
        bp['description'] = ('Reference-book unloading geometry, normalized to '
            'the chunk grid. Connect its tracks and output belts/pipes manually. '
            'Use explicit source → destination schedules for the bootstrap; '
            'the city-block interrupt/dispatch migration is a separate change. '
            'Train limit 1. Ore goes to external smelting; coal goes to '
            'chemistry/military and any remaining backup boilers.')
        for entity in bp['entities']:
            if entity['name'] == 'train-stop':
                entity['station'] = f'[item={resource}] Bootstrap unload' if resource != 'crude-oil' else '[fluid=crude-oil] Bootstrap unload'
                entity['manual_trains_limit'] = 1
        if resource != 'crude-oil':
            chests = [t for t in bp['entities'] if t['name'] == 'steel-chest']
            assert sorted(t['position']['x'] for t in chests) == [
                16.5, 17.5, 18.5, 19.5, 20.5, 21.5,
                23.5, 24.5, 25.5, 26.5, 27.5, 28.5]
            for chest in chests:
                bp['entities'].append(e('bulk-inserter', chest['position']['x'],
                                         32.5, direction=0))
            # Four chests per output, sideloading from both sides. Three red
            # outputs allow 90/s instead of the 60/s ceiling of two red belts.
            for left, join, right in [(16, 18, 19), (20, 22, 24), (25, 27, 28)]:
                for x in range(left, right + 1):
                    direction = 4 if x < join else 12 if x > join else 8
                    bp['entities'].append(e('fast-transport-belt', x + .5,
                                             33.5, direction=direction))
                for y in range(34, 64):
                    bp['entities'].append(e('fast-transport-belt', join + .5,
                                             y + .5, direction=8))
            for x, y in [(15.5, 32.5), (22.5, 31.5), (29.5, 32.5)]:
                bp['entities'].append(e('medium-electric-pole', x, y))
            bp['description'] += (' Outputs, southbound: (18.5,63.5), '
                '(22.5,63.5), (27.5,63.5). Three red belts, up to 90/s '
                'with sufficient unloading speed, wagon contents and train service.')
        else:
            for y in range(33, 64):
                bp['entities'].append(e('pipe', 22.5, y + .5))
            bp['entities'].append(e('medium-electric-pole', 22.5, 30.5))
            bp['description'] += ' Crude pipe output: (22.5,63.5).'
        yield i, resource, aligned(power_wires(bp))


def resource_trains():
    from fatul import Processor
    raw = source_train_book()
    Processor(False, ids_mode='refs').process_ids(raw, to_abs_ids=False)
    templates = list(flatten(raw))
    for resource in ['iron-ore', 'copper-ore', 'coal', 'stone', 'crude-oil']:
        wagon = 'fluid-wagon' if resource == 'crude-oil' else 'cargo-wagon'
        src = next(b for b in templates if len(b['entities']) == 4
                   and any(t['name'] == wagon for t in b['entities']))
        bp = move(src, -612, -428)
        tag = f'[fluid={resource}]' if resource == 'crude-oil' else f'[item={resource}]'
        bp['label'] = resource + ' — 2-2 bootstrap train'
        bp['description'] = ('Two locomotives, two wagons. Place on existing rails; '
            'fuel locomotives with coal until a fuel-loading station is built. '
            'Explicit resource-specific schedules do not depend on rocket fuel '
            'or the later city-block interrupt overhaul.')
        for t in bp['entities']:
            t.pop('items', None)
        for schedule in bp.get('schedules', []):
            schedule['schedule'] = {'group': 'Bootstrap: ' + resource, 'records': [
                {'station': tag + ' Outpost load', 'wait_conditions': [
                    {'type': 'full', 'compare_type': 'and'}]},
                {'station': tag + ' Bootstrap unload', 'wait_conditions': [
                    {'type': 'empty', 'compare_type': 'and'}]}]}
        yield resource, aligned(bp)


def build():
    # Only generated JSON is owned here; do not touch other repository books.
    for p in DEST.rglob('*.json'):
        p.unlink()
    write(DEST / '_metadata.json', metadata("Brian's Bootstrap — Space Age 2.1", 0))
    early = DEST / 'early-support'
    write(early / '_metadata.json', metadata('Early solar and defenses', 7))
    for i, (recipe, label) in enumerate([
        ('solar-panel', 'Solar panels — green science unlock'),
        ('gun-turret', 'Gun turrets — early batch production'),
        ('gate', 'Gates — early batch production'),
        ('accumulator', 'Accumulators — after batteries')]):
        write(early / (recipe + '.json'), early_cell(recipe, label, i))

    batches = DEST / 'nauvis-infrastructure'
    write(batches / '_metadata.json', metadata('Nauvis infrastructure batch mall — no space science', 9))
    for i, recipe in enumerate(['concrete', 'refined-concrete', 'hazard-concrete',
            'refined-hazard-concrete', 'gun-turret', 'flamethrower-turret',
            'laser-turret', 'stone-wall', 'gate', 'electric-furnace',
            'nuclear-reactor', 'centrifuge', 'heat-exchanger', 'heat-pipe',
            'steam-turbine', 'uranium-fuel-cell', 'roboport', 'solar-panel',
            'accumulator', 'construction-robot', 'assembling-machine-1',
            'assembling-machine-2','fast-inserter','long-handed-inserter',
            'electric-mining-drill','boiler','steam-engine','offshore-pump',
            'pipe','pipe-to-ground','pump','pumpjack','oil-refinery','chemical-plant',
            'storage-tank','rail','rail-signal','rail-chain-signal','train-stop',
            'locomotive','cargo-wagon','fluid-wagon','medium-electric-pole',
            'big-electric-pole','radar','lab','fast-transport-belt',
            'fast-underground-belt','fast-splitter','express-transport-belt',
            'express-underground-belt','express-splitter','piercing-rounds-magazine']):
        write(batches / (recipe + '.json'), early_cell(recipe, recipe, i))
    save_bp(batches, 'uranium-processing', uranium_processing(), 99)

    ext = DEST / 'phase-6-external-resources'
    write(ext / '_metadata.json', metadata('External electric smelting and raw imports', 8))
    from compact_bootstrap import furnace_bank
    save_bp(ext, 'electric-smelting', furnace_bank(ROOT, e, power_wires, aligned), 0)
    for i, resource, bp in import_stations():
        save_bp(ext, 'import-' + resource, bp, i + 1)
    for i, (resource, bp) in enumerate(resource_trains()):
        save_bp(ext, 'train-' + resource, bp, i + 6)
    save_bp(ext, 'brick-smelting', furnace_bank(ROOT, e, power_wires, aligned, rows=2), 11)

    from compact_bootstrap import compact, phases, tier
    science, ports = science_reference()
    science = compact(science, ROOT, e, power_wires, early_cell)
    first = {k: copy.deepcopy(v) for k,v in science.items() if k not in {'entities','wires'}}
    first['entities'] = [{k:copy.deepcopy(v) for k,v in t.items() if not k.startswith('_')} for t in science['entities'] if t.get('_starter_only')]
    first['icons'] = icon('stone-furnace')
    first['label'] = 'Phase 1 — First smelting, permanent bootstrap anchor'
    first['description'] = 'Hand-fed iron, copper and coal. Same 160x128 reservation as all later phases. Connect external steam power for phase 2. Retire these fuel furnaces at phase 5, after external smelting is running.'
    save_bp(DEST, 'phase-1', first, 0)
    for stage, data in phases(science, ROOT, e, power_wires):
        save_bp(DEST, f'phase-{stage}', data, stage-1)

    planners = DEST / 'planners'
    write(planners / '_metadata.json', metadata('Transition planners', 10))
    upgrade_tiers = {**TIERS, 'underground-belt':'fast-underground-belt'}
    write(planners / 'upgrade.json', {'index': 0, 'upgrade_planner': {
        'item': 'upgrade-planner', 'label': 'Starter tier upgrade', 'version': VERSION,
        'settings': {'mappers': [{'index': i, 'from': {'type': 'entity', 'name': a},
                                  'to': {'type': 'entity', 'name': b}}
                                 for i, (a, b) in enumerate(upgrade_tiers.items())]}}})
    for label, old, new, idx in [('Yellow to red belts',('transport-belt','underground-belt','splitter'),('fast-transport-belt','fast-underground-belt','fast-splitter'),1),('Red to blue belts',('fast-transport-belt','fast-underground-belt','fast-splitter'),('express-transport-belt','express-underground-belt','express-splitter'),2)]:
        write(planners / ('red-belts.json' if idx==1 else 'blue-belts.json'), {'index':idx,'upgrade_planner':{'item':'upgrade-planner','label':label,'version':VERSION,'settings':{'mappers':[{'index':i,'from':{'type':'entity','name':a},'to':{'type':'entity','name':b}} for i,(a,b) in enumerate(zip(old,new))]}}})
    write(planners / 'medium-pole.json', {'index':4,'upgrade_planner':{'item':'upgrade-planner','label':'Medium poles — green science unlock','version':VERSION,'settings':{'mappers':[{'index':0,'from':{'type':'entity','name':'small-electric-pole'},'to':{'type':'entity','name':'medium-electric-pole'}}]}}})
    write(planners / 'retire-fuel-smelting.json', {'index': 3, 'deconstruction_planner': {
        'item': 'deconstruction-planner', 'label': 'Retire starter furnaces only',
        'version': VERSION, 'settings': {'entity_filters': [
            {'index': 1, 'name': 'stone-furnace'}, {'index': 2, 'name': 'steel-furnace'}]}}})
    write(ROOT / 'brians-bootstrap/science-ports.json', [
        {'x': x, 'y': y, 'item': item, 'direction': d} for x, y, item, d in ports])
    write(ROOT / 'brians-bootstrap/science-fluid-ports.json', [
        {'x': .5, 'y': 97.5, 'fluid': 'water'},
        {'x': .5, 'y': 99.5, 'fluid': 'crude-oil'}])


if __name__ == '__main__':
    build()
