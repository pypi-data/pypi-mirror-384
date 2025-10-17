from .entity_movement import move_entity
from .empty_place import find_empty_place
from .love_search import search_love
from ...info import ATTRACTION, ADJACENT_ROOMS, BREEDABLE


def animal(
    chunks,
    chunk,
    tile,
    current_tile,
    create_tiles,
    delete_tiles,
    location,
    inventory_key,
    player_distance,
):
    move = True
    if "love" in current_tile:
        found_love, love_chunk, love_tile = search_love(chunks, chunk, tile, ADJACENT_ROOMS)
        if found_love:
            empty = find_empty_place(tile, chunk, chunks)
            if empty:
                offspring_chunk, offspring_tile = empty
                create_tiles.append((offspring_chunk, offspring_tile, BREEDABLE[current_tile["kind"]]))
                chunks[chunk][tile]["love"] = 0
                del chunks[love_chunk][love_tile]["love"]
        else:
            found_love, love_chunk, love_tile = search_love(chunks, chunk, tile, ((x, y) for x in range(-4, 5) for y in range(-4, 5)))
            if found_love:
                create_tiles, delete_tiles = move_entity(
                    chunks, chunk, tile, current_tile, create_tiles, delete_tiles, 1, (*love_chunk, *love_tile)
                )
                move = False
        chunks[chunk][tile]["love"] -= 1
        if chunks[chunk][tile]["love"] <= 0:
            del chunks[chunk][tile]["love"]
    if move:
        if player_distance < 73 and inventory_key == ATTRACTION[current_tile["kind"]]:
            create_tiles, delete_tiles = move_entity(
                chunks, chunk, tile, current_tile, create_tiles, delete_tiles, 1, location
            )
        else:
            create_tiles, delete_tiles = move_entity(
                chunks, chunk, tile, current_tile, create_tiles, delete_tiles, 0, location
            )
    return create_tiles, delete_tiles
