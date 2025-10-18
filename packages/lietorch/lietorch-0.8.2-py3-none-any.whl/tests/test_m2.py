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


def print_graph(g, level=0):
    if g == None:
        return
    print(" |--" * level, g)
    for subg in g.next_functions:
        print_graph(subg[0], level + 1)


def test_adp_cpu():
    from lietorch.nn.m2 import anisotropic_dilated_project_m2

    input = torch.randn(2, 2, 8, 10, 10)
    output = anisotropic_dilated_project_m2(input, 3, 2.5, 2.0 / 3.0)

    assert list(output.shape) == [2, 2, 10, 10]


def test_adp_cuda():
    from lietorch.nn.m2 import anisotropic_dilated_project_m2

    input = torch.randn(2, 2, 8, 10, 10).cuda()
    output = anisotropic_dilated_project_m2(input, 3, 2.5, 2.0 / 3.0)

    assert list(output.shape) == [2, 2, 10, 10]


def test_adp_compare():
    from lietorch.nn.m2 import anisotropic_dilated_project_m2

    input = torch.randn(2, 2, 8, 10, 10)
    output = anisotropic_dilated_project_m2(input, 3, 2.5, 2.0 / 3.0)

    input_cuda = input.cuda()
    output_cuda = anisotropic_dilated_project_m2(input, 3, 2.5, 2.0 / 3.0)

    assert output.allclose(output_cuda.cpu())


def test_adp_autograd_cpu():
    from lietorch.nn import AnisotropicDilatedProjectM2
    from torch.autograd.gradcheck import gradcheck

    input = (torch.randn(2, 2, 8, 10, 10, dtype=torch.float64, requires_grad=True),)

    assert gradcheck(AnisotropicDilatedProjectM2(), input)


def test_adp_autograd_cuda():
    from lietorch.nn import AnisotropicDilatedProjectM2
    from torch.autograd.gradcheck import gradcheck

    input = (
        torch.randn(2, 2, 8, 10, 10, dtype=torch.float64, requires_grad=True).cuda(),
    )

    assert gradcheck(AnisotropicDilatedProjectM2(), input)


def test_lift_m2_cartesian_autograd():
    from lietorch.nn import LiftM2Cartesian
    from lietorch.nn.functional import lift_m2_cartesian
    from torch.autograd.gradcheck import gradcheck

    input = (torch.randn(1, 2, 10, 10, dtype=torch.float64, requires_grad=True),)
    module = LiftM2Cartesian(
        in_channels=2, out_channels=3, orientations=8, kernel_size=5
    ).double()

    assert gradcheck(module, input)

    input_cuda = (input[0].cuda(),)
    module_cuda = module.cuda()

    assert gradcheck(module_cuda, input_cuda, atol=1e-3)

def test_convection_m2_autograd_cpu():
    from lietorch.nn import ConvectionM2
    from lietorch.nn.functional import convection_m2
    from torch.autograd.gradcheck import gradcheck

    input = (torch.randn(1, 2, 8, 5, 5, dtype=torch.float64, requires_grad=True),)
    module = ConvectionM2(channels=2, parameter_dtype=torch.float64)

    g1 = torch.tensor(
        [[0, 0, 1.0], [0.5, 0, 1.0]], dtype=torch.float64, requires_grad=True
    )
    module.g0 = torch.nn.Parameter(g1)
    assert gradcheck(module, input, atol=1e-3)

    g2 = torch.tensor(
        [[0, 1.0, 0], [0.5, 1.0, 0.3]], dtype=torch.float64, requires_grad=True
    )
    module.g0 = torch.nn.Parameter(g2)
    assert gradcheck(module, input, atol=1e-3)

    g3 = torch.tensor(
        [[1.0, 0, 0], [1.1, -0.3, 2.1]], dtype=torch.float64, requires_grad=True
    )
    module.g0 = torch.nn.Parameter(g3)
    assert gradcheck(module, input, atol=1e-3)

    g4 = torch.tensor(
        [[0, 1.0, 1.0], [0.5, 0.00001, 1.0]], dtype=torch.float64, requires_grad=True
    )
    module.g0 = torch.nn.Parameter(g4)
    assert gradcheck(module, input, atol=1e-3)

    g5 = torch.tensor(
        [[10.0, 0, 1.0], [-1.4, 0, -5.0]], dtype=torch.float64, requires_grad=True
    )
    module.g0 = torch.nn.Parameter(g5)
    assert gradcheck(module, input, atol=1e-3)

    input2 = (
        torch.randn(1, 1, 4, 2, 2, dtype=torch.float64, requires_grad=True),
        torch.tensor([[0.1, 0.1, 0.1]], dtype=torch.float64, requires_grad=True),
    )
    assert gradcheck(convection_m2, input2, atol=1e-3)

    input3 = (
        torch.randn(1, 3, 8, 5, 5, dtype=torch.float64, requires_grad=True),
        torch.tensor(
            [[0.2, 0.5, 0.5], [-1.9, 1.2, 1.2], [10.1, -1.1, -1.2]],
            dtype=torch.float64,
            requires_grad=True,
        ),
    )
    assert gradcheck(convection_m2, input3, atol=1e-3)


def test_convection_m2_autograd_cuda():
    from lietorch.nn import ConvectionM2
    from lietorch.nn.functional import convection_m2
    from torch.autograd.gradcheck import gradcheck

    input = (
        torch.randn(1, 2, 8, 5, 5, dtype=torch.float64, requires_grad=True).cuda(),
    )
    module = ConvectionM2(channels=2, parameter_dtype=torch.float64)

    g1 = torch.tensor(
        [[0, 0, 1.0], [0.5, 0, 1.0]], dtype=torch.float64, requires_grad=True
    ).cuda()
    module.g0 = torch.nn.Parameter(g1)
    assert gradcheck(module, input, atol=1e-3)

    g2 = torch.tensor(
        [[0, 1.0, 0], [0.5, 1.0, 0.3]], dtype=torch.float64, requires_grad=True
    ).cuda()
    module.g0 = torch.nn.Parameter(g2)
    assert gradcheck(module, input, atol=1e-3)

    g3 = torch.tensor(
        [[1.0, 0, 0], [1.1, -0.3, 2.1]], dtype=torch.float64, requires_grad=True
    ).cuda()
    module.g0 = torch.nn.Parameter(g3)
    assert gradcheck(module, input, atol=1e-3)

    g4 = torch.tensor(
        [[0, 1.0, 1.0], [0.5, 0.00001, 1.0]], dtype=torch.float64, requires_grad=True
    ).cuda()
    module.g0 = torch.nn.Parameter(g4)
    assert gradcheck(module, input, atol=1e-3)

    g5 = torch.tensor(
        [[10.0, 0, 1.0], [-1.4, 0, -5.0]], dtype=torch.float64, requires_grad=True
    ).cuda()
    module.g0 = torch.nn.Parameter(g5)
    assert gradcheck(module, input, atol=1e-3)

    input2 = (
        torch.randn(1, 1, 4, 2, 2, dtype=torch.float64, requires_grad=True).cuda(),
        torch.tensor([[0.1, 0.1, 0.1]], dtype=torch.float64, requires_grad=True).cuda(),
    )
    assert gradcheck(convection_m2, input2, atol=1e-3)

    input3 = (
        torch.randn(1, 3, 8, 5, 5, dtype=torch.float64, requires_grad=True).cuda(),
        torch.tensor(
            [[0.2, 0.5, 0.5], [-1.9, 1.2, 1.2], [10.1, -1.1, -1.2]],
            dtype=torch.float64,
            requires_grad=True,
        ).cuda(),
    )
    assert gradcheck(convection_m2, input3, atol=1e-3)


def test_m2_lift_shape():
    x = torch.randn(2, 3, 100, 200)
    module = lietorch.nn.m2.LiftM2Cartesian(
        3, 4, orientations=8, kernel_size=5, spline_order=2
    )
    os1 = module(x)
    os2 = lietorch.nn.m2.lift_m2_cartesian(
        x, module.weights, orientations=8, spline_order=2
    )

    assert os1.shape == os2.shape == (2, 4, 8, 100 - 4, 200 - 4)
    assert (os1 - os2).abs().max() < 1e-8

def test_m2_cakewavelet_lift_shape():
    B, C, H, W = 2, 3, 100, 200
    Or = 8
    x = torch.randn(B, C, H, W)
    module = lietorch.nn.m2.LiftM2Cakewavelets(
        C, orientations=Or
    )
    os1 = module(x)

    cws_F = lietorch.nn.m2.cakewavelet_stack_fourier(min(x.shape[-2:]), Or)
    os2 = lietorch.nn.m2.lift_m2_cakewavelets(
        x, cws_F
    )

    assert os1.shape == os2.shape == (B, C, Or, H, W)
    assert (os1 - os2).abs().max() < 1e-8

def test_m2_reconstruction():
    B, C, H, W = 1, 1, 64, 64
    Or = 8
    x = torch.randn(B, C, H, W)
    # Remove high frequencies, then reconstruction is "exact"
    # (Not really because M_psi is not a perfect indicator on B_rho)
    rho_cutoff = 0.5
    ys, xs = torch.meshgrid(torch.linspace(-1., 1., W), torch.linspace(-1., 1., W), indexing="ij")
    high_frequency = ((xs**2 + ys**2) >= rho_cutoff**2)[None, None, ...]
    x_hat = torch.fft.fftshift(torch.fft.fft2(x), dim=(-2, -1))
    x_hat[high_frequency] = 0.
    x = torch.fft.ifft2(torch.fft.ifftshift(x_hat, dim=(-2, -1))).real

    module = lietorch.nn.m2.LiftM2Cakewavelets(
        C, orientations=Or, mn_order=16
    )
    os1 = module(x)
    assert (os1.sum(-3) - x).abs().max() < 1e-3

    cws_F = lietorch.nn.m2.cakewavelet_stack_fourier(min(x.shape[-2:]), Or, mn_order=16)
    os2 = lietorch.nn.m2.lift_m2_cakewavelets(
        x, cws_F
    )
    assert (os2.sum(-3) - x).abs().max() < 1e-3

def test_maxproject():
    # test forward
    a = torch.tensor([[[1, 2], [3, 4]]]).float().requires_grad_()
    expected = torch.tensor([[2, 4]]).float()

    compare = lietorch.nn.m2.max_project_m2(a) == expected
    assert compare.all().item()

    # test backward
    torch.autograd.gradcheck(lietorch.nn.m2.max_project_m2, a.double())

    # test modular interface
    module = lietorch.nn.m2.MaxProjectM2()
    compare = module(a) == expected
    assert compare.all().item()

    # test backward
    torch.autograd.gradcheck(module, a.double())


def test_reflectionpadding():
    a = torch.tensor([[[[[1.0, 2.0], [3.0, 4.0]], [[5.0, 6.0], [7.0, 8.0]]]]])
    b = torch.tensor(
        [
            [
                [
                    [
                        [4.0, 3.0, 3.0, 4.0, 4.0, 3.0],
                        [2.0, 1.0, 1.0, 2.0, 2.0, 1.0],
                        [2.0, 1.0, 1.0, 2.0, 2.0, 1.0],
                        [4.0, 3.0, 3.0, 4.0, 4.0, 3.0],
                        [4.0, 3.0, 3.0, 4.0, 4.0, 3.0],
                        [2.0, 1.0, 1.0, 2.0, 2.0, 1.0],
                    ],
                    [
                        [8.0, 7.0, 7.0, 8.0, 8.0, 7.0],
                        [6.0, 5.0, 5.0, 6.0, 6.0, 5.0],
                        [6.0, 5.0, 5.0, 6.0, 6.0, 5.0],
                        [8.0, 7.0, 7.0, 8.0, 8.0, 7.0],
                        [8.0, 7.0, 7.0, 8.0, 8.0, 7.0],
                        [6.0, 5.0, 5.0, 6.0, 6.0, 5.0],
                    ],
                ]
            ]
        ]
    )

    assert (lietorch.nn.m2.reflection_pad_m2(a, 2) == b).all().item()

def test_linear_convolution_m2_cpu_linear_delta():
    from lietorch.nn.functional import linear_convolution_m2

    input = torch.randn(2, 2, 8, 7, 7, requires_grad=True, dtype=torch.float64)
    kernel = torch.ones(2, 1, 1, 1, requires_grad=True, dtype=torch.float64)

    assert (linear_convolution_m2(input, kernel) == input).all().item()

    kernel = torch.zeros(2, 3, 3, 3, requires_grad=False, dtype=torch.float64)
    kernel[:, 1, 1, 1] += 1

    assert (linear_convolution_m2(input, kernel) == input).all().item()

    kernel = torch.zeros(2, 5, 5, 5, requires_grad=False, dtype=torch.float64)
    kernel[:, 2, 2, 2] += 1

    assert (linear_convolution_m2(input, kernel) == input).all().item()

    kernel = torch.zeros(2, 9, 9, 9, requires_grad=False, dtype=torch.float64)
    kernel[:, 4, 4, 4] += 1

    assert (linear_convolution_m2(input, kernel) == input).all().item()

def test_linear_convolution_m2_cuda_linear_delta():
    from lietorch.nn.functional import linear_convolution_m2

    input = torch.randn(2, 2, 8, 7, 7, requires_grad=True, dtype=torch.float64).cuda()
    kernel = torch.ones(2, 1, 1, 1, requires_grad=True, dtype=torch.float64).cuda()

    assert (linear_convolution_m2(input, kernel) == input).all().item()

    kernel = torch.zeros(2, 3, 3, 3, requires_grad=False, dtype=torch.float64).cuda()
    kernel[:, 1, 1, 1] += 1

    assert (linear_convolution_m2(input, kernel) == input).all().item()

    kernel = torch.zeros(2, 5, 5, 5, requires_grad=False, dtype=torch.float64).cuda()
    kernel[:, 2, 2, 2] += 1

    assert (linear_convolution_m2(input, kernel) == input).all().item()

    kernel = torch.zeros(2, 9, 9, 9, requires_grad=False, dtype=torch.float64).cuda()
    kernel[:, 4, 4, 4] += 1

    assert (linear_convolution_m2(input, kernel) == input).all().item()

def test_linear_convolution_m2_cpu_and_cuda_compare():
    from lietorch.nn.functional import linear_convolution_m2

    input = torch.randn(2, 2, 8, 7, 7, requires_grad=True, dtype=torch.float64)
    kernel = torch.randn(2, 3, 3, 3, requires_grad=True, dtype=torch.float64)

    output_cpu = linear_convolution_m2(input, kernel)

    input = input.cuda()
    kernel = kernel.cuda()
    
    output_cuda = linear_convolution_m2(input, kernel)

    assert output_cpu.allclose(output_cuda.cpu())

def test_linear_convolution_m2_cpu_autograd():
    from lietorch.nn import LinearConvolutionM2
    from lietorch.nn.functional import linear_convolution_m2
    from torch.autograd.gradcheck import gradcheck

    input = torch.randn(2, 2, 8, 7, 7, requires_grad=True, dtype=torch.float64)
    kernel = torch.randn(2, 3, 3, 3, requires_grad=True, dtype=torch.float64)

    assert gradcheck(linear_convolution_m2, (input, kernel), atol=1e-4)

    module = LinearConvolutionM2(channels=2, kernel_size=(2, 2, 2)).double()

    assert gradcheck(module, input, atol=1e-3, nondet_tol=1e-3)

def test_linear_convolution_m2_cuda_autograd():
    from lietorch.nn import LinearConvolutionM2
    from lietorch.nn.functional import linear_convolution_m2
    from torch.autograd.gradcheck import gradcheck

    input = torch.randn(2, 2, 8, 7, 7, requires_grad=True, dtype=torch.float64).cuda()
    kernel = torch.randn(2, 3, 3, 3, requires_grad=True, dtype=torch.float64).cuda()

    assert gradcheck(linear_convolution_m2, (input, kernel), atol=1e-4)

    module = LinearConvolutionM2(channels=2, kernel_size=(2, 2, 2)).double().cuda()

    assert gradcheck(module, input, atol=1e-3, nondet_tol=1e-3)

def test_linear_convolution_m2_permute():
    from lietorch.nn.functional import linear_convolution_m2

    B, C, O, H, W = 2, 3, 8, 5, 7

    kO, kH, kW = 3, 4, 5

    input = torch.randn(W, H, O, C, B, requires_grad=True, dtype=torch.float64)
    kernel = torch.randn(kW, kH, kO, C, requires_grad=True, dtype=torch.float64)

    input = input.permute(4, 3, 2, 1 ,0)
    kernel = kernel.permute(3, 2, 1, 0)

    output_cpu = linear_convolution_m2(input, kernel)

    input = input.cuda()
    kernel = kernel.cuda()
    
    output_cuda = linear_convolution_m2(input, kernel)

    assert output_cpu.allclose(output_cuda.cpu())

def test_morphological_convolution_m2_cpu_morphological_delta():
    from lietorch.nn.functional import morphological_convolution_m2

    input = torch.randn(2, 2, 8, 7, 7, requires_grad=True, dtype=torch.float64)
    kernel = torch.zeros(2, 1, 1, 1, requires_grad=True, dtype=torch.float64)

    assert (morphological_convolution_m2(input, kernel) == input).all().item()

    kernel = torch.full((2, 3, 3, 3), float('Inf'), requires_grad=False, dtype=torch.float64)
    kernel[:, 1, 1, 1] = 0

    assert (morphological_convolution_m2(input, kernel) == input).all().item()

    kernel = torch.full((2, 5, 5, 5), float('Inf'), requires_grad=False, dtype=torch.float64)
    kernel[:, 2, 2, 2] = 0

    assert (morphological_convolution_m2(input, kernel) == input).all().item()

    kernel = torch.full((2, 9, 9, 9), float('Inf'), requires_grad=False, dtype=torch.float64)
    kernel[:, 4, 4, 4] = 0

    assert (morphological_convolution_m2(input, kernel) == input).all().item()

def test_morphological_convolution_m2_cuda_morphological_delta():
    from lietorch.nn.functional import morphological_convolution_m2

    input = torch.randn(2, 2, 8, 7, 7, requires_grad=True, dtype=torch.float64).cuda()
    kernel = torch.zeros(2, 1, 1, 1, requires_grad=True, dtype=torch.float64).cuda()

    assert (morphological_convolution_m2(input, kernel) == input).all().item()

    kernel = torch.full((2, 3, 3, 3), float('Inf'), requires_grad=False, dtype=torch.float64).cuda()
    kernel[:, 1, 1, 1] = 0

    assert (morphological_convolution_m2(input, kernel) == input).all().item()

    kernel = torch.full((2, 5, 5, 5), float('Inf'), requires_grad=False, dtype=torch.float64).cuda()
    kernel[:, 2, 2, 2] = 0

    assert (morphological_convolution_m2(input, kernel) == input).all().item()

    kernel = torch.full((2, 9, 9, 9), float('Inf'), requires_grad=False, dtype=torch.float64).cuda()
    kernel[:, 4, 4, 4] = 0

    assert (morphological_convolution_m2(input, kernel) == input).all().item()

def test_morphological_convolution_m2_cpu_and_cuda_compare():
    from lietorch.nn.functional import morphological_convolution_m2

    input = torch.randn(2, 2, 8, 7, 7, requires_grad=True, dtype=torch.float64)
    kernel = torch.randn(2, 3, 3, 3, requires_grad=True, dtype=torch.float64)

    output_cpu = morphological_convolution_m2(input, kernel)

    input = input.cuda()
    kernel = kernel.cuda()
    
    output_cuda = morphological_convolution_m2(input, kernel)

    assert output_cpu.allclose(output_cuda.cpu())

def test_morphological_convolution_m2_cpu_autograd():
    from lietorch.nn import MorphologicalConvolutionM2
    from lietorch.nn.functional import morphological_convolution_m2
    from torch.autograd.gradcheck import gradcheck

    input = torch.randn(2, 2, 8, 7, 7, requires_grad=True, dtype=torch.float64)
    kernel = torch.randn(2, 3, 3, 3, requires_grad=True, dtype=torch.float64)

    assert gradcheck(morphological_convolution_m2, (input, kernel), atol=1e-4)

    module = MorphologicalConvolutionM2(channels=2, kernel_size=(2, 2, 2))

    assert gradcheck(module, input, atol=1e-4)

def test_morphological_convolution_m2_cuda_autograd():
    from lietorch.nn import MorphologicalConvolutionM2
    from lietorch.nn.functional import morphological_convolution_m2
    from torch.autograd.gradcheck import gradcheck

    input = torch.randn(2, 2, 8, 7, 7, requires_grad=True, dtype=torch.float64).cuda()
    kernel = torch.randn(2, 3, 3, 3, requires_grad=True, dtype=torch.float64).cuda()

    assert gradcheck(morphological_convolution_m2, (input, kernel), atol=1e-4)

    module = MorphologicalConvolutionM2(channels=2, kernel_size=(2, 2, 2)).cuda()

    assert gradcheck(module, input, atol=1e-4)


def test_morphological_convolution_m2_permute():
    from lietorch.nn.functional import morphological_convolution_m2

    B, C, O, H, W = 2, 3, 8, 5, 7

    kO, kH, kW = 3, 4, 5

    input = torch.randn(W, H, O, C, B, requires_grad=True, dtype=torch.float64)
    kernel = torch.randn(kW, kH, kO, C, requires_grad=True, dtype=torch.float64)

    input = input.permute(4, 3, 2, 1 ,0)
    kernel = kernel.permute(3, 2, 1, 0)

    output_cpu = morphological_convolution_m2(input, kernel)

    input = input.cuda()
    kernel = kernel.cuda()
    
    output_cuda = morphological_convolution_m2(input, kernel)

    assert output_cpu.allclose(output_cuda.cpu())


def test_logarithmic_metric_estimate():
    import torch
    from torch.autograd.gradcheck import gradcheck

    rho = torch.ops.lietorch.m2_logarithmic_metric_estimate

    params = torch.rand([2, 4, 3], dtype=torch.float64, requires_grad=True)

    assert gradcheck(rho, (params, [5, 5, 5], 8), atol=1e-4)
    assert gradcheck(rho, (params.cuda(), [5, 5, 5], 8), atol=1e-4)

    assert gradcheck(rho, (params, [4, 4, 4], 8), atol=1e-4)
    assert gradcheck(rho, (params.cuda(), [4, 4, 4], 8), atol=1e-4)


def test_morphological_kernel():
    import torch
    from torch.autograd.gradcheck import gradcheck

    kf = torch.ops.lietorch.m2_morphological_kernel

    params = torch.rand([2, 4, 3], dtype=torch.float64, requires_grad=True)

    k = kf(params, [5, 5, 5], 8, 0.55)
    k = kf(params, [5, 5, 5], 8, 1.0)

    assert gradcheck(kf, (params, [5, 5, 5], 8, 0.55), atol=1e-4)
    assert gradcheck(kf, (params, [5, 5, 5], 8, 1.0), atol=1e-4)


def test_diffusion_kernel():
    import torch
    from torch.autograd.gradcheck import gradcheck

    kf = torch.ops.lietorch.m2_diffusion_kernel

    params = torch.rand([2, 4, 3], dtype=torch.float64, requires_grad=True)

    k = kf(
        torch.tensor(
            [[1, 1, 0.5], [0.5, 2.0, 0.1]], dtype=torch.float64, requires_grad=True
        ),
        [5, 5, 5],
        8,
    )

    assert (k.sum([-3, -2, -1]) - 1).abs().max() < 1e-8

    assert gradcheck(kf, (params, [5, 5, 5], 8))
    assert gradcheck(kf, (params, [6, 6, 6], 7))


def test_fractional_dilation():
    import torch
    from torch.autograd.gradcheck import gradcheck
    from lietorch.nn.functional import fractional_dilation_m2
    from lietorch.nn import FractionalDilationM2

    x = torch.randn([2, 2, 8, 5, 5], dtype=torch.float64, requires_grad=True)
    p = torch.rand([2, 3], dtype=torch.float64, requires_grad=True)

    assert gradcheck(fractional_dilation_m2, (x, p, [3, 3, 3], 0.55), atol=1e-4)
    assert gradcheck(fractional_dilation_m2, (x, p, [4, 4, 4], 1.0), atol=1e-4)

    xc = x.cuda()
    pc = p.cuda()

    assert gradcheck(fractional_dilation_m2, (xc, pc, [3, 3, 3], 0.55), atol=1e-4)
    assert gradcheck(fractional_dilation_m2, (xc, pc, [4, 4, 4], 1.0), atol=1e-4)

    module = FractionalDilationM2(2, [2, 2, 2], alpha=0.7)

    assert gradcheck(module, (x,), atol=1e-4)
    assert gradcheck(module.cuda(), (x.cuda(),), atol=1e-4)


def test_fractional_erosion():
    import torch
    from torch.autograd.gradcheck import gradcheck
    from lietorch.nn.functional import fractional_erosion_m2
    from lietorch.nn import FractionalErosionM2

    x = torch.randn([2, 2, 8, 5, 5], dtype=torch.float64, requires_grad=True)
    p = torch.rand([2, 3], dtype=torch.float64, requires_grad=True)

    assert gradcheck(fractional_erosion_m2, (x, p, [3, 3, 3], 0.55), atol=1e-4)
    assert gradcheck(fractional_erosion_m2, (x, p, [4, 4, 4], 1.0), atol=1e-4)

    xc = x.cuda()
    pc = p.cuda()

    assert gradcheck(fractional_erosion_m2, (xc, pc, [3, 3, 3], 0.55), atol=1e-4)
    assert gradcheck(fractional_erosion_m2, (xc, pc, [4, 4, 4], 1.0), atol=1e-4)

    module = FractionalErosionM2(2, [2, 2, 2], alpha=0.7)

    assert gradcheck(module, (x,), atol=1e-4)
    assert gradcheck(module.cuda(), (x.cuda(),), atol=1e-4)


def test_linear():
    import torch
    from torch.autograd.gradcheck import gradcheck
    from lietorch.nn.functional import linear_m2
    from lietorch.nn import LinearM2

    a = torch.tensor([[[[[1, 1], [1, 1]]]]], dtype=torch.float64)
    v = torch.tensor([[2, 3]], dtype=torch.float64)
    b = linear_m2(a, v)
    b_exp = torch.tensor(
        [[[[[2, 2], [2, 2]]], [[[3, 3], [3, 3]]]]], dtype=torch.float64
    )
    assert b.allclose(b_exp)
    assert linear_m2(a.cuda(), v.cuda()).allclose(b_exp.cuda())

    x = torch.randn([2, 3, 8, 5, 5], dtype=torch.float64, requires_grad=True)
    w = torch.randn([3, 6], dtype=torch.float64, requires_grad=True)

    assert gradcheck(linear_m2, (x, w), atol=1e-4)
    assert gradcheck(linear_m2, (x.cuda(), w.cuda()), atol=1e-4)

    module = LinearM2(3, 5).double()

    assert gradcheck(module, (x,), atol=1e-4)


def test_convection_dilation_pde():
    from torch.autograd.gradcheck import gradcheck
    from lietorch.nn import ConvectionDilationPdeM2

    x = torch.randn([1, 2, 8, 7, 7], dtype=torch.float64, requires_grad=True)
    module = ConvectionDilationPdeM2(channels=2, kernel_size=[5, 5, 5]).double()
    module2 = ConvectionDilationPdeM2(
        channels=2, kernel_size=[4, 4, 4], alpha_dilation=1.0, iterations=2,
    ).double()

    assert gradcheck(module, (x,), atol=1e-4)
    assert gradcheck(module2, (x,), atol=1e-4)
    assert gradcheck(module.cuda(), (x.cuda(),), atol=1e-4)
    assert gradcheck(module2.cuda(), (x.cuda(),), atol=1e-4)


def test_convection_erosion_pde():
    from torch.autograd.gradcheck import gradcheck
    from lietorch.nn import ConvectionErosionPdeM2

    x = torch.randn([1, 2, 8, 7, 7], dtype=torch.float64, requires_grad=True)
    module = ConvectionErosionPdeM2(channels=2, kernel_size=[5, 5, 5]).double()
    module2 = ConvectionErosionPdeM2(
        channels=2, kernel_size=[4, 4, 4], alpha_erosion=1.0, iterations=2,
    ).double()

    assert gradcheck(module, (x,), atol=1e-4)
    assert gradcheck(module2, (x,), atol=1e-4)
    assert gradcheck(module.cuda(), (x.cuda(),), atol=1e-4)
    assert gradcheck(module2.cuda(), (x.cuda(),), atol=1e-4)


def test_cde_pde_layer():
    from torch.autograd.gradcheck import gradcheck
    from lietorch.nn import CDEPdeLayerM2

    x = torch.randn([1, 2, 4, 5, 5], dtype=torch.float64, requires_grad=True)
    module = CDEPdeLayerM2(
        in_channels=2, out_channels=3, kernel_size=[3, 3, 3]
    ).double()

    assert gradcheck(module, (x,), atol=1e-4)
    assert gradcheck(module.cuda(), (x.cuda(),), atol=1e-4, nondet_tol=1e-4)

