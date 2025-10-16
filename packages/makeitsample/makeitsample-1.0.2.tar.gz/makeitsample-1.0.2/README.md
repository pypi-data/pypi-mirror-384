<div align="center">

# makeitsample

<!-- [![Paper](http://img.shields.io/badge/paper-ACL--anthology-B31B1B.svg)](https://aclanthology.org/2021.sigtyp-1.2/)
[![Conference](https://img.shields.io/badge/conference-NAACL--2021-blue.svg)](https://2021.naacl.org/)-->
[![License: MIT][mit-shield]][mit]
![Python](https://img.shields.io/badge/python-3.7%20|%20higher%20version-orange.svg)

[mit]: https://opensource.org/license/mit
[mit-shield]: https://img.shields.io/badge/License-MIT-yellow.svg

</div>

**makeitsample** is a Python library for generating typological language samples
using the *diversity value (DV)* metric (Rijkhoff et al., 1993; Rijkhoff and
Bakker, 1998; Bakker, 2010).

It provides tools to build language family trees from CSV data, compute
diversity values for each node, and select a representative set of languages
that reflect genealogical and typological diversity.

---

## 📚 What It Does

makeitsample is designed to support researchers and linguists in the creation of
typologically diverse language samples. It consists of two main modules:

- `language_family_tree.py` — defines tree structures and computes diversity
values (DV).
- `forest.py` — manages a forest of language families and handles sampling logic
across multiple trees.

---

## 🚀 Features

- Build hierarchical language family trees from CSV input.
- Handle both nested genealogies and isolated languages.
- Calculate diversity values at each node in a tree.
- Select representative languages based on weighted sampling.
- Minimal dependencies and easy integration into other projects.

---

## 📦 Installation

```bash
pip install makeitsample
```

## 🛠️ Usage

### Prepare the input files

makeitsample requires a set of input files (representing language families) in CSV
format.
The CSV files should contain the following columns:
- `id`: the id of the node
- `name`: the name of the node
- `parent_id`: the id of the parent node
- `type`: the type of the node (the only allowed values are "family", "group" or "language")

The user can also add any other columns to the CSV files.

### As a library

#### Create a language family tree from CSV data

```python
import makeitsample.language_family_tree as lft

# Create a language family tree from CSV data
family = lft.LanguageFamilyTree("path/to/csv/file.csv")

# Print the tree structure
print(family)
```

#### Calculate diversity values for the language family trees

```python
from makeitsample.forest import Forest

# Create a forest of language families
language_families = Forest(dir="path/to/directory/with/csv/files")

# Update the trees with diversity values
language_families.dv()

# Export the updated trees to CSV
language_families.export_forest(dir="path/to/output/dir", format="csv")
```

#### Sample languages from the language family trees

```python
from makeitsample.forest import Forest

# Create a forest of language families
language_families = Forest("path/to/directory/with/csv/files")

# Sample languages from the forest
language_families.make_sample(n=100)

# Export the sampled languages to CSV
language_families.export_sample(dir="path/to/output/dir", format="csv")

# Export the sampled languages to JSON
language_families.export_sample(dir="path/to/output/dir", format="json")
```

### As a command-line tool

#### Sample languages from the language family trees

```bash
makeitsample [-h] [-n N] [-i INPUT] [-o OUTPUT] [-f {csv,json}] [-s SAMPLENAME] [-r RANDOM_SEED]
```

#### Arguments
- `-h`, `--help`: Show this help message and exit.
- `-n N`, `--number N`: Number of languages to sample.
- `-i INPUT`, `--input INPUT`: Path to the input directory containing CSV files.
- `-o OUTPUT`, `--output OUTPUT`: Path to the output directory for sampled languages.
- `-f {csv,json}`, `--format {csv,json}`: Output format for sampled languages (default: csv).
- `-s SAMPLENAME`, `--sample_name SAMPLENAME`: Name of the sample (default: sample).
- `-r RANDOM_SEED`, `--random_seed RANDOM_SEED`: Random seed for reproducibility.

#### Example usage

```bash
makeitsample -n 100 -i data -o out -f csv -s test_sample
```

## 📄 License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 📄 Citation

If you use this library in your research, please cite the following paper:

<!--```bibtex
@inproceedings{makeitsample2025,
  title = {Samplify: a Tool for Generating Typological Language Samples Based on the Diversity Value},
  author = {Brigada Villa, Luca},
  year = {2025},
  url = {https://makeitsample.unipv.it},
  version = {1.0}
}
```-->