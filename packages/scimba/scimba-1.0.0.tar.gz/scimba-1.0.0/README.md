# ScimBa

[![pipeline status](https://gitlab.com/scimba/scimba/badges/main/pipeline.svg)](https://gitlab.com/scimba/scimba/-/commits/main)
[![coverage report](https://gitlab.com/scimba/scimba/badges/main/coverage.svg)](https://scimba.gitlab.io/scimba/coverage)
[![Latest Release](https://gitlab.com/scimba/scimba/-/badges/release.svg)](https://gitlab.com/scimba/scimba/-/releases)
[![Doc](https://img.shields.io/badge/doc-sphinx-blue)](https://scimba.gitlab.io/scimba/)

Scimba is a Python library that implements varying Scientific Machine Learning (SciML)
methods for PDE problems, as well as tools for hybrid numerical methods.

The current version of the code solves parametric PDEs using various nonlinear
approximation spaces such as neural networks, low-rank approximations, and nonlinear
kernel methods.
These methods:

- can handle complex geometries generated via level-set techniques and mappings, including sub-volumetric and surface domains;
- support function projections as well as elliptic, time-dependent, and kinetic parametric PDEs;
- are compatible with both space–time algorithms (PINN, Deep Ritz) and time-sequential ones (discrete PINNs, neural Galerkin and neural semi-Lagrangian schemes).

To achieve this, the code provides several optimization strategies, including:

- Adam and L-BFGS;
- natural gradient methods (for neural network-based models);
- hybrid least-squares approaches.

The current version of Scimba relies on a PyTorch backend.
A JAX version is under development.
