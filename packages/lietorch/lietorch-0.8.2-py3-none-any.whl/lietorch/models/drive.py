"""
Models used for retinal vessel segmentation on the DRIVE dataset.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

import lietorch.nn as lnn


class BasicSpatialCNN6(nn.Module):
    """
    Basic spatial binary segmentation network with 6 layers.
    """

    def __init__(self, in_channels):
        super(BasicSpatialCNN6, self).__init__()

        track = True
        c = 24
        c_final = 16

        self.conv1 = nn.Sequential(
            nn.ReplicationPad2d(3),
            nn.Conv2d(in_channels, c, 7, bias=False),
            nn.BatchNorm2d(c, track_running_stats=track),
            nn.ReLU(),
        )
        self.conv2 = nn.Sequential(
            nn.ReplicationPad2d(2),
            nn.Conv2d(c, c, 5, bias=False),
            nn.BatchNorm2d(c, track_running_stats=track),
            nn.ReLU(),
            nn.Dropout2d(0.1),
        )
        self.conv3 = nn.Sequential(
            nn.ReplicationPad2d(2),
            nn.Conv2d(c, c, 5, bias=False),
            nn.BatchNorm2d(c, track_running_stats=track),
            nn.ReLU(),
        )
        self.conv4 = nn.Sequential(
            nn.ReplicationPad2d(2),
            nn.Conv2d(c, c, 5, bias=False),
            nn.BatchNorm2d(c, track_running_stats=track),
            nn.ReLU(),
            nn.Dropout2d(0.1),
        )
        self.conv5 = nn.Sequential(
            nn.Conv2d(c, c_final, 1, bias=False),
            nn.BatchNorm2d(c_final, track_running_stats=track),
            nn.ReLU(),
        )
        self.conv6 = nn.Sequential(nn.Conv2d(c_final, 1, 1, bias=False), nn.Sigmoid())

        # init parameters
        def _init_xavier_norm(m):
            if type(m) == torch.nn.Conv2d:
                torch.nn.init.xavier_uniform_(
                    m.weight, gain=torch.nn.init.calculate_gain("relu")
                )

        self.apply(_init_xavier_norm)

    def forward(self, x):
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.conv3(x)
        x = self.conv4(x)
        x = self.conv5(x)
        x = self.conv6(x)
        return x

    def __repr__(self):
        return self.__class__.__name__


class BasicSpatialCNN12(nn.Module):
    """
    Basic spatial binary segmentation network with 12 layers.
    """

    def __init__(self, in_channels):
        super(BasicSpatialCNN12, self).__init__()

        track = True
        c = 24
        c_final = 16

        self.conv1 = nn.Sequential(
            nn.ReplicationPad2d(3),
            nn.Conv2d(in_channels, c, 7, bias=False),
            nn.BatchNorm2d(c, track_running_stats=track),
            nn.ReLU(),
        )
        self.conv2 = nn.Sequential(
            nn.ReplicationPad2d(2),
            nn.Conv2d(c, c, 5, bias=False),
            nn.BatchNorm2d(c, track_running_stats=track),
            nn.ReLU(),
            nn.Dropout2d(0.1),
        )
        self.conv3 = nn.Sequential(
            nn.ReplicationPad2d(2),
            nn.Conv2d(c, c, 5, bias=False),
            nn.BatchNorm2d(c, track_running_stats=track),
            nn.ReLU(),
        )
        self.conv4 = nn.Sequential(
            nn.ReplicationPad2d(2),
            nn.Conv2d(c, c, 5, bias=False),
            nn.BatchNorm2d(c, track_running_stats=track),
            nn.ReLU(),
        )
        self.conv5 = nn.Sequential(
            nn.Conv2d(c, c, 1, bias=False),
            nn.BatchNorm2d(c, track_running_stats=track),
            nn.ReLU(),
        )
        self.conv6 = nn.Sequential(
            nn.ReplicationPad2d(2),
            nn.Conv2d(c, c, 5, bias=False),
            nn.BatchNorm2d(c, track_running_stats=track),
            nn.ReLU(),
            nn.Dropout2d(0.1),
        )
        self.conv7 = nn.Sequential(
            nn.ReplicationPad2d(2),
            nn.Conv2d(c, c, 5, bias=False),
            nn.BatchNorm2d(c, track_running_stats=track),
            nn.ReLU(),
        )
        self.conv8 = nn.Sequential(
            nn.ReplicationPad2d(2),
            nn.Conv2d(c, c, 5, bias=False),
            nn.BatchNorm2d(c, track_running_stats=track),
            nn.ReLU(),
        )
        self.conv9 = nn.Sequential(
            nn.ReplicationPad2d(2),
            nn.Conv2d(c, c, 5, bias=False),
            nn.BatchNorm2d(c, track_running_stats=track),
            nn.ReLU(),
            nn.Dropout2d(0.1),
        )
        self.conv10 = nn.Sequential(
            nn.ReplicationPad2d(2),
            nn.Conv2d(c, c, 5, bias=False),
            nn.BatchNorm2d(c, track_running_stats=track),
            nn.ReLU(),
        )
        self.conv11 = nn.Sequential(
            nn.ReplicationPad2d(2),
            nn.Conv2d(c, c_final, 5, bias=False),
            nn.BatchNorm2d(c_final, track_running_stats=track),
            nn.ReLU(),
        )
        self.conv12 = nn.Sequential(nn.Conv2d(c_final, 1, 1, bias=False), nn.Sigmoid())

        # init parameters
        def _init_xavier_norm(m):
            if type(m) == torch.nn.Conv2d:
                torch.nn.init.xavier_uniform_(
                    m.weight, gain=torch.nn.init.calculate_gain("relu")
                )

        self.apply(_init_xavier_norm)

    def forward(self, x):
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.conv3(x)
        x = self.conv4(x)
        x = self.conv5(x)
        x = self.conv6(x)
        x = self.conv7(x)
        x = self.conv8(x)
        x = self.conv9(x)
        x = self.conv10(x)
        x = self.conv11(x)
        x = self.conv12(x)
        return x

    def __repr__(self):
        return self.__class__.__name__


class BasicGroupCNN6(nn.Module):
    """
    Basic 2D roto-translation equivariant binary segmentation network with 6
    layers.
    """

    def __init__(self, in_channels):
        super(BasicGroupCNN6, self).__init__()

        track = True
        c = 16
        c_final = 16

        self.lift = nn.Sequential(
            nn.ReflectionPad2d(3),
            lnn.LiftM2Cartesian(
                in_channels=in_channels, out_channels=c, orientations=8, kernel_size=7
            ),
            nn.BatchNorm3d(c, track_running_stats=track),
            nn.ReLU(),
        )
        self.conv1 = nn.Sequential(
            lnn.ReflectionPadM2(padding=2),
            lnn.ConvM2Cartesian(c, c, 8, 5),
            nn.BatchNorm3d(c, track_running_stats=track),
            nn.ReLU(),
            nn.Dropout3d(0.1),
        )
        self.conv2 = nn.Sequential(
            lnn.ReflectionPadM2(2),
            lnn.ConvM2Cartesian(c, c, 8, 5),
            nn.BatchNorm3d(c, track_running_stats=track),
            nn.ReLU(),
        )
        self.conv3 = nn.Sequential(
            lnn.ReflectionPadM2(2),
            lnn.ConvM2Cartesian(c, c, 8, 5),
            nn.BatchNorm3d(c, track_running_stats=track),
            nn.ReLU(),
            nn.Dropout3d(0.1),
        )
        self.conv4 = nn.Sequential(
            lnn.ConvM2Cartesian(c, c_final, 8, 1),
            nn.BatchNorm3d(c_final, track_running_stats=track),
            nn.ReLU(),
        )
        self.project = lnn.MaxProjectM2()
        self.convfinal = nn.Sequential(
            nn.Conv2d(c_final, 1, 1, bias=False), nn.Sigmoid()
        )

    def forward(self, x):
        x = self.lift(x)
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.conv3(x)
        x = self.conv4(x)
        x = self.convfinal(self.project(x))
        return x

    def __repr__(self):
        return self.__class__.__name__


class FixedLiftGroupCNN6(nn.Module):
    """
    Basic 2D roto-translation equivariant binary segmentation network with 6
    layers.
    """

    def __init__(self, in_channels):
        super(FixedLiftGroupCNN6, self).__init__()

        track = True
        c = 16
        c_final = 16

        self.lift = nn.Sequential(
            lnn.LiftM2Cakewavelets(in_channels=in_channels, orientations=8),
            lnn.LinearM2(in_channels=in_channels, out_channels=c),
            lnn.ConvectionM2(c),
            nn.BatchNorm3d(c, track_running_stats=True),
        )
        self.conv1 = nn.Sequential(
            lnn.ReflectionPadM2(padding=2),
            lnn.ConvM2Cartesian(c, c, 8, 5),
            nn.BatchNorm3d(c, track_running_stats=track),
            nn.ReLU(),
            nn.Dropout3d(0.1),
        )
        self.conv2 = nn.Sequential(
            lnn.ReflectionPadM2(2),
            lnn.ConvM2Cartesian(c, c, 8, 5),
            nn.BatchNorm3d(c, track_running_stats=track),
            nn.ReLU(),
        )
        self.conv3 = nn.Sequential(
            lnn.ReflectionPadM2(2),
            lnn.ConvM2Cartesian(c, c, 8, 5),
            nn.BatchNorm3d(c, track_running_stats=track),
            nn.ReLU(),
            nn.Dropout3d(0.1),
        )
        self.conv4 = nn.Sequential(
            lnn.ConvM2Cartesian(c, c_final, 8, 1),
            nn.BatchNorm3d(c_final, track_running_stats=track),
            nn.ReLU(),
        )
        self.project = lnn.MaxProjectM2()
        self.convfinal = nn.Sequential(
            nn.Conv2d(c_final, 1, 1, bias=False), nn.Sigmoid()
        )

    def forward(self, x):
        x = self.lift(x)
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.conv3(x)
        x = self.conv4(x)
        x = self.convfinal(self.project(x))
        return x

    def __repr__(self):
        return self.__class__.__name__


class BasicGroupCNN12(nn.Module):
    """
    Basic 2D roto-translation equivariant binary segmentation network with 12 layers.
    """

    def __init__(self, in_channels):
        super(BasicGroupCNN12, self).__init__()

        track = True
        c = 10
        c_final = 16

        self.lift = nn.Sequential(
            nn.ReflectionPad2d(3),
            lnn.LiftM2Cartesian(
                in_channels=in_channels, out_channels=c, orientations=8, kernel_size=7
            ),
            nn.BatchNorm3d(c, track_running_stats=track),
            nn.ReLU(),
        )
        self.conv1 = nn.Sequential(
            lnn.ReflectionPadM2(padding=2),
            lnn.ConvM2Cartesian(c, c, 8, 5),
            nn.BatchNorm3d(c, track_running_stats=track),
            nn.ReLU(),
            nn.Dropout3d(0.1),
        )
        self.conv2 = nn.Sequential(
            lnn.ReflectionPadM2(2),
            lnn.ConvM2Cartesian(c, c, 8, 5),
            nn.BatchNorm3d(c, track_running_stats=track),
            nn.ReLU(),
        )
        self.conv3 = nn.Sequential(
            lnn.ReflectionPadM2(2),
            lnn.ConvM2Cartesian(c, c, 8, 5),
            nn.BatchNorm3d(c, track_running_stats=track),
            nn.ReLU(),
        )
        self.conv4 = nn.Sequential(
            lnn.ReflectionPadM2(2),
            lnn.ConvM2Cartesian(c, c, 8, 5),
            nn.BatchNorm3d(c, track_running_stats=track),
            nn.ReLU(),
        )
        self.conv5 = nn.Sequential(
            lnn.ReflectionPadM2(2),
            lnn.ConvM2Cartesian(c, c, 8, 5),
            nn.BatchNorm3d(c, track_running_stats=track),
            nn.ReLU(),
            nn.Dropout3d(0.1),
        )
        self.conv6 = nn.Sequential(
            lnn.ReflectionPadM2(2),
            lnn.ConvM2Cartesian(c, c, 8, 5),
            nn.BatchNorm3d(c, track_running_stats=track),
            nn.ReLU(),
        )
        self.conv7 = nn.Sequential(
            lnn.ReflectionPadM2(2),
            lnn.ConvM2Cartesian(c, c, 8, 5),
            nn.BatchNorm3d(c, track_running_stats=track),
            nn.ReLU(),
        )
        self.conv8 = nn.Sequential(
            lnn.ReflectionPadM2(2),
            lnn.ConvM2Cartesian(c, c, 8, 5),
            nn.BatchNorm3d(c, track_running_stats=track),
            nn.ReLU(),
        )
        self.conv9 = nn.Sequential(
            lnn.ReflectionPadM2(2),
            lnn.ConvM2Cartesian(c, c, 8, 5),
            nn.BatchNorm3d(c, track_running_stats=track),
            nn.ReLU(),
        )
        self.conv10 = nn.Sequential(
            lnn.ConvM2Cartesian(c, c_final, 8, 1),
            nn.BatchNorm3d(c_final, track_running_stats=track),
            nn.ReLU(),
        )
        self.project = lnn.MaxProjectM2()
        self.convfinal = nn.Sequential(
            nn.Conv2d(c_final, 1, 1, bias=False), nn.Sigmoid()
        )

    def forward(self, x):
        x = self.lift(x)
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.conv3(x)
        x = self.conv4(x)
        x = self.conv5(x)
        x = self.conv6(x)
        x = self.conv7(x)
        x = self.conv8(x)
        x = self.conv9(x)
        x = self.conv10(x)
        x = self.convfinal(self.project(x))
        return x

    def __repr__(self):
        return self.__class__.__name__


class CDEPdeNN6(nn.Module):
    """
    Basic Convection-Dilation-Eriosion PDE-G-CNN binary segmentation network with 6 layers.
    """

    def __init__(self, in_channels):
        super(CDEPdeNN6, self).__init__()

        its = 1
        kernel_size = [5, 5, 5]
        c = 16
        c_final = 16
        alpha = 0.65

        self.lift = nn.Sequential(
            nn.ReflectionPad2d(3),
            lnn.LiftM2Cartesian(
                in_channels=in_channels, out_channels=c, orientations=8, kernel_size=7
            ),
            nn.BatchNorm3d(c, track_running_stats=True),
        )
        self.pde = nn.Sequential(
            lnn.CDEPdeLayerM2(c, c, kernel_size, its, alpha),
            nn.Dropout3d(0.1),
            lnn.CDEPdeLayerM2(c, c, kernel_size, its, alpha),
            lnn.CDEPdeLayerM2(c, c, kernel_size, its, alpha),
            lnn.CDEPdeLayerM2(c, c_final, kernel_size, its, alpha),
        )
        self.project = lnn.MaxProjectM2()
        self.final = nn.Sequential(
            nn.Conv2d(c_final, 1, 1, bias=False),
            nn.Sigmoid(),
        )

    def forward(self, x):
        x = self.lift(x)
        x = self.pde(x)
        x = self.project(x)
        x = self.final(x)
        return x

    def __repr__(self):
        return self.__class__.__name__


class CDEPdeNN6NonDiag(nn.Module):
    """
    Basic Non-Diagonal Convection-Dilation-Eriosion PDE-G-CNN binary segmentation network with 6 layers.
    """

    def __init__(self, in_channels):
        super(CDEPdeNN6NonDiag, self).__init__()

        its = 1
        kernel_size = [5, 5, 5]
        c = 16
        c_final = 16
        alpha = 0.65

        self.lift = nn.Sequential(
            nn.ReflectionPad2d(3),
            lnn.LiftM2Cartesian(
                in_channels=in_channels, out_channels=c, orientations=8, kernel_size=7
            ),
            nn.BatchNorm3d(c, track_running_stats=True),
        )
        self.pde = nn.Sequential(
            lnn.CDEPdeLayerM2NonDiag(c, c, kernel_size, its, alpha),
            nn.Dropout3d(0.1),
            lnn.CDEPdeLayerM2NonDiag(c, c, kernel_size, its, alpha),
            lnn.CDEPdeLayerM2NonDiag(c, c, kernel_size, its, alpha),
            lnn.CDEPdeLayerM2NonDiag(c, c_final, kernel_size, its, alpha),
        )
        self.project = lnn.MaxProjectM2()
        self.final = nn.Sequential(
            nn.Conv2d(c_final, 1, 1, bias=False),
            nn.Sigmoid(),
        )

    def forward(self, x):
        x = self.lift(x)
        x = self.pde(x)
        x = self.project(x)
        x = self.final(x)
        return x

    def __repr__(self):
        return self.__class__.__name__


class FixedLiftCDEPdeNN6(nn.Module):
    """
    Convection-Dilation-Erosion PDE-G-CNN binary segmentation network with
    6 layers with untrained lift.
    """

    def __init__(self, in_channels):
        super(FixedLiftCDEPdeNN6, self).__init__()

        kernel_size = [5, 5, 5]
        its = 1
        c = 16
        c_convections = 32
        c_final = 16
        alpha = 0.65

        # Training the lift is in theory equivalent to fixing the lift and
        # subsequently applying trained convections, see
        # "Geometric Adaptations of PDE-G-CNNs" by Gijs Bellaard et al. (2023),
        # https://doi.org/10.1007/978-3-031-31975-4_41
        self.lift = nn.Sequential(
            lnn.LiftM2Cakewavelets(in_channels=in_channels, orientations=8),
            lnn.LinearM2(in_channels=in_channels, out_channels=c_convections),
            lnn.ConvectionM2(c_convections),
            nn.BatchNorm3d(c_convections, track_running_stats=True),
        )
        self.pde = nn.Sequential(
            lnn.CDEPdeLayerM2(c_convections, c, kernel_size, its, alpha),
            nn.Dropout3d(0.1),
            lnn.CDEPdeLayerM2(c, c, kernel_size, its, alpha),
            lnn.CDEPdeLayerM2(c, c, kernel_size, its, alpha),
            lnn.CDEPdeLayerM2(c, c_final, kernel_size, its, alpha),
        )
        self.project = lnn.MaxProjectM2()
        # self.project = SumProjectM2() # also works.
        self.final = nn.Sequential(
            nn.Conv2d(c_final, 1, 1, bias=False),
            nn.Sigmoid(),
        )

    def forward(self, x):
        x = self.lift(x)
        x = self.pde(x)
        x = self.project(x)
        x = self.final(x)
        return x

    def __repr__(self):
        return self.__class__.__name__


class CDEPdeNN12(nn.Module):
    """
    Basic Convection-Dilation-Eriosion PDE-G-CNN binary segmentation network with 3 layers.
    """

    def __init__(self, in_channels):
        super(CDEPdeNN12, self).__init__()

        its = 1
        kernel_size = [5, 5, 5]
        c = 10
        c_final = 16
        alpha = 0.65

        self.lift = nn.Sequential(
            nn.ReflectionPad2d(3),
            lnn.LiftM2Cartesian(
                in_channels=in_channels, out_channels=c, orientations=8, kernel_size=7
            ),
            nn.BatchNorm3d(c, track_running_stats=True),
        )
        self.pde = nn.Sequential(
            lnn.CDEPdeLayerM2(c, c, kernel_size, its, alpha),
            nn.Dropout3d(0.1),
            lnn.CDEPdeLayerM2(c, c, kernel_size, its, alpha),
            lnn.CDEPdeLayerM2(c, c, kernel_size, its, alpha),
            lnn.CDEPdeLayerM2(c, c, kernel_size, its, alpha),
            lnn.CDEPdeLayerM2(c, c, kernel_size, its, alpha),
            nn.Dropout3d(0.1),
            lnn.CDEPdeLayerM2(c, c, kernel_size, its, alpha),
            lnn.CDEPdeLayerM2(c, c, kernel_size, its, alpha),
            lnn.CDEPdeLayerM2(c, c, kernel_size, its, alpha),
            lnn.CDEPdeLayerM2(c, c, kernel_size, its, alpha),
            lnn.CDEPdeLayerM2(c, c_final, kernel_size, its, alpha),
        )
        self.project = lnn.MaxProjectM2()
        self.final = nn.Sequential(
            nn.Conv2d(c_final, 1, 1, bias=False),
            nn.Sigmoid(),
        )

    def forward(self, x):
        x = self.lift(x)
        x = self.pde(x)
        x = self.project(x)
        x = self.final(x)
        return x

    def __repr__(self):
        return self.__class__.__name__


class ADPBasicGroupCNN(nn.Module):
    """
    Basic 2D roto-translation equivariant binary segmentation network with a fixed anisotropic projection layer.
    """

    def __init__(self, in_channels):
        super(ADPBasicGroupCNN, self).__init__()

        track = True

        self.lift = nn.Sequential(
            nn.ReflectionPad2d(3),
            lnn.LiftM2Cartesian(
                in_channels=in_channels, out_channels=8, orientations=8, kernel_size=7
            ),
            nn.BatchNorm3d(8, track_running_stats=track),
            nn.ReLU(),
        )
        self.conv1 = nn.Sequential(
            lnn.ReflectionPadM2(padding=2),
            lnn.ConvM2Cartesian(
                in_channels=8, out_channels=8, orientations=8, kernel_size=5
            ),
            nn.BatchNorm3d(8, track_running_stats=track),
            nn.ReLU(),
        )
        self.conv2 = nn.Sequential(
            lnn.ReflectionPadM2(2),
            lnn.ConvM2Cartesian(8, 8, 8, 5),
            nn.BatchNorm3d(8, track_running_stats=track),
            nn.ReLU(),
        )
        self.conv3 = nn.Sequential(
            lnn.ReflectionPadM2(2),
            lnn.ConvM2Cartesian(8, 8, 8, 5),
            nn.BatchNorm3d(8, track_running_stats=track),
            nn.ReLU(),
        )
        self.conv4 = nn.Sequential(
            lnn.ConvM2Cartesian(8, 16, 8, 1),
            nn.BatchNorm3d(16, track_running_stats=track),
            nn.ReLU(),
        )
        self.project = lnn.AnisotropicDilatedProjectM2(
            longitudinal=3, lateral=1.5, alpha=0.65
        )
        self.conv5 = nn.Sequential(nn.Conv2d(16, 1, 1, bias=False), nn.Sigmoid())

    def forward(self, x):
        x = self.lift(x)
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.conv3(x)
        x = self.conv4(x)
        x = self.project(x)
        x = self.conv5(x)
        return x

    def __repr__(self):
        return self.__class__.__name__


class CDEPdeR2NN12(nn.Module):
    """ """

    def __init__(self, in_channels):
        super().__init__()

        its = 1
        kernel_size = 5
        c = 56
        c_final = 16
        alpha = 0.65
        finsler_order = 5

        self.pde = nn.Sequential(
            lnn.CDEPdeLayerR2Finslerian(
                in_channels, c, kernel_size, its, alpha, finsler_order
            ),
            lnn.CDEPdeLayerR2Finslerian(c, c, kernel_size, its, alpha, finsler_order),
            lnn.CDEPdeLayerR2Finslerian(c, c, kernel_size, its, alpha, finsler_order),
            lnn.CDEPdeLayerR2Finslerian(c, c, kernel_size, its, alpha, finsler_order),
            nn.Dropout2d(0.1),
            lnn.CDEPdeLayerR2Finslerian(c, c, kernel_size, its, alpha, finsler_order),
            lnn.CDEPdeLayerR2Finslerian(c, c, kernel_size, its, alpha, finsler_order),
            lnn.CDEPdeLayerR2Finslerian(c, c, kernel_size, its, alpha, finsler_order),
            lnn.CDEPdeLayerR2Finslerian(c, c, kernel_size, its, alpha, finsler_order),
            nn.Dropout2d(0.1),
            lnn.CDEPdeLayerR2Finslerian(c, c, 7, its, alpha, 7),
            lnn.CDEPdeLayerR2Finslerian(c, c, 7, its, alpha, 7),
            lnn.CDEPdeLayerR2Finslerian(c, c_final, 7, its, alpha, 7),
        )
        self.final = nn.Sequential(
            nn.Conv2d(c_final, 1, 1, bias=False),
            nn.Sigmoid(),
        )

    def forward(self, x):
        x = self.pde(x)
        x = self.final(x)
        return x

    def __repr__(self):
        return self.__class__.__name__


class DEPdeR2NN12(nn.Module):
    """ """

    def __init__(self, in_channels):
        super().__init__()

        its = 1
        kernel_size = 5
        c = 56
        c_final = 16
        alpha = 0.65
        finsler_order = 5

        self.pde = nn.Sequential(
            lnn.DEPdeLayerR2Finslerian(
                in_channels, c, kernel_size, its, alpha, finsler_order
            ),
            lnn.DEPdeLayerR2Finslerian(c, c, kernel_size, its, alpha, finsler_order),
            lnn.DEPdeLayerR2Finslerian(c, c, kernel_size, its, alpha, finsler_order),
            lnn.DEPdeLayerR2Finslerian(c, c, kernel_size, its, alpha, finsler_order),
            nn.Dropout2d(0.1),
            lnn.DEPdeLayerR2Finslerian(c, c, kernel_size, its, alpha, finsler_order),
            lnn.DEPdeLayerR2Finslerian(c, c, kernel_size, its, alpha, finsler_order),
            lnn.DEPdeLayerR2Finslerian(c, c, kernel_size, its, alpha, finsler_order),
            lnn.DEPdeLayerR2Finslerian(c, c, kernel_size, its, alpha, finsler_order),
            nn.Dropout2d(0.1),
            lnn.DEPdeLayerR2Finslerian(c, c, 7, its, alpha, 7),
            lnn.DEPdeLayerR2Finslerian(c, c, 7, its, alpha, 7),
            lnn.DEPdeLayerR2Finslerian(c, c_final, 7, its, alpha, 7),
        )
        self.final = nn.Sequential(
            nn.Conv2d(c_final, 1, 1, bias=False),
            nn.Sigmoid(),
        )

    def forward(self, x):
        x = self.pde(x)
        x = self.final(x)
        return x

    def __repr__(self):
        return self.__class__.__name__
