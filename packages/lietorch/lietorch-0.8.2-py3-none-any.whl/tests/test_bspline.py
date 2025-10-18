import pytest
import torch
import numpy as np

import sys, os

# expecting to find lietorch package in parent directory
sys.path.append("..")
import lietorch

RNG_SEED = 0

if RNG_SEED:
    torch.manual_seed(RNG_SEED)

torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False


x = torch.tensor([[0, 0], [1, 0], [0, 1], [1, 1], [0.5, 0.5]]).float()
fx_order2 = torch.tensor([0.6927, -0.5022, 0.2812, 0.9740, 0.2187]).float()

nodes = torch.tensor([[0, 0], [1, 1], [1, 0], [0, 1]]).float()
scales = torch.tensor([0.5, 0.2, 0.4, 1.5]).float()
weights = torch.tensor([1, 1.5, -1, 0.5]).float()


def test_verify_deboor():
    torch.manual_seed(RNG_SEED)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

    out2 = lietorch.bspline.sample(nodes, scales, weights, x, order=2)
    assert (out2 - fx_order2).abs().max().item() < 1e-3

    r = torch.randn(1000, 1000, dtype=torch.float32)

    poly0 = lietorch.bspline._basis_constant(r)
    deboor0 = lietorch.bspline._basis_deboor(r, 0)
    assert (poly0 - deboor0).abs().max().item() < 1e-3

    poly1 = lietorch.bspline._basis_linear(r)
    deboor1 = lietorch.bspline._basis_deboor(r, 1)
    assert (poly1 - deboor1).abs().max().item() < 1e-3

    poly2 = lietorch.bspline._basis_quadratic(r)
    deboor2 = lietorch.bspline._basis_deboor(r, 2)
    assert (poly2 - deboor2).abs().max().item() < 1e-3

    poly3 = lietorch.bspline._basis_cubic(r)
    deboor3 = lietorch.bspline._basis_deboor(r, 3)
    assert (poly3 - deboor3).abs().max().item() < 1e-3


def test_sampling_shape():
    Co = 2
    Sp = 3
    C1, C2 = 4, 5
    XC1, XC2 = 6, 7

    nodes = torch.randn(C1, C2, Sp, Co)
    scales = torch.randn(C1, C2, Sp).abs()
    weights = torch.randn(C1, C2, Sp)
    x = torch.randn(XC1, XC2, Co)

    y = lietorch.bspline.sample(nodes, scales, weights, x, order=3)
    assert y.shape == (C1, C2, XC1, XC2)


def show_bspline():
    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 unused import

    from matplotlib import cm
    from matplotlib.colors import LightSource

    x = np.arange(-2, 3, 0.1)
    y = np.arange(-2, 3, 0.1)
    xs, ys = np.meshgrid(x, y)
    grid = np.array([xs, ys]).transpose(1, 2, 0)

    z = lietorch.bspline.sample(
        nodes, scales, weights, torch.tensor(grid), order=2
    ).numpy()

    # Set up plot
    fig, ax = plt.subplots(subplot_kw=dict(projection="3d"))

    ls = LightSource(270, 45)

    rgb = ls.shade(z, cmap=cm.gist_earth, vert_exag=0.1, blend_mode="soft")
    surf = ax.plot_surface(
        xs,
        ys,
        z,
        rstride=1,
        cstride=1,
        linewidth=0,
        antialiased=False,
        shade=True,
        facecolors=rgb,
    )

    plt.show()
