import lagrange.core


def mesh_smoothing(mesh: lagrange.core.SurfaceMesh, method: str = 'NormalSmoothing', curvature_weight: float = 0.02, normal_smoothing_weight: float = 0.0001, gradient_weight: float = 0.0001, gradient_modulation_scale: float = 0.0, normal_projection_weight: float = 100.0) -> None:
    """
    Smooths a mesh using anisotropic mesh smoothing.

    :param mesh: Input mesh.
    :param method: The filtering method. Options are ['VertexSmoothing', 'NormalSmoothing']. Default is 'NormalSmoothing'.
    :param curvature_weight: The curvature/inhomogeneity weight. Specifies the extent to which total curvature should be used to change the underlying metric. Setting =0 is equivalent to using standard homogeneous/anisotropic diffusion.
    :param normal_smoothing_weight: The normal smoothing weight. Specifies the extent to which normals should be diffused before curvature is estimated. Formally, this is the time-step for heat-diffusion performed on the normals. Setting =0 will reproduce the original normals.
    :param gradient_weight: Gradient fitting weight. Specifies the importance of matching the gradient constraints (objective #2) relative to matching the positional constraints (objective #1). Setting =0 reproduces the original normals.
    :param gradient_modulation_scale: Gradient modulation scale. Prescribes the scale factor relating the gradients of the source to those of the target. <1 => gradients are dampened => smoothing. >1 => gradients are amplified => sharpening. Setting =0 is equivalent to performing a semi-implicit step of heat-diffusion, with time-step equal to gradient_weight. Setting =1 reproduces the original normals.
    :param normal_projection_weight: Weight for fitting the surface to prescribed normals. Specifies the importance of matching the target normals (objective #2) relative to matching the original positions (objective #1). Setting =0 will reproduce the original geometry.

    :return: The smoothed mesh.
    """

def scalar_attribute_smoothing(mesh: lagrange.core.SurfaceMesh, attribute_name: str = '', curvature_weight: float = 0.02, normal_smoothing_weight: float = 0.0001, gradient_weight: float = 0.0001, gradient_modulation_scale: float = 0.0) -> None:
    """
    Smooths a (multi-channel) scalar attribute on a surface mesh.

    :param mesh: Input mesh.
    :param attribute_name: The name of the scalar vertex attribute to smooth. If empty, all attributes with scalar usage and vertex element type will be smoothed.
    :param curvature_weight: The curvature/inhomogeneity weight. Controls the strength of the smoothing operation. Higher values result in stretching in the surface metric, slowing down diffusion process. The default value of 0.02 provides a moderate smoothing effect. Values should typically be in the range [0.0, 1.0].
    :param normal_smoothing_weight: The normal smoothing weight. Specifies the extent to which normals should be diffused before curvature is estimated.
    :param gradient_weight: Gradient fitting weight. Specifies the importance of matching the gradient constraints.
    :param gradient_modulation_scale: Gradient modulation scale. Prescribes the scale factor relating the gradients of the source to those of the target.

    :return: None. The attribute is modified in place.
    """
