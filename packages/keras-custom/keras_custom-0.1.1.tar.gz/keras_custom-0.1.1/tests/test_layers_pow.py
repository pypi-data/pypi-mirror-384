from keras_custom.layers import Pow

from .conftest import func_layer


def test_Pow():
    layer = Pow(power=1)

    input_shape = (2,)
    func_layer(layer, input_shape)

    layer = Pow(power=2)
    input_shape = (1, 32)
    func_layer(layer, input_shape)

    layer = Pow(power=3)
    input_shape = (1, 32, 32)
    func_layer(layer, input_shape)
