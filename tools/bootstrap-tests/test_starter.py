"""Contract tests for the saved experimental starter subset."""
import copy
import json
from pathlib import Path
import sys
import unittest

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
from fatul import Processor, read_files

BOOK = TOOLS.parent / "brians-bootstrap/experimental/book"


def get(i):
    return json.loads((BOOK / f"phase-{i}.json").read_text())["blueprint"]


def positions(bp, predicate):
    return {tuple(e["position"].values()) for e in bp["entities"] if predicate(e)}


class Starter(unittest.TestCase):
    def test_round_trip(self):
        data = read_files(BOOK, False)
        packed = Processor(False).encode(copy.deepcopy(data))
        result = Processor(False, ids_mode="keep").decode(packed)
        self.assertEqual(data["blueprint_book"]["label"],
                         result["blueprint_book"]["label"])

    def test_shared_anchor(self):
        self.assertTrue(positions(get(1), lambda e: e["name"] == "stone-furnace")
                        <= positions(get(2), lambda e: e["name"] == "stone-furnace"))
        for i in range(2, 5):
            self.assertTrue(positions(get(i), lambda e: e.get("recipe") == "iron-gear-wheel")
                            <= positions(get(i + 1), lambda e: e.get("recipe") == "iron-gear-wheel"))

    def test_upgrade_preserves_tunnels_and_reach(self):
        def special(bp):
            return [(e["name"], e["position"], e.get("type"))
                    for e in bp["entities"]
                    if "underground-belt" in e["name"] or e["name"] == "long-handed-inserter"]
        self.assertEqual(special(get(4)), special(get(5)))
        self.assertFalse(any(e["name"] in {"assembling-machine-1", "transport-belt",
            "splitter", "inserter"} for e in get(5)["entities"]))

    def test_grid_and_technology_gate(self):
        for i in range(1, 6):
            bp = get(i)
            self.assertEqual(bp["snap-to-grid"], {"x": 32, "y": 32})
            self.assertTrue(bp["absolute-snapping"])
            self.assertFalse(any(e.get("recipe") == "cliff-explosives"
                                 for e in bp["entities"]))


if __name__ == "__main__":
    unittest.main()
