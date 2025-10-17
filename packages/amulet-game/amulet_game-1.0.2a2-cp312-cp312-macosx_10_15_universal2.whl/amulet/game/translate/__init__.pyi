"""
A package to support translating block and entity data between versions.
Everything that is not imported into this module is an implementation detail.
"""

from __future__ import annotations

from amulet.game.translate._translator import (
    BlockFromUniversalTranslator,
    BlockToUniversalTranslator,
    EntityFromUniversalTranslator,
    EntityToUniversalTranslator,
    load_json_block_translations,
)

from . import _functions, _translator

__all__: list[str] = [
    "BlockFromUniversalTranslator",
    "BlockToUniversalTranslator",
    "EntityFromUniversalTranslator",
    "EntityToUniversalTranslator",
    "load_json_block_translations",
]
