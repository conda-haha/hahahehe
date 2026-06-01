"""PvP system prompt builder — single source of truth for all env games.

Loads core/config/pvp_game_prompts.yml (canonical copy from G.O.D-game) so
that SFT trajectory data is trained with the exact same system prompt the
validator uses at PvP eval time.

Usage:
    from envs.pvp_format import SYSTEM_PROMPT_LIARS_DICE
    from envs.pvp_format import SYSTEM_PROMPT_GIN_RUMMY
    from envs.pvp_format import SYSTEM_PROMPT_LEDUC_POKER
"""

from pathlib import Path

import yaml

_PROMPTS_PATH = Path(__file__).resolve().parent / "pvp_assets" / "pvp_game_prompts.yml"


def _load_prompts() -> dict[str, str]:
    with open(_PROMPTS_PATH) as f:
        return yaml.safe_load(f)


def build_system_prompt(game_name: str) -> str:
    prompts = _load_prompts()
    rules_key = f"{game_name}_rules"
    if rules_key not in prompts:
        raise ValueError(f"Unknown game: {game_name!r} (no {rules_key} in pvp_game_prompts.yml)")
    return prompts["system_prompt_template"].format(game_name=game_name, rules=prompts[rules_key])


SYSTEM_PROMPT_LIARS_DICE  = build_system_prompt("liars_dice")
SYSTEM_PROMPT_GIN_RUMMY   = build_system_prompt("gin_rummy")
SYSTEM_PROMPT_LEDUC_POKER = build_system_prompt("leduc_poker")
