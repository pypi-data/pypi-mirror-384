<!-- Entries in each category are sorted by merge time, with the latest PRs appearing first. -->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on a mixture of [Keep a Changelog] and [Common Changelog].
This project adheres to [Semantic Versioning], with the exception that minor releases may include breaking changes.

## [Unreleased]

## [2.1.0] - 2025-10-15

_If you are upgrading: please see [`UPGRADING.md`](UPGRADING.md#210)._

### Added

- ✨ Add support for Qiskit's `IfElse` operations ([#681]) ([**@denialhaag**])
- 👷 Enable testing on Python 3.14 ([#674]) ([**@denialhaag**])

### Changed

- ⬆️ Bump minimum required `mqt-core` version to `3.3.1` ([#681]) ([**@denialhaag**])

### Removed

- 🔥 Drop support for Python 3.9 ([#645]) ([**@denialhaag**])

## [2.0.0] - 2025-08-04

_If you are upgrading: please see [`UPGRADING.md`](UPGRADING.md#200)._

### Added

- 🐍 Build Python 3.14 wheels ([#608]) ([**@denialhaag**])
- ✨ Add Windows 11 ARM64 wheels and C++ testing ([#556]) ([**@burgholzer**])

### Changed

- ♻️ Streamline names of Python modules and classes ([#614]) ([**@denialhaag**])
- ⬆️ Bump minimum required `mqt-core` version to `3.2.1` ([#610]) ([**@denialhaag**])
- ⬆️ Require C++20 ([#610]) ([**@denialhaag**])
- ✨ Expose enums to Python via `pybind11`'s new (`enum.Enum`-compatible) `py::native_enum` ([#607]) ([**@denialhaag**])
- ⬆️ Bump minimum required `mqt-core` version to `3.1.0` ([#591]) ([**@denialhaag**])
- ⬆️ Bump minimum required `pybind11` version to `3.0.0` ([#591]) ([**@denialhaag**])
- ♻️ Move the C++ code for the Python bindings to the top-level `bindings` directory ([#567]) ([**@denialhaag**])
- ♻️ Move all Python code (no tests) to the top-level `python` directory ([#567]) ([**@denialhaag**])
- ⬆️ Support Qiskit 2.0 ([#571]) ([**@denialhaag**])
- 🚚 Move MQT DDSIM to the [munich-quantum-toolkit] GitHub organization
- ♻️ Use the `mqt-core` Python package for handling circuits ([#336]) ([**@burgholzer**])
- ⬆️ Bump minimum required CMake version to `3.24.0` ([#538]) ([**@burgholzer**])
- 📝 Rework existing project documentation ([#556]) ([**@burgholzer**])

### Removed

- 🔥 Remove methods for querying maximum node count ([#591]) ([**@denialhaag**])
- 🔥 Remove the TN flow from the path simulator ([#336]) ([**@burgholzer**])
- 🔥 Remove some superfluous C++ executables ([#336]) ([**@burgholzer**])
- 🔥 Remove support for `.real`, `.qc`, `.tfc`, and `GRCS` files ([#538]) ([**@burgholzer**])

### Fixed

- 🚸 Increase binary compatibility between `mqt-ddsim` and `mqt-core` ([#606]) ([**@denialhaag**])

## [1.24.0] - 2024-10-10

_📚 Refer to the [GitHub Release Notes] for previous changelogs._

<!-- Version links -->

[unreleased]: https://github.com/munich-quantum-toolkit/ddsim/compare/v2.1.0...HEAD
[2.1.0]: https://github.com/munich-quantum-toolkit/ddsim/releases/tag/v2.1.0
[2.0.0]: https://github.com/munich-quantum-toolkit/ddsim/releases/tag/v2.0.0
[1.24.0]: https://github.com/munich-quantum-toolkit/ddsim/releases/tag/v1.24.0

<!-- PR links -->

[#681]: https://github.com/munich-quantum-toolkit/ddsim/pull/681
[#674]: https://github.com/munich-quantum-toolkit/ddsim/pull/674
[#645]: https://github.com/munich-quantum-toolkit/ddsim/pull/645
[#640]: https://github.com/munich-quantum-toolkit/ddsim/pull/640
[#614]: https://github.com/munich-quantum-toolkit/ddsim/pull/614
[#610]: https://github.com/munich-quantum-toolkit/ddsim/pull/610
[#608]: https://github.com/munich-quantum-toolkit/ddsim/pull/608
[#607]: https://github.com/munich-quantum-toolkit/ddsim/pull/607
[#606]: https://github.com/munich-quantum-toolkit/ddsim/pull/606
[#591]: https://github.com/munich-quantum-toolkit/ddsim/pull/591
[#571]: https://github.com/munich-quantum-toolkit/ddsim/pull/571
[#567]: https://github.com/munich-quantum-toolkit/ddsim/pull/567
[#556]: https://github.com/munich-quantum-toolkit/ddsim/pull/556
[#538]: https://github.com/munich-quantum-toolkit/ddsim/pull/538
[#336]: https://github.com/munich-quantum-toolkit/ddsim/pull/336

<!-- Contributor -->

[**@burgholzer**]: https://github.com/burgholzer
[**@denialhaag**]: https://github.com/denialhaag

<!-- General links -->

[Keep a Changelog]: https://keepachangelog.com/en/1.1.0/
[Common Changelog]: https://common-changelog.org
[Semantic Versioning]: https://semver.org/spec/v2.0.0.html
[GitHub Release Notes]: https://github.com/munich-quantum-toolkit/ddsim/releases
[munich-quantum-toolkit]: https://github.com/munich-quantum-toolkit
