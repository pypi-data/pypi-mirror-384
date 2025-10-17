# define non native class Min
import keras  # type:ignore
import keras.ops as K  # type:ignore
from keras_custom.layers.reduce.base_reduce import BaseAxisKeepdimsLayer


@keras.saving.register_keras_serializable()
class Min(BaseAxisKeepdimsLayer):
    """
    Custom Keras Layer that computes the minimum value along a specified axis.
    Inherits axis and keepdims attributes from BaseAxisKeepdimsLayer.
    """

    def call(self, inputs_):
        """Computes the minimum value along the specified axis, retaining dimensions if keepdims is True."""
        return K.min(inputs_, axis=self.axis, keepdims=self.keepdims)
