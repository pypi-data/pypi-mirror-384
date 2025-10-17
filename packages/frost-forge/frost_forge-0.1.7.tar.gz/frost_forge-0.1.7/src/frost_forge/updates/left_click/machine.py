from ...info import (
    SCREEN_SIZE,
    UI_SCALE,
    INVENTORY_SIZE,
    RECIPES,
    STORAGE,
    MACHINES,
    VALUES,
)
from .put_in import put_in
from .take_out import take_out


def machine_storage(position, chunks, location, inventory, machine_ui):
    if "inventory" not in chunks[location["opened"][0]][location["opened"][1]]:
        chunks[location["opened"][0]][location["opened"][1]]["inventory"] = {}
    moved_x = position[0] - SCREEN_SIZE[0] // 2
    machine = chunks[location["opened"][0]][location["opened"][1]]
    machine_recipe = RECIPES[machine_ui][machine.get("recipe", 0)]
    holding_over_inventory = (
        position[1] >= SCREEN_SIZE[1] - 32 * UI_SCALE
        and abs(moved_x) <= 16 * INVENTORY_SIZE[0] * UI_SCALE
    )
    if holding_over_inventory:
        inventory_number = (
            (moved_x - 16 * UI_SCALE * (INVENTORY_SIZE[0] % 2)) // (32 * UI_SCALE)
            + INVENTORY_SIZE[0] // 2
            + INVENTORY_SIZE[0] % 2
        )
        if inventory_number < len(inventory):
            item = list(inventory.items())[inventory_number]
            may_put_in = False
            if machine["kind"] in MACHINES and item[0] in VALUES[MACHINES[machine["kind"]]]:
                may_put_in = True
                convertion_inventory = list(inventory.items())
                convertion_inventory[inventory_number] = (MACHINES[machine["kind"]], item[1] * VALUES[MACHINES[machine["kind"]]][item[0]])
                inventory = dict(convertion_inventory)
            for i in range(0, len(machine_recipe[1])):
                if machine_recipe[1][i][0] == item[0]:
                    may_put_in = True
            if may_put_in:
                machine_storage = STORAGE.get(machine_ui, (14, 16))
                chunks = put_in(
                    chunks,
                    location,
                    inventory,
                    machine_storage,
                    inventory_number,
                    machine["inventory"],
                )
    slot_row = (position[1] - SCREEN_SIZE[1] + 144 * UI_SCALE) // (32 * UI_SCALE)
    if slot_row == 2 and (moved_x + 112 * UI_SCALE) // (32 * UI_SCALE) == 0:
        item = (machine_recipe[0][0], machine["inventory"].get(machine_recipe[0][0], 0))
        if item[0] in machine["inventory"]:
            checking_inventory = list(machine["inventory"])
            for i in range(len(checking_inventory)):
                if checking_inventory[i] == item[0]:
                    slot_number = i
            chunks = take_out(chunks, location, inventory, slot_number, machine["inventory"])
    return chunks, inventory
