# Installation

[TOC]

### Document Sections
* Requirements
* Installation
* Basic usage


### Requirements

Minimum requirements run ASGarD
* a C/C++ compiler with support for C++-17
* [CMake](https://cmake.org/) build system
* [Basic Linear Algebra Subroutine (BLAS)](https://en.wikipedia.org/wiki/Basic_Linear_Algebra_Subprograms) and [Linear Algebra PACKage (LAPACK)](http://www.netlib.org/lapack/)
    * many optimized BLAS and LAPACK implementations exist, e.g., OpenBLAS, MKL, Blis/Flame
* GIT which works with CMake to find additional dependencies for testing

Recommended but optional
* [OpenMP](https://en.wikipedia.org/wiki/OpenMP) for CPU multi-threading
    * supported by GCC and most recent versions of Clang (16 or newer)
* If you have Nvidia GPU ASGarD can take advantage of the [linear algebra libraries](https://developer.nvidia.com/cublas) and custom [CUDA kernels](https://developer.nvidia.com/cuda-zone)
* [HDF5](https://en.wikipedia.org/wiki/Hierarchical_Data_Format) and [HighFive](https://bluebrain.github.io/HighFive/) libraries to output the solution state
* Python bindings using [h5py](https://www.h5py.org/) and [numpy](https://numpy.org/) for easier visualization and HDF5 post-processing
* [Message Passing Interface (MPI)](https://en.wikipedia.org/wiki/Message_Passing_Interface) capabilities for spreading the workload across multiple computing nodes, uses option

Other CMake options
* dynamic/shared libraries are used by default, static build is possible with `-DBUILD_SHARED_LIBS=OFF`
    * Python bindings require shared libraries
* tests with CMake's ctest are enabled by default, disable with `-DASGARD_BUILD_TESTS=OFF`
* ASGarD builds with both single (float) and double precision, pick just one for faster compile time

ASGarD has the ability to automatically download and install OpenBLAS and HDF5.
However, it is recommended to use system provided libraries, available in most Linux distributions and HPC systems.

Limited support
* [Message Passing Interface (MPI)](https://en.wikipedia.org/wiki/Message_Passing_Interface)
* [Doxygen](http://www.doxygen.org/) documentation

Note that ASGarD is under heavy development and some of the requirements may change.
This document will be kept up-to-date with the changes.


### Installation

CMake uses out-of-source build, clone the repo and build in a subfolder
```
  git clone https://github.com/project-asgard/asgard.git
  cd asgard
  mkdir build
  cd build
  cmake \
    -D CMAKE_BUILD_TYPE=Release \
    -D CMAKE_INSTALL_PREFIX=../install \
    -D CMAKE_CXX_FLAGS="-march=native -mtune=native" \
    -D ASGARD_USE_OPENMP=ON \
    -D ASGARD_USE_PYTHON=ON \
    -D ASGARD_USE_HIGHFIVE=ON \
    -D ASGARD_PRECISIONS=double \
    ..
  cmake --build . -j
  ctest
  cmake install .
```

On a OSX system, users have reported instabilities with the homebrew provided HDF5,
especially on Apple M chips.
ASGarD provides an option to download and install HDF5 automatically
that can work around potential problems.
Also, OpenMP has limited benefits, due to what appears to be kernel scheduling overhead.
The BLAS/LAPACK acceleration needs a flag to enable the most recent mode.
```
  cmake \
    -D CMAKE_BUILD_TYPE=Release \
    -D CMAKE_INSTALL_PREFIX=../install \
    -D CMAKE_CXX_FLAGS="-march=native -mtune=native -DACCELERATE_NEW_LAPACK" \
    -D ASGARD_USE_OPENMP=OFF \
    -D ASGARD_USE_PYTHON=ON \
    -D ASGARD_USE_HIGHFIVE=ON \
    -D ASGARD_BUILD_HDF5=ON \
    -D ASGARD_PRECISIONS=double \
    ..
```

The installation step is required to use ASGarD as a library for an external project,
allowing the user to define their own PDE specification without intruding into the ASGarD code.
However, the currently available equations and all tools can be used directly from the
build folder.

It is recommended to use a dedicated `CMAKE_INSTALL_PREFIX` as opposed to common
locations such as `~/.local/` or `/opt/`, which will make it easier to uninstall.

For specific platform build instructions, [see this wiki page.](https://github.com/project-asgard/asgard/wiki/platforms)

### Python pip install

ASGarD has a pip installer called [ornl-asgard](https://pypi.org/project/ornl-asgard/) to avoid conflicts with existing project name.

Both venv and user-space installs are supported, e.g.,
```
python3 -m pip install ornl-asgard --user
```
The `--user` tag is not needed for a venv install
```
python3 -m pip install ornl-asgard
```

The installer is still experimental and the version will be changing often,
check the PyPIP project page and please report potential issues.

OSX and other systems often come with different versions of python,
be consistent between the version used for install and runtime.

MPI can be enabled using the pip-installer by setting an environment variable
```
export ASGARD_USE_MPI=ON
python3 -m pip install ornl-asgard
```
However, in this mode, CMake must be able to automatically find all necessary components for MPI,
i.e., it is not possible to pass fine-grained details about the path to MPI using PyPIP,
use CMake instead.

### Basic usage

List of all ASGarD flags is given by the executable
```
  asgard --help
```

Check out the installed examples in
```
  <CMAKE_INSTALL_PREFIX>/share/asgard/examples
```

Setting up the enronment paths can be done with
```
  source <CMAKE_INSTALL_PREFIX>/share/asgard/asgard-env.sh
```
The prefix used by the pip-installer is either the root of the venv envitonment
or `.local` subfolder for the user home folder.

For more details, see the [Basic Usage Section.](basic_usage.md)
