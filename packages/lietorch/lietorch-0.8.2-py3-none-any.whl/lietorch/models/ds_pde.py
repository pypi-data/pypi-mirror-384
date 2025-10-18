"""
Models used to compare diffusion-shock PDE-CNNs to (diffusion)-convection-
dilation-erosion PDE-CNNs and normal CNNs.
"""

import torch
import torch.nn as nn
from torch.utils.data import Dataset, TensorDataset, DataLoader, random_split
from torchvision.io import decode_image
from torchvision.transforms import GaussianBlur
import lietorch.nn as lnn
from lietorch.nn.functional import dice_loss
import lightning.pytorch as lp
from torchmetrics import (
    PeakSignalNoiseRatio,
    StructuralSimilarityIndexMeasure,
    Metric,
)
from lightning import Callback
import time

import numpy as np
from math import ceil
from dataclasses import dataclass
from pathlib import Path
import tifffile
from PIL import Image
import cv2

# Models


@dataclass
class ModelArgs:
    layers: int = 6
    in_channels: int = 3
    kernel_size: int = 5
    c: int = 16
    c_final: int = 16
    orientations: int = 8
    fixed_lift: bool = False

    # lr: float = 0.001
    # lr_gamma: float = 0.99
    # weight_decay: float = 0.00001


@dataclass
class OptimizerArgs:
    lr: float = 0.01
    lr_gamma: float = 0.95
    weight_decay: float = 0.005
    last_epoch: int = -1


class SegmentationModel(lp.LightningModule):
    """
    Lightning wrapper for segmentation networks.
    """

    def __init__(
        self, architecture, args_model: ModelArgs, args_optimizer: OptimizerArgs
    ):
        super().__init__()

        self.args_optimizer = args_optimizer
        model, name = get_model(architecture, args_model)
        self.model = model.append(
            nn.Conv2d(args_model.c_final, 1, 1, bias=False)
        ).append(nn.Sigmoid())
        self.name = "Segmentation" + name
        self.metrics()

    def forward(self, x):
        return self.model(x)

    def training_step(self, batch):
        x, y = batch
        output = self(x)
        loss = self.loss_f(output, y)
        self.train_loss = loss

        self.train_confmat(output, y)

        return loss

    def on_train_epoch_end(self):
        self.log_metrics("train", *self.train_confmat.compute())
        self.log("train_loss", self.train_loss, prog_bar=True)

    def validation_step(self, batch):
        x, y = batch
        output = self(x)
        self.val_loss = self.loss_f(output, y)

        self.val_confmat(output, y)

    def on_validation_epoch_end(self):
        self.log_metrics("val", *self.val_confmat.compute())
        self.log("val_loss", self.val_loss, prog_bar=True)

    def test_step(self, batch):
        x, y = batch
        output = self(x)

        self.test_confmat(output, y)

    def on_test_epoch_end(self):
        self.log_metrics("test", *self.test_confmat.compute())

    def metrics(self):
        self.train_confmat = GlobalMeasures()
        self.val_confmat = GlobalMeasures()
        self.test_confmat = GlobalMeasures()

    def log_metrics(self, stage, tp, tn, fp, fn):
        metric_kwargs = dict(
            prog_bar=False, sync_dist=True, on_step=False, on_epoch=True
        )
        self.log(f"{stage}_dice", dice(tp, tn, fp, fn, smooth=1.0), **metric_kwargs)
        self.log(
            f"{stage}_precision",
            precision(tp, tn, fp, fn),
            **metric_kwargs,
        )
        self.log(f"{stage}_recall", recall(tp, tn, fp, fn), **metric_kwargs)
        self.log(f"{stage}_f1score", f1(tp, tn, fp, fn), **metric_kwargs)
        self.log(f"{stage}_iou", iou(tp, tn, fp, fn), **metric_kwargs)

    def loss_f(self, x, y):
        return dice_loss(x, y)

    def __repr__(self):
        return self.name

    def configure_optimizers(self):
        return get_optimizer(self)


class DenoisingModel(lp.LightningModule):
    """
    Lightning wrapper for denoising networks.
    """

    def __init__(
        self, architecture, args_model: ModelArgs, args_optimizer: OptimizerArgs
    ):
        super().__init__()

        self.args_optimizer = args_optimizer
        model, name = get_model(architecture, args_model)
        self.model = model.append(
            nn.Conv2d(args_model.c_final, args_model.in_channels, 1, bias=False)
        )
        self.name = "Denoising" + name
        self.loss_f = nn.MSELoss()
        self.metrics()

    def forward(self, x):
        return self.model(x)

    def training_step(self, batch):
        x, y = batch
        output = self(x)
        loss = self.loss_f(output, y)
        self.train_loss = loss
        self.train_psnr(output, y)
        self.train_ssim(output, y)

        return loss

    def on_train_epoch_end(self):
        self.log("train_loss", self.train_loss, prog_bar=True)
        self.log("train_psnr", self.train_psnr)
        self.log("train_ssim", self.train_ssim)

    def validation_step(self, batch):
        x, y = batch
        output = self(x)
        self.val_loss = self.loss_f(output, y)
        self.val_psnr(output, y)
        self.val_ssim(output, y)

    def on_validation_epoch_end(self):
        self.log("val_loss", self.val_loss, prog_bar=True)
        self.log("val_psnr", self.val_psnr)
        self.log("val_ssim", self.val_ssim)

    def test_step(self, batch):
        x, y = batch
        output = self(x)
        self.test_loss = self.loss_f(output, y)
        self.test_psnr(output, y)
        self.test_ssim(output, y)

    def on_test_epoch_end(self):
        self.log("test_loss", self.test_loss)
        self.log("test_psnr", self.test_psnr)
        self.log("test_ssim", self.test_ssim)

    def metrics(self, data_range=(0, 1)):
        self.train_psnr = PeakSignalNoiseRatio(data_range=data_range)
        self.train_ssim = StructuralSimilarityIndexMeasure(data_range=data_range)
        self.val_psnr = PeakSignalNoiseRatio(data_range=data_range)
        self.val_ssim = StructuralSimilarityIndexMeasure(data_range=data_range)
        self.test_psnr = PeakSignalNoiseRatio(data_range=data_range)
        self.test_ssim = StructuralSimilarityIndexMeasure(data_range=data_range)

    def __repr__(self):
        return self.name

    def configure_optimizers(self):
        return get_optimizer(self)


def get_model(architecture: str, args_model: ModelArgs):
    match architecture:
        case "DSR2":
            model = CNN_model_maker(args_model, lnn.DSPdeLayerR2)
            name = "DSR2DSR2NN"
        case "CDER2Isotropic":
            model = CNN_model_maker(args_model, lnn.CDEPdeLayerR2Isotropic)
            name = "CDER2IsotropicNN"
        case "DDER2Isotropic":
            model = CNN_model_maker(args_model, lnn.DDEPdeLayerR2Isotropic)
            name = "DDER2IsotropicNN"
        case "DSR2Isotropic":
            model = CNN_model_maker(args_model, lnn.DSPdeLayerR2Isotropic)
            name = "DSR2IsotropicNN"
        case "DDEM2":
            model = GCNN_model_maker(args_model, lnn.DDEPdeLayerM2)
            name = "DDEM2NN"
        case "CDEM2":
            model = GCNN_model_maker(args_model, lnn.CDEPdeLayerM2)
            name = "CDEM2NN"
        case "DSM2":
            model = GCNN_model_maker(args_model, lnn.DSPdeLayerM2)
            name = "DSM2NN"
    return model, name


def get_optimizer(model: SegmentationModel | DenoisingModel):
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=model.args_optimizer.lr,
        weight_decay=model.args_optimizer.weight_decay,
    )
    scheduler = torch.optim.lr_scheduler.ExponentialLR(
        optimizer,
        model.args_optimizer.lr_gamma,
        last_epoch=model.args_optimizer.last_epoch,
    )

    return {"optimizer": optimizer, "lr_scheduler": scheduler}


def GCNN_model_maker(args: ModelArgs, layer: nn.Module):
    layers = args.layers
    in_channels = args.in_channels
    kernel_size = args.kernel_size
    c = args.c
    c_final = args.c_final
    orientations = args.orientations
    fixed_lift = args.fixed_lift

    if fixed_lift:
        print("Fixed lifting")
        c_convections = 40
        model = nn.Sequential(
            lnn.LiftM2Cakewavelets(in_channels=in_channels, orientations=orientations),
            lnn.LinearM2(in_channels=in_channels, out_channels=c_convections),
            lnn.ConvectionM2(c_convections),
            nn.BatchNorm3d(c_convections, track_running_stats=True),
            lnn.LinearM2(in_channels=c_convections, out_channels=c),
            nn.ReLU(),
        )
    else:
        print("Trained lifting")
        model = nn.Sequential(
            nn.ReflectionPad2d(3),
            lnn.LiftM2Cartesian(
                in_channels=in_channels, out_channels=c, orientations=8, kernel_size=7
            ),
            nn.BatchNorm3d(c, track_running_stats=True),
            nn.ReLU(),
        )

    for _ in range(layers - 3):
        model.append(layer(c, c, kernel_size))
    model.append(layer(c, c_final, 1 if isinstance(kernel_size, int) else kernel_size))
    return model.append(lnn.MaxProjectM2())


class GCNNLayer(torch.nn.Module):
    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int,
        orientations: int = 8,
    ):
        super().__init__()
        pad = kernel_size // 2

        self.model = torch.nn.Sequential(
            lnn.ReflectionPadM2(pad),
            lnn.ConvM2Cartesian(in_channels, out_channels, orientations, kernel_size),
            nn.BatchNorm3d(out_channels, track_running_stats=True),
            nn.ReLU(),
        )

    def forward(self, x):
        return self.model(x)


def CNN_model_maker(args: ModelArgs, layer: nn.Module):
    layers = args.layers
    in_channels = args.in_channels
    kernel_size = args.kernel_size
    c = args.c
    c_final = args.c_final

    model = nn.Sequential(
        nn.Conv2d(
            in_channels, c, 7, padding="same", padding_mode="replicate", bias=False
        ),
        nn.BatchNorm2d(c, track_running_stats=True),
        nn.ReLU(),
    )
    for _ in range(layers - 3):
        model.append(layer(c, c, kernel_size))
    model.append(layer(c, c_final, 1))
    return model


class CNNLayer(torch.nn.Module):
    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int,
    ):
        super().__init__()

        self.model = torch.nn.Sequential(
            torch.nn.Conv2d(
                in_channels,
                out_channels,
                kernel_size,
                bias=False,
                padding="same",
                padding_mode="replicate",
            ),
            torch.nn.BatchNorm2d(out_channels, track_running_stats=True),
            torch.nn.ReLU(),
        )

        torch.nn.init.xavier_uniform_(
            self.model[0].weight, gain=torch.nn.init.calculate_gain("relu")
        )

    def forward(self, input):
        return self.model(input)


@dataclass
class DatasetArgs:
    data_folder: str = "../../datasets"
    dataset: str = "DRIVE"
    task: str = "inpainting"
    patch_shape: int = None
    patch_overlap: int = 0
    n_train: int = None
    train_frac: float = 0.88
    batch_size: int = 8
    num_workers: int = 16

    def __post_init__(self):
        folder = Path(self.data_folder) / self.dataset
        match self.dataset:
            case "DRIVE":
                self.train_images = str(folder / "training" / "images")
                self.train_masks = str(folder / "training" / "1st_manual")
                self.test_images = str(folder / "test" / "images")
                self.test_masks = str(folder / "test" / "1st_manual")
                self.channels = 3
            case "Lines":
                self.train_images = str(folder / "train" / "images")
                self.train_masks = str(folder / "train" / "segmentation")
                self.test_images = str(folder / "test" / "images")
                self.test_masks = str(folder / "test" / "segmentation")
                self.channels = 1
            case "DCA1":
                self.train_images = str(folder / "training" / "images")
                self.train_masks = str(folder / "training" / "groundtruth")
                self.test_images = str(folder / "test" / "images")
                self.test_masks = str(folder / "test" / "groundtruth")
                self.channels = 1
            case _:
                raise ValueError(
                    f"{self.dataset} is not a valid dataset! Choose one of 'DRIVE', 'Lines', 'DCA1."
                )


class DatasetModule(lp.LightningDataModule):
    """
    Lightning data module providing the training, validation, and testing data
    loaders.
    """

    def __init__(self, args: DatasetArgs):
        super().__init__()

        self.args = args
        self.patch_shape = (args.patch_shape, args.patch_shape)
        print(f"Performing {args.task} on {args.dataset}.")

    def setup(self, stage: str):
        match self.args.dataset:
            case "DRIVE":
                get_dataset = get_DRIVE
            case "Lines":
                get_dataset = get_Lines
            case "DCA1":
                get_dataset = get_DCA1

        if stage == "fit":
            x, y = get_dataset(self.args, train=True)

            if self.args.task == "denoising":
                full_train_set = DenoisingDataset(x, mode="train")
            elif self.args.task == "inpainting":
                full_train_set = TensorDataset(x, y)
            self.train_set, self.val_set = random_split(
                full_train_set, [self.args.train_frac, 1.0 - self.args.train_frac]
            )
            print("train set size:", len(self.train_set))
            print("val set size:", len(self.val_set))

        if stage == "test":
            x, y = get_dataset(self.args, train=False)

            if self.args.task == "denoising":
                self.test_set = DenoisingDataset(x, mode="test", fixed_seed=0)
            elif self.args.task == "inpainting":
                self.test_set = TensorDataset(x, y)
            print("test set size:", len(self.test_set))

    def train_dataloader(self):
        return DataLoader(
            self.train_set,
            batch_size=self.args.batch_size,
            shuffle=True,
            num_workers=self.args.num_workers,
        )

    def val_dataloader(self):
        return DataLoader(
            self.val_set,
            batch_size=self.args.batch_size,
            shuffle=False,
            num_workers=self.args.num_workers,
        )

    def test_dataloader(self):
        return DataLoader(
            self.test_set,
            batch_size=1,
            shuffle=False,
            num_workers=self.args.num_workers,
        )

    def __repr__(self):
        return self.args.dataset + "DatasetModule"


class DenoisingDataset(Dataset):
    """
    Pytorch dataset for training a denoising network.
    """

    def __init__(
        self, clean_images, sigma=63.75, rho=2.0, fixed_seed=None, mode="train"
    ):
        self.clean_images = clean_images
        self.sigma = sigma
        self.correlate = GaussianBlur(2 * ceil(4 * rho) + 1, sigma=rho)
        self.fixed_seed = fixed_seed
        self.mode = mode

        if fixed_seed is not None:
            self.rng = torch.Generator()
            self.rng.manual_seed(fixed_seed)
        else:
            self.rng = None

    def __len__(self):
        return len(self.clean_images)

    def add_noise(self, image):
        """image: torch tensor in [0, 1]"""
        shape = (1, *image.shape[-2:])
        device = image.device
        if self.rng is not None:
            noise = torch.randn(shape, device=device, generator=self.rng)
        else:
            noise = torch.randn(shape, device=device)

        noisy = image + self.correlate(noise * (self.sigma / 255.0))
        return torch.clamp(noisy, 0, 1)

    def __getitem__(self, idx):
        clean = self.clean_images[idx]

        noisy = self.add_noise(clean)
        return noisy, clean


def get_DRIVE(args: DatasetArgs, train=True):
    """
    Load and pre-process DRIVE images (x) and segmentation maps (y).
    """
    x = []
    y = []

    path_x, path_y = (
        (args.train_images, args.train_masks)
        if train
        else (args.test_images, args.test_masks)
    )
    path_x, path_y = Path(path_x), Path(path_y)

    for p in sorted(path_x.glob("*.tif")):
        x.append(
            torch.tensor(np.array(tifffile.imread(p)), dtype=torch.float32) / 255.0
        )

    for p in sorted(path_y.glob("*.gif")):
        y.append(torch.tensor(np.array(Image.open(p)), dtype=torch.float32) / 255.0)

    x = torch.stack(x)
    y = torch.stack(y)

    if train and args.patch_shape is not None:
        # first calculate anchor (corner) point for the individual patches
        h, w = x.shape[1:3]
        patch_h, patch_w = args.patch_shape, args.patch_shape
        overlap_h, overlap_w = args.patch_overlap, args.patch_overlap

        anchors_h = list(range(0, h, patch_h - overlap_h))

        if anchors_h[-1] >= h - overlap_h:
            anchors_h = anchors_h[:-1]
        anchors_h[-1] = h - patch_h

        anchors_w = list(range(0, w, patch_w - overlap_w))

        if anchors_w[-1] >= w - overlap_w:
            anchors_w = anchors_w[:-1]
        anchors_w[-1] = w - patch_w

        anchors = np.reshape(
            np.stack(np.meshgrid(anchors_h, anchors_w), axis=-1), (-1, 2)
        )

        x_patches = []
        y_patches = []

        for i in range(x.shape[0]):
            for a in anchors:
                y_patch = y[i, a[0] : a[0] + patch_h, a[1] : a[1] + patch_w]
                # Remove background patches.
                if y_patch.sum() > 0.0:
                    x_patches.append(
                        x[i, a[0] : a[0] + patch_h, a[1] : a[1] + patch_w, :]
                    )
                    y_patches.append(y_patch)

        x = torch.stack(x_patches)
        y = torch.stack(y_patches)

    # permute dimensions to [batch, channel, height, width]
    x = x[: args.n_train].permute(0, 3, 1, 2)
    # convert to long
    y = y[: args.n_train].long()[..., None, :, :]

    return x, y


def get_Lines(args: DatasetArgs, train=True):
    """
    Load and pre-process Lines images (x) and segmentation maps (y).
    """
    x = []
    y = []

    path_x, path_y = (
        (args.train_images, args.train_masks)
        if train
        else (args.test_images, args.test_masks)
    )
    path_x, path_y = Path(path_x), Path(path_y)

    # torchvision.io.decode_image returns tensors of shape [C,H,W].
    for p in sorted(path_x.glob("*.png")):
        x.append(decode_image(p, mode="GRAY").to(dtype=torch.float32) / 255.0)

    for p in sorted(path_y.glob("*.png")):
        y.append(decode_image(p, mode="GRAY").to(dtype=torch.float32) / 255.0)

    x, y = x[: args.n_train], y[: args.n_train]

    x = torch.stack(x)
    y = torch.stack(y).long()

    return x, y


def get_DCA1(args: DatasetArgs, train=True):
    """
    Load and pre-process DCA1 images (x) and segmentation maps (y).
    """
    x = []
    y = []

    path_x, path_y = (
        (args.train_images, args.train_masks)
        if train
        else (args.test_images, args.test_masks)
    )
    path_x, path_y = Path(path_x), Path(path_y)

    print(1)
    for p in sorted(path_x.glob("*.pgm")):
        x.append(
            torch.tensor(cv2.imread(p, cv2.IMREAD_GRAYSCALE), dtype=torch.float32)
            / 255.0
        )

    for p in sorted(path_y.glob("*.pgm")):
        y.append(
            torch.tensor(cv2.imread(p, cv2.IMREAD_GRAYSCALE), dtype=torch.float32)
            / 255.0
        )
    print(2)

    x, y = x, y

    x = torch.stack(x)
    y = torch.stack(y)

    if train and args.patch_shape is not None:
        # first calculate anchor (corner) point for the individual patches
        h, w = x.shape[1:3]
        patch_h, patch_w = args.patch_shape, args.patch_shape
        overlap_h, overlap_w = args.patch_overlap, args.patch_overlap

        anchors_h = list(range(0, h, patch_h - overlap_h))

        if anchors_h[-1] >= h - overlap_h:
            anchors_h = anchors_h[:-1]
        anchors_h[-1] = h - patch_h

        anchors_w = list(range(0, w, patch_w - overlap_w))

        if anchors_w[-1] >= w - overlap_w:
            anchors_w = anchors_w[:-1]
        anchors_w[-1] = w - patch_w

        anchors = np.reshape(
            np.stack(np.meshgrid(anchors_h, anchors_w), axis=-1), (-1, 2)
        )

        x_patches = []
        y_patches = []

        for i in range(x.shape[0]):
            for a in anchors:
                y_patch = y[i, a[0] : a[0] + patch_h, a[1] : a[1] + patch_w]
                # Remove background patches.
                if y_patch.sum() > 0.0:
                    x_patches.append(x[i, a[0] : a[0] + patch_h, a[1] : a[1] + patch_w])
                    y_patches.append(y_patch)

        x = torch.stack(x_patches)
        y = torch.stack(y_patches)

    print(x.shape, y.shape)

    # permute dimensions to [batch, channel, height, width]
    x = x[: args.n_train, None]
    # convert to long
    y = y[: args.n_train].long()[:, None]

    print(x.shape, y.shape)

    return x, y


# Lightning Callbacks


class EpochTimer(Callback):
    def __init__(self, skip_epochs=1):
        super().__init__()
        # First epoch can be slow, you might want to skip it
        self.skip_epochs = skip_epochs
        self.train_times = []
        self.valid_times = []
        self.test_times = []

    def on_train_epoch_start(self, trainer, pl_module):
        self.train_time = time.time()

    def on_train_epoch_end(self, trainer, pl_module):
        if trainer.current_epoch >= self.skip_epochs:
            self.train_time = time.time() - self.train_time
            self.train_times.append(self.train_time)
            pl_module.log("train epoch time", self.train_time)

    def on_validation_epoch_start(self, trainer, pl_module):
        if trainer.current_epoch >= self.skip_epochs:
            self.valid_time = time.time()

    def on_validation_epoch_end(self, trainer, pl_module):
        if trainer.current_epoch >= self.skip_epochs:
            self.valid_time = time.time() - self.valid_time
            self.valid_times.append(self.valid_time)
            pl_module.log("valid epoch time", self.valid_time)

    def on_test_epoch_start(self, trainer, pl_module):
        if trainer.current_epoch >= self.skip_epochs:
            self.test_time = time.time()

    def on_test_epoch_end(self, trainer, pl_module):
        if trainer.current_epoch >= self.skip_epochs:
            self.test_time = time.time() - self.test_time
            self.test_times.append(self.test_time)
            pl_module.log("test epoch time", self.test_time)

    def on_train_end(self, trainer, pl_module):
        if len(self.train_times) > 0:
            print(
                "train epoch time",
                np.mean(self.train_times),
                "±",
                np.std(self.train_times),
            )
        if len(self.valid_times) > 0:
            print(
                "valid epoch time",
                np.mean(self.valid_times),
                "±",
                np.std(self.valid_times),
            )
        if len(self.test_times) > 0:
            print(
                "test epoch time",
                np.mean(self.test_times),
                "±",
                np.std(self.test_times),
            )


# Metrics


class GlobalMeasures(Metric):
    def __init__(self, dist_sync_on_step=False):
        super().__init__(dist_sync_on_step=dist_sync_on_step)
        self.add_state("tp", default=torch.tensor(0.0), dist_reduce_fx="sum")
        self.add_state("tn", default=torch.tensor(0.0), dist_reduce_fx="sum")
        self.add_state("fp", default=torch.tensor(0.0), dist_reduce_fx="sum")
        self.add_state("fn", default=torch.tensor(0.0), dist_reduce_fx="sum")

    def update(self, preds: torch.Tensor, target: torch.Tensor):
        preds = preds.round().bool()
        target = target.round().bool()
        self.tp += (preds & target).sum()
        self.tn += (~preds & ~target).sum()
        self.fp += (preds & ~target).sum()
        self.fn += (~preds & target).sum()

    def compute(self):
        return (self.tp, self.tn, self.fp, self.fn)


def dice(tp, tn, fp, fn, smooth=1e-7):
    return (2 * tp + smooth) / (2 * tp + fp + fn + smooth)


def precision(tp, tn, fp, fn, smooth=1e-7):
    return (tp + smooth) / (tp + fp + smooth)


def recall(tp, tn, fp, fn, smooth=1e-7):
    return (tp + smooth) / (tp + fn + smooth)


def f1(tp, tn, fp, fn, smooth=1e-7):
    return (2 * tp + smooth) / (2 * tp + fp + fn + smooth)


def iou(tp, tn, fp, fn, smooth=1e-7):
    return (tp + smooth) / (tp + fp + fn + smooth)
