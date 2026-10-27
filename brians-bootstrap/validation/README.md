# Native verification — integrated bootstrap

Factorio **2.1.23**, official Space Age components only. Every report records the SHA-256 of its encoded blueprint. Inputs are saturated at the declared ports; electricity is supplied externally. Recipe-productivity research is disabled, inserter-capacity bonuses are limited to 1–3, and labs are drained so a research queue cannot limit production. No modules or beacons are installed.

| Phase | Belts | Sciences measured | Warmup | Sample | Packs/min, in science order |
|---|---|---|---|---|---|
| 2 | Yellow | Automation | 5 min | 5 min | 30 |
| 3 | Yellow | Automation, logistic, military | 15 min | 5 min | 30 / 30 / 30 |
| 4 | Yellow | First four, basic oil | 30 min | 10 min | 30 / 30 / 30 / 30 |
| 5 | Red | First four, advanced oil | 80 min | 10 min | 45 / 45 / 45 / 45 |
| 6 | Red | All six | 80 min | 18 min 40 sec | **45 / 45 / 45 / 45 / 45 / 45** |
| 7 | Blue | All six | 80 min | 18 min 40 sec | **45 / 45 / 45 / 45 / 45 / 45** |

The final two tests each produced **840 of every science pack**, with zero unpowered assembling machines. The 18-minute-40-second window covers complete crafting cycles for all six assembler-2 science recipes. Shorter windows can show synchronized bursts above or below machine capacity; they should not be interpreted as a change in sustained crafting speed.

The 80-minute cold start allows deep intermediate chains and transport buffers to settle. These tests do not say that the factory produces its final rate immediately after construction. The first four sciences can run while the later production chains fill.

Reproduce the two final runs using the runner's defaults:

```sh
python3 tools/check-bootstrap-engine.py --phase 6 --factorio /path/to/factorio
python3 tools/check-bootstrap-engine.py --phase 7 --factorio /path/to/factorio
```

For the earlier rows, pass the listed `--warmup-minutes` and `--sample-minutes` values. Early phases use assembler 1s and ordinary inserters; phase 5 upgrades them. All technologies are researched in the disposable test world, so recipe/milestone order is separately specified in the setup guide rather than claimed as a full survival-playthrough result.

## Reusable modules

`support.json` records native placement and throughput checks for:

- All seven bootstrap phases, including all 7,514 entities in each completed layout.
- User-tile electric banks: about 1,793 plates/min, 357 steel/min or 900 bricks/min in the short sampling window, against nominal 1,800 / 360 / 900 capacities.
- Solid unloading: 4,300 items/min from a continuously filled parked 2-2 train, using both wagons.
- Fluid unloading: 144,000 fluid/min in that fixture, using both wagons; travel time is excluded.
- Uranium processing: 20 isotope items/min across four centrifuges.
- Solar-panel batch production: 3 panels/min with an assembler 1.

Run these with `--scenario support`. Construction counts and throughput are independent checks; successful placement alone does not establish production rate.

`book-import.json` records native import/export of the complete deliverable, including all 82 leaf items and the upgrade/deconstruction planners. The import-string hash identifies the tested book. This can be reproduced with `--inspect`; that mode inspects topology and imports the whole book but does not perform a production benchmark.

The upstream mines, smelter-to-factory bus, train travel, power plant, manual batch-cell supplies and survival defense playthrough are outside these production fixtures. They still need to be commissioned in the player's world.
