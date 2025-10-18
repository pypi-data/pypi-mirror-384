"""
Functions for adding various types of padding to tensors.
"""

import torch


def pad_reflect(x, dim, padding):
    """
    Pad a tensor via reflection along a specified dimension.

    Parameters
    ---------------
    x : torch.Tensor
        Input tensor to be padded.
    dim : int
        Dimension to pad along.
    padding : int or (int, int)
        Amount of padding on each side.
    """
    if dim < 0:
        dim += len(x.shape)

    if type(padding) is int:
        pad_bottom, pad_top = padding, padding
    else:
        pad_bottom, pad_top = padding

    if pad_bottom == 0 and pad_top == 0:
        return x

    bottom = tuple(
        slice(0, None if i != dim else pad_bottom, 1) for i in range(len(x.shape))
    )
    top = tuple(
        slice(0 if i != dim else -pad_top, None, 1) for i in range(len(x.shape))
    )
    x = torch.cat(
        [torch.flip(x[bottom], (dim,)), x, torch.flip(x[top], (dim,))], dim=dim
    )
    return x


def pad_periodic(x, dim, padding):
    """
    Pad a tensor periodically along a specified dimension.

    Parameters
    ---------------
    x : torch.Tensor
        Input tensor to be padded.
    dim : int
        Dimension to pad along.
    padding : int or (int, int)
        Amount of padding on each side.
    """
    if dim < 0:
        dim += len(x.shape)

    if type(padding) is int:
        pad_bottom, pad_top = padding, padding
    else:
        pad_bottom, pad_top = padding

    bottom = tuple(
        slice(0, None if i != dim else pad_top, 1) for i in range(len(x.shape))
    )
    top = tuple(
        slice(0 if i != dim else -pad_bottom, None, 1) for i in range(len(x.shape))
    )
    x = torch.cat([x[top], x, x[bottom]], dim=dim)
    return x
