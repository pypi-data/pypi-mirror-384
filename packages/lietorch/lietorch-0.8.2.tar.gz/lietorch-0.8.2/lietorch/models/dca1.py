"""
Models used for retinal vessel segmentation on the DCA1 dataset.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

import lietorch.nn as lnn


class BasicSpatialCNN3(nn.Module):
    """
    Basic spatial binary segmentation network with 3 layers.
    """

    def __init__(self, in_channels):
        super(BasicSpatialCNN3, self).__init__()

        track = True
        c = 40  # 18 - original
        c_final = 18

        self.conv1 = nn.Sequential(
            nn.ReplicationPad2d(3),
            nn.Conv2d(in_channels, c, 7, bias=False),
            nn.BatchNorm2d(c, track_running_stats=track),
            nn.ReLU(),
        )
        self.conv2 = nn.Sequential(
            nn.Conv2d(c, c_final, 1, bias=False),
            nn.BatchNorm2d(c_final, track_running_stats=track),
            nn.ReLU(),
        )
        self.conv3 = nn.Sequential(nn.Conv2d(c_final, 1, 1, bias=False), nn.Sigmoid())

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
        return x

    def __repr__(self):
        return self.__class__.__name__


class BasicSpatialCNN6(nn.Module):
    """
    Basic spatial binary segmentation network with 6 layers.
    """

    def __init__(self, in_channels):
        super(BasicSpatialCNN6, self).__init__()

        track = True
        c = 18  # 18 - original
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
        c = 18  # 20 original
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


class BasicGroupCNN3(nn.Module):
    """
    Basic 2D roto-translation equivariant binary segmentation network with 3 layers.
    """

    def __init__(self, in_channels):
        super(BasicGroupCNN3, self).__init__()

        track = True
        c = 30
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
        x = self.convfinal(self.project(x))
        return x

    def __repr__(self):
        return self.__class__.__name__


class BasicGroupCNN6(nn.Module):
    """
    Basic 2D roto-translation equivariant binary segmentation network with 6 layers.
    """

    def __init__(self, in_channels):
        super(BasicGroupCNN6, self).__init__()

        track = True
        c = 8
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


class BasicGroupCNN12(nn.Module):
    """
    Basic 2D roto-translation equivariant binary segmentation network with 12 layers.
    """

    def __init__(self, in_channels):
        super(BasicGroupCNN12, self).__init__()

        track = True
        c = 8
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


class CDEPdeNN3(nn.Module):
    """
    Basic Convection-Dilation-Eriosion PDE-G-CNN binary segmentation network with 3 layers.
    """

    def __init__(self, in_channels):
        super(CDEPdeNN3, self).__init__()

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


class CDEPdeNN12(nn.Module):
    """
    Basic Convection-Dilation-Eriosion PDE-G-CNN binary segmentation network with 12 layers.
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
