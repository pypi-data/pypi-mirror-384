"""
Functions and modules for R2 (i.e. 2D translation equivariant) neural networks.
"""

import torch
from math import sqrt, floor
import torch.nn.functional as F

_epsilon_float32 = (
    torch.tensor([7], dtype=torch.float32) / 3
    - torch.tensor([4], dtype=torch.float32) / 3
    - 1
).abs()
"""
    Single precision (float32) machine epsilon in tensor form.
"""


def norm_squared_kernel(
    metric_params: torch.Tensor, kernel_radius: int
) -> torch.Tensor:
    c = metric_params.size(dim=0)
    k = kernel_radius
    d = 2 * k + 1
    r = torch.arange(-k, k + 1).to(metric_params.device)
    y, x = torch.meshgrid(r, r, indexing="ij")

    v = torch.stack((x, y), dim=0)
    v = v.float()
    v = v.reshape(2, d * d)

    Hv = metric_params @ v

    norm2 = torch.sum(Hv.square(), dim=1)
    norm2 = norm2.reshape(c, d, d)

    # equivalent way using einsum:
    # G = torch.transpose(H,1,2) @ H
    # norm2 = torch.einsum('cij,xyi,xyj->cxy',G,v,v)

    return norm2


def norm_squared_kernel_isotropic(
    metric_params: torch.Tensor, kernel_radius: int
) -> torch.Tensor:
    k = kernel_radius
    r = torch.arange(-k, k + 1).to(metric_params.device)
    y, x = torch.meshgrid(r, r, indexing="ij")

    return F.relu(metric_params)[:, None, None] * (x**2 + y**2)


def first_order_derivatives(input: torch.Tensor):
    device = input.device
    C = input.shape[-3]

    kernel_x = (
        torch.tensor([-1.0, 0.0, 1.0], device=device).view(1, 3).repeat(C, 1, 1, 1)
        / 2.0
    )
    kernel_y = (
        torch.tensor([-1.0, 0.0, 1.0], device=device).view(3, 1).repeat(C, 1, 1, 1)
        / 2.0
    )

    dx = F.conv2d(
        F.pad(input, (1, 1, 0, 0), mode="replicate"),
        kernel_x,
        groups=C,
    )
    dy = F.conv2d(
        F.pad(input, (0, 0, 1, 1), mode="replicate"),
        kernel_y,
        groups=C,
    )

    return dx, dy


def second_order_derivatives(input: torch.Tensor):
    device = input.device
    C = input.shape[-3]

    kernel_x = (
        torch.tensor([1.0, -2.0, 1.0], device=device).view(1, 3).repeat(C, 1, 1, 1)
    )
    kernel_y = (
        torch.tensor([1.0, -2.0, 1.0], device=device).view(3, 1).repeat(C, 1, 1, 1)
    )

    ddx = F.conv2d(
        F.pad(input, (1, 1, 0, 0), mode="reflect"),
        kernel_x,
        groups=C,
    )
    ddy = F.conv2d(
        F.pad(input, (0, 0, 1, 1), mode="reflect"),
        kernel_y,
        groups=C,
    )

    return ddx, ddy  # , dxdy


def morphological_kernel_r2_finslerian(
    finsler_params: torch.Tensor, kernel_radius: int, alpha: float
) -> torch.Tensor:
    """
    Construct a set of Finsler functions based on circular harmonics basis functions.

    Parameters
    -----------

    finsler_params: torch.Tensor
        Tensor of shape `[... , K]`,

    kernel_radius: int
        The kernel will be sampled on a recti-linear grid of size `[2*kernel_radius+1, 2*kernel_radius+1]`.

    alpha: float
        Alpha parameter, must be >= 0.55 and <= 1.0 for stability.

    Returns
    ---------
    A Tensor of shape `[... , 2*kernel_radius+1, 2*kernel_radius+1]`.
    """
    return torch.ops.lietorch.r2_morphological_kernel(
        finsler_params, kernel_radius, alpha
    )


def morphological_kernel_r2(
    metric_params: torch.Tensor, kernel_radius: int, alpha: float
) -> torch.Tensor:
    """
    Construct approximate morphological kernel corresponding to the Riemannian metric given by `metric_params`. Based on https://gitlab.com/gijsbel/semifield-pde-cnns.

    Parameters
    ------------
    metric_params: torch.Tensor
        Metric parameters in a tensor of shape `[C,2,2]`. The Riemannian metric tensor is parametrized by `H`:
        $$
            G_{C}(x,y) = H[C]^T H[C],
        $$

    kernel_radius: int
        Size `[2*kernel_radius+1, 2*kernel_radius+1]` of the grid on which the kernel will be sampled.

    Returns
    ---------
    A Tensor of shape `[... , 2*kernel_radius+1, 2*kernel_radius+1]`.
    """
    beta = 1.0 / (1.0 - 1.0 / (2.0 * alpha))
    norm2 = norm_squared_kernel(metric_params, kernel_radius)
    kernel = 1.0 / beta * norm2.pow(beta / 2.0)
    return kernel


def morphological_kernel_r2_isotropic(
    metric_params: torch.Tensor, kernel_radius: int, alpha: float
) -> torch.Tensor:
    """
    Construct approximate morphological kernel corresponding to the Riemannian metric given by `metric_params`.

    Parameters
    ------------
    metric_params: torch.Tensor
        Metric parameters in a tensor of shape `[C]`. The Riemannian metric tensor is parametrized by `g`:
        $$
            G_{C}(x,y) = g[C] * Id(2),
        $$

    kernel_radius: int
        Size `[2*kernel_radius+1, 2*kernel_radius+1]` of the grid on which the kernel will be sampled.

    Returns
    ---------
    A Tensor of shape `[... , 2*kernel_radius+1, 2*kernel_radius+1]`.
    """
    beta = 1.0 / (1.0 - 1.0 / (2.0 * alpha))
    norm2 = norm_squared_kernel_isotropic(metric_params, kernel_radius)
    kernel = 1.0 / beta * norm2.pow(beta / 2.0)
    return kernel


def morphological_convolution_r2(
    input: torch.Tensor, kernel: torch.Tensor
) -> torch.Tensor:
    """
    Apply morphological convolution to each channel with the corresponding kernel.

    In pseudo-code where we take liberties with tensor indices we can write:
    $$
        output[b,c,y,x] = \\inf_{(y', x') ∈ ℝ²} input[b,c,y+y',x+x'] + kernel[c,y',x'].
    $$

    Parameters
    ----------

    input: torch.Tensor
        Tensor of shape `[B,C,H,W]`

    kernel: torch.Tensor
        Tensor of shape `[C,kH,kW]`

    Returns
    ---------
    A Tensor of shape `[B,C,H,W]`
    """
    return torch.ops.lietorch.r2_morphological_convolution(input, kernel)


class MorphologicalConvolutionR2(torch.nn.Module):
    """
    Modular interface to `lietorch.nn.r2.morphological_convolution_r2`. The **kernel** tensor is part of the module's state.

    Parameters
    ------------
    channels: int
        Number of channels the input tensor is expected to have, i.e. the `C` in `[B,C,H,W]`.

    kernel_size: tuple[int, int]
        Size of the kernel, i.e. the `kH`, `kW` in `[C,kH,kW]`. Needs to be an odd number.
    """

    channels: int
    kernel_size: tuple[int, int]
    kernel: torch.Tensor

    def __init__(self, channels: int, kernel_size: tuple[int, int]) -> None:
        super().__init__()

        assert (
            kernel_size[0] % 2 == 1
            and kernel_size[1] % 2 == 1
            and kernel_size[0] > 0
            and kernel_size[1] > 1
        ), "kernel sizes need to be positive odd numbers"

        self.channels = channels
        self.kernel_size = kernel_size
        self.kernel = torch.nn.Parameter(torch.Tensor(channels, *kernel_size))

        self.reset_parameters()

    def reset_parameters(self) -> None:
        torch.nn.init.uniform_(self.kernel, a=0.0, b=1.0)

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        return morphological_convolution_r2(input, self.kernel)


def fractional_dilation_r2_finslerian(
    input: torch.Tensor, finsler_params: torch.Tensor, kernel_radius: int, alpha: float
) -> torch.Tensor:
    """
    Apply left invariant (translation equivariant in this case) dilation to the `input` based on the Finsler functions as given by `finsler_params`.

    Parameters
    ------------
    input: torch.Tensor
        Input tensor of shape `[B,C,H,W]`.

    finsler_params: torch.Tensor
        Finsler parameters in a tensor of shape `[C,K]`. The Finsler function is parametrized by the `K` parameters as:
        $$
            F_{C}(x,y) = \\sqrt{x^2+y^2} \\exp{\\left( - \\sum_{k=1}^K \\textrm{finsler_params}[C, k] \\cdot B_k(x,y) \\right)},
        $$
        where B_k is the k-th circular harmonic basis function.

    kernel_radius: int
        Size `[2*kernel_radius+1, 2*kernel_radius+1]` of the grid on which the kernel will be sampled.

    alpha: float
        Alpha parameter, must be >= 0.55 and <= 1.0 for stability.

    Returns
    --------
    A tensor of shape `[B,C,H,W]`
    """
    return torch.ops.lietorch.r2_fractional_dilation(
        input, finsler_params, kernel_radius, alpha
    )


class FractionalDilationR2Finslerian(torch.nn.Module):
    """
    Modular interface to `lietorch.nn.r2.fractional_dilation_r2` where the **finsler_params** tensor is part of the module's state.

    Parameters
    ------------
    channels: int
        Number of channels the input tensor is expected to have, i.e. the `C` in `[B,C,H,W]`.

    finsler_order: int
        Orders of the circular harmonics used to construct the Finsler function, i.e. the kernel will be parametrized by this number of parameters.

    kernel_size: int
        Size of the grid where the morphological kernel will be sampled, i.e. kernel_size both in height and width.

    alpha: float
        Alpha parameter, has to be >= 0.55 and <= 1.0 for stability.
    """

    channels: int
    finsler_order: int
    kernel_size: int
    alpha: float
    finsler_params: torch.Tensor

    def __init__(
        self, channels: int, kernel_size: int, alpha: float, finsler_order: int
    ):
        super().__init__()

        assert channels > 0, "channels needs to be strictly positive"
        assert finsler_order > 0, "finsler_order needs to be strictly positive"
        assert kernel_size % 2 == 1 and kernel_size > 0, (
            f"kernel_size ({kernel_size}) must be a positive odd number for well-defined convolutions."
        )
        assert alpha >= 0.55 and alpha <= 1.0, "alpha needs to be >= 0.55 and <= 1.0"

        self.channels = channels
        self.finsler_order = finsler_order
        self.kernel_radius = kernel_size // 2
        self.alpha = alpha
        self.finsler_params = torch.nn.Parameter(torch.Tensor(channels, finsler_order))
        self._cached_kernel = None

        self.reset_parameters()

    def reset_parameters(self) -> None:
        torch.nn.init.uniform_(self.finsler_params, a=-1.0, b=1.0)

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        return fractional_dilation_r2_finslerian(
            input, self.finsler_params, self.kernel_radius, self.alpha
        )


def fractional_dilation_r2(
    input: torch.Tensor, metric_params: torch.Tensor, kernel_radius: int, alpha: float
) -> torch.Tensor:
    """
    Apply left invariant (translation equivariant in this case) dilation to the `input` based on the Riemannian metric as given by `metric_params`. Based on https://gitlab.com/gijsbel/semifield-pde-cnns.

    Parameters
    ------------
    input: torch.Tensor
        Input tensor of shape `[B,C,H,W]`.

    metric_params: torch.Tensor
        Metric parameters in a tensor of shape `[C,2,2]`. The Riemannian metric tensor is parametrized by `H`:
        $$
            G_{C}(x,y) = H[C]^T H[C],
        $$

    kernel_radius: int
        Size `[2*kernel_radius+1, 2*kernel_radius+1]` of the grid on which the kernel will be sampled.

    alpha: float
        Alpha parameter, must be >= 0.55 and <= 1.0 for stability.

    Returns
    --------
    A tensor of shape `[B,C,H,W]`
    """
    kernel = morphological_kernel_r2(metric_params, kernel_radius, alpha)
    return -morphological_convolution_r2(-input, kernel)


class FractionalDilationR2(torch.nn.Module):
    """
    Modular interface to `lietorch.nn.r2.fractional_dilation_r2_riemannian` where the **metric_params** tensor is part of the module's state.

    Parameters
    ------------
    channels: int
        Number of channels the input tensor is expected to have, i.e. the `C` in `[B,C,H,W]`.

    metric_params: torch.Tensor
        Metric parameters in a tensor of shape `[C,2,2]`. The Riemannian metric tensor is parametrized by `H`:
        $$
            G_{C}(x,y) = H[C]^T H[C],
        $$

    kernel_size: int
        Size of the grid where the morphological kernel will be sampled, i.e. kernel_size both in height and width.

    alpha: float
        Alpha parameter, has to be >= 0.55 and <= 1.0 for stability.
    """

    channels: int
    kernel_size: int
    alpha: float
    metric_params: torch.Tensor

    def __init__(self, channels: int, kernel_size: int, alpha: float):
        super().__init__()

        assert channels > 0, "channels needs to be strictly positive"
        assert kernel_size % 2 == 1 and kernel_size > 0, (
            f"kernel_size ({kernel_size}) must be a positive odd number for well-defined convolutions."
        )
        assert alpha >= 0.55 and alpha <= 1.0, "alpha needs to be >= 0.55 and <= 1.0"

        self.channels = channels
        self.kernel_radius = kernel_size // 2
        self.alpha = alpha
        self.metric_params = torch.nn.Parameter(torch.Tensor(channels, 2, 2))
        self._cached_kernel = None

        self.reset_parameters()

    def reset_parameters(self) -> None:
        torch.nn.init.uniform_(self.metric_params, a=-1.0, b=1.0)

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        return fractional_dilation_r2(
            input, self.metric_params, self.kernel_radius, self.alpha
        )


def fractional_dilation_r2_isotropic(
    input: torch.Tensor, metric_params: torch.Tensor, kernel_radius: int, alpha: float
) -> torch.Tensor:
    """
    Apply left invariant (translation equivariant in this case) dilation to the `input` based on the Finsler functions as given by `finsler_params`. Based on https://gitlab.com/gijsbel/semifield-pde-cnns.

    Parameters
    ------------
    input: torch.Tensor
        Input tensor of shape `[B,C,H,W]`.

    metric_params: torch.Tensor
        Metric parameters in a tensor of shape `[C]`. The Riemannian metric tensor is parametrized by `g`:
        $$
            G_{C}(x,y) = g[C] * Id(2),
        $$

    kernel_radius: int
        Size `[2*kernel_radius+1, 2*kernel_radius+1]` of the grid on which the kernel will be sampled.

    alpha: float
        Alpha parameter, must be >= 0.55 and <= 1.0 for stability.

    Returns
    --------
    A tensor of shape `[B,C,H,W]`
    """
    kernel = morphological_kernel_r2_isotropic(metric_params, kernel_radius, alpha)
    return -morphological_convolution_r2(-input, kernel)


class FractionalDilationR2Isotropic(torch.nn.Module):
    """
    Modular interface to `lietorch.nn.r2.fractional_dilation_r2_isotropic` where the **metric_params** tensor is part of the module's state.

    Parameters
    ------------
    channels: int
        Number of channels the input tensor is expected to have, i.e. the `C` in `[B,C,H,W]`.

    metric_params: torch.Tensor
        Metric parameters in a tensor of shape `[C,2,2]`. The Riemannian metric tensor is parametrized by `H`:
        $$
            G_{C}(x,y) = H[C]^T H[C],
        $$

    kernel_size: int
        Size of the grid where the morphological kernel will be sampled, i.e. kernel_size both in height and width.

    alpha: float
        Alpha parameter, has to be >= 0.55 and <= 1.0 for stability.
    """

    channels: int
    kernel_size: int
    alpha: float
    metric_params: torch.Tensor

    def __init__(self, channels: int, kernel_size: int, alpha: float):
        super().__init__()

        assert channels > 0, "channels needs to be strictly positive"
        assert kernel_size % 2 == 1 and kernel_size > 0, (
            f"kernel_size ({kernel_size}) must be a positive odd number for well-defined convolutions."
        )
        assert alpha >= 0.55 and alpha <= 1.0, "alpha needs to be >= 0.55 and <= 1.0"

        self.channels = channels
        self.kernel_radius = kernel_size // 2
        self.alpha = alpha
        self.metric_params = torch.nn.Parameter(torch.Tensor(channels))
        self._cached_kernel = None

        self.reset_parameters()

    def reset_parameters(self) -> None:
        torch.nn.init.uniform_(self.metric_params, a=-1.0, b=1.0)

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        return fractional_dilation_r2_isotropic(
            input, self.metric_params, self.kernel_radius, self.alpha
        )


def fractional_erosion_r2_finslerian(
    input: torch.Tensor, finsler_params: torch.Tensor, kernel_radius: int, alpha: float
) -> torch.Tensor:
    """
    Apply left invariant (translation equivariant in this case) erosion to the `input` based on the Finsler functions as given by `finsler_params`.

    Parameters
    ------------
    input: torch.Tensor
        Input tensor of shape `[B,C,H,W]`.

    finsler_params: torch.Tensor
        Finsler parameters in a tensor of shape `[C,K]`. The Finsler function is parametrized by the `K` parameters as:
        $$
            F_{C}(x,y) = \\sqrt{x^2+y^2} \\exp{\\left( - \\sum_{k=1}^K \\textrm{finsler_params}[C, k] \\cdot B_k(x,y) \\right)},
        $$
        where B_k is the k-th circular harmonic basis function.

    kernel_radius: int
        Size `[2*kernel_radius+1, 2*kernel_radius+1]` of the grid on which the kernel will be sampled.

    alpha: float
        Alpha parameter, must be >= 0.55 and <= 1.0 for stability.

    Returns
    --------
    A tensor of shape `[B,C,H,W]`
    """
    return torch.ops.lietorch.r2_fractional_erosion(
        input, finsler_params, kernel_radius, alpha
    )


class FractionalErosionR2Finslerian(torch.nn.Module):
    """
    Modular interface to `lietorch.nn.r2.fractional_erosion_r2` where the **finsler_params** tensor is part of the module's state.

    Parameters
    ------------
    channels: int
        Number of channels the input tensor is expected to have, i.e. the `C` in `[B,C,H,W]`.

    finsler_order: int
        Orders of the circular harmonics used to construct the Finsler function, i.e. the kernel will be parametrized by this number of parameters.

    kernel_size: int
        Size of the grid where the morphological kernel will be sampled, i.e. kernel_size both in height and width.

    alpha: float
        Alpha parameter, has to be >= 0.55 and <= 1.0 for stability.
    """

    channels: int
    finsler_order: int
    kernel_size: int
    alpha: float
    finsler_params: torch.Tensor

    def __init__(
        self, channels: int, kernel_size: int, alpha: float, finsler_order: int
    ):
        super().__init__()

        assert channels > 0, "channels needs to be strictly positive"
        assert finsler_order > 0, "finsler_order needs to be strictly positive"
        assert kernel_size % 2 == 1 and kernel_size > 0, (
            f"kernel_size ({kernel_size}) must be a positive odd number for well-defined convolutions."
        )
        assert alpha >= 0.55 and alpha <= 1.0, "alpha needs to be >= 0.55 and <= 1.0"

        self.channels = channels
        self.finsler_order = finsler_order
        self.kernel_radius = kernel_size // 2
        self.alpha = alpha
        self.finsler_params = torch.nn.Parameter(torch.Tensor(channels, finsler_order))
        self._cached_kernel = None

        self.reset_parameters()

    def reset_parameters(self) -> None:
        torch.nn.init.uniform_(self.finsler_params, a=-1.0, b=1.0)

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        return fractional_erosion_r2_finslerian(
            input, self.finsler_params, self.kernel_radius, self.alpha
        )


def fractional_erosion_r2(
    input: torch.Tensor, metric_params: torch.Tensor, kernel_radius: int, alpha: float
) -> torch.Tensor:
    """
    Apply left invariant (translation equivariant in this case) erosion to the `input` based on the Finsler functions as given by `finsler_params`. Based on https://gitlab.com/gijsbel/semifield-pde-cnns.

    Parameters
    ------------
    input: torch.Tensor
        Input tensor of shape `[B,C,H,W]`.

    metric_params: torch.Tensor
        Metric parameters in a tensor of shape `[C,2,2]`. The Riemannian metric tensor is parametrized by `H`:
        $$
            G_{C}(x,y) = H[C]^T H[C],
        $$

    kernel_radius: int
        Size `[2*kernel_radius+1, 2*kernel_radius+1]` of the grid on which the kernel will be sampled.

    alpha: float
        Alpha parameter, must be >= 0.55 and <= 1.0 for stability.

    Returns
    --------
    A tensor of shape `[B,C,H,W]`
    """
    kernel = morphological_kernel_r2(metric_params, kernel_radius, alpha)
    return morphological_convolution_r2(input, kernel)


class FractionalErosionR2(torch.nn.Module):
    """
    Modular interface to `lietorch.nn.r2.fractional_erosion_r2_riemannian` where the **metric_params** tensor is part of the module's state.

    Parameters
    ------------
    channels: int
        Number of channels the input tensor is expected to have, i.e. the `C` in `[B,C,H,W]`.

    metric_params: torch.Tensor
        Metric parameters in a tensor of shape `[C,2,2]`. The Riemannian metric tensor is parametrized by `H`:
        $$
            G_{C}(x,y) = H[C]^T H[C],
        $$

    kernel_size: int
        Size of the grid where the morphological kernel will be sampled, i.e. kernel_size both in height and width.

    alpha: float
        Alpha parameter, has to be >= 0.55 and <= 1.0 for stability.
    """

    channels: int
    kernel_size: int
    alpha: float
    metric_params: torch.Tensor

    def __init__(self, channels: int, kernel_size: int, alpha: float):
        super().__init__()

        assert channels > 0, "channels needs to be strictly positive"
        assert kernel_size % 2 == 1 and kernel_size > 0, (
            f"kernel_size ({kernel_size}) must be a positive odd number for well-defined convolutions."
        )
        assert alpha >= 0.55 and alpha <= 1.0, "alpha needs to be >= 0.55 and <= 1.0"

        self.channels = channels
        self.kernel_radius = kernel_size // 2
        self.alpha = alpha
        self.metric_params = torch.nn.Parameter(torch.Tensor(channels, 2, 2))
        self._cached_kernel = None

        self.reset_parameters()

    def reset_parameters(self) -> None:
        torch.nn.init.uniform_(self.metric_params, a=-1.0, b=1.0)

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        return fractional_erosion_r2(
            input, self.metric_params, self.kernel_radius, self.alpha
        )


def fractional_erosion_r2_isotropic(
    input: torch.Tensor, metric_params: torch.Tensor, kernel_radius: int, alpha: float
) -> torch.Tensor:
    """
    Apply left invariant (translation equivariant in this case) erosion to the `input` based on the Finsler functions as given by `finsler_params`. Based on https://gitlab.com/gijsbel/semifield-pde-cnns.

    Parameters
    ------------
    input: torch.Tensor
        Input tensor of shape `[B,C,H,W]`.

    metric_params: torch.Tensor
        Metric parameters in a tensor of shape `[C]`. The Riemannian metric tensor is parametrized by `g`:
        $$
            G_{C}(x,y) = g[C] * Id(2),
        $$

    kernel_radius: int
        Size `[2*kernel_radius+1, 2*kernel_radius+1]` of the grid on which the kernel will be sampled.

    alpha: float
        Alpha parameter, must be >= 0.55 and <= 1.0 for stability.

    Returns
    --------
    A tensor of shape `[B,C,H,W]`
    """
    kernel = morphological_kernel_r2_isotropic(metric_params, kernel_radius, alpha)
    return morphological_convolution_r2(input, kernel)


class FractionalErosionR2Isotropic(torch.nn.Module):
    """
    Modular interface to `lietorch.nn.r2.fractional_erosion_r2_isotropic` where the **metric_params** tensor is part of the module's state.

    Parameters
    ------------
    channels: int
        Number of channels the input tensor is expected to have, i.e. the `C` in `[B,C,H,W]`.

    metric_params: torch.Tensor
        Metric parameters in a tensor of shape `[C,2,2]`. The Riemannian metric tensor is parametrized by `H`:
        $$
            G_{C}(x,y) = H[C]^T H[C],
        $$

    kernel_size: int
        Size of the grid where the morphological kernel will be sampled, i.e. kernel_size both in height and width.

    alpha: float
        Alpha parameter, has to be >= 0.55 and <= 1.0 for stability.
    """

    channels: int
    kernel_size: int
    alpha: float
    metric_params: torch.Tensor

    def __init__(self, channels: int, kernel_size: int, alpha: float):
        super().__init__()

        assert channels > 0, "channels needs to be strictly positive"
        assert kernel_size % 2 == 1 and kernel_size > 0, (
            f"kernel_size ({kernel_size}) must be a positive odd number for well-defined convolutions."
        )
        assert alpha >= 0.55 and alpha <= 1.0, "alpha needs to be >= 0.55 and <= 1.0"

        self.channels = channels
        self.kernel_radius = kernel_size // 2
        self.alpha = alpha
        self.metric_params = torch.nn.Parameter(torch.Tensor(channels))
        self._cached_kernel = None

        self.reset_parameters()

    def reset_parameters(self) -> None:
        torch.nn.init.uniform_(self.metric_params, a=-1.0, b=1.0)

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        return fractional_erosion_r2_isotropic(
            input, self.metric_params, self.kernel_radius, self.alpha
        )


def diffusion_kernel_r2(
    metric_params: torch.Tensor, kernel_radius: int
) -> torch.Tensor:
    """
    Construct approximate diffusion kernel corresponding to the Riemannian metric given by `metric_params`. Based on https://gitlab.com/gijsbel/semifield-pde-cnns.

    Parameters
    ------------
    metric_params: torch.Tensor
        Metric parameters in a tensor of shape `[C,2,2]`. The Riemannian metric tensor is parametrized by `H`:
        $$
            G_{C}(x,y) = H[C]^T H[C],
        $$

    kernel_radius: int
        Size `[2*kernel_radius+1, 2*kernel_radius+1]` of the grid on which the kernel will be sampled.

    Returns
    ---------
    A Tensor of shape `[... , 2*kernel_radius+1, 2*kernel_radius+1]`.
    """
    norm2 = norm_squared_kernel(metric_params, kernel_radius)
    kernel = torch.exp(-norm2)
    kernel = kernel / (
        kernel.sum(dim=(1, 2))[:, None, None]
        + _epsilon_float32.to(metric_params.device)
    )
    return kernel


def diffusion_r2(
    input: torch.Tensor, metric_params: torch.Tensor, kernel_radius: int
) -> torch.Tensor:
    """
    Apply left invariant (translation equivariant in this case) diffusion to the `input` based on the Riemannian metric given by `metric_params`. Based on https://gitlab.com/gijsbel/semifield-pde-cnns.

    Parameters
    ------------
    input: torch.Tensor
        Input tensor of shape `[B,C,H,W]`.

    metric_params: torch.Tensor
        Metric parameters in a tensor of shape `[C,2,2]`. The Riemannian metric tensor is parametrized by `H`:
        $$
            G_{C}(x,y) = H[C]^T H[C],
        $$

    kernel_radius: int
        Size `[2*kernel_radius+1, 2*kernel_radius+1]` of the grid on which the kernel will be sampled.

    Returns
    --------
    A tensor of shape `[B,C,H,W]`
    """
    c = metric_params.shape[0]
    kernel = diffusion_kernel_r2(metric_params, kernel_radius)
    padded_input = F.pad(input, 4 * (kernel_radius,), mode="reflect")
    return F.conv2d(padded_input, kernel[:, None, ...], groups=c)


class DiffusionR2(torch.nn.Module):
    """
    Modular interface to `lietorch.nn.r2.diffusion_r2` where the **metric_params** tensor is part of the module's state.

    Parameters
    ------------
    channels: int
        Number of channels the input tensor is expected to have, i.e. the `C` in `[B,C,H,W]`.

    metric_params: int
        Metric parameters used to construct the metric.

    kernel_size: int
        Size of the grid where the morphological kernel will be sampled, i.e. kernel_size both in height and width.
    """

    channels: int
    kernel_size: int
    metric_params: torch.Tensor

    def __init__(self, channels: int, kernel_size: int):
        super().__init__()

        assert channels > 0, "channels needs to be strictly positive"

        self.channels = channels
        assert kernel_size % 2 == 1 and kernel_size > 0, (
            f"kernel_size ({kernel_size}) must be a positive odd number for well-defined convolutions."
        )
        self.kernel_radius = kernel_size // 2
        self.metric_params = torch.nn.Parameter(torch.Tensor(channels, 2, 2))
        self._cached_kernel = None

        self.reset_parameters()

    def reset_parameters(self) -> None:
        torch.nn.init.uniform_(self.metric_params, a=-1.0, b=1.0)

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        return diffusion_r2(input, self.metric_params, self.kernel_radius)


def diffusion_kernel_r2_isotropic(
    metric_params: torch.Tensor, kernel_radius: int
) -> torch.Tensor:
    """
    Construct approximate diffusion kernel corresponding to the Riemannian metric given by `metric_params`. Based on https://gitlab.com/gijsbel/semifield-pde-cnns.

    Parameters
    ------------
    metric_params: torch.Tensor
        Metric parameters in a tensor of shape `[C]`. The Riemannian metric tensor is parametrized by `g`:
        $$
            G_{C}(x,y) = g[C] * Id(2),
        $$

    kernel_radius: int
        Size `[2*kernel_radius+1, 2*kernel_radius+1]` of the grid on which the kernel will be sampled.

    Returns
    ---------
    A Tensor of shape `[... , 2*kernel_radius+1, 2*kernel_radius+1]`.
    """
    norm2 = norm_squared_kernel_isotropic(metric_params, kernel_radius)
    kernel = torch.exp(-norm2)
    kernel = kernel / (
        kernel.sum(dim=(1, 2))[:, None, None]
        + _epsilon_float32.to(metric_params.device)
    )
    return kernel


def diffusion_r2_isotropic(
    input: torch.Tensor, metric_params: torch.Tensor, kernel_radius: int
) -> torch.Tensor:
    """
    Apply left invariant (translation equivariant in this case) diffusion to the `input` based on the Riemannian metric given by `metric_params`. Based on https://gitlab.com/gijsbel/semifield-pde-cnns.

    Parameters
    ------------
    input: torch.Tensor
        Input tensor of shape `[B,C,H,W]`.

    metric_params: torch.Tensor
        Metric parameters in a tensor of shape `[C]`. The Riemannian metric tensor is parametrized by `g`:
        $$
            G_{C}(x,y) = g[C] * Id(2),
        $$

    kernel_radius: int
        Size `[2*kernel_radius+1, 2*kernel_radius+1]` of the grid on which the kernel will be sampled.

    Returns
    --------
    A tensor of shape `[B,C,H,W]`
    """
    c = metric_params.shape[0]
    kernel = diffusion_kernel_r2_isotropic(metric_params, kernel_radius)
    padded_input = F.pad(input, 4 * (kernel_radius,), mode="reflect")
    return F.conv2d(padded_input, kernel[:, None, ...], groups=c)


class DiffusionR2Isotropic(torch.nn.Module):
    """
    Modular interface to `lietorch.nn.r2.diffusion_r2_isotropic` where the **metric_params** tensor is part of the module's state.

    Parameters
    ------------
    channels: int
        Number of channels the input tensor is expected to have, i.e. the `C` in `[B,C,H,W]`.

    metric_params: int
        Metric parameters used to construct the metric.

    kernel_size: int
        Size of the grid where the morphological kernel will be sampled, i.e. kernel_size both in height and width.
    """

    channels: int
    kernel_size: int
    metric_params: torch.Tensor

    def __init__(self, channels: int, kernel_size: int):
        super().__init__()

        assert channels > 0, "channels needs to be strictly positive"

        self.channels = channels
        assert kernel_size % 2 == 1 and kernel_size > 0, (
            f"kernel_size ({kernel_size}) must be a positive odd number for well-defined convolutions."
        )
        self.kernel_radius = kernel_size // 2
        self.metric_params = torch.nn.Parameter(torch.Tensor(channels))
        self._cached_kernel = None

        self.reset_parameters()

    def reset_parameters(self) -> None:
        torch.nn.init.uniform_(self.metric_params, a=-1.0, b=1.0)

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        return diffusion_r2_isotropic(input, self.metric_params, self.kernel_radius)


def linear_r2(input: torch.Tensor, weight: torch.Tensor) -> torch.Tensor:
    """
    Linear combinations of R2 tensors.

    Parameters
    ------------
    input: torch.Tensor
    Tensor of shape `[B,Cin,H,W]`.

    weight: torch.Tensor
    Tensor of shape `[Cin, Cout]`.

    Returns
    --------
    Tensor of shape `[B,Cout,H,W]`.
    """
    return (weight[..., None, None] * input[..., None, :, :]).sum(1)


class LinearR2(torch.nn.Module):
    """
    Modular interface to `lietorch.nn.r2.linear_r2` where the **weight** tensor is part of the module's state.

    Parameters
    -----------
    in_channels: int
    Number of input channels.

    out_channels: int
    Number of output channels.
    """

    __constants__ = ["in_channels", "out_channels"]
    in_channels: int
    out_channels: int
    weight: torch.Tensor

    def __init__(self, in_channels: int, out_channels: int) -> None:
        super().__init__()

        self.in_channels = in_channels
        self.out_channels = out_channels
        self.weight = torch.nn.Parameter(torch.Tensor(in_channels, out_channels))

        self.reset_parameters()

    def reset_parameters(self) -> None:
        torch.nn.init.kaiming_uniform_(self.weight, a=sqrt(5))

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        return linear_r2(input, self.weight)


def convection_r2(input: torch.Tensor, c: torch.Tensor) -> torch.Tensor:
    """
    Translation equivariant convection of R2 tensors.

    Parameters
    ------------
    input: torch.Tensor
    Tensor of shape `[B,C,H,W]`.

    c: torch.Tensor
    Tensor of shape `[C,2]`.

    Returns
    --------
    Tensor of shape `[B,C,H,W]`.
    """
    B, C, H, W = input.shape
    device = input.device

    c_scaled = torch.zeros_like(c)
    c_scaled[..., 0] = 2.0 * c[..., 0] / (H - 1.0)
    c_scaled[..., 1] = 2.0 * c[..., 1] / (W - 1.0)

    y_grid, x_grid = torch.meshgrid(
        torch.linspace(-1, 1, H, device=device),
        torch.linspace(-1, 1, W, device=device),
        indexing="ij",
    )
    g_grid = torch.stack((y_grid, x_grid), dim=-1)  # [H, W, 2]
    shifted_g_grid = g_grid - c_scaled[..., None, None, :]  # [C, H, W, 2]

    return F.grid_sample(
        input.permute(1, 0, 2, 3), shifted_g_grid.flip(dims=(-1,)), align_corners=True
    ).permute(1, 0, 2, 3)


class ConvectionR2(torch.nn.Module):
    """
    Modular interface to `lietorch.nn.r2.convection_r2` where the **c** tensor is part of the module's state.

    Parameters
    -----------
    channels: int
    Number of input channels.
    """

    __constants__ = ["channels"]
    channels: int
    c: torch.Tensor

    def __init__(self, channels: int) -> None:
        super().__init__()

        self.channels = channels
        self.c = torch.nn.Parameter(torch.Tensor(channels, 2))

        self.reset_parameters()

    def reset_parameters(self) -> None:
        torch.nn.init.kaiming_uniform_(self.c, a=sqrt(5))

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        return convection_r2(input, self.c)


def switch_diffusion_shock_r2(
    input: torch.Tensor,
    labda: torch.Tensor,
    metric_params: torch.Tensor,
    kernel_radius: int,
) -> torch.Tensor:
    """
    Construct approximate

    Parameters
    ------------
    input: torch.Tensor
        Input tensor of shape `[B,C,H,W]`.

    labda: torch.Tensor
        Switch 'strength' parameters in a tensor of shape `[C]`. Use Dutch spelling to avoid Python keyword 🙃.

    metric_params: torch.Tensor
        Metric parameters in a tensor of shape `[C,2,2]`. The Riemannian metric tensor is parametrized by `H`:
        $$
            G_{C}(x,y) = H[C]^T H[C],
        $$

    kernel_radius: int
        Size `[2*kernel_radius+1, 2*kernel_radius+1]` of the grid on which the kernel will be sampled.

    Returns
    ---------
    A Tensor of shape `[B,C,H,W]`.
    """
    smoothed = diffusion_r2(input, metric_params, kernel_radius)
    dx, dy = first_order_derivatives(smoothed)

    norm2 = dx**2 + dy**2

    return 1.0 / (
        1.0 + norm2 / (labda[..., None, None] ** 2 + _epsilon_float32.to(labda.device))
    )


class DSSwitchR2(torch.nn.Module):
    """
    Modular interface to `lietorch.nn.r2.switch_diffusion_shock_r2` where the **labda** and **metric_params** tensors are part of the module's state.

    Parameters
    ------------
    channels: int
        Number of channels the input tensor is expected to have, i.e. the `C` in `[B,C,H,W]`.

    labda: torch.Tensor
        Switch 'strength' parameters in a tensor of shape `[C]`. Use Dutch spelling to avoid Python keyword 🙃.

    metric_params: int
        Metric parameters used to construct the metric.

    kernel_radius: int
        Size of the grid where the morphological kernel will be sampled, i.e. 2*kernel_radius+1 both in height and width.
    """

    channels: int
    kernel_radius: int
    labda: torch.Tensor
    metric_params: torch.Tensor

    def __init__(self, channels: int, kernel_radius: int):
        super().__init__()

        assert channels > 0, "channels needs to be strictly positive"
        assert kernel_radius >= 0, "kernel_radius needs to be positive"

        self.channels = channels
        self.kernel_radius = kernel_radius
        self.labda = torch.nn.Parameter(torch.Tensor(channels))
        self.metric_params = torch.nn.Parameter(torch.Tensor(channels, 2, 2))
        self._cached_kernel_x = None
        self._cached_kernel_y = None

        self.reset_parameters()

    def reset_parameters(self) -> None:
        torch.nn.init.uniform_(self.labda, a=-1.0, b=1.0)
        torch.nn.init.uniform_(self.metric_params, a=-1.0, b=1.0)

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        return switch_diffusion_shock_r2(
            input, self.labda, self.metric_params, self.kernel_radius
        )


def switch_diffusion_shock_r2_isotropic(
    input: torch.Tensor,
    labda: torch.Tensor,
    metric_params: torch.Tensor,
    kernel_radius: int,
) -> torch.Tensor:
    """
    Construct approximate

    Parameters
    ------------
    input: torch.Tensor
        Input tensor of shape `[B,C,H,W]`.

    labda: torch.Tensor
        Switch 'strength' parameters in a tensor of shape `[C]`. Use Dutch spelling to avoid Python keyword 🙃.

    metric_params: torch.Tensor
        Metric parameters in a tensor of shape `[C,2,2]`. The Riemannian metric tensor is parametrized by `H`:
        $$
            G_{C}(x,y) = H[C]^T H[C],
        $$

    kernel_radius: int
        Size `[2*kernel_radius+1, 2*kernel_radius+1]` of the grid on which the kernel will be sampled.

    Returns
    ---------
    A Tensor of shape `[B,C,H,W]`.
    """
    smoothed = diffusion_r2_isotropic(input, metric_params, kernel_radius)
    dx, dy = first_order_derivatives(smoothed)

    norm2 = dx**2 + dy**2

    return 1.0 / (
        1.0 + norm2 / (labda[..., None, None] ** 2 + _epsilon_float32.to(labda.device))
    )


class DSSwitchR2Isotropic(torch.nn.Module):
    """
    Modular interface to `lietorch.nn.r2.switch_diffusion_shock_r2_isotropic` where the **labda** and **metric_params** tensors are part of the module's state.

    Parameters
    ------------
    channels: int
        Number of channels the input tensor is expected to have, i.e. the `C` in `[B,C,H,W]`.

    labda: torch.Tensor
        Switch 'strength' parameters in a tensor of shape `[C]`. Use Dutch spelling to avoid Python keyword 🙃.

    metric_params: int
        Metric parameters used to construct the metric.

    kernel_radius: int
        Size of the grid where the morphological kernel will be sampled, i.e. 2*kernel_radius+1 both in height and width.
    """

    channels: int
    kernel_radius: int
    labda: torch.Tensor
    metric_params: torch.Tensor

    def __init__(self, channels: int, kernel_radius: int):
        super().__init__()

        assert channels > 0, "channels needs to be strictly positive"
        assert kernel_radius >= 0, "kernel_radius needs to be positive"

        self.channels = channels
        self.kernel_radius = kernel_radius
        self.labda = torch.nn.Parameter(torch.Tensor(channels))
        self.metric_params = torch.nn.Parameter(torch.Tensor(channels))
        self._cached_kernel_x = None
        self._cached_kernel_y = None

        self.reset_parameters()

    def reset_parameters(self) -> None:
        torch.nn.init.uniform_(self.labda, a=-1.0, b=1.0)
        torch.nn.init.uniform_(self.metric_params, a=-1.0, b=1.0)

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        return switch_diffusion_shock_r2_isotropic(
            input, self.labda, self.metric_params, self.kernel_radius
        )


def switch_morphology_r2(
    input: torch.Tensor,
    epsilon: torch.Tensor,
    metric_params: torch.Tensor,
    kernel_radius: int,
) -> torch.Tensor:
    """
    Construct approximate

    Parameters
    ------------
    input: torch.Tensor
        Input tensor of shape `[B,C,H,W]`.

    epsilon: torch.Tensor
        Switch 'strength' parameters in a tensor of shape `[C]`.

    metric_params: torch.Tensor
        Metric parameters in a tensor of shape `[C,2,2]`. The Riemannian metric tensor is parametrized by `H`:
        $$
            G_{C}(x,y) = H[C]^T H[C],
        $$

    kernel_radius: int
        Size `[2*kernel_radius+1, 2*kernel_radius+1]` of the grid on which the kernel will be sampled.

    Returns
    ---------
    A Tensor of shape `[... , 2*kernel_radius+1, 2*kernel_radius+1]`.
    """
    smoothed = diffusion_r2(input, metric_params, kernel_radius)
    ddx, ddy = second_order_derivatives(smoothed)

    convexity = ddx + ddy

    return (2.0 / torch.pi) * torch.atan2(
        convexity, epsilon[..., None, None] ** 2 + _epsilon_float32.to(epsilon.device)
    )


class MorphologicalSwitchR2(torch.nn.Module):
    """
    Modular interface to `lietorch.nn.r2.switch_morphology_r2` where the **metric_params** tensor is part of the module's state.

    Parameters
    ------------
    channels: int
        Number of channels the input tensor is expected to have, i.e. the `C` in `[B,C,H,W]`.

    epsilon: torch.Tensor
        Switch 'strength' parameters in a tensor of shape `[C]`.

    metric_params: int
        Metric parameters used to construct the metric.

    kernel_radius: int
        Size of the grid where the morphological kernel will be sampled, i.e. 2*kernel_radius+1 both in height and width.
    """

    channels: int
    kernel_radius: int
    epsilon: torch.Tensor
    metric_params: torch.Tensor

    def __init__(self, channels: int, kernel_radius: int):
        super().__init__()

        assert channels > 0, "channels needs to be strictly positive"
        assert kernel_radius >= 0, "kernel_radius needs to be positive"

        self.channels = channels
        self.kernel_radius = kernel_radius
        self.epsilon = torch.nn.Parameter(torch.Tensor(channels))
        self.metric_params = torch.nn.Parameter(torch.Tensor(channels, 2, 2))
        self._cached_kernel = None

        self.reset_parameters()

    def reset_parameters(self) -> None:
        torch.nn.init.uniform_(self.epsilon, a=-1.0, b=1.0)
        torch.nn.init.uniform_(self.metric_params, a=-1.0, b=1.0)

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        return switch_morphology_r2(
            input, self.epsilon, self.metric_params, self.kernel_radius
        )


def switch_morphology_r2_isotropic(
    input: torch.Tensor,
    epsilon: torch.Tensor,
    metric_params: torch.Tensor,
    kernel_radius: int,
) -> torch.Tensor:
    """
    Construct approximate

    Parameters
    ------------
    input: torch.Tensor
        Input tensor of shape `[B,C,H,W]`.

    epsilon: torch.Tensor
        Switch 'strength' parameters in a tensor of shape `[C]`.

    metric_params: torch.Tensor
        Metric parameters in a tensor of shape `[C,2,2]`. The Riemannian metric tensor is parametrized by `H`:
        $$
            G_{C}(x,y) = H[C]^T H[C],
        $$

    kernel_radius: int
        Size `[2*kernel_radius+1, 2*kernel_radius+1]` of the grid on which the kernel will be sampled.

    Returns
    ---------
    A Tensor of shape `[... , 2*kernel_radius+1, 2*kernel_radius+1]`.
    """
    smoothed = diffusion_r2_isotropic(input, metric_params, kernel_radius)
    ddx, ddy = second_order_derivatives(smoothed)

    convexity = ddx + ddy

    return (2.0 / torch.pi) * torch.atan2(
        convexity, epsilon[..., None, None] ** 2 + _epsilon_float32.to(epsilon.device)
    )


class MorphologicalSwitchR2Isotropic(torch.nn.Module):
    """
    Modular interface to `lietorch.nn.r2.switch_morphology_r2_isotropic` where the **metric_params** tensor is part of the module's state.

    Parameters
    ------------
    channels: int
        Number of channels the input tensor is expected to have, i.e. the `C` in `[B,C,H,W]`.

    epsilon: torch.Tensor
        Switch 'strength' parameters in a tensor of shape `[C]`.

    metric_params: int
        Metric parameters used to construct the metric.

    kernel_radius: int
        Size of the grid where the morphological kernel will be sampled, i.e. 2*kernel_radius+1 both in height and width.
    """

    channels: int
    kernel_radius: int
    epsilon: torch.Tensor
    metric_params: torch.Tensor

    def __init__(self, channels: int, kernel_radius: int):
        super().__init__()

        assert channels > 0, "channels needs to be strictly positive"
        assert kernel_radius >= 0, "kernel_radius needs to be positive"

        self.channels = channels
        self.kernel_radius = kernel_radius
        self.epsilon = torch.nn.Parameter(torch.Tensor(channels))
        self.metric_params = torch.nn.Parameter(torch.Tensor(channels))
        self._cached_kernel = None

        self.reset_parameters()

    def reset_parameters(self) -> None:
        torch.nn.init.uniform_(self.epsilon, a=-1.0, b=1.0)
        torch.nn.init.uniform_(self.metric_params, a=-1.0, b=1.0)

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        return switch_morphology_r2_isotropic(
            input, self.epsilon, self.metric_params, self.kernel_radius
        )


class CDEPdeLayerR2Finslerian(torch.nn.Module):
    """
    Full convection/dilation/erosion layer that includes batch normalization and linear combinations.
    Solves the PDE:
    $$
        u_t = -\\mathbf{c}u + \\left\\| \\nabla u \\right\\|^{2\\alpha}_{\\mathcal{G}_1} - \\left\\| \\nabla u \\right\\|^{2\\alpha}_{\\mathcal{G}_2},
    $$
    where the convection vector \\(\\mathbf{c}\\) and the Riemannian metrics \\( \\mathcal{G}_1 \\) and \\( \\mathcal{G}_2 \\) are the trainable parameters. Subsequently linear combinations are taken and batch normalization (`torch.nn.BatchNorm2d`) is applied.
    """

    __constants__ = [
        "in_channels",
        "out_channels",
        "kernel_size",
        "iterations",
        "alpha",
        "bn_momentum",
    ]

    in_channels: int
    """
        Number of input channels.
    """

    out_channels: int
    """
        Number of output channels.
    """

    finsler_order: int
    """
        Orders of the circular harmonics used to construct the Finsler function for the dilation and erosion kernels, i.e. the kernel will be parametrized by this number of parameters.
    """

    kernel_size: int
    """
        Size `[kH,kW]` of the grid on which the approximative kernel that solves the dilation/erosion will be sampled. Larger grid sizes increase computational load but also allow more dilation and erosion to take place.
    """

    iterations: int
    """
        How many times the split operators are applied, defaults to 1. Higher iterations improve how well the output approximates the PDE solution but increases computational load.
    """

    alpha: float
    """
        Alpha parameter to determine the dilation and erosion's fractionality. Must be at least *0.55* and at most *1.0*, defaults to the happy compromise of *0.65*.
    """

    convection: ConvectionR2
    dilation: FractionalDilationR2Finslerian
    erosion: FractionalErosionR2Finslerian
    linear: LinearR2
    batch_normalization: torch.nn.BatchNorm2d

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int,
        iterations: int = 1,
        alpha: float = 0.65,
        finsler_order: int = 5,
    ) -> None:
        super().__init__()

        self.in_channels = in_channels
        self.out_channels = out_channels
        self.finsler_order = finsler_order
        self.kernel_size = kernel_size
        self.iterations = iterations
        self.alpha = alpha

        self.convection = ConvectionR2(in_channels)
        self.dilation = FractionalDilationR2Finslerian(
            in_channels, kernel_size, alpha, finsler_order
        )
        self.erosion = FractionalErosionR2Finslerian(
            in_channels, kernel_size, alpha, finsler_order
        )
        self.linear = LinearR2(in_channels, out_channels)
        self.batch_normalization = torch.nn.BatchNorm2d(
            out_channels, track_running_stats=True
        )

        self.reset_parameters()

    def reset_parameters(self) -> None:
        self.convection.reset_parameters()
        self.dilation.reset_parameters()
        self.erosion.reset_parameters()
        self.linear.reset_parameters()
        self.batch_normalization.reset_parameters()

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        x = input
        for i in range(self.iterations):
            x = self.erosion(self.dilation(self.convection(x)))
        return self.batch_normalization(self.linear(x))


class DSPdeLayerR2Finslerian(torch.nn.Module):
    """
    Diffusion-shock layer that includes batch normalization and linear combinations.
    Solves the PDE:
    $$
        u_t = g_\\lambda(\\|\\nabla u\\|) \\Delta u - (1 - g_\\lambda(\\|\\nabla u\\|)) S_\\epsilon(\\Delta_\\perp u) \\|\\nabla u\\|^\\alpha,
    $$
    where \\(g_\\lambda(x) = 1 / (1 + \\lambda x^2\\) and \\(S_\\epsilon(x) = (2/\\pi) atan2(x, \\epsilon)\\). The trainable parameters are \\(\\lambda\\), \\(\\epsilon\\), as well as the Riemannian metrics used to define the norms, gradients, and Laplacians.
    Subsequently linear combinations are taken and batch normalization (`torch.nn.BatchNorm2d`) is applied.
    """

    __constants__ = [
        "in_channels",
        "out_channels",
        "kernel_size",
        "iterations",
        "bn_momentum",
    ]

    in_channels: int
    """
        Number of input channels.
    """

    out_channels: int
    """
        Number of output channels.
    """

    finsler_order: int
    """
        Orders of the circular harmonics used to construct the Finsler function for the dilation and erosion kernels, i.e. the kernel will be parametrized by this number of parameters.
    """

    kernel_size: int
    """
        Size `[kH,kW]` of the grid on which the approximative kernel that solves the dilation/erosion will be sampled. Larger grid sizes increase computational load but also allow more dilation and erosion to take place.
    """

    iterations: int
    """
        How many times the split operators are applied, defaults to 1. Higher iterations improve how well the output approximates the PDE solution but increases computational load.
    """

    alpha: float
    """
        Alpha parameter to determine the dilation and erosion's fractionality. Must be at least *0.55* and at most *1.0*, defaults to the happy compromise of *0.65*.
    """

    diffusion: DiffusionR2
    dilation: FractionalDilationR2Finslerian
    erosion: FractionalErosionR2Finslerian
    switchds: DSSwitchR2
    switchmorphology: MorphologicalSwitchR2
    linear: LinearR2
    batch_normalization: torch.nn.BatchNorm2d

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int,
        iterations: int = 1,
        alpha: float = 0.65,
        finsler_order: int = 5,
    ) -> None:
        super().__init__()

        self.in_channels = in_channels
        self.out_channels = out_channels
        self.kernel_size = kernel_size
        self.iterations = iterations

        self.diffusion = DiffusionR2(in_channels, kernel_size)
        self.dilation = FractionalDilationR2Finslerian(
            in_channels, kernel_size, alpha, finsler_order
        )
        self.erosion = FractionalErosionR2Finslerian(
            in_channels, kernel_size, alpha, finsler_order
        )
        self.switchds = DSSwitchR2(in_channels, kernel_size)
        self.switchmorphology = MorphologicalSwitchR2(in_channels, kernel_size)
        self.linear = LinearR2(in_channels, out_channels)
        self.batch_normalization = torch.nn.BatchNorm2d(
            out_channels, track_running_stats=True
        )

        self.reset_parameters()

    def reset_parameters(self) -> None:
        self.diffusion.reset_parameters()
        self.dilation.reset_parameters()
        self.erosion.reset_parameters()
        self.switchds.reset_parameters()
        self.switchmorphology.reset_parameters()
        self.linear.reset_parameters()
        self.batch_normalization.reset_parameters()

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        x = input
        for i in range(self.iterations):
            diffused = self.diffusion(x)
            dilated = self.dilation(x)
            eroded = self.erosion(x)
            switchds = self.switchds(x)
            switchmorphology = self.switchmorphology(x)

            x = (
                # Diffusion
                switchds * diffused
                -
                # Shock
                (1 - switchds)
                * (
                    switchmorphology.abs()
                    * (
                        # Erosion
                        eroded * (switchmorphology > 0.0)
                        +
                        # Dilation
                        dilated * (switchmorphology < 0.0)
                        # When there is little diffusion or shock, return original
                        # feature map.
                    )
                    + (1.0 - switchmorphology.abs()) * x
                )
            )
        return self.batch_normalization(self.linear(x))


class CDSPdeLayerR2Finslerian(torch.nn.Module):
    """
    Diffusion-shock layer that includes batch normalization and linear combinations.
    Solves the PDE:
    $$
        u_t = -\\( \\mathbf{c} \\) u + g_\\lambda(\\|\\nabla u\\|) \\Delta u - (1 - g_\\lambda(\\|\\nabla u\\|)) S_\\epsilon(\\Delta_\\perp u) \\|\\nabla u\\|^\\alpha,
    $$
    where \\(g_\\lambda(x) = 1 / (1 + \\lambda x^2\\) and \\(S_\\epsilon(x) = (2/\\pi) atan2(x, \\epsilon)\\). The trainable parameters are \\(\\lambda\\), \\(\\epsilon\\), the convection vector \\( \\mathbf{c} \\), as well as the Riemannian metrics used to define the norms, gradients, and Laplacians.
    Subsequently linear combinations are taken and batch normalization (`torch.nn.BatchNorm2d`) is applied.
    """

    __constants__ = [
        "in_channels",
        "out_channels",
        "kernel_size",
        "iterations",
        "bn_momentum",
    ]

    in_channels: int
    """
        Number of input channels.
    """

    out_channels: int
    """
        Number of output channels.
    """

    finsler_order: int
    """
        Orders of the circular harmonics used to construct the Finsler function for the dilation and erosion kernels, i.e. the kernel will be parametrized by this number of parameters.
    """

    kernel_size: int
    """
        Size `[kH,kW]` of the grid on which the approximative kernel that solves the dilation/erosion will be sampled. Larger grid sizes increase computational load but also allow more dilation and erosion to take place.
    """

    iterations: int
    """
        How many times the split operators are applied, defaults to 1. Higher iterations improve how well the output approximates the PDE solution but increases computational load.
    """

    alpha: float
    """
        Alpha parameter to determine the dilation and erosion's fractionality. Must be at least *0.55* and at most *1.0*, defaults to the happy compromise of *0.65*.
    """

    convection: ConvectionR2
    diffusion: DiffusionR2
    dilation: FractionalDilationR2Finslerian
    erosion: FractionalErosionR2Finslerian
    switchds: DSSwitchR2
    switchmorphology: MorphologicalSwitchR2
    linear: LinearR2
    batch_normalization: torch.nn.BatchNorm2d

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int,
        iterations: int = 1,
        alpha: float = 0.65,
        finsler_order: int = 5,
    ) -> None:
        super().__init__()

        self.in_channels = in_channels
        self.out_channels = out_channels
        self.kernel_size = kernel_size
        self.iterations = iterations

        self.convection = ConvectionR2(in_channels)
        self.diffusion = DiffusionR2(in_channels, kernel_size)
        self.dilation = FractionalDilationR2Finslerian(
            in_channels, kernel_size, alpha, finsler_order
        )
        self.erosion = FractionalErosionR2Finslerian(
            in_channels, kernel_size, alpha, finsler_order
        )
        self.switchds = DSSwitchR2(in_channels, kernel_size)
        self.switchmorphology = MorphologicalSwitchR2(in_channels, kernel_size)
        self.linear = LinearR2(in_channels, out_channels)
        self.batch_normalization = torch.nn.BatchNorm2d(
            out_channels, track_running_stats=True
        )

        self.reset_parameters()

    def reset_parameters(self) -> None:
        self.diffusion.reset_parameters()
        self.dilation.reset_parameters()
        self.erosion.reset_parameters()
        self.switchds.reset_parameters()
        self.switchmorphology.reset_parameters()
        self.linear.reset_parameters()
        self.batch_normalization.reset_parameters()

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        x = input
        for i in range(self.iterations):
            x = self.convection(x)
            diffused = self.diffusion(x)
            dilated = self.dilation(x)
            eroded = self.erosion(x)
            switchds = self.switchds(x)
            switchmorphology = self.switchmorphology(x)

            x = (
                # Diffusion
                switchds * diffused
                -
                # Shock
                (1 - switchds)
                * (
                    switchmorphology.abs()
                    * (
                        # Erosion
                        eroded * (switchmorphology > 0.0)
                        +
                        # Dilation
                        dilated * (switchmorphology < 0.0)
                        # When there is little diffusion or shock, return original
                        # feature map.
                    )
                    + (1.0 - switchmorphology.abs()) * x
                )
            )
        return self.batch_normalization(self.linear(x))


class DEPdeLayerR2Finslerian(torch.nn.Module):
    """
    Full dilation/erosion layer that includes batch normalization and linear combinations.
    Solves the PDE:
    $$
        u_t =  + \\left\\| \\nabla u \\right\\|^{2\\alpha}_{\\mathcal{G}_1} - \\left\\| \\nabla u \\right\\|^{2\\alpha}_{\\mathcal{G}_2},
    $$
    where the Riemannian metrics \\( \\mathcal{G}_1 \\) and \\( \\mathcal{G}_2 \\) are the trainable parameters. Subsequently linear combinations are taken and batch normalization (`torch.nn.BatchNorm2d`) is applied.
    """

    __constants__ = [
        "in_channels",
        "out_channels",
        "kernel_size",
        "iterations",
        "alpha",
        "bn_momentum",
    ]

    in_channels: int
    """
        Number of input channels.
    """

    out_channels: int
    """
        Number of output channels.
    """

    finsler_order: int
    """
        Orders of the circular harmonics used to construct the Finsler function for the dilation and erosion kernels, i.e. the kernel will be parametrized by this number of parameters.
    """

    kernel_size: int
    """
        Size `[kH,kW]` of the grid on which the approximative kernel that solves the dilation/erosion will be sampled. Larger grid sizes increase computational load but also allow more dilation and erosion to take place.
    """

    iterations: int
    """
        How many times the split operators are applied, defaults to 1. Higher iterations improve how well the output approximates the PDE solution but increases computational load.
    """

    alpha: float
    """
        Alpha parameter to determine the dilation and erosion's fractionality. Must be at least *0.55* and at most *1.0*, defaults to the happy compromise of *0.65*.
    """

    dilation: FractionalDilationR2Finslerian
    erosion: FractionalErosionR2Finslerian
    linear: LinearR2
    batch_normalization: torch.nn.BatchNorm2d

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int,
        iterations: int = 1,
        alpha: float = 0.65,
        finsler_order: int = 5,
    ) -> None:
        super().__init__()

        self.in_channels = in_channels
        self.out_channels = out_channels
        self.finsler_order = finsler_order
        self.kernel_size = kernel_size
        self.iterations = iterations
        self.alpha = alpha

        self.dilation = FractionalDilationR2Finslerian(
            in_channels, kernel_size, alpha, finsler_order
        )
        self.erosion = FractionalErosionR2Finslerian(
            in_channels, kernel_size, alpha, finsler_order
        )
        self.linear = LinearR2(in_channels, out_channels)
        self.batch_normalization = torch.nn.BatchNorm2d(
            out_channels, track_running_stats=True
        )

        self.reset_parameters()

    def reset_parameters(self) -> None:
        self.dilation.reset_parameters()
        self.erosion.reset_parameters()
        self.linear.reset_parameters()
        self.batch_normalization.reset_parameters()

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        x = input
        for i in range(self.iterations):
            x = self.erosion(self.dilation(x))

        return self.batch_normalization(self.linear(x))


class DDEPdeLayerR2Finslerian(torch.nn.Module):
    """
    Full diffusion/dilation/erosion layer that includes batch normalization and linear combinations.
    Solves the PDE:
    $$
        u_t = \\Delta_{\\matchal{G}_1} u + \\left\\| \\nabla u \\right\\|^{2\\alpha}_{\\mathcal{G}_2} - \\left\\| \\nabla u \\right\\|^{2\\alpha}_{\\mathcal{G}_3},
    $$
    where the Riemannian metrics \\( \\mathcal{G}_1 \\), \\( \\mathcal{G}_2 \\), and \\( \\mathcal{G}_3 \\) are the trainable parameters. Subsequently linear combinations are taken and batch normalization (`torch.nn.BatchNorm2d`) is applied.
    """

    __constants__ = [
        "in_channels",
        "out_channels",
        "kernel_size",
        "iterations",
        "alpha",
        "bn_momentum",
    ]

    in_channels: int
    """
        Number of input channels.
    """

    out_channels: int
    """
        Number of output channels.
    """

    finsler_order: int
    """
        Orders of the circular harmonics used to construct the Finsler function for the dilation and erosion kernels, i.e. the kernel will be parametrized by this number of parameters.
    """

    kernel_size: int
    """
        Size `[kH,kW]` of the grid on which the approximative kernel that solves the dilation/erosion will be sampled. Larger grid sizes increase computational load but also allow more dilation and erosion to take place.
    """

    iterations: int
    """
        How many times the split operators are applied, defaults to 1. Higher iterations improve how well the output approximates the PDE solution but increases computational load.
    """

    alpha: float
    """
        Alpha parameter to determine the dilation and erosion's fractionality. Must be at least *0.55* and at most *1.0*, defaults to the happy compromise of *0.65*.
    """

    diffusion: DiffusionR2
    dilation: FractionalDilationR2Finslerian
    erosion: FractionalErosionR2Finslerian
    linear: LinearR2
    batch_normalization: torch.nn.BatchNorm2d

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int,
        iterations: int = 1,
        alpha: float = 0.65,
        finsler_order: int = 5,
    ) -> None:
        super().__init__()

        self.in_channels = in_channels
        self.out_channels = out_channels
        self.finsler_order = finsler_order
        self.kernel_size = kernel_size
        self.iterations = iterations
        self.alpha = alpha

        self.diffusion = DiffusionR2(in_channels, kernel_size)
        self.dilation = FractionalDilationR2Finslerian(
            in_channels, kernel_size, alpha, finsler_order
        )
        self.erosion = FractionalErosionR2Finslerian(
            in_channels, kernel_size, alpha, finsler_order
        )
        self.linear = LinearR2(in_channels, out_channels)
        self.batch_normalization = torch.nn.BatchNorm2d(
            out_channels, track_running_stats=True
        )

        self.reset_parameters()

    def reset_parameters(self) -> None:
        self.diffusion.reset_parameters()
        self.dilation.reset_parameters()
        self.erosion.reset_parameters()
        self.linear.reset_parameters()
        self.batch_normalization.reset_parameters()

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        x = input
        for i in range(self.iterations):
            x = self.erosion(self.dilation(self.diffusion(x)))

        return self.batch_normalization(self.linear(x))


class CDDEPdeLayerR2Finslerian(torch.nn.Module):
    """
    Full convection/diffusion/dilation/erosion layer that includes batch normalization and linear combinations.
    Solves the PDE:
    $$
        u_t = -\\mathbf{c} u + \\Delta_{\\matchal{G}_1} u + \\left\\| \\nabla u \\right\\|^{2\\alpha}_{\\mathcal{G}_2} - \\left\\| \\nabla u \\right\\|^{2\\alpha}_{\\mathcal{G}_3},
    $$
    wheret the convection vector \\( \\mathbf{c} \\) and the Riemannian metrics \\( \\mathcal{G}_1 \\), \\( \\mathcal{G}_2 \\), and \\( \\mathcal{G}_3 \\) are the trainable parameters. Subsequently linear combinations are taken and batch normalization (`torch.nn.BatchNorm2d`) is applied.
    """

    __constants__ = [
        "in_channels",
        "out_channels",
        "kernel_size",
        "iterations",
        "alpha",
        "bn_momentum",
    ]

    in_channels: int
    """
        Number of input channels.
    """

    out_channels: int
    """
        Number of output channels.
    """

    finsler_order: int
    """
        Orders of the circular harmonics used to construct the Finsler function for the dilation and erosion kernels, i.e. the kernel will be parametrized by this number of parameters.
    """

    kernel_size: int
    """
        Size `[kH,kW]` of the grid on which the approximative kernel that solves the dilation/erosion will be sampled. Larger grid sizes increase computational load but also allow more dilation and erosion to take place.
    """

    iterations: int
    """
        How many times the split operators are applied, defaults to 1. Higher iterations improve how well the output approximates the PDE solution but increases computational load.
    """

    alpha: float
    """
        Alpha parameter to determine the dilation and erosion's fractionality. Must be at least *0.55* and at most *1.0*, defaults to the happy compromise of *0.65*.
    """

    convection: ConvectionR2
    diffusion: DiffusionR2
    dilation: FractionalDilationR2Finslerian
    erosion: FractionalErosionR2Finslerian
    linear: LinearR2
    batch_normalization: torch.nn.BatchNorm2d

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int,
        iterations: int = 1,
        alpha: float = 0.65,
        finsler_order: int = 5,
    ) -> None:
        super().__init__()

        self.in_channels = in_channels
        self.out_channels = out_channels
        self.finsler_order = finsler_order
        self.kernel_size = kernel_size
        self.iterations = iterations
        self.alpha = alpha

        self.convection = ConvectionR2(in_channels)
        self.diffusion = DiffusionR2(in_channels, kernel_size)
        self.dilation = FractionalDilationR2Finslerian(
            in_channels, kernel_size, alpha, finsler_order
        )
        self.erosion = FractionalErosionR2Finslerian(
            in_channels, kernel_size, alpha, finsler_order
        )
        self.linear = LinearR2(in_channels, out_channels)
        self.batch_normalization = torch.nn.BatchNorm2d(
            out_channels, track_running_stats=True
        )

        self.reset_parameters()

    def reset_parameters(self) -> None:
        self.convection.reset_parameters()
        self.diffusion.reset_parameters()
        self.dilation.reset_parameters()
        self.erosion.reset_parameters()
        self.linear.reset_parameters()
        self.batch_normalization.reset_parameters()

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        x = input
        for i in range(self.iterations):
            x = self.erosion(self.dilation(self.diffusion(self.convection(x))))

        return self.batch_normalization(self.linear(x))


class DSPdeLayerR2(torch.nn.Module):
    """
    Diffusion-shock layer that includes batch normalization and linear combinations.
    Solves the PDE:
    $$
        u_t = g_\\lambda(\\|\\nabla u\\|) \\Delta u - (1 - g_\\lambda(\\|\\nabla u\\|)) S_\\epsilon(\\Delta_\\perp u) \\|\\nabla u\\|^\\alpha,
    $$
    where \\(g_\\lambda(x) = 1 / (1 + \\lambda x^2\\) and \\(S_\\epsilon(x) = (2/\\pi) atan2(x, \\epsilon)\\). The trainable parameters are \\(\\lambda\\), \\(\\epsilon\\), as well as the Riemannian metrics used to define the norms, gradients, and Laplacians.
    Subsequently linear combinations are taken and batch normalization (`torch.nn.BatchNorm2d`) is applied.
    """

    __constants__ = [
        "in_channels",
        "out_channels",
        "kernel_size",
        "iterations",
        "bn_momentum",
    ]

    in_channels: int
    """
        Number of input channels.
    """

    out_channels: int
    """
        Number of output channels.
    """

    kernel_size: int
    """
        Size `[kH,kW]` of the grid on which the approximative kernel that solves the dilation/erosion will be sampled. Larger grid sizes increase computational load but also allow more dilation and erosion to take place.
    """

    iterations: int
    """
        How many times the split operators are applied, defaults to 1. Higher iterations improve how well the output approximates the PDE solution but increases computational load.
    """

    alpha: float
    """
        Alpha parameter to determine the dilation and erosion's fractionality. Must be at least *0.55* and at most *1.0*, defaults to the happy compromise of *0.65*.
    """

    diffusion: DiffusionR2
    dilation: FractionalDilationR2
    switchds: DSSwitchR2
    switchmorphology: MorphologicalSwitchR2
    linear: LinearR2
    batch_normalization: torch.nn.BatchNorm2d

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int,
        iterations: int = 1,
        alpha: float = 0.65,
    ) -> None:
        super().__init__()

        self.in_channels = in_channels
        self.out_channels = out_channels
        self.kernel_size = kernel_size
        self.iterations = iterations

        self.diffusion = DiffusionR2(in_channels, kernel_size)
        self.dilation = FractionalDilationR2(in_channels, kernel_size, alpha)
        self.switchds = DSSwitchR2(in_channels, kernel_size)
        self.switchmorphology = MorphologicalSwitchR2(in_channels, kernel_size)
        self.linear = LinearR2(in_channels, out_channels)
        self.batch_normalization = torch.nn.BatchNorm2d(
            out_channels, track_running_stats=True
        )

        self.reset_parameters()

    def reset_parameters(self) -> None:
        self.diffusion.reset_parameters()
        self.dilation.reset_parameters()
        self.erosion.reset_parameters()
        self.switchds.reset_parameters()
        self.switchmorphology.reset_parameters()
        self.linear.reset_parameters()
        self.batch_normalization.reset_parameters()

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        x = input
        for i in range(self.iterations):
            diffused = self.diffusion(x)
            dilated = self.dilation(x)
            eroded = -self.dilation(-x)
            switchds = self.switchds(x)
            switchmorphology = self.switchmorphology(x)

            x = (
                # Diffusion
                switchds * diffused
                -
                # Shock
                (1 - switchds)
                * (
                    switchmorphology.abs()
                    * (
                        # Erosion
                        eroded * (switchmorphology > 0.0)
                        +
                        # Dilation
                        dilated * (switchmorphology < 0.0)
                        # When there is little diffusion or shock, return original
                        # feature map.
                    )
                    + (1.0 - switchmorphology.abs()) * x
                )
            )
            # assert torch.isfinite(x).all(), "out"
        return self.batch_normalization(self.linear(x))


class CDSPdeLayerR2(torch.nn.Module):
    """
    Diffusion-shock layer that includes batch normalization and linear combinations.
    Solves the PDE:
    $$
        u_t = -\\( \\mathbf{c} \\) u + g_\\lambda(\\|\\nabla u\\|) \\Delta u - (1 - g_\\lambda(\\|\\nabla u\\|)) S_\\epsilon(\\Delta_\\perp u) \\|\\nabla u\\|^\\alpha,
    $$
    where \\(g_\\lambda(x) = 1 / (1 + \\lambda x^2\\) and \\(S_\\epsilon(x) = (2/\\pi) atan2(x, \\epsilon)\\). The trainable parameters are \\(\\lambda\\), \\(\\epsilon\\), the convection vector \\( \\mathbf{c} \\), as well as the Riemannian metrics used to define the norms, gradients, and Laplacians.
    Subsequently linear combinations are taken and batch normalization (`torch.nn.BatchNorm2d`) is applied.
    """

    __constants__ = [
        "in_channels",
        "out_channels",
        "kernel_size",
        "iterations",
        "bn_momentum",
    ]

    in_channels: int
    """
        Number of input channels.
    """

    out_channels: int
    """
        Number of output channels.
    """

    kernel_size: int
    """
        Size `[kH,kW]` of the grid on which the approximative kernel that solves the dilation/erosion will be sampled. Larger grid sizes increase computational load but also allow more dilation and erosion to take place.
    """

    iterations: int
    """
        How many times the split operators are applied, defaults to 1. Higher iterations improve how well the output approximates the PDE solution but increases computational load.
    """

    alpha: float
    """
        Alpha parameter to determine the dilation and erosion's fractionality. Must be at least *0.55* and at most *1.0*, defaults to the happy compromise of *0.65*.
    """

    convection: ConvectionR2
    diffusion: DiffusionR2
    dilation: FractionalDilationR2
    switchds: DSSwitchR2
    switchmorphology: MorphologicalSwitchR2
    linear: LinearR2
    batch_normalization: torch.nn.BatchNorm2d

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int,
        iterations: int = 1,
        alpha: float = 0.65,
    ) -> None:
        super().__init__()

        self.in_channels = in_channels
        self.out_channels = out_channels
        self.kernel_size = kernel_size
        self.iterations = iterations

        self.convection = ConvectionR2(in_channels)
        self.diffusion = DiffusionR2(in_channels, kernel_size)
        self.dilation = FractionalDilationR2(in_channels, kernel_size, alpha)
        self.switchds = DSSwitchR2(in_channels, kernel_size)
        self.switchmorphology = MorphologicalSwitchR2(in_channels, kernel_size)
        self.linear = LinearR2(in_channels, out_channels)
        self.batch_normalization = torch.nn.BatchNorm2d(
            out_channels, track_running_stats=True
        )

        self.reset_parameters()

    def reset_parameters(self) -> None:
        self.diffusion.reset_parameters()
        self.dilation.reset_parameters()
        self.switchds.reset_parameters()
        self.switchmorphology.reset_parameters()
        self.linear.reset_parameters()
        self.batch_normalization.reset_parameters()

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        x = input
        for i in range(self.iterations):
            x = self.convection(x)
            diffused = self.diffusion(x)
            dilated = self.dilation(x)
            eroded = -self.dilation(-x)
            switchds = self.switchds(x)
            switchmorphology = self.switchmorphology(x)

            x = (
                # Diffusion
                switchds * diffused
                -
                # Shock
                (1 - switchds)
                * (
                    switchmorphology.abs()
                    * (
                        # Erosion
                        eroded * (switchmorphology > 0.0)
                        +
                        # Dilation
                        dilated * (switchmorphology < 0.0)
                        # When there is little diffusion or shock, return original
                        # feature map.
                    )
                    + (1.0 - switchmorphology.abs()) * x
                )
            )
        return self.batch_normalization(self.linear(x))


class CDEPdeLayerR2(torch.nn.Module):
    """
    Full convection/dilation/erosion layer that includes batch normalization and linear combinations.
    Solves the PDE:
    $$
        u_t = \\Delta_{\\matchal{G}_1} u + \\left\\| \\nabla u \\right\\|^{2\\alpha}_{\\mathcal{G}_2} - \\left\\| \\nabla u \\right\\|^{2\\alpha}_{\\mathcal{G}_3},
    $$
    where the Riemannian metrics \\( \\mathcal{G}_1 \\), \\( \\mathcal{G}_2 \\), and \\( \\mathcal{G}_3 \\) are the trainable parameters. Subsequently linear combinations are taken and batch normalization (`torch.nn.BatchNorm2d`) is applied.
    """

    __constants__ = [
        "in_channels",
        "out_channels",
        "kernel_size",
        "iterations",
        "alpha",
        "bn_momentum",
    ]

    in_channels: int
    """
        Number of input channels.
    """

    out_channels: int
    """
        Number of output channels.
    """

    kernel_size: int
    """
        Size `[kH,kW]` of the grid on which the approximative kernel that solves the dilation/erosion will be sampled. Larger grid sizes increase computational load but also allow more dilation and erosion to take place.
    """

    iterations: int
    """
        How many times the split operators are applied, defaults to 1. Higher iterations improve how well the output approximates the PDE solution but increases computational load.
    """

    alpha: float
    """
        Alpha parameter to determine the dilation and erosion's fractionality. Must be at least *0.55* and at most *1.0*, defaults to the happy compromise of *0.65*.
    """

    convection: ConvectionR2
    dilation: FractionalDilationR2
    erosion: FractionalErosionR2
    linear: LinearR2
    batch_normalization: torch.nn.BatchNorm2d

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int,
        iterations: int = 1,
        alpha: float = 0.65,
    ) -> None:
        super().__init__()

        self.in_channels = in_channels
        self.out_channels = out_channels
        self.kernel_size = kernel_size
        self.iterations = iterations
        self.alpha = alpha

        self.convection = ConvectionR2(in_channels)
        self.dilation = FractionalDilationR2(in_channels, kernel_size, alpha)
        self.erosion = FractionalErosionR2(in_channels, kernel_size, alpha)
        self.linear = LinearR2(in_channels, out_channels)
        self.batch_normalization = torch.nn.BatchNorm2d(
            out_channels, track_running_stats=True
        )

        self.reset_parameters()

    def reset_parameters(self) -> None:
        self.convection.reset_parameters()
        self.dilation.reset_parameters()
        self.erosion.reset_parameters()
        self.linear.reset_parameters()
        self.batch_normalization.reset_parameters()

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        x = input
        for i in range(self.iterations):
            x = self.erosion(self.dilation(self.convection(x)))

        return self.batch_normalization(self.linear(x))


class DDEPdeLayerR2(torch.nn.Module):
    """
    Full diffusion/dilation/erosion layer that includes batch normalization and linear combinations.
    Solves the PDE:
    $$
        u_t = \\Delta_{\\matchal{G}_1} u + \\left\\| \\nabla u \\right\\|^{2\\alpha}_{\\mathcal{G}_2} - \\left\\| \\nabla u \\right\\|^{2\\alpha}_{\\mathcal{G}_3},
    $$
    where the Riemannian metrics \\( \\mathcal{G}_1 \\), \\( \\mathcal{G}_2 \\), and \\( \\mathcal{G}_3 \\) are the trainable parameters. Subsequently linear combinations are taken and batch normalization (`torch.nn.BatchNorm2d`) is applied.
    """

    __constants__ = [
        "in_channels",
        "out_channels",
        "kernel_size",
        "iterations",
        "alpha",
        "bn_momentum",
    ]

    in_channels: int
    """
        Number of input channels.
    """

    out_channels: int
    """
        Number of output channels.
    """

    kernel_size: int
    """
        Size `[kH,kW]` of the grid on which the approximative kernel that solves the dilation/erosion will be sampled. Larger grid sizes increase computational load but also allow more dilation and erosion to take place.
    """

    iterations: int
    """
        How many times the split operators are applied, defaults to 1. Higher iterations improve how well the output approximates the PDE solution but increases computational load.
    """

    alpha: float
    """
        Alpha parameter to determine the dilation and erosion's fractionality. Must be at least *0.55* and at most *1.0*, defaults to the happy compromise of *0.65*.
    """

    diffusion: DiffusionR2
    dilation: FractionalDilationR2
    erosion: FractionalErosionR2
    linear: LinearR2
    batch_normalization: torch.nn.BatchNorm2d

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int,
        iterations: int = 1,
        alpha: float = 0.65,
    ) -> None:
        super().__init__()

        self.in_channels = in_channels
        self.out_channels = out_channels
        self.kernel_size = kernel_size
        self.iterations = iterations
        self.alpha = alpha

        self.diffusion = DiffusionR2(in_channels, kernel_size)
        self.dilation = FractionalDilationR2(in_channels, kernel_size, alpha)
        self.erosion = FractionalErosionR2(in_channels, kernel_size, alpha)
        self.linear = LinearR2(in_channels, out_channels)
        self.batch_normalization = torch.nn.BatchNorm2d(
            out_channels, track_running_stats=True
        )

        self.reset_parameters()

    def reset_parameters(self) -> None:
        self.diffusion.reset_parameters()
        self.dilation.reset_parameters()
        self.erosion.reset_parameters()
        self.linear.reset_parameters()
        self.batch_normalization.reset_parameters()

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        x = input
        for i in range(self.iterations):
            x = self.erosion(self.dilation(self.diffusion(x)))

        return self.batch_normalization(self.linear(x))


class CDDEPdeLayerR2(torch.nn.Module):
    """
    Full convection/diffusion/dilation/erosion layer that includes batch normalization and linear combinations.
    Solves the PDE:
    $$
        u_t = -\\mathbf{c} u + \\Delta_{\\matchal{G}_1} u + \\left\\| \\nabla u \\right\\|^{2\\alpha}_{\\mathcal{G}_2} - \\left\\| \\nabla u \\right\\|^{2\\alpha}_{\\mathcal{G}_3},
    $$
    wheret the convection vector \\( \\mathbf{c} \\) and the Riemannian metrics \\( \\mathcal{G}_1 \\), \\( \\mathcal{G}_2 \\), and \\( \\mathcal{G}_3 \\) are the trainable parameters. Subsequently linear combinations are taken and batch normalization (`torch.nn.BatchNorm2d`) is applied.
    """

    __constants__ = [
        "in_channels",
        "out_channels",
        "kernel_size",
        "iterations",
        "alpha",
        "bn_momentum",
    ]

    in_channels: int
    """
        Number of input channels.
    """

    out_channels: int
    """
        Number of output channels.
    """

    kernel_size: int
    """
        Size `[kH,kW]` of the grid on which the approximative kernel that solves the dilation/erosion will be sampled. Larger grid sizes increase computational load but also allow more dilation and erosion to take place.
    """

    iterations: int
    """
        How many times the split operators are applied, defaults to 1. Higher iterations improve how well the output approximates the PDE solution but increases computational load.
    """

    alpha: float
    """
        Alpha parameter to determine the dilation and erosion's fractionality. Must be at least *0.55* and at most *1.0*, defaults to the happy compromise of *0.65*.
    """

    convection: ConvectionR2
    diffusion: DiffusionR2
    dilation: FractionalDilationR2
    erosion: FractionalErosionR2
    linear: LinearR2
    batch_normalization: torch.nn.BatchNorm2d

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int,
        iterations: int = 1,
        alpha: float = 0.65,
    ) -> None:
        super().__init__()

        self.in_channels = in_channels
        self.out_channels = out_channels
        self.kernel_size = kernel_size
        self.iterations = iterations
        self.alpha = alpha

        self.convection = ConvectionR2(in_channels)
        self.diffusion = DiffusionR2(in_channels, kernel_size)
        self.dilation = FractionalDilationR2(in_channels, kernel_size, alpha)
        self.erosion = FractionalErosionR2(in_channels, kernel_size, alpha)
        self.linear = LinearR2(in_channels, out_channels)
        self.batch_normalization = torch.nn.BatchNorm2d(
            out_channels, track_running_stats=True
        )

        self.reset_parameters()

    def reset_parameters(self) -> None:
        self.convection.reset_parameters()
        self.diffusion.reset_parameters()
        self.dilation.reset_parameters()
        self.erosion.reset_parameters()
        self.linear.reset_parameters()
        self.batch_normalization.reset_parameters()

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        x = input
        for i in range(self.iterations):
            x = self.erosion(self.dilation(self.diffusion(self.convection(x))))

        return self.batch_normalization(self.linear(x))


class DSPdeLayerR2Isotropic(torch.nn.Module):
    """
    Diffusion-shock layer that includes batch normalization and linear combinations.
    Solves the PDE:
    $$
        u_t = g_\\lambda(\\|\\nabla u\\|) \\Delta u - (1 - g_\\lambda(\\|\\nabla u\\|)) S_\\epsilon(\\Delta_\\perp u) \\|\\nabla u\\|^\\alpha,
    $$
    where \\(g_\\lambda(x) = 1 / (1 + \\lambda x^2\\) and \\(S_\\epsilon(x) = (2/\\pi) atan2(x, \\epsilon)\\). The trainable parameters are \\(\\lambda\\), \\(\\epsilon\\), as well as the Riemannian metrics used to define the norms, gradients, and Laplacians.
    Subsequently linear combinations are taken and batch normalization (`torch.nn.BatchNorm2d`) is applied.
    """

    __constants__ = [
        "in_channels",
        "out_channels",
        "kernel_size",
        "iterations",
        "bn_momentum",
    ]

    in_channels: int
    """
        Number of input channels.
    """

    out_channels: int
    """
        Number of output channels.
    """

    kernel_size: int
    """
        Size `[kH,kW]` of the grid on which the approximative kernel that solves the dilation/erosion will be sampled. Larger grid sizes increase computational load but also allow more dilation and erosion to take place.
    """

    iterations: int
    """
        How many times the split operators are applied, defaults to 1. Higher iterations improve how well the output approximates the PDE solution but increases computational load.
    """

    alpha: float
    """
        Alpha parameter to determine the dilation and erosion's fractionality. Must be at least *0.55* and at most *1.0*, defaults to the happy compromise of *0.65*.
    """

    diffusion: DiffusionR2Isotropic
    dilation: FractionalDilationR2Isotropic
    switchds: DSSwitchR2Isotropic
    switchmorphology: MorphologicalSwitchR2Isotropic
    linear: LinearR2
    batch_normalization: torch.nn.BatchNorm2d

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int,
        iterations: int = 1,
        alpha: float = 0.65,
    ) -> None:
        super().__init__()

        self.in_channels = in_channels
        self.out_channels = out_channels
        self.kernel_size = kernel_size
        self.iterations = iterations

        self.diffusion = DiffusionR2Isotropic(in_channels, kernel_size)
        self.dilation = FractionalDilationR2Isotropic(in_channels, kernel_size, alpha)
        self.switchds = DSSwitchR2Isotropic(in_channels, kernel_size)
        self.switchmorphology = MorphologicalSwitchR2Isotropic(in_channels, kernel_size)
        self.linear = LinearR2(in_channels, out_channels)
        self.batch_normalization = torch.nn.BatchNorm2d(
            out_channels, track_running_stats=True
        )

        self.reset_parameters()

    def reset_parameters(self) -> None:
        self.diffusion.reset_parameters()
        self.dilation.reset_parameters()
        self.switchds.reset_parameters()
        self.switchmorphology.reset_parameters()
        self.linear.reset_parameters()
        self.batch_normalization.reset_parameters()

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        x = input
        for i in range(self.iterations):
            diffused = self.diffusion(x)
            dilated = self.dilation(x)
            eroded = -self.dilation(-x)
            switchds = self.switchds(x)
            switchmorphology = self.switchmorphology(x)

            x = (
                # Diffusion
                switchds * diffused
                -
                # Shock
                (1 - switchds)
                * (
                    switchmorphology.abs()
                    * (
                        # Erosion
                        eroded * (switchmorphology > 0.0)
                        +
                        # Dilation
                        dilated * (switchmorphology < 0.0)
                        # When there is little diffusion or shock, return original
                        # feature map.
                    )
                    + (1.0 - switchmorphology.abs()) * x
                )
            )
        return self.batch_normalization(self.linear(x))


class CDSPdeLayerR2Isotropic(torch.nn.Module):
    """
    Diffusion-shock layer that includes batch normalization and linear combinations.
    Solves the PDE:
    $$
        u_t = -\\( \\mathbf{c} \\) u + g_\\lambda(\\|\\nabla u\\|) \\Delta u - (1 - g_\\lambda(\\|\\nabla u\\|)) S_\\epsilon(\\Delta_\\perp u) \\|\\nabla u\\|^\\alpha,
    $$
    where \\(g_\\lambda(x) = 1 / (1 + \\lambda x^2\\) and \\(S_\\epsilon(x) = (2/\\pi) atan2(x, \\epsilon)\\). The trainable parameters are \\(\\lambda\\), \\(\\epsilon\\), the convection vector \\( \\mathbf{c} \\), as well as the Riemannian metrics used to define the norms, gradients, and Laplacians.
    Subsequently linear combinations are taken and batch normalization (`torch.nn.BatchNorm2d`) is applied.
    """

    __constants__ = [
        "in_channels",
        "out_channels",
        "kernel_size",
        "iterations",
        "bn_momentum",
    ]

    in_channels: int
    """
        Number of input channels.
    """

    out_channels: int
    """
        Number of output channels.
    """

    kernel_size: int
    """
        Size `[kH,kW]` of the grid on which the approximative kernel that solves the dilation/erosion will be sampled. Larger grid sizes increase computational load but also allow more dilation and erosion to take place.
    """

    iterations: int
    """
        How many times the split operators are applied, defaults to 1. Higher iterations improve how well the output approximates the PDE solution but increases computational load.
    """

    alpha: float
    """
        Alpha parameter to determine the dilation and erosion's fractionality. Must be at least *0.55* and at most *1.0*, defaults to the happy compromise of *0.65*.
    """

    convection: ConvectionR2
    diffusion: DiffusionR2Isotropic
    dilation: FractionalDilationR2Isotropic
    switchds: DSSwitchR2Isotropic
    switchmorphology: MorphologicalSwitchR2Isotropic
    linear: LinearR2
    batch_normalization: torch.nn.BatchNorm2d

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int,
        iterations: int = 1,
        alpha: float = 0.65,
    ) -> None:
        super().__init__()

        self.in_channels = in_channels
        self.out_channels = out_channels
        self.kernel_size = kernel_size
        self.iterations = iterations

        self.convection = ConvectionR2(in_channels)
        self.diffusion = DiffusionR2Isotropic(in_channels, kernel_size)
        self.dilation = FractionalDilationR2Isotropic(in_channels, kernel_size, alpha)
        self.switchds = DSSwitchR2Isotropic(in_channels, kernel_size)
        self.switchmorphology = MorphologicalSwitchR2Isotropic(in_channels, kernel_size)
        self.linear = LinearR2(in_channels, out_channels)
        self.batch_normalization = torch.nn.BatchNorm2d(
            out_channels, track_running_stats=True
        )

        self.reset_parameters()

    def reset_parameters(self) -> None:
        self.diffusion.reset_parameters()
        self.dilation.reset_parameters()
        self.switchds.reset_parameters()
        self.switchmorphology.reset_parameters()
        self.linear.reset_parameters()
        self.batch_normalization.reset_parameters()

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        x = input
        for i in range(self.iterations):
            x = self.convection(x)
            diffused = self.diffusion(x)
            dilated = self.dilation(x)
            eroded = -self.dilation(-x)
            switchds = self.switchds(x)
            switchmorphology = self.switchmorphology(x)

            x = (
                # Diffusion
                switchds * diffused
                -
                # Shock
                (1 - switchds)
                * (
                    switchmorphology.abs()
                    * (
                        # Erosion
                        eroded * (switchmorphology > 0.0)
                        +
                        # Dilation
                        dilated * (switchmorphology < 0.0)
                        # When there is little diffusion or shock, return original
                        # feature map.
                    )
                    + (1.0 - switchmorphology.abs()) * x
                )
            )
        return self.batch_normalization(self.linear(x))


class CDEPdeLayerR2Isotropic(torch.nn.Module):
    """
    Full convection/dilation/erosion layer that includes batch normalization and linear combinations.
    Solves the PDE:
    $$
        u_t = \\Delta_{\\matchal{G}_1} u + \\left\\| \\nabla u \\right\\|^{2\\alpha}_{\\mathcal{G}_2} - \\left\\| \\nabla u \\right\\|^{2\\alpha}_{\\mathcal{G}_3},
    $$
    where the Riemannian metrics \\( \\mathcal{G}_1 \\), \\( \\mathcal{G}_2 \\), and \\( \\mathcal{G}_3 \\) are the trainable parameters. Subsequently linear combinations are taken and batch normalization (`torch.nn.BatchNorm2d`) is applied.
    """

    __constants__ = [
        "in_channels",
        "out_channels",
        "kernel_size",
        "iterations",
        "alpha",
        "bn_momentum",
    ]

    in_channels: int
    """
        Number of input channels.
    """

    out_channels: int
    """
        Number of output channels.
    """

    kernel_size: int
    """
        Size `[kH,kW]` of the grid on which the approximative kernel that solves the dilation/erosion will be sampled. Larger grid sizes increase computational load but also allow more dilation and erosion to take place.
    """

    iterations: int
    """
        How many times the split operators are applied, defaults to 1. Higher iterations improve how well the output approximates the PDE solution but increases computational load.
    """

    alpha: float
    """
        Alpha parameter to determine the dilation and erosion's fractionality. Must be at least *0.55* and at most *1.0*, defaults to the happy compromise of *0.65*.
    """

    convection: ConvectionR2
    dilation: FractionalDilationR2Isotropic
    erosion: FractionalErosionR2Isotropic
    linear: LinearR2
    batch_normalization: torch.nn.BatchNorm2d

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int,
        iterations: int = 1,
        alpha: float = 0.65,
    ) -> None:
        super().__init__()

        self.in_channels = in_channels
        self.out_channels = out_channels
        self.kernel_size = kernel_size
        self.iterations = iterations
        self.alpha = alpha

        self.convection = ConvectionR2(in_channels)
        self.dilation = FractionalDilationR2Isotropic(in_channels, kernel_size, alpha)
        self.erosion = FractionalErosionR2Isotropic(in_channels, kernel_size, alpha)
        self.linear = LinearR2(in_channels, out_channels)
        self.batch_normalization = torch.nn.BatchNorm2d(
            out_channels, track_running_stats=True
        )

        self.reset_parameters()

    def reset_parameters(self) -> None:
        self.convection.reset_parameters()
        self.dilation.reset_parameters()
        self.erosion.reset_parameters()
        self.linear.reset_parameters()
        self.batch_normalization.reset_parameters()

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        x = input
        for i in range(self.iterations):
            x = self.erosion(self.dilation(self.convection(x)))

        return self.batch_normalization(self.linear(x))


class DDEPdeLayerR2Isotropic(torch.nn.Module):
    """
    Full diffusion/dilation/erosion layer that includes batch normalization and linear combinations.
    Solves the PDE:
    $$
        u_t = \\Delta_{\\matchal{G}_1} u + \\left\\| \\nabla u \\right\\|^{2\\alpha}_{\\mathcal{G}_2} - \\left\\| \\nabla u \\right\\|^{2\\alpha}_{\\mathcal{G}_3},
    $$
    where the Riemannian metrics \\( \\mathcal{G}_1 \\), \\( \\mathcal{G}_2 \\), and \\( \\mathcal{G}_3 \\) are the trainable parameters. Subsequently linear combinations are taken and batch normalization (`torch.nn.BatchNorm2d`) is applied.
    """

    __constants__ = [
        "in_channels",
        "out_channels",
        "kernel_size",
        "iterations",
        "alpha",
        "bn_momentum",
    ]

    in_channels: int
    """
        Number of input channels.
    """

    out_channels: int
    """
        Number of output channels.
    """

    kernel_size: int
    """
        Size `[kH,kW]` of the grid on which the approximative kernel that solves the dilation/erosion will be sampled. Larger grid sizes increase computational load but also allow more dilation and erosion to take place.
    """

    iterations: int
    """
        How many times the split operators are applied, defaults to 1. Higher iterations improve how well the output approximates the PDE solution but increases computational load.
    """

    alpha: float
    """
        Alpha parameter to determine the dilation and erosion's fractionality. Must be at least *0.55* and at most *1.0*, defaults to the happy compromise of *0.65*.
    """

    diffusion: DiffusionR2Isotropic
    dilation: FractionalDilationR2Isotropic
    erosion: FractionalErosionR2Isotropic
    linear: LinearR2
    batch_normalization: torch.nn.BatchNorm2d

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int,
        iterations: int = 1,
        alpha: float = 0.65,
    ) -> None:
        super().__init__()

        self.in_channels = in_channels
        self.out_channels = out_channels
        self.kernel_size = kernel_size
        self.iterations = iterations
        self.alpha = alpha

        self.diffusion = DiffusionR2Isotropic(in_channels, kernel_size)
        self.dilation = FractionalDilationR2Isotropic(in_channels, kernel_size, alpha)
        self.erosion = FractionalErosionR2Isotropic(in_channels, kernel_size, alpha)
        self.linear = LinearR2(in_channels, out_channels)
        self.batch_normalization = torch.nn.BatchNorm2d(
            out_channels, track_running_stats=True
        )

        self.reset_parameters()

    def reset_parameters(self) -> None:
        self.diffusion.reset_parameters()
        self.dilation.reset_parameters()
        self.erosion.reset_parameters()
        self.linear.reset_parameters()
        self.batch_normalization.reset_parameters()

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        x = input
        for i in range(self.iterations):
            x = self.erosion(self.dilation(self.diffusion(x)))

        return self.batch_normalization(self.linear(x))


class CDDEPdeLayerR2Isotropic(torch.nn.Module):
    """
    Full convection/diffusion/dilation/erosion layer that includes batch normalization and linear combinations.
    Solves the PDE:
    $$
        u_t = -\\mathbf{c} u + \\Delta_{\\matchal{G}_1} u + \\left\\| \\nabla u \\right\\|^{2\\alpha}_{\\mathcal{G}_2} - \\left\\| \\nabla u \\right\\|^{2\\alpha}_{\\mathcal{G}_3},
    $$
    wheret the convection vector \\( \\mathbf{c} \\) and the Riemannian metrics \\( \\mathcal{G}_1 \\), \\( \\mathcal{G}_2 \\), and \\( \\mathcal{G}_3 \\) are the trainable parameters. Subsequently linear combinations are taken and batch normalization (`torch.nn.BatchNorm2d`) is applied.
    """

    __constants__ = [
        "in_channels",
        "out_channels",
        "kernel_size",
        "iterations",
        "alpha",
        "bn_momentum",
    ]

    in_channels: int
    """
        Number of input channels.
    """

    out_channels: int
    """
        Number of output channels.
    """

    kernel_size: int
    """
        Size `[kH,kW]` of the grid on which the approximative kernel that solves the dilation/erosion will be sampled. Larger grid sizes increase computational load but also allow more dilation and erosion to take place.
    """

    iterations: int
    """
        How many times the split operators are applied, defaults to 1. Higher iterations improve how well the output approximates the PDE solution but increases computational load.
    """

    alpha: float
    """
        Alpha parameter to determine the dilation and erosion's fractionality. Must be at least *0.55* and at most *1.0*, defaults to the happy compromise of *0.65*.
    """

    convection: ConvectionR2
    diffusion: DiffusionR2Isotropic
    dilation: FractionalDilationR2Isotropic
    erosion: FractionalErosionR2Isotropic
    linear: LinearR2
    batch_normalization: torch.nn.BatchNorm2d

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int,
        iterations: int = 1,
        alpha: float = 0.65,
    ) -> None:
        super().__init__()

        self.in_channels = in_channels
        self.out_channels = out_channels
        self.kernel_size = kernel_size
        self.iterations = iterations
        self.alpha = alpha

        self.convection = ConvectionR2(in_channels)
        self.diffusion = DiffusionR2Isotropic(in_channels, kernel_size)
        self.dilation = FractionalDilationR2Isotropic(in_channels, kernel_size, alpha)
        self.erosion = FractionalErosionR2Isotropic(in_channels, kernel_size, alpha)
        self.linear = LinearR2(in_channels, out_channels)
        self.batch_normalization = torch.nn.BatchNorm2d(
            out_channels, track_running_stats=True
        )

        self.reset_parameters()

    def reset_parameters(self) -> None:
        self.convection.reset_parameters()
        self.diffusion.reset_parameters()
        self.dilation.reset_parameters()
        self.erosion.reset_parameters()
        self.linear.reset_parameters()
        self.batch_normalization.reset_parameters()

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        x = input
        for i in range(self.iterations):
            x = self.erosion(self.dilation(self.diffusion(self.convection(x))))

        return self.batch_normalization(self.linear(x))


class SpatialResampleR2(torch.nn.Module):
    """ """

    __constants__ = []

    """

    """
    size: tuple[int, int]
    scale_factor: float
    mode: str

    def __init__(
        self,
        size: tuple[int, int] = None,
        scale_factor: float = None,
        mode: str = "nearest",
    ) -> None:
        super().__init__()
        if size is None and scale_factor is None:
            raise ValueError("size or scale_factor needs to be specified")

        if size is not None and scale_factor is not None:
            raise ValueError("size or scale_factor needs to be specified, not both")

        self.size = size
        self.scale_factor = scale_factor
        self.mode = mode

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        if self.scale_factor is not None:
            h = floor(input.shape[2] * self.scale_factor)
            w = floor(input.shape[3] * self.scale_factor)
        else:
            h = self.size[0]
            w = self.size[1]

        return F.interpolate(input, size=(h, w), mode=self.mode)
