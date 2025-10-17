# define non native class Max
# Decomon Custom for Max(axis...)
from typing import List

import keras
from keras.layers import Layer  # type:ignore


@keras.saving.register_keras_serializable()
class Linear(keras.layers.Layer):
    """
    Custom Keras Layer that sequentially applies a list of linear layers to the input.
    This layer allows for chaining multiple linear transformations or other operations.
    """

    def __init__(self, layers: List[Layer], **kwargs):
        """
        Initializes the Linear layer with a list of layers to be applied sequentially.

        Args:
            layers: A list of Keras layers to apply in sequence.
        """
        super(Linear, self).__init__(**kwargs)
        self.layers = layers

    def call(self, inputs_):
        output = inputs_
        for layer in self.layers:
            output = layer(output)

        return output

    def get_config(self):
        config = super().get_config()
        config_layers = []
        for layer in self.layers:
            config_layers.append(keras.saving.serialize_keras_object(layer))

        config.update(
            {
                "layers": config_layers,
            }
        )
        return config

    def compute_output_shape(self, input_shape):
        output_shape = input_shape
        for layer in self.layers:
            output_shape = layer.compute_output_shape(output_shape)

        return output_shape

    @classmethod
    def from_config(cls, config):
        config_layers = config.pop("layers")
        layers = [
            keras.saving.deserialize_keras_object(config_layer) for config_layer in config_layers
        ]
        return cls(layers=layers, **config)
