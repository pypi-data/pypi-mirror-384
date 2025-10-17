from __future__ import annotations

import typing

import amulet.core.block
import amulet.core.chunk.component.section_array_map
import amulet.core.palette.block_palette
import amulet.core.version

__all__: list[str] = ["BlockComponent", "BlockStorage"]

class BlockComponent:
    ComponentID: typing.ClassVar[str] = "Amulet::BlockComponent"
    block_storage: BlockStorage

class BlockStorage:
    def __init__(
        self,
        version_range: amulet.core.version.VersionRange,
        array_shape: tuple[typing.SupportsInt, typing.SupportsInt, typing.SupportsInt],
        default_block: amulet.core.block.BlockStack,
    ) -> None: ...
    @property
    def palette(self) -> amulet.core.palette.block_palette.BlockPalette: ...
    @property
    def sections(
        self,
    ) -> amulet.core.chunk.component.section_array_map.SectionArrayMap: ...
