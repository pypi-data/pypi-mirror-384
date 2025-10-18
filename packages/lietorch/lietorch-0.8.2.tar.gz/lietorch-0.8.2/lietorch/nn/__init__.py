"""
Functions and modules for implementing geometric neural networks.
"""

import lietorch.nn.functional

from lietorch.nn.m2 import (
    LiftM2Cakewavelets,
    LiftM2Cartesian,
    ReflectionPadM2,
    MaxProjectM2,
    SumProjectM2,
    ConvM2Cartesian,
    AnisotropicDilatedProjectM2,
    ConvectionM2,
    LinearConvolutionM2,
    MorphologicalConvolutionM2,
    FractionalDilationM2,
    FractionalDilationM2NonDiag,
    FractionalErosionM2,
    FractionalErosionM2NonDiag,
    LinearM2,
    DiffusionM2,
    ConvectionDilationPdeM2,
    ConvectionErosionPdeM2,
    CDEPdeLayerM2,
    CDEPdeLayerM2NonDiag,
    DEPdeLayerM2,
    DSPdeLayerM2,
    CDSPdeLayerM2,
    DDEPdeLayerM2,
    CDDEPdeLayerM2,
    SpatialResampleM2,
)

from lietorch.nn.r2 import (
    MorphologicalConvolutionR2,
    FractionalDilationR2,
    FractionalErosionR2,
    LinearR2,
    ConvectionR2,
    DiffusionR2,
    CDEPdeLayerR2Finslerian,
    DEPdeLayerR2Finslerian,
    DDEPdeLayerR2Finslerian,
    CDDEPdeLayerR2Finslerian,
    DSPdeLayerR2Finslerian,
    CDSPdeLayerR2Finslerian,
    CDEPdeLayerR2,
    DDEPdeLayerR2,
    CDDEPdeLayerR2,
    DSPdeLayerR2,
    CDSPdeLayerR2,
    CDEPdeLayerR2Isotropic,
    DDEPdeLayerR2Isotropic,
    CDDEPdeLayerR2Isotropic,
    DSPdeLayerR2Isotropic,
    CDSPdeLayerR2Isotropic,
    SpatialResampleR2,
)

from lietorch.nn.loss import DiceLoss
