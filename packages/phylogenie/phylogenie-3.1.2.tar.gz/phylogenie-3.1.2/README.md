<p align="center">
<img src="https://raw.githubusercontent.com/gabriele-marino/phylogenie/main/logo.png" style="width:100%; height:auto;"/>
</p>

---

[![AliSim](https://img.shields.io/badge/Powered%20by-AliSim-orange?style=flat-square)](https://iqtree.github.io/doc/AliSim)
[![PyPI version](https://img.shields.io/pypi/v/phylogenie)](https://pypi.org/project/phylogenie/)
![Downloads](https://img.shields.io/pypi/dm/phylogenie)


Phylogenie is a [Python](https://www.python.org/) package designed to easily simulate phylogenetic datasets—such as trees and multiple sequence alignments (MSAs)—with minimal setup effort. Simply specify the distributions from which your parameters should be sampled, and Phylogenie will handle the rest!

## ✨ Features

Phylogenie comes packed with useful features, including:

- **Simulate tree and multiple sequence alignment (MSA) datasets from parameter distributions** 🌳🧬  
  Define distributions over your parameters and sample a different combination of parameters for each dataset sample.

- **Automatic metadata management** 🗂️  
  Phylogenie stores each parameter combination sampled during dataset generation in a `.csv` file.

- **Generalizable configurations** 🔄  
  Easily apply the same configuration across multiple dataset splits (e.g., train, validation, test).

- **Multiprocessing support** ⚙️💻  
  Simply specify the number of cores to use, and Phylogenie handles multiprocessing automatically.

- **Pre-implemented parameterizations** 🎯  
  Include canonical, fossilized birth-death, epidemiological, birth-death with exposed-infectious (BDEI), birth-death with superspreading (BDSS), and contact tracing (CT).

- **Skyline parameter support** 🪜  
  Support for piece-wise constant parameters.

- **Arithmetic operations on parameters** 🧮  
  Perform flexible arithmetic operations between parameters directly within the config file.

## 📦 Installation
Phylogenie requires [Python](https://www.python.org/) 3.10 to be installed on your system. There are several ways to install Python and managing different Python versions. One popular option is to use [pyenv](https://github.com/pyenv/pyenv).

Once you have Python set up, you can install Phylogenie directly from PyPI:

```bash
pip install phylogenie
```

Or install from source:
```bash
git clone https://github.com/gabriele-marino/phylogenie.git
cd phylogenie
pip install .
```

## 🛠 Backend dependency

Phylogenie relies on [AliSim](https://iqtree.github.io/doc/AliSim) for simulating multiple sequence alignments (MSAs). AliSim is a powerful MSAs simulation tool distributed with [IQ-TREE](https://iqtree.github.io/), and requires separate installation to use it as a simulation backend.

## 🚀 Quick Start

Once you have installed Phylogenie, check out the [examples](https://github.com/gabriele-marino/phylogenie/tree/main/examples) folder.  
It includes a collection of thoroughly commented configuration files, organized as a step-by-step tutorial. These examples will help you understand how to use Phylogenie in practice and can be easily adapted to fit your own workflow.

For quick start, pick your favorite config file and run Phylogenie with:
```bash
phylogenie examples/config_file.yaml
```
This command will create the output dataset in the folder specified inside the configuration file, including data directories and metadata files for each dataset split defined in the config.

>❗ *Tip*: Can’t choose just one config file?
You can run them all at once by pointing Phylogenie to the folder! Just use: `phylogenie examples`. In this mode, Phylogenie will automatically find all `.yaml` files in the folder you specified and run for each of them!

## 📖 Documentation

- The [examples](https://github.com/gabriele-marino/phylogenie/tree/main/examples) folder contains many ready-to-use, extensively commented configuration files that serve as a step-by-step tutorial to guide you through using Phylogenie. You can explore them to learn how it works or adapt them directly to your own workflows.
- A complete user guide and API reference are under development. In the meantime, feel free to [reach out](mailto:gabmarino.8601@email.com) if you have any questions about integrating Phylogenie into your workflows.

## 📄 License

This project is licensed under [MIT License](https://raw.githubusercontent.com/gabriele-marino/phylogenie/main/LICENSE.txt). 

## 📫 Contact

For questions, bug reports, or feature requests, please, consider opening an [issue on GitHub](https://github.com/gabriele-marino/phylogenie/issues), or [contact me directly](mailto:gabmarino.8601@email.com).

If you need help with the configuration files, feel free to reach out —  I am always very available and happy to assist!
