#!/usr/bin/env python3
"""Rebuild the experimental starter subset; the full overhaul is unfinished."""
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "brians-bootstrap/experimental/book"
VERSION = (2 << 48) | (1 << 32) | (23 << 16)
TIERS = {"assembling-machine-1": "assembling-machine-2",
         "transport-belt": "fast-transport-belt",
         "splitter": "fast-splitter", "inserter": "fast-inserter"}
OFFSETS = [(1, 47), (4, 43), (4, 14), (4, 4), (4, 4)]
LABELS = ["First smelting", "Automation", "Construction and green science",
          "Oil, blue science and rail supplies",
          "Red belts, assembler 2s and fast inserters"]


def write(name, data):
    DEST.mkdir(parents=True, exist_ok=True)
    (DEST / name).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def build():
    for i in range(1, 6):
        path = ROOT / f"brians-bootstrap/source/early-game/phase-#{min(i, 4)}.json"
        bp = copy.deepcopy(json.loads(path.read_text())["blueprint"])
        dx, dy = OFFSETS[i - 1]
        bp["entities"] = [e for e in bp["entities"]
                          if e.get("recipe") != "cliff-explosives"]
        for e in bp["entities"]:
            e["position"]["x"] += dx
            e["position"]["y"] += dy
            if i == 5:
                e["name"] = TIERS.get(e["name"], e["name"])
        # FaTul wire/schedule coordinates are relative to minimum entity
        # coordinates; uniform translation leaves those references unchanged.
        bp.pop("shift_x", None)
        bp.pop("shift_y", None)
        bp["version"] = VERSION
        bp["snap-to-grid"] = {"x": 32, "y": 32}
        bp["absolute-snapping"] = True
        bp["position-relative-to-grid"] = {"x": 0, "y": 0}
        bp["label"] = f"Phase {i} — {LABELS[i - 1]}"
        bp["description"] = (
            "Experimental starter subset, not the completed overhaul. Reserve "
            "96x96 tiles and align all five phases on one chunk intersection. "
            "Phase 5 requires applying the upgrade planner to built entities. "
            "Preserve underground belt tiers and long-handed inserters. "
            "Follow the Space Age milestone order in ../CHECKPOINT.md. "
            "Cliff explosives require Vulcanus and are omitted.")
        write(f"phase-{i}.json", {"index": i - 1, "blueprint": bp})
    write("_metadata.json", {"blueprint_book": {
        "item": "blueprint-book",
        "label": "Brian's Bootstrap — experimental Space Age starter",
        "version": VERSION, "active_index": 0}})
    write("tier-upgrade.json", {"index": 5, "upgrade_planner": {
        "item": "upgrade-planner",
        "label": "Starter tier upgrade — preserve underground braids",
        "version": VERSION, "settings": {"mappers": [
            {"index": i, "from": {"type": "entity", "name": a},
             "to": {"type": "entity", "name": b}}
            for i, (a, b) in enumerate(TIERS.items())]}}})


if __name__ == "__main__":
    build()
