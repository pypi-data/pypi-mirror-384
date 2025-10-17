from collections.abc import Sequence
from typing import Annotated

import numpy
from numpy.typing import NDArray

import lagrange.core
import lagrange.scene


def texture_filtering(mesh: lagrange.core.SurfaceMesh, image: Annotated[NDArray[numpy.float32], dict(shape=(None, None, None), order='C', device='cpu')], value_weight: float = 1000.0, gradient_weight: float = 1.0, gradient_scale: float = 1.0, quadrature_samples: int = 6, jitter_epsilon: float = 0.0001) -> object:
    """
    "Smooth or sharpen a texture image associated with a mesh.

    :param mesh: Input mesh with UV attributes.
    :param image: Texture image to filter.
    :param value_weight: The weight for fitting the values of the signal.
    :param gradient_weight: The weight for fitting the modulated gradients of the signal.
    :param gradient_scale: The gradient modulation weight. Use a value of 0 for smoothing, and use a value between [2, 10] for sharpening.
    :param quadrature_samples: The number of quadrature samples to use for integration (in {1, 3, 6, 12, 24, 32}).
    :param jitter_epsilon: Jitter amount per texel (0 to deactivate).

    :return: The filtered texture image.
    """

def texture_stitching(mesh: lagrange.core.SurfaceMesh, image: Annotated[NDArray[numpy.float32], dict(shape=(None, None, None), order='C', device='cpu')], exterior_only: bool = False, quadrature_samples: int = 6, jitter_epsilon: float = 0.0001) -> object:
    """
    Smooth or sharpen a texture image associated with a mesh.

    :param mesh: Input mesh with UV attributes.
    :param image: Texture image to stitch.
    :param exterior_only: If true, interior texels are fixed degrees of freedom.
    :param quadrature_samples: The number of quadrature samples to use for integration (in {1, 3, 6, 12, 24, 32}).
    :param jitter_epsilon: Jitter amount per texel (0 to deactivate).

    :return: The stitched texture image.
    """

def geodesic_dilation(mesh: lagrange.core.SurfaceMesh, image: Annotated[NDArray[numpy.float32], dict(shape=(None, None, None), order='C', device='cpu')], dilation_radius: float = 10) -> object:
    """
    Extend pixels of a texture beyond the defined UV mesh by walking along the 3D surface.

    :param mesh: Input mesh with UV attributes.
    :param image: Texture to extend beyond UV mesh boundaries.
    :param dilation_radius: The radius by which the texture should be dilated into the gutter.

    :return: The dilated texture image.
    """

def geodesic_position(mesh: lagrange.core.SurfaceMesh, width: int, height: int, dilation_radius: float = 10) -> object:
    """
    Computes a dilated position map to extend a texture beyond the defined UV mesh by walking along the 3D surface.

    :param mesh: Input mesh with UV attributes.
    :param width: Width of the output position map.
    :param height: Height of the output position map.
    :param dilation_radius: The radius by which the texture should be dilated into the gutter.

    :return: The dilated position map.
    """

def texture_compositing(mesh: lagrange.core.SurfaceMesh, colors: Sequence[Annotated[NDArray[numpy.float32], dict(shape=(None, None, None), order='C', device='cpu')]], weights: Sequence[Annotated[NDArray[numpy.float32], dict(shape=(None, None, None), order='C', device='cpu')]], value_weight: float = 1000.0, quadrature_samples: int = 6, jitter_epsilon: float = 0.0001, smooth_low_weight_areas: bool = False, num_multigrid_levels: int = 4, num_gauss_seidel_iterations: int = 3, num_v_cycles: int = 5) -> object:
    """
    Composite multiple (color, weight) into a single texture given a unwrapped mesh.

    :param mesh: Input mesh with UV attributes.
    :param colors: List of texture images to composite. Input textures must have the same dimensions.
    :param weights: List of confidence weights for each texel. 0 means the texel should be ignored, 1 means the texel should be fully trusted. Input weights must have the same dimensions as colors.
    :param value_weight: The weight for fitting the values of the signal.
    :param quadrature_samples: The number of quadrature samples to use for integration (in {1, 3, 6, 12, 24, 32}).
    :param jitter_epsilon: Jitter amount per texel (0 to deactivate).
    :param smooth_low_weight_areas: Whether to smooth pixels with a low total weight (< 1). When enabled, this will not dampen the gradient terms for pixels with a low total weight, resulting in a smoother texture in low-confidence areas.
    :param num_multigrid_levels: Number of multigrid levels.
    :param num_gauss_seidel_iterations: Number of Gauss-Seidel iterations per multigrid level.
    :param num_v_cycles: Number of V-cycles to perform.

    :return: The composited texture image.
    """

def rasterize_textures_from_renders(scene: lagrange.scene.Scene, renders: Sequence[Annotated[NDArray[numpy.float32], dict(shape=(None, None, None), order='C', device='cpu')]], width: int | None = None, height: int | None = None, low_confidence_ratio: float = 0.75, base_confidence: float | None = None) -> tuple[list[object], list[object]]:
    """
    Rasterize one (color, weight) per (render, camera) and filter our low-confidence weights.

    :param scene: Scene containing a single mesh (possibly with a base texture), and multiple cameras.
    :param renders: List of rendered images, one per camera.
    :param width: Width of the rasterized textures. Must match the width of the base texture if present. Otherwise, defaults to 1024.
    :param height: Height of the rasterized textures. Must match the height of the base texture if present. Otherwise, defaults to 1024.
    :param low_confidence_ratio: Discard low confidence texels whose weights are < ratio * max_weight.
    :param base_confidence: Confidence value for the base texture if present in the scene. If set to 0, ignore the base texture of the mesh. Defaults to 0.3 otherwise.

    :return: A pair of lists (textures, weights), one per camera.
    """
