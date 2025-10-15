[![PyPI](https://img.shields.io/pypi/v/mqt.qcec?logo=pypi&style=flat-square)](https://pypi.org/project/mqt.qcec/)
![OS](https://img.shields.io/badge/os-linux%20%7C%20macos%20%7C%20windows-blue?style=flat-square)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![CI](https://img.shields.io/github/actions/workflow/status/munich-quantum-toolkit/qcec/ci.yml?branch=main&style=flat-square&logo=github&label=ci)](https://github.com/munich-quantum-toolkit/qcec/actions/workflows/ci.yml)
[![CD](https://img.shields.io/github/actions/workflow/status/munich-quantum-toolkit/qcec/cd.yml?style=flat-square&logo=github&label=cd)](https://github.com/munich-quantum-toolkit/qcec/actions/workflows/cd.yml)
[![Documentation](https://img.shields.io/readthedocs/qcec?logo=readthedocs&style=flat-square)](https://mqt.readthedocs.io/projects/qcec)
[![codecov](https://img.shields.io/codecov/c/github/munich-quantum-toolkit/qcec?style=flat-square&logo=codecov)](https://codecov.io/gh/munich-quantum-toolkit/qcec)

<p align="center">
  <a href="https://mqt.readthedocs.io">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/munich-quantum-toolkit/.github/refs/heads/main/docs/_static/mqt-banner-dark.svg" width="90%">
      <img src="https://raw.githubusercontent.com/munich-quantum-toolkit/.github/refs/heads/main/docs/_static/mqt-banner-light.svg" width="90%" alt="MQT Banner">
    </picture>
  </a>
</p>

# MQT QCEC - A tool for Quantum Circuit Equivalence Checking

A tool for quantum circuit equivalence checking developed as part of the [_Munich Quantum Toolkit (MQT)_](https://mqt.readthedocs.io).
It builds upon [MQT Core](https://github.com/munich-quantum-toolkit/core), which forms the backbone of the MQT.

<p align="center">
  <a href="https://mqt.readthedocs.io/projects/qcec">
  <img width=30% src="https://img.shields.io/badge/documentation-blue?style=for-the-badge&logo=read%20the%20docs" alt="Documentation" />
  </a>
</p>

## Key Features

- Comprehensive equivalence checking engines: [Decision-diagram construction](https://mqt.readthedocs.io/projects/qcec/en/latest/equivalence_checking.html#construction-equivalence-checker-using-decision-diagrams), [Alternating DD](https://mqt.readthedocs.io/projects/qcec/en/latest/equivalence_checking.html#alternating-equivalence-checker-using-decision-diagrams), [Simulation-based falsification](https://mqt.readthedocs.io/projects/qcec/en/latest/equivalence_checking.html#simulation-equivalence-checker-using-decision-diagrams), and [ZX-calculus rewriting](https://mqt.readthedocs.io/projects/qcec/en/latest/equivalence_checking.html#zx-calculus-equivalence-checker)—coordinated in an automated [equivalence checking flow](https://mqt.readthedocs.io/projects/qcec/en/latest/equivalence_checking.html#resulting-equivalence-checking-flow) to prove equivalence or quickly find counterexamples.
- Compilation flow verification: validate transpiled/compiled circuits incl. layout permutations and measurements. [Guide](https://mqt.readthedocs.io/projects/qcec/en/latest/compilation_flow_verification.html)
- Parameterized circuits: prove or refute equivalence with symbolic parameters. [Guide](https://mqt.readthedocs.io/projects/qcec/en/latest/parametrized_circuits.html)
- Partial equivalence: compare measured output distributions, handling ancillary and garbage qubits. [Guide](https://mqt.readthedocs.io/projects/qcec/en/latest/partial_equivalence.html)
- Python-first API and Qiskit integration: pass `QuantumCircuit` or OpenQASM; one-call `verify()` or `verify_compilation()`. [Quickstart](https://mqt.readthedocs.io/projects/qcec/en/latest/quickstart.html) • [API](https://mqt.readthedocs.io/projects/qcec/en/latest/api/mqt/qcec/index.html)
- Efficient and portable: C++20 core with DD engines and ZX backend, prebuilt wheels for Linux/macOS/Windows via [PyPI](https://pypi.org/project/mqt.qcec/).

If you have any questions, feel free to create a [discussion](https://github.com/munich-quantum-toolkit/qcec/discussions) or an [issue](https://github.com/munich-quantum-toolkit/qcec/issues) on [GitHub](https://github.com/munich-quantum-toolkit/qcec).

## Contributors and Supporters

The _[Munich Quantum Toolkit (MQT)](https://mqt.readthedocs.io)_ is developed by the [Chair for Design Automation](https://www.cda.cit.tum.de/) at the [Technical University of Munich](https://www.tum.de/) and supported by the [Munich Quantum Software Company (MQSC)](https://munichquantum.software).
Among others, it is part of the [Munich Quantum Software Stack (MQSS)](https://www.munich-quantum-valley.de/research/research-areas/mqss) ecosystem, which is being developed as part of the [Munich Quantum Valley (MQV)](https://www.munich-quantum-valley.de) initiative.

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/munich-quantum-toolkit/.github/refs/heads/main/docs/_static/mqt-logo-banner-dark.svg" width="90%">
    <img src="https://raw.githubusercontent.com/munich-quantum-toolkit/.github/refs/heads/main/docs/_static/mqt-logo-banner-light.svg" width="90%" alt="MQT Partner Logos">
  </picture>
</p>

Thank you to all the contributors who have helped make MQT QCEC a reality!

<p align="center">
  <a href="https://github.com/munich-quantum-toolkit/qcec/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=munich-quantum-toolkit/qcec" alt="Contributors to munich-quantum-toolkit/qcec" />
  </a>
</p>

The MQT will remain free, open-source, and permissively licensed—now and in the future.
We are firmly committed to keeping it open and actively maintained for the quantum computing community.

To support this endeavor, please consider:

- Starring and sharing our repositories: https://github.com/munich-quantum-toolkit
- Contributing code, documentation, tests, or examples via issues and pull requests
- Citing the MQT in your publications (see [Cite This](#cite-this))
- Citing our research in your publications (see [References](https://mqt.readthedocs.io/projects/qcec/en/latest/references.html))
- Using the MQT in research and teaching, and sharing feedback and use cases
- Sponsoring us on GitHub: https://github.com/sponsors/munich-quantum-toolkit

<p align="center">
  <a href="https://github.com/sponsors/munich-quantum-toolkit">
  <img width=20% src="https://img.shields.io/badge/Sponsor-white?style=for-the-badge&logo=githubsponsors&labelColor=black&color=blue" alt="Sponsor the MQT" />
  </a>
</p>

## Getting Started

MQT QCEC is available via [PyPI](https://pypi.org/project/mqt.qcec/).

```console
(venv) $ pip install mqt.qcec
```

The following code gives an example on the usage:

```python3
from mqt import qcec

# verify the equivalence of two circuits provided as qasm files
result = qcec.verify("circ1.qasm", "circ2.qasm")

# print the result
print(result.equivalence)
```

**Detailed documentation and examples are available at [ReadTheDocs](https://mqt.readthedocs.io/projects/qcec).**

## System Requirements and Building

Building the project requires a C++ compiler with support for C++20 and CMake 3.24 or newer.
For details on how to build the project, please refer to the [documentation](https://mqt.readthedocs.io/projects/qcec).
Building (and running) is continuously tested under Linux, macOS, and Windows using the [latest available system versions for GitHub Actions](https://github.com/actions/runner-images).
MQT QCEC is compatible with all [officially supported Python versions](https://devguide.python.org/versions/).

## Cite This

Please cite the work that best fits your use case.

### MQT QCEC (the tool)

When citing the software itself or results produced with it, cite the MQT QCEC paper:

```bibtex
@article{burgholzerQCECJKQTool2021,
  title        = {{{QCEC}}: {{A JKQ}} tool for quantum circuit equivalence checking},
  author       = {Burgholzer, Lukas and Wille, Robert},
  year         = 2021,
  month        = feb,
  journal      = {Software Impacts},
  doi          = {10.1016/j.simpa.2020.100051}
}
```

### The Munich Quantum Toolkit (the project)

When discussing the overall MQT project or its ecosystem, cite the MQT Handbook:

```bibtex
@inproceedings{mqt,
  title        = {The {{MQT}} Handbook: {{A}} Summary of Design Automation Tools and Software for Quantum Computing},
  shorttitle   = {{The MQT Handbook}},
  author       = {Wille, Robert and Berent, Lucas and Forster, Tobias and Kunasaikaran, Jagatheesan and Mato, Kevin and Peham, Tom and Quetschlich, Nils and Rovara, Damian and Sander, Aaron and Schmid, Ludwig and Schoenberger, Daniel and Stade, Yannick and Burgholzer, Lukas},
  year         = 2024,
  booktitle    = {IEEE International Conference on Quantum Software (QSW)},
  doi          = {10.1109/QSW62656.2024.00013},
  eprint       = {2405.17543},
  eprinttype   = {arxiv},
  addendum     = {A live version of this document is available at \url{https://mqt.readthedocs.io}}
}
```

### Peer-Reviewed Research

When citing the underlying methods and research, please reference the most relevant peer-reviewed publications from the list below:

[[1]](https://arxiv.org/pdf/2004.08420.pdf) L. Burgholzer and R. Wille. Advanced Equivalence Checking for Quantum Circuits. _IEEE Transactions on Computer-Aided Design of Integrated Circuits and Systems (TCAD)_, 2021.

[[2]](https://arxiv.org/pdf/2009.02376.pdf) L. Burgholzer, R. Raymond, and R. Wille. Verifying Results of the IBM Qiskit Quantum Circuit Compilation Flow. In _IEEE International Conference on Quantum Computing and Engineering (QCE)_, 2020.

[[3]](https://arxiv.org/pdf/2011.07288.pdf) L. Burgholzer, R. Kueng, and R. Wille. Random Stimuli Generation for the Verification of Quantum Circuits. In _Asia and South Pacific Design Automation Conference (ASP-DAC)_, 2021.

[[4]](https://arxiv.org/pdf/2106.01099.pdf) L. Burgholzer and R. Wille. Handling Non-Unitaries in Quantum Circuit Equivalence Checking. In _Design Automation Conference (DAC)_, 2022.

[[5]](https://arxiv.org/pdf/2208.12820.pdf) T. Peham, L. Burgholzer, and R. Wille. Equivalence Checking of Quantum Circuits with the ZX-Calculus. _IEEE Journal on Emerging and Selected Topics in Circuits and Systems (JETCAS)_, 2022.

[[6]](https://arxiv.org/pdf/2210.12166.pdf) T. Peham, L. Burgholzer, and R. Wille. Equivalence Checking of Parameterized Quantum Circuits: Verifying the Compilation of Variational Quantum Algorithms. In _Asia and South Pacific Design Automation Conference (ASP-DAC)_, 2023.

---

## Acknowledgements

The Munich Quantum Toolkit has been supported by the European Research Council (ERC) under the European Union's Horizon 2020 research and innovation program (grant agreement No. 101001318), the Bavarian State Ministry for Science and Arts through the Distinguished Professorship Program, as well as the Munich Quantum Valley, which is supported by the Bavarian state government with funds from the Hightech Agenda Bayern Plus.

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/munich-quantum-toolkit/.github/refs/heads/main/docs/_static/mqt-funding-footer-dark.svg" width="90%">
    <img src="https://raw.githubusercontent.com/munich-quantum-toolkit/.github/refs/heads/main/docs/_static/mqt-funding-footer-light.svg" width="90%" alt="MQT Funding Footer">
  </picture>
</p>
