from ..right_click import break_tile, break_floor
from ..left_click import open_storage
from ...info import UNBREAK, ATTRIBUTES


def right_click(
    chunks,
    grid_position: tuple[tuple[int, int], tuple[int, int]],
    inventory: dict[str, int],
    inventory_number: int,
    location: dict,
    machine_ui: str,
    position,
    machine_inventory,
    health,
):
    if "store" in ATTRIBUTES.get(machine_ui, ()):
        chunks, machine_inventory = open_storage(
            position, chunks, location, inventory, machine_ui, True
        )
    else:
        machine_ui = "game"
        if grid_position[1] not in chunks[grid_position[0]]:
            return chunks, location, machine_ui, machine_inventory, health
        mining_tile = chunks[grid_position[0]][grid_position[1]]
        delete_mining_tile = False
        location["mined"] = (grid_position[0], grid_position[1])
        if "kind" in mining_tile:
            if mining_tile["kind"] not in UNBREAK:
                chunks, delete_mining_tile, mining_tile = break_tile(
                    inventory, chunks, mining_tile, inventory_number
                )
            elif mining_tile["kind"] == "player":
                health -= 1
        elif "floor" in mining_tile and mining_tile["floor"] not in UNBREAK:
            delete_mining_tile, inventory, mining_tile = break_floor(
                mining_tile, inventory, inventory_number
            )
        if delete_mining_tile:
            del chunks[grid_position[0]][grid_position[1]]
        else:
            chunks[grid_position[0]][grid_position[1]] = mining_tile
    return chunks, location, machine_ui, machine_inventory, health
