import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from verse_sdk import observe_tool

DATA_DIR = Path(__file__).parent

# JSON field constants
ID_FIELD = "id"
LOCATION_ID_FIELD = "locationId"
OCCUPATION_ID_FIELD = "occupationId"
CHARACTERS_FIELD = "characters"
FRIENDS_FIELD = "friends"
FAVORITE_ITEMS_FIELD = "favoriteItems"
ITEMS_FIELD = "items"


def load_json(filename: str) -> List[Dict[str, Any]]:
    """Load JSON data from a file in the data directory."""
    try:
        with open(DATA_DIR / filename, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Data file not found: {filename}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in file {filename}: {e}")


characters = load_json("characters.json")
locations = load_json("locations.json")
occupations = load_json("occupations.json")
items = load_json("items.json")
episodes = load_json("episodes.json")


@observe_tool(name="Get Character by ID")
def get_character_by_id(character_id: int) -> Optional[Dict[str, Any]]:
    """Get a character by their ID."""
    if not isinstance(character_id, int):
        raise TypeError(
            f"character_id must be an integer, got {type(character_id).__name__}"
        )
    return next((c for c in characters if c[ID_FIELD] == character_id), None)


@observe_tool(name="Get All Characters")
def get_all_characters() -> List[Dict[str, Any]]:
    """Get all characters (lite to force other lookups)."""
    return [
        {
            "id": c["id"],
            "name": c["name"],
            "age": c["age"],
            "species": "Monkey",
            "locationId": c["locationId"],
            "occupationId": c["occupationId"],
        }
        for c in characters
    ]


@observe_tool(name="Get Friends")
def get_friends(character_id: int) -> List[Dict[str, Any]]:
    """Get all friends of a character."""
    character = get_character_by_id(character_id)
    if not character:
        return []
    return [get_character_by_id(fid) for fid in character.get(FRIENDS_FIELD, [])]


@observe_tool()
def get_character_location(character_id: int) -> Optional[Dict[str, Any]]:
    """Get the location of a character."""
    character = get_character_by_id(character_id)
    return get_location_by_id(character[LOCATION_ID_FIELD]) if character else None


@observe_tool()
def get_character_occupation(character_id: int) -> Optional[Dict[str, Any]]:
    """Get the occupation of a character."""
    character = get_character_by_id(character_id)
    return get_occupation_by_id(character[OCCUPATION_ID_FIELD]) if character else None


@observe_tool()
def get_favorite_items(character_id: int) -> List[Dict[str, Any]]:
    """Get all favorite items of a character."""
    character = get_character_by_id(character_id)
    if not character:
        return []
    return [get_item_by_id(iid) for iid in character.get(FAVORITE_ITEMS_FIELD, [])]


@observe_tool()
def get_episodes_by_character(character_id: int) -> List[Dict[str, Any]]:
    """Get all episodes featuring a character."""
    return [e for e in episodes if character_id in e.get(CHARACTERS_FIELD, [])]


@observe_tool()
def get_location_by_id(location_id: int) -> Optional[Dict[str, Any]]:
    """Get a location by its ID."""
    if not isinstance(location_id, int):
        raise TypeError(
            f"location_id must be an integer, got {type(location_id).__name__}"
        )
    return next(
        (location for location in locations if location[ID_FIELD] == location_id), None
    )


@observe_tool()
def get_all_locations() -> List[Dict[str, Any]]:
    """Get all locations."""
    return locations


@observe_tool()
def get_characters_by_location(location_id: int) -> List[Dict[str, Any]]:
    """Get all characters at a specific location."""
    return [c for c in characters if c[LOCATION_ID_FIELD] == location_id]


@observe_tool()
def get_episodes_by_location(location_id: int) -> List[Dict[str, Any]]:
    """Get all episodes at a specific location."""
    return [e for e in episodes if e[LOCATION_ID_FIELD] == location_id]


@observe_tool()
def get_occupation_by_id(occupation_id: int) -> Optional[Dict[str, Any]]:
    """Get an occupation by its ID."""
    if not isinstance(occupation_id, int):
        raise TypeError(
            f"occupation_id must be an integer, got {type(occupation_id).__name__}"
        )
    return next((o for o in occupations if o[ID_FIELD] == occupation_id), None)


@observe_tool()
def get_all_occupations() -> List[Dict[str, Any]]:
    """Get all occupations."""
    return occupations


@observe_tool()
def get_characters_by_occupation(occupation_id: int) -> List[Dict[str, Any]]:
    """Get all characters with a specific occupation."""
    return [c for c in characters if c[OCCUPATION_ID_FIELD] == occupation_id]


@observe_tool()
def get_item_by_id(item_id: int) -> Optional[Dict[str, Any]]:
    """Get an item by its ID."""
    if not isinstance(item_id, int):
        raise TypeError(f"item_id must be an integer, got {type(item_id).__name__}")
    return next((i for i in items if i[ID_FIELD] == item_id), None)


@observe_tool()
def get_all_items() -> List[Dict[str, Any]]:
    """Get all items."""
    return items


@observe_tool()
def get_characters_by_item(item_id: int) -> List[Dict[str, Any]]:
    """Get all characters who have a specific item as favorite."""
    return [c for c in characters if item_id in c.get(FAVORITE_ITEMS_FIELD, [])]


@observe_tool()
def get_episodes_by_item(item_id: int) -> List[Dict[str, Any]]:
    """Get all episodes featuring a specific item."""
    return [e for e in episodes if item_id in e.get(ITEMS_FIELD, [])]


@observe_tool()
def get_episode_by_id(episode_id: int) -> Optional[Dict[str, Any]]:
    """Get an episode by its ID."""
    if not isinstance(episode_id, int):
        raise TypeError(
            f"episode_id must be an integer, got {type(episode_id).__name__}"
        )
    return next((e for e in episodes if e[ID_FIELD] == episode_id), None)


@observe_tool()
def get_all_episodes() -> List[Dict[str, Any]]:
    """Get all episodes."""
    return episodes


@observe_tool()
def get_characters_by_episode(episode_id: int) -> List[Dict[str, Any]]:
    """Get all characters in a specific episode."""
    ep = get_episode_by_id(episode_id)
    if not ep:
        return []
    return [get_character_by_id(cid) for cid in ep.get(CHARACTERS_FIELD, [])]


@observe_tool()
def get_location_by_episode(episode_id: int) -> Optional[Dict[str, Any]]:
    """Get the location of a specific episode."""
    ep = get_episode_by_id(episode_id)
    return get_location_by_id(ep[LOCATION_ID_FIELD]) if ep else None


@observe_tool()
def get_items_by_episode(episode_id: int) -> List[Dict[str, Any]]:
    """Get all items featured in a specific episode."""
    ep = get_episode_by_id(episode_id)
    if not ep:
        return []
    return [get_item_by_id(iid) for iid in ep.get(ITEMS_FIELD, [])]
