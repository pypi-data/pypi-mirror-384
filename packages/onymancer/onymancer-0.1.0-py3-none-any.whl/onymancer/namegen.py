"""Fantasy name generator module."""

import json
import random

# Global token map
_token_map: dict[str, list[str]] = {}


# Default tokens
_default_tokens = {
    "s": [
        "ach",
        "ack",
        "ad",
        "age",
        "ald",
        "ale",
        "an",
        "ang",
        "ar",
        "ard",
        "as",
        "ash",
        "at",
        "ath",
        "augh",
        "aw",
        "ban",
        "bel",
        "bur",
        "cer",
        "cha",
        "che",
        "dan",
        "dar",
        "del",
        "den",
        "dra",
        "dyn",
        "ech",
        "eld",
        "elm",
        "em",
        "en",
        "end",
        "eng",
        "enth",
        "er",
        "ess",
        "est",
        "et",
        "gar",
        "gha",
        "hat",
        "hin",
        "hon",
        "ia",
        "ight",
        "ild",
        "im",
        "ina",
        "ine",
        "ing",
        "ir",
        "is",
        "iss",
        "it",
        "kal",
        "kel",
        "kim",
        "kin",
        "ler",
        "lor",
        "lye",
        "mor",
        "mos",
        "nal",
        "ny",
        "nys",
        "old",
        "om",
        "on",
        "or",
        "orm",
        "os",
        "ough",
        "per",
        "pol",
        "qua",
        "que",
        "rad",
        "rak",
        "ran",
        "ray",
        "ril",
        "ris",
        "rod",
        "roth",
        "ryn",
        "sam",
        "say",
        "ser",
        "shy",
        "skel",
        "sul",
        "tai",
        "tan",
        "tas",
        "ter",
        "tim",
        "tin",
        "tor",
        "tur",
        "um",
        "und",
        "unt",
        "urn",
        "usk",
        "ust",
        "ver",
        "ves",
        "vor",
        "war",
        "wor",
        "yer",
    ],
    "v": ["a", "e", "i", "o", "u", "y"],
    "V": [
        "a",
        "e",
        "i",
        "o",
        "u",
        "y",
        "ae",
        "ai",
        "au",
        "ay",
        "ea",
        "ee",
        "ei",
        "eu",
        "ey",
        "ia",
        "ie",
        "oe",
        "oi",
        "oo",
        "ou",
        "ui",
    ],
    "c": [
        "b",
        "c",
        "d",
        "f",
        "g",
        "h",
        "j",
        "k",
        "l",
        "m",
        "n",
        "p",
        "q",
        "r",
        "s",
        "t",
        "v",
        "w",
        "x",
        "y",
        "z",
    ],
    "B": [
        "b",
        "bl",
        "br",
        "c",
        "ch",
        "chr",
        "cl",
        "cr",
        "d",
        "dr",
        "f",
        "g",
        "h",
        "j",
        "k",
        "l",
        "ll",
        "m",
        "n",
        "p",
        "ph",
        "qu",
        "r",
        "rh",
        "s",
        "sch",
        "sh",
        "sl",
        "sm",
        "sn",
        "st",
        "str",
        "sw",
        "t",
        "th",
        "thr",
        "tr",
        "v",
        "w",
        "wh",
        "y",
        "z",
        "zh",
    ],
    "C": [
        "b",
        "c",
        "ch",
        "ck",
        "d",
        "f",
        "g",
        "gh",
        "h",
        "k",
        "l",
        "ld",
        "ll",
        "lt",
        "m",
        "n",
        "nd",
        "nn",
        "nt",
        "p",
        "ph",
        "q",
        "r",
        "rd",
        "rr",
        "rt",
        "s",
        "sh",
        "ss",
        "st",
        "t",
        "th",
        "v",
        "w",
        "y",
        "z",
    ],
    "i": [
        "big",
        "black",
        "blind",
        "bloody",
        "brave",
        "broken",
        "cold",
        "coward",
        "cowardly",
        "cunning",
        "daft",
        "dead",
        "deadly",
        "deaf",
        "dreadful",
        "evil",
        "false",
        "foul",
        "frightful",
        "ghastly",
        "grim",
        "grisly",
        "gullible",
        "hateful",
        "hearty",
        "horrible",
        "idiotic",
        "ignorant",
        "lame",
        "large",
        "lazy",
        "little",
        "lively",
        "loathsome",
        "long",
        "loud",
        "mad",
        "meek",
        "mighty",
        "miserable",
        "moronic",
        "naughty",
        "naive",
        "nimble",
        "noble",
        "old",
        "old",
        "pale",
        "petite",
        "plain",
        "poor",
        "quick",
        "quiet",
        "rash",
        "red",
        "rotten",
        "rude",
        "silly",
        "small",
        "stupid",
        "swift",
        "tall",
        "tame",
        "terrible",
        "thin",
        "tiny",
        "tough",
        "ugly",
        "vile",
        "wicked",
        "wise",
        "young",
    ],
    "m": [
        "baby",
        "dear",
        "darling",
        "love",
        "lover",
        "dearest",
        "sweet",
        "sweetie",
        "sugar",
    ],
    "M": ["boo", "kins", "pie", "poo", "tum", "ums"],
    "D": [
        "b",
        "bl",
        "br",
        "cl",
        "d",
        "f",
        "fl",
        "fr",
        "g",
        "gh",
        "gl",
        "gr",
        "h",
        "j",
        "k",
        "kl",
        "m",
        "n",
        "p",
        "th",
        "w",
    ],
    "d": [
        "el",
        "al",
        "an",
        "ar",
        "cha",
        "co",
        "el",
        "er",
        "he",
        "hi",
        "is",
        "or",
        "son",
        "ther",
        "y",
    ],
    "t": [
        "Master of",
        "Ruler of",
        "Teacher of",
        "Conqueror of",
        "Lord of",
        "Guardian of",
        "Keeper of",
        "Seeker of",
        "Bringer of",
        "Bearer of",
        "Defender of",
        "Slayer of",
        "Hunter of",
        "Watcher of",
        "Follower of",
    ],
    "T": [
        "the Endless",
        "the Sea",
        "the Fiery Pit",
        "the Mountains",
        "the Forest",
        "the Plains",
        "the Desert",
        "the Storm",
        "the Night",
        "the Day",
        "the Shadows",
        "the Light",
        "the Dark",
        "the Ancient",
        "the Forgotten",
        "the Lost",
        "the Hidden",
        "the Eternal",
        "the Mighty",
    ],
}


# Initialize with default tokens
_token_map.update(_default_tokens)


def get_tokens(key: str) -> list[str]:
    """Retrieve the tokens corresponding to a key.

    Args:
        key: The key to retrieve the tokens for.

    Returns:
        The list of tokens for the specified key.

    """
    return _token_map.get(key, [])


def _get_rand(seed: int, min_val: int, max_val: int) -> int:
    """Return a random number between min_val and max_val.

    Args:
        seed: The seed for the random number generator.
        min_val: The lower bound.
        max_val: The upper bound.

    Returns:
        A random integer between min_val and max_val.

    """
    random.seed(seed)
    return random.randint(min_val, max_val)


def _pick_random_element(seed: int, strings: list[str]) -> str:
    """Pick a random element from the given container of strings.

    Args:
        seed: The seed for random selection.
        strings: The list of strings to pick from.

    Returns:
        The randomly selected string.

    """
    if not strings:
        return ""
    index = _get_rand(seed, 0, len(strings) - 1)
    return strings[index]


def _capitalize_and_clear(character: str, capitalize: bool) -> str:
    """Capitalize the given character if capitalize is True.

    Args:
        character: The input character.
        capitalize: Whether to capitalize.

    Returns:
        The capitalized character if capitalize is True, else the original.

    """
    if capitalize:
        return character.upper()
    return character


class _OptionT:
    """Struct that encapsulates all the state options."""

    def __init__(self) -> None:
        self.capitalize: bool = False
        self.emit_literal: bool = False
        self.inside_group: bool = False
        self.seed: int = 0
        self.current_option: str = ""
        self.options: list[str] = []


def _process_token(options: _OptionT, buffer: list[str], key: str) -> bool:
    """Process a token based on the provided key and append it to the buffer.

    Args:
        options: The current state options.
        buffer: The string buffer where the processed token will be appended.
        key: The key representing the type of token to process.

    Returns:
        True on success, False otherwise.

    """
    tokens = get_tokens(key)
    if not tokens:
        buffer.append(_capitalize_and_clear(key, options.capitalize))
    else:
        token = _pick_random_element(options.seed, tokens)
        if not token:
            return False
        # Update seed for next random call
        options.seed += 1
        it = iter(token)
        first_char = next(it, "")
        buffer.append(_capitalize_and_clear(first_char, options.capitalize))
        buffer.extend(it)
    return True


def _process_character(options: _OptionT, buffer: list[str], character: str) -> bool:
    """Process a character from the pattern and append it to the buffer.

    Args:
        options: The current state options.
        buffer: The string buffer where the processed character will be appended.
        character: The character to process.

    Returns:
        True on success, False otherwise.

    """
    if character == "(":
        if options.inside_group:
            options.current_option += character
        else:
            options.emit_literal = True
    elif character == ")":
        if options.inside_group:
            options.current_option += character
        else:
            options.emit_literal = False
    elif character == "<":
        options.inside_group = True
        options.options.clear()
        options.current_option = ""
    elif character == "|":
        options.options.append(options.current_option)
        options.current_option = ""
    elif character == ">":
        options.inside_group = False
        options.options.append(options.current_option)
        options.current_option = ""
        # Ensure there's at least one option in the group.
        if not options.options:
            return False
        # Randomly pick an option.
        option = _pick_random_element(options.seed, options.options)
        options.seed += 1
        # Process and append the selected option.
        for token in option:
            if not _process_character(options, buffer, token):
                return False
        # Clear options after processing the group.
        options.options.clear()
    elif character == "!":
        if options.inside_group:
            options.current_option += character
        else:
            options.capitalize = True
    elif options.inside_group:
        options.current_option += character
    elif options.emit_literal:
        buffer.append(_capitalize_and_clear(character, options.capitalize))
    elif not _process_token(options, buffer, character):
        return False
    return True


def load_tokens_from_json(filename: str) -> bool:
    """Load tokens from a JSON file.

    Args:
        filename: The path to the JSON file containing the tokens.

    Returns:
        True if the loading was successful, False otherwise.

    """
    try:
        with open(filename, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return False
        global _token_map
        _token_map.clear()
        _token_map.update(data)
        return True
    except (OSError, json.JSONDecodeError):
        return False


def set_token(key: str, tokens: list[str]) -> None:
    """Set the token list of a given key in the global token map.

    Args:
        key: The key for which to set the token list.
        tokens: The list of tokens (strings) to associate with the key.

    """
    _token_map[key] = tokens


def set_tokens(tokens: dict[str, list[str]]) -> None:
    """Set a given list of key-value pairs in the global token map.

    Args:
        tokens: A map where each key is a character and the value is a list of strings (tokens).

    """
    _token_map.update(tokens)


def generate(pattern: str, seed: int) -> str:
    """Generate a random name based on the provided pattern and seed.

    Args:
        pattern: The pattern defining the structure of the name.
        seed: The seed for random number generation.

    Returns:
        The generated name.

    """
    options = _OptionT()
    options.seed = seed
    buffer: list[str] = []
    for c in pattern:
        if not _process_character(options, buffer, c):
            return ""
    return "".join(buffer)
