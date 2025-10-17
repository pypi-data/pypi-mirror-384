from ..chunk_update import update_tile, create_tile, delete_tile
from ...info import GROW_TILES
from ..chunk_update.growth import grow


def update_tiles(state, chunks):
    delete_tiles = []
    create_tiles = []
    tile_location = state.location["tile"]
    if len(state.inventory) > state.inventory_number:
        inventory_key = list(state.inventory.keys())[state.inventory_number]
    else:
        inventory_key = None

    for chunk_dx in range(-3, 4):
        for chunk_dy in range(-3, 4):
            chunk = (chunk_dx + tile_location[0], chunk_dy + tile_location[1])
            if chunk in chunks:
                for tile in list(chunks[chunk]):
                    current_tile = chunks[chunk][tile]
                    if "kind" in current_tile:
                        chunks, create_tiles, delete_tiles, state.health = update_tile(
                            current_tile,
                            chunks,
                            chunk,
                            tile,
                            delete_tiles,
                            create_tiles,
                            state.tick,
                            state.location["tile"],
                            inventory_key,
                            state.health,
                        )
                    elif (
                        "floor" in current_tile and current_tile["floor"] in GROW_TILES
                    ):
                        chunks[chunk][tile] = grow(current_tile)
                        if chunks[chunk][tile] == {}:
                            delete_tiles.append((chunk, tile))

    chunks = create_tile(chunks, create_tiles)
    chunks = delete_tile(chunks, delete_tiles)
    return chunks
