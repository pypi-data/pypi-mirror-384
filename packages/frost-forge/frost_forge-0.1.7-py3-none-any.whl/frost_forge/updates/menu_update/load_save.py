from ast import literal_eval
import os

from ...info import SAVES_FOLDER, TEXT_DISTANCE


def save_loading(state, chunks):
    saves = [f[:-4] for f in os.listdir(SAVES_FOLDER) if f.endswith(".txt")]
    index = (state.position[1] // TEXT_DISTANCE) - 2
    if index < len(saves):
        state.save_file_name = saves[index]
        if state.position[0] >= 120:
            state.menu_placement = "main_game"
            with open(
                os.path.join(SAVES_FOLDER, state.save_file_name + ".txt"),
                "r",
                encoding="utf-8",
            ) as file:
                file_content = file.read().split(";")
            chunks = literal_eval(file_content[0])
            state.location["tile"] = literal_eval(file_content[1])
            state.location["real"] = list(state.location["tile"])
            state.inventory = literal_eval(file_content[2])
            state.max_health = int(float(file_content[3]))
            state.health = state.max_health
            state.tick = int(float(file_content[4]))
            state.noise_offset = literal_eval(file_content[5])
            state.world_type = int(file_content[6])
            state.checked = literal_eval(file_content[7])
        elif state.position[0] <= 90:
            file = os.path.join(SAVES_FOLDER, state.save_file_name + ".txt")
            if os.path.exists(file):
                os.remove(file)
    return chunks
