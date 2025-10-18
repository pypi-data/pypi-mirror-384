
<p align="center">
  <img width="40%" src="./assets/ltlogo.png" />
</p>

# LieTorch

This project provides a python package that expands the functionality of the PyTorch framework with PDE-based group equivariant CNN operators [[1]](#cite).


#### The name

The name LieTorch is a reference to the Norwegian mathematician [Sophus Lie](https://infogalactic.com/info/Sophus_Lie), whose contributions to geometry are extensively used in this project. The name is pronounced */li:/* (as in *Lee*) and not */ˈlī/* (as in *lie*).


## Installation

The version of LieTorch you install must match the installed PyTorch version per the following table.

| PyTorch version | LieTorch version |
| ---       | --- |
| 2.6+cu126 | 0.8 |
| 2.5       | 0.7 |
| 2.0       | 0.6 |
| 1.13      | 0.5 |
| 1.12      | 0.4 |


The following commands will install [PyTorch](https://pytorch.org/get-started/locally/) and the _lietorch_ package in a fresh virtual environment.
Note that installing PyTorch via the Anaconda packages is deprecated since 2.6.
```shell
  conda create -n <environment name>
  conda activate <environment name>

  # install python and pip
  conda install python=3.13 pip

  # install PyTorch with pip
  pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126

  # and install lietorch with pip
  pip install lietorch
```
Make sure your [Nvidia drivers](https://www.nvidia.com/download/index.aspx) are up to date!

## Container

Container images are available from https://github.com/bmnsmets/gldg-containers.
The `lietorch-ssh` image contains LieTorch and its dependencies as well as an SSH server (so you can connect to it via VS Code for example).
To pull the latest image:
```shell
  podman pull ghcr.io/bmnsmets/lietorch-ssh:latest
```
or if you are using Docker:
```shell
  docker pull ghcr.io/bmnsmets/lietorch-ssh:latest
```

## Neural network modules

Modules are grouped according to the manifold they operate on. Most modules have a functional equivalant in the `lietorch.nn.functional` namespace.

### Euclidean Space ℝ² 

Basic operators:

| Module | Functional | C++/CUDA backend  |
| --- | --- | :---: |
| `MorphologicalConvolutionR2` | `morphological_convolution_r2` | ✓ |
| `FractionalDilationR2` | `fractional_dilation_r2` | ✓ |
| `FractionalErosionR2` | `fractional_erosion_r2` | ✓ |
| `ConvectionR2` | `convection_r2` | ⏳ |
| `DiffusionR2` | `diffusion_r2` | ⏳ |
| `LinearR2` | `linear_r2` | ✓ |

### Position and Orientation Space 𝕄₂

Basic operators:

| Module | Functional | C++/CUDA backend  |
| --- | --- | :---: |
| `LiftM2Cartesian` | `lift_m2_cartesian` | - |
| `LiftM2Cakewavelets` | `lift_m2_cakewavelets` | - |
| `ReflectionPadM2` | `reflection_pad_m2` | - |
| `ConvM2Cartesian` | `conv_m2_cartesian`  | - |
| `MaxProjectM2`    |  `max_project_m2` | - | 
| `AnisotropicDilatedProjectM2` | `anisotropic_dilated_project_m2` | ✓ |
| `MorphologicalConvolutionM2` | `morphological_convolution_m2` | ✓ |
| `LinearConvolutionM2` | `linear_convolution_m2` | ✓ |
| `ConvectionM2` | `convection_m2` | ✓ |
| `DiffusionM2` | `diffusion_m2` | ⏳ |
| `FractionalDilationM2` | `fractional_dilation_m2` | ✓ |
| `FractionalErosionM2` | `fractional_erosion_m2` | ✓ |
| `LinearM2` | `linear_m2` | ✓ |


High-level modules for implementing PDE-based networks:

| Module | Description/PDE  |
| --- | :--- |
| `ConvectionDilationPdeM2` | $`u_t=-\mathbf{c}u + \lVert \nabla u \rVert^{2 \alpha}_{\mathcal{G}}`$ |
| `ConvectionErosionPdeM2` | $`u_t=-\mathbf{c}u - \lVert \nabla u \rVert^{2 \alpha}_{\mathcal{G}}`$ |
| `CDEPdeLayerM2` | $`u_t=-\mathbf{c}u + \lVert \nabla u \rVert^{2 \alpha}_{\mathcal{G}_1} - \lVert \nabla u \rVert^{2 \alpha}_{\mathcal{G}_2}`$ <br>  with batch normalization and linear combinations |


### Loss functions

Additional loss functions.

| Module | Functional | Description |
| ------ | ---------- | :---------: |
| `lietorch.nn.loss.DiceLoss` | `lietorch.nn.functional.dice_loss` | Binary DICE loss |


### Generic 

The modules in the generic category do not fit into any previous category and include operators that serve as C++/CUDA implementation examples.

| Module | Functional | C++/CUDA backend  |
| --- | --- | :---: |
| `GrayscaleDilation2D` | `grayscale_dilation_2d` | ✓ |
| `GrayscaleErosion2D` | `grayscale_erosion_2d` | ✓ |



## Extra Dependencies
 
 The included experiments additionally depend on the following packages.
 - scikit-learn
 - tqdm
 - numpy
 - sty
 - mlflow
 - libtiff

 ## Structure

- `/lietorch` contains the main python package.
- `/experiments` contains various experiments, including those used in publications.
- `/tests` contains unit tests.
- `/backend` contains the source code of the C++/CUDA backend,
    - see [./backend/README.md](./backend/README.md) if you wish to compile the extension yourself.
- `/assets` various files used in tests and documentation.



## Cite

If you use this code in your own work please cite our paper:

<a id="cite">[1]</a> Smets, B.M.N., Portegies, J., Bekkers, E.J. et al. PDE-Based Group Equivariant Convolutional Neural Networks. J Math Imaging Vis (2022). <https://doi.org/10.1007/s10851-022-01114-x>



```
@article{smets2022pde,
  title={PDE-based Group Equivariant Convolutional Neural Networks},
  author={Smets, Bart and Portegies, Jim and Bekkers, Erik and Duits, Remco},
  journal={Journal of Mathematical Imaging and Vision},
  year={2022},
  doi={10.1007/s10851-022-01114-x},
  url={https://doi.org/10.1007/s10851-022-01114-x}
}
```