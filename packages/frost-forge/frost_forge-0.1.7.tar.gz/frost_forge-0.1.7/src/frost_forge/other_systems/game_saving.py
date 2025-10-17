from os import path

from ..info import SAVES_FOLDER


def save_game(chunks, state, file):
    with open(path.join(SAVES_FOLDER, f"{file}.txt"), "w", encoding="utf-8") as file:
        file.write(
            f"{chunks};{state.location['tile']};{state.inventory};{state.max_health};{state.tick};{state.noise_offset};{state.world_type};{state.checked}"
        )
