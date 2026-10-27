# Experimental Space Age starter

This is an archived **partial development checkpoint**. Use the current [bootstrap book and setup guide](../README.md) for the expanded overhaul.

The book contains the first four starter phases with a shared chunk-grid anchor, plus a fifth phase for assembler 2s, red surface belts/splitters and fast inserters. A matching upgrade planner is included. Underground tiers and long-handed inserters retain their routing/reach. Cliff-explosive production is omitted because Space Age gates it behind Vulcanus.

Reserve 96×96 tiles and place every starter phase on the same chunk intersection. Do not overlay these exports onto an older bootstrap without checking alignment. Apply the upgrade planner to existing entities for phase 5; placing a later blueprint alone does not upgrade built machines.

This archived subset does not include the expanded main book. External smelting, imports, six-science production, infrastructure mall integration and the larger city-block train overhaul are **not included in this saved subset**. See [CHECKPOINT.md](CHECKPOINT.md) for the agreed scope and unfinished validation.

Build an import string with the existing repository tool:

```sh
python3 tools/build-bootstrap-starter.py
python3 -m unittest discover -s tools/bootstrap-tests -p test_starter.py
python3 tools/fatul.py encode brians-bootstrap/experimental/book bootstrap-experimental.txt
```

The local workspace became unavailable during development. The starter subset was reconstructed through the GitHub connector; its anchor alignment and wire endpoints were checked again. The reconstructed subset is covered by `test_starter.py`; subsequent work recovered the full draft and continued engine validation.
