from __future__ import annotations

import collections.abc
import typing

import amulet.core.block
import amulet.core.version

__all__: list[str] = ["BlockPalette"]

class BlockPalette(amulet.core.version.VersionRangeContainer):
    @typing.overload
    def __contains__(self, arg0: typing.SupportsInt) -> bool: ...
    @typing.overload
    def __contains__(self, arg0: amulet.core.block.BlockStack) -> bool: ...
    @typing.overload
    def __getitem__(self, arg0: typing.SupportsInt) -> amulet.core.block.BlockStack: ...
    @typing.overload
    def __getitem__(self, item: slice) -> list[amulet.core.block.BlockStack]: ...
    def __init__(self, arg0: amulet.core.version.VersionRange) -> None: ...
    def __iter__(self) -> collections.abc.Iterator[amulet.core.block.BlockStack]: ...
    def __len__(self) -> int: ...
    def __repr__(self) -> str: ...
    def __reversed__(
        self,
    ) -> collections.abc.Iterator[amulet.core.block.BlockStack]: ...
    def block_stack_to_index(self, arg0: amulet.core.block.BlockStack) -> int:
        """
        Get the index of the block stack in the palette.
        If it is not in the palette already it will be added first.

        :param block_stack: The block stack to get the index of.
        :return: The index of the block stack in the palette.
        """

    def count(self, value: amulet.core.block.BlockStack) -> int: ...
    def index(
        self,
        value: amulet.core.block.BlockStack,
        start: typing.SupportsInt = 0,
        stop: typing.SupportsInt = 9223372036854775807,
    ) -> int: ...
    def index_to_block_stack(
        self, arg0: typing.SupportsInt
    ) -> amulet.core.block.BlockStack:
        """
        Get the block stack at the specified palette index.

        :param index: The index to get
        :return: The block stack at that index
        :raises IndexError if there is no block stack at that index.
        """
