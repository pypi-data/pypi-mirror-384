from collections.abc import Sequence, Set
import enum
from typing import (
    Annotated,
    List,
    Literal,
    Optional,
    Union,
    overload
)

import numpy
from numpy.typing import NDArray


invalid_scalar: float = float('inf')

invalid_index: int = 4294967295

class AttributeElement(enum.IntEnum):
    """Attribute element type"""

    Vertex = 1
    """Per-vertex attribute"""

    Facet = 2
    """Per-facet attribute"""

    Edge = 4
    """Per-edge attribute"""

    Corner = 8
    """Per-corner attribute"""

    Value = 16
    """Value attribute not attached to any mesh elements"""

    Indexed = 32
    """Indexed attribute"""

class AttributeUsage(enum.Enum):
    """Attribute usage type"""

    Vector = 1
    """Vector attribute that may have any number of channels"""

    Scalar = 2
    """Scalar attribute that has exactly 1 channel"""

    Position = 4
    """Position attribute must have exactly dim channels"""

    Normal = 8
    """Normal attribute must have exactly dim channels"""

    Tangent = 16
    """Tangent attribute must have exactly dim channels"""

    Bitangent = 32
    """Bitangent attribute must have exactly dim channels"""

    Color = 64
    """Color attribute may have 1, 2, 3 or 4 channels"""

    UV = 128
    """UV attribute has exactly 2 channels"""

    VertexIndex = 256
    """Single channel integer attribute indexing mesh vertices"""

    FacetIndex = 512
    """Single channel integer attribute indexing mesh facets"""

    CornerIndex = 1024
    """Single channel integer attribute indexing mesh corners"""

    EdgeIndex = 2048
    """Single channel integer attribute indexing mesh edges"""

class AttributeCreatePolicy(enum.Enum):
    """Attribute creation policy"""

    ErrorIfReserved = 0
    """Default policy, error if attribute name is reserved"""

    Force = 1
    """Force create attribute even if name is reserved"""

class AttributeGrowthPolicy(enum.Enum):
    """Attribute growth policy (for external buffers)"""

    ErrorIfExtenal = 0
    """Disallow growth if external buffer is used (default)"""

    AllowWithinCapacity = 1
    """
    Allow growth as long as it is within the capacity of the external buffer
    """

    WarnAndCopy = 2
    """
    Warn and copy attribute to internal buffer when growth exceeds external buffer capacity
    """

    SilentCopy = 3
    """
    Silently copy attribute to internal buffer when growth exceeds external buffer capacity
    """

class AttributeShrinkPolicy(enum.Enum):
    """Attribute shrink policy (for external buffers)"""

    ErrorIfExternal = 0
    """Disallow shrink if external buffer is used (default)"""

    IgnoreIfExternal = 1
    """Ignore shrink if external buffer is used"""

    WarnAndCopy = 2
    """
    Warn and copy attribute to internal buffer when shrinking below external buffer capacity
    """

    SilentCopy = 3
    """
    Silently copy attribute to internal buffer when shrinking below external buffer capacity
    """

class AttributeWritePolicy(enum.Enum):
    """Policy for attempting to write to read-only external buffer"""

    ErrorIfReadOnly = 0
    """Disallow writing to read-only external buffer (default)"""

    WarnAndCopy = 1
    """
    Warn and copy attribute to internal buffer when writing to read-only external buffer
    """

    SilentCopy = 2
    """
    Silently copy attribute to internal buffer when writing to read-only external buffer
    """

class AttributeExportPolicy(enum.Enum):
    """Policy for exporting attribute that is a view of an external buffer"""

    CopyIfExternal = 0
    """Copy attribute to internal buffer"""

    CopyIfUnmanaged = 1
    """
    Copy attribute to internal buffer if the external buffer is unmanaged (i.e. not reference counted)
    """

    KeepExternalPtr = 2
    """Keep external buffer pointer"""

    ErrorIfExternal = 3
    """Error if external buffer is used"""

class AttributeCopyPolicy(enum.Enum):
    """Policy for copying attribute that is a view of an external buffer"""

    CopyIfExternal = 0
    """Copy attribute to internal buffer"""

    KeepExternalPtr = 1
    """Keep external buffer pointer"""

    ErrorIfExternal = 2
    """Error if external buffer is used"""

class AttributeCastPolicy(enum.Enum):
    """
    Policy for remapping invalid values when casting to a different value type
    """

    RemapInvalidIndices = 0
    """Map invalid values only if the AttributeUsage represents indices"""

    RemapInvalidAlways = 1
    """
    Always remap invalid values from source type to target type, regardless of AttributeUsage
    """

    DoNotRemapInvalid = 2
    """
    Do not remap invalid values. They are simply static_cast<> to the target type
    """

class AttributeDeletePolicy(enum.Enum):
    """Policy for deleting attributes with reserved names"""

    ErrorIfReserved = 0
    """Disallow deletion (default)"""

    Force = 1
    """Force delete attribute"""

class SurfaceMesh:
    """Surface mesh data structure"""

    def __init__(self, dimension: int = 3) -> None: ...

    @overload
    def add_vertex(self, vertex: Annotated[NDArray[numpy.float64], dict(order='C', device='cpu')]) -> None:
        """
        Add a vertex to the mesh.

        :param vertex: vertex coordinates
        """

    @overload
    def add_vertex(self, vertex: list) -> None:
        """
        Add a vertex to the mesh.

        :param vertex: vertex coordinates as a list
        """

    def add_vertices(self, vertices: Annotated[NDArray[numpy.float64], dict(order='C', device='cpu')]) -> None:
        """
        Add multiple vertices to the mesh.

        :param vertices: N x D tensor of vertex coordinates, where N is the number of vertices and D is the dimension
        """

    def add_triangle(self, v0: int, v1: int, v2: int) -> None:
        """
        Add a triangle to the mesh.

        :param v0: first vertex index
        :param v1: second vertex index
        :param v2: third vertex index

        :returns: facet index of the added triangle
        """

    def add_triangles(self, triangles: Annotated[NDArray[numpy.uint32], dict(order='C', device='cpu')]) -> None:
        """
        Add multiple triangles to the mesh.

        :param triangles: N x 3 tensor of vertex indices, where N is the number of triangles
        """

    def add_quad(self, v0: int, v1: int, v2: int, v3: int) -> None:
        """
        Add a quad to the mesh.

        :param v0: first vertex index
        :param v1: second vertex index
        :param v2: third vertex index
        :param v3: fourth vertex index

        :returns: facet index of the added quad
        """

    def add_quads(self, quads: Annotated[NDArray[numpy.uint32], dict(order='C', device='cpu')]) -> None:
        """
        Add multiple quads to the mesh.

        :param quads: N x 4 tensor of vertex indices, where N is the number of quads
        """

    def add_polygon(self, vertices: Annotated[NDArray[numpy.uint32], dict(order='C', device='cpu')]) -> None:
        """
        Add a polygon to the mesh.

        :param vertices: 1D tensor of vertex indices defining the polygon

        :returns: facet index of the added polygon
        """

    def add_polygons(self, polygons: Annotated[NDArray[numpy.uint32], dict(order='C', device='cpu')]) -> None:
        """
        Add multiple regular polygons to the mesh.

        :param polygons: N x K tensor of vertex indices, where N is the number of polygons and K is the number of vertices per polygon
        """

    def add_hybrid(self, sizes: Annotated[NDArray[numpy.uint32], dict(order='C', device='cpu')], indices: Annotated[NDArray[numpy.uint32], dict(order='C', device='cpu')]) -> None:
        """
        Add hybrid facets (polygons with varying number of vertices) to the mesh.

        :param sizes: 1D tensor specifying the number of vertices for each facet
        :param indices: 1D tensor of vertex indices for all facets concatenated together
        """

    @overload
    def remove_vertices(self, vertices: Annotated[NDArray[numpy.uint32], dict(order='C', device='cpu')]) -> None:
        """
        Remove selected vertices from the mesh.

        :param vertices: 1D tensor of vertex indices to remove
        """

    @overload
    def remove_vertices(self, vertices: list) -> None:
        """
        Remove selected vertices from the mesh.

        :param vertices: list of vertex indices to remove
        """

    @overload
    def remove_facets(self, facets: Annotated[NDArray[numpy.uint32], dict(order='C', device='cpu')]) -> None:
        """
        Remove selected facets from the mesh.

        :param facets: 1D tensor of facet indices to remove
        """

    @overload
    def remove_facets(self, facets: list) -> None:
        """
        Remove selected facets from the mesh.

        :param facets: list of facet indices to remove
        """

    def clear_vertices(self) -> None:
        """Remove all vertices from the mesh."""

    def clear_facets(self) -> None:
        """Remove all facets from the mesh."""

    def shrink_to_fit(self) -> None:
        """Shrink the internal storage to fit the current mesh size."""

    def compress_if_regular(self) -> None:
        """
        Compress the mesh representation if it is regular (all facets have the same number of vertices).

        :returns: True if the mesh was compressed, False otherwise
        """

    @property
    def is_triangle_mesh(self) -> bool: ...

    @property
    def is_quad_mesh(self) -> bool: ...

    @property
    def is_regular(self) -> bool: ...

    @property
    def is_hybrid(self) -> bool: ...

    @property
    def dimension(self) -> int: ...

    @property
    def vertex_per_facet(self) -> int: ...

    @property
    def num_vertices(self) -> int: ...

    @property
    def num_facets(self) -> int: ...

    @property
    def num_corners(self) -> int: ...

    @property
    def num_edges(self) -> int: ...

    def get_position(self, vertex_id: int) -> Annotated[NDArray[numpy.float64], dict(order='C', device='cpu')]:
        """
        Get the position of a vertex.

        :param vertex_id: vertex index

        :returns: position coordinates as a tensor
        """

    def ref_position(self, vertex_id: int) -> Annotated[NDArray[numpy.float64], dict(order='C', device='cpu')]:
        """
        Get a mutable reference to the position of a vertex.

        :param vertex_id: vertex index

        :returns: mutable position coordinates as a tensor
        """

    def get_facet_size(self, facet_id: int) -> int:
        """
        Get the number of vertices in a facet.

        :param facet_id: facet index

        :returns: number of vertices in the facet
        """

    def get_facet_vertex(self, facet_id: int, local_vertex_id: int) -> int:
        """
        Get a vertex index from a facet.

        :param facet_id: facet index
        :param local_vertex_id: local vertex index within the facet (0 to facet_size-1)

        :returns: global vertex index
        """

    def get_facet_corner_begin(self, facet_id: int) -> int:
        """
        Get the first corner index of a facet.

        :param facet_id: facet index

        :returns: first corner index of the facet
        """

    def get_facet_corner_end(self, facet_id: int) -> int:
        """
        Get the end corner index of a facet (one past the last corner).

        :param facet_id: facet index

        :returns: end corner index of the facet
        """

    def get_corner_vertex(self, corner_id: int) -> int:
        """
        Get the vertex index associated with a corner.

        :param corner_id: corner index

        :returns: vertex index
        """

    def get_corner_facet(self, corner_id: int) -> int:
        """
        Get the facet index associated with a corner.

        :param corner_id: corner index

        :returns: facet index
        """

    def get_facet_vertices(self, facet_id: int) -> Annotated[NDArray[numpy.uint32], dict(order='C', device='cpu')]:
        """
        Get all vertex indices of a facet.

        :param facet_id: facet index

        :returns: vertex indices as a tensor
        """

    def ref_facet_vertices(self, facet_id: int) -> Annotated[NDArray[numpy.uint32], dict(order='C', device='cpu')]:
        """
        Get a mutable reference to all vertex indices of a facet.

        :param facet_id: facet index

        :returns: mutable vertex indices as a tensor
        """

    def get_attribute_id(self, name: str) -> int:
        """
        Get the attribute ID by name.

        :param name: attribute name

        :returns: attribute ID
        """

    def get_attribute_name(self, id: int) -> str:
        """
        Get the attribute name by ID.

        :param id: attribute ID

        :returns: attribute name
        """

    def create_attribute(self, name: str, element: Union[AttributeElement, Literal['Vertex', 'Facet', 'Edge', 'Corner', 'Value', 'Indexed'], None] = None, usage: Union[AttributeUsage, Literal['Vector', 'Scalar', 'Position', 'Normal', 'Tangent', 'Bitangent', 'Color', 'UV', 'VertexIndex', 'FacetIndex', 'CornerIndex', 'EdgeIndex'], None] = None, initial_values: Union[numpy.typing.NDArray, List[float], None] = None, initial_indices: Union[numpy.typing.NDArray, List[int], None] = None, num_channels: Optional[int] = None, dtype: Optional[numpy.typing.DTypeLike] = None) -> int:
        """
        Create an attribute.

        :param name: Name of the attribute.
        :param element: Element type of the attribute. If None, derive from the shape of initial values.
        :param usage: Usage type of the attribute. If None, derive from the shape of initial values or the number of channels.
        :param initial_values: Initial values of the attribute.
        :param initial_indices: Initial indices of the attribute (Indexed attribute only).
        :param num_channels: Number of channels of the attribute.
        :param dtype: Data type of the attribute.

        :returns: The id of the created attribute.

        .. note::
           If `element` is None, it will be derived based on the cardinality of the mesh elements.
           If there is an ambiguity, an exception will be raised.
           In addition, explicit `element` specification is required for value attributes.

        .. note::
           If `usage` is None, it will be derived based on the shape of `initial_values` or `num_channels` if specified.
        """

    def create_attribute_from(self, name: str, source_mesh: SurfaceMesh, source_name: str = '') -> int:
        """
        Shallow copy an attribute from another mesh.

        :param name: Name of the attribute.
        :param source_mesh: Source mesh.
        :param source_name: Name of the attribute in the source mesh. If empty, use the same name as `name`.

        :returns: The id of the created attribute.
        """

    def wrap_as_attribute(self, name: str, element: AttributeElement, usage: AttributeUsage, values: Annotated[NDArray, dict(order='C', device='cpu')]) -> int:
        """
        Wrap an existing numpy array as an attribute.

        :param name: Name of the attribute.
        :param element: Element type of the attribute.
        :param usage: Usage type of the attribute.
        :param values: Values of the attribute.

        :returns: The id of the created attribute.
        """

    def wrap_as_indexed_attribute(self, name: str, usage: AttributeUsage, values: Annotated[NDArray, dict(order='C', device='cpu')], indices: Annotated[NDArray[numpy.uint32], dict(order='C', device='cpu')]) -> int:
        """
        Wrap an existing numpy array as an indexed attribute.

        :param name: Name of the attribute.
        :param usage: Usage type of the attribute.
        :param values: Values of the attribute.
        :param indices: Indices of the attribute.

        :returns: The id of the created attribute.
        """

    def duplicate_attribute(self, old_name: str, new_name: str) -> int:
        """
        Duplicate an attribute with a new name.

        :param old_name: name of the attribute to duplicate
        :param new_name: name for the new attribute

        :returns: attribute ID of the duplicated attribute
        """

    def rename_attribute(self, old_name: str, new_name: str) -> None:
        """
        Rename an attribute.

        :param old_name: current name of the attribute
        :param new_name: new name for the attribute
        """

    @overload
    def delete_attribute(self, name: str, policy: AttributeDeletePolicy) -> None: ...

    @overload
    def delete_attribute(self, name: str) -> None:
        """
        Delete an attribute by name.

        :param name: Name of the attribute.
        """

    @overload
    def delete_attribute(self, id: int) -> None:
        """
        Delete an attribute by id.

        :param id: Id of the attribute.
        """

    def has_attribute(self, name: str) -> bool:
        """
        Check if an attribute exists.

        :param name: attribute name

        :returns: True if the attribute exists, False otherwise
        """

    @overload
    def is_attribute_indexed(self, id: int) -> bool:
        """
        Check if an attribute is indexed.

        :param id: attribute ID

        :returns: True if the attribute is indexed, False otherwise
        """

    @overload
    def is_attribute_indexed(self, name: str) -> bool:
        """
        Check if an attribute is indexed.

        :param name: attribute name

        :returns: True if the attribute is indexed, False otherwise
        """

    @overload
    def attribute(self, id: int, sharing: bool = True) -> Attribute:
        """
        Get an attribute by id.

        :param id: Id of the attribute.
        :param sharing: Whether to allow sharing the attribute with other meshes.

        :returns: The attribute.
        """

    @overload
    def attribute(self, name: str, sharing: bool = True) -> Attribute:
        """
        Get an attribute by name.

        :param name: Name of the attribute.
        :param sharing: Whether to allow sharing the attribute with other meshes.

        :return: The attribute.
        """

    @overload
    def indexed_attribute(self, id: int, sharing: bool = True) -> IndexedAttribute:
        """
        Get an indexed attribute by id.

        :param id: Id of the attribute.
        :param sharing: Whether to allow sharing the attribute with other meshes.

        :returns: The indexed attribute.
        """

    @overload
    def indexed_attribute(self, name: str, sharing: bool = True) -> IndexedAttribute:
        """
        Get an indexed attribute by name.

        :param name: Name of the attribute.
        :param sharing: Whether to allow sharing the attribute with other meshes.

        :returns: The indexed attribute.
        """

    def __attribute_ref_count__(self, id: int) -> int:
        """
        Get the reference count of an attribute (for debugging purposes).

        :param id: attribute ID

        :returns: reference count of the attribute
        """

    @property
    def vertices(self) -> Annotated[NDArray[numpy.float64], dict(order='C', device='cpu')]:
        """Vertices of the mesh."""

    @vertices.setter
    def vertices(self, arg: Annotated[NDArray[numpy.float64], dict(order='C', device='cpu')], /) -> None: ...

    @property
    def facets(self) -> Annotated[NDArray[numpy.uint32], dict(order='C', device='cpu')]:
        """Facets of the mesh."""

    @facets.setter
    def facets(self, arg: Annotated[NDArray[numpy.uint32], dict(order='C', device='cpu')], /) -> None: ...

    @property
    def edges(self) -> Annotated[NDArray[numpy.uint32], dict(shape=(None, 2), order='C', device='cpu')]:
        """Edges of the mesh."""

    def wrap_as_vertices(self, tensor: Annotated[NDArray[numpy.float64], dict(order='C', device='cpu')], num_vertices: int) -> int:
        """
        Wrap a tensor as vertices.

        :param tensor: The tensor to wrap.
        :param num_vertices: Number of vertices.

        :return: The id of the wrapped vertices attribute.
        """

    @overload
    def wrap_as_facets(self, tensor: Annotated[NDArray[numpy.uint32], dict(order='C', device='cpu')], num_facets: int, vertex_per_facet: int) -> int:
        """
        Wrap a tensor as a list of regular facets.

        :param tensor: The tensor to wrap.
        :param num_facets: Number of facets.
        :param vertex_per_facet: Number of vertices per facet.

        :return: The id of the wrapped facet attribute.
        """

    @overload
    def wrap_as_facets(self, offsets: Annotated[NDArray[numpy.uint32], dict(order='C', device='cpu')], num_facets: int, facets: Annotated[NDArray[numpy.uint32], dict(order='C', device='cpu')], num_corners: int) -> int:
        """
        Wrap a tensor as a list of hybrid facets.

        :param offsets: The offset indices into the facets array.
        :param num_facets: Number of facets.
        :param facets: The indices of the vertices of the facets.
        :param num_corners: Number of corners.

        :return: The id of the wrapped facet attribute.
        """

    @staticmethod
    def attr_name_is_reserved(name: str) -> bool:
        """
        Check if an attribute name is reserved.

        :param name: attribute name to check

        :returns: True if the name is reserved, False otherwise
        """

    attr_name_vertex_to_position: str = ...
    """The name of the attribute that stores the vertex positions."""

    attr_name_corner_to_vertex: str = ...
    """The name of the attribute that stores the corner to vertex mapping."""

    attr_name_facet_to_first_corner: str = ...
    """
    The name of the attribute that stores the facet to first corner mapping.
    """

    attr_name_corner_to_facet: str = ...
    """The name of the attribute that stores the corner to facet mapping."""

    attr_name_corner_to_edge: str = ...
    """The name of the attribute that stores the corner to edge mapping."""

    attr_name_edge_to_first_corner: str = ...
    """
    The name of the attribute that stores the edge to first corner mapping.
    """

    attr_name_next_corner_around_edge: str = ...
    """
    The name of the attribute that stores the next corner around edge mapping.
    """

    attr_name_vertex_to_first_corner: str = ...
    """
    The name of the attribute that stores the vertex to first corner mapping.
    """

    attr_name_next_corner_around_vertex: str = ...
    """
    The name of the attribute that stores the next corner around vertex mapping.
    """

    @property
    def attr_id_vertex_to_position(self) -> int: ...

    @property
    def attr_id_corner_to_vertex(self) -> int: ...

    @property
    def attr_id_facet_to_first_corner(self) -> int: ...

    @property
    def attr_id_corner_to_facet(self) -> int: ...

    @property
    def attr_id_corner_to_edge(self) -> int: ...

    @property
    def attr_id_edge_to_first_corner(self) -> int: ...

    @property
    def attr_id_next_corner_around_edge(self) -> int: ...

    @property
    def attr_id_vertex_to_first_corner(self) -> int: ...

    @property
    def attr_id_next_corner_around_vertex(self) -> int: ...

    def initialize_edges(self, edges: Optional[Annotated[NDArray[numpy.uint32], dict(order='C', device='cpu')]] = None) -> None:
        """
        Initialize the edges.

        The `edges` tensor provides a predefined ordering of the edges.
        If not provided, the edges are initialized in an arbitrary order.

        :param edges: M x 2 tensor of predefined edge vertex indices, where M is the number of edges.
        """

    def clear_edges(self) -> None:
        """Clear all edge connectivity information."""

    @property
    def has_edges(self) -> bool: ...

    def get_edge(self, facet_id: int, lv: int) -> int:
        """
        Get the edge index associated with a local vertex of a facet.

        :param facet_id: facet index
        :param lv: local vertex index of the facet

        :returns: edge index
        """

    def get_corner_edge(self, corner_id: int) -> int:
        """
        Get the edge index associated with a corner.

        :param corner_id: corner index

        :returns: edge index
        """

    def get_edge_vertices(self, edge_id: int) -> list[int]:
        """
        Get the two vertex indices of an edge.

        :param edge_id: edge index

        :returns: tuple of (vertex1_id, vertex2_id)
        """

    def find_edge_from_vertices(self, vertex1_id: int, vertex2_id: int) -> int:
        """
        Find the edge connecting two vertices.

        :param vertex1_id: first vertex index
        :param vertex2_id: second vertex index

        :returns: edge index, or invalid_index if no such edge exists
        """

    def get_first_corner_around_edge(self, edge_id: int) -> int:
        """
        Get the first corner around an edge.

        :param edge_id: edge index

        :returns: first corner index around the edge
        """

    def get_next_corner_around_edge(self, corner_id: int) -> int:
        """
        Get the next corner around the same edge.

        :param corner_id: current corner index

        :returns: next corner index around the same edge
        """

    def get_first_corner_around_vertex(self, vertex_id: int) -> int:
        """
        Get the first corner around a vertex.

        :param vertex_id: vertex index

        :returns: first corner index around the vertex
        """

    def get_next_corner_around_vertex(self, corner_id: int) -> int:
        """
        Get the next corner around the same vertex.

        :param corner_id: current corner index

        :returns: next corner index around the same vertex
        """

    def count_num_corners_around_edge(self, edge_id: int) -> int:
        """
        Count the number of corners around an edge.

        :param edge_id: edge index

        :returns: number of corners around the edge
        """

    def count_num_corners_around_vertex(self, vertex_id: int) -> int:
        """
        Count the number of corners around a vertex.

        :param vertex_id: vertex index

        :returns: number of corners around the vertex
        """

    def get_counterclockwise_corner_around_vertex(self, corner: int) -> int:
        """
        Get the counterclockwise corner around the vertex associated with the input corner.

        .. note::
            If the vertex is a non-manifold vertex, only one "umbrella" (a set of connected
            corners based on edge-connectivity) will be visited.

            If the traversal reaches a boundary or a non-manifold edge, the next adjacent corner
            is not well defined. It will return `invalid_index` in this case.

        :param corner: The input corner index.

        :returns: The counterclockwise corner index or `invalid_index` if none exists.
        """

    def get_clockwise_corner_around_vertex(self, corner: int) -> int:
        """
        Get the clockwise corner around the vertex associated with the input corner.

        .. note::
            If the vertex is a non-manifold vertex, only one "umbrella" (a set of connected
            corners based on edge-connectivity) will be visited.

            If the traversal reaches a boundary or a non-manifold edge, the next adjacent corner
            is not well defined. It will return `invalid_index` in this case.

        :param corner: The input corner index.

        :returns: The clockwise corner index or `invalid_index` if none exists.
        """

    def get_one_facet_around_edge(self, edge_id: int) -> int:
        """
        Get one facet adjacent to an edge.

        :param edge_id: edge index

        :returns: facet index adjacent to the edge
        """

    def get_one_corner_around_edge(self, edge_id: int) -> int:
        """
        Get one corner around an edge.

        :param edge_id: edge index

        :returns: corner index around the edge
        """

    def get_one_corner_around_vertex(self, vertex_id: int) -> int:
        """
        Get one corner around a vertex.

        :param vertex_id: vertex index

        :returns: corner index around the vertex
        """

    def is_boundary_edge(self, edge_id: int) -> bool:
        """
        Check if an edge is on the boundary.

        :param edge_id: edge index

        :returns: True if the edge is on the boundary, False otherwise
        """

    @property
    def metadata(self) -> MetaData:
        """Metadata of the mesh."""

    def get_matching_attribute_ids(self, element: Optional[AttributeElement] = None, usage: Optional[AttributeUsage] = None, num_channels: int = 0) -> list[int]:
        """
        Get all matching attribute ids with the desired element type, usage and number of channels.

        :param element:       The target element type. None matches all element types.
        :param usage:         The target usage type.  None matches all usage types.
        :param num_channels:  The target number of channels. 0 matches arbitrary number of channels.

        :returns: A list of attribute ids matching the target element, usage and number of channels.
        """

    def get_matching_attribute_id(self, element: Optional[AttributeElement] = None, usage: Optional[AttributeUsage] = None, num_channels: int = 0) -> Optional[int]:
        """
        Get one matching attribute id with the desired element type, usage and number of channels.

        :param element:       The target element type. None matches all element types.
        :param usage:         The target usage type.  None matches all usage types.
        :param num_channels:  The target number of channels. 0 matches arbitrary number of channels.

        :returns: An attribute id matching the target element, usage and number of channels, if found. None otherwise.
        """

    def __copy__(self) -> SurfaceMesh:
        """Create a shallow copy of this mesh."""

    def __deepcopy__(self, memo: Optional[dict] = None) -> SurfaceMesh:
        """Create a deep copy of this mesh."""

    def clone(self, strip: bool = False) -> SurfaceMesh:
        """
        Create a deep copy of this mesh.

        :param strip: If True, strip the mesh of all attributes except for the reserved attributes.
        """

class MetaData:
    """Metadata `dict` of the mesh"""

    def __len__(self) -> int: ...

    def __getitem__(self, arg: str, /) -> str: ...

    def __setitem__(self, arg0: str, arg1: str, /) -> None: ...

    def __delitem__(self, arg: str, /) -> None: ...

    def __repr__(self) -> str: ...

class Attribute:
    """
    Attribute data associated with mesh elements (vertices, facets, corners, edges).
    """

    @property
    def element_type(self) -> AttributeElement:
        """Element type (Vertex, Facet, Corner, Edge, Value)."""

    @property
    def usage(self) -> AttributeUsage:
        """Usage type (Position, Normal, UV, Color, etc.)."""

    @property
    def num_channels(self) -> int:
        """Number of channels per element."""

    @property
    def default_value(self) -> object:
        """Default value for new elements."""

    @default_value.setter
    def default_value(self, arg: float, /) -> None: ...

    @property
    def growth_policy(self) -> AttributeGrowthPolicy:
        """Policy for growing the attribute when elements are added."""

    @growth_policy.setter
    def growth_policy(self, arg: AttributeGrowthPolicy, /) -> None: ...

    @property
    def shrink_policy(self) -> AttributeShrinkPolicy:
        """Policy for shrinking the attribute when elements are removed."""

    @shrink_policy.setter
    def shrink_policy(self, arg: AttributeShrinkPolicy, /) -> None: ...

    @property
    def write_policy(self) -> AttributeWritePolicy:
        """Policy for write operations on the attribute."""

    @write_policy.setter
    def write_policy(self, arg: AttributeWritePolicy, /) -> None: ...

    @property
    def copy_policy(self) -> AttributeCopyPolicy:
        """Policy for copying the attribute."""

    @copy_policy.setter
    def copy_policy(self, arg: AttributeCopyPolicy, /) -> None: ...

    @property
    def cast_policy(self) -> AttributeCastPolicy:
        """Policy for casting the attribute to different types."""

    @cast_policy.setter
    def cast_policy(self, arg: AttributeCastPolicy, /) -> None: ...

    def create_internal_copy(self) -> None:
        """Create an internal copy if the attribute wraps external data."""

    def clear(self) -> None:
        """Remove all elements from the attribute."""

    def reserve_entries(self, num_entries: int) -> None:
        """
        Reserve enough memory for `num_entries` entries.

        :param num_entries: Number of entries to reserve. It does not need to be a multiple of `num_channels`.
        """

    @overload
    def insert_elements(self, num_elements: int) -> None:
        """
        Insert new elements with default value to the attribute.

        :param num_elements: Number of elements to insert.
        """

    @overload
    def insert_elements(self, tensor: object) -> None:
        """
        Insert new elements to the attribute.

        :param tensor: A tensor with shape (num_elements, num_channels) or (num_elements,).
        """

    def empty(self) -> bool:
        """Check if the attribute has no elements."""

    @property
    def num_elements(self) -> int:
        """Number of elements in the attribute."""

    @property
    def external(self) -> bool:
        """Check if the attribute wraps external data."""

    @property
    def readonly(self) -> bool:
        """Check if the attribute is read-only."""

    @property
    def data(self, /) -> numpy.typing.NDArray:
        """Raw data as a numpy array."""

    @data.setter
    def data(self, arg: object, /) -> None: ...

    @property
    def dtype(self) -> Optional[type]:
        """NumPy dtype of the attribute values."""

class IndexedAttribute:
    """
    Indexed attribute data structure.

    An indexed attribute stores values and indices separately, allowing for efficient
    storage when multiple elements share the same values. This is commonly used for
    UV coordinates, normals, or colors where the same value may be referenced by
    multiple vertices, corners, or facets.
    """

    @property
    def element_type(self) -> AttributeElement:
        """Element type (i.e. Indexed)."""

    @property
    def usage(self) -> AttributeUsage:
        """Usage type (Position, Normal, UV, Color, etc.)."""

    @property
    def num_channels(self) -> int:
        """Number of channels per element."""

    @property
    def values(self) -> Attribute:
        """
        The values array of the indexed attribute.

        :returns: Attribute containing the unique values referenced by the indices
        """

    @property
    def indices(self) -> Attribute:
        """
        The indices array of the indexed attribute.

        :returns: Attribute containing the indices that reference into the values array
        """

class NormalWeightingType(enum.Enum):
    """Normal weighting type."""

    Uniform = 0
    """Uniform weighting"""

    CornerTriangleArea = 1
    """Weight by corner triangle area"""

    Angle = 2
    """Weight by corner angle"""

class VertexNormalOptions:
    """Options for computing vertex normals"""

    def __init__(self) -> None: ...

    @property
    def output_attribute_name(self) -> str:
        """Output attribute name. Default is `@vertex_normal`."""

    @output_attribute_name.setter
    def output_attribute_name(self, arg: str, /) -> None: ...

    @property
    def weight_type(self) -> NormalWeightingType:
        """Weighting type for normal computation. Default is Angle."""

    @weight_type.setter
    def weight_type(self, arg: NormalWeightingType, /) -> None: ...

    @property
    def weighted_corner_normal_attribute_name(self) -> str:
        """
        Precomputed weighted corner normals attribute name (default: @weighted_corner_normal).

        If attribute exists, the precomputed weighted corner normal will be used.
        """

    @weighted_corner_normal_attribute_name.setter
    def weighted_corner_normal_attribute_name(self, arg: str, /) -> None: ...

    @property
    def recompute_weighted_corner_normals(self) -> bool:
        """Whether to recompute weighted corner normals (default: false)."""

    @recompute_weighted_corner_normals.setter
    def recompute_weighted_corner_normals(self, arg: bool, /) -> None: ...

    @property
    def keep_weighted_corner_normals(self) -> bool:
        """Whether to keep the weighted corner normal attribute (default: false)."""

    @keep_weighted_corner_normals.setter
    def keep_weighted_corner_normals(self, arg: bool, /) -> None: ...

    @property
    def distance_tolerance(self) -> float:
        """Distance tolerance for degenerate edge check in polygon facets."""

    @distance_tolerance.setter
    def distance_tolerance(self, arg: float, /) -> None: ...

@overload
def compute_vertex_normal(mesh: SurfaceMesh, options: VertexNormalOptions = ...) -> int:
    """
    Compute vertex normal.

    :param mesh: Input mesh.
    :param options: Options for computing vertex normals.

    :returns: Vertex normal attribute id.
    """

@overload
def compute_vertex_normal(mesh: SurfaceMesh, output_attribute_name: Optional[str] = None, weight_type: Optional[NormalWeightingType] = None, weighted_corner_normal_attribute_name: Optional[str] = None, recompute_weighted_corner_normals: Optional[bool] = None, keep_weighted_corner_normals: Optional[bool] = None, distance_tolerance: Optional[float] = None) -> int:
    """
    Compute vertex normal (Pythonic API).

    :param mesh: Input mesh.
    :param output_attribute_name: Output attribute name.
    :param weight_type: Weighting type for normal computation.
    :param weighted_corner_normal_attribute_name: Precomputed weighted corner normals attribute name.
    :param recompute_weighted_corner_normals: Whether to recompute weighted corner normals.
    :param keep_weighted_corner_normals: Whether to keep the weighted corner normal attribute.
    :param distance_tolerance: Distance tolerance for degenerate edge check.
                               (Only used to bypass degenerate edge in polygon facets.)

    :returns: Vertex normal attribute id.
    """

class FacetNormalOptions:
    """Facet normal computation options."""

    def __init__(self) -> None: ...

    @property
    def output_attribute_name(self) -> str:
        """Output attribute name. Default: `@facet_normal`"""

    @output_attribute_name.setter
    def output_attribute_name(self, arg: str, /) -> None: ...

@overload
def compute_facet_normal(mesh: SurfaceMesh, options: FacetNormalOptions = ...) -> int:
    """
    Compute facet normal.

    :param mesh: Input mesh.
    :param options: Options for computing facet normals.

    :returns: Facet normal attribute id.
    """

@overload
def compute_facet_normal(mesh: SurfaceMesh, output_attribute_name: Optional[str] = None) -> int:
    """
    Compute facet normal (Pythonic API).

    :param mesh: Input mesh.
    :param output_attribute_name: Output attribute name.

    :returns: Facet normal attribute id.
    """

class NormalOptions:
    """Normal computation options."""

    def __init__(self) -> None: ...

    @property
    def output_attribute_name(self) -> str:
        """Output attribute name. Default: `@normal`"""

    @output_attribute_name.setter
    def output_attribute_name(self, arg: str, /) -> None: ...

    @property
    def weight_type(self) -> NormalWeightingType:
        """Weighting type for normal computation. Default is Angle."""

    @weight_type.setter
    def weight_type(self, arg: NormalWeightingType, /) -> None: ...

    @property
    def facet_normal_attribute_name(self) -> str:
        """Facet normal attribute name to use. Default is `@facet_normal`."""

    @facet_normal_attribute_name.setter
    def facet_normal_attribute_name(self, arg: str, /) -> None: ...

    @property
    def recompute_facet_normals(self) -> bool:
        """Whether to recompute facet normals. Default is false."""

    @recompute_facet_normals.setter
    def recompute_facet_normals(self, arg: bool, /) -> None: ...

    @property
    def keep_facet_normals(self) -> bool:
        """Whether to keep the computed facet normal attribute. Default is false."""

    @keep_facet_normals.setter
    def keep_facet_normals(self, arg: bool, /) -> None: ...

    @property
    def distance_tolerance(self) -> float:
        """
        Distance tolerance for degenerate edge check. (Only used to bypass degenerate edge in polygon facets.)
        """

    @distance_tolerance.setter
    def distance_tolerance(self, arg: float, /) -> None: ...

@overload
def compute_normal(mesh: SurfaceMesh, feature_angle_threshold: float = 0.7853981633974483, cone_vertices: Optional[object] = None, options: Optional[NormalOptions] = None) -> int:
    """
    Compute indexed normal attribute.

    Edge with dihedral angles larger than `feature_angle_threshold` are considered as sharp edges.
    Vertices listed in `cone_vertices` are considered as cone vertices, which is always sharp.

    :param mesh: input mesh
    :param feature_angle_threshold: feature angle threshold
    :param cone_vertices: cone vertices
    :param options: normal options

    :returns: the id of the indexed normal attribute.
    """

@overload
def compute_normal(mesh: SurfaceMesh, feature_angle_threshold: float = 0.7853981633974483, cone_vertices: Optional[object] = None, output_attribute_name: Optional[str] = None, weight_type: Optional[NormalWeightingType] = None, facet_normal_attribute_name: Optional[str] = None, recompute_facet_normals: Optional[bool] = None, keep_facet_normals: Optional[bool] = None, distance_tolerance: Optional[float] = None) -> int:
    """
    Compute indexed normal attribute (Pythonic API).

    :param mesh: input mesh
    :param feature_angle_threshold: feature angle threshold
    :param cone_vertices: cone vertices
    :param output_attribute_name: output normal attribute name
    :param weight_type: normal weighting type
    :param facet_normal_attribute_name: facet normal attribute name
    :param recompute_facet_normals: whether to recompute facet normals
    :param keep_facet_normals: whether to keep the computed facet normal attribute
    :param distance_tolerance: distance tolerance for degenerate edge check
                               (only used to bypass degenerate edges in polygon facets)

    :returns: the id of the indexed normal attribute.
    """

def compute_pointcloud_pca(points: Annotated[NDArray[numpy.float64], dict(shape=(None, 3), order='C', device='cpu', writable=False)], shift_centroid: bool = False, normalize: bool = False) -> tuple[list[float], list[list[float]], list[float]]:
    """
    Compute principal components of a point cloud.

    :param points: Input points.
    :param shift_centroid: When true: covariance = (P-centroid)^T (P-centroid), when false: covariance = (P)^T (P).
    :param normalize: Should we divide the result by number of points?

    :returns: tuple of (center, eigenvectors, eigenvalues).
    """

def compute_greedy_coloring(mesh: SurfaceMesh, element_type: AttributeElement = AttributeElement.Facet, num_color_used: int = 8, output_attribute_name: Optional[str] = None) -> int:
    """
    Compute greedy coloring of mesh elements.

    :param mesh: Input mesh.
    :param element_type: Element type to be colored. Can be either Vertex or Facet.
    :param num_color_used: Minimum number of colors to use. The algorithm will cycle through them but may use more.
    :param output_attribute_name: Output attribute name.

    :returns: Color attribute id.
    """

def normalize_mesh_with_transform(mesh: SurfaceMesh, normalize_normals: bool = True, normalize_tangents_bitangents: bool = True) -> Annotated[NDArray[numpy.float64], dict(shape=(4, 4), order='F')]:
    """
    Normalize a mesh to fit into a unit box centered at the origin.

    :param mesh: Input mesh.
    :param normalize_normals:             Whether to normalize normals.
    :param normalize_tangents_bitangents: Whether to normalize tangents and bitangents.

    :return Inverse transform, can be used to undo the normalization process.
    """

def normalize_mesh_with_transform_2d(mesh: SurfaceMesh, normalize_normals: bool = True, normalize_tangents_bitangents: bool = True) -> Annotated[NDArray[numpy.float64], dict(shape=(3, 3), order='F')]:
    """
    Normalize a mesh to fit into a unit box centered at the origin.

    :param mesh: Input mesh.
    :param normalize_normals:             Whether to normalize normals.
    :param normalize_tangents_bitangents: Whether to normalize tangents and bitangents.

    :return Inverse transform, can be used to undo the normalization process.
    """

def normalize_mesh(mesh: SurfaceMesh, normalize_normals: bool = True, normalize_tangents_bitangents: bool = True) -> None:
    """
    Normalize a mesh to fit into a unit box centered at the origin.

    :param mesh: Input mesh.
    :param normalize_normals:             Whether to normalize normals.
    :param normalize_tangents_bitangents: Whether to normalize tangents and bitangents.
    """

def normalize_meshes_with_transform(meshes: Sequence[SurfaceMesh], normalize_normals: bool = True, normalize_tangents_bitangents: bool = True) -> Annotated[NDArray[numpy.float64], dict(shape=(4, 4), order='F')]:
    """
    Normalize a mesh to fit into a unit box centered at the origin.

    :param meshes: Input meshes.
    :param normalize_normals:             Whether to normalize normals.
    :param normalize_tangents_bitangents: Whether to normalize tangents and bitangents.

    :return Inverse transform, can be used to undo the normalization process.
    """

def normalize_meshes_with_transform_2d(meshes: Sequence[SurfaceMesh], normalize_normals: bool = True, normalize_tangents_bitangents: bool = True) -> Annotated[NDArray[numpy.float64], dict(shape=(3, 3), order='F')]:
    """
    Normalize a mesh to fit into a unit box centered at the origin.

    :param meshes: Input meshes.
    :param normalize_normals:             Whether to normalize normals.
    :param normalize_tangents_bitangents: Whether to normalize tangents and bitangents.

    :return Inverse transform, can be used to undo the normalization process.
    """

def normalize_meshes(meshes: Sequence[SurfaceMesh], normalize_normals: bool = True, normalize_tangents_bitangents: bool = True) -> None:
    """
    Normalize a list of meshes to fit into a unit box centered at the origin.

    :param meshes: Input meshes.
    :param normalize_normals:             Whether to normalize normals.
    :param normalize_tangents_bitangents: Whether to normalize tangents and bitangents.
    """

def combine_meshes(meshes: Sequence[SurfaceMesh], preserve_attributes: bool = True) -> SurfaceMesh:
    """
    Combine a list of meshes into a single mesh.

    :param meshes: Input meshes.
    :param preserve_attributes: Whether to preserve attributes.

    :returns: The combined mesh.
    """

def compute_seam_edges(mesh: SurfaceMesh, indexed_attribute_id: int, output_attribute_name: Optional[str] = None) -> int:
    """
    Compute seam edges for a given indexed attribute.

    :param mesh: Input mesh.
    :param indexed_attribute_id: Input indexed attribute id.
    :param output_attribute_name: Output attribute name.

    :returns: Attribute id for the output per-edge seam attribute (1 is a seam, 0 is not).
    """

def orient_outward(mesh: SurfaceMesh, positive: bool = True) -> None:
    """
    Orient mesh facets to ensure positive or negative signed volume.

    :param mesh: Input mesh.
    :param positive: Whether to orient volumes positively or negatively.
    """

@overload
def unify_index_buffer(mesh: SurfaceMesh) -> SurfaceMesh:
    """
    Unify the index buffer for all indexed attributes.

    :param mesh: Input mesh.

    :returns: Unified mesh.
    """

@overload
def unify_index_buffer(mesh: SurfaceMesh, attribute_ids: Sequence[int]) -> SurfaceMesh:
    """
    Unify the index buffer for selected attributes.

    :param mesh: Input mesh.
    :param attribute_ids: Attribute IDs to unify.

    :returns: Unified mesh.
    """

@overload
def unify_index_buffer(mesh: SurfaceMesh, attribute_names: Sequence[str]) -> SurfaceMesh:
    """
    Unify the index buffer for selected attributes.

    :param mesh: Input mesh.
    :param attribute_names: Attribute names to unify.

    :returns: Unified mesh.
    """

def triangulate_polygonal_facets(mesh: SurfaceMesh, scheme: str = 'earcut') -> None:
    """
    Triangulate polygonal facets of the mesh.

    :param mesh: The input mesh to be triangulated in place.
    :param scheme: The triangulation scheme (options are 'earcut' and 'centroid_fan')
    """

class ConnectivityType(enum.Enum):
    """Mesh connectivity type"""

    Vertex = 0
    """Two facets are connected if they share a vertex"""

    Edge = 1
    """Two facets are connected if they share an edge"""

def compute_components(mesh: SurfaceMesh, output_attribute_name: Optional[str] = None, connectivity_type: Optional[ConnectivityType] = None, blocker_elements: Optional[list] = None) -> int:
    """
    Compute connected components.

    This method will create a per-facet component id attribute named by the `output_attribute_name`
    argument. Each component id is in [0, num_components-1] range.

    :param mesh: The input mesh.
    :param output_attribute_name: The name of the output attribute.
    :param connectivity_type: The connectivity type.  Either "Vertex" or "Edge".
    :param blocker_elements: The list of blocker element indices. If `connectivity_type` is `Edge`, facets adjacent to a blocker edge are not considered as connected through this edge. If `connectivity_type` is `Vertex`, facets sharing a blocker vertex are not considered as connected through this vertex.

    :returns: The total number of components.
    """

class VertexValenceOptions:
    """Vertex valence options"""

    def __init__(self) -> None: ...

    @property
    def output_attribute_name(self) -> str:
        """The name of the output attribute"""

    @output_attribute_name.setter
    def output_attribute_name(self, arg: str, /) -> None: ...

    @property
    def induced_by_attribute(self) -> str:
        """
        Optional per-edge attribute used as indicator function to restrict the graph used for vertex valence computation
        """

    @induced_by_attribute.setter
    def induced_by_attribute(self, arg: str, /) -> None: ...

@overload
def compute_vertex_valence(mesh: SurfaceMesh, options: VertexValenceOptions = ...) -> int:
    """
    Compute vertex valence

    :param mesh: The input mesh.
    :param options: The vertex valence options.

    :returns: The vertex valence attribute id.
    """

@overload
def compute_vertex_valence(mesh: SurfaceMesh, output_attribute_name: Optional[str] = None, induced_by_attribute: Optional[str] = None) -> int:
    """
    Compute vertex valence);

    :param mesh: The input mesh.
    :param output_attribute_name: The name of the output attribute.
    :param induced_by_attribute: Optional per-edge attribute used as indicator function to restrict the graph used for vertex valence computation.

    :returns: The vertex valence attribute id
    """

class TangentBitangentOptions:
    """Tangent bitangent options"""

    def __init__(self) -> None: ...

    @property
    def tangent_attribute_name(self) -> str:
        """The name of the output tangent attribute, default is `@tangent`"""

    @tangent_attribute_name.setter
    def tangent_attribute_name(self, arg: str, /) -> None: ...

    @property
    def bitangent_attribute_name(self) -> str:
        """The name of the output bitangent attribute, default is `@bitangent`"""

    @bitangent_attribute_name.setter
    def bitangent_attribute_name(self, arg: str, /) -> None: ...

    @property
    def uv_attribute_name(self) -> str:
        """The name of the uv attribute"""

    @uv_attribute_name.setter
    def uv_attribute_name(self, arg: str, /) -> None: ...

    @property
    def normal_attribute_name(self) -> str:
        """The name of the normal attribute"""

    @normal_attribute_name.setter
    def normal_attribute_name(self, arg: str, /) -> None: ...

    @property
    def output_element_type(self) -> AttributeElement:
        """The output element type"""

    @output_element_type.setter
    def output_element_type(self, arg: AttributeElement, /) -> None: ...

    @property
    def pad_with_sign(self) -> bool:
        """Whether to pad the output tangent/bitangent with sign"""

    @pad_with_sign.setter
    def pad_with_sign(self, arg: bool, /) -> None: ...

    @property
    def orthogonalize_bitangent(self) -> bool:
        """
        Whether to compute the bitangent as cross(normal, tangent). If false, the bitangent is computed as the derivative of v-coordinate
        """

    @orthogonalize_bitangent.setter
    def orthogonalize_bitangent(self, arg: bool, /) -> None: ...

    @property
    def keep_existing_tangent(self) -> bool:
        """
        Whether to recompute tangent if the tangent attribute (specified by tangent_attribute_name) already exists. If true, bitangent is computed by normalizing cross(normal, tangent) and param orthogonalize_bitangent must be true.
        """

    @keep_existing_tangent.setter
    def keep_existing_tangent(self, arg: bool, /) -> None: ...

class TangentBitangentResult:
    """Tangent bitangent result"""

    def __init__(self) -> None: ...

    @property
    def tangent_id(self) -> int:
        """The output tangent attribute id"""

    @tangent_id.setter
    def tangent_id(self, arg: int, /) -> None: ...

    @property
    def bitangent_id(self) -> int:
        """The output bitangent attribute id"""

    @bitangent_id.setter
    def bitangent_id(self, arg: int, /) -> None: ...

@overload
def compute_tangent_bitangent(mesh: SurfaceMesh, options: TangentBitangentOptions = ...) -> TangentBitangentResult:
    """
    Compute tangent and bitangent vector attributes.

    :param mesh: The input mesh.
    :param options: The tangent bitangent options.

    :returns: The tangent and bitangent attribute ids
    """

@overload
def compute_tangent_bitangent(mesh: SurfaceMesh, tangent_attribute_name: Optional[str] = None, bitangent_attribute_name: Optional[str] = None, uv_attribute_name: Optional[str] = None, normal_attribute_name: Optional[str] = None, output_attribute_type: Optional[AttributeElement] = None, pad_with_sign: Optional[bool] = None, orthogonalize_bitangent: Optional[bool] = None, keep_existing_tangent: Optional[bool] = None) -> tuple[int, int]:
    """
    Compute tangent and bitangent vector attributes (Pythonic API).

    :param mesh: The input mesh.
    :param tangent_attribute_name: The name of the output tangent attribute.
    :param bitangent_attribute_name: The name of the output bitangent attribute.
    :param uv_attribute_name: The name of the uv attribute.
    :param normal_attribute_name: The name of the normal attribute.
    :param output_attribute_type: The output element type.
    :param pad_with_sign: Whether to pad the output tangent/bitangent with sign.
    :param orthogonalize_bitangent: Whether to compute the bitangent as sign * cross(normal, tangent).
    :param keep_existing_tangent: Whether to recompute tangent if the tangent attribute (specified by tangent_attribute_name) already exists. If true, bitangent is computed by normalizing cross(normal, tangent) and param orthogonalize_bitangent must be true.

    :returns: The tangent and bitangent attribute ids
    """

@overload
def map_attribute(mesh: SurfaceMesh, old_attribute_id: int, new_attribute_name: str, new_element: AttributeElement) -> int:
    """
    Map an attribute to a new element type.

    :param mesh: The input mesh.
    :param old_attribute_id: The id of the input attribute.
    :param new_attribute_name: The name of the new attribute.
    :param new_element: The new element type.

    :returns: The id of the new attribute.
    """

@overload
def map_attribute(mesh: SurfaceMesh, old_attribute_name: str, new_attribute_name: str, new_element: AttributeElement) -> int:
    """
    Map an attribute to a new element type.

    :param mesh: The input mesh.
    :param old_attribute_name: The name of the input attribute.
    :param new_attribute_name: The name of the new attribute.
    :param new_element: The new element type.

    :returns: The id of the new attribute.
    """

@overload
def map_attribute_in_place(mesh: SurfaceMesh, id: int, new_element: AttributeElement) -> int:
    """
    Map an attribute to a new element type in place.

    :param mesh: The input mesh.
    :param id: The id of the input attribute.
    :param new_element: The new element type.

    :returns: The id of the new attribute.
    """

@overload
def map_attribute_in_place(mesh: SurfaceMesh, name: str, new_element: AttributeElement) -> int:
    """
    Map an attribute to a new element type in place.

    :param mesh: The input mesh.
    :param name: The name of the input attribute.
    :param new_element: The new element type.

    :returns: The id of the new attribute.
    """

class FacetAreaOptions:
    """Options for computing facet area."""

    def __init__(self) -> None: ...

    @property
    def output_attribute_name(self) -> str:
        """The name of the output attribute."""

    @output_attribute_name.setter
    def output_attribute_name(self, arg: str, /) -> None: ...

@overload
def compute_facet_area(mesh: SurfaceMesh, options: FacetAreaOptions = ...) -> int:
    """
    Compute facet area.

    :param mesh: The input mesh.
    :param options: The options for computing facet area.

    :returns: The id of the new attribute.
    """

@overload
def compute_facet_area(mesh: SurfaceMesh, output_attribute_name: Optional[str] = None) -> int:
    """
    Compute facet area (Pythonic API).

    :param mesh: The input mesh.
    :param output_attribute_name: The name of the output attribute.

    :returns: The id of the new attribute.
    """

def compute_facet_vector_area(mesh: SurfaceMesh, output_attribute_name: Optional[str] = None) -> int:
    """
    Compute facet vector area (Pythonic API).

    Vector area is defined as the area multiplied by the facet normal.
    For triangular facets, it is equivalent to half of the cross product of two edges.
    For non-planar polygonal facets, the vector area offers a robust way to compute the area and normal.
    The magnitude of the vector area is the largest area of any orthogonal projection of the facet.
    The direction of the vector area is the normal direction that maximizes the projected area [1, 2].

    [1] Sullivan, John M. "Curvatures of smooth and discrete surfaces." Discrete differential geometry.
    Basel: Birkhäuser Basel, 2008. 175-188.

    [2] Alexa, Marc, and Max Wardetzky. "Discrete Laplacians on general polygonal meshes." ACM SIGGRAPH
    2011 papers. 2011. 1-10.

    :param mesh: The input mesh.
    :param output_attribute_name: The name of the output attribute.

    :returns: The id of the new attribute.
    """

class MeshAreaOptions:
    """Options for computing mesh area."""

    def __init__(self) -> None: ...

    @property
    def input_attribute_name(self) -> str:
        """
        The name of the pre-computed facet area attribute, default is `@facet_area`.
        """

    @input_attribute_name.setter
    def input_attribute_name(self, arg: str, /) -> None: ...

    @property
    def use_signed_area(self) -> bool:
        """Whether to use signed area."""

    @use_signed_area.setter
    def use_signed_area(self, arg: bool, /) -> None: ...

@overload
def compute_mesh_area(mesh: SurfaceMesh, options: MeshAreaOptions = ...) -> float:
    """
    Compute mesh area.

    :param mesh: The input mesh.
    :param options: The options for computing mesh area.

    :returns: The mesh area.
    """

@overload
def compute_mesh_area(mesh: SurfaceMesh, input_attribute_name: Optional[str] = None, use_signed_area: Optional[bool] = None) -> float:
    """
    Compute mesh area (Pythonic API).

    :param mesh: The input mesh.
    :param input_attribute_name: The name of the pre-computed facet area attribute.
    :param use_signed_area: Whether to use signed area.

    :returns: The mesh area.
    """

class FacetCentroidOptions:
    """Facet centroid options."""

    def __init__(self) -> None: ...

    @property
    def output_attribute_name(self) -> str:
        """The name of the output attribute."""

    @output_attribute_name.setter
    def output_attribute_name(self, arg: str, /) -> None: ...

@overload
def compute_facet_centroid(mesh: SurfaceMesh, options: FacetCentroidOptions = ...) -> int:
    """
    Compute facet centroid.

    :param mesh: The input mesh.
    :param options: The options for computing facet centroid.

    :returns: The id of the new attribute.
    """

@overload
def compute_facet_centroid(mesh: SurfaceMesh, output_attribute_name: Optional[str] = None) -> int:
    """
    Compute facet centroid (Pythonic API).

    :param mesh: Input mesh.
    :param output_attribute_name: Output attribute name.

    :returns: Attribute ID.
    """

def compute_facet_circumcenter(mesh: SurfaceMesh, output_attribute_name: Optional[str] = None) -> int:
    """
    Compute facet circumcenter (Pythonic API).

    :param mesh: The input mesh.
    :param output_attribute_name: The name of the output attribute.

    :returns: The id of the new attribute.
    """

class CentroidWeightingType(enum.Enum):
    """Centroid weighting type."""

    Uniform = 0
    """Uniform weighting."""

    Area = 1
    """Area weighting."""

class MeshCentroidOptions:
    """Mesh centroid options."""

    def __init__(self) -> None: ...

    @property
    def weighting_type(self) -> CentroidWeightingType:
        """The weighting type."""

    @weighting_type.setter
    def weighting_type(self, arg: CentroidWeightingType, /) -> None: ...

    @property
    def facet_centroid_attribute_name(self) -> str:
        """The name of the pre-computed facet centroid attribute if available."""

    @facet_centroid_attribute_name.setter
    def facet_centroid_attribute_name(self, arg: str, /) -> None: ...

    @property
    def facet_area_attribute_name(self) -> str:
        """The name of the pre-computed facet area attribute if available."""

    @facet_area_attribute_name.setter
    def facet_area_attribute_name(self, arg: str, /) -> None: ...

@overload
def compute_mesh_centroid(mesh: SurfaceMesh, options: MeshCentroidOptions = ...) -> list[float]:
    """
    Compute mesh centroid.

    :param mesh: Input mesh.
    :param options: Centroid computation options.

    :returns: Mesh centroid coordinates.
    """

@overload
def compute_mesh_centroid(mesh: SurfaceMesh, weighting_type: Optional[CentroidWeightingType] = None, facet_centroid_attribute_name: Optional[str] = None, facet_area_attribute_name: Optional[str] = None) -> list[float]:
    """
    Compute mesh centroid (Pythonic API).

    :param mesh: Input mesh.
    :param weighting_type: Weighting type (default: Area).
    :param facet_centroid_attribute_name: Pre-computed facet centroid attribute name.
    :param facet_area_attribute_name: Pre-computed facet area attribute name.

    :returns: Mesh centroid coordinates.
    """

def permute_vertices(mesh: SurfaceMesh, new_to_old: Annotated[NDArray[numpy.uint32], dict(order='C', device='cpu')]) -> None:
    """
    Reorder vertices of a mesh in place based on a permutation.

    :param mesh: input mesh
    :param new_to_old: permutation vector for vertices
    """

def permute_facets(mesh: SurfaceMesh, new_to_old: Annotated[NDArray[numpy.uint32], dict(order='C', device='cpu')]) -> None:
    """
    Reorder facets of a mesh in place based on a permutation.

    :param mesh: input mesh
    :param new_to_old: permutation vector for facets
    """

class MappingPolicy(enum.Enum):
    """Mapping policy for handling collisions."""

    Average = 0
    """Compute the average of the collided values."""

    KeepFirst = 1
    """Keep the first collided value."""

    Error = 2
    """Throw an error when collision happens."""

class RemapVerticesOptions:
    """Options for remapping vertices."""

    def __init__(self) -> None: ...

    @property
    def collision_policy_float(self) -> MappingPolicy:
        """The collision policy for float attributes."""

    @collision_policy_float.setter
    def collision_policy_float(self, arg: MappingPolicy, /) -> None: ...

    @property
    def collision_policy_integral(self) -> MappingPolicy:
        """The collision policy for integral attributes."""

    @collision_policy_integral.setter
    def collision_policy_integral(self, arg: MappingPolicy, /) -> None: ...

@overload
def remap_vertices(mesh: SurfaceMesh, old_to_new: Annotated[NDArray[numpy.uint32], dict(order='C', device='cpu')], options: RemapVerticesOptions = ...) -> None:
    """
    Remap vertices of a mesh in place based on a permutation.

    :param mesh: input mesh
    :param old_to_new: permutation vector for vertices
    :param options: options for remapping vertices
    """

@overload
def remap_vertices(mesh: SurfaceMesh, old_to_new: Annotated[NDArray[numpy.uint32], dict(order='C', device='cpu')], collision_policy_float: Optional[MappingPolicy] = None, collision_policy_integral: Optional[MappingPolicy] = None) -> None:
    """
    Remap vertices of a mesh in place based on a permutation (Pythonic API).

    :param mesh: input mesh
    :param old_to_new: permutation vector for vertices
    :param collision_policy_float: The collision policy for float attributes.
    :param collision_policy_integral: The collision policy for integral attributes.
    """

def reorder_mesh(mesh: SurfaceMesh, method: Literal['Lexicographic', 'Morton', 'Hilbert', 'None']) -> None:
    """
    Reorder a mesh in place.

    :param mesh: input mesh
    :param method: reordering method, options are 'Lexicographic', 'Morton', 'Hilbert', 'None' (default is 'Morton').
    """

def separate_by_facet_groups(mesh: SurfaceMesh, facet_group_indices: Annotated[NDArray[numpy.uint32], dict(order='C', device='cpu')], source_vertex_attr_name: str = '', source_facet_attr_name: str = '', map_attributes: bool = False) -> list[SurfaceMesh]:
    """
    Extract a set of submeshes based on facet groups.

    :param mesh:                    The source mesh.
    :param facet_group_indices:     The group index for each facet. Each group index must be in the range of [0, max(facet_group_indices)]
    :param source_vertex_attr_name: The optional attribute name to track source vertices.
    :param source_facet_attr_name:  The optional attribute name to track source facets.

    :returns: A list of meshes, one for each facet group.
    """

def separate_by_components(mesh: SurfaceMesh, source_vertex_attr_name: str = '', source_facet_attr_name: str = '', map_attributes: bool = False, connectivity_type: ConnectivityType = ConnectivityType.Edge) -> list[SurfaceMesh]:
    """
    Extract a set of submeshes based on connected components.

    :param mesh:                    The source mesh.
    :param source_vertex_attr_name: The optional attribute name to track source vertices.
    :param source_facet_attr_name:  The optional attribute name to track source facets.
    :param map_attributes:          Map attributes from the source to target meshes.
    :param connectivity_type:       The connectivity used for component computation.

    :returns: A list of meshes, one for each connected component.
    """

def extract_submesh(mesh: SurfaceMesh, selected_facets: Annotated[NDArray[numpy.uint32], dict(order='C', device='cpu')], source_vertex_attr_name: str = '', source_facet_attr_name: str = '', map_attributes: bool = False) -> SurfaceMesh:
    """
    Extract a submesh based on the selected facets.

    :param mesh:                    The source mesh.
    :param selected_facets:         A listed of facet ids to extract.
    :param source_vertex_attr_name: The optional attribute name to track source vertices.
    :param source_facet_attr_name:  The optional attribute name to track source facets.
    :param map_attributes:          Map attributes from the source to target meshes.

    :returns: A mesh that contains only the selected facets.
    """

def compute_dihedral_angles(mesh: SurfaceMesh, output_attribute_name: Optional[str] = None, facet_normal_attribute_name: Optional[str] = None, recompute_facet_normals: Optional[bool] = None, keep_facet_normals: Optional[bool] = None) -> int:
    """
    Compute dihedral angles for each edge.

    The dihedral angle of an edge is defined as the angle between the __normals__ of two facets adjacent
    to the edge. The dihedral angle is always in the range [0, pi] for manifold edges. For boundary
    edges, the dihedral angle defaults to 0.  For non-manifold edges, the dihedral angle is not
    well-defined and will be set to the special value 2 * π.

    :param mesh:                        The source mesh.
    :param output_attribute_name:       The optional edge attribute name to store the dihedral angles.
    :param facet_normal_attribute_name: The optional attribute name to store the facet normals.
    :param recompute_facet_normals:     Whether to recompute facet normals.
    :param keep_facet_normals:          Whether to keep newly computed facet normals. It has no effect on pre-existing facet normals.

    :return: The edge attribute id of dihedral angles.
    """

def compute_edge_lengths(mesh: SurfaceMesh, output_attribute_name: Optional[str] = None) -> int:
    """
    Compute edge lengths.

    :param mesh:                  The source mesh.
    :param output_attribute_name: The optional edge attribute name to store the edge lengths.

    :return: The edge attribute id of edge lengths.
    """

def compute_dijkstra_distance(mesh: SurfaceMesh, seed_facet: int, barycentric_coords: list, radius: Optional[float] = None, output_attribute_name: str = '@dijkstra_distance', output_involved_vertices: bool = False) -> Optional[list[int]]:
    """
    Compute Dijkstra distance from a seed facet.

    :param mesh:                  The source mesh.
    :param seed_facet:            The seed facet index.
    :param barycentric_coords:    The barycentric coordinates of the seed facet.
    :param radius:                The maximum radius of the dijkstra distance.
    :param output_attribute_name: The output attribute name to store the dijkstra distance.
    :param output_involved_vertices: Whether to output the list of involved vertices.
    """

def weld_indexed_attribute(mesh: SurfaceMesh, attribute_id: int, epsilon_rel: Optional[float] = None, epsilon_abs: Optional[float] = None, angle_abs: Optional[float] = None, exclude_vertices: Optional[Sequence[int]] = None) -> None:
    """
    Weld indexed attribute.

    :param mesh:         The source mesh to be updated in place.
    :param attribute_id: The indexed attribute id to weld.
    :param epsilon_rel:  The relative tolerance for welding.
    :param epsilon_abs:  The absolute tolerance for welding.
    :param angle_abs:    The absolute angle tolerance for welding.
    :param exclude_vertices: Optional list of vertex indices to exclude from welding.
    """

def compute_euler(mesh: SurfaceMesh) -> int:
    """
    Compute the Euler characteristic.

    :param mesh: The source mesh.

    :return: The Euler characteristic.
    """

def is_closed(mesh: SurfaceMesh) -> bool:
    """
    Check if the mesh is closed.

    A mesh is considered closed if it has no boundary edges.

    :param mesh: The source mesh.

    :return: Whether the mesh is closed.
    """

def is_vertex_manifold(mesh: SurfaceMesh) -> bool:
    """
    Check if the mesh is vertex manifold.

    :param mesh: The source mesh.

    :return: Whether the mesh is vertex manifold.
    """

def is_edge_manifold(mesh: SurfaceMesh) -> bool:
    """
    Check if the mesh is edge manifold.

    :param mesh: The source mesh.

    :return: Whether the mesh is edge manifold.
    """

def is_manifold(mesh: SurfaceMesh) -> bool:
    """
    Check if the mesh is manifold.

    A mesh considered as manifold if it is both vertex and edge manifold.

    :param mesh: The source mesh.

    :return: Whether the mesh is manifold.
    """

def is_oriented(mesh: SurfaceMesh) -> bool:
    """
    Check if the mesh is oriented.

    :param mesh: The source mesh.

    :return: Whether the mesh is oriented.
    """

def transform_mesh(mesh: SurfaceMesh, affine_transform: Annotated[NDArray[numpy.float64], dict(shape=(4, 4), order='F')], normalize_normals: bool = True, normalize_tangents_bitangents: bool = True, in_place: bool = True) -> Optional[SurfaceMesh]:
    """
    Apply affine transformation to a mesh.

    :param mesh: Input mesh.
    :param affine_transform: Affine transformation matrix.
    :param normalize_normals: Whether to normalize normals.
    :param normalize_tangents_bitangents: Whether to normalize tangents and bitangents.
    :param in_place: Whether to apply transformation in place.

    :returns: Transformed mesh if in_place is False.
    """

class DistortionMetric(enum.Enum):
    """Distortion metric."""

    Dirichlet = 0
    """Dirichlet energy"""

    InverseDirichlet = 1
    """Inverse Dirichlet energy"""

    SymmetricDirichlet = 2
    """Symmetric Dirichlet energy"""

    AreaRatio = 3
    """Area ratio"""

    MIPS = 4
    """Most isotropic parameterization energy"""

def compute_uv_distortion(mesh: SurfaceMesh, uv_attribute_name: str = '@uv', output_attribute_name: str = '@uv_measure', metric: DistortionMetric = DistortionMetric.MIPS) -> int:
    """
    Compute UV distortion.

    :param mesh: Input mesh.
    :param uv_attribute_name: UV attribute name (default: "@uv").
    :param output_attribute_name: Output attribute name (default: "@uv_measure").
    :param metric: Distortion metric (default: MIPS).

    :returns: Facet attribute ID for distortion.
    """

def trim_by_isoline(mesh: SurfaceMesh, attribute: Union[int, str], isovalue: float = 0.0, keep_below: bool = True) -> SurfaceMesh:
    """
    Trim a triangle mesh by an isoline.

    :param mesh: Input triangle mesh.
    :param attribute: Attribute ID or name of scalar field (vertex or indexed).
    :param isovalue: Isovalue to trim with.
    :param keep_below: Whether to keep the part below the isoline.

    :returns: Trimmed mesh.
    """

def extract_isoline(mesh: SurfaceMesh, attribute: Union[int, str], isovalue: float = 0.0) -> SurfaceMesh:
    """
    Extract the isoline of an implicit function defined on the mesh vertices/corners.

    The input mesh must be a triangle mesh.

    :param mesh:       Input triangle mesh to extract the isoline from.
    :param attribute:  Attribute id or name of the scalar field to use. Can be a vertex or indexed attribute.
    :param isovalue:   Isovalue to extract.

    :return: A mesh whose facets is a collection of size 2 elements representing the extracted isoline.
    """

def filter_attributes(mesh: SurfaceMesh, included_attributes: Optional[Sequence[Union[int, str]]] = None, excluded_attributes: Optional[Sequence[Union[int, str]]] = None, included_usages: Optional[Set[AttributeUsage]] = None, included_element_types: Optional[Set[AttributeElement]] = None) -> SurfaceMesh:
    """
    Filters the attributes of mesh according to user specifications.

    :param mesh: Input mesh.
    :param included_attributes: List of attribute names or ids to include. By default, all attributes are included.
    :param excluded_attributes: List of attribute names or ids to exclude. By default, no attribute is excluded.
    :param included_usages: List of attribute usages to include. By default, all usages are included.
    :param included_element_types: List of attribute element types to include. By default, all element types are included.
    """

def cast_attribute(mesh: SurfaceMesh, input_attribute: Union[int, str], dtype: type, output_attribute_name: Optional[str] = None) -> int:
    """
    Cast an attribute to a new dtype.

    :param mesh:            The input mesh.
    :param input_attribute: The input attribute id or name.
    :param dtype:           The new dtype.
    :param output_attribute_name: The output attribute name. If none, cast will replace the input attribute.

    :returns: The id of the new attribute.
    """

def compute_mesh_covariance(mesh: SurfaceMesh, center: Sequence[float], active_facets_attribute_name: Optional[str] = None) -> list[list[float]]:
    """
    Compute the covariance matrix of a mesh w.r.t. a center (Pythonic API).

    :param mesh: Input mesh.
    :param center: The center of the covariance computation.
    :param active_facets_attribute_name: (optional) Attribute name of whether a facet should be considered in the computation.

    :returns: The 3 by 3 covariance matrix, which should be symmetric.
    """

def select_facets_by_normal_similarity(mesh: SurfaceMesh, seed_facet_id: int, flood_error_limit: float | None = None, flood_second_to_first_order_limit_ratio: float | None = None, facet_normal_attribute_name: str | None = None, is_facet_selectable_attribute_name: str | None = None, output_attribute_name: str | None = None, search_type: Literal['BFS', 'DFS'] | None = None,num_smooth_iterations: int | None = None) -> int:
    """
    Select facets by normal similarity (Pythonic API).

    :param mesh: Input mesh.
    :param seed_facet_id: Index of the seed facet.
    :param flood_error_limit: Tolerance for normals of the seed and the selected facets. Higher limit leads to larger selected region.
    :param flood_second_to_first_order_limit_ratio: Ratio of the flood_error_limit and the tolerance for normals of neighboring selected facets. Higher ratio leads to more curvature in selected region.
    :param facet_normal_attribute_name: Attribute name of the facets normal. If the mesh doesn't have this attribute, it will call compute_facet_normal to compute it.
    :param is_facet_selectable_attribute_name: If provided, this function will look for this attribute to determine if a facet is selectable.
    :param output_attribute_name: Attribute name of whether a facet is selected.
    :param search_type: Use 'BFS' for breadth-first search or 'DFS' for depth-first search.
    :param num_smooth_iterations: Number of iterations to smooth the boundary of the selected region.

    :returns: Id of the attribute on whether a facet is selected.
    """

def select_facets_in_frustum(mesh: SurfaceMesh, frustum_plane_points: Sequence[Sequence[float]], frustum_plane_normals: Sequence[Sequence[float]], greedy: Optional[bool] = None, output_attribute_name: Optional[str] = None) -> bool:
    """
    Select facets in a frustum (Pythonic API).

    :param mesh: Input mesh.
    :param frustum_plane_points: Four points on each of the frustum planes.
    :param frustum_plane_normals: Four normals of each of the frustum planes.
    :param greedy: If true, the function returns as soon as the first facet is found.
    :param output_attribute_name: Attribute name of whether a facet is selected.

    :returns: Whether any facets got selected.
    """

def thicken_and_close_mesh(mesh: SurfaceMesh, offset_amount: Optional[float] = None, direction: Optional[Union[Sequence[float], str]] = None, mirror_ratio: Optional[float] = None, num_segments: Optional[int] = None, indexed_attributes: Optional[Sequence[str]] = None) -> SurfaceMesh:
    """
    Thicken a mesh by offsetting it, and close the shape into a thick 3D solid.

    :param mesh: Input mesh.
    :param direction: Direction of the offset. Can be an attribute name or a fixed 3D vector.
    :param offset_amount: Amount of offset.
    :param mirror_ratio: Ratio of the offset amount to mirror the mesh.
    :param num_segments: Number of segments to use for the thickening.
    :param indexed_attributes: List of indexed attributes to copy to the new mesh.

    :returns: The thickened and closed mesh.
    """

def extract_boundary_loops(mesh: SurfaceMesh) -> list[list[int]]:
    """
    Extract boundary loops from a mesh.

    :param mesh: Input mesh.

    :returns: A list of boundary loops, each represented as a list of vertex indices.
    """

def extract_boundary_edges(mesh: SurfaceMesh) -> list[int]:
    """
    Extract boundary edges from a mesh.

    :param mesh: Input mesh.

    :returns: A list of boundary edge indices.
    """

def compute_uv_charts(mesh: SurfaceMesh, uv_attribute_name: str = '', output_attribute_name: str = '@chart_id', connectivity_type: str = 'Edge') -> int:
    """
    Compute UV charts.

    @param mesh: Input mesh.
    @param uv_attribute_name: Name of the UV attribute.
    @param output_attribute_name: Name of the output attribute to store the chart ids.
    @param connectivity_type: Type of connectivity to use for chart computation. Can be "Vertex" or "Edge".

    @returns: A list of chart ids for each vertex.
    """

def uv_mesh_view(mesh: SurfaceMesh, uv_attribute_name: str = '') -> SurfaceMesh:
    """
    Extract a UV mesh view from a 3D mesh.

    :param mesh: Input mesh.
    :param uv_attribute_name: Name of the (indexed or vertex) UV attribute.

    :return: A new mesh representing the UV mesh.
    """

def uv_mesh_ref(mesh: SurfaceMesh, uv_attribute_name: str = '') -> SurfaceMesh:
    """
    Extract a UV mesh reference from a 3D mesh.

    :param mesh: Input mesh.
    :param uv_attribute_name: Name of the (indexed or vertex) UV attribute.

    :return: A new mesh representing the UV mesh.
    """

def split_facets_by_material(mesh: SurfaceMesh, material_attribute_name: str) -> None:
    """
    Split mesh facets based on a material attribute.

    @param mesh: Input mesh on which material segmentation will be applied in place.
    @param material_attribute_name: Name of the material attribute to use for inserting boundaries.

    @note The material attribute should be n by k vertex attribute, where n is the number of vertices,
    and k is the number of materials. The value at row i and column j indicates the probability of vertex
    i belonging to material j. The function will insert boundaries between different materials based on
    the material attribute.
    """

def remove_isolated_vertices(mesh: SurfaceMesh) -> None:
    """
    Remove isolated vertices from a mesh.

    .. note::
        A vertex is considered isolated if it is not referenced by any facet.

    :param mesh: Input mesh (modified in place).
    """

def detect_degenerate_facets(mesh: SurfaceMesh) -> list[int]:
    """
    Detect degenerate facets in a mesh.

    .. note::
        Only exactly degenerate facets are detected.

    :param mesh: Input mesh.

    :returns: List of degenerate facet indices.
    """

def remove_null_area_facets(mesh: SurfaceMesh, null_area_threshold: float = 0, remove_isolated_vertices: bool = False) -> None:
    """
    Remove facets with unsigned facets area <= `null_area_threhsold`.

    :param mesh: Input mesh (modified in place).
    :param null_area_threshold: Area threshold below which facets are considered null.
    :param remove_isolated_vertices: Whether to remove isolated vertices after removing null area facets.
    """

def remove_duplicate_vertices(mesh: SurfaceMesh, extra_attributes: Optional[Sequence[int]] = None, boundary_only: bool = False) -> None:
    """
    Remove duplicate vertices from a mesh.

    :param mesh: Input mesh (modified in place).
    :param extra_attributes: Additional attributes to consider when detecting duplicates.
    :param boundary_only: Only remove duplicate vertices on the boundary.
    """

def remove_duplicate_facets(mesh: SurfaceMesh, consider_orientation: bool = False) -> None:
    """
    Remove duplicate facets from a mesh.

    Facets with different orientations (e.g. (0,1,2) and (2,1,0)) are considered duplicates.
    If both orientations have equal counts, all are removed.
    If one orientation has more duplicates, all but one of the majority orientation are kept.

    :param mesh: Input mesh (modified in place).
    :param consider_orientation: Whether to consider orientation when detecting duplicates.
    """

def remove_topologically_degenerate_facets(mesh: SurfaceMesh) -> None:
    """
    Remove topologically degenerate facets such as (0,1,1).

    For polygons, topological degeneracy means the polygon has at most two unique vertices.
    E.g. quad (0,0,1,1) is degenerate, while (1,1,2,3) is not.

    :param mesh: Input mesh (modified in place).
    """

def remove_short_edges(mesh: SurfaceMesh, threshold: float = 0) -> None:
    """
    Remove short edges from a mesh.

    :param mesh: Input mesh (modified in place).
    :param threshold: Minimum edge length below which edges are considered short.
    """

def resolve_vertex_nonmanifoldness(mesh: SurfaceMesh) -> None:
    """
    Resolve vertex non-manifoldness in a mesh.

    :param mesh: Input mesh (modified in place).

    :raises RuntimeError: If the input mesh is not edge-manifold.
    """

def resolve_nonmanifoldness(mesh: SurfaceMesh) -> None:
    """
    Resolve both vertex and edge nonmanifoldness in a mesh.

    :param mesh: Input mesh (modified in place).
    """

def split_long_edges(mesh: SurfaceMesh, max_edge_length: float = 0.10000000149011612, recursive: bool = True, active_region_attribute: Optional[str] = None, edge_length_attribute: Optional[str] = None) -> None:
    """
    Split edges longer than max_edge_length.

    :param mesh: Input mesh (modified in place).
    :param max_edge_length: Maximum edge length threshold.
    :param recursive: If true, apply recursively until no edge exceeds threshold.
    :param active_region_attribute: Facet attribute name for active region (uint8_t type).
                                    If None, all edges are considered.
    :param edge_length_attribute: Edge length attribute name.
                                  If None, edge lengths are computed.
    """

def remove_degenerate_facets(mesh: SurfaceMesh) -> None:
    """
    Remove degenerate facets from a mesh.

    .. note::
        Assumes triangular mesh. Use `triangulate_polygonal_facets` for non-triangular meshes.
        Adjacent non-degenerate facets may be re-triangulated during removal.

    :param mesh: Input mesh (modified in place).
    """

def close_small_holes(mesh: SurfaceMesh, max_hole_size: int = 16, triangulate_holes: bool = True) -> None:
    """
    Close small holes in a mesh.

    :param mesh: Input mesh (modified in place).
    :param max_hole_size: Maximum number of vertices on a hole to be closed.
    :param triangulate_holes: Whether to triangulate holes (if false, fill with polygons).
    """

def rescale_uv_charts(mesh: SurfaceMesh, uv_attribute_name: str = '', chart_id_attribute_name: str = '', uv_area_threshold: float = 1e-06) -> None:
    """
    Rescale UV charts to match their 3D aspect ratios.

    :param mesh: Input mesh (modified in place).
    :param uv_attribute_name: UV attribute name for rescaling.
                             If empty, uses first UV attribute found.
    :param chart_id_attribute_name: Patch ID attribute name.
                                    If empty, computes patches from UV chart connectivity.
    :param uv_area_threshold: UV area threshold.
                             Triangles below this threshold don't contribute to scale computation.
    """
