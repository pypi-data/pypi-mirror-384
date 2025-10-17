# check if a layer or a model is linear

from keras.layers import (
    Activation,
    Add,
    AveragePooling1D,
    AveragePooling2D,
    AveragePooling3D,
    BatchNormalization,
    Conv2D,
    Cropping1D,
    Cropping2D,
    Cropping3D,
    Dense,
    Flatten,
    GlobalAveragePooling1D,
    GlobalAveragePooling2D,
    GlobalAveragePooling3D,
    GroupNormalization,
    InputLayer,
    Layer,
    LayerNormalization,
    Permute,
    RepeatVector,
    Reshape,
    SpectralNormalization,
    UnitNormalization,
    UpSampling1D,
    UpSampling2D,
    UpSampling3D,
    ZeroPadding1D,
    ZeroPadding2D,
    ZeroPadding3D,
)
from keras_custom.layers import DivConstant, MulConstant, PlusConstant

set_linear = {
    InputLayer,
    Add,
    ZeroPadding1D,
    ZeroPadding2D,
    ZeroPadding3D,
    Cropping1D,
    Cropping2D,
    Cropping3D,
    Flatten,
    RepeatVector,
    Reshape,
    Permute,
    UpSampling1D,
    UpSampling2D,
    UpSampling3D,
    BatchNormalization,
    GroupNormalization,
    UnitNormalization,
    LayerNormalization,
    SpectralNormalization,
    AveragePooling1D,
    AveragePooling2D,
    AveragePooling3D,
    GlobalAveragePooling1D,
    GlobalAveragePooling2D,
    GlobalAveragePooling3D,
    MulConstant,
    PlusConstant,
    DivConstant,
}

# layers that could be linear iff there is no activation function
set_linear_wo_activation = {Dense, Conv2D, Activation}


def is_linear(layer: Layer):
    is_linear_wo_cond = max([isinstance(layer, class_linear) for class_linear in set_linear])
    if is_linear_wo_cond:
        return True
    # check with conditions
    is_linear_with_cond = max(
        [isinstance(layer, class_linear) for class_linear in set_linear_wo_activation]
    )
    if is_linear_with_cond:
        # check activation
        return layer.get_config()["activation"] == "linear"

    return False
