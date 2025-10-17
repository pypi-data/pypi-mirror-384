from random import random

from ...info import GROW_CHANCE, GROW_TILES, GROW_REQUIREMENT, SOIL_STRENGTH


def grow(tile, guarantee=False):
    if "kind" in tile:
        old_kind = tile["kind"]
    else:
        old_kind = tile["floor"]
    if random() < SOIL_STRENGTH.get(tile.get("floor"), 1) / (GROW_CHANCE[old_kind] * 6) or guarantee:
        if GROW_REQUIREMENT.get(old_kind, 1) <= SOIL_STRENGTH.get(tile["floor"], 1):
            for info in GROW_TILES[old_kind]:
                tile[info] = GROW_TILES[old_kind][info]
            if "inventory" in GROW_TILES[old_kind]:
                tile["inventory"] = {}
                for item in GROW_TILES[old_kind]["inventory"]:
                    tile["inventory"][item] = GROW_TILES[old_kind]["inventory"][item]
    return tile
