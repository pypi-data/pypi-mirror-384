import keras  # type:ignore


@keras.saving.register_keras_serializable()
class Identity(keras.layers.Layer):
    """
    Custom Keras Layer that outputs the input tensor unchanged, acting as an identity operation.
    """

    def __init__(self, **kwargs):
        super(Identity, self).__init__(**kwargs)

    def call(self, inputs_):
        return inputs_

    def compute_output_shape(self, input_shape):
        return input_shape


@keras.saving.register_keras_serializable()
class Log(keras.layers.Layer):
    """
    Custom Keras Layer that applies the natural logarithm (log) operation to each element in the input tensor.

    This layer performs an element-wise natural logarithm on the input tensor, which is useful for various
    mathematical and preprocessing applications where log transformations are applied to data. Note that input
    values must be strictly positive, as the log of non-positive numbers is undefined.

    Example:
        .. code-block:: python

            import tensorflow as tf

            log_layer = Log()
            input_data = tf.constant([[1.0, 2.0, 10.0]])
            output_data = log_layer(input_data)
            # Output will be approximately: [[0.0, 0.6931, 2.3026]]

    """

    def call(self, inputs_):
        return keras.ops.log(inputs_)

    def compute_output_shape(self, input_shape):
        return input_shape


@keras.ops.custom_gradient
def floor(inputs):
    def grad(*args, upstream=None):
        if upstream is None:
            (upstream,) = args
        return upstream

    return keras.ops.floor(inputs), grad


@keras.saving.register_keras_serializable()
class Floor(keras.layers.Layer):
    """
    Custom Keras Layer that applies the floor operation to each element in the input tensor.

    This layer rounds down each element in the input tensor to the nearest integer. It is often
    used in scenarios where discrete, integer values are needed, or where fractional components
    of tensor elements should be removed.

    Example:
        .. code-block:: python

            import tensorflow as tf

            floor_layer = Floor()
            input_data = tf.constant([[1.7, 2.9, -0.3]])
            output_data = floor_layer(input_data)
            # Output will be: [[1.0, 2.0, -1.0]]
    """

    def call(self, inputs_):
        return floor(inputs_)

    def compute_output_shape(self, input_shape):
        return input_shape


@keras.ops.custom_gradient
def ceil(inputs_):
    def grad(*args, upstream=None):
        if upstream is None:
            (upstream,) = args
        return upstream

    return keras.ops.ceil(inputs_), grad


@keras.saving.register_keras_serializable()
class Ceil(keras.layers.Layer):
    """
    Custom Keras Layer that applies the ceil operation to each element in the input tensor.

    This layer rounds down each element in the input tensor to the nearest integer. It is often
    used in scenarios where discrete, integer values are needed, or where fractional components
    of tensor elements should be removed.

    Example:
        .. code-block:: python

            import tensorflow as tf

            ceil_layer = Ceil()
            input_data = tf.constant([[1.7, 2.9, -0.3]])
            output_data = ceil_layer(input_data)
            # Output will be: [[2.0, 3.0, -0.0]]
    """

    def call(self, inputs_):
        return ceil(inputs_)

    def compute_output_shape(self, input_shape):
        return input_shape


@keras.saving.register_keras_serializable()
class Clip(keras.layers.Layer):
    """
    Custom Keras Layer that clips the values of a Keras Tensor element-wise, within a specified range.

    This layer performs element-wise clipping, setting values below a given minimum (vmin) to that minimum
    and values above a given maximum (`vmax`) to that maximum. This is useful for constraining values
    in a neural network layer to a fixed range during forward propagation.

    Example:

        .. code-block:: python

            import tensorflow as tf

            clip_layer = Clip(vmin=0.0, vmax=1.0)
            input_data = tf.constant([[-1.0, 0.5, 2.0]])
            output_data = clip_layer(input_data)
            # Output will be: [[0.0, 0.5, 1.0]]
    """

    def __init__(self, vmin: float, vmax: float, **kwargs):
        super(Clip, self).__init__(**kwargs)
        self.vmin: float = vmin
        self.vmax: float = vmax

    def call(self, inputs_):
        return keras.ops.clip(inputs_, self.vmin, self.vmax)

    def get_config(self):
        config = super().get_config()
        config.update({"vmin": self.vmin, "vmax": self.vmax})
        return config

    def compute_output_shape(self, input_shape):
        return input_shape

    @classmethod
    def from_config(cls, config):
        vmin_config = config.pop("vmin")
        vmax_config = config.pop("vmax")
        vmin = keras.saving.deserialize_keras_object(vmin_config)
        vmax = keras.saving.deserialize_keras_object(vmax_config)
        return cls(vmin=vmin, vmax=vmax, **config)
