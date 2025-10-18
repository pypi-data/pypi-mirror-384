"""
Loss functions.
"""

import torch


def dice_loss(input, target, smooth=1):
    """
    Continuous DICE coefficient suitable for use as a loss function for binary segmentation, calculated as:
    $$
        1 - \\frac{2*(input*target).sum()+smooth}{input.sum()+target.sum()+smooth}
    $$

    Parameters
    ------------
    input: torch.Tensor
    Tensor of any shape with scalar elements in the range [0,1].

    target: torch.Tensor
    Label tensor with the same shape as the input with elements in the set {0,1}.

    smooth: float
    Smoothing factor that is added to both the numerator and denominator to avoid divide-by-zero.

    """
    AinterB = (input.view(-1) * target.view(-1)).sum()
    A = input.view(-1).sum()
    B = target.view(-1).sum()
    dice = (2 * AinterB + smooth) / (A + B + smooth)
    return 1 - dice


class DiceLoss(torch.nn.Module):
    """
    Modular interface to `lietorch.nn.loss.dice_loss`
    """

    def __init__(self):
        super().__init__()

    def forward(self, input, target, smooth=1):
        return dice_loss(input, target, smooth)
