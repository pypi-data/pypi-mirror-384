import importlib

import keras
import numpy as np
import pytest
from keras import ops
from keras_custom.gradient import compute_gradient


# ---------------------------
# Helper: check if backend is available
# ---------------------------
def backend_available(backend: str) -> bool:
    modules = {
        "tensorflow": "tensorflow",
        "jax": "jax",
        "torch": "torch",
    }
    try:
        importlib.import_module(modules[backend])
        return True
    except ImportError:
        return False


# ---------------------------
# Fixture: skip test if backend missing
# ---------------------------
def require_backend(backend):
    return pytest.mark.skipif(
        not backend_available(backend), reason=f"{backend} backend not installed"
    )


# ---------------------------
# Actual tests
# ---------------------------


@require_backend("tensorflow")
@require_backend("jax")
@require_backend("torch")
@pytest.mark.parametrize("backend", ["tensorflow", "jax", "torch"])
def test_gradient_square_function(backend):
    keras.backend.set_backend(backend)

    x = keras.ops.arange(3.0)
    y = ops.sum(x**2)
    grad = compute_gradient(y, x)

    expected = 2 * np.arange(3.0)
    grad_np = np.array(grad, dtype=float)
    assert np.allclose(grad_np, expected, atol=1e-5), f"{backend} gradient mismatch"


@require_backend("tensorflow")
@require_backend("jax")
@require_backend("torch")
@pytest.mark.parametrize("backend", ["tensorflow", "jax", "torch"])
def test_gradient_with_sum_and_broadcast(backend):
    keras.backend.set_backend(backend)

    x = keras.ops.reshape(keras.ops.arange(6.0), (2, 3))
    y = ops.sum(x * 3.0)
    grad = compute_gradient(y, x)

    expected = np.ones((2, 3)) * 3.0
    grad_np = np.array(grad, dtype=float)
    assert np.allclose(grad_np, expected, atol=1e-5), f"{backend} gradient mismatch"


@require_backend("tensorflow")
@require_backend("jax")
@require_backend("torch")
@pytest.mark.parametrize("backend", ["tensorflow", "jax", "torch"])
def test_gradient_constant_zero(backend):
    keras.backend.set_backend(backend)

    x = keras.ops.arange(4.0)
    y = ops.sum(x * 0.0)
    grad = compute_gradient(y, x)

    expected = np.zeros_like(np.arange(4.0))
    grad_np = np.array(grad, dtype=float)
    assert np.allclose(grad_np, expected, atol=1e-8), f"{backend} gradient mismatch"
