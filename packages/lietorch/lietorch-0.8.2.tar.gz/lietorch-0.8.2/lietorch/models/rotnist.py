"""
Models used for Rotated MNIST digit classification.
"""

import os
import gzip
import struct
import array
import torch
import torch.nn as nn
import torch.nn.functional as F

import lietorch.nn as lnn


def read_idx_gz_file(filename):
    with gzip.open(filename, "rb") as f:
        magic, type_code, dims = struct.unpack(">HBB", f.read(4))
        sizes = struct.unpack(">" + "I" * dims, f.read(4 * dims))

        type_fmts = {
            0x08: "B",  # unsigned byte
            0x09: "b",  # signed byte
            0x0B: "h",  # short (2 bytes)
            0x0C: "i",  # int (4 bytes)
            0x0D: "f",  # float (4 bytes)
            0x0E: "d",  # double (8 bytes)
        }

        type_dtypes = {
            0x08: torch.uint8,
            0x09: torch.int8,
            0x0B: torch.int16,
            0x0C: torch.int32,
            0x0D: torch.float32,
            0x0E: torch.float64,
        }

        type_fmt = type_fmts.get(type_code)

        if type_fmt is None:
            raise RuntimeError(
                f"Error reading file: not a known data type code: {type_code:x}"
            )

        dtype = type_dtypes.get(type_code)

        data = array.array(type_fmt, f.read())

        return torch.tensor(data, dtype=dtype).view(sizes)


def load_rotnist_data_from_path(path):
    train_img_fn = "train-images-idx3-ubyte.gz"
    train_lbl_fn = "train-labels-idx1-ubyte.gz"
    test_img_fn = "t10k-images-idx3-ubyte.gz"
    test_lbl_fn = "t10k-labels-idx1-ubyte.gz"

    train_img_fn = os.path.join(path, train_img_fn)
    train_lbl_fn = os.path.join(path, train_lbl_fn)
    test_img_fn = os.path.join(path, test_img_fn)
    test_lbl_fn = os.path.join(path, test_lbl_fn)

    train_img = read_idx_gz_file(train_img_fn)
    train_lbl = read_idx_gz_file(train_lbl_fn)
    test_img = read_idx_gz_file(test_img_fn)
    test_lbl = read_idx_gz_file(test_lbl_fn)

    return train_img, train_lbl, test_img, test_lbl


class LeNet5(nn.Module):
    """
    LeNet-5
    """

    def __init__(self):
        super(LeNet5, self).__init__()

        self.conv1 = nn.Sequential(
            nn.Conv2d(1, 6, kernel_size=(5, 5)),
            nn.Tanh(),
            nn.MaxPool2d(2),
        )

        self.conv2 = nn.Sequential(
            nn.Conv2d(6, 16, 5),
            nn.Tanh(),
            nn.MaxPool2d(2),
        )

        self.fc1 = nn.Sequential(
            nn.Flatten(), nn.Linear(256, 120), nn.Tanh(), nn.Dropout(0.1)
        )

        self.fc2 = nn.Sequential(
            nn.Linear(120, 84),
            nn.Tanh(),
        )

        self.fc3 = nn.Sequential(
            nn.Linear(84, 10),
        )

    def forward(self, x):
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.fc1(x)
        x = self.fc2(x)
        x = self.fc3(x)
        return x


class GroupM2Classifier4(nn.Module):
    """
    4-layer G-CNN
    """

    classes = 10

    def __init__(self, classes: int = 10):
        super().__init__()

        self.classes = classes

        self.lift = nn.Sequential(
            lnn.LiftM2Cartesian(
                in_channels=1, out_channels=6, orientations=8, kernel_size=5
            ),
            nn.BatchNorm3d(6, track_running_stats=True),
            nn.ReLU(),
        )

        self.conv1 = nn.Sequential(
            # lnn.ReflectionPadM2(padding=2),
            lnn.ConvM2Cartesian(6, 6, 8, 5),
            nn.BatchNorm3d(6, track_running_stats=True),
            nn.ReLU(),
            nn.Dropout3d(0.1),
        )
        self.conv2 = nn.Sequential(
            # lnn.ReflectionPadM2(2),
            lnn.ConvM2Cartesian(6, 8, 8, 5),
            nn.BatchNorm3d(8, track_running_stats=True),
            nn.ReLU(),
            lnn.SpatialResampleM2(size=(5, 5)),
        )

        self.fc = nn.Sequential(
            lnn.MaxProjectM2(),
            nn.Flatten(),
            nn.Dropout(0.1),
            nn.Linear(8 * 5 * 5, self.classes),
        )

    def forward(self, x):
        x = self.lift(x)
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.fc(x)
        return x


class CDEPdeM2Classifier4(nn.Module):
    """ """

    its = 1
    kernel_size = [5, 5, 5]
    alpha = 0.65
    classes = 10

    def __init__(self, classes: int = 10):
        super().__init__()

        self.classes = classes

        self.lift = nn.Sequential(
            lnn.LiftM2Cartesian(
                in_channels=1, out_channels=6, orientations=8, kernel_size=5
            ),
            nn.BatchNorm3d(6, track_running_stats=True),
            nn.ReLU(),
        )

        self.pde = nn.Sequential(
            lnn.CDEPdeLayerM2(6, 12, self.kernel_size, self.its, self.alpha),
            lnn.SpatialResampleM2(size=(14, 14)),
            nn.Dropout3d(0.1),
            lnn.CDEPdeLayerM2(12, 8, self.kernel_size, self.its, self.alpha),
            lnn.SpatialResampleM2(size=(5, 5)),
        )

        self.fc = nn.Sequential(
            lnn.MaxProjectM2(),
            nn.Flatten(),
            nn.Dropout(0.1),
            nn.Linear(8 * 5 * 5, self.classes),
        )

    def forward(self, x):
        x = self.lift(x)
        x = self.pde(x)
        x = self.fc(x)
        return x


class DEPdeM2Classifier4(nn.Module):
    """ """

    its = 1
    kernel_size = [5, 5, 5]
    alpha = 0.65
    classes = 10

    def __init__(self, classes: int = 10):
        super().__init__()

        self.classes = classes

        self.lift = nn.Sequential(
            lnn.LiftM2Cartesian(
                in_channels=1, out_channels=6, orientations=8, kernel_size=5
            ),
            nn.BatchNorm3d(6, track_running_stats=True),
            nn.ReLU(),
        )

        self.pde = nn.Sequential(
            lnn.DEPdeLayerM2(6, 12, self.kernel_size, self.its, self.alpha),
            lnn.SpatialResampleM2(size=(14, 14)),
            nn.Dropout3d(0.1),
            lnn.DEPdeLayerM2(12, 8, self.kernel_size, self.its, self.alpha),
            lnn.SpatialResampleM2(size=(5, 5)),
        )

        self.fc = nn.Sequential(
            lnn.MaxProjectM2(),
            nn.Flatten(),
            nn.Dropout(0.1),
            nn.Linear(8 * 5 * 5, self.classes),
        )

    def forward(self, x):
        x = self.lift(x)
        x = self.pde(x)
        x = self.fc(x)
        return x


class CDEPdeR2Classifier4(nn.Module):
    """ """

    its = 1
    kernel_size = 5
    alpha = 0.65
    classes = 10

    def __init__(self, classes: int = 10):
        super().__init__()

        self.classes = classes

        self.pde = nn.Sequential(
            lnn.CDEPdeLayerR2(
                1, 8, self.kernel_size, self.its, self.alpha, finsler_order=5
            ),
            lnn.CDEPdeLayerR2(
                8, 12, self.kernel_size, self.its, self.alpha, finsler_order=5
            ),
            lnn.SpatialResampleR2(size=(14, 14)),
            nn.Dropout2d(0.1),
            lnn.CDEPdeLayerR2(
                12, 8, self.kernel_size, self.its, self.alpha, finsler_order=5
            ),
            lnn.SpatialResampleR2(size=(5, 5)),
        )

        self.fc = nn.Sequential(
            nn.Flatten(),
            nn.Dropout(0.1),
            nn.Linear(8 * 5 * 5, self.classes),
        )

    def forward(self, x):
        x = self.pde(x)
        x = self.fc(x)
        return x


class DEPdeR2Classifier4(nn.Module):
    """ """

    its = 1
    kernel_size = 5
    alpha = 0.65
    classes = 10

    def __init__(self, classes: int = 10):
        super().__init__()

        self.classes = classes

        self.pde = nn.Sequential(
            lnn.DEPdeLayerR2Finslerian(
                1, 8, self.kernel_size, self.its, self.alpha, finsler_order=5
            ),
            lnn.DEPdeLayerR2Finslerian(
                8, 12, self.kernel_size, self.its, self.alpha, finsler_order=5
            ),
            lnn.SpatialResampleR2(size=(14, 14)),
            nn.Dropout2d(0.1),
            lnn.DEPdeLayerR2Finslerian(
                12, 8, self.kernel_size, self.its, self.alpha, finsler_order=5
            ),
            lnn.SpatialResampleR2(size=(5, 5)),
        )

        self.fc = nn.Sequential(
            nn.Flatten(),
            nn.Dropout(0.1),
            nn.Linear(8 * 5 * 5, self.classes),
        )

    def forward(self, x):
        x = self.pde(x)
        x = self.fc(x)
        return x
