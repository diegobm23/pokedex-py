"""
pokeapi.py — PokéAPI integration layer
Handles all HTTP communication with https://pokeapi.co/api/v2/
"""

from typing import Optional
from requests import get

BASE_URL = "https://pokeapi.co/api/v2"


def _get(endpoint: str) -> Optional[dict]:
    """Make a GET request to PokéAPI and return parsed JSON, or None on error."""
    url = f"{BASE_URL}/{endpoint}"
    response = get(url, timeout=10)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


# ── Pokémon ──────────────────────────────────────────────────────────────────

def get_pokemon(name_or_id: str | int) -> Optional[dict]:
    """
    Fetch full Pokémon data by name (case-insensitive) or National Dex ID.
    Returns a dict with keys: id, name, types, stats, abilities, moves,
    height, weight, base_experience, sprites.
    Returns None if not found.
    """
    raw = _get(f"pokemon/{str(name_or_id).lower()}")
    if raw is None:
        return None

    return {
        "id": raw["id"],
        "name": raw["name"].capitalize(),
        "height": raw["height"],          # decimetres
        "weight": raw["weight"],          # hectograms
        "base_experience": raw["base_experience"],
        "types": [t["type"]["name"] for t in raw["types"]],
        "abilities": [
            {"name": a["ability"]["name"], "hidden": a["is_hidden"]}
            for a in raw["abilities"]
        ],
        "stats": {s["stat"]["name"]: s["base_stat"] for s in raw["stats"]},
        "moves": [m["move"]["name"] for m in raw["moves"]],
        "sprite": raw["sprites"]["front_default"],
        "sprite_shiny": raw["sprites"]["front_shiny"],
    }


def get_species(name_or_id: str | int) -> Optional[dict]:
    """
    Fetch species-level data: flavor text, genera, evolution chain URL,
    legendary/mythical flags, and habitat.
    """
    raw = _get(f"pokemon-species/{str(name_or_id).lower()}")
    if raw is None:
        return None

    # Pick English flavor text (latest entry)
    flavor = next(
        (
            e["flavor_text"].replace("\n", " ").replace("\f", " ")
            for e in reversed(raw["flavor_text_entries"])
            if e["language"]["name"] == "en"
        ),
        "No description available.",
    )

    genus = next(
        (g["genus"] for g in raw["genera"] if g["language"]["name"] == "en"),
        "",
    )

    return {
        "flavor_text": flavor,
        "genus": genus,
        "is_legendary": raw["is_legendary"],
        "is_mythical": raw["is_mythical"],
        "habitat": raw["habitat"]["name"] if raw["habitat"] else "unknown",
        "evolution_chain_url": raw["evolution_chain"]["url"],
        "capture_rate": raw["capture_rate"],
        "base_happiness": raw["base_happiness"],
        "growth_rate": raw["growth_rate"]["name"],
    }


# ── Evolution chain ──────────────────────────────────────────────────────────

def _parse_chain(link: dict) -> list[str]:
    """Recursively flatten an evolution chain into a list of names."""
    names = [link["species"]["name"].capitalize()]
    for evolution in link.get("evolves_to", []):
        names.extend(_parse_chain(evolution))
    return names


def get_evolution_chain(url: str) -> list[str]:
    """
    Given a full evolution chain URL (from get_species), return an ordered
    list of Pokémon names in the chain.
    """
    # Strip base URL to get just the path segment
    endpoint = url.replace(f"{BASE_URL}/", "")
    raw = _get(endpoint)
    if raw is None:
        return []
    return _parse_chain(raw["chain"])


# ── Type ─────────────────────────────────────────────────────────────────────

def get_type_matchups(type_name: str) -> Optional[dict]:
    """
    Return damage relations for a given type name.
    Keys: double_damage_to, half_damage_to, no_damage_to,
          double_damage_from, half_damage_from, no_damage_from
    """
    raw = _get(f"type/{type_name.lower()}")
    if raw is None:
        return None

    dr = raw["damage_relations"]
    return {
        "double_damage_to":   [t["name"] for t in dr["double_damage_to"]],
        "half_damage_to":     [t["name"] for t in dr["half_damage_to"]],
        "no_damage_to":       [t["name"] for t in dr["no_damage_to"]],
        "double_damage_from": [t["name"] for t in dr["double_damage_from"]],
        "half_damage_from":   [t["name"] for t in dr["half_damage_from"]],
        "no_damage_from":     [t["name"] for t in dr["no_damage_from"]],
    }


# ── Listing ──────────────────────────────────────────────────────────────────

def list_pokemon(limit: int = 20, offset: int = 0) -> dict:
    """
    Return a page of Pokémon names and their API URLs.
    Dict keys: count (total), next_offset, results [{name, url}]
    """
    raw = _get(f"pokemon?limit={limit}&offset={offset}")
    if raw is None:
        return {"count": 0, "next_offset": None, "results": []}

    next_offset = offset + limit if (offset + limit) < raw["count"] else None
    return {
        "count": raw["count"],
        "next_offset": next_offset,
        "results": [{"name": r["name"].capitalize(), "url": r["url"]} for r in raw["results"]],
    }