import platform, sys, os
import pytest
import torch
import numpy as np

# expecting to find lietorch package in parent directory
sys.path.append("..")
import lietorch

RNG_SEED = 0

if RNG_SEED:
    torch.manual_seed(RNG_SEED)

torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False


def test_generic_add():
    a = torch.randn(100, 200)
    b = torch.randn(100, 200)
    c1 = a + b
    c2 = torch.ops.lietorch.generic_add_fw(a, b)
    assert (c1 - c2).abs().sum().item() < 1e-8

    a = torch.randn(100, 200).cuda()
    b = torch.randn(100, 200).cuda()
    c1 = a + b
    c2 = torch.ops.lietorch.generic_add_fw(a, b)
    assert (c1 - c2).abs().sum().item() < 1e-8


def test_generic_add_autograd():
    from lietorch.generic import GenericAdd
    from torch.autograd.gradcheck import gradcheck

    input = [
        torch.randn(10, 20, dtype=torch.float64, requires_grad=True),
        torch.randn(10, 20, dtype=torch.float64, requires_grad=True),
    ]

    assert gradcheck(GenericAdd(), input)

    input = [
        torch.randn(20, 10, dtype=torch.float64, requires_grad=True).cuda(),
        torch.randn(20, 10, dtype=torch.float64, requires_grad=True).cuda(),
    ]

    assert gradcheck(GenericAdd(), input)


def test_lietorch_backend_init():
    assert lietorch._backend_initialized



if __name__ == "__main__":
    _load_shared_library()
    print(f"PyTorch CUDA version: {torch.version.cuda}")
    print(f"Backend CUDA version: {torch.ops.lietorch._cuda_version()}")
