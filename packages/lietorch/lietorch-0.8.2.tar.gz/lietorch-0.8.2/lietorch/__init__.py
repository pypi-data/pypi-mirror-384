"""
The python package *lietorch* extends *pytorch* with types and functions that enable Lie group based geometric deep learning.

### Tensor dimension naming scheme

In the documentation we will use the following abreviations to name tensor dimensions.

* __B__ : batch size.

* __C__ : channels.

* __Cin__, __Cout__ : input and output channels.

* __Or__ : orientations.

* __H__, __W__ : height and width, usually in the context of images.

* __KH__, __KW__, __KOr__ : height, width and orientations usually in the context of kernels.

* __Spl__ : number of basis splines in a spline function.

For example a batch of multi-channel orientation scores would have a shape that we label as `[B, C, Or, H, W]`.
"""

import lietorch.models
import lietorch.nn
import lietorch.bspline
import lietorch.padding
import lietorch.generic

__version__ = "0.8.2"

_backend_initialized = False
_backend_version = None


def _init_backend():
    import platform, os, torch

    path, filename = os.path.split(os.path.abspath(__file__))
    libpath = []
    if platform.system() == "Windows":
        libpath = os.path.join(path, "lib/lietorch.dll")
    elif platform.system() == "Linux":
        libpath = os.path.join(path, "lib/liblietorch.so")
    else:
        raise NotImplementedError(
            f"Error: {platform.system()} is not a supported platform"
        )

    if not os.path.isfile(libpath):
        raise FileNotFoundError(f"Error: Could not find {libpath}")

    torch.ops.load_library(libpath)

    v = [int(x) for x in torch.version.cuda.split(".")]
    torch_cuda_version = 1000 * v[0] + 10 * v[1]
    if len(v) == 3:
        torch_cuda_version += v[2]
    lietorch_cuda_version = torch.ops.lietorch._cuda_version()

    # if not lietorch_cuda_version == torch_cuda_version:
    #     raise RuntimeError(
    #         f"PyTorch has been compiled with CUDA {torch_cuda_version} but LieTorch was compiled with CUDA {lietorch_cuda_version}"
    #     )

    global _backend_initialized, _backend_version
    _backend_initialized = True
    _backend_version = torch.ops.lietorch._build_version()


_init_backend()
