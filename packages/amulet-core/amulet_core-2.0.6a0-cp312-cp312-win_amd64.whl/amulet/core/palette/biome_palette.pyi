from __future__ import annotations

import collections.abc
import typing

import amulet.core.biome
import amulet.core.version

__all__: list[str] = ["BiomePalette"]

class BiomePalette(amulet.core.version.VersionRangeContainer):
    @typing.overload
    def __contains__(self, arg0: typing.SupportsInt) -> bool: ...
    @typing.overload
    def __contains__(self, arg0: amulet.core.biome.Biome) -> bool: ...
    @typing.overload
    def __getitem__(self, arg0: typing.SupportsInt) -> amulet.core.biome.Biome: ...
    @typing.overload
    def __getitem__(self, item: slice) -> list[amulet.core.biome.Biome]: ...
    def __init__(self, arg0: amulet.core.version.VersionRange) -> None: ...
    def __iter__(self) -> collections.abc.Iterator[amulet.core.biome.Biome]: ...
    def __len__(self) -> int: ...
    def __repr__(self) -> str: ...
    def __reversed__(self) -> collections.abc.Iterator[amulet.core.biome.Biome]: ...
    def biome_to_index(self, arg0: amulet.core.biome.Biome) -> int:
        """
        Get the index of the biome in the palette.
        If it is not in the palette already it will be added first.

        :param biome: The biome to get the index of.
        :return: The index of the biome in the palette.
        """

    def count(self, value: amulet.core.biome.Biome) -> int: ...
    def index(
        self,
        value: amulet.core.biome.Biome,
        start: typing.SupportsInt = 0,
        stop: typing.SupportsInt = 9223372036854775807,
    ) -> int: ...
    def index_to_biome(self, arg0: typing.SupportsInt) -> amulet.core.biome.Biome:
        """
        Get the biome at the specified palette index.

        :param index: The index to get
        :return: The biome at that index
        :raises IndexError if there is no biome at that index.
        """
