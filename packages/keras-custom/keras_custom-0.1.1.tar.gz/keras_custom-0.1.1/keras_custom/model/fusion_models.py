from typing import List
import keras
from keras.layers import Layer, InputLayer
from keras.models import Model, Sequential

def _unroll_model(model_or_layer: keras.layers.Layer, input_tensor: keras.KerasTensor) -> keras.KerasTensor:
    """
    Recursively unrolls a model or applies a layer to an input tensor.

    If the input is a Model, it iterates through its layers and connects them sequentially.
    If a layer within the model is itself a Model, it calls itself recursively to flatten the structure.
    If the input is just a regular Layer, it applies it to the tensor.

    Args:
        model_or_layer: The Keras Model or Layer to process.
        input_tensor: The tensor to be used as input.

    Returns:
        The output tensor after processing.
    """
    # If it's a model, we need to unroll it
    if isinstance(model_or_layer, Model):
        current_tensor = input_tensor
        for layer in model_or_layer.layers:
            # The InputLayer is a placeholder for the model's original input, skip it.
            if isinstance(layer, InputLayer):
                continue
            # Recursively call to handle potentially nested models
            current_tensor = _unroll_model(layer, current_tensor)
        return current_tensor
    # If it's a regular layer, just call it on the tensor
    else:
        return model_or_layer(input_tensor)


def fuse_sequential(model: Sequential) -> Model:
    """
    Fuse a Keras model into a single, flattened model.

    This function takes a Sequential model and 'unrolls'
    any nested models, ensuring the final combined model's graph consists only of
    Layer objects, not nested Model objects.

    Args:
        model: A Keras Sequential Model.

    Returns:
        A single, flattened Keras Model.
        
    Raises:
        ValueError: If the input list of models is empty.
    """
    if not model:
        raise ValueError("Input list of models cannot be empty.")

    # Use the input shape of the very first model for the new combined input
    # The shape is taken without the batch size dimension.
    input_shape = model.input_shape[1:]
    combined_input = keras.Input(shape=input_shape, name="combined_input")

    # Start the forward pass with the new combined input
    current_tensor = combined_input

    # Sequentially process each model in the list
    for layer in model.layers:
        current_tensor = _unroll_model(layer, current_tensor)

    # Create the final model from the combined input and the final output tensor
    combined_model = Model(inputs=combined_input, outputs=current_tensor)

    return combined_model