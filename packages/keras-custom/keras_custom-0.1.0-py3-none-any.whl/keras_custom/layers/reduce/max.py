# define non native class Max
# Decomon Custom for Max(axis...)
import keras  # type:ignore
import keras.ops as K  # type:ignore
from keras_custom.layers.reduce.base_reduce import BaseAxisKeepdimsLayer


@keras.saving.register_keras_serializable()
class Max(BaseAxisKeepdimsLayer):
    """
    Custom Keras Layer that computes the maximum value along a specified axis of the input tensor.
    Inherits axis and keepdims attributes from BaseAxisKeepdimsLayer.
    """

    def call(self, inputs_):
        """Computes the maximum value along the specified axis, retaining dimensions if keepdims is True."""
        return K.max(inputs_, axis=self.axis, keepdims=self.keepdims)


@keras.saving.register_keras_serializable()
class Argmax(BaseAxisKeepdimsLayer):
    """
    Custom Keras Layer that computes the index of the maximum value along a specified axis.
    Inherits axis and keepdims attributes from BaseAxisKeepdimsLayer.
    """

    def call(self, inputs_):
        """Computes the index of the maximum value along the specified axis, retaining dimensions if keepdims is True."""
        return K.argmax(inputs_, axis=self.axis, keepdims=self.keepdims)
