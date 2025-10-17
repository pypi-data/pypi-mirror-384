import keras


def compute_gradient(output_tensor, input_tensor):
    """Compute the gradient of a scalar output wrt an input tensor (Keras 3 backend-agnostic).

    Args:
        output_tensor: A scalar KerasTensor (e.g. model output or loss).
        input_tensor: A KerasTensor or backend tensor for which the gradient is desired.

    Returns:
        grad_tensor: Tensor of same shape as input_tensor containing the gradients.
    """
    K = keras.backend
    backend = K.backend()

    if backend == "tensorflow":
        import tensorflow as tf

        with tf.GradientTape() as tape:
            tape.watch(input_tensor)
            y = output_tensor
        grad = tape.gradient(y, input_tensor)

    elif backend == "jax":
        import jax

        def func(x):
            # we re-evaluate to keep JAX tracing pure
            return output_tensor

        grad = jax.grad(lambda x: func(x))(input_tensor)

    elif backend == "torch":
        x = input_tensor.clone().detach().requires_grad_(True)
        y = output_tensor
        y.backward()
        grad = x.grad

    else:
        raise ValueError(f"Unsupported backend: {backend}")

    return grad
