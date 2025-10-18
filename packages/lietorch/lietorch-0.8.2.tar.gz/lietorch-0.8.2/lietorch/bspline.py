"""
    Non-uniform B-spline implementation.
"""

import torch
import torch.nn.functional as F

_epsilon_float32 = (
    torch.tensor([7], dtype=torch.float32) / 3
    - torch.tensor([4], dtype=torch.float32) / 3
    - 1
).abs()
"""
    Single precision (float32) machine epsilon in tensor form.
"""


def _get_basis_function(order):
    assert order >= 0
    if order == 0:
        return _basis_constant
    elif order == 1:
        return _basis_linear
    elif order == 2:
        return _basis_quadratic
    elif order == 3:
        return _basis_cubic
    else:
        return lambda x: _basis_deboor(x, order=order)


def _basis_constant(x):
    return (torch.sign(1 / 2 - x) + torch.sign(1 / 2 + x)) / 2


def _basis_linear(x):
    return (
        (1 - x) * torch.sign(1 - x)
        - 2 * x * torch.sign(x)
        + (1 + x) * torch.sign(1 + x)
    ) / 2


def _basis_quadratic(x):
    return (
        -3 * (1 / 2 - x) ** 2 * torch.sign(1 / 2 - x)
        + (3 / 2 - x) ** 2 * torch.sign(3 / 2 - x)
        - 3 * (1 / 2 + x) ** 2 * torch.sign(1 / 2 + x)
        + (3 / 2 + x) ** 2 * torch.sign(3 / 2 + x)
    ) / 4


def _basis_cubic(x):
    return (
        -4 * (1 - x) ** 3 * torch.sign(1 - x)
        + (2 - x) ** 3 * torch.sign(2 - x)
        + 6 * x ** 3 * torch.sign(x)
        - 4 * (1 + x) ** 3 * torch.sign(1 + x)
        + (2 + x) ** 3 * torch.sign(2 + x)
    ) / 12


def _basis_deboor(x, order):
    """
        Compute centered basis with de Boor's algorithm.

        Parameters:
        ---------------
        x : torch.Tensor

        order: int >= 0

        Returns:
        --------------
        torch.Tensor
    """
    order += 1

    # offsets from the point we are interested in
    a = torch.linspace(
        -(order - 1.0) / 2.0, (order - 1.0) / 2.0, order, device=x.device
    )
    # apply offsets to the points
    b = x[..., None] + a
    # calculate 1st order bspline value at the offsets
    c = torch.where(
        (b >= -0.5) & (b < 0.5),
        torch.ones_like(b, dtype=x.dtype, device=x.device),
        torch.zeros_like(b, dtype=x.dtype, device=x.device),
    )

    if order == 1:
        return torch.squeeze(c, dim=-1)

    # walk up the offset pyramid:
    #
    #   i                               bspline order
    #  -----------                      --------------
    #  order-1          x               order               ^
    #  order-2        +   +             order-1             |
    #  order-3      +   +   +           order-2             |
    #   ...       +   +   +   +         order-3             |
    #    1                                ...               |
    #    0    + .................. +    1                   |
    #
    for i in torch.arange(1, order):
        # calculate next level offsets (one less vs. last level)
        a = torch.linspace(
            -(order - i - 1.0) / 2.0,
            (order - i - 1.0) / 2.0,
            order - i,
            device=x.device,
        )
        # apply offsets to x
        b = x[..., None] + a

        # bspline values of previous level
        c1 = c[..., 1:] if i == 1 else c[..., 1 : -(i - 1)]
        c2 = c[..., :-i]

        # this levels factors
        b1 = (b + (i + 1.0) / 2.0) / i
        b2 = ((i + 1.0) / 2.0 - b) / i

        c = torch.reshape(F.pad(b1 * c1 + b2 * c2, (0, i)), c.shape)

    return c[..., 0]


def sample(nodes, scales, weights, x, order=2):
    """
        Sample a set of functions that are represented by linear combinations of shifted B-splines.

        Parameters
        --------------
        nodes : torch.Tensor
            Center points of each spline, has shape [Channels1 ... ChannelsN, Splines, Coordinates].

        scales : torch.Tensor
            Scale of each spline, has shape [Channels1 ... ChannelsN, Splines]

        weights : torch.Tensor
            Weight coëfficient of each spline, has shape [Channels1 ... ChannelsN, Splines].
            
        x : torch.Tensor
            Tensor of shape [XShape1 ... XShapeM, Coordinates] that gives coordinates for a set of points at which to evaluate the function specified by the splines given by the first three arguments.

        order : int
            Order of B-splines to use, defaults to 2 (i.e. quadratic B-splines).

        Returns
        -----------
        A tensor of shape [XShape1 ... XShapeM, Channels1 ... ChannelsN], i.e. the same shape as the `x` tensor minus the last dimension plus the channel dimensions.
    """
    basis_fn = _get_basis_function(order=order)

    # print(f"Devices: {nodes.device}, {scales.device}, {weights.device}, {x.device}")

    # number of coordinates in x needs to match the number used in f
    assert x.shape[-1] == nodes.shape[-1]
    # equal amount and shape center coordinates, scales and weights
    assert nodes.shape[:-1] == scales.shape == weights.shape, print(
        f"shapes: {nodes.shape[:-1]}, {scales.shape}, {weights.shape}"
    )

    # Insert dummy dimensions for broadcasting
    for i in range(len(x.shape) - 1):
        nodes = nodes[..., None, :, :]
        scales = scales[..., None, :]
        weights = weights[..., None, :]
    x = x[..., None, :]

    # locations where we will evaluate the basis function
    y = (x - nodes) / torch.sqrt(scales[..., None] ** 2 + _epsilon_float32.to(x.device))
    # evaluate the basis function and multiply the results from all dimensions
    # then scale each spline with its respective weight
    z = basis_fn(y).prod(dim=-1) * weights
    # sum over all the splines and return
    return z.sum(dim=-1)

