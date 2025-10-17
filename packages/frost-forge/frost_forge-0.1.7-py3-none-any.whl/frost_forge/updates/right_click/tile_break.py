from ...info import INVENTORY_SIZE, HEALTH, UNOBTAINABLE
from .damage_calculation import calculate_damage


def break_tile(inventory, chunks, mining_tile, inventory_number):
    delete_mining_tile = False
    if "health" not in mining_tile:
        mining_tile["health"] = HEALTH[mining_tile["kind"]]
    mining_tile["health"] -= calculate_damage(
        mining_tile["kind"], inventory, inventory_number
    )
    if mining_tile["health"] <= 0:
        mining_floor_exist = "floor" in mining_tile
        if mining_floor_exist:
            mining_floor = mining_tile["floor"]
        junk_inventory = {}
        if "inventory" not in mining_tile:
            mining_tile["inventory"] = {}
        if mining_tile["kind"] not in UNOBTAINABLE:
            mining_tile["inventory"][mining_tile["kind"]] = (
                mining_tile["inventory"].get(mining_tile["kind"], 0) + 1
            )
        for item, amount in mining_tile["inventory"].items():
            if item in inventory:
                inventory[item] += amount
                if inventory[item] > INVENTORY_SIZE[1]:
                    junk_inventory[item] = inventory[item] - INVENTORY_SIZE[1]
                    inventory[item] = INVENTORY_SIZE[1]
            else:
                if len(inventory) < INVENTORY_SIZE[0]:
                    inventory[item] = amount
                else:
                    junk_inventory[item] = amount
        if mining_floor_exist:
            mining_tile = {}
        else:
            delete_mining_tile = True
        if len(junk_inventory) > 0:
            mining_tile = {"kind": "junk", "inventory": junk_inventory}
        if mining_floor_exist:
            mining_tile["floor"] = mining_floor
    return chunks, delete_mining_tile, mining_tile
