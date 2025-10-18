"""
Functional interface to common nn operations.

`lietorch.nn.m2.max_project_m2`

`lietorch.nn.m2.reflection_pad_m2`

`lietorch.nn.m2.lift_m2_cartesian`

`lietorch.nn.m2.conv_m2_cartesian`

`lietorch.nn.m2.conv_m2_bspline`

`lietorch.nn.m2.anisotropic_dilated_project_m2`

`lietorch.nn.m2.convection_m2`
"""

from lietorch.nn.m2 import (
    max_project_m2,
    reflection_pad_m2,
    lift_m2_cartesian,
    conv_m2_cartesian,
    conv_m2_bspline,
    anisotropic_dilated_project_m2,
    convection_m2,
    linear_convolution_m2,
    morphological_convolution_m2,
    diffusion_m2,
    fractional_dilation_m2,
    fractional_erosion_m2,
    linear_m2,
)

from lietorch.nn.r2 import (
    morphological_convolution_r2,
    morphological_kernel_r2,
    fractional_dilation_r2,
    fractional_erosion_r2,
    linear_r2,
    convection_r2,
    diffusion_kernel_r2,
    diffusion_r2,
    switch_diffusion_shock_r2,
)

from lietorch.nn.loss import dice_loss
