def create_tile(chunks, create_tiles):
    for chunk_pos, tile_pos, tile_data in create_tiles:
        if "floor" in tile_data:
            del tile_data["floor"]
        if "floor" in chunks[chunk_pos].get(tile_pos, {}):
            tile_data["floor"] = chunks[chunk_pos][tile_pos]["floor"]
        if tile_pos not in chunks[chunk_pos]:
            chunks[chunk_pos][tile_pos] = {}
        for info in tile_data:
            chunks[chunk_pos][tile_pos][info] = tile_data[info]
    return chunks


def delete_tile(chunks, delete_tiles):
    for chunk_pos, tile_pos in delete_tiles:
        tile = chunks[chunk_pos][tile_pos]
        if "floor" in tile:
            chunks[chunk_pos][tile_pos] = {"floor": tile["floor"]}
        else:
            del chunks[chunk_pos][tile_pos]
    return chunks
