from random import randint

from .maze_solving import bfs
from ...other_systems.walk import walkable


def move_entity(
    chunks, chunk, tile, current_tile, create_tiles, delete_tiles, type, location
):
    obscured_path = False
    if "goal" not in current_tile:
        if type == 0:
            goal = (randint(-8, 8), randint(-8, 8))
            current_tile["goal"] = (
                (
                    chunk[0] + int((tile[0] + goal[0]) / 16),
                    chunk[1] + int((tile[1] + goal[1]) / 16),
                ),
                ((tile[0] + goal[0]) % 16, (tile[1] + goal[1]) % 16),
            )
        elif type == 1:
            current_tile["goal"] = (
                (location[0], location[1]),
                (location[2], location[3]),
            )
        current_tile["path"] = []
        start = (chunk[0] * 16 + tile[0], chunk[1] * 16 + tile[1])
        goal = (
            current_tile["goal"][0][0] * 16 + current_tile["goal"][1][0],
            current_tile["goal"][0][1] * 16 + current_tile["goal"][1][1],
        )
        path = bfs(start, goal, chunks, current_tile)
        for road in path:
            current_tile["path"].append(
                ((road[0] // 16, road[1] // 16), (road[0] % 16, road[1] % 16))
            )
    if len(current_tile["path"]) > 0:
        can_move = True
        for create_tile in create_tiles:
            if current_tile["path"][0] == (create_tiles[0], create_tile[1]):
                can_move = False
        if can_move and walkable(
            chunks, current_tile["path"][0][0], current_tile["path"][0][1]
        ):
            create_tiles.append(
                (current_tile["path"][0][0], current_tile["path"][0][1], current_tile)
            )
            current_tile["path"].pop(0)
            delete_tiles.append((chunk, tile))
        else:
            obscured_path = True
    if len(current_tile["path"]) == 0 or obscured_path:
        del current_tile["path"]
        del current_tile["goal"]
    return create_tiles, delete_tiles
