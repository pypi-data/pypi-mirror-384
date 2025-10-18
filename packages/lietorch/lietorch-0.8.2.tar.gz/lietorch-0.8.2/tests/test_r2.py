import pytest
import torch

import sys, os

# expecting to find lietorch package in parent directory
sys.path.append("..")
import lietorch

RNG_SEED = 0

if RNG_SEED:
    torch.manual_seed(RNG_SEED)

torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False


def test_morphological_convolution_r2_cpu_autograd():
    from lietorch.nn import MorphologicalConvolutionR2
    from lietorch.nn.functional import morphological_convolution_r2
    from torch.autograd.gradcheck import gradcheck

    input = (
        torch.randn(2, 2, 9, 9, requires_grad=True, dtype=torch.float64),
        torch.randn(2, 5, 5, requires_grad=True, dtype=torch.float64),
    )

    # input = (
    #     torch.randperm(8 * 7 * 7, dtype=torch.float64, requires_grad=True).view(
    #         1, 1, 8, 7, 7
    #     ),
    #     torch.randn(3 * 3 * 3, dtype=torch.float64, requires_grad=True).view(
    #         1, 3, 3, 3
    #     ),
    # )
    assert gradcheck(morphological_convolution_r2, input, atol=1e-4)

    module = MorphologicalConvolutionR2(channels=2, kernel_size=(3, 3))

    assert gradcheck(
        module,
        torch.randn(1, 2, 9, 9, requires_grad=True, dtype=torch.float64),
        atol=1e-4,
    )


def test_morphological_convolution_r2_cuda_autograd():
    from lietorch.nn import MorphologicalConvolutionR2
    from lietorch.nn.functional import morphological_convolution_r2
    from torch.autograd.gradcheck import gradcheck

    input = (
        torch.randn(2, 2, 9, 9, requires_grad=True, dtype=torch.float64).cuda(),
        torch.randn(2, 5, 5, requires_grad=True, dtype=torch.float64).cuda(),
    )

    # input = (
    #     torch.randperm(8 * 7 * 7, dtype=torch.float64, requires_grad=True).view(
    #         1, 1, 8, 7, 7
    #     ),
    #     torch.randn(3 * 3 * 3, dtype=torch.float64, requires_grad=True).view(
    #         1, 3, 3, 3
    #     ),
    # )
    assert gradcheck(morphological_convolution_r2, input, atol=1e-4)

    module = MorphologicalConvolutionR2(channels=2, kernel_size=(3, 3))

    assert gradcheck(
        module.cuda(),
        torch.randn(1, 2, 9, 9, requires_grad=True, dtype=torch.float64).cuda(),
        atol=1e-4,
    )


def test_morphological_kernel_r2_autograd():
    from lietorch.nn.functional import morphological_kernel_r2
    from torch.autograd.gradcheck import gradcheck

    input = (
        torch.randn(8, 8, 9, requires_grad=True, dtype=torch.float64),
        2,
        0.65,
    )

    assert gradcheck(morphological_kernel_r2, input, atol=1e-4)

    input = (
        torch.randn(8, 8, 9, requires_grad=True, dtype=torch.float64).cuda(),
        5,
        1.0,
    )

    assert gradcheck(morphological_kernel_r2, input, atol=1e-4)


def test_fractional_dilation_r2_autograd():
    import torch
    from torch.autograd.gradcheck import gradcheck
    from lietorch.nn.functional import fractional_dilation_r2
    from lietorch.nn import FractionalDilationR2

    x = torch.randn([2, 2, 10, 10], dtype=torch.float64, requires_grad=True)
    p = torch.rand([2, 5], dtype=torch.float64, requires_grad=True)

    assert gradcheck(fractional_dilation_r2, (x, p, 2, 0.55), atol=1e-4)
    assert gradcheck(fractional_dilation_r2, (x, p, 3, 1.0), atol=1e-4)

    xc = x.cuda()
    pc = p.cuda()

    assert gradcheck(fractional_dilation_r2, (xc, pc, 2, 0.55), atol=1e-4)
    assert gradcheck(fractional_dilation_r2, (xc, pc, 3, 1.0), atol=1e-4)

    module = FractionalDilationR2(2, 5, alpha=0.7, finsler_order=5).to(torch.float64)

    assert gradcheck(module, (x,), atol=1e-4)
    assert gradcheck(module.cuda(), (x.cuda(),), atol=1e-4)

    module.train()
    y1 = module(xc)
    module.eval()
    with torch.no_grad():
        y2 = module(xc)
    assert y1.allclose(y2)


def test_fractional_erosion_r2_autograd():
    import torch
    from torch.autograd.gradcheck import gradcheck
    from lietorch.nn.functional import fractional_erosion_r2
    from lietorch.nn import FractionalErosionR2

    x = torch.randn([2, 2, 10, 10], dtype=torch.float64, requires_grad=True)
    p = torch.rand([2, 5], dtype=torch.float64, requires_grad=True)

    assert gradcheck(fractional_erosion_r2, (x, p, 2, 0.55), atol=1e-4)
    assert gradcheck(fractional_erosion_r2, (x, p, 3, 1.0), atol=1e-4)

    xc = x.cuda()
    pc = p.cuda()

    assert gradcheck(fractional_erosion_r2, (xc, pc, 2, 0.55), atol=1e-4)
    assert gradcheck(fractional_erosion_r2, (xc, pc, 3, 1.0), atol=1e-4)

    module = FractionalErosionR2(2, 5, alpha=0.7, finsler_order=5).to(torch.float64)

    assert gradcheck(module, (x,), atol=1e-4)
    assert gradcheck(module.cuda(), (x.cuda(),), atol=1e-4)

    module.train()
    y1 = module(xc)
    module.eval()
    with torch.no_grad():
        y2 = module(xc)
    assert y1.allclose(y2)


def test_linear():
    import torch
    from torch.autograd.gradcheck import gradcheck
    from lietorch.nn.functional import linear_r2
    from lietorch.nn import LinearR2

    a = torch.tensor([[[[1]], [[2]]]], dtype=torch.float64)
    v = torch.tensor([[1, 2, 3], [-3, -2, -1]], dtype=torch.float64)
    b = linear_r2(a, v)
    b_exp = torch.tensor([[[-5]], [[-2]], [[1]]], dtype=torch.float64)
    assert b.allclose(b_exp)
    assert linear_r2(a.cuda(), v.cuda()).allclose(b_exp.cuda())

    x = torch.randn([2, 3, 5, 5], dtype=torch.float64, requires_grad=True)
    w = torch.randn([3, 6], dtype=torch.float64, requires_grad=True)

    assert gradcheck(linear_r2, (x, w), atol=1e-4)
    assert gradcheck(linear_r2, (x.cuda(), w.cuda()), atol=1e-4)

    module = LinearR2(3, 5).double()

    assert gradcheck(module, (x,), atol=1e-4)


def test_convection_r2_autograd():
    import torch
    from torch.autograd.gradcheck import gradcheck
    from lietorch.nn.functional import convection_r2
    from lietorch.nn import ConvectionR2

    x = torch.randn([2, 2, 5, 5], dtype=torch.float64, requires_grad=True)

    g1 = torch.tensor(
        [[0.1, 2.5], [-0.1, -2.5]], dtype=torch.float64, requires_grad=True
    )
    assert gradcheck(convection_r2, (x, g1), atol=1e-3)

    g2 = torch.tensor(
        [[1.5, -0.01], [-1.5, 0.01]], dtype=torch.float64, requires_grad=True
    )
    assert gradcheck(convection_r2, (x, g2), atol=1e-3)

    g3 = torch.tensor(
        [[-1.2, -0.1], [1.2, 0.1]], dtype=torch.float64, requires_grad=True
    )
    assert gradcheck(convection_r2, (x, g3), atol=1e-3)

    g4 = torch.tensor(
        [[0.7, -2.8], [-0.7, -4.8]], dtype=torch.float64, requires_grad=True
    )
    assert gradcheck(convection_r2, (x, g4), atol=1e-3)

    x2 = torch.randn([1, 1, 3, 3], dtype=torch.float64, requires_grad=True)

    g5 = torch.tensor([[0.1, 1.5]], dtype=torch.float64, requires_grad=True)
    assert gradcheck(convection_r2, (x2.cuda(), g5.cuda()), atol=1e-3)

    assert gradcheck(convection_r2, (x.cuda(), g1.cuda()), atol=1e-3)
    assert gradcheck(convection_r2, (x.cuda(), g2.cuda()), atol=1e-3)
    assert gradcheck(convection_r2, (x.cuda(), g3.cuda()), atol=1e-3)
    assert gradcheck(convection_r2, (x.cuda(), g4.cuda()), atol=1e-3)

