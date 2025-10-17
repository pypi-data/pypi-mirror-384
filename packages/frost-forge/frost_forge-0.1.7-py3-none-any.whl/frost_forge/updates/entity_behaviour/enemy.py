from .entity_movement import move_entity


def enemy(
    chunks, chunk, tile, current_tile, create_tiles, delete_tiles, location, health, player_distance
):
    if player_distance == 1:
        health -= 1
    elif player_distance < 73:
        create_tiles, delete_tiles = move_entity(
            chunks, chunk, tile, current_tile, create_tiles, delete_tiles, 1, location
        )
    else:
        create_tiles, delete_tiles = move_entity(
            chunks, chunk, tile, current_tile, create_tiles, delete_tiles, 0, location
        )
    return create_tiles, delete_tiles, health
