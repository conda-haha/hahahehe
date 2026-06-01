"""Lightweight registry mapping env names to their SFT trajectory generator.

Generators may return either ``list[dict]`` (messages only) or
``tuple[list[dict], float]`` (messages + final reward score).  The score is
used by generate_trajectories.py for optional score-based sampling.

Note: "intercode" is NOT registered here. It uses a separate offline generation
path (envs/intercode_dataset.py) that reads from the validator-mounted miner
dataset rather than an env server. See sft_env_config.py for the routing.
"""

from typing import Callable

from envs.liar_dice_trajectories     import generate_expert_episode as _liar_gen
from envs.gin_rummy_trajectories     import generate_expert_episode as _gin_gen
from envs.leduc_poker_trajectories   import generate_random_episode as _leduc_gen

_SFT_REGISTRY: dict[str, Callable] = {
    "liars_dice":  _liar_gen,
    "gin_rummy":   _gin_gen,
    "leduc_poker": _leduc_gen,
}

# envs that have their own generate path (not via generate_trajectories.py + env server)
_OFFLINE_ENVS: frozenset[str] = frozenset({"intercode"})


def supports_sft(env_name: str) -> bool:
    return env_name in _SFT_REGISTRY or env_name in _OFFLINE_ENVS


def get_sft_trajectory_generator(env_name: str) -> Callable:
    if env_name not in _SFT_REGISTRY:
        raise ValueError(f"No SFT trajectory generator for env: {env_name!r}")
    return _SFT_REGISTRY[env_name]
