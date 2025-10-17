from ...info import FOOD, FLOOR, HEALTH_INCREASE
from ...other_systems.tile_placement import place_tile
from ...other_systems.tile_placable import is_placable


def place(
    inventory,
    inventory_key,
    is_not_tile,
    is_kind,
    health,
    max_health,
    grid_position,
    chunks,
):
    if inventory_key not in FLOOR:
        if is_not_tile or not is_kind:
            if inventory_key in FOOD and health < max_health:
                health = min(health + FOOD[inventory_key], max_health)
            elif (
                inventory_key in HEALTH_INCREASE
                and HEALTH_INCREASE[inventory_key][0]
                <= max_health
                < HEALTH_INCREASE[inventory_key][1]
            ):
                max_health += HEALTH_INCREASE[inventory_key][2]
                health += HEALTH_INCREASE[inventory_key][2]
            elif is_placable(inventory_key, grid_position, chunks):
                chunks = place_tile(inventory_key, grid_position, chunks)
            else:
                inventory[inventory_key] += 1
            inventory[inventory_key] -= 1
    elif is_not_tile:
        inventory[inventory_key] -= 1
        chunks[grid_position[0]][grid_position[1]] = {"floor": inventory_key}
    if inventory[inventory_key] == 0:
        del inventory[inventory_key]
    return chunks, health, max_health
