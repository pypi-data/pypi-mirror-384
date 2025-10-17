import keras  # type:ignore
import keras.ops as K  # type:ignore
from keras_custom.layers.reduce.base_reduce import BaseAxisKeepdimsLayer


@keras.saving.register_keras_serializable()
class Mean(BaseAxisKeepdimsLayer):
    """
    Custom Keras Layer that computes the mean of elements along a specified axis.
    Inherits axis and keepdims attributes from BaseAxisKeepdimsLayer.
    """

    def call(self, inputs_):
        """Computes the mean along the specified axis, retaining dimensions if keepdims is True."""
        return K.mean(inputs_, keepdims=self.keepdims, axis=self.axis)
