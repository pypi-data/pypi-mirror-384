import os

import keras
import numpy as np

# import torch
from keras.models import Sequential  # type:ignore
from keras_custom.layers import Slice, Split

from .conftest import func_layer


def test_Slice():
    layer = Slice(axis=2, starts=0, ends=-1, steps=1)
    input_shape = (1, 32, 32)
    func_layer(layer, input_shape)


def test_Split():
    layer = Split(splits=[2, 5], axis=-1)
    toy_model = Sequential([layer])
    input_ = np.ones((1, 4, 32))
    elems = toy_model.predict(input_)
    # serialize
    filename = "test_serialize_{}_{}.keras".format(layer.__class__.__name__, layer.name)

    # detach toy model to cpu
    # toy_model.to('cpu')
    toy_model.save(filename)  # The file needs to end with the .keras extension

    # deserialize
    load_model = keras.models.load_model(filename)

    # compare with the previous output
    output_after_export = load_model.predict(input_)
    for i in range(len(elems)):
        np.testing.assert_almost_equal(
            elems[i], output_after_export[i], err_msg="corrupted weights"
        )
    os.remove(filename)
