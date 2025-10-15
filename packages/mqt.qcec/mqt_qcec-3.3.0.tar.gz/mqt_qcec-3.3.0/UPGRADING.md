# Upgrade Guide

This document describes breaking changes and how to upgrade. For a complete list of changes including minor and patch releases, please refer to the [changelog](CHANGELOG.md).

## [Unreleased]

## [3.3.0]

### End of support for Python 3.9

Starting with this release, MQT QCEC no longer supports Python 3.9.
This is in line with the scheduled end of life of the version.
As a result, MQT QCEC is no longer tested under Python 3.9 and no longer ships Python 3.9 wheels.

## [3.2.0]

Testing previous versions of the `mqt-qcec` package built via `uv sync` or simple `(uv) pip install .` generally failed due to binary incompatibility of the `mqt-core` compiled extension packages and the `mqt-qcec` one.
This required building `mqt-core` from source and without build isolation to get a working local setup.
By using the latest `pybind11` release (`v3`), the binary compatibility between extension modules compiled under different circumstances (such as different compilers) has been greatly increased.
As such, it is no longer necessary to build `mqt-core` from source and without build isolation when locally working on `mqt-qcec`.
A simple `uv sync` is enough to successfully run `pytest`.

The `ApplicationScheme`, `EquivalenceCriterion`, and `StateType` enums are now exposed via `pybind11`'s new `py::native_enum`, which makes them compatible with Python's `enum.Enum` class (PEP 435).
As a result, the enums can no longer be initialized using a string.
Instead of `ApplicationScheme("sequential")` or `"sequential"`, use `ApplicationScheme.sequential`.

Finally, the minimum required C++ version has been raised from C++17 to C++20.
The default compilers of our test systems support all relevant features of the standard.

## [3.1.0]

Even tough this is not a breaking change, it is worth mentioning to developers of MQT QCEC that all Python code (except tests) has been moved to the top-level `python` directory.
Furthermore, the C++ code for the Python bindings has been moved to the top-level `bindings` directory.

## [3.0.0]

This major release introduces several breaking changes, including the removal of deprecated features and the introduction of new APIs.
The following paragraphs describe the most important changes and how to adapt your code accordingly.
We intend to provide a more comprehensive migration guide for future releases.

The major change in this major release is the move to the MQT Core Python package.
This move allows us to make `qiskit` a fully optional dependency and entirely rely on the MQT Core IR for representing circuits.
Additionally, the `mqt-core` Python package now ships all its C++ libraries as shared libraries so that these need not be fetched or built as part of the build process.
This was tricky to achieve cross-platform, and you can find some more backstory in the corresponding [PR](https://github.com/munich-quantum-toolkit/qcec/pulls/432).
We expect this integration to mature over the next few releases.
If you encounter any issues, please let us know.

Some internals of QCEC have been streamlined and refactored to improve the overall code quality and maintainability.
Most notably, counterexamples are now returned as decision diagrams instead of dense arrays.
This was made possible by the move to the MQT Core Python package, which now also exposes the underlying DD package to Python.
The returned DDs have a [`get_vector()`](https://mqt.readthedocs.io/projects/core/en/v3.0.2/api/mqt/core/dd/#mqt.core.dd.VectorDD.get_vector) method that can be used to convert them to a dense array if needed.

MQT Core itself dropped support for several parsers in `v3.0.0`, including the `.real`, `.qc`, `.tfc`, and `GRCS` parsers.
The `.real` parser lives on as part of the [MQT SyReC] project. All others have been removed without replacement.
Consequently, these input formats are no longer supported in MQT QCEC.

MQT QCEC has moved to the [munich-quantum-toolkit](https://github.com/munich-quantum-toolkit) GitHub organization under https://github.com/munich-quantum-toolkit/qcec.
While most links should be automatically redirected, please update any links in your code to point to the new location.
All links in the documentation have been updated accordingly.

MQT QCEC now requires CMake 3.24 or higher.
Most modern operating systems should have this version available in their package manager.
Alternatively, CMake can be conveniently installed from PyPI using the [`cmake`](https://pypi.org/project/cmake/) package.

<!-- Version links -->

[unreleased]: https://github.com/munich-quantum-toolkit/qcec/compare/v3.3.0...HEAD
[3.3.0]: https://github.com/munich-quantum-toolkit/qcec/compare/v3.2.0...v3.3.0
[3.2.0]: https://github.com/munich-quantum-toolkit/qcec/compare/v3.1.0...v3.2.0
[3.1.0]: https://github.com/munich-quantum-toolkit/qcec/compare/v3.0.0...v3.1.0
[3.0.0]: https://github.com/munich-quantum-toolkit/qcec/compare/v2.8.2...v3.0.0

<!-- Other links -->

[MQT SyReC]: https://github.com/cda-tum/mqt-syrec
