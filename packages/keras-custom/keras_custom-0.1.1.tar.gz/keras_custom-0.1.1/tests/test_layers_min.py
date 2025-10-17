from keras_custom.layers import Min

from .conftest import func_layer


def test_Min():
    layer = Min(axis=-1, keepdims=True)

    input_shape = (2,)
    func_layer(layer, input_shape)

    layer = Min(axis=1, keepdims=True)
    input_shape = (1, 32)
    func_layer(layer, input_shape)

    layer = Min(axis=2, keepdims=False)
    input_shape = (1, 32, 32)
    func_layer(layer, input_shape)
