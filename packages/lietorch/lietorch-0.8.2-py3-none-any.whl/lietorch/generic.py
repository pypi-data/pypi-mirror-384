"""
    Generic functions, mainly used for testing purposes.
"""
import torch
import sys


class GenericAddFunction(torch.autograd.Function):
    @staticmethod
    def forward(ctx, a, b):
        return torch.ops.lietorch.generic_add_fw(a, b)

    @staticmethod
    def backward(ctx, grad):
        return torch.ops.lietorch.generic_add_bw(grad)


class GenericAdd(torch.nn.Module):
    def __init__(self):
        super(GenericAdd, self).__init__()

    def forward(self, a, b):
        return GenericAddFunction.apply(a, b)


def grayscale_dilation_2d(image, filter):
    return torch.ops.lietorch.generic_grayscale_dilation_2d(image, filter)


class GrayscaleDilation2D(torch.nn.Module):
    def __init__(self, kernel_size):
        super(GrayscaleDilation2D, self).__init__()
        self._kernel_size = kernel_size

        self._filter = torch.nn.Parameter(torch.empty(kernel_size, kernel_size))

        self.reset_parameters()

    def reset_parameters(self):
        torch.nn.init.xavier_normal_(
            self._filter, gain=torch.nn.init.calculate_gain("relu")
        )

    def forward(self, image):
        return grayscale_dilation_2d(image, self._filter.to(image.dtype))


def grayscale_erosion_2d(image, filter):
    return torch.ops.lietorch.generic_grayscale_erosion_2d(image, filter)


class GrayscaleErosion2D(torch.nn.Module):
    def __init__(self, kernel_size):
        super(GrayscaleErosion2D, self).__init__()
        self._kernel_size = kernel_size

        self._filter = torch.nn.Parameter(torch.empty(kernel_size, kernel_size))

        self.reset_parameters()

    def reset_parameters(self):
        torch.nn.init.xavier_normal_(
            self._filter, gain=torch.nn.init.calculate_gain("relu")
        )

    def forward(self, image):
        return grayscale_erosion_2d(image, self._filter.to(image.dtype))
