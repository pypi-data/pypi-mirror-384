from __future__ import annotations

import typing

from amulet.game.abc._block_specification import (
    BlockSpec,
    NBTSpec,
    PropertySpec,
    PropertyValueSpec,
    load_json_block_spec,
)
from amulet.game.abc.biome import (
    BiomeData,
    BiomeDataNumericalComponent,
    BiomeTranslationError,
    DatabaseBiomeData,
    load_json_biome_data,
)
from amulet.game.abc.block import (
    BlockData,
    BlockDataNumericalComponent,
    BlockTranslationError,
    DatabaseBlockData,
)
from amulet.game.abc.json_interface import JSONInterface
from amulet.game.abc.version import GameVersion

from . import (
    _block_specification,
    biome,
    block,
    game_version_container,
    json_interface,
    version,
)

__all__: list[str] = [
    "BiomeData",
    "BiomeDataNumericalComponent",
    "BiomeTranslationError",
    "BlockData",
    "BlockDataNumericalComponent",
    "BlockSpec",
    "BlockTranslationError",
    "DatabaseBiomeData",
    "DatabaseBlockData",
    "GameVersion",
    "JSONCompatible",
    "JSONDict",
    "JSONInterface",
    "JSONList",
    "NBTSpec",
    "PropertySpec",
    "PropertyValueSpec",
    "biome",
    "block",
    "game_version_container",
    "json_interface",
    "load_json_biome_data",
    "load_json_block_spec",
    "version",
]
JSONCompatible: (
    typing._UnionGenericAlias
)  # value = typing.Union[str, int, float, bool, NoneType, ForwardRef('JSONList'), ForwardRef('JSONDict')]
JSONDict: typing.TypeAlias = dict[str, "JSONCompatible"]
JSONList: typing.TypeAlias = list["JSONCompatible"]
