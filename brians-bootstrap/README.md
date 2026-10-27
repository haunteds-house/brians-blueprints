# Brian's Bootstrap — Space Age 2.1

Development revision for **Factorio 2.1.23 + Space Age, Quality, Elevated Rails and Recycler**, with **no third-party mods**. The earlier editable starter is preserved in `source/early-game`. Do not mix these phases with an already-built older version: the exports now share an explicit chunk-grid anchor.

[Import string](space-age-bootstrap.txt) · [Connection coordinates](PORTS.md) · [Native validation reports](validation/)

## Progression

Reserve 96×96 tiles for the starter. Align phases 1–5 to the same chunk intersection. Later districts are **separate modules**, not overlays that demolish and reconnect the old factory automatically. Leave corridors between them for belts, power and access.

| Stage | Purpose |
|---|---|
| 1 | Hand-fed smelting and first electricity |
| 2 | Belts, gears and automation science |
| 3 | Construction supplies and logistic science; start solar-panel production |
| 4 | Oil, chemical science, railway supplies and construction robots |
| 5 | Upgrade to assembler 2s, red surface belts/splitters and fast inserters |
| 6 | Raw-resource trains and external electric smelting |
| 7 | Separate six-science campus, reserving 192×160 tiles |
| 8 | Separate infrastructure mall, including defenses, concrete and nuclear supplies |
| Early/support cells | Small batch producers for solar, defenses and infrastructure before the large mall is built |

Use the upgrade planner on existing entities in phase 5; placing a later blueprint alone does not upgrade a built machine. **Underground belts retain their tiers** because some routes braid yellow and red tunnels. A blanket tunnel upgrade can silently connect different endpoints. Long-handed inserters also retain their reach.

The larger infrastructure mall is deliberately a later district, not something to construct before green science. Its former requester inputs are ordinary chests, and its active-provider/buffer chests have been replaced. It requires no Logistics System or third-party mod. Local feed belts or manual supplies are still needed at those former requester inputs; the small support cells explicitly use batch input chests.

## Science scale

Normal-quality assembler 2s, no modules or beacons:

| Science | Assemblers | Machine capacity, packs/min |
|---|---:|---:|
| Automation | 5 | 45 |
| Logistic | 6 | 45 |
| Military | 5 | 45 |
| Chemical | 12 | 45 |
| Production | 7 | 47.25 |
| Utility | 7 | 47.25 |

Size supporting supply for **45/min of each**. Purple/yellow have 5% machine headroom because their exact 45/min count is fractional. These are machine capacities, not measured sustained rates when supply, routing or power is insufficient. Producing 1,000 packs at 45/min takes 22 minutes 13 seconds; lab capacity and research speed may impose further limits.

At simultaneous 45/min of all six, normal recipes without productivity need approximately **37.375 iron plates/s, 59.625 copper plates/s, 9.1875 steel/s, 6.25 bricks/s, 3.75 raw stone/s and 10.25 coal/s** at the production interfaces. Including steel's iron, this is **83.3125 iron ore/s**. Water, oil and electricity are additional requirements. Coal here is an ingredient and excludes boiler/furnace fuel. Actual research does not continuously consume every science equally.

The scale is appropriate for a bootstrap: enlarge its supply progressively rather than constructing all purple/yellow support production early. Utility science's processing units, robot frames and low-density structures are particularly expensive. Keep mall buffers limited so stockpiling does not consume every circuit and plate needed for research.

## Recommended technology and milestone order

Follow technology prerequisites; the following is a priority order, not a replacement for the technology tree. Reapply recipe settings after unlocks where necessary.

1. **First smelting:** smelt 50 iron plates for Steam Power and 10 copper plates for Electronics. Build the first power plant and lab, and handcraft the initial science needed for Automation. Research Logistics and establish powered mining.
2. **Construction/green:** Steel Processing, Logistic Science Pack, Automation 2 and Fast Inserter. Research gun turrets, walls and ammunition improvements early if enemies threaten the starting deposits. Use a dedicated turret cell instead of repeatedly changing the repair-pack assembler's recipe.
3. **Early solar:** prioritize Solar Energy once green science and steel are available. The batch cell makes panels immediately; continue steam at night until batteries and accumulators are available. No solar/accumulator field is included inside the bootstrap.
4. **Rail and oil:** Railway, engines, rail signals and fluid handling as needed for remote deposits. Research **Oil Gathering**, place and power a pumpjack on actual crude, and **extract oil** to unlock **Oil Processing**. Start with basic refining; do not wait for blue science or advanced refining to bootstrap petroleum.
5. **Blue and tier upgrade:** plastics, sulfur, engines and advanced circuits → Chemical Science Pack. Prioritize Logistics 2, Advanced Oil Processing, Advanced Material Processing 2 and construction robotics as their prerequisites allow. Research inserter capacity bonuses 1–3. Switch to advanced refining with cracking and a lubricant reserve.
6. **External electric smelting/defense:** provide sufficient electricity before replacing fuel smelting. Produce electric furnaces, then connect external plates/steel/bricks. Add flamethrower and laser turret production as unlocked; allow for laser power demand. Begin accumulator production once batteries are available.
7. **Nuclear/purple/yellow:** supply sulfuric acid to uranium miners and mine actual uranium ore for the **Uranium Processing** trigger. Conventional processing and fuel cells can start nuclear power before Kovarex. Build reactor, centrifuge, heat exchanger, heat pipe and steam turbine supplies as needed. Production science needs productivity modules/electric furnaces/rails; utility science needs robotics, processing units and low-density structures.
8. **Space handoff:** Space Age's rocket route can use red/green/blue science; purple/yellow are not rocket prerequisites. Logistics System requires space science. Cliff explosives and artillery require Vulcanus progression and are omitted from the Nauvis-only mall. Other space/planet-gated recipes are filtered using a snapshot of the official 2.1.23 technology graph, including prerequisites.

Do not delete refinery fluids as the normal balancing mechanism. Commission advanced oil, cracking and lubricant storage before retiring the temporary starter refinery.

The science district accepts water at **(0.5,137.5)** and crude at **(0.5,143.5)**. Its eight advanced refineries plus one basic refinery provide petroleum headroom without changing the science-machine counts. Allow up to 180 crude/s with all refineries active. Heavy-oil and lubricant working reserves are limited to 1,000 fluid each; obsolete acid export buffers are replaced by pipes so batteries do not wait for 125,000 fluid of storage to fill.

## External smelting

The iron/copper/steel bank occupies **32×128** tiles and contains **48 electric furnaces**, with no fuel belt. The dedicated brick bank is **32×64** with **24 furnaces**, avoiding an idle extra column length.

| Local interface | Use |
|---|---|
| (16.5, 0.5), southbound | One red input belt |
| (9.5, 127.5), southbound | Left output belt |
| (23.5, 127.5), southbound | Right output belt |

Iron/copper output is 15/s per belt. For steel, feed **iron plates**, giving 3 steel/s per belt. The shorter brick bank accepts 30 stone/s and produces 15 bricks/s; its output ports are at y=63.5. Outputs remain separate; do not merge both onto the same lane. Fully active furnaces alone use **8.64 MW per bank**, plus inserters and drain; the brick bank uses 4.32 MW.

For the six sciences alone, allow roughly three iron-plate banks (split between direct iron demand and steel input), two copper banks, two steel banks and one brick bank. Mall demand needs additional supply. Install banks progressively as demand grows.

Electric furnaces are 3×3, so they do not directly fit the old 2×2 furnace positions. Commission external smelting first, connect its outputs to the existing plate/steel/brick belts, and disconnect old ore/fuel inputs. Use the furnace-only deconstruction planner over the starter, then remove disused fuel inserters and coal branches manually. Coal remains for plastic, grenades/explosives and any retained backup boilers. Once the new science district works, retire the starter science/labs so both installations are not counted as the 5/6/5/12/7/7 layout.

## Raw-resource trains

Five unloading stations use geometry from `LTN Style Train System Blueprint.txt`: iron ore, copper ore, coal, stone and crude oil. They use vanilla train stops, resource-specific names and train limit one. Solid unloaders have three red output belts; connect southbound ports **(18.5,63.5), (22.5,63.5), (27.5,63.5)**. Crude has a pipe outlet at **(22.5,63.5)**. Supply electricity to each station.

At inserter-capacity bonuses 1–3, the solid unloader measured about **71.7 items/s**, below the three belts' combined 90/s capacity. The all-six-science iron requirement exceeds one such unloader: use parallel iron unloading or verify higher inserter-capacity upgrades before relying on one station. Station limits and fleet size must support that expansion.

The resource-specific **2-2 trains** have explicit schedules:

- `[item=RESOURCE] Outpost load` → depart full.
- `[item=RESOURCE] Bootstrap unload` → depart empty.
- Crude uses `[fluid=crude-oil]` names.

Fuel locomotives with coal until an automated fuel-loading point is built. These starter trains do not require the reference book's rocket-fuel interrupt or its generic dispatcher. Place them on compatible existing rails, and match outpost loaders to their wagon positions.

Connect the rail approaches and output belts/pipes manually. Ore goes to external smelting; stone goes to bricks and raw-stone consumers; coal goes to chemistry/military and backup boilers; crude goes to the oil district. Remote mining, power and perimeter defenses remain site-specific.

Size the fleet for the actual round trip: required trains ≈ ceil(items/s × trip seconds ÷ cargo per train). Two ordinary cargo wagons hold 4,000 iron/copper ore. At the six-science iron demand, a 120-second round trip needs three such trains before allowing for delays. Belt capacity alone does not guarantee train throughput.

The existing overall city-block books and their dispatch logic are unchanged. Their migration to the newer interrupt-based system is the subsequent task.

## Infrastructure

The large belt mall includes concrete/refined concrete, gun/flamethrower/laser turrets, ammunition, electric furnaces, solar/accumulators, robots, nuclear construction and fuel handling. It retains the existing city-block resource interfaces while the larger train overhaul is pending. Build by unlocked recipe rather than constructing the entire district at once.

The small support cells use ordinary input/output chests. Supply ingredients manually or connect local feed belts; **these cells are batch producers, not an automatically interconnected mall**. Outputs are limited to one stack. Connect water to the east pipe for concrete/refined concrete. The four-centrifuge uranium-processing module accepts ore at (10.5,0.5), with separate filtered isotope chests. Nuclear construction cells are not a reactor power plant, uranium mine or complete enrichment installation.

## Development

```sh
python3 tools/build-bootstrap.py
python3 tools/fatul.py encode brians-bootstrap/book brians-bootstrap/space-age-bootstrap.txt
python3 -m unittest discover -s tools/bootstrap-tests
```

A real Factorio 2.1.23 test, using only official expansion components, measured **45 / 45 / 45 / 45.2 / 45.6 / 45.3 packs/min** over ten minutes after an 80-minute cold-start warmup. Empty belts, circuits, batteries and machine input buffers take time to fill. No recipe-productivity research, modules or beacons were used; inserter capacity was limited to bonuses 1–3. Inputs were saturated at the declared ports, power was unlimited externally, and labs were drained to keep demand active. This tests the science district, not the upstream mines, fleet or power plant.

Reproduce native tests with an official Space Age headless installation:

```sh
python3 tools/check-bootstrap-engine.py --factorio /path/to/factorio
python3 tools/check-bootstrap-engine.py --scenario support --factorio /path/to/factorio
```

Results and blueprint hashes are committed under `validation/`. The support test checks smelter throughput, a continuously supplied parked 2-2 train, uranium processing, solar-panel batch production, starter-phase placement and large-mall placement. Large-mall production rates and a full survival playthrough have not been validated. The runner creates disposable worlds and does not load or change your save.

The generator preserves the original editable starter sources and reuses the existing larger factory layouts. See [PORTS.md](PORTS.md) for the science district's explicit local interfaces. Do not confuse machine counts or successful blueprint import with a measured sustained production result. Attribution and the repository license continue to apply.
