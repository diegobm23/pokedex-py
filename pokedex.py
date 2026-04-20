"""
pokedex.py — A CLI Pokédex powered by PokéAPI
Usage: python pokedex.py
"""

import sys
import textwrap
from pokeapi import (
    get_pokemon,
    get_species,
    get_evolution_chain,
    get_type_matchups,
    list_pokemon,
)

# ── ANSI colour palette ───────────────────────────────────────────────────────

RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"

RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
MAGENTA= "\033[95m"
CYAN   = "\033[96m"
WHITE  = "\033[97m"

TYPE_COLORS = {
    "fire":     "\033[38;5;202m",
    "water":    "\033[38;5;39m",
    "grass":    "\033[38;5;34m",
    "electric": "\033[38;5;220m",
    "psychic":  "\033[38;5;205m",
    "ice":      "\033[38;5;117m",
    "dragon":   "\033[38;5;57m",
    "dark":     "\033[38;5;94m",
    "fairy":    "\033[38;5;213m",
    "fighting": "\033[38;5;160m",
    "poison":   "\033[38;5;90m",
    "ground":   "\033[38;5;136m",
    "flying":   "\033[38;5;111m",
    "bug":      "\033[38;5;70m",
    "rock":     "\033[38;5;137m",
    "ghost":    "\033[38;5;61m",
    "steel":    "\033[38;5;250m",
    "normal":   "\033[38;5;252m",
}

STAT_COLORS = {
    "hp":              GREEN,
    "attack":          RED,
    "defense":         YELLOW,
    "special-attack":  MAGENTA,
    "special-defense": CYAN,
    "speed":           BLUE,
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def color_type(type_name: str) -> str:
    c = TYPE_COLORS.get(type_name, WHITE)
    return f"{c}{BOLD}[{type_name.upper()}]{RESET}"


def stat_bar(value: int, max_val: int = 255, width: int = 20) -> str:
    filled = round(value / max_val * width)
    bar = "█" * filled + "░" * (width - filled)
    return bar


def hr(char: str = "─", width: int = 54) -> str:
    return DIM + char * width + RESET


def section(title: str) -> str:
    pad = (50 - len(title)) // 2
    return f"\n{BOLD}{CYAN}{'─' * pad} {title} {'─' * pad}{RESET}\n"


def wrap(text: str, width: int = 54, indent: str = "  ") -> str:
    return textwrap.fill(text, width=width, initial_indent=indent, subsequent_indent=indent)


def badge(label: str, color: str = YELLOW) -> str:
    return f"{color}{BOLD} {label} {RESET}"


# ── Views ─────────────────────────────────────────────────────────────────────

def display_pokemon(name_or_id: str):
    print(f"\n{DIM}Fetching Pokémon data…{RESET}")

    poke = get_pokemon(name_or_id)
    if poke is None:
        print(f"{RED}✘ Pokémon '{name_or_id}' not found.{RESET}\n")
        return

    species = get_species(poke["id"])

    # ── Header ────────────────────────────────────────────────────────────────
    types_str = "  ".join(color_type(t) for t in poke["types"])
    flags = ""
    if species:
        if species["is_legendary"]:
            flags += badge("★ LEGENDARY", YELLOW)
        if species["is_mythical"]:
            flags += badge("✦ MYTHICAL", MAGENTA)

    print(hr("═"))
    print(f"  {BOLD}{WHITE}#{poke['id']:04d}  {poke['name'].upper()}{RESET}  {flags}")
    if species:
        print(f"  {DIM}{species['genus']}{RESET}")
    print(f"  {types_str}")
    print(hr("═"))

    # ── Flavor text ───────────────────────────────────────────────────────────
    if species:
        print(wrap(f'"{species["flavor_text"]}"', indent="  "))

    # ── Physical ──────────────────────────────────────────────────────────────
    print(section("INFO"))
    height_m  = poke["height"] / 10
    weight_kg = poke["weight"] / 10
    print(f"  Height        {CYAN}{height_m:.1f} m{RESET}")
    print(f"  Weight        {CYAN}{weight_kg:.1f} kg{RESET}")
    print(f"  Base EXP      {CYAN}{poke['base_experience']}{RESET}")
    if species:
        print(f"  Habitat       {CYAN}{species['habitat']}{RESET}")
        print(f"  Capture rate  {CYAN}{species['capture_rate']}{RESET}")
        print(f"  Growth rate   {CYAN}{species['growth_rate']}{RESET}")

    # ── Stats ─────────────────────────────────────────────────────────────────
    print(section("BASE STATS"))
    for stat_name, value in poke["stats"].items():
        color = STAT_COLORS.get(stat_name, WHITE)
        bar   = stat_bar(value)
        label = stat_name.replace("-", " ").title().ljust(16)
        print(f"  {color}{label}{RESET} {bar} {BOLD}{value:>3}{RESET}")

    # ── Abilities ─────────────────────────────────────────────────────────────
    print(section("ABILITIES"))
    for ab in poke["abilities"]:
        tag = f"{DIM}(hidden){RESET}" if ab["hidden"] else ""
        print(f"  • {CYAN}{ab['name'].replace('-', ' ').title()}{RESET} {tag}")

    # ── Evolution chain ───────────────────────────────────────────────────────
    if species:
        chain = get_evolution_chain(species["evolution_chain_url"])
        if chain:
            print(section("EVOLUTION CHAIN"))
            print("  " + f"  {YELLOW}→{RESET}  ".join(
                f"{BOLD}{n}{RESET}" for n in chain
            ))

    # ── First 10 moves ────────────────────────────────────────────────────────
    print(section("MOVES (first 10)"))
    sample = poke["moves"][:10]
    cols = [sample[i:i+2] for i in range(0, len(sample), 2)]
    for pair in cols:
        row = "".join(f"  • {m.replace('-', ' ').title():<26}" for m in pair)
        print(row)

    print("\n" + hr("═") + "\n")


def display_type(type_name: str):
    print(f"\n{DIM}Fetching type data…{RESET}")
    data = get_type_matchups(type_name)
    if data is None:
        print(f"{RED}✘ Type '{type_name}' not found.{RESET}\n")
        return

    print(hr("═"))
    print(f"  {BOLD}{color_type(type_name)}  TYPE MATCHUPS{RESET}")
    print(hr("═"))

    def fmt_types(types):
        if not types:
            return f"{DIM}none{RESET}"
        return "  ".join(color_type(t) for t in types)

    print(section("OFFENSIVE"))
    print(f"  2×  damage to:  {fmt_types(data['double_damage_to'])}")
    print(f"  ½×  damage to:  {fmt_types(data['half_damage_to'])}")
    print(f"  0×  damage to:  {fmt_types(data['no_damage_to'])}")

    print(section("DEFENSIVE"))
    print(f"  2×  damage from:  {fmt_types(data['double_damage_from'])}")
    print(f"  ½×  damage from:  {fmt_types(data['half_damage_from'])}")
    print(f"  0×  damage from:  {fmt_types(data['no_damage_from'])}")
    print("\n" + hr("═") + "\n")


def display_list(offset: int = 0, limit: int = 20):
    print(f"\n{DIM}Fetching Pokémon list…{RESET}")
    page = list_pokemon(limit=limit, offset=offset)
    results = page["results"]

    print(hr("═"))
    print(f"  {BOLD}POKÉMON LIST{RESET}  {DIM}(#{offset+1}–#{offset+len(results)} of {page['count']}){RESET}")
    print(hr("═"))

    cols = 4
    for i in range(0, len(results), cols):
        row = results[i:i+cols]
        print("".join(f"  {CYAN}{r['name']:<18}{RESET}" for r in row))

    if page["next_offset"] is not None:
        print(f"\n  {DIM}Type 'list {page['next_offset']}' to see more.{RESET}")
    print()


# ── Help ──────────────────────────────────────────────────────────────────────

HELP_TEXT = f"""
{BOLD}{CYAN}╔══════════════════════════════════════╗
║       P O K É D E X   CLI  v1.0     ║
╚══════════════════════════════════════╝{RESET}

{BOLD}Commands:{RESET}
  {GREEN}<name>{RESET}           Search a Pokémon by name  (e.g. {YELLOW}pikachu{RESET})
  {GREEN}<id>{RESET}             Search a Pokémon by Dex # (e.g. {YELLOW}25{RESET})
  {GREEN}type <name>{RESET}      Show type matchups         (e.g. {YELLOW}type fire{RESET})
  {GREEN}list [offset]{RESET}    Browse all Pokémon         (e.g. {YELLOW}list 20{RESET})
  {GREEN}help{RESET}             Show this help screen
  {GREEN}quit / exit{RESET}      Exit the Pokédex

{DIM}Data provided by https://pokeapi.co — no API key required.{RESET}
"""


# ── Main REPL ─────────────────────────────────────────────────────────────────

def main():
    print(HELP_TEXT)

    while True:
        try:
            raw = input(f"{BOLD}{RED}pokédex{RESET} {DIM}›{RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{DIM}Goodbye!{RESET}")
            sys.exit(0)

        if not raw:
            continue

        parts = raw.lower().split()
        cmd   = parts[0]

        if cmd in ("quit", "exit", "q"):
            print(f"\n{DIM}Goodbye!{RESET}")
            break

        elif cmd == "help":
            print(HELP_TEXT)

        elif cmd == "type":
            if len(parts) < 2:
                print(f"{RED}Usage: type <type_name>{RESET}\n")
            else:
                display_type(parts[1])

        elif cmd == "list":
            offset = 0
            if len(parts) >= 2:
                try:
                    offset = int(parts[1])
                except ValueError:
                    print(f"{RED}Usage: list [offset]{RESET}\n")
                    continue
            display_list(offset=offset)

        else:
            # Treat entire input as a Pokémon name or ID
            display_pokemon(raw)


if __name__ == "__main__":
    main()
