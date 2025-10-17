from __future__ import annotations

from amulet.game.translate._functions._state import (
    DstData,
    SrcData,
    SrcDataExtra,
    StateData,
)
from amulet.game.translate._functions.abc import AbstractBaseTranslationFunction
from amulet.game.translate._functions.carry_nbt import CarryNBT
from amulet.game.translate._functions.carry_properties import CarryProperties
from amulet.game.translate._functions.code import Code
from amulet.game.translate._functions.map_block_name import MapBlockName
from amulet.game.translate._functions.map_nbt import MapNBT
from amulet.game.translate._functions.map_properties import MapProperties
from amulet.game.translate._functions.multiblock import MultiBlock
from amulet.game.translate._functions.new_block import NewBlock
from amulet.game.translate._functions.new_entity import NewEntity
from amulet.game.translate._functions.new_nbt import NewNBT
from amulet.game.translate._functions.new_properties import NewProperties
from amulet.game.translate._functions.sequence import TranslationFunctionSequence
from amulet.game.translate._functions.walk_input_nbt import WalkInputNBT

from . import (
    _code_functions,
    _frozen,
    _state,
    _typing,
    abc,
    carry_nbt,
    carry_properties,
    code,
    map_block_name,
    map_nbt,
    map_properties,
    multiblock,
    new_block,
    new_entity,
    new_nbt,
    new_properties,
    sequence,
    walk_input_nbt,
)

__all__: list[str] = [
    "AbstractBaseTranslationFunction",
    "CarryNBT",
    "CarryProperties",
    "Code",
    "DstData",
    "MapBlockName",
    "MapNBT",
    "MapProperties",
    "MultiBlock",
    "NewBlock",
    "NewEntity",
    "NewNBT",
    "NewProperties",
    "SrcData",
    "SrcDataExtra",
    "StateData",
    "TranslationFunctionSequence",
    "WalkInputNBT",
    "abc",
    "carry_nbt",
    "carry_properties",
    "code",
    "map_block_name",
    "map_nbt",
    "map_properties",
    "multiblock",
    "new_block",
    "new_entity",
    "new_nbt",
    "new_properties",
    "sequence",
    "walk_input_nbt",
]
