# First launch before eight hours, then expansion

The book now builds toward **one Space Age rocket carrying a platform starter pack**, before adding production/utility science. This is an eight-hour route design, not a verified eight-hour survival run. Use default research cost and normal-quality recipes. Construction, mining, travel, enemy pressure and resource placement determine the actual completion time.

## Eligible map

Start Freeplay with achievement-eligible settings and check the achievement tracker before committing to the run. The standard Rail World preset reduces enemy settings and is unsuitable for There is no spoon. Start from Default, increase resource patch size/richness and adjust resource frequency for rail-world-style deposits, while retaining default enemy and pollution settings. Do not use console commands, editor mode or third-party gameplay mods in the achievement save. The supplied headless test commands belong in disposable test worlds only.

## Route and time budget

These are **planning targets**, not recorded splits. Aim to launch by 7:00, leaving an hour for recovery. Keep unnecessary military research, construction stockpiles and solar production bounded. Defend the factory; military science is available but the silo does not consume it.

| Game clock target | Action |
|---|---|
| 0:00–0:45 | Phase 1, steam, powered mining, labs and automation |
| 0:45–1:30 | Phases 2–3, green science, steel, turrets and ammunition; start only the rail imports required by distant deposits |
| 1:30–2:30 | Pump actual oil, phase 4 basic refining, plastic, sulfur, red circuits and blue science |
| 2:30–4:30 | Phase 5 assembler-2/fast-inserter upgrade; advanced oil; start launch workshop batches as recipes unlock; research the silo prerequisite tree |
| 4:30–5:30 | Finish silo research and ingredient reserves; build foundation, starter pack, silo and landing pad |
| 5:30–7:00 | Assemble 50 rocket parts, load starter pack, create platform and launch |
| 7:00–8:00 | Recovery allowance; no optional factory expansion before launch |

Phase 5 keeps **yellow belts** and upgrades crafting machines/inserters. A complete red-belt replacement is deferred to phase 6. The launch workshop itself has no belts. Reserve its **32×32** annex separately on the chunk grid; the science factory still occupies its original **160×128** reservation. Reserve a further **32×32** launch pad and **32×32** research annex. Do not overlay either annex onto the science factory.

### Research priority

Follow prerequisites in the technology tree; this is a priority list, not permission to skip dependencies:

1. Automation, Logistics, Logistic Science Pack, steel and essential defensive unlocks. Electric Energy Distribution 1 commissions the marked military pole. Railway/engines/fluid handling are priorities only when the selected map needs remote imports.
2. Oil Gathering → run a pumpjack on actual crude → Oil Processing, then plastics, sulfur, engines, advanced circuits and Chemical Science Pack. Basic refining starts blue science.
3. Automation 2, Fast Inserter, Advanced Oil Processing and lubricant. Unlock Processing Unit, Electric Engine, Concrete, Flammables/Rocket Fuel and Low Density Structure; run their workshop cells while research continues.
4. Complete **all** Rocket Silo prerequisites, including **Logistic Robotics** and **Advanced Material Processing 2**. Researching electric furnaces is mandatory; physically replacing every fuel furnace before launch is optional. Logistic Robotics does not require building an operating bot network for the workshop.
5. Rocket Silo: **1,000 automation + 1,000 logistic + 1,000 chemical packs**. At 45/min this batch takes at least 22m13s to manufacture once settled. Use the 36-lab annex below for research capacity; the prerequisite tree is additional. Reserve these packs and keep labs fed; military packs do not substitute for them.
6. After the silo unlock, craft platform foundation, starter pack, silo and landing pad in the reserved cells. Launch before researching purple/yellow science, nuclear/Kovarex, Logistics 3 or optional productivity upgrades.

Solar panel production remains available early, but do not wait for a large solar field or replace reliable steam solely for the deadline. Keep the existing external fuel smelting until electric banks and adequate power are actually commissioned. Retire the internal hand-fed starter cell once external supply is reliable. A missing entity in a later blueprint does not demolish it.

## Silo research annex

The original nine labs alone take about **111 minutes** for the 1,000-unit, 60-second silo technology without research-speed bonuses. Use the supplied **32×32, 36-lab research annex** for the deadline; with the existing nine labs there are 45 in total. The annex alone has nominal capacity 36 units/min (27m47s for the silo), while all 45 can match 45 science/min. Research-speed bonuses reduce these durations further; startup, loading and interruptions add time.

Each annex lab has a wooden input chest three tiles north. For a simple finite silo batch, put **28 automation + 28 logistic + 28 chemical packs in each of the 36 chests**: 1,008 of each pack in total, with eight spare. Select Rocket Silo after its prerequisites. Existing belt-fed labs can help as supplies allow, but the annex does not depend on them. Connect power at **(6.5,4.5)**; active lab demand is 2.16 MW plus inserters. Packs must be manufactured and transferred from the science factory; the annex is not a new science-production campus. Reuse these labs for postlaunch research or replace them with a larger belt-fed laboratory section.

## Launch workshop

All thirteen cells are ordinary **batch producers**, using assembler 2s or one chemical plant. Supply north steel chests, collect south steel chests, and transfer intermediate batches between the listed cells manually. No requester chests, bots or continuous ingredient routing is supplied. Chests are intentionally not stack-limited: the silo construction batch needs many stacks. Load exactly the listed solid quantities to bound production. Cell 6 consumes only fluid: collect 500 solid fuel, then clear its recipe to stop that batch; otherwise it keeps using light oil.

Coordinates are local to the workshop's north-west chunk corner. Connect power at **(2.5,4.5)**. Each machine has input at `(x,y−3)` and output at `(x,y+3)`.

| ID | Machine center | Product target | Put in north chest; fluids supplied separately |
|---|---|---|---|
| 0 | 4.5,4.5 | 140 processing units | 2,800 green circuits + 280 red circuits; 700 acid |
| 1 | 12.5,4.5 | 140 processing units | Same as cell 0 |
| 2 | 20.5,4.5 | 100 electric engines | 200 green circuits + 100 engines; 1,500 lubricant |
| 3 | 28.5,4.5 | 100 electric engines | Same as cell 2 |
| 4 | 4.5,12.5 | 50 low-density structures | 1,000 copper plates + 100 steel + 250 plastic |
| 5 | 12.5,12.5 | 1,200 concrete | 120 iron ore + 600 stone bricks; 12,000 water |
| 6 | 20.5,12.5 | 500 solid fuel | No solids; 5,000 light oil |
| 7 | 28.5,12.5 | 50 rocket fuel | Transfer 500 solid fuel from cell 6; 500 light oil |
| 8 | 4.5,20.5 | 1,200 copper cable | 600 copper plates |
| 9 | 12.5,20.5 | 60 platform foundation | 1,200 steel + 1,200 cable from cell 8 |
| 10 | 20.5,20.5 | 1 starter pack | 20 steel + 20 processing units + 60 foundation |
| 11 | 28.5,20.5 | 1 rocket silo | 1,000 steel + 200 processing units + 200 electric engines + 100 pipes + 1,000 concrete |
| 12 | 4.5,28.5 | 1 landing pad | 25 steel + 10 processing units + 200 concrete |

Fluid ports: acid **(7.5,4.5)** and **(15.5,4.5)**; lubricant **(23.5,4.5)** and **(31.5,4.5)**; water **(15.5,12.5)**; light oil **(23.5,11.5)** and **(31.5,12.5)**. Connect external pipes to the appropriate networks in the phase-5 oil district. These are additional workshop taps, not new connections to the science factory's crude inlet. Keep different fluids separate. Crack only surplus light oil while reserving 5,500 for fuel production; provide extra petroleum/acid/lubricant as needed without starving blue science. Fluid numbers are recipe consumption; pipe fill is extra.

Start cells 0–8 as soon as their recipes unlock. In ideal uninterrupted crafting, the two processing-unit cells take about 31m07s and the two electric-engine cells 22m13s, before inserter/startup delays. Concrete takes 26m40s. These can overlap research. Foundation starts only after silo research and takes 13m20s of ideal crafting. Do not postpone the expensive steel/circuit reserves until that unlock.

### External shopping list

For the complete batch, including silo construction, landing pad, first rocket and starter pack:

| External ingredient | Total |
|---|---:|
| Green circuits | 6,000 |
| Red circuits | 560 |
| Engines | 200 |
| Copper plates | 1,600 |
| Steel plates | 2,345 |
| Plastic | 250 |
| Iron ore | 120 |
| Stone bricks | 600 |
| Pipes | 100 |
| Sulfuric acid | 1,400 |
| Lubricant | 3,000 |
| Water | 12,000 |
| Light oil | 5,500 |

This list begins at the workshop interfaces. It excludes materials already consumed making circuits/engines/plastic, the workshop/pad construction entities, research packs, mining/smelting, fuel, power and defenses. Take bounded surplus batches from the science supply or provision additional producers; continuously diverting its circuit output can delay research. Do not mix workshop and science budgets. In particular, the core’s engine line is sized for blue science: reserve the workshop’s 200 engines before the uninterrupted silo-research batch, temporarily pause blue production to collect them, or add engine capacity. Diverting them while expecting full blue output would double-count that line.

`launch-plan.json` is the generated, machine-readable checklist. The checked-in recipe snapshot comes from official 2.1.23 Space Age prototypes, without modules or recipe-productivity bonuses.

## Assemble and launch

1. Transfer workshop silo and landing-pad items to the **Phase 5c** blueprint. Connect power at **(4.5,8.5)**; the silo can draw 4 MW while working, in addition to the factory.
2. Put **50 processing units + 50 low-density structures + 50 rocket fuel** in the west chest at **(4.5,10.5)**. The fast inserter feeds the silo's rocket-part recipe. These are the remaining 50 processing units after 200 silo + 20 starter-pack + 10 landing-pad units.
3. Wait for the rocket to become ready. Put **one space platform starter pack** into **rocket cargo** through the silo UI, rather than the west ingredient chest.
4. Select **New platform**, name the platform, and launch. Confirm the rocket actually launches before eight hours and check the achievement tracker. Researching the silo or merely finishing its 50 parts does not complete the achievement.

## After launch

1. **Phase 6:** apply the yellow→red belt planner across the main factory (including undergrounds/splitters), retaining assembler 2s and fast inserters. Add the seven purple and seven yellow assemblers and their shared intermediates in the original reservation. All six sciences then target 45/min. This is the completed Nauvis bootstrap.
2. Commission external electric smelting progressively, remove obsolete fuel supply and scale train imports/power for the full six-science load. Add solar/accumulators, concrete, turrets, nuclear and construction robotics as useful. Keep enough defense and material reserves for off-world time.
3. Build orbital science production and ship its packs down to the existing labs. The first starter platform alone is not an operating space-science factory; the orbital build remains separate future work. Use postlaunch space science for Logistics System when desired.
4. **Optional phase 7:** blue belts only after a measured bottleneck justifies their cost. This upgrade alone leaves science crafting capacity at 45/min. City-block train dispatch redesign remains the next separate project.


Reference rules: [official achievement eligibility](https://wiki.factorio.com/Achievements), [Space Age rocket/silo requirements](https://wiki.factorio.com/Rocket_silo), and [platform starter packs](https://wiki.factorio.com/Space_platform_starter_pack). Recipe quantities are pinned separately to the checked-in official 2.1.23 prototype snapshot.
