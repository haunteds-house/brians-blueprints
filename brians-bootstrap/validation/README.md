# Native verification — integrated bootstrap

Factorio **2.1.23**, official Space Age components only. Reports record encoded blueprint hashes. Where only labels/descriptions changed, reports retain the original test hash and record the current hash after checking identical entities, wires and grid settings. Historical support reports retain the hashes they originally tested; phase-5 yellow placement/production is checked by the newer science run. Inputs are saturated at the declared ports; electricity is supplied externally. Recipe-productivity research is disabled, inserter-capacity bonuses are limited to 1–3, and labs are drained so a research queue cannot limit production. No modules or beacons are installed.

| Phase | Belts | Sciences measured | Warmup | Sample | Packs/min, in science order |
|---|---|---|---|---|---|
| 2 | Yellow | Automation | 5 min | 5 min | 30 |
| 3 | Yellow | Automation, logistic, military | 15 min | 5 min | 30 / 30 / 30 |
| 4 | Yellow | First four, basic oil | 30 min | 10 min | 30 / 30 / 30 / 30 |
| 5 | Yellow | First four, advanced oil | 36 min | 10 min | 45 / 45 / 45 / 45 |
| 6 | Red | All six | 80 min | 18 min 40 sec | **45 / 45 / 45 / 45 / 45 / 45** |
| 7 | Blue | All six | 80 min | 18 min 40 sec | **45 / 45 / 45 / 45 / 45 / 45** |

The final two tests each produced **840 of every science pack**, with zero unpowered assembling machines. The 18-minute-40-second window covers complete crafting cycles for all six assembler-2 science recipes. Shorter windows can show synchronized bursts above or below machine capacity; they should not be interpreted as a change in sustained crafting speed.

The 80-minute cold start allows deep intermediate chains and transport buffers to settle. These tests do not say that the factory produces its final rate immediately after construction. The first four sciences can run while the later production chains fill.

Reproduce the two final runs using the runner's defaults:

```sh
python3 tools/check-bootstrap-engine.py --phase 6 --factorio /path/to/factorio
python3 tools/check-bootstrap-engine.py --phase 7 --factorio /path/to/factorio
```

The phase-5 yellow-belt result uses the difference between the native fixture’s minute-36 and minute-46 production-statistics snapshots, with 450 of every early science and no unpowered machines. It replaces the earlier red-belt phase-5 benchmark. Reproduce with `--phase 5 --warmup-minutes 36 --sample-minutes 10 --timeout 1800`.

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

`book-import.json` records native import/export of the complete deliverable, including all 85 leaf items and the upgrade/deconstruction planners. The import-string hash identifies the tested book. This can be reproduced with `--inspect`; that mode inspects topology and imports the whole book but does not perform a production benchmark.

The upstream mines, smelter-to-factory bus, train travel, power plant, manual batch-cell supplies and survival defense playthrough are outside these production fixtures. They still need to be commissioned in the player's world.


## First-launch workshop

Run `--scenario launch --timeout 1800` to test the finite workshop and launch pad. The fixture researches only the Rocket Silo prerequisite closure plus assembler 2s, fast inserters and medium poles; it asserts that this closure uses automation/logistic/chemical science only. Milestone triggers and research costs are bypassed in this disposable test, so it is not a timed research or survival run.

The compact workshop, research annex and launch pad each occupy one 32×32 chunk. The fixture supplies the declared external ingredient checklist and external electricity/fluids. A scripted courier transfers only items actually made into output chests to the next batch's input chest, modeling the documented manual work. It stops each batch at its target (including the fluid-only solid-fuel cell), consumes the crafted silo and landing-pad items to build the pad blueprint, then uses the pad's inserter to feed 50 rocket parts. It loads the crafted starter pack, orders a launch and checks that the destination platform has a hub. No processing units, electric engines, concrete, rocket fuel, silo, starter pack or rocket parts are injected as external supplies.

The reported workshop elapsed time starts with researched technologies, construction ghosts revived and all external ingredients available. It excludes mining, research, factory construction, fluid connection work, manual travel and enemy defense. The eight-hour splits in LAUNCH.md remain planning targets pending a full achievement-eligible survival playthrough.


## Silo research capacity

Run `--scenario research --timeout 1800` for the independent 36-lab annex. The fixture unlocks prerequisites, supplies exactly 28 of each red/green/blue science to each input chest, then actually researches Rocket Silo. It supplies no further packs and does not inject research progress. Existing nine labs are excluded from this fixture. This measures lab consumption, separately from the science-production tests which drain labs.

`silo-research.json`: 1,000 silo research units completed in **27m49s** with 36 labs, finite chest-fed packs and research-speed modifier zero.

`first-launch.json`: the 92-entity workshop completed its exact batches, the five-entity pad was built using the crafted silo/landing-pad items, and the rocket delivered the crafted starter pack to a platform with a hub. Total fixture time was **32m06s**, with researched technologies and all external ingredients available at the start. This is not a start-to-rocket run.
