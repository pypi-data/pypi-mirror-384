# plot-tree

## Description

plot-tree creates tree views from a csv file with child-parent relationships. 
It supports time-based snapshots and generates hierarchical data visuals in meraid, yaml, and text-tree formats.

## Setting Up the Project

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd plot-tree
   ```

1. Make sure base python verison is >=3.11
   - if base python is lower than 3.11, you can use conda to create a new environment with Python 3.11:

   ```bash
    conda create -n py311 python=3.11
    conda activate py311
    which python
   ```
   - then use poetry to create a new virtual environment with python 3.11
   ```bash
    poetry env use python3.11
   ```

1. Install Poetry if has not installed:
https://python-poetry.org/docs/#installation

   ```bash
    pipx install poetry
   ```

1. Install Python dependencies using Poetry:

   ```bash
   poetry install
   ```

   This command will install all Python packages specified in `pyproject.toml`, including:
   - `pyyaml` version ^6.0.1
   - `anytree` version ^2.12.1

## Run all the pytest unit tests
   ```bash
   poetry run pytest -v
   ```

## How to Run

1. Input: put the child and parent entries in [child_parent.csv](/child_parent.csv) by using the same format of the csv file
2. Run at project's root folder:

```bash
poetry run plot
```
![](/assets.run.gif)

3. Output: at folder [/output](/output)

## `treeplots` cli
```zsh
pip install treeplots
treeplots --help
treeplots -v
treeplots --example
treeplots
```

### cli publish
```zsh
poetry version patch
poetry publish --build
poetry publish --build --dry-run
tox -e release
```
