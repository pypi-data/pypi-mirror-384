# KerasCustom

<div align="center">
    <img src="images/logo.png" width="55%" alt="keras_custom" align="center" />
</div>

> 🧩 Custom layers and operations for **Keras 3**, designed to extend its capabilities with modular, composable components.

---

## 🌟 Overview

**KerasCustom** provides advanced and non-native Keras layers and operations that simplify the definition, transformation, and manipulation of neural network architectures.
It is built to integrate seamlessly with the Keras Core backend system (TensorFlow, JAX, or PyTorch).

This library is part of a broader ecosystem including:

- **[JacobiNet](https://github.com/ducoffeM/jacobinet)** – for Jacobian computation as a Keras layer
- **[Decomon](https://github.com/airbus/decomon)** – for LiRPA / formal verification methods
- **[Onnx2Keras3](https://github.com/ducoffeM/onnx2keras3)** – for ONNX-to-Keras model conversion
- **[Keras2Marabou](https://github.com/ducoffeM/keras2marabou)** – for expressing verification properties
- **[Airobas](https://github.com/airbus/airobas)** – for end-to-end formal verification pipelines

---

```{toctree}
---
maxdepth: 2
caption: Contents
---
install
getting_started
tutorials
api/modules
contribute
Github  <https://github.com/ducoffeM/keras_custom>
```

## 🚀 Installation

```bash
pip install git+https://github.com/ducoffeM/keras_custom.git

### 📊 Summary of `keras_custom` Functions

| Category | Functions |
| :--- | :--- |
| **Array Creation & Manipulation** | `append`, `arange`, `diag`, `diagonal`, `expand_dims`, `flip`, `full_like`, `get_item`, `hstack`, `identity`, `moveaxis`, `ones_like`, `repeat`, `roll`, `sort`, `split`, `squeeze`, `stack`, `swapaxes`, `transpose`, `tril`, `triu`, `zeros_like` |
| **Mathematical Operations** | `abs`, `absolute`, `add`, `ceil`, `clip`, `divide`, `expm1`, `floor`, `log`, `log10`, `log1p`, `log2`, `logaddexp`, `maximum`, `minimum`, `negative`, `power`, `reciprocal`, `round`, `sign`, `sqrt`, `square`, `true_divide`, `trunc` |
| **Reduction Operations** | `all`, `amax`, `amin`, `any`, `average`, `cumprod`, `cumsum`, `max`, `mean`, `min`, `prod`, `std`, `sum`, `var` |
| **Linear Algebra** | `cross`, `norm`, `trace` |
| **Trigonometric Functions** | `arccos`, `arccosh`, `arcsin`, `arcsinh`, `arctan`, `arctan2`, `arctanh`, `cos`, `cosh`, `sin`, `sinh`, `tan`, `tanh` |
