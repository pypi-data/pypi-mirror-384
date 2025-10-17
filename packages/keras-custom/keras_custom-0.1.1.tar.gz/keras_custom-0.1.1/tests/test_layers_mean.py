from keras_custom.layers import Mean

from .conftest import func_layer


def test_Mean():
    layer = Mean(axis=-1, keepdims=True)

    input_shape = (2,)
    func_layer(layer, input_shape)

    layer = Mean(axis=1, keepdims=True)
    input_shape = (1, 32)
    func_layer(layer, input_shape)

    layer = Mean(axis=2, keepdims=False)
    input_shape = (1, 32, 32)
    func_layer(layer, input_shape)
