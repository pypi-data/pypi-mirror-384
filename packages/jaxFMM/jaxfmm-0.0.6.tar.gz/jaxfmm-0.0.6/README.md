# jaxFMM

jaxFMM is an open source implementation of the Fast Multipole Method in JAX. The goal is to offer an easily readable/maintainable FMM implementation with good performance that runs on CPU/GPU and supports autodiff. This is enabled through JAX's just-in-time compiler.

## Installation and Usage

jaxFMM depends only on JAX and can be installed from pypi or by downloading the source as follows:

    pip install jaxfmm

If you want to run jaxFMM on GPUs, the easiest way is to use NVIDIA CUDA and cuDNN from pip wheels by instead typing:

    pip install jaxfmm[cuda]

Using a custom, self-installed CUDA with jax is [described in the JAX documentation](https://docs.jax.dev/en/latest/installation.html).

The [unitcube demo](/demos/unitcube.py) is a short and simple example demonstrating how to use jaxFMM.

## Features

There are many flavors of FMM implementations. In short, jaxFMM currently:

- only supports the Laplacian kernel.
- only supports point charges.
- uses real basis functions computed via recurrence relations.
- uses "nested sum" O(p^4) M2M/M2L/L2L transformations.
- uses a non-uniform 2^N-ary tree hierarchy (directly inspired by [this work of A. Goude and S. Engblom](https://link.springer.com/article/10.1007/s11227-012-0836-0)), allowing arbitrary shape of the boxes in the hierarchy and guaranteeing balanced trees but requiring storage of interaction lists.
- has jit-compiled functions and autodiff for every substep of the algorithm except for the generation of interaction lists.

In summary, jaxFMM in its current state can do adaptive point charge FMM for Laplace kernels with good performance for lower expansion orders (p <= 3) and reasonably homogenous distributions. Autodiff only works if the particle positions remain constant. A first benchmark of uniformly distributed charges in the unit cube, computed on Google Cloud [g2-standard-8](https://cloud.google.com/compute/docs/gpus#l4-gpus) (GPU timings) and [c3d-highmem-16](https://cloud.google.com/compute/docs/general-purpose-machines#c3d_series) (CPU timings) machines can be found below:

<img src="https://gitlab.com/jaxfmm/jaxfmm/-/raw/main/docs/images/jax_unitcube_benchmark_p3.png" alt="unitcube benchmark" width="500"/>

## TODOs

jaxFMM is primarily developed for my PhD project, where I am working on a GPU parallel FMM stray field evaluation routine with autodiff for finite-element micromagnetics. Alongside the very early state that it is in, this explains the currently limited feature set and design decisions mentioned above.

Contributions are always welcome however, and I plan to still improve jaxFMM. Topics that come to mind here are:

- volume FMM.
- other kernels or even a kernel-independent formulation.
- distributed parallelism via jax.sharding.
- faster M2M/M2L/L2L transformations.
- faster jit-compilation, especially for large systems, higher orders and gradient computations.
- jit-compilable (and differentiable) interaction list generation, if possible.
- various other performance improvements.
- some degree of autotuning for the parameters.

## Stray Field Evaluation

As mentioned above, jaxFMM is developed for rapid stray field evaluation in finite-element micromagnetics. The [strayfield branch](https://gitlab.com/jaxfmm/jaxfmm/-/tree/strayfield) features stray field evaluation functions for P1-FEM meshes and the corresponding [strayfield unitcube demo](https://gitlab.com/jaxfmm/jaxfmm/-/blob/strayfield/demos/strayfield_unitcube.py) shows how they are used. Note that this is still work in progress and currently only gives accurate results for meshes of good quality (i.e. all tetrahedra have low aspect ratio).