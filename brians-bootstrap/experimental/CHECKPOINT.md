# Bootstrap overhaul checkpoint

Historical interruption checkpoint. The workspace was subsequently recovered,
and the broader draft is now preserved in the main bootstrap directory on this
development branch. The observations below describe the earlier diagnostic
version, not the current acceptance result. See ../README.md and ../validation
for current scope and validation. No release or main-branch merge was made.

## Agreed target

- Factorio 2.1 with Space Age, Quality, Elevated Rails and Recycler; no third-party mods.
- Redesign is allowed, generally following the 32×32 chunk grid.
- Retain a staged starter, add a tier-upgrade phase, then move smelting outside.
- Coal should leave internal smelting and remain for recipe consumers and any retained backup boilers.
- All six Nauvis sciences: **5 automation, 6 logistic, 5 military, 12 chemical, 7 production, 7 utility assemblers**.
- Enemy-enabled play: military science, ammunition, defenses and production of Nauvis-available turrets.
- Infrastructure production: concrete/refined concrete, electric furnaces, solar/accumulators, nuclear construction and related supplies.
- Solar production as early as practical; no solar field required inside the bootstrap.
- Recommended technology/build order must respect milestone technologies.
- Rail-world resource imports: iron ore, copper ore, coal, stone and crude.
- Later, separately overhaul the overall city-block train system using the supplied newer vanilla LTN-style book. Its unloading templates use ordinary train stops, not the LTN mod.

## Science scale and resource budget

With ordinary assembler 2s, no modules/beacons, the requested counts give capacities of **45/45/45/45/47.25/47.25 packs per minute**. Purple/yellow have 5% headroom from rounding to whole assemblers.

45/min is a reasonable starter target. Producing 1,000 packs takes 22m13s before further lab/supply limits. Build purple/yellow support chains later; their material cost is the main scaling constraint, rather than the number of science assemblers.

Calculated from official 2.1.23 normal recipes, simultaneous 45/min of all six needs these interface rates, excluding productivity and mall stockpiling:

| Material | Items/s |
|---|---:|
| Iron plate, excluding steel input | 37.375 |
| Copper plate | 59.625 |
| Steel | 9.1875 |
| Stone brick | 6.25 |
| Raw stone | 3.75 |
| Coal as an ingredient | 10.25 |

Iron ore becomes **83.3125/s** when steel's iron is included. Water, oil, electricity and boiler fuel are additional.

## Durable changes in this branch

The experimental starter is separate from the original book:

- Phases 1–4 translated onto one shared chunk anchor.
- Phase 5 upgrades assembler 1 → 2, yellow surface belts/splitters → red, ordinary inserters → fast.
- Underground belts retain their tiers; different tiers can isolate overlapping tunnels.
- Long-handed inserters retain their reach.
- Cliff-explosive assemblers omitted.
- Generator and contract tests included.

Original-source translations, before removing historical export shift metadata:

| Phase | Add x | Add y |
|---|---:|---:|
| 1 | 1 | 47 |
| 2 | 4 | 43 |
| 3 | 4 | 14 |
| 4 | 4 | 4 |
| 5, derived from phase 4 | 4 | 4 |

FaTul top-level wire/schedule coordinate strings are **relative to minimum entity coordinates**, not absolute positions. A uniform translation must not also translate those strings. Cropping/removing entities can change the reference origin and needs separate care.

## Local draft work not safely saved

The offline workspace had a broader draft generator, external smelters/imports, a cropped science campus, a larger infrastructure mall and eight passing structural tests. Those files are not part of this durable checkpoint and should not be represented as a completed implementation.

Useful findings for continuing:

1. The existing `self-building-factory/book/science-research-(45-spm,-from-raw).json` already contains 5 military, 12 chemical, 7 production and 7 utility machines. Red and green are doubled and need careful reduction.
2. A trial production crop used source coordinates x=60..224, y=80..208, translated by (-60,-80), reserving 192×160 tiles. Remove fuel furnaces/old rail interfaces. This crop still requires deliberate input and fluid-interface engineering; do not treat cropping alone as a finished design.
3. Remove obsolete intermediate-export buffers and unwanted lab/productivity-module-2 production. Large buffers delay science startup.
4. Do not blindly remove every circuit behavior. Opening formerly disabled export pumps can drain useful fluid reserves. Preserve/rebuild oil controls deliberately.
5. Keep lubricant reserves small enough that initial filling does not consume excessive heavy oil. Check cracking and sulfuric-acid/battery supply under sustained load.
6. The existing red mall includes requester/buffer/active-provider chests. In Space Age, Logistics System requires space science. Replace or reroute those early dependencies rather than silently requiring a space platform. A batch chest is not an automatically interconnected mall.
7. Technology gating should follow the actual Space Age prerequisite graph; do not guess from item names. Express belts and power armor MK2 are not automatically off-planet recipes just because other high tiers are.
8. The reference book includes 2-locomotive/2-wagon cargo/fluid trains and generic item/fluid interrupt schedules. Renamed bootstrap stations need matching explicit schedules or updated interrupt destinations.

## Headless validation findings and limits

Factorio **2.1.23**, with the official expansion components enabled, was used locally. Eight contract checks passed for the wider draft: book encoding/reference integrity, science counts, starter alignment, tier/tunnel preservation, external smelter geometry, import/train consistency, Nauvis mall dependency filtering and chunk snapping.

A later test with real electrical connectivity and injected raw inputs produced all six science types. This was **not** proof of sustained 45/min or external fluid-interface correctness: water/crude were injected at machine inputs during that diagnostic test. It also had a long startup period.

The last recorded 10-minute ramp-up window gave these derived pack rates (craft counts multiplied by recipe yield):

| Science | Packs/min during diagnostic window |
|---|---:|
| Automation | 17.3 |
| Logistic | 45 |
| Military | 45 |
| Chemical | 22.6 |
| Production | 32.4 |
| Utility | 4.5 |

Robot frames were short of batteries. The acid plant was waiting for sulfur; this needs checking after startup, alongside oil/cracking behavior and competing buffers. Do not increase science-machine counts to hide an upstream supply problem.

For a proper acceptance test, supply only the declared external interfaces, give sufficient real power, drain science continuously, allow startup to settle and measure a separate steady-state interval. Test the old-to-new smelter handoff and the resource train service as well.

Runtime API notes for 2.1: `LuaEntity.fluidbox` is gone; use the current fluid-storage methods such as `get_fluid_box_neighbours`, `get_fluid_segment_id` and `set_fluid`. The crafting input inventory enum is `defines.inventory.crafter_input`. Match test tooling to the engine version.

## Recommended progression to document

1. Smelt 50 iron plates for Steam Power and 10 copper plates for Electronics; establish electricity, a lab, Automation and Logistics.
2. Steel/green science/construction; gun turrets, walls and ammunition as needed.
3. Solar Energy early; panels first, accumulators after battery production; retain night-time generation.
4. Railway/fluid handling as geography requires. Oil Gathering → power a real pumpjack and extract crude → Oil Processing. Begin with basic refining.
5. Plastics/sulfur/engines/advanced circuits → blue science; then red logistics, advanced refining, electric furnaces, construction robotics and inserter capacity.
6. Commission external smelting before retiring internal furnaces/fuel routes. Coal remains for recipe consumers.
7. Mine uranium using sulfuric acid for the Uranium Processing trigger; conventional processing/fuel cells can precede Kovarex. Add nuclear construction supplies.
8. Add production and utility science at the agreed counts; build only unlocked sections.
9. Space science/Logistics System and Vulcanus gates are later choices, not hidden bootstrap requirements.

## Next implementation work

Finish the integrated interfaces, balanced oil and automatic infrastructure production; verify sustained science output; then package a tested import string. Only afterwards migrate the wider city-block train system. No ready-to-use full overhaul or release should be claimed from this checkpoint.
