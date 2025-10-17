import keras  # type:ignore
from keras.layers import ZeroPadding2D  # type: ignore
from keras.src import ops  # type: ignore


@keras.saving.register_keras_serializable()
class ConstantPadding2D(ZeroPadding2D):
    """Constant-padding layer for 2D input (e.g., picture).

    This layer can add rows and columns of constant value at the top, bottom, left, and
    right side of an image tensor.

    Example:
        .. code-block:: python

            import numpy as np
            import keras
            input_shape = (1, 1, 2, 2)
            x = np.arange(np.prod(input_shape)).reshape(input_shape)
            print(x)
            # Output: [[[[0 1]
            #            [2 3]]]]]
            y = keras.layers.ConstantPadding2D(const=5, padding=1)(x)
            print(y)
            # Output: [[[[5 5]
            #            [5 5]
            #            [5 5]
            #            [5 5]]
            #           [[5 5]
            #            [0 1]
            #            [2 3]
            #            [5 5]]
            #           [[5 5]
            #            [5 5]
            #            [5 5]
            #            [5 5]]]]


    """

    def __init__(self, const=0.0, padding=(1, 1), data_format=None, **kwargs):
        """
        Args:
            padding: Int, or tuple of 2 ints, or tuple of 2 tuples of 2 ints.
                - If int: the same symmetric padding is applied to height and width.
                - If tuple of 2 ints: interpreted as two different symmetric padding
                values for height and width: `(symmetric_height_pad, symmetric_width_pad)`.
                - If tuple of 2 tuples of 2 ints: interpreted as `((top_pad, bottom_pad), (left_pad, right_pad))`.
            data_format: A string, one of `"channels_last"` (default) or `"channels_first"`.
                The ordering of the dimensions in the inputs. `"channels_last"` corresponds
                to inputs with shape `(batch_size, height, width, channels)` while `"channels_first"`
                corresponds to inputs with shape `(batch_size, channels, height, width)`.
                When unspecified, uses the `image_data_format` value found in your Keras
                config file at `~/.keras/keras.json` (if exists). Defaults to `"channels_last"`.
        """
        super().__init__(padding=padding, data_format=data_format, **kwargs)
        self.const = const

    def call(self, inputs):
        if self.data_format == "channels_first":
            all_dims_padding = ((0, 0), (0, 0), *self.padding)
        else:
            all_dims_padding = ((0, 0), *self.padding, (0, 0))
        return ops.pad(
            inputs, all_dims_padding, constant_values=self.const
        )  # , mode="constant", constant_values=self.const)

    def get_config(self):
        config = {"const": self.const}
        base_config = super().get_config()
        return {**base_config, **config}
