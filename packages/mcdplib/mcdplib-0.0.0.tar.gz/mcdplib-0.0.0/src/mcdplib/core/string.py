def substring(string: str, start_character_index: int, characters_count: int) -> str:
    if start_character_index + characters_count >= string.__len__():
        return string[start_character_index:]
    return string[start_character_index:start_character_index + characters_count]


def contains_only(string: str, allowed_symbols: str) -> bool:
    for symbol in string:
        if symbol not in allowed_symbols:
            return False
    return True
