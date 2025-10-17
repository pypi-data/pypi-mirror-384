# Installation


## Prerequisites

### Python 3.9+ environment

The use of a virtual environment is recommended, and you will need to ensure that the environment use a Python version
greater than 3.9.
This can be achieved for instance either by using [conda](https://docs.conda.io/en/latest/) or by using [pyenv](https://github.com/pyenv/pyenv) (or [pyenv-win](https://github.com/pyenv-win/pyenv-win) on windows)
and [venv](https://docs.python.org/fr/3/library/venv.html) module.

The following examples show how to create a virtual environment with Python version 3.10.13 with the mentioned methods.

#### With conda (all platforms)

```shell
conda create -n do-env python=3.10.13
conda activate do-env
```

# 🚀 Installation
You can install KerasCustom using `pip`:
> [!IMPORTANT]
> 🚨 Please ensure you install **`keras_custom`** to get this library.


```python
pip install keras_custom
```

Alternatively, to install from source:

```python
git clone https://github.com/your-repo/keras_custom.git # Replace with your actual repo URL
cd keras_custom
pip install .
```

### Keras

`autoroot` relies on [Keras](https://keras.io/) 3x.

## Issues

If you have any issue when installing, you may need to update pip and setuptools:

```shell
pip install --upgrade pip setuptools
```

If still not working, please [submit an issue on github](https://github.com/ducoffeM/keras_custom/issues).
