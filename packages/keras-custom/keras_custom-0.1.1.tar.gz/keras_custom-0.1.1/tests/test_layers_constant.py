from keras_custom.layers import DivConstant, MulConstant, PlusConstant

from .conftest import func_layer


def test_PlusConstant():
    layer = PlusConstant(constant=1.0)

    input_shape = (2,)
    func_layer(layer, input_shape)

    layer = PlusConstant(constant=-1.0)
    input_shape = (1, 32)
    func_layer(layer, input_shape)

    layer = PlusConstant(constant=2.0, minus=True)
    input_shape = (1, 32, 32)
    func_layer(layer, input_shape)


def test_MulConstant():
    layer = MulConstant(constant=1.0)

    input_shape = (2,)
    func_layer(layer, input_shape)

    layer = MulConstant(constant=-1.0)
    input_shape = (1, 32)
    func_layer(layer, input_shape)

    layer = MulConstant(constant=2.0)
    input_shape = (1, 32, 32)
    func_layer(layer, input_shape)


def test_DivConstant():
    layer = DivConstant(constant=1.0)

    input_shape = (2,)
    func_layer(layer, input_shape)

    layer = DivConstant(constant=-2.0)
    input_shape = (1, 32)
    func_layer(layer, input_shape)

    layer = DivConstant(constant=2.0)
    input_shape = (1, 32, 32)
    func_layer(layer, input_shape)
