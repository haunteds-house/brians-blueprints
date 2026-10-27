# Bootstrap connections

Coordinates are local tile positions in the exported blueprint. Align its absolute 32-tile grid first; apply the same translation to every coordinate below. South means increasing y, east increasing x. Connect power and unlock the recipes before commissioning a district. Later modules are separate placements and require connecting belts/pipes manually.

## Science campus — 192×160 reservation

This district receives externally smelted material. There is no ore or fuel-smelting input. Multiple ports for one material feed different production branches; supply every listed port. Do not replace them with a single belt feeding only the first port.

| Input | Local belt position(s) | Direction |
|---|---|---|
| Iron plate | (2.5,0.5), (3.5,0.5), (4.5,0.5), (5.5,0.5) | South |
| Iron plate | (4.5,11.5), (4.5,12.5) | East |
| Copper plate | (115.5,0.5), (116.5,0.5), (117.5,0.5), (118.5,0.5) | South |
| Steel plate | (0.5,0.5) | South |
| Steel plate | (4.5,13.5) | East |
| Coal | (4.5,47.5) | East |
| Coal | (19.5,3.5) | South |
| Stone | (85.5,3.5) | South |
| Stone brick | (108.5,3.5) | South |
| Water | Pipe (0.5,137.5) | Into district |
| Crude oil | Pipe (0.5,143.5) | Into district |

Some belt ports sit inside the reserved rectangle because the former railway/smelting district was removed. Bring feeds through that cleared western/northern space. Split supply between ports without starving the far end of a shared belt. The acceptance test saturates all ports independently; it does not demonstrate a particular upstream belt bus.

Connect the campus power poles to the external power supply. There is no power plant in this module. Final science belts feed the retained labs; the engine benchmark removes packs at the labs to measure production without a research queue limiting demand.

## External electric smelting

| Bank | Input, southbound | Output, southbound | Reservation |
|---|---|---|---|
| 48 furnaces: iron/copper/steel | (16.5,0.5) | (9.5,127.5), (23.5,127.5) | 32×128 |
| 24 furnaces: stone brick | (16.5,0.5) | (9.5,63.5), (23.5,63.5) | 32×64 |

Use iron ore for iron plate, copper ore for copper plate, iron plate for steel, and stone for bricks. Furnace recipes select automatically. Keep the two outputs separate to preserve lane capacity. Connect the central medium-pole chain to electricity.

## Raw train imports

Each solid unloading station exposes southbound red belts at **(18.5,63.5), (22.5,63.5), (27.5,63.5)**. Connect all three. Crude oil uses the pipe at **(22.5,63.5)**. Connect electricity to the station poles and join the rail approaches to your railway. Stations are sized for the supplied two-locomotive/two-wagon trains. Outpost loading stations are site-specific and must match those wagon positions.

## Batch infrastructure and uranium

Small assembler cells take ingredients in the north iron chest **(8.5,5.5)** and place one stack of output in the south wooden chest **(8.5,11.5)**. Concrete/refined-concrete cells take water through the east pipe **(11.5,8.5)**. Connect the small pole to electricity. These are manual or locally belt-supplied cells, with no requester-chest dependency.

The four-centrifuge module takes uranium ore southbound at **(10.5,0.5)**. Each centrifuge outputs U-238 into the upper steel chest and U-235 into the chest one tile below it. Collect both isotopes; a full output chest eventually stops processing. Connect the medium-pole chain to electricity.

The large infrastructure mall retains the original red-mall resource interfaces and includes ordinary chests at former requester inputs. Refill these locally. It is a separate later district, not a fully connected extension of the 96×96 starter. Build only the recipes you have unlocked and need.
