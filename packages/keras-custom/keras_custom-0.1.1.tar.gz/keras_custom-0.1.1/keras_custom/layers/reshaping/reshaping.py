import keras
import numpy as np


@keras.saving.register_keras_serializable()
class Slice(keras.layers.Layer):
    """
    Custom Keras Layer that slices the input tensor along a specified axis, using start, end, and step values.
    """

    def __init__(self, axis, starts, ends, steps, **kwargs):
        """
        Initializes the Slice layer with axis, starts, ends, and steps for slicing.

        Args:
            axis: axis along which to perform slicing.
            starts: Start indices for slicing.
            ends: End indices for slicing.
            steps: Step sizes for slicing.
        """
        super(Slice, self).__init__(**kwargs)
        self.axis = axis
        self.starts = starts
        self.ends = ends
        self.steps = steps

        if self.axis not in [2, 3]:
            raise ValueError(axis)

    def call(self, inputs_):
        if self.axis == 2:
            return inputs_[:, :, self.starts : self.ends][:, :, :: self.steps]
        elif self.axis == 3:
            return inputs_[:, :, :, self.starts : self.ends][:, :, :, :: self.steps]

    def get_config(self):
        config = super().get_config()
        config.update(
            {"axis": self.axis, "starts": self.starts, "ends": self.ends, "steps": self.steps}
        )
        return config

    def compute_output_shape(self, input_shape):
        input_shape = list(input_shape)
        w = np.arange(input_shape[self.axis])
        w_ = len(w[self.starts : self.ends][:: self.steps])
        input_shape[self.axis] = w_
        return input_shape

    @classmethod
    def from_config(cls, config):
        axis_config = config.pop("axis")
        starts_config = config.pop("starts")
        ends_config = config.pop("ends")
        steps_config = config.pop("steps")
        axis = keras.saving.deserialize_keras_object(axis_config)
        starts = keras.saving.deserialize_keras_object(starts_config)
        ends = keras.saving.deserialize_keras_object(ends_config)
        steps = keras.saving.deserialize_keras_object(steps_config)
        return cls(axis=axis, starts=starts, ends=ends, steps=steps, **config)


@keras.saving.register_keras_serializable()
class Split(keras.layers.Layer):
    """
    Custom Keras Layer that splits the input tensor into multiple sub-tensors along a specified axis.
    """

    def __init__(self, splits, axis, **kwargs):
        """
        Initializes the Split layer with the specified splits and axis.

        Args:
            splits: List of indices or sections to split the input tensor.
            axis: The axis along which to split the tensor.
        """
        super(Split, self).__init__(**kwargs)
        self.splits = list(splits)
        self.axis = axis

    def call(self, inputs_):
        output = keras.ops.split(inputs_, indices_or_sections=self.splits, axis=self.axis)
        return output

    def get_config(self):
        config = super().get_config()
        config.update(
            {
                "splits": self.splits,
                "axis": self.axis,
            }
        )
        return config

    def compute_output_shape(self, input_shape):
        input_shape_ = list(input_shape)
        input_shape_ = input_shape_[1:]
        tmp = np.ones(input_shape_)[None]

        output = np.split(tmp, indices_or_sections=self.splits, axis=self.axis)
        return [e.shape for e in output]

    @classmethod
    def from_config(cls, config):
        axis_config = config.pop("axis")
        splits_config = config.pop("splits")
        axis = keras.saving.deserialize_keras_object(axis_config)
        splits = keras.saving.deserialize_keras_object(splits_config)
        return cls(axis=axis, splits=splits, **config)
