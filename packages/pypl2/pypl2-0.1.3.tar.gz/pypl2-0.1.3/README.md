# Introduction
The PyPL2 Python package wraps the PL2FileReader library written in C++.

# Installation
## Clone repository
```bash
mkdir pypl2
cd pypl2
git clone git@192.168.37.103:Chris/PyPL2.git .
```

## Create virtual environment
```bash
python -m venv venv
./venv/scripts/activate
python -m pip install setuptools build
```
OR
```bash
conda create -n <env_name> python=3.<version #> --yes
conda activate <env_name>
python -m pip install build
```

## Install pypl2 to virtual environment
```bash
python -m build
python -m pip install ./dist/<name-of-tar.gz-file>
```