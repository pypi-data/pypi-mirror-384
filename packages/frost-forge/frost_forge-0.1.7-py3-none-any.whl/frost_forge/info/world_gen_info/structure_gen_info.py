NOISE_STRUCTURES = {
    "forest": (((0, 0.01), "mushroom hut"),),
    "mountain": (((0, 0.005), "mineshaft"),),
    "plains": (((0, 0), "copper dungeon"),),
}
ROOM_COLORS = {
    "copper dungeon": {
        (136, 68, 31): {"kind": "copper brick", "floor": "copper brick floor"},
        (181, 102, 60): {"floor": "copper brick floor"},
    },
    "mineshaft": {
        (53, 53, 54): {"kind": "stone brick", "floor": "stone floor"},
        (138, 138, 140): {"floor": "stone brick floor"},
        (247, 247, 255): {"kind": "rock", "floor": "stone floor"},
        (73, 58, 37): {"kind": "log", "floor": "wood floor"},
        (92, 74, 49): {"kind": "wood", "floor": "wood floor"},
        (129, 107, 63): {"floor": "wood door"},
        (19, 17, 18): {
            "kind": "coal ore",
            "inventory": {"coal": 1},
            "floor": "stone floor",
        },
        (123, 104, 150): {
            "kind": "small crate",
            "loot": "mine chest",
            "floor": "stone floor",
        },
        (60, 181, 71): {
            "kind": "slime",
            "inventory": {"slime ball": 1},
            "floor": "stone floor",
        },
    },
    "mushroom hut": {
        (247, 247, 255): {"kind": "mushroom block", "floor": "mushroom floor"},
        (138, 138, 140): {"floor": "mushroom floor"},
        (53, 53, 54): {"floor": "mushroom door"},
        (106, 228, 138): {"kind": "mushroom shaper", "floor": "mushroom floor"},
        (92, 74, 49): {
            "kind": "small crate",
            "loot": "mushroom chest",
            "floor": "mushroom floor",
        },
    },
}
STRUCTURE_ENTRANCE = {
    "copper dungeon": {"kind": "glass lock"},
    "mineshaft": {"floor": "stone floor"},
    "mushroom hut": {"floor": "mushroom door"},
}
STRUCTURE_ROOM_SIZES = {
    "copper dungeon": ((1, 1), (2, 1), (2, 2)),
    "mineshaft": ((1, 1),),
    "mushroom hut": ((1, 1),),
}
STRUCTURE_SIZE = {"copper dungeon": 0.8, "mushroom hut": 0, "mineshaft": 0.4}
STRUCTURE_ROOMS = {
    "copper dungeon": {
        (1, 1): ("treasury", "hallway"),
        (2, 1): ("library", "banquet"),
        (2, 2): ("forge",),
    },
    "mineshaft": {
        (1, 1): ("hallway", "coal mine"),
    },
    "mushroom hut": {
        (1, 1): ("mushroom hut",),
    },
}
LOOT_TABLES = {
    "mushroom chest": {
        (0.7, "mushroom", 2, 7),
        (0.5, "mushroom block", 3, 5),
        (0.35, "spore", 1, 5),
        (0.25, "fertilizer", 1, 2),
        (0.2, "mushroom floor", 2, 3),
        (0.15, "plant bouquet", 1, 3),
        (0.1, "mushroom shaper", 1, 1),
        (0.05, "mushroom door", 1, 2),
        (0.03, "bonsai pot", 1, 2),
        (0.01, "composter", 1, 1),
    },
    "mine chest": {
        (0.7, "rock", 2, 4),
        (0.5, "flint", 3, 5),
        (0.35, "coal", 1, 3),
        (0.25, "stone", 2, 4),
        (0.15, "handle", 1, 2),
        (0.1, "life crystal", 1, 1),
        (0.05, "sawbench", 1, 1),
        (0.03, "rock pickaxe", 1, 1),
        (0.02, "rock axe", 1, 1),
        (0.01, "rock sword", 1, 1),
    },
}
ADJACENT_ROOMS = ((0, -1), (0, 1), (-1, 0), (1, 0))
