from ...info import (
    ATTRIBUTES,
    DAY_LENGTH,
    FLOOR_TYPE,
    FERTILIZER_EFFICIENCY,
    GROW_TILES,
    ATTRACTION,
    BREEDABLE,
)
from ..left_click import (
    recipe,
    place,
    open_storage,
    closed_storage,
    machine_storage,
    unlock,
    fertilize_grow,
    fertilize_spawn,
)


def left_click(
    machine_ui: str,
    grid_position: list[int, int],
    chunks,
    inventory_number: int,
    health: int,
    max_health: int,
    position,
    recipe_number: int,
    location: dict[str],
    inventory: dict[str, int],
    machine_inventory: dict[str, int],
    tick: int,
):
    if machine_ui == "game":
        if inventory_number < len(inventory):
            inventory_key = list(inventory.keys())[inventory_number]
        else:
            inventory_key = None
        is_not_tile = grid_position[1] not in chunks[grid_position[0]]
        if is_not_tile:
            is_kind = True
        else:
            is_kind = "kind" in chunks[grid_position[0]][grid_position[1]]
            current_tile = chunks[grid_position[0]][grid_position[1]]
        is_floor = not is_not_tile and not is_kind
        if is_floor and FLOOR_TYPE.get(current_tile["floor"]) == "door":
            chunks[grid_position[0]][grid_position[1]]["floor"] += " open"
        elif is_floor and FLOOR_TYPE.get(current_tile["floor"]) == "open":
            chunks[grid_position[0]][grid_position[1]]["floor"] = current_tile["floor"][:-5]
        elif (
            is_floor
            and FLOOR_TYPE.get(current_tile["floor"]) == "soil"
            and inventory_key in FERTILIZER_EFFICIENCY
        ):
            chunks = fertilize_spawn(chunks, inventory, inventory_key, grid_position)
        elif is_not_tile or not is_kind:
            chunks, health, max_health = place(
                inventory,
                inventory_key,
                is_not_tile,
                is_kind,
                health,
                max_health,
                grid_position,
                chunks,
            )
        else:
            attributes = ATTRIBUTES.get(
                chunks[grid_position[0]][grid_position[1]]["kind"], ()
            )
            kind = chunks[grid_position[0]][grid_position[1]]["kind"]
            if "open" in attributes:
                machine_ui = kind
                location["opened"] = (grid_position[0], grid_position[1])
                machine_inventory = chunks[grid_position[0]][grid_position[1]].get(
                    "inventory", {}
                )
            elif "sleep" in attributes:
                if 9 / 16 <= (tick / DAY_LENGTH) % 1 < 15 / 16:
                    tick = (tick // DAY_LENGTH + 9 / 16) * DAY_LENGTH
            elif "lock" in attributes:
                chunks = unlock(inventory, inventory_number, chunks, grid_position)
            elif (
                kind in GROW_TILES
                and inventory_key in FERTILIZER_EFFICIENCY
            ):
                chunks = fertilize_grow(
                    chunks, inventory, inventory_key, grid_position
                )
            elif "store" in attributes:
                chunks = closed_storage(
                    chunks, grid_position, inventory, location, inventory_number
                )
            elif kind in BREEDABLE and inventory_key == ATTRACTION[kind]:
                inventory[inventory_key] -= 1
                if inventory[inventory_key] == 0:
                    del inventory[inventory_key]
                chunks[grid_position[0]][grid_position[1]]["love"] = 100
    elif "machine" in ATTRIBUTES.get(machine_ui, ()):
        chunks, inventory = machine_storage(position, chunks, location, inventory, machine_ui)
    elif "store" in ATTRIBUTES.get(machine_ui, ()):
        chunks, machine_inventory = open_storage(
            position, chunks, location, inventory, machine_ui
        )
    elif "craft" in ATTRIBUTES.get(machine_ui, ()):
        inventory = recipe(machine_ui, recipe_number, inventory)
    return machine_ui, chunks, location, machine_inventory, tick, health, max_health, inventory
