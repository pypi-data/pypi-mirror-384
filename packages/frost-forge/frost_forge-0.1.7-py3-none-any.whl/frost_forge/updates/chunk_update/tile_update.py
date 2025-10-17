from .point import left, up
from ..entity_behaviour.animal import animal
from ..entity_behaviour.enemy import enemy
from .growth import grow
from ..left_click import recipe
from ...info import ATTRIBUTES, GROW_TILES, FPS, PROCESSING_TIME


def update_tile(
    current_tile,
    chunks,
    chunk,
    tile,
    delete_tiles,
    create_tiles,
    tick,
    location,
    inventory_key,
    health,
):
    attributes = ATTRIBUTES.get(current_tile["kind"], ())
    if current_tile["kind"] == "left":
        chunks, delete_tiles = left(chunks, chunk, tile, delete_tiles)
    elif current_tile["kind"] == "up":
        chunks, delete_tiles = up(chunks, chunk, tile, delete_tiles)
    elif "machine" in attributes and tick % PROCESSING_TIME[current_tile["kind"]] == 0:
        chunks[chunk][tile]["inventory"] = recipe(current_tile["kind"], current_tile.get("recipe", 0), current_tile.get("inventory", {}))
    elif current_tile["kind"] in GROW_TILES:
        chunks[chunk][tile] = grow(current_tile)
        if chunks[chunk][tile] == {}:
            delete_tiles.append((chunk, tile))
    if "animal" in attributes or "enemy" in attributes:
        player_distance_x = abs(chunk[0] * 16 + tile[0] - location[0] * 16 - location[2])
        player_distance_y = abs(chunk[1] * 16 + tile[1] - location[1] * 16 - location[3])
        player_distance = player_distance_x ** 2 + player_distance_y ** 2
        if "animal" in attributes:
            create_tiles, delete_tiles = animal(
                chunks,
                chunk,
                tile,
                current_tile,
                create_tiles,
                delete_tiles,
                location,
                inventory_key,
                player_distance,
            )
        else:
            create_tiles, delete_tiles, health = enemy(
                chunks,
                chunk,
                tile,
                current_tile,
                create_tiles,
                delete_tiles,
                location,
                health,
                player_distance,
            )
    return chunks, create_tiles, delete_tiles, health
