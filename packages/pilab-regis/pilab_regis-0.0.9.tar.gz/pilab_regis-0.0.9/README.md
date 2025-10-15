# Registration Operations

Welcome to the Registration Operations's Github repository! 

[![PyPI](https://img.shields.io/pypi/v/pilab_regis?label=pypi%20package)](https://pypi.org/project/pilab_regis/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/pilab_regis)](https://pypi.org/project/pilab_regis/)

## Description

This package contains helpful functions enabling an easier use of registration functions.


## Installing & importing

### Online install

The BinaMa package is available through ```pip install``` under the name ```pilab-regis```. Note that the online version might not always be up to date with the latest changes.

```
pip install pilab-regis
```
To upgrade the current version : ```pip install pilab-regis --upgrade```.

To install a specific version of the package use
```
pip install pilab-regis==0.0.1
```
All available versions are listed in [PyPI](https://pypi.org/project/pilab-regis/). The package names follow the rules of [semantic versioning](https://semver.org/).

### Local install

If you want to download the latest version directly from GitHub, you can clone this repository
```
git clone https://github.com/PiLAB-Medical-Imaging/registration
```
For a more frequent use of the library, you may wish to permanently add the package to your current Python environment. Navigate to the folder where this repository was cloned or downloaded (the folder containing the ```setup.py``` file) and install the package as follows
```
cd registration
pip install .
```

If you have an existing install, and want to ensure package and dependencies are updated use --upgrade
```
pip install --upgrade .
```
### Importing
At the top of your Python scripts, import the library as
```
import regis.core as rg
```

### Checking current version installed

The version of the TIME package installed can be displayed by typing the following command in your python environment
```
regis.__version__
``` 

### Uninstalling
```
pip uninstall pilab-regis
```
