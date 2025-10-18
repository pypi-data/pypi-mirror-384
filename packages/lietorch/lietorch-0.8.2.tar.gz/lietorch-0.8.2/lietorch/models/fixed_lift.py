"""
Models used to compare trained and fixed lifting.
"""

import torch.nn as nn
import lietorch.nn as lnn


class TrainedLiftGCNN(nn.Module):
    """
    Basic 2D roto-translation equivariant binary segmentation network with 6
    layers and trained lifting layer.
    """

    def __init__(self, in_channels, inflection_point=None):
        super().__init__()

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


class FixedLiftGCNN(nn.Module):
    """
    Basic 2D roto-translation equivariant binary segmentation network with 6
    layers and fixed lifting layer.
    """

    def __init__(self, in_channels, inflection_point=None):
        super().__init__()

        track = True
        c = 16
        c_convections = 40
        c_final = 16

        self.lift = nn.Sequential(
            lnn.LiftM2Cakewavelets(
                in_channels=in_channels,
                orientations=8,
                inflection_point=inflection_point,
            ),
            lnn.LinearM2(in_channels=in_channels, out_channels=c_convections),
            lnn.ConvectionM2(c_convections),
            nn.BatchNorm3d(c_convections, track_running_stats=True),
            lnn.LinearM2(in_channels=c_convections, out_channels=c),
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


class TrainedLiftPDEGCNN(nn.Module):
    """
    Basic Convection-Dilation-Eriosion PDE-G-CNN binary segmentation network
    with 6 layers and trained lifting layer.
    """

    def __init__(self, in_channels, inflection_point=None):
        super().__init__()

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


class FixedLiftPDEGCNN(nn.Module):
    """
    Basic Convection-Dilation-Eriosion PDE-G-CNN binary segmentation network
    with 6 layers and fixed lifting layer.
    """

    def __init__(self, in_channels, inflection_point=None):
        super().__init__()

        kernel_size = [5, 5, 5]
        its = 1
        c = 16
        c_convections = 40
        c_final = 16
        alpha = 0.65

        self.lift = nn.Sequential(
            lnn.LiftM2Cakewavelets(
                in_channels=in_channels,
                orientations=8,
                inflection_point=inflection_point,
            ),
            lnn.LinearM2(in_channels=in_channels, out_channels=c_convections),
            lnn.ConvectionM2(c_convections),
            nn.BatchNorm3d(c_convections, track_running_stats=True),
            lnn.LinearM2(in_channels=c_convections, out_channels=c),
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
