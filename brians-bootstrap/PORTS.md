# Bootstrap connections

All coordinates are local to the **same 160×128 bootstrap anchor**. South increases y; east increases x. Every phase snaps to the same 32-tile grid. Bring external feeds to the existing ports as the relevant production chain is added. Some ports are not present in the earliest phases.

## Material inputs

Multiple ports for one material feed different shared production branches. Supply all ports present in the phase; feeding only the first one does not supply the entire factory. These are plates, steel and bricks, not ore.

| Material | Belt position(s) | Direction |
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
| Water | Pipe (0.5,97.5) | Into factory |
| Crude oil | Pipe (0.5,99.5) | Into factory |

Use the cleared northern/western access corridors for feeds to the internal belt ports. Split supplies without starving downstream branches. The acceptance tests saturate each port independently; they do not demonstrate a particular supply-bus arrangement.

Connect external power at the pole **(1.5,1.5)**. Steam/solar/nuclear power plants are outside the bootstrap. At the green-science milestone, upgrade the pole **(18.5,26.5)** to medium for the military input inserters. Use the later phase's additional marked medium poles as shown.

## Construction bay

The ten integrated batch cells have centers at x=111.5, 117.5, 123.5, 147.5 and 153.5, on rows y=108.5 and 120.5. Their ordinary input chests are three tiles north of the assembler; limited output chests are three tiles south. Supply ingredients manually or through local belts. The rest of the science production is belt-fed.

The first-smelting cell occupies the southwest pocket and accepts hand-fed ore/coal in its ordinary chests. It is retained through phase 4 and retired in phase 5. Expand ore smelting outside this cell before trying to sustain science. Later phases do not automatically remove omitted entities.

## Electric-furnace banks

The supplied 6×8 electric tile repeats six times per short row. The 48-furnace bank is physically 40×32; the 24-furnace brick bank is 40×16. Both reserve **64×32** on the chunk grid.

| Interface | Position | Direction |
|---|---|---|
| Ore/plate input, both banks | (39.5,0.5) | South |
| Row 1 output | (0.5,6.5) | West |
| Row 2 output | (0.5,14.5) | West |
| Row 3 output, 48-furnace bank | (0.5,22.5) | West |
| Row 4 output, 48-furnace bank | (0.5,30.5) | West |

Input iron ore, copper ore, iron plates for steel, or stone for bricks. Connect the medium-pole network to electricity. Keep row outputs separate or merge with splitters. All four row outputs side-loaded onto the same lane would bottleneck the bank.

## Raw train imports

Each solid unloading station has southbound belts at **(18.5,63.5), (22.5,63.5), (27.5,63.5)**. Connect all three. Crude uses the pipe at **(22.5,63.5)**. Connect station electricity and rail approaches. Match outpost loaders to the supplied two-locomotive/two-wagon train positions and schedule names.

## Other infrastructure

Optional batch cells take ingredients in the north iron chest **(8.5,5.5)** and place one stack of output in the south wooden chest **(8.5,11.5)**. Concrete/refined-concrete cells take water through **(11.5,8.5)**. Connect their poles to electricity. These cells have no requester-chest dependency.

The four-centrifuge module takes uranium ore southbound at **(10.5,0.5)**. Each centrifuge outputs U-238 into the upper steel chest and U-235 into the chest immediately below. Collect both isotopes before storage fills. Connect the pole chain to electricity; the module does not include a uranium mine or reactor plant.
