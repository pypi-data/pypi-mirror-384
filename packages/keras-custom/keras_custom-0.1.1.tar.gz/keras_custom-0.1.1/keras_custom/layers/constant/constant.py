# custom layers used during onnx export: onnx2keras3
from typing import Union

import keras  # type:ignore
from keras import KerasTensor as Tensor
from keras_custom.layers.typing import ArrayLike  # type: ignore


@keras.saving.register_keras_serializable()
class PlusConstant(keras.layers.Layer):
    """Custom Keras Layer that adds a constant value to a Keras Tensor.
    This layer performs element-wise addition of a constant value to a Keras Tensor.
    """

    def __init__(self, constant, minus=False, **kwargs):
        """
        Compute the result of (-1 * x + constant) or (x + constant), depending on the 'minus' parameter.
        Args:
            constant: The constant value to be added to the tensor.
            minus: The indicator for the operation to be performed:
                 - If minus equals 1, it computes (-1 * x + constant).
                 - If minus equals -1, it computes (x + constant).
        """
        super(PlusConstant, self).__init__(**kwargs)
        self.constant = keras.Variable(constant)
        self.sign: int = 1
        if minus:
            self.sign = -1

    def call(self, inputs_):
        return self.sign * inputs_ + self.constant

    def get_config(self):
        config = super().get_config()
        # self.constant is a tensor, first convert it to float value
        const_ = self.constant.numpy()
        dico_params = {}
        dico_params["constant"] = const_
        dico_params["sign"] = self.sign
        config.update(dico_params)
        return config

    def compute_output_shape(self, input_shape):
        return input_shape

    @classmethod
    def from_config(cls, config):
        constant_config = config.pop("constant")
        constant = keras.saving.deserialize_keras_object(constant_config)
        sign_config = config.pop("sign")
        sign = keras.saving.deserialize_keras_object(sign_config)
        if sign > 0:
            minus = False
        else:
            minus = True
        return cls(constant=constant, minus=minus, **config)


@keras.saving.register_keras_serializable()
class MulConstant(keras.layers.Layer):
    """Custom Keras Layer that multiply a constant value to a Keras Tensor.
    This layer performs element-wise multiplication of a constant value to a Keras Tensor.
    """

    def __init__(self, constant, **kwargs):
        """
        Compute the result of  x*constant.
        Args:
            constant: The constant value to be elementwise multiplied with the tensor.
        """
        super(MulConstant, self).__init__(**kwargs)
        if not isinstance(constant, float) and len(constant.shape):
            self.constant = keras.ops.convert_to_tensor(constant)
        else:
            self.constant = constant

    def call(self, inputs_):
        return keras.ops.multiply(inputs_, self.constant)

    def get_config(self):
        config = super().get_config()
        config.update(
            {
                "constant": keras.saving.serialize_keras_object(self.constant),
            }
        )
        return config

    def compute_output_shape(self, input_shape):
        return input_shape

    @classmethod
    def from_config(cls, config):
        sublayer_config = config.pop("constant")
        sublayer = keras.saving.deserialize_keras_object(sublayer_config)
        return cls(sublayer, **config)


@keras.saving.register_keras_serializable()
class DivConstant(keras.layers.Layer):
    """Custom Keras Layer that divide a constant value with a Keras Tensor.
    This layer performs element-wise division of a constant value and a Keras Tensor.
    """

    def __init__(self, constant: Union[float, ArrayLike], **kwargs):  # type:ignore
        """
        Compute the result of  x*constant.
        Args:
            constant: The constant value to be elementwise multiplied with the tensor.
        """
        super(DivConstant, self).__init__(**kwargs)

        if hasattr(constant, "shape"):
            self.constant: Union[float, Tensor] = keras.ops.convert_to_tensor(constant)
        else:
            self.constant: Union[float, Tensor] = constant

    def call(self, inputs_):
        return self.constant / inputs_

    def get_config(self):
        config = super().get_config()
        config.update(
            {
                "constant": self.constant,
            }
        )
        return config

    def compute_output_shape(self, input_shape):
        return input_shape

    @classmethod
    def from_config(cls, config):
        sublayer_config = config.pop("constant")
        sublayer = keras.saving.deserialize_keras_object(sublayer_config)
        return cls(sublayer, **config)
