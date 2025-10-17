import keras
import keras.ops as K  # type:ignore


@keras.saving.register_keras_serializable()
class Cast(keras.layers.Layer):
    """
    Custom Keras Layer that casts the input tensor to a specified data type.

    This layer allows the conversion of the tensor's data type to various types such as float32, int32, etc.
    The desired data type is specified upon initialization.
    """

    def __init__(self, dtype_key: int, **kwargs):
        super(Cast, self).__init__(**kwargs)
        self.dtype_key: int = dtype_key
        self.cast_map = {
            1: "float32",
            2: "uint8",
            3: "int8",
            5: "int16",
            6: "int32",
            7: "int64",
            9: "bool",
            10: "float16",
            11: "double",
        }

    def call(self, inputs_):
        @keras.ops.custom_gradient
        def cast(inputs_):
            def grad(*args, upstream=None):
                if upstream is None:
                    (upstream,) = args
                return upstream

            return keras.ops.cast(inputs_, self.cast_map[self.dtype_key]), grad

        return cast(inputs_)

    def get_config(self):
        config = super().get_config()
        config.update({"dtype_key": self.dtype_key})
        return config

    def compute_output_shape(self, input_shape):
        return input_shape

    @classmethod
    def from_config(cls, config):
        dtype_key_config = config.pop("dtype_key")
        dtype_key = keras.saving.deserialize_keras_object(dtype_key_config)
        return cls(dtype_key=dtype_key, **config)
