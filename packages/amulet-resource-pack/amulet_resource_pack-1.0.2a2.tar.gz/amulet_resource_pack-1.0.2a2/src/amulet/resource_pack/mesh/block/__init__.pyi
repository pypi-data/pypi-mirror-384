from __future__ import annotations

import collections.abc
import typing

import numpy
from amulet.resource_pack.mesh.block._cube import get_cube, get_unit_cube

from . import _cube

__all__ = [
    "BlockMesh",
    "BlockMeshCullDirection",
    "BlockMeshPart",
    "BlockMeshTransparency",
    "CUBE_FACE_LUT",
    "FACE_KEYS",
    "FloatVec2",
    "FloatVec3",
    "TRI_FACE",
    "Triangle",
    "UV_ROTATION_LUT",
    "Vertex",
    "get_cube",
    "get_unit_cube",
    "merge_block_meshes",
]

class BlockMesh:
    """
    All the data that makes up a block mesh.
    """

    def __init__(
        self,
        transparency: BlockMeshTransparency,
        textures: collections.abc.Sequence[str],
        parts: tuple[
            amulet.resource_pack.mesh.block.BlockMeshPart | None,
            amulet.resource_pack.mesh.block.BlockMeshPart | None,
            amulet.resource_pack.mesh.block.BlockMeshPart | None,
            amulet.resource_pack.mesh.block.BlockMeshPart | None,
            amulet.resource_pack.mesh.block.BlockMeshPart | None,
            amulet.resource_pack.mesh.block.BlockMeshPart | None,
            amulet.resource_pack.mesh.block.BlockMeshPart | None,
        ],
    ) -> None: ...
    def rotate(self, rotx: typing.SupportsInt, roty: typing.SupportsInt) -> BlockMesh:
        """
        Rotate the mesh in the x and y axis. Accepted values are -3 to 3 which correspond to 90 degree rotations.
        """

    @property
    def parts(
        self,
    ) -> tuple[
        amulet.resource_pack.mesh.block.BlockMeshPart | None,
        amulet.resource_pack.mesh.block.BlockMeshPart | None,
        amulet.resource_pack.mesh.block.BlockMeshPart | None,
        amulet.resource_pack.mesh.block.BlockMeshPart | None,
        amulet.resource_pack.mesh.block.BlockMeshPart | None,
        amulet.resource_pack.mesh.block.BlockMeshPart | None,
        amulet.resource_pack.mesh.block.BlockMeshPart | None,
    ]:
        """
        The mesh parts that make up this mesh. The index corresponds to the value of BlockMeshCullDirection.
        """

    @property
    def textures(self) -> list[str]:
        """
        The texture paths used in this block mesh. The Triangle's texture_index attribute is an index into this list.
        """

    @property
    def transparency(self) -> BlockMeshTransparency:
        """
        The transparency state of this block mesh.
        """

class BlockMeshCullDirection:
    """
    The direction a mesh part is culled by. The value corresponds to the index in the mesh parts array.

    Members:

      CullNone : Is not culled by any neighbouring blocks.

      CullUp : Is culled by an opaque block above.

      CullDown : Is culled by an opaque block below.

      CullNorth : Is culled by an opaque block to the north.

      CullEast : Is culled by an opaque block to the east.

      CullSouth : Is culled by an opaque block to the south.

      CullWest : Is culled by an opaque block to the west.
    """

    CullDown: typing.ClassVar[
        BlockMeshCullDirection
    ]  # value = <BlockMeshCullDirection.CullDown: 2>
    CullEast: typing.ClassVar[
        BlockMeshCullDirection
    ]  # value = <BlockMeshCullDirection.CullEast: 4>
    CullNone: typing.ClassVar[
        BlockMeshCullDirection
    ]  # value = <BlockMeshCullDirection.CullNone: 0>
    CullNorth: typing.ClassVar[
        BlockMeshCullDirection
    ]  # value = <BlockMeshCullDirection.CullNorth: 3>
    CullSouth: typing.ClassVar[
        BlockMeshCullDirection
    ]  # value = <BlockMeshCullDirection.CullSouth: 5>
    CullUp: typing.ClassVar[
        BlockMeshCullDirection
    ]  # value = <BlockMeshCullDirection.CullUp: 1>
    CullWest: typing.ClassVar[
        BlockMeshCullDirection
    ]  # value = <BlockMeshCullDirection.CullWest: 6>
    __members__: typing.ClassVar[
        dict[str, BlockMeshCullDirection]
    ]  # value = {'CullNone': <BlockMeshCullDirection.CullNone: 0>, 'CullUp': <BlockMeshCullDirection.CullUp: 1>, 'CullDown': <BlockMeshCullDirection.CullDown: 2>, 'CullNorth': <BlockMeshCullDirection.CullNorth: 3>, 'CullEast': <BlockMeshCullDirection.CullEast: 4>, 'CullSouth': <BlockMeshCullDirection.CullSouth: 5>, 'CullWest': <BlockMeshCullDirection.CullWest: 6>}
    def __and__(self, other: typing.Any) -> typing.Any: ...
    def __eq__(self, other: typing.Any) -> bool: ...
    def __ge__(self, other: typing.Any) -> bool: ...
    def __gt__(self, other: typing.Any) -> bool: ...
    def __hash__(self) -> int: ...
    def __index__(self) -> int: ...
    def __init__(self, value: typing.SupportsInt) -> None: ...
    def __int__(self) -> int: ...
    def __invert__(self) -> typing.Any: ...
    def __le__(self, other: typing.Any) -> bool: ...
    def __lt__(self, other: typing.Any) -> bool: ...
    def __ne__(self, other: typing.Any) -> bool: ...
    def __or__(self, other: typing.Any) -> typing.Any: ...
    def __rand__(self, other: typing.Any) -> typing.Any: ...
    def __repr__(self) -> str: ...
    def __ror__(self, other: typing.Any) -> typing.Any: ...
    def __rxor__(self, other: typing.Any) -> typing.Any: ...
    def __str__(self) -> str: ...
    def __xor__(self, other: typing.Any) -> typing.Any: ...
    @property
    def name(self) -> str: ...
    @property
    def value(self) -> int: ...

class BlockMeshPart:
    """
    A part of a block mesh for one of the culling directions.
    """

    def __init__(
        self,
        verts: collections.abc.Sequence[Vertex],
        triangles: collections.abc.Sequence[Triangle],
    ) -> None: ...
    @property
    def triangles(self) -> list[Triangle]:
        """
        The triangles in this block mesh part.
        """

    @property
    def verts(self) -> list[Vertex]:
        """
        The vertices in this block mesh part.
        """

class BlockMeshTransparency:
    """
    The transparency of a block mesh.

    Members:

      FullOpaque : A block that occupies the whole block and is opaque.

      FullTranslucent : A block that occupies the whole block and has at least one translucent face.

      Partial : A block that does not occupy the whole block.
    """

    FullOpaque: typing.ClassVar[
        BlockMeshTransparency
    ]  # value = <BlockMeshTransparency.FullOpaque: 0>
    FullTranslucent: typing.ClassVar[
        BlockMeshTransparency
    ]  # value = <BlockMeshTransparency.FullTranslucent: 1>
    Partial: typing.ClassVar[
        BlockMeshTransparency
    ]  # value = <BlockMeshTransparency.Partial: 2>
    __members__: typing.ClassVar[
        dict[str, BlockMeshTransparency]
    ]  # value = {'FullOpaque': <BlockMeshTransparency.FullOpaque: 0>, 'FullTranslucent': <BlockMeshTransparency.FullTranslucent: 1>, 'Partial': <BlockMeshTransparency.Partial: 2>}
    def __eq__(self, other: typing.Any) -> bool: ...
    def __ge__(self, other: typing.Any) -> bool: ...
    def __gt__(self, other: typing.Any) -> bool: ...
    def __hash__(self) -> int: ...
    def __index__(self) -> int: ...
    def __init__(self, value: typing.SupportsInt) -> None: ...
    def __int__(self) -> int: ...
    def __le__(self, other: typing.Any) -> bool: ...
    def __lt__(self, other: typing.Any) -> bool: ...
    def __ne__(self, other: typing.Any) -> bool: ...
    def __repr__(self) -> str: ...
    def __str__(self) -> str: ...
    @property
    def name(self) -> str: ...
    @property
    def value(self) -> int: ...

class FloatVec2:
    """
    A 2D floating point vector
    """

    def __init__(self, x: typing.SupportsFloat, y: typing.SupportsFloat) -> None: ...
    @property
    def x(self) -> float: ...
    @property
    def y(self) -> float: ...

class FloatVec3:
    """
    A 3D floating point vector
    """

    def __init__(
        self, x: typing.SupportsFloat, y: typing.SupportsFloat, z: typing.SupportsFloat
    ) -> None: ...
    @property
    def x(self) -> float: ...
    @property
    def y(self) -> float: ...
    @property
    def z(self) -> float: ...

class Triangle:
    """
    The vertex and texture indexes that make up a triangle.
    """

    def __init__(
        self,
        vert_index_a: typing.SupportsInt,
        vert_index_b: typing.SupportsInt,
        vert_index_c: typing.SupportsInt,
        texture_index: typing.SupportsInt,
    ) -> None: ...
    @property
    def texture_index(self) -> int: ...
    @property
    def vert_index_a(self) -> int: ...
    @property
    def vert_index_b(self) -> int: ...
    @property
    def vert_index_c(self) -> int: ...

class Vertex:
    """
    Attributes for a single vertex.
    """

    def __init__(
        self, coord: FloatVec3, texture_coord: FloatVec2, tint: FloatVec3
    ) -> None: ...
    @property
    def coord(self) -> FloatVec3:
        """
        The spatial coordinate of the vertex.
        """

    @property
    def texture_coord(self) -> FloatVec2:
        """
        The texture coordinate of the vertex.
        """

    @property
    def tint(self) -> FloatVec3:
        """
        The tint colour for the vertex.
        """

def merge_block_meshes(meshes: collections.abc.Sequence[BlockMesh]) -> BlockMesh:
    """
    Merge multiple block mesh objects into one block mesh.
    """

CUBE_FACE_LUT: dict  # value = {'down': array([0, 4, 5, 1]), 'up': array([3, 7, 6, 2]), 'north': array([4, 0, 2, 6]), 'east': array([5, 4, 6, 7]), 'south': array([1, 5, 7, 3]), 'west': array([0, 1, 3, 2])}
FACE_KEYS: dict  # value = {None: <BlockMeshCullDirection.CullNone: 0>, 'up': <BlockMeshCullDirection.CullUp: 1>, 'down': <BlockMeshCullDirection.CullDown: 2>, 'north': <BlockMeshCullDirection.CullNorth: 3>, 'east': <BlockMeshCullDirection.CullEast: 4>, 'south': <BlockMeshCullDirection.CullSouth: 5>, 'west': <BlockMeshCullDirection.CullWest: 6>}
TRI_FACE: numpy.ndarray  # value = array([0, 1, 2, 0, 2, 3], dtype=uint32)
UV_ROTATION_LUT: list = [0, 3, 2, 3, 2, 1, 0, 1]
