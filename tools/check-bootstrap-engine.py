#!/usr/bin/env python3
"""Run a real Space Age 2.1 headless acceptance test in a disposable world.

No extra gameplay mod or external Python dependency is required.
Example: FACTORIO_BINARY=/opt/factorio/bin/x64/factorio python3 tools/check-bootstrap-engine.py
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import time

from fatul import Processor, read_files

ROOT = Path(__file__).resolve().parents[1]


class Rcon:
    def __init__(self, port, password):
        self.connection = socket.create_connection(('127.0.0.1', port), timeout=30)
        self.request = 1
        self.send(3, password)
        while self.receive()[1] != 2:
            pass

    def read(self, length):
        data = b''
        while len(data) < length:
            part = self.connection.recv(length - len(data))
            if not part:
                raise RuntimeError('Headless server disconnected')
            data += part
        return data

    def send(self, kind, text):
        body = struct.pack('<ii', self.request, kind) + text.encode() + b'\0\0'
        self.connection.sendall(struct.pack('<i', len(body)) + body)

    def receive(self):
        size = struct.unpack('<i', self.read(4))[0]
        data = self.read(size)
        number, kind = struct.unpack('<ii', data[:8])
        return number, kind, data[8:-2].decode()

    def command(self, command):
        self.request += 1
        self.send(2, command)
        while True:
            number, _, body = self.receive()
            if number == self.request:
                return body

    def lua(self, source):
        return self.command('/c ' + source)

    def value(self, name, text):
        self.lua(f'storage.{name}=""')
        for offset in range(0, len(text), 12000):
            self.lua(f'storage.{name}=storage.{name}..' + json.dumps(text[offset:offset + 12000]))


def free_port():
    with socket.socket() as candidate:
        candidate.bind(('127.0.0.1', 0))
        return candidate.getsockname()[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--factorio', default=os.environ.get('FACTORIO_BINARY', shutil.which('factorio')))
    parser.add_argument('--inspect', action='store_true')
    parser.add_argument('--phase', type=int, choices=range(2,8), default=6)
    parser.add_argument('--scenario', choices=['science', 'support', 'launch', 'research', 'original'], default='science')
    parser.add_argument('--warmup-minutes', type=int, default=80)
    parser.add_argument('--sample-minutes', type=float, default=None,
                        help='Default 4m for assembler 1 phases; 18m40s for assembler 2 phases')
    parser.add_argument('--timeout', type=int, default=600)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.scenario == 'original' and args.phase not in {3,4,5,6}:
        parser.error('Original-layout fixtures support phases 3, 4, 5 and 6')
    if args.sample_minutes is None:
        args.sample_minutes = 4 if args.phase < 5 else 56/3
    if args.output is None:
        args.output = ROOT / f'brians-bootstrap/validation/{args.scenario}.json'
    if not args.factorio:
        parser.error('Set FACTORIO_BINARY or pass --factorio to a Factorio 2.1 headless binary')
    if args.warmup_minutes < 1 or args.sample_minutes < 1:
        parser.error('Warmup and sample durations must be positive')
    binary = Path(args.factorio).resolve()
    data_path = binary.parents[2] / 'data'
    if not (data_path / 'space-age').exists():
        parser.error('The binary installation must include the official Space Age data')
    config = {
        'warmup_minutes': args.warmup_minutes, 'sample_minutes': args.sample_minutes,
        'item_ports': json.loads((ROOT / 'brians-bootstrap/science-ports.json').read_text()),
        'fluid_ports': json.loads((ROOT / 'brians-bootstrap/science-fluid-ports.json').read_text()),
        'science_counts': {name + '-science-pack': count for name, count in
                          {'automation': 5, 'logistic': 6, 'military': 5,
                           'chemical': 12, 'production': 7, 'utility': 7}.items()}}
    blueprint = json.loads((ROOT / f'brians-bootstrap/book/phase-{args.phase}.json').read_text())
    present = {(e['position']['x'], e['position']['y']) for e in blueprint['blueprint']['entities'] if 'transport-belt' in e['name']}
    config['item_ports'] = [p for p in config['item_ports'] if (p['x'],p['y']) in present]
    if args.phase < 4: config['fluid_ports'] = []
    active = {'automation'} if args.phase == 2 else {'automation','logistic','military'} if args.phase == 3 else {'automation','logistic','military','chemical'} if args.phase < 6 else set(config['science_counts'])
    config['science_counts'] = {name:count for name,count in config['science_counts'].items() if name in active or name.removesuffix('-science-pack') in active}
    config['minimum_spm'] = 29.5 if args.phase < 5 else 44.5
    config['phase'] = args.phase
    config['inspect'] = args.inspect
    if args.inspect:
        config['book'] = Processor(False).encode(read_files(ROOT / 'brians-bootstrap/book', False))
    encoded = Processor(False).encode(copy.deepcopy(blueprint))
    if args.scenario == 'support':
        cases = []
        for name, ingredient, product, expected_rate in [
            ('iron', 'iron-ore', 'iron-plate', 1800),
            ('copper', 'copper-ore', 'copper-plate', 1800),
            ('steel', 'iron-plate', 'steel-plate', 360),
            ('brick', 'stone', 'stone-brick', 900)]:
            path = 'brick-smelting' if name == 'brick' else 'electric-smelting'
            data = json.loads((ROOT / f'brians-bootstrap/book/phase-6-external-resources/{path}.json').read_text())
            cases.append({'name': name, 'kind': 'smelting', 'ingredient': ingredient,
                'product': product, 'expected_rate': expected_rate,
                'rows': 2 if name == 'brick' else 4,
                'blueprint': Processor(False).encode(copy.deepcopy(data))})
        for kind, path in [
            ('solid-import', 'phase-6-external-resources/import-iron-ore'),
            ('fluid-import', 'phase-6-external-resources/import-crude-oil'),
            ('uranium', 'nauvis-infrastructure/uranium-processing'),
            ('solar', 'early-support/solar-panel'),
            ('placement', 'phase-6')]:
            data = json.loads((ROOT / f'brians-bootstrap/book/{path}.json').read_text())
            cases.append({'name': kind, 'kind': kind,
                          'blueprint': Processor(False).encode(copy.deepcopy(data))})
        for phase in range(1, 8):
            data = json.loads((ROOT / f'brians-bootstrap/book/phase-{phase}.json').read_text())
            cases.append({'name': f'phase-{phase}', 'kind': 'placement',
                          'blueprint': Processor(False).encode(copy.deepcopy(data))})
        config = {'cases': cases, 'warmup_minutes': 2, 'sample_minutes': 3}
    if args.scenario == 'launch':
        data = json.loads((ROOT / 'brians-bootstrap/book/first-launch/workshop.json').read_text())
        encoded = Processor(False).encode(copy.deepcopy(data))
        pad = json.loads((ROOT / 'brians-bootstrap/book/first-launch/launch-pad.json').read_text())
        config = json.loads((ROOT / 'brians-bootstrap/launch-plan.json').read_text())
        config['pad'] = Processor(False).encode(copy.deepcopy(pad))
    if args.scenario == 'research':
        data = json.loads((ROOT / 'brians-bootstrap/book/first-launch/research-labs.json').read_text())
        encoded = Processor(False).encode(copy.deepcopy(data))
        config = {}
    if args.scenario == 'original':
        data = json.loads((ROOT / f'brians-bootstrap/original-rework/book/phase-{args.phase}.json').read_text())
        encoded = Processor(False).encode(copy.deepcopy(data))
        config = {'original_phase': args.phase, 'inspect_only': args.inspect}
        if args.phase == 6: config['imports'] = json.loads((ROOT / 'brians-bootstrap/original-rework/priority-imports.json').read_text())
    fixture = (ROOT / f'tools/bootstrap-tests/engine/{args.scenario}.lua').read_text()
    with tempfile.TemporaryDirectory(prefix='bootstrap-engine-') as directory:
        temp = Path(directory)
        runtime = temp / 'runtime'
        runtime.mkdir()
        ini = temp / 'config.ini'
        ini.write_text(f'[path]\nread-data={data_path}\nwrite-data={runtime}\n')
        mods = temp / 'mods'
        mods.mkdir()
        (mods / 'mod-list.json').write_text(json.dumps({'mods': [
            {'name': name, 'enabled': True}
            for name in ['base', 'space-age', 'quality', 'elevated-rails', 'recycler']]}))
        settings = json.loads((data_path / 'server-settings.example.json').read_text())
        settings.update(visibility={'public': False, 'lan': False}, auto_pause=False,
                        require_user_verification=False, autosave_interval=0)
        settings_file = temp / 'server.json'
        settings_file.write_text(json.dumps(settings))
        common = [str(binary), '--config', str(ini), '--mod-directory', str(mods)]
        save = temp / 'world.zip'
        log = temp / 'engine.log'
        with log.open('w') as output:
            subprocess.run(common + ['--create', str(save)], stdout=output,
                           stderr=subprocess.STDOUT, check=True, timeout=60)
        password = secrets.token_hex(16)
        port = free_port()
        udp_port = free_port()
        with log.open('a') as output:
            server = subprocess.Popen(common + [
                '--start-server', str(save), '--server-settings', str(settings_file),
                '--rcon-port', str(port), '--rcon-password', password,
                '--bind', '127.0.0.1', '--port', str(udp_port)],
                stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT)
            try:
                client = None
                for _ in range(200):
                    if server.poll() is not None:
                        raise RuntimeError('Server startup failed')
                    try:
                        client = Rcon(port, password)
                        break
                    except OSError:
                        time.sleep(.1)
                if client is None:
                    raise RuntimeError('Headless server did not open RCON')
                # A fresh map requires the same console command twice to
                # acknowledge disabling achievements in this disposable test.
                for _ in range(2):
                    client.lua('storage.bootstrap_test=true')
                client.value('blueprint_string', encoded)
                client.value('test_config_string', json.dumps(config))
                client.lua('storage.test_config=helpers.json_to_table(storage.test_config_string)')
                client.value('fixture_string', fixture)
                client.lua("local chunk,message=load(storage.fixture_string,'bootstrap-acceptance');"
                    "local ok=false;if chunk then ok,message=pcall(chunk) end;"
                    "if not ok then helpers.write_file('bootstrap-result.json',"
                    "helpers.table_to_json{passed=false,error=message}) end")
                results = runtime / 'script-output/bootstrap-result.json'
                progress = runtime / 'script-output/bootstrap-progress.json'
                deadline = time.monotonic() + args.timeout
                last_minute = -1
                while not results.exists():
                    if server.poll() is not None:
                        raise RuntimeError('Headless server exited during test')
                    if time.monotonic() > deadline:
                        raise RuntimeError('Acceptance test timed out')
                    if progress.exists():
                        try:
                            minute = json.loads(progress.read_text())['elapsed_ticks'] // 3600
                            if minute != last_minute:
                                print(f'Simulated {minute} minutes', flush=True)
                                last_minute = minute
                        except (json.JSONDecodeError, KeyError):
                            pass
                    time.sleep(.2)
                report = json.loads(results.read_text())
                report['blueprint_sha256'] = hashlib.sha256(encoded.encode()).hexdigest() \
                    if args.scenario != 'support' else {
                        case['name']: hashlib.sha256(case['blueprint'].encode()).hexdigest()
                        for case in config['cases']}
                if args.scenario == 'launch':
                    report['launch_pad_sha256'] = hashlib.sha256(config['pad'].encode()).hexdigest()
                    report['launch_plan_sha256'] = hashlib.sha256((ROOT / 'brians-bootstrap/launch-plan.json').read_bytes()).hexdigest()
                if report.get('passed'):
                    report.pop('machines', None)
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(json.dumps(report, indent=2) + '\n')
                print(json.dumps({k: report[k] for k in ['passed', 'engine_version',
                    'packs_per_minute', 'cases', 'unpowered_machines', 'error'] if k in report}, indent=2))
                if not report.get('passed'):
                    raise RuntimeError('Acceptance checks failed; inspect the saved report')
            except Exception:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(log, args.output.with_suffix('.log'))
                raise
            finally:
                server.terminate()
                try:
                    server.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait()


if __name__ == '__main__':
    main()
