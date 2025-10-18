import sys, os

sys.path.append(".")
sys.path.append("..")
import lietorch
import torch
import matplotlib.pyplot as plt

RNG_SEED = 0

if RNG_SEED:
    torch.manual_seed(RNG_SEED)

torch.backends.cudnn.enabled = False
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False


def test_dilation_2d_flat_cpu():
    a = torch.tensor(
        [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 1, 3, 1, 0, 0],
            [0, 0, 1, 1, 1, 0, 0],
            [0, 0, 1, 1, 2, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ]
    ).float()
    b = torch.zeros(3, 3).float()

    c_expected = torch.tensor(
        [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 1, 3, 3, 3, 1, 0],
            [0, 1, 3, 3, 3, 1, 0],
            [0, 1, 3, 3, 3, 2, 0],
            [0, 1, 1, 2, 2, 2, 0],
            [0, 1, 1, 2, 2, 2, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ]
    ).float()

    c_actual = lietorch.generic.grayscale_dilation_2d(a, b)

    assert c_actual.allclose(c_expected)


def test_dilation_2d_flat_cuda():
    a = (
        torch.tensor(
            [
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 1, 3, 1, 0, 0],
                [0, 0, 1, 1, 1, 0, 0],
                [0, 0, 1, 1, 2, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
            ]
        )
        .float()
        .cuda()
    )
    b = torch.zeros(3, 3).float().cuda()

    c_expected = (
        torch.tensor(
            [
                [0, 0, 0, 0, 0, 0, 0],
                [0, 1, 3, 3, 3, 1, 0],
                [0, 1, 3, 3, 3, 1, 0],
                [0, 1, 3, 3, 3, 2, 0],
                [0, 1, 1, 2, 2, 2, 0],
                [0, 1, 1, 2, 2, 2, 0],
                [0, 0, 0, 0, 0, 0, 0],
            ]
        )
        .float()
        .cuda()
    )

    c_actual = lietorch.generic.grayscale_dilation_2d(a, b)

    assert c_actual.allclose(c_expected)


def test_dilation_2d_compare():
    a = torch.randn(100, 100)
    b = torch.randn(5, 5)
    ac = a.cuda()
    bc = b.cuda()

    out_cpu = lietorch.generic.grayscale_dilation_2d(a, b)
    out_cuda = lietorch.generic.grayscale_dilation_2d(ac, bc)

    assert out_cpu.allclose(out_cuda.cpu())


def test_dilation_2d_autograd_cpu():
    from lietorch.generic import GrayscaleDilation2D
    from torch.autograd.gradcheck import gradcheck

    torch.manual_seed(RNG_SEED)
    torch.backends.cudnn.enabled = False
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

    input = [
        torch.randn(20, 20, dtype=torch.float64, requires_grad=True),
    ]

    assert gradcheck(
        GrayscaleDilation2D(kernel_size=5), input, rtol=1e-3, nondet_tol=1e-3
    )


def test_dilation_2d_autograd_cuda():
    from lietorch.generic import GrayscaleDilation2D
    from torch.autograd.gradcheck import gradcheck

    torch.manual_seed(RNG_SEED)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

    input = [
        torch.randn(20, 20, dtype=torch.float64, requires_grad=True).cuda(),
    ]

    assert gradcheck(
        GrayscaleDilation2D(kernel_size=5).cuda(), input, rtol=1e-3, nondet_tol=1e-3
    )


def test_erosion_2d_flat_cpu():
    a = torch.tensor(
        [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 3, 3, 3, 3, 3, 0],
            [0, 3, 3, 1, 3, 3, 0],
            [0, 3, 3, 3, 3, 3, 0],
            [0, 3, 3, 3, 2, 3, 0],
            [0, 3, 3, 3, 3, 3, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ]
    ).float()
    b = torch.zeros(3, 3).float()

    c_expected = torch.tensor(
        [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 1, 1, 1, 0, 0],
            [0, 0, 1, 1, 1, 0, 0],
            [0, 0, 3, 2, 2, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ]
    ).float()

    c_actual = lietorch.generic.grayscale_erosion_2d(a, b)

    assert c_actual.allclose(c_expected)


def test_erosion_2d_flat_cuda():
    a = (
        torch.tensor(
            [
                [0, 0, 0, 0, 0, 0, 0],
                [0, 3, 3, 3, 3, 3, 0],
                [0, 3, 3, 1, 3, 3, 0],
                [0, 3, 3, 3, 3, 3, 0],
                [0, 3, 3, 3, 2, 3, 0],
                [0, 3, 3, 3, 3, 3, 0],
                [0, 0, 0, 0, 0, 0, 0],
            ]
        )
        .float()
        .cuda()
    )
    b = torch.zeros(3, 3).float().cuda()

    c_expected = (
        torch.tensor(
            [
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 1, 1, 1, 0, 0],
                [0, 0, 1, 1, 1, 0, 0],
                [0, 0, 3, 2, 2, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
            ]
        )
        .float()
        .cuda()
    )

    c_actual = lietorch.generic.grayscale_erosion_2d(a, b)

    assert c_actual.allclose(c_expected)


def test_erosion_2d_compare():
    a = torch.randn(100, 100)
    b = torch.randn(5, 5)
    ac = a.cuda()
    bc = b.cuda()

    out_cpu = lietorch.generic.grayscale_erosion_2d(a, b)
    out_cuda = lietorch.generic.grayscale_erosion_2d(ac, bc)

    assert out_cpu.allclose(out_cuda.cpu())


def test_erosion_2d_autograd_cpu():
    from lietorch.generic import GrayscaleErosion2D
    from torch.autograd.gradcheck import gradcheck

    torch.manual_seed(RNG_SEED)
    torch.backends.cudnn.enabled = False
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

    input = [
        torch.randn(20, 20, dtype=torch.float64, requires_grad=True),
    ]

    assert gradcheck(
        GrayscaleErosion2D(kernel_size=5), input, rtol=1e-2, nondet_tol=1e-3
    )


def test_erosion_2d_autograd_cuda():
    from lietorch.generic import GrayscaleErosion2D
    from torch.autograd.gradcheck import gradcheck

    torch.manual_seed(RNG_SEED)
    torch.backends.cudnn.enabled = False
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

    input = [
        torch.randn(20, 20, dtype=torch.float64, requires_grad=True).cuda(),
    ]

    assert gradcheck(
        GrayscaleErosion2D(kernel_size=5).cuda(), input, rtol=1e-2, nondet_tol=1e-3
    )


if __name__ == "__main__":
    a = 1 - torch.tensor(plt.imread("./assets/cross.png")).float().mean(-1)
    plt.imshow(a)
    plt.show()
    f = torch.zeros(10, 10).float()
    b, d = torch.ops.lietorch.generic_grayscale_dilation_2d_fw(a, f)
    plt.imshow(b)
    plt.show()
