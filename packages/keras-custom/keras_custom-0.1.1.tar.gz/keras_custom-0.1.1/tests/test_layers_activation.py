import optparse

from keras_custom.layers import Ceil, Clip, Floor, Identity, Log

from .conftest import func_layer


def test_Identity():
    layer = Identity()

    input_shape = (2,)
    func_layer(layer, input_shape)

    layer = Identity()
    input_shape = (1, 32)
    func_layer(layer, input_shape)

    layer = Identity()
    input_shape = (1, 32, 32)
    func_layer(layer, input_shape)


def test_Floor():
    layer = Floor()

    input_shape = (2,)
    func_layer(layer, input_shape)

    layer = Floor()
    input_shape = (1, 32)
    func_layer(layer, input_shape)

    layer = Floor()
    input_shape = (1, 32, 32)
    func_layer(layer, input_shape)


def test_Ceil():
    layer = Ceil()
    input_shape = (2,)
    func_layer(layer, input_shape)

    layer = Ceil()
    input_shape = (1, 32)
    func_layer(layer, input_shape)

    layer = Ceil()
    input_shape = (1, 32, 32)
    func_layer(layer, input_shape)


def test_Clip():
    layer = Clip(vmin=0, vmax=1)

    input_shape = (2,)
    func_layer(layer, input_shape)

    layer = Clip(vmin=0.0, vmax=1.0)
    input_shape = (1, 32)
    func_layer(layer, input_shape)

    layer = Clip(vmin=0, vmax=1)
    input_shape = (1, 32, 32)
    func_layer(layer, input_shape)


def test_Log():
    # combine Clip and Log because Log admits only positive input values
    layers = [Clip(vmin=0.5, vmax=10), Log()]

    input_shape = (2,)
    func_layer(layers, input_shape)

    layers = [Clip(vmin=0.5, vmax=10), Log()]
    input_shape = (1, 32)
    func_layer(layers, input_shape)

    layers = [Clip(vmin=0.5, vmax=10), Log()]
    input_shape = (1, 32, 32)
    func_layer(layers, input_shape)
