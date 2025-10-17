from __future__ import annotations

import collections.abc
import types
import typing

import amulet.core.selection.box
import amulet.core.selection.shape_group
import amulet.utils.matrix

__all__: list[str] = ["SelectionBoxGroup"]

class SelectionBoxGroup:
    """
    A container for zero or more :class:`SelectionBox` instances.

    This allows for non-rectangular and non-contiguous selections.
    """

    __hash__: typing.ClassVar[None] = None  # type: ignore
    def __bool__(self) -> bool:
        """
        Are there any selections in the group.
        """

    @typing.overload
    def __eq__(self, other: SelectionBoxGroup) -> bool:
        """
        Does the contents of this :class:`SelectionBoxGroup` match the other :class:`SelectionBoxGroup`.

        Note if the boxes do not exactly match this will return False even if the volume represented is the same.

        :param other: The other :class:`SelectionBoxGroup` to compare with.
        :return: True if the boxes contained match.
        """

    @typing.overload
    def __eq__(self, other: typing.Any) -> bool | types.NotImplementedType: ...
    @typing.overload
    def __init__(self) -> None:
        """
        Create an empty SelectionBoxGroup.

        >>> SelectionBoxGroup()
        """

    @typing.overload
    def __init__(
        self, shape_group: amulet.core.selection.shape_group.SelectionShapeGroup
    ) -> None: ...
    @typing.overload
    def __init__(
        self, boxes: collections.abc.Iterable[amulet.core.selection.box.SelectionBox]
    ) -> None:
        """
        Create a SelectionBoxGroup from the boxes in the iterable.

        >>> SelectionBoxGroup([
        >>>     SelectionBox(0, 0, 0, 1, 1, 1),
        >>>     SelectionBox(1, 1, 1, 1, 1, 1)
        >>> ])
        """

    def __iter__(
        self,
    ) -> collections.abc.Iterator[amulet.core.selection.box.SelectionBox]:
        """
        An iterable of all the :class:`SelectionBox` classes in the group.
        """

    def __len__(self) -> int:
        """
        The number of :class:`SelectionBox` classes in the group.
        """

    def __repr__(self) -> str: ...
    def __str__(self) -> str: ...
    def contains_block(
        self, x: typing.SupportsInt, y: typing.SupportsInt, z: typing.SupportsInt
    ) -> bool:
        """
        Is the block contained within the selection.

        >>> selection1: AbstractBaseSelection
        >>> (1, 2, 3) in selection1
        True

        :param x: The x coordinate of the block. Defined by the most negative corner.
        :param y: The y coordinate of the block. Defined by the most negative corner.
        :param z: The z coordinate of the block. Defined by the most negative corner.
        :return: True if the block is in the selection.
        """

    def contains_point(
        self, x: typing.SupportsFloat, y: typing.SupportsFloat, z: typing.SupportsFloat
    ) -> bool:
        """
        Is the point contained within the selection.

        >>> selection1: AbstractBaseSelection
        >>> (1.5, 2.5, 3.5) in selection1
        True

        :param x: The x coordinate of the point.
        :param y: The y coordinate of the point.
        :param z: The z coordinate of the point.
        :return: True if the point is in the selection.
        """

    @typing.overload
    def intersects(self, other: amulet.core.selection.box.SelectionBox) -> bool:
        """
        Does this selection intersect ``other``.

        :param other: The other selection.
        :return: True if the selections intersect, False otherwise.
        """

    @typing.overload
    def intersects(self, other: SelectionBoxGroup) -> bool: ...
    def transform(self, matrix: amulet.utils.matrix.Matrix4x4) -> SelectionBoxGroup:
        """
        Transform the boxes in this group by the given transformation matrix.
        """

    def translate(
        self, dx: typing.SupportsInt, dy: typing.SupportsInt, dz: typing.SupportsInt
    ) -> SelectionBoxGroup:
        """
        Create a new :class:`SelectionBoxGroup` based on this one with the coordinates moved by the given offset.

        :param dx: The x offset.
        :param dy: The y offset.
        :param dz: The z offset.
        :return: The new selection with the given offset.
        """

    @property
    def bounding_box(self) -> amulet.core.selection.box.SelectionBox:
        """
        A SelectionBox containing this entire selection.

        :raises RuntimeError: If there are no boxes in the selection.
        """

    @property
    def bounds(self) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
        """
        The minimum and maximum x, y and z coordinates in the selection.

        :raises RuntimeError: If there are no boxes in the selection.
        """

    @property
    def boxes(self) -> collections.abc.Iterator[amulet.core.selection.box.SelectionBox]:
        """
        An iterator of the :class:`SelectionBox` instances stored for this group.
        """

    @property
    def max(self) -> tuple[int, int, int]:
        """
        The maximum x, y and z coordinates in the selection.

        :raises RuntimeError: If there are no boxes in the selection.
        """

    @property
    def max_x(self) -> int:
        """
        The maximum x coordinate in the selection.

        :raises RuntimeError: If there are no boxes in the selection.
        """

    @property
    def max_y(self) -> int:
        """
        The maximum y coordinate in the selection.

        :raises RuntimeError: If there are no boxes in the selection.
        """

    @property
    def max_z(self) -> int:
        """
        The maximum z coordinate in the selection.

        :raises RuntimeError: If there are no boxes in the selection.
        """

    @property
    def min(self) -> tuple[int, int, int]:
        """
        The minimum x, y and z coordinates in the selection.

        :raises RuntimeError: If there are no boxes in the selection.
        """

    @property
    def min_x(self) -> int:
        """
        The minimum x coordinate in the selection.

        :raises RuntimeError: If there are no boxes in the selection.
        """

    @property
    def min_y(self) -> int:
        """
        The minimum y coordinate in the selection.

        :raises RuntimeError: If there are no boxes in the selection.
        """

    @property
    def min_z(self) -> int:
        """
        The minimum z coordinate in the selection.

        :raises RuntimeError: If there are no boxes in the selection.
        """
