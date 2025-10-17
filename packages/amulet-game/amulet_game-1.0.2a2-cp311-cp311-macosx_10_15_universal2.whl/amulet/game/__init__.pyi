"""
A module to store data about the game including state enumerations and translations between different game versions.
"""

from __future__ import annotations

from amulet.game.bedrock._version import BedrockGameVersion
from amulet.game.game import game_platforms, game_versions, get_game_version
from amulet.game.java.version import JavaGameVersion

from . import _amulet_game, _version, abc, bedrock, game, java, translate

__all__: list[str] = [
    "BedrockGameVersion",
    "JavaGameVersion",
    "abc",
    "bedrock",
    "compiler_config",
    "game",
    "game_platforms",
    "game_versions",
    "get_game_version",
    "java",
    "translate",
]

def _init() -> None: ...

__version__: str
compiler_config: dict
