from typing import Annotated, Union

import numpy
from numpy.typing import NDArray

import lagrange.core


class TriangleAABBTree3D:
    def __init__(self, mesh: lagrange.core.SurfaceMesh) -> None:
        """Construct AABB tree from a triangle mesh"""

    def empty(self) -> bool:
        """Check if the tree is empty"""

    def get_elements_in_radius(self, query_point: Union[list, Annotated[NDArray[numpy.float64], dict(shape=(3), order='C', device='cpu')]], radius: float) -> tuple[list[int], Annotated[NDArray[numpy.float64], dict(shape=(None, 3), order='C', device='cpu')]]:
        """
        Find all elements within a given radius from a query point.

        :param query_point: Query point.
        :param radius: Search radius.

        :return: A tuple containing:
            - A list of element indices within the specified radius.
            - A NumPy array of shape (N, 3) containing the closest points on each element.
        """

    def get_closest_point(self, query_point: Union[list, Annotated[NDArray[numpy.float64], dict(shape=(3), order='C', device='cpu')]]) -> tuple[int, Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')], float]:
        """
        Find the closest element and point within the element to the query point

        :param query_point: Query point.
        :return: A tuple containing:
            - The index of the closest element.
            - A NumPy array representing the closest point on the element.
            - The squared distance between the query point and the closest point.
        """

class TriangleAABBTree2D:
    def __init__(self, mesh: lagrange.core.SurfaceMesh) -> None:
        """Construct AABB tree from a 2D triangle mesh"""

    def empty(self) -> bool:
        """Check if the tree is empty"""

    def get_elements_in_radius(self, query_point: Union[list, Annotated[NDArray[numpy.float64], dict(shape=(2), order='C', device='cpu')]], radius: float) -> tuple[list[int], Annotated[NDArray[numpy.float64], dict(shape=(None, 2), order='C', device='cpu')]]:
        """
        Find all elements within a given radius from a query point.

        :param query_point: Query point.
        :param radius: Search radius.

        :return: A tuple containing:
            - A list of element indices within the specified radius.
            - A NumPy array of shape (N, 2) containing the closest points on each element.
        """

    def get_closest_point(self, query_point: Union[list, Annotated[NDArray[numpy.float64], dict(shape=(2), order='C', device='cpu')]]) -> tuple[int, Annotated[NDArray[numpy.float64], dict(shape=(2), order='C')], float]:
        """
        Find the closest element and point within the element to the query point

        :param query_point: Query point.
        :return: A tuple containing:
            - The index of the closest element.
            - A NumPy array representing the closest point on the element.
            - The squared distance between the query point and the closest point.
        """

class EdgeAABBTree3D:
    def __init__(self, vertices: Annotated[NDArray[numpy.float64], dict(shape=(None, 3), order='F')], edges: Annotated[NDArray[numpy.uint32], dict(shape=(None, 2), order='F')]) -> None:
        """Construct AABB tree from 3D edge graph"""

    def empty(self) -> bool:
        """Check if the tree is empty"""

    def get_element_closest_point(self, query_point: Union[list, Annotated[NDArray[numpy.float64], dict(shape=(3), order='C', device='cpu')]], element_id: int) -> tuple[Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')], float]:
        """
        Get the closest point on a specific edge.

        :param query_point: Query point.
        :param element_id: Index of the edge to query.

        :return: A tuple containing:
            - A NumPy array representing the closest point on the edge.
            - The squared distance between the query point and the closest point.
        """

    def get_elements_in_radius(self, query_point: Union[list, Annotated[NDArray[numpy.float64], dict(shape=(3), order='C', device='cpu')]], radius: float) -> tuple[list[int], Annotated[NDArray[numpy.float64], dict(shape=(None, 3), order='C', device='cpu')]]:
        """
        Find all elements within a given radius from a query point.

        :param query_point: Query point.
        :param radius: Search radius.

        :return: A tuple containing:
            - A list of element indices within the specified radius.
            - A NumPy array of shape (N, 3) containing the closest points on each element.
        """

    def get_containing_elements(self, query_point: Union[list, Annotated[NDArray[numpy.float64], dict(shape=(3), order='C', device='cpu')]]) -> list[int]:
        """
        Find all elements that contain the query point.

        :param query_point: Query point.
        :return: A list of element indices that contain the query point.
        """

    def get_closest_point(self, query_point: Union[list, Annotated[NDArray[numpy.float64], dict(shape=(3), order='C', device='cpu')]]) -> tuple[int, Annotated[NDArray[numpy.float64], dict(shape=(3), order='C')], float]:
        """
        Find the closest element and point within the element to the query point

        :param query_point: Query point.
        :return: A tuple containing:
            - The index of the closest element.
            - A NumPy array representing the closest point on the element.
            - The squared distance between the query point and the closest point.
        """

class EdgeAABBTree2D:
    def __init__(self, vertices: Annotated[NDArray[numpy.float64], dict(shape=(None, 2), order='F')], edges: Annotated[NDArray[numpy.uint32], dict(shape=(None, 2), order='F')]) -> None:
        """Construct AABB tree from 2D edge graph"""

    def empty(self) -> bool:
        """Check if the tree is empty"""

    def get_element_closest_point(self, query_point: Union[list, Annotated[NDArray[numpy.float64], dict(shape=(2), order='C', device='cpu')]], element_id: int) -> tuple[Annotated[NDArray[numpy.float64], dict(shape=(2), order='C')], float]:
        """
        Get the closest point on a specific edge.

        :param query_point: Query point.
        :param element_id: Index of the edge to query.

        :return: A tuple containing:
            - A NumPy array representing the closest point on the edge.
            - The squared distance between the query point and the closest point.
        """

    def get_elements_in_radius(self, query_point: Union[list, Annotated[NDArray[numpy.float64], dict(shape=(2), order='C', device='cpu')]], radius: float) -> tuple[list[int], Annotated[NDArray[numpy.float64], dict(shape=(None, 2), order='C', device='cpu')]]:
        """
        Find all elements within a given radius from a query point.

        :param query_point: Query point.
        :param radius: Search radius.

        :return: A tuple containing:
            - A list of element indices within the specified radius.
            - A NumPy array of shape (N, 2) containing the closest points on each element.
        """

    def get_containing_elements(self, query_point: Union[list, Annotated[NDArray[numpy.float64], dict(shape=(2), order='C', device='cpu')]]) -> list[int]:
        """
        Find all elements that contain the query point.

        :param query_point: Query point.
        :return: A list of element indices that contain the query point.
        """

    def get_closest_point(self, query_point: Union[list, Annotated[NDArray[numpy.float64], dict(shape=(2), order='C', device='cpu')]]) -> tuple[int, Annotated[NDArray[numpy.float64], dict(shape=(2), order='C')], float]:
        """
        Find the closest element and point within the element to the query point

        :param query_point: Query point.
        :return: A tuple containing:
            - The index of the closest element.
            - A NumPy array representing the closest point on the element.
            - The squared distance between the query point and the closest point.
        """

def weld_vertices(mesh: lagrange.core.SurfaceMesh, radius: float = 9.999999974752427e-07, boundary_only: bool = False) -> None:
    """
    Weld nearby vertices together of a surface mesh.

    :param mesh: The target surface mesh to be welded in place.
    :param radius: The maximum distance between vertices to be considered for welding. Default is 1e-6.
    :param boundary_only: If true, only boundary vertices will be considered for welding. Defaults to False.

    .. warning:: This method may introduce non-manifoldness and degeneracy in the mesh.
    """
