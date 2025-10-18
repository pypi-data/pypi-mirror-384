import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

install_requires = ["torch==2.6.*", "torchvision==0.21.*"]

setuptools.setup(
    name="lietorch",
    author="B.M.N. Smets et.al",
    author_email="b.m.n.smets@tue.nl",
    description="PDE-G-CNN package for PyTorch",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.com/bsmetsjr/lietorch",
    packages=setuptools.find_packages(),
    package_data={"lietorch": ["lib/*"]},
    install_requires=install_requires,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: C++",
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Environment :: GPU :: NVIDIA CUDA",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Mathematics",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.12",
)
