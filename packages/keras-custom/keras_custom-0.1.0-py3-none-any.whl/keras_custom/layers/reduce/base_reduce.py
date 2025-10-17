from abc import ABC, abstractmethod

import keras


@keras.saving.register_keras_serializable()
class BaseAxisKeepdimsLayer(keras.layers.Layer, ABC):
    """
    Base Keras layer providing axis and keepdims attributes for layers performing reduction operations.
    This layer serves as an abstract base class, allowing subclasses to inherit and use these attributes.
    """

    def __init__(self, axis: int, keepdims=True, **kwargs):
        """
        Initializes the BaseAxisKeepdimsLayer with axis and keepdims attributes.

        Args:
            axis: The axis along which to perform the operation.
            keepdims: If True, retains reduced dimensions with broadcast length 1.
        """
        super(BaseAxisKeepdimsLayer, self).__init__(**kwargs)
        self.axis = axis
        self.keepdims = keepdims

    @abstractmethod
    def call(self, inputs):
        """Abstract method for defining the layer's forward computation."""
        pass

    def get_config(self):
        config = super().get_config()
        config.update(
            {
                "axis": keras.saving.serialize_keras_object(self.axis),
                "keepdims": keras.saving.serialize_keras_object(self.keepdims),
            }
        )
        return config

    def compute_output_shape(self, input_shape):
        input_shape = list(input_shape)
        if self.axis < 0:
            axis_ = len(input_shape) + self.axis
        else:
            axis_ = self.axis

        if self.keepdims:
            tmp_shape = [1]
        else:
            tmp_shape = []
        return input_shape[:axis_] + tmp_shape + input_shape[axis_ + 1 :]

    @classmethod
    def from_config(cls, config):
        axis_config = config.pop("axis")
        keepdims_config = config.pop("keepdims")
        axis = keras.saving.deserialize_keras_object(axis_config)
        keepdims = keras.saving.deserialize_keras_object(keepdims_config)
        return cls(axis=axis, keepdims=keepdims, **config)
