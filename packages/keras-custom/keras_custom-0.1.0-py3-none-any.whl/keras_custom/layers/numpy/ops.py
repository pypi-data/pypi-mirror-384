import math

import keras
from keras import ops


@keras.saving.register_keras_serializable()
class Abs(keras.layers.Layer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def call(self, inputs):
        """Shorthand for `keras.ops.absolute`."""
        return ops.abs(inputs)

    def get_ops(
        self,
    ):
        return ops.abs


@keras.saving.register_keras_serializable()
class Absolute(keras.layers.Layer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def call(self, inputs):
        """
        Calculates the absolute value element-wise.

        `keras.ops.abs` is a shorthand for this function.

        Args:
            inputs: Input tensor.

        Returns:
            An array containing the absolute value of each element in `inputs`.
            For complex input, `(a + ib)`, the absolute value is
            `sqrt(a^2 + b^2)`.

        Example:
        >>> x = ops.convert_to_tensor([-1.2, 1.2])
        >>> ops.numpy.absolute(x)
        array([1.2, 1.2], dtype=float32)
        """
        return ops.absolute(inputs)

    def get_ops(self):
        return keras.ops.absolute


@keras.saving.register_keras_serializable()
class AMax(keras.layers.Layer):
    def __init__(self, axis=None, keepdims=False, **kwargs):
        """
        Initializes the AMax layer.

        Args:
            axis (None or int or tuple of ints, optional): Axis or axes along
                which to operate. By default, flattened input is used.
                Defaults to None.
            keepdims (bool, optional): If this is set to True, the axes which
                are reduced are left in the result as dimensions with size one.
                With this option, the result will broadcast correctly against
                the input array. Defaults to False.
        """
        super().__init__(**kwargs)
        self.axis = axis
        self.keepdims = keepdims

    def call(self, inputs):
        """
        Return the maximum of an array or maximum along an axis.

        Args:
            inputs: Input tensor.

        Returns:
            Maximum of `inputs`. If `axis` is None, the result is a scalar value.
            If `axis` is an int, the result is an array of dimension
            `inputs.ndim - 1`.
        """
        return ops.amax(inputs, axis=self.axis, keepdims=self.keepdims)

    def get_ops(self):
        return lambda x: ops.amax(x, axis=self.axis, keepdims=self.keepdims)


@keras.saving.register_keras_serializable()
class AMin(keras.layers.Layer):
    def __init__(self, axis=None, keepdims=False, **kwargs):
        """
        Initializes the AMin layer.

        Args:
            axis (None or int or tuple of ints, optional): Axis or axes along
                which to operate. By default, flattened input is used.
                Defaults to None.
            keepdims (bool, optional): If this is set to True, the axes which
                are reduced are left in the result as dimensions with size one.
                With this option, the result will broadcast correctly against
                the input array. Defaults to False.
        """
        super().__init__(**kwargs)
        self.axis = axis
        self.keepdims = keepdims

    def call(self, inputs):
        """
        Return the minimum of an array or minimum along an axis.

        Args:
            inputs: Input tensor.

        Returns:
            Minimum of `inputs`. If `axis` is None, the result is a scalar value.
            If `axis` is an int, the result is an array of dimension
            `inputs.ndim - 1`.
        """
        return ops.amin(inputs, axis=self.axis, keepdims=self.keepdims)

    def get_ops(self):
        return lambda x: ops.amin(x, axis=self.axis, keepdims=self.keepdims)


@keras.saving.register_keras_serializable()
class Append(keras.layers.Layer):
    def __init__(self, axis=None, **kwargs):
        """
        Initializes the Append layer.

        Args:
            axis (int, optional): The axis along which `values` are appended.
                If `axis` is not given, both `arr` and `values` are flattened
                before use. Defaults to None.
        """
        super().__init__(**kwargs)
        self.axis = axis

    def call(self, inputs):
        """
        Append values to the end of an array.

        Args:
            inputs (list or tuple): A list or tuple of two tensors,
                `[arr, values]`, where `values` will be appended to `arr`.

        Returns:
            A copy of `arr` with `values` appended to `axis`. Note that
            `append` does not occur in-place: a new array is allocated and
            filled. If `axis` is None, `out` is a flattened array.
        """
        if not isinstance(inputs, (list, tuple)) or len(inputs) != 2:
            raise ValueError("Input to Append layer must be a list or tuple of two tensors.")
        arr, values = inputs
        return ops.append(arr, values, axis=self.axis)

    def get_ops(self):
        return lambda x: ops.append(x[0], x[1], axis=self.axis)


@keras.saving.register_keras_serializable()
class Arccos(keras.layers.Layer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def call(self, inputs):
        """
        Computes the trigonometric inverse cosine of an array, element-wise.

        The inverse of `cos` so that, if `y = cos(x)`, then `x = arccos(y)`.

        Args:
            inputs: Input tensor with values in the range `[-1, 1]`.

        Returns:
            The angle of the ray intersecting the unit circle at the given
            x-coordinate in radians `[0, pi]`. If `inputs` is a real-valued
            tensor, the output will also be real-valued. Any element with an
            absolute value greater than 1 will result in `nan`.
        """
        return ops.arccos(inputs)

    def get_ops(self):
        return ops.arccos


@keras.saving.register_keras_serializable()
class Arccosh(keras.layers.Layer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def call(self, inputs):
        """
        Computes the inverse hyperbolic cosine of an array, element-wise.

        Args:
            inputs: Input tensor with values in the range `[1, inf)`.

        Returns:
            The inverse hyperbolic cosine of the input. For real-valued input,
            the output is in the range `[0, inf)`. Any element with a value
            less than 1 will result in `nan`.
        """
        return ops.arccosh(inputs)

    def get_ops(self):
        return ops.arccosh


@keras.saving.register_keras_serializable()
class Arcsin(keras.layers.Layer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def call(self, inputs):
        """
        Computes the trigonometric inverse sine of an array, element-wise.

        The inverse of `sin` so that, if `y = sin(x)`, then `x = arcsin(y)`.

        Args:
            inputs: Input tensor with values in the range `[-1, 1]`.

        Returns:
            The inverse sine of each element in `inputs`, in radians `[-pi/2, pi/2]`.
            Any element with an absolute value greater than 1 will result in `nan`.
        """
        return ops.arcsin(inputs)

    def get_ops(self):
        return ops.arcsin


@keras.saving.register_keras_serializable()
class Arcsinh(keras.layers.Layer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def call(self, inputs):
        """
        Computes the inverse hyperbolic sine of an array, element-wise.

        Args:
            inputs: Input tensor.

        Returns:
            The inverse hyperbolic sine of each element in `inputs`.
        """
        return ops.arcsinh(inputs)

    def get_ops(self):
        return ops.arcsinh


@keras.saving.register_keras_serializable()
class Arctan(keras.layers.Layer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def call(self, inputs):
        """
        Computes the trigonometric inverse tangent of an array, element-wise.

        The inverse of `tan` so that, if `y = tan(x)`, then `x = arctan(y)`.

        Args:
            inputs: Input tensor.

        Returns:
            The inverse tangent of each element in `inputs`, in radians
            `(-pi/2, pi/2)`.
        """
        return ops.arctan(inputs)

    def get_ops(self):
        return ops.arctan


@keras.saving.register_keras_serializable()
class Arctanh(keras.layers.Layer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def call(self, inputs):
        """
        Computes the inverse hyperbolic tangent of an array, element-wise.

        Args:
            inputs: Input tensor with values in the open interval `(-1, 1)`.

        Returns:
            The inverse hyperbolic tangent of each element in `inputs`.
            Any element with an absolute value greater than or equal to 1
            will result in `inf`, `-inf`, or `nan`.
        """
        return ops.arctanh(inputs)

    def get_ops(self):
        return ops.arctanh


@keras.saving.register_keras_serializable()
class Arctan2(keras.layers.Layer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def call(self, inputs):
        """
        Computes the element-wise arc tangent of `y / x`.

        This function is able to determine the correct quadrant for the angle
        by considering the sign of both `y` and `x`.

        Args:
            inputs (list or tuple): A list or tuple of two tensors, `[y, x]`.

        Returns:
            The signed angle in radians, `(-pi, pi]`, between the positive
            x-axis and the point `(x, y)`.
        """
        if not isinstance(inputs, (list, tuple)) or len(inputs) != 2:
            raise ValueError(
                "Input to Arctan2 layer must be a list or tuple of two tensors, [y, x]."
            )
        y, x = inputs
        return ops.arctan2(y, x)

    def get_ops(self):
        return lambda x: ops.arctan2(x[0], x[1])

    def compute_output_shape(self, input_shape):
        return input_shape[0]


@keras.saving.register_keras_serializable()
class Average(keras.layers.Layer):
    def __init__(self, axis=None, **kwargs):
        """
        Initializes the Average layer.

        Args:
            axis (int, optional): The axis along which to average. If None,
                the input is flattened before the operation. Defaults to None.
        """
        super().__init__(**kwargs)
        self.axis = axis

    def call(self, inputs):
        """
        Computes the average of a tensor.

        Args:
            inputs: A single tensor, or a list/tuple of two tensors
                `[values, weights]`.

        Returns:
            The average of the tensor. If `weights` are provided, computes
            the weighted average.
        """
        if isinstance(inputs, (list, tuple)):
            if len(inputs) != 2:
                raise ValueError(
                    "If providing weights, input must be a list of two tensors "
                    "[values, weights]."
                )
            values, weights = inputs
            return ops.average(values, axis=self.axis, weights=weights)
        else:
            return ops.average(inputs, axis=self.axis)

    def get_ops(self):
        def func(x):
            if isinstance(x, list) and len(x) == 2:
                return ops.average(x[0], axis=self.axis, weights=x[1])
            else:
                return ops.average(x, axis=self.axis)

        return lambda x: func(x)

    def compute_output_shape(self, input_shape):
        """
        Computes the output shape of the layer.
        """
        # Determine the shape of the tensor being averaged.
        if isinstance(input_shape[0], (list, tuple)):
            shape_to_reduce = input_shape[0]
        else:
            shape_to_reduce = input_shape

        # If axis is None, the output is a scalar.
        if self.axis is None:
            return ()

        # Otherwise, the output shape is the input shape with the
        # specified axis removed.
        output_shape = list(shape_to_reduce)
        output_shape.pop(self.axis)
        return tuple(output_shape)


@keras.saving.register_keras_serializable()
class Cos(keras.layers.Layer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def call(self, inputs):
        """
        Computes the element-wise cosine of the input tensor.

        Args:
            inputs: Input tensor (angles in radians).

        Returns:
            A tensor of the same shape as `inputs` containing the cosine
            of each element.
        """
        return keras.ops.cos(inputs)

    def get_ops(self):
        return keras.ops.cos


@keras.saving.register_keras_serializable()
class Cosh(keras.layers.Layer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def call(self, inputs):
        """
        Computes the element-wise hyperbolic cosine of the input tensor.

        Args:
            inputs: Input tensor.

        Returns:
            A tensor of the same shape as `inputs` containing the hyperbolic
            cosine of each element.
        """
        return keras.ops.cosh(inputs)

    def get_ops(self):
        return keras.ops.cosh


@keras.saving.register_keras_serializable()
class Cross(keras.layers.Layer):
    """
    A custom Keras layer to compute the cross product of two tensors.

    This layer takes a list of two tensors as input and returns their cross product.
    The input tensors must have the same shape.

    Methods:
    call(self, inputs): Computes the cross product of the input tensors.
    """

    def __init__(self, **kwargs):
        """
        Initializes the Cross layer.

        Args:
        **kwargs: Standard layer keyword arguments.
        """
        super().__init__(**kwargs)

    def call(self, inputs):
        """
        Computes the cross product of two tensors.

        Args:
        inputs: A list of two tensors [x1, x2] to compute the cross product of.
            Both tensors should have the same shape.

        Returns:
        A tensor representing the cross product of x1 and x2.
        """
        if not isinstance(inputs, list) or len(inputs) != 2:
            raise ValueError("Input to Cross layer must be a list of two tensors.")
        x1, x2 = inputs
        return ops.cross(x1, x2)

    def get_ops(self):
        return lambda x: ops.cross(x[0], x[1])


@keras.saving.register_keras_serializable()
class Cumprod(keras.layers.Layer):
    """
    A custom Keras layer to compute the cumulative product of a tensor.

    This layer wraps the `keras.ops.cumprod` function.

    Args:
        axis (int, optional): The axis along which the cumulative product is
            computed. Defaults to None, which computes the cumulative product
            over the flattened array.
    """

    def __init__(self, axis=None, **kwargs):
        """
        Initializes the Cumprod layer.

        Args:
            axis (int, optional): The axis for the cumulative product.
            **kwargs: Standard layer keyword arguments.
        """
        super().__init__(**kwargs)
        self.axis = axis

    def call(self, inputs):
        """
        Computes the cumulative product of the input tensor.

        Args:
            inputs: The input tensor.

        Returns:
            A tensor of the same shape as inputs with the cumulative product.
        """
        return ops.cumprod(inputs, axis=self.axis)

    def get_ops(self):
        return lambda x: ops.cumprod(x, axis=self.axis)


@keras.saving.register_keras_serializable()
class Cumsum(keras.layers.Layer):
    """
    A custom Keras layer to compute the cumulative sum of a tensor.

    This layer wraps the `keras.ops.cumsum` function.

    Args:
        axis (int, optional): The axis along which the cumulative sum is
            computed. Defaults to None, which computes the cumulative sum
            over the flattened array.
    """

    def __init__(self, axis=None, **kwargs):
        """
        Initializes the Cumsum layer.

        Args:
            axis (int, optional): The axis for the cumulative sum.
            **kwargs: Standard layer keyword arguments.
        """
        super().__init__(**kwargs)
        self.axis = axis

    def call(self, inputs):
        """
        Computes the cumulative sum of the input tensor.

        Args:
            inputs: The input tensor.

        Returns:
            A tensor of the same shape as inputs with the cumulative sum.
        """
        return ops.cumsum(inputs, axis=self.axis)

    def get_ops(self):
        return lambda x: ops.cumsum(x, axis=self.axis)


@keras.saving.register_keras_serializable()
class Diag(keras.layers.Layer):
    """
    A Keras layer to construct a diagonal matrix or extract a diagonal.

    This layer wraps `keras.ops.diag`. Its behavior depends on the
    rank of the input tensor:
    - If input is 1D, it returns a 2D matrix with the input elements
      as the k-th diagonal.
    - If input is 2D or higher, it extracts the k-th diagonal from the
      last two dimensions.

    Args:
        k (int, optional): The diagonal to consider. `k=0` is the main
            diagonal, `k>0` is above, and `k<0` is below. Defaults to 0.
    """

    def __init__(self, k=0, **kwargs):
        """
        Initializes the Diag layer.

        Args:
            k (int, optional): The diagonal offset.
            **kwargs: Standard layer keyword arguments.
        """
        super().__init__(**kwargs)
        self.k = int(k)

    def call(self, inputs):
        """
        Applies the diagonal operation.

        Args:
            inputs: The input tensor (1D or 2D).

        Returns:
            A new tensor with the result of the diagonal operation.
        """
        return ops.diag(inputs, k=self.k)

    def get_ops(self):
        return lambda x: ops.diag(x, k=self.k)

    def compute_output_shape(self, input_shape):
        """
        Computes the output shape based on the input shape and rank.
        """
        rank = len(input_shape)

        if rank == 0:
            raise ValueError("Input cannot be a scalar.")

        # Case 1: Constructing a matrix from a 1D vector
        if rank == 1:
            if input_shape[0] is None:
                return (None, None)
            dim = input_shape[0] + abs(self.k)
            return (dim, dim)

        # Case 2: Extracting a diagonal from a matrix (2D or higher)
        else:
            if input_shape[-2] is None or input_shape[-1] is None:
                diag_len = None
            else:
                m, n = input_shape[-2], input_shape[-1]
                if self.k >= 0:
                    diag_len = max(0, min(m, n - self.k))
                else:
                    diag_len = max(0, min(m + self.k, n))

            # The output has one less dimension
            return input_shape[:-2] + (diag_len,)


@keras.saving.register_keras_serializable()
class Diagonal(keras.layers.Layer):
    """
    A Keras layer to extract a diagonal from a tensor.

    This layer wraps `keras.ops.diagonal`, which is a generalized
    diagonal extraction. It can extract diagonals from specific 2D planes
    within a higher-dimensional tensor.

    The rank of the output tensor is one less than the rank of the input tensor.

    Args:
        offset (int, optional): The diagonal to consider. `offset=0` is the main
            diagonal. Defaults to 0.
        axis1 (int, optional): The first axis of the 2D planes from which to
            extract diagonals. Defaults to 0.
        axis2 (int, optional): The second axis of the 2D planes from which to
            extract diagonals. Defaults to 1.
    """

    def __init__(self, offset=0, axis1=0, axis2=1, **kwargs):
        """
        Initializes the Diagonal layer.

        Args:
            offset (int): The diagonal offset.
            axis1 (int): The first axis defining the 2D planes.
            axis2 (int): The second axis defining the 2D planes.
            **kwargs: Standard layer keyword arguments.
        """
        super().__init__(**kwargs)
        self.offset = int(offset)
        self.axis1 = int(axis1)
        self.axis2 = int(axis2)

    def call(self, inputs):
        """
        Applies the diagonal extraction.

        Args:
            inputs: The input tensor.

        Returns:
            A new tensor containing the extracted diagonals.
        """
        return ops.diagonal(inputs, offset=self.offset, axis1=self.axis1, axis2=self.axis2)

    def get_ops(self):
        return lambda x: ops.diagonal(x, offset=self.offset, axis1=self.axis1, axis2=self.axis2)

    def compute_output_shape(self, input_shape):
        """
        Computes the output shape for the diagonal extraction.
        """
        rank = len(input_shape)
        if rank < 2:
            raise ValueError(f"Input tensor must have a rank of at least 2, but got rank {rank}.")

        # Normalize negative axes
        pos_axis1 = self.axis1 if self.axis1 >= 0 else rank + self.axis1
        pos_axis2 = self.axis2 if self.axis2 >= 0 else rank + self.axis2

        if not (0 <= pos_axis1 < rank and 0 <= pos_axis2 < rank):
            raise ValueError(
                f"Axes ({self.axis1}, {self.axis2}) are out of bounds for input rank {rank}."
            )

        # Determine the length of the diagonal
        dim1 = input_shape[pos_axis1]
        dim2 = input_shape[pos_axis2]

        if dim1 is None or dim2 is None:
            diag_len = None
        else:
            if self.offset >= 0:
                diag_len = max(0, min(dim1, dim2 - self.offset))
            else:
                diag_len = max(0, min(dim1 + self.offset, dim2))

        # Build the output shape by removing the two diagonal axes
        output_shape = []
        for i in range(rank):
            if i not in (pos_axis1, pos_axis2):
                output_shape.append(input_shape[i])

        # Append the new dimension for the diagonal
        output_shape.append(diag_len)

        return tuple(output_shape)


@keras.saving.register_keras_serializable()
class ExpandDims(keras.layers.Layer):
    """
    A Keras layer to insert a new axis of size 1 into a tensor's shape.

    This layer wraps the `keras.ops.expand_dims` function.

    Args:
        axis (int): The position in the input shape where the new axis is
            to be inserted.
    """

    def __init__(self, axis, **kwargs):
        """
        Initializes the ExpandDims layer.

        Args:
            axis (int): The index where the new axis will be added.
            **kwargs: Standard layer keyword arguments.
        """
        super().__init__(**kwargs)
        self.axis = int(axis)

    def call(self, inputs):
        """
        Applies the expand_dims operation.

        Args:
            inputs: The input tensor.

        Returns:
            A new tensor with an additional dimension.
        """
        return ops.expand_dims(inputs, axis=self.axis)

    def compute_output_shape(self, input_shape):
        """
        Computes the output shape by adding a new axis.
        """
        # Convert the tuple to a list to use the insert method
        output_shape = list(input_shape)

        # Insert a dimension of size 1 at the specified axis
        output_shape.insert(self.axis, 1)

        return tuple(output_shape)

    def get_ops(self):
        return lambda x: ops.expand_dims(x, axis=self.axis)


@keras.saving.register_keras_serializable()
class Expm1(keras.layers.Layer):
    """
    A Keras layer to compute the element-wise `exp(x) - 1`.

    This layer is a wrapper for the `keras.ops.expm1` function, which provides
    greater numerical stability than `ops.exp(x) - 1` for small values of `x`.
    """

    def __init__(self, **kwargs):
        """
        Initializes the Expm1 layer.

        Args:
            **kwargs: Standard layer keyword arguments.
        """
        super().__init__(**kwargs)

    def call(self, inputs):
        """
        Applies the expm1 operation.

        Args:
            inputs: The input tensor.

        Returns:
            A tensor of the same shape as the input, with the operation applied.
        """
        return ops.expm1(inputs)

    def get_ops(self):
        return ops.expm1


@keras.saving.register_keras_serializable()
class Flip(keras.layers.Layer):
    """
    A Keras layer to reverse the order of elements along a given axis.

    This layer is a wrapper for the `keras.ops.flip` function. The shape of
    the tensor remains unchanged.

    Args:
        axis (int or tuple of ints, optional): The axis or axes along which
            to flip. If None, the tensor is flipped along all axes.
    """

    def __init__(self, axis=None, **kwargs):
        """
        Initializes the Flip layer.

        Args:
            axis (int or tuple of ints, optional): Axis or axes to flip.
            **kwargs: Standard layer keyword arguments.
        """
        super().__init__(**kwargs)
        self.axis = axis

    def call(self, inputs):
        """
        Applies the flip operation.

        Args:
            inputs: The input tensor.

        Returns:
            A new tensor with elements flipped along the specified axis.
        """
        return ops.flip(inputs, axis=self.axis)

    def get_ops(self):
        return lambda x: ops.flip(x, axis=self.axis)


@keras.saving.register_keras_serializable()
class Floor(keras.layers.Layer):
    """
    A Keras layer to compute the element-wise floor of a tensor.

    This layer is a wrapper for the `keras.ops.floor` function. The floor of a
    scalar `x` is the largest integer `i`, such that `i <= x`.
    """

    def __init__(self, **kwargs):
        """
        Initializes the Floor layer.

        Args:
            **kwargs: Standard layer keyword arguments.
        """
        super().__init__(**kwargs)

    def call(self, inputs):
        """
        Applies the floor operation.

        Args:
            inputs: The input tensor.

        Returns:
            A tensor of the same shape as the input, with the operation applied.
        """
        return ops.floor(inputs)

    def get_ops(self):
        return ops.floor


@keras.saving.register_keras_serializable()
class FullLike(keras.layers.Layer):
    """
    A Keras layer that creates a tensor of a given value, with the same
    shape as another tensor.

    This layer is a wrapper for the `keras.ops.full_like` function. The
    values of the input tensor are ignored; only its shape is used.

    Args:
        fill_value (int or float): The scalar value to fill the new tensor with.
    """

    def __init__(self, fill_value, **kwargs):
        """
        Initializes the FullLike layer.

        Args:
            fill_value: The value to fill the output tensor with.
            **kwargs: Standard layer keyword arguments.
        """
        super().__init__(**kwargs)
        self.fill_value = fill_value

    def call(self, inputs):
        """
        Applies the full_like operation.

        Args:
            inputs: The input tensor (used for its shape).

        Returns:
            A new tensor with the same shape as the input, filled with `fill_value`.
        """
        return ops.full_like(inputs, self.fill_value, dtype=inputs.dtype)

    def get_ops(self):
        return lambda x: ops.full_like(x, self.fill_value, dtype=x.dtype)


@keras.saving.register_keras_serializable()
class GetItem(keras.layers.Layer):
    """
    A Keras layer to slice a tensor using `__getitem__` syntax.

    This layer is a wrapper for `keras.ops.get_item`. It allows you to
    perform tensor slicing as part of a Keras model.

    Args:
        item: The key to be used for slicing. This can be an integer, a slice,
            a tuple of slices, or any other valid tensor index.
    """

    def __init__(self, item, **kwargs):
        """
        Initializes the GetItem layer.

        Args:
            item: The slice or index key.
            **kwargs: Standard layer keyword arguments.
        """
        super().__init__(**kwargs)
        self.item = item

    def call(self, inputs):
        """
        Applies the slicing operation.

        Args:
            inputs: The input tensor to be sliced.

        Returns:
            The sliced tensor.
        """
        return inputs[:, self.item : self.item + 1]

    def get_ops(self):
        return lambda x: x[:, self.item : self.item + 1]

    def compute_output_shape(self, input_shape):
        """
        Computes the output shape.
        """
        return (input_shape[0], 1)


@keras.saving.register_keras_serializable()
class Hstack(keras.layers.Layer):
    """
    A Keras layer to stack a list of tensors horizontally (column-wise).

    This layer is a wrapper for the `keras.ops.hstack` function, which is
    equivalent to `ops.concatenate(tensors, axis=1)`. All input tensors
    must have the same shape, except for the second axis (axis=1).

    The layer expects a list of tensors as its input.
    """

    def __init__(self, **kwargs):
        """
        Initializes the Hstack layer.

        Args:
            **kwargs: Standard layer keyword arguments.
        """
        super().__init__(**kwargs)

    def call(self, inputs):
        """
        Applies the hstack operation.

        Args:
            inputs: A list of tensors to be stacked.

        Returns:
            A single tensor, the result of the horizontal stacking.
        """
        if not isinstance(inputs, (list, tuple)):
            raise ValueError("Input to Hstack layer must be a list of tensors.")
        return ops.hstack(inputs)

    def get_ops(self):
        return ops.hstack

    def compute_output_shape(self, input_shape):
        """
        Computes the output shape of the layer.
        """
        if not isinstance(input_shape, (list, tuple)) or not input_shape:
            raise ValueError("Input shape must be a list of shapes.")

        ref_shape = list(input_shape[0])
        if len(ref_shape) < 2:
            raise ValueError("Hstack requires inputs with at least 2 dimensions.")

        # Sum the dimensions along the stacking axis (axis=1)
        stacked_dim_size = 0
        for shape in input_shape:
            if shape[1] is None:
                stacked_dim_size = None
                break
            stacked_dim_size += shape[1]

        # The output shape is the reference shape with an updated second axis
        output_shape = ref_shape
        output_shape[1] = stacked_dim_size

        return tuple(output_shape)


@keras.saving.register_keras_serializable()
class Log(keras.layers.Layer):
    """
    A Keras layer to compute the element-wise natural logarithm of a tensor.

    This layer is a wrapper for the `keras.ops.log` function. Input values
    should be positive.
    """

    def __init__(self, **kwargs):
        """
        Initializes the Log layer.

        Args:
            **kwargs: Standard layer keyword arguments.
        """
        super().__init__(**kwargs)

    def call(self, inputs):
        """
        Applies the natural logarithm operation.

        Args:
            inputs: The input tensor.

        Returns:
            A tensor of the same shape as the input, with the operation applied.
        """
        return ops.log(inputs)

    def get_ops(self):
        return ops.log


@keras.saving.register_keras_serializable()
class Log10(keras.layers.Layer):
    """
    A Keras layer to compute the element-wise base-10 logarithm of a tensor.

    This layer is a wrapper for the `keras.ops.log10` function. Input values
    should be positive.
    """

    def __init__(self, **kwargs):
        """
        Initializes the Log10 layer.

        Args:
            **kwargs: Standard layer keyword arguments.
        """
        super().__init__(**kwargs)

    def call(self, inputs):
        """
        Applies the base-10 logarithm operation.

        Args:
            inputs: The input tensor.

        Returns:
            A tensor of the same shape as the input, with the operation applied.
        """
        return ops.log10(inputs)

    def get_ops(self):
        return ops.log10


@keras.saving.register_keras_serializable()
class Log1p(keras.layers.Layer):
    """
    A Keras layer to compute the element-wise `log(1 + x)`.

    This layer is a wrapper for the `keras.ops.log1p` function, which
    provides greater numerical stability for small values of `x`.
    """

    def __init__(self, **kwargs):
        """
        Initializes the Log1p layer.

        Args:
            **kwargs: Standard layer keyword arguments.
        """
        super().__init__(**kwargs)

    def call(self, inputs):
        """
        Applies the log1p operation.

        Args:
            inputs: The input tensor.

        Returns:
            A tensor of the same shape as the input, with the operation applied.
        """
        return ops.log1p(inputs)

    def get_ops(self):
        return ops.log1p


@keras.saving.register_keras_serializable()
class Log2(keras.layers.Layer):
    """
    A Keras layer to compute the element-wise base-2 logarithm of a tensor.

    This layer is a wrapper for the `keras.ops.log2` function. Input values
    should be positive.
    """

    def __init__(self, **kwargs):
        """
        Initializes the Log2 layer.

        Args:
            **kwargs: Standard layer keyword arguments.
        """
        super().__init__(**kwargs)

    def call(self, inputs):
        """
        Applies the base-2 logarithm operation.

        Args:
            inputs: The input tensor.

        Returns:
            A tensor of the same shape as the input, with the operation applied.
        """
        return ops.log2(inputs)

    def get_ops(self):
        return ops.log2


@keras.saving.register_keras_serializable()
class LogAddExp(keras.layers.Layer):
    """
    A Keras layer to compute log(exp(x1) + exp(x2)) element-wise.

    This layer is a wrapper for `keras.ops.logaddexp`. It takes a list of two
    tensors as input, which must be broadcastable to the same shape.
    """

    def __init__(self, **kwargs):
        """
        Initializes the LogAddExp layer.
        """
        super().__init__(**kwargs)

    def call(self, inputs):
        """
        Applies the logaddexp operation.

        Args:
            inputs: A list or tuple of two tensors, `[x1, x2]`.

        Returns:
            The tensor resulting from the operation.
        """
        if not isinstance(inputs, (list, tuple)) or len(inputs) != 2:
            raise ValueError("Input to LogAddExp layer must be a list of two tensors.")
        x1, x2 = inputs
        return ops.logaddexp(x1, x2)

    def get_ops(self):
        return lambda x: ops.logaddexp(x[0], x[1])

    def compute_output_shape(self, input_shape):
        """
        Computes the output shape of the layer via broadcasting rules.
        """

        if len(input_shape[0]) == len(input_shape[1]):
            return input_shape[0]

        # broadcast
        n_0 = len(input_shape[0])
        n_1 = len(input_shape[1])
        if n_0 < n_1:
            assert input_shape[0] == input_shape[1][:n_0]
            return input_shape[0] + (1,) * (n_1 - n_0)
        else:
            assert input_shape[1] == input_shape[0][:n_1]
            return input_shape[1] + (1,) * (n_0 - n_1)


@keras.saving.register_keras_serializable()
class Matmul(keras.layers.Layer):
    """
    A Keras layer to compute the matrix product of two tensors.

    This layer is a wrapper for `keras.ops.matmul`. It takes a list of two
    tensors as input. For 2D tensors, the shapes must be `(a, b)` and
    `(b, c)`, and the output will be `(a, c)`. The layer also supports
    batch matrix multiplication.
    """

    def __init__(self, **kwargs):
        """
        Initializes the Matmul layer.
        """
        super().__init__(**kwargs)

    def call(self, inputs):
        """
        Applies the matrix multiplication operation.

        Args:
            inputs: A list or tuple of two tensors, `[x1, x2]`.

        Returns:
            The tensor resulting from the matrix product.
        """
        if not isinstance(inputs, (list, tuple)) or len(inputs) != 2:
            raise ValueError("Input to Matmul layer must be a list of two tensors.")
        x1, x2 = inputs
        return ops.matmul(x1, x2)

    def get_ops(self):
        return lambda x: ops.matmul(x[0], x[1])

    def compute_output_shape(self, input_shape):
        """
        Computes the output shape of the layer.
        """
        if not isinstance(input_shape, (list, tuple)) or len(input_shape) != 2:
            raise ValueError("Input shape must be a list of two shapes.")

        shape1, shape2 = input_shape

        if len(shape1) < 2 or len(shape2) < 2:
            raise ValueError("Inputs must be at least 2D for matrix multiplication.")

        if shape1[-1] != shape2[-2]:
            raise ValueError(
                "The last dimension of the first input must match the "
                f"second-to-last dimension of the second input. "
                f"Received shapes {shape1} and {shape2}."
            )

        # Handle broadcasting for batch dimensions
        batch_shape1 = list(shape1[:-2])
        batch_shape2 = list(shape2[:-2])

        s1_rev = batch_shape1[::-1]
        s2_rev = batch_shape2[::-1]
        max_len = max(len(s1_rev), len(s2_rev))

        output_batch_shape_rev = []
        for i in range(max_len):
            d1 = s1_rev[i] if i < len(s1_rev) else 1
            d2 = s2_rev[i] if i < len(s2_rev) else 1

            if d1 is None or d2 is None:
                output_batch_shape_rev.append(None)
            elif d1 == d2 or d1 == 1 or d2 == 1:
                output_batch_shape_rev.append(max(d1, d2))
            else:
                raise ValueError(
                    f"Batch shapes {shape1[:-2]} and {shape2[:-2]} are not broadcastable."
                )

        output_batch_shape = tuple(output_batch_shape_rev[::-1])

        return output_batch_shape + (shape1[-2], shape2[-1])


@keras.saving.register_keras_serializable()
class Maximum(keras.layers.Layer):
    """
    A Keras layer to compute the element-wise maximum of two tensors.

    This layer is a wrapper for `keras.ops.maximum`. It takes a list of two
    tensors as input, which must be broadcastable to the same shape.
    """

    def __init__(self, **kwargs):
        """
        Initializes the Maximum layer.
        """
        super().__init__(**kwargs)

    def call(self, inputs):
        """
        Applies the maximum operation.

        Args:
            inputs: A list or tuple of two tensors, `[x1, x2]`.

        Returns:
            The tensor resulting from the element-wise maximum.
        """
        if not isinstance(inputs, (list, tuple)) or len(inputs) != 2:
            raise ValueError("Input to Maximum layer must be a list of two tensors.")
        x1, x2 = inputs
        return ops.maximum(x1, x2)

    def compute_output_shape(self, input_shape):
        """
        Computes the output shape of the layer via broadcasting rules.
        """
        if not isinstance(input_shape, (list, tuple)) or len(input_shape) != 2:
            raise ValueError("Input shape must be a list of two shapes.")

        shape1, shape2 = input_shape

        # To compute the broadcasted shape, we align shapes from the right.
        s1_rev = list(shape1)[::-1]
        s2_rev = list(shape2)[::-1]
        max_len = max(len(s1_rev), len(s2_rev))

        output_shape_rev = []
        for i in range(max_len):
            d1 = s1_rev[i] if i < len(s1_rev) else 1
            d2 = s2_rev[i] if i < len(s2_rev) else 1

            if d1 is None or d2 is None:
                output_shape_rev.append(None)
            elif d1 == d2:
                output_shape_rev.append(d1)
            elif d1 == 1:
                output_shape_rev.append(d2)
            elif d2 == 1:
                output_shape_rev.append(d1)
            else:
                raise ValueError("Input shapes are not broadcastable: " f"{shape1} and {shape2}")

        return tuple(output_shape_rev[::-1])

    def get_ops(self):
        return lambda x: ops.maximum(x[0], x[1])


@keras.saving.register_keras_serializable()
class Minimum(keras.layers.Layer):
    """
    A Keras layer to compute the element-wise minimum of two tensors.

    This layer is a wrapper for `keras.ops.minimum`. It takes a list of two
    tensors as input, which must be broadcastable to the same shape.
    """

    def __init__(self, **kwargs):
        """
        Initializes the Minimum layer.
        """
        super().__init__(**kwargs)

    def call(self, inputs):
        """
        Applies the minimum operation.

        Args:
            inputs: A list or tuple of two tensors, `[x1, x2]`.

        Returns:
            The tensor resulting from the element-wise minimum.
        """
        if not isinstance(inputs, (list, tuple)) or len(inputs) != 2:
            raise ValueError("Input to Minimum layer must be a list of two tensors.")
        x1, x2 = inputs
        return ops.minimum(x1, x2)

    def compute_output_shape(self, input_shape):
        """
        Computes the output shape of the layer via broadcasting rules.
        """
        if not isinstance(input_shape, (list, tuple)) or len(input_shape) != 2:
            raise ValueError("Input shape must be a list of two shapes.")

        shape1, shape2 = input_shape

        # To compute the broadcasted shape, we align shapes from the right.
        s1_rev = list(shape1)[::-1]
        s2_rev = list(shape2)[::-1]
        max_len = max(len(s1_rev), len(s2_rev))

        output_shape_rev = []
        for i in range(max_len):
            d1 = s1_rev[i] if i < len(s1_rev) else 1
            d2 = s2_rev[i] if i < len(s2_rev) else 1

            if d1 is None or d2 is None:
                output_shape_rev.append(None)
            elif d1 == d2:
                output_shape_rev.append(d1)
            elif d1 == 1:
                output_shape_rev.append(d2)
            elif d2 == 1:
                output_shape_rev.append(d1)
            else:
                raise ValueError("Input shapes are not broadcastable: " f"{shape1} and {shape2}")

        return tuple(output_shape_rev[::-1])

    def get_ops(self):
        return lambda x: ops.minimum(x[0], x[1])


@keras.saving.register_keras_serializable()
class MoveAxis(keras.layers.Layer):
    """
    A Keras layer to move axes of a tensor to new positions.

    This layer is a wrapper for `keras.ops.moveaxis`.

    Args:
        source (int or tuple of ints): The original positions of the axes
            to move.
        destination (int or tuple of ints): The new positions for the axes.
    """

    def __init__(self, source, destination, **kwargs):
        """
        Initializes the MoveAxis layer.

        Args:
            source: Original positions of the axes.
            destination: Destination positions for the axes.
            **kwargs: Standard layer keyword arguments.
        """
        super().__init__(**kwargs)
        self.source = source
        self.destination = destination

    def call(self, inputs):
        """
        Applies the moveaxis operation.

        Args:
            inputs: The input tensor.

        Returns:
            A new tensor with axes moved.
        """
        return ops.moveaxis(inputs, self.source, self.destination)

    def compute_output_shape(self, input_shape):
        """
        Computes the output shape by reordering the input shape's dimensions.
        """
        source = self.source if isinstance(self.source, (list, tuple)) else (self.source,)
        destination = (
            self.destination if isinstance(self.destination, (list, tuple)) else (self.destination,)
        )

        rank = len(input_shape)

        # Normalize axes to be positive
        source = [s if s >= 0 else rank + s for s in source]
        destination = [d if d >= 0 else rank + d for d in destination]

        # Create a permutation of axis indices
        perm = [i for i in range(rank) if i not in source]

        for d, s in sorted(zip(destination, source)):
            perm.insert(d, s)

        # Build the output shape using the permutation
        output_shape = [input_shape[i] for i in perm]

        return tuple(output_shape)

    def get_ops(self):
        return lambda x: ops.moveaxis(x, self.source, self.destination)


@keras.saving.register_keras_serializable()
class Negative(keras.layers.Layer):
    """
    A Keras layer to compute the element-wise numerical negative of a tensor.

    This layer is a wrapper for the `keras.ops.negative` function, which
    is equivalent to `-x`.
    """

    def __init__(self, **kwargs):
        """
        Initializes the Negative layer.

        Args:
            **kwargs: Standard layer keyword arguments.
        """
        super().__init__(**kwargs)

    def call(self, inputs):
        """
        Applies the negative operation.

        Args:
            inputs: The input tensor.

        Returns:
            A tensor of the same shape as the input, with each element negated.
        """
        return ops.negative(inputs)

    def get_ops(self):
        return ops.negative


@keras.saving.register_keras_serializable()
class Norm(keras.layers.Layer):
    """
    A Keras layer to compute the norm of a tensor.

    This layer is a wrapper for `keras.ops.norm`. It can compute vector
    norms along a given axis or matrix norms over a pair of axes.

    Args:
        ord (int, float, 'fro', 'inf', optional): The order of the norm.
            See `keras.ops.norm` documentation for details. Defaults to None.
        axis (int, tuple of ints, optional): The axis or axes along which
            to compute the norm. If None, the norm is computed over the
            entire tensor. Defaults to None.
        keepdims (bool, optional): If True, the axes which are normed over
            are left in the result as dimensions with size 1. Defaults to False.
    """

    def __init__(self, ord=None, axis=None, keepdims=False, **kwargs):
        """
        Initializes the Norm layer.
        """
        super().__init__(**kwargs)
        self.ord = ord
        self.axis = axis
        self.keepdims = keepdims

    def call(self, inputs):
        """
        Applies the norm operation.

        Args:
            inputs: The input tensor.

        Returns:
            A tensor containing the computed norms.
        """
        return ops.norm(inputs, ord=self.ord, axis=self.axis, keepdims=self.keepdims)

    def get_ops(self):
        return lambda x: ops.norm(x, ord=self.ord, axis=self.axis, keepdims=self.keepdims)

    def compute_output_shape(self, input_shape):
        """
        Computes the output shape of the layer.
        """
        if self.axis is None:
            if self.keepdims:
                return (1,) * len(input_shape)
            else:
                return ()

        # Normalize axis to be a tuple of positive integers
        rank = len(input_shape)
        axis = self.axis if isinstance(self.axis, (list, tuple)) else (self.axis,)
        axis = [ax if ax >= 0 else rank + ax for ax in axis]

        if self.keepdims:
            output_shape = list(input_shape)
            for ax in axis:
                output_shape[ax] = 1
            return tuple(output_shape)
        else:
            output_shape = [dim for i, dim in enumerate(input_shape) if i not in axis]
            return tuple(output_shape)


@keras.saving.register_keras_serializable()
class OnesLike(keras.layers.Layer):
    """
    A Keras layer that creates a tensor of ones with the same shape as
    another tensor.

    This layer is a wrapper for the `keras.ops.ones_like` function. The
    values of the input tensor are ignored; only its shape is used.

    Args:
        dtype (string, optional): The data type of the output tensor. If None,
            the dtype is inferred from the input tensor.
    """

    def call(self, inputs):
        """
        Applies the ones_like operation.

        Args:
            inputs: The input tensor (used for its shape).

        Returns:
            A new tensor of the same shape as the input, filled with ones.
        """
        return ops.ones_like(inputs, dtype=inputs.dtype)

    def get_ops(self):
        return ops.ones_like


@keras.saving.register_keras_serializable()
class Prod(keras.layers.Layer):
    """
    A Keras layer to compute the product of tensor elements over given axes.

    This layer is a wrapper for `keras.ops.prod`.

    Args:
        axis (int, tuple of ints, optional): The axis or axes along which
            to compute the product. If None, the product of all elements is
            computed. Defaults to None.
        keepdims (bool, optional): If True, the reduced axes are left in the
            result as dimensions with size 1. Defaults to False.
    """

    def __init__(self, axis=None, keepdims=False, **kwargs):
        """
        Initializes the Prod layer.
        """
        super().__init__(**kwargs)
        self.axis = axis
        self.keepdims = keepdims

    def call(self, inputs):
        """
        Applies the product operation.

        Args:
            inputs: The input tensor.

        Returns:
            A tensor with the products.
        """
        return ops.prod(
            inputs,
            axis=self.axis,
            keepdims=self.keepdims,
            dtype=inputs.dtype,
        )

    def get_ops(self):
        return lambda x: ops.prod(
            x,
            axis=self.axis,
            keepdims=self.keepdims,
            dtype=x.dtype,
        )

    def compute_output_shape(self, input_shape):
        """
        Computes the output shape of the layer.
        """
        if self.axis is None:
            if self.keepdims:
                return (1,) * len(input_shape)
            else:
                return ()

        # Normalize axis to be a tuple of positive integers
        rank = len(input_shape)
        axis = self.axis if isinstance(self.axis, (list, tuple)) else (self.axis,)
        axis = [ax if ax >= 0 else rank + ax for ax in axis]

        if self.keepdims:
            output_shape = list(input_shape)
            for ax in axis:
                output_shape[ax] = 1
            return tuple(output_shape)
        else:
            output_shape = [dim for i, dim in enumerate(input_shape) if i not in axis]
            return tuple(output_shape)


@keras.saving.register_keras_serializable()
class Reciprocal(keras.layers.Layer):
    """
    A Keras layer to compute the element-wise reciprocal of a tensor.

    This layer is a wrapper for the `keras.ops.reciprocal` function, which
    is equivalent to `1 / x`.
    """

    def call(self, inputs):
        """
        Applies the reciprocal operation.

        Args:
            inputs: The input tensor.

        Returns:
            A tensor of the same shape as the input, with each element's reciprocal.
        """
        return ops.reciprocal(inputs)

    def get_ops(self):
        return ops.reciprocal


@keras.saving.register_keras_serializable()
class Repeat(keras.layers.Layer):
    """
    A Keras layer that repeats elements of a tensor along an axis.

    This layer is a wrapper for `keras.ops.repeat`.

    Args:
        repeats (int): The number of repetitions for each element.
        axis (int, optional): The axis along which to repeat values. If not
            specified, the tensor will be flattened and then repeated.
    """

    def __init__(self, repeats, axis=None, **kwargs):
        """
        Initializes the Repeat layer.

        Args:
            repeats: The number of repetitions.
            axis: The axis along which to repeat.
            **kwargs: Standard layer keyword arguments.
        """
        super().__init__(**kwargs)
        self.repeats = repeats
        self.axis = axis

    def call(self, inputs):
        """
        Applies the repeat operation.

        Args:
            inputs: The input tensor.

        Returns:
            A new tensor with elements repeated.
        """
        return ops.repeat(inputs, self.repeats, axis=self.axis)

    def get_ops(self):
        return lambda x: ops.repeat(x, self.repeats, axis=self.axis)

    def compute_output_shape(self, input_shape):
        """
        Computes the output shape after repeating elements.
        """
        if self.axis is None:
            # Flatten and repeat
            if any(dim is None for dim in input_shape):
                return (None,)
            num_elements = math.prod(input_shape)
            return (num_elements * self.repeats,)
        else:
            # Repeat along a specific axis
            output_shape = list(input_shape)
            dim_at_axis = output_shape[self.axis]

            if dim_at_axis is not None:
                output_shape[self.axis] = dim_at_axis * self.repeats
            else:
                output_shape[self.axis] = None

            return tuple(output_shape)


@keras.saving.register_keras_serializable()
class Roll(keras.layers.Layer):
    """
    A Keras layer to roll tensor elements along a given axis.

    This layer is a wrapper for `keras.ops.roll`. Elements that are shifted
    off the end of an axis are re-introduced at the beginning.

    Args:
        shift (int or tuple of ints): The number of places by which elements
            are shifted. If a tuple, it must be the same length as `axis`.
        axis (int or tuple of ints, optional): The axis or axes along which
            to roll. If None, the tensor is flattened before rolling and then
            reshaped to its original shape. Defaults to None.
    """

    def __init__(self, shift, axis=None, **kwargs):
        """
        Initializes the Roll layer.
        """
        super().__init__(**kwargs)
        self.shift = shift
        self.axis = axis

    def call(self, inputs):
        """
        Applies the roll operation.

        Args:
            inputs: The input tensor.

        Returns:
            A new tensor with elements rolled.
        """
        return ops.roll(inputs, shift=self.shift, axis=self.axis)

    def get_ops(self):
        return lambda x: ops.roll(x, shift=self.shift, axis=self.axis)


@keras.saving.register_keras_serializable()
class Round(keras.layers.Layer):
    """
    A Keras layer to round the elements of a tensor to the nearest value.

    This layer is a wrapper for `keras.ops.round`.

    Args:
        decimals (int, optional): The number of decimal places to round to.
            If 0, the tensor is rounded to the nearest integer. Defaults to 0.
    """

    def __init__(self, decimals=0, **kwargs):
        """
        Initializes the Round layer.
        """
        super().__init__(**kwargs)
        self.decimals = decimals

    def call(self, inputs):
        """
        Applies the round operation.

        Args:
            inputs: The input tensor.

        Returns:
            A new tensor with elements rounded.
        """
        return ops.round(inputs, decimals=self.decimals)

    def get_ops(self):
        return lambda x: ops.round(x, decimals=self.decimals)


@keras.saving.register_keras_serializable()
class Sign(keras.layers.Layer):
    """
    A Keras layer to compute the element-wise sign of a tensor.

    This layer is a wrapper for `keras.ops.sign`. It returns -1 for negative
    elements, 0 for zero, and 1 for positive elements.
    """

    def __init__(self, **kwargs):
        """
        Initializes the Sign layer.
        """
        super().__init__(**kwargs)

    def call(self, inputs):
        """
        Applies the sign operation.

        Args:
            inputs: The input tensor.

        Returns:
            A new tensor containing the signs of the input elements.
        """
        return ops.sign(inputs)

    def get_ops(self):
        return ops.sign


@keras.saving.register_keras_serializable()
class Sin(keras.layers.Layer):
    """
    A Keras layer to compute the element-wise sine of a tensor.

    This layer is a wrapper for `keras.ops.sin`. The input tensor is
    assumed to be in radians.
    """

    def __init__(self, **kwargs):
        """
        Initializes the Sin layer.
        """
        super().__init__(**kwargs)

    def call(self, inputs):
        """
        Applies the sine operation.

        Args:
            inputs: The input tensor (in radians).

        Returns:
            A new tensor containing the sines of the input elements.
        """
        return ops.sin(inputs)

    def get_ops(self):
        return ops.sin


@keras.saving.register_keras_serializable()
class Sinh(keras.layers.Layer):
    """
    A Keras layer to compute the element-wise hyperbolic sine of a tensor.

    This layer is a wrapper for `keras.ops.sinh`.
    """

    def __init__(self, **kwargs):
        """
        Initializes the Sinh layer.
        """
        super().__init__(**kwargs)

    def call(self, inputs):
        """
        Applies the hyperbolic sine operation.

        Args:
            inputs: The input tensor.

        Returns:
            A new tensor containing the hyperbolic sines of the input elements.
        """
        return ops.sinh(inputs)

    def get_ops(self):
        return ops.sinh


@keras.saving.register_keras_serializable()
class Sort(keras.layers.Layer):
    """
    A Keras layer to sort the elements of a tensor along an axis.

    This layer is a wrapper for `keras.ops.sort`.

    Args:
        axis (int, optional): The axis along which to sort. The default is -1,
            which sorts along the last axis. If None, the tensor is
            flattened before sorting. Defaults to -1.
        descending (bool, optional): If True, sorts in descending order;
            otherwise, sorts in ascending order. Defaults to False.
    """

    def __init__(self, axis=-1, descending=False, **kwargs):
        """
        Initializes the Sort layer.
        """
        super().__init__(**kwargs)
        self.axis = axis
        self.descending = descending

    def call(self, inputs):
        """
        Applies the sort operation.

        Args:
            inputs: The input tensor.

        Returns:
            A new tensor with elements sorted.
        """
        if self.descending:
            return -ops.sort(-inputs, axis=self.axis)
        else:
            return ops.sort(inputs, axis=self.axis)

    def get_ops(self):
        def func(x):
            if self.descending:
                return -ops.sort(-x, axis=self.axis)
            else:
                return ops.sort(x, axis=self.axis)

        return lambda x: func(x)


@keras.saving.register_keras_serializable()
class Sqrt(keras.layers.Layer):
    """
    A Keras layer to compute the element-wise square root of a tensor.

    This layer is a wrapper for `keras.ops.sqrt`. Input values should be
    non-negative.
    """

    def __init__(self, **kwargs):
        """
        Initializes the Sqrt layer.
        """
        super().__init__(**kwargs)

    def call(self, inputs):
        """
        Applies the square root operation.

        Args:
            inputs: The input tensor.

        Returns:
            A new tensor containing the square roots of the input elements.
        """
        return ops.sqrt(inputs)

    def get_ops(self):
        return ops.sqrt


@keras.saving.register_keras_serializable()
class Square(keras.layers.Layer):
    """
    A Keras layer to compute the element-wise square of a tensor.

    This layer is a wrapper for `keras.ops.square`.
    """

    def __init__(self, **kwargs):
        """
        Initializes the Square layer.
        """
        super().__init__(**kwargs)

    def call(self, inputs):
        """
        Applies the square operation.

        Args:
            inputs: The input tensor.

        Returns:
            A new tensor containing the squares of the input elements.
        """
        return ops.square(inputs)

    def get_ops(self):
        return ops.square


@keras.saving.register_keras_serializable()
class Squeeze(keras.layers.Layer):
    """
    A Keras layer to remove dimensions of size 1 from a tensor's shape.

    This layer is a wrapper for `keras.ops.squeeze`.

    Args:
        axis (int or tuple of ints, optional): The axis or axes to squeeze.
            If an axis is specified, it is only removed if its size is 1.
            If None, all dimensions of size 1 are removed. Defaults to None.
    """

    def __init__(self, axis=None, **kwargs):
        """
        Initializes the Squeeze layer.
        """
        super().__init__(**kwargs)
        self.axis = axis

    def call(self, inputs):
        """
        Applies the squeeze operation.

        Args:
            inputs: The input tensor.

        Returns:
            A new tensor with dimensions of size 1 removed.
        """
        return ops.squeeze(inputs, axis=self.axis)

    def get_ops(self):
        return lambda x: ops.squeeze(x, axis=self.axis)

    def compute_output_shape(self, input_shape):
        """
        Computes the output shape after squeezing.
        """
        if self.axis is None:
            # Squeeze all dimensions of size 1
            return tuple(dim for dim in input_shape if dim != 1)
        else:
            # Squeeze specified axes
            axis = self.axis if isinstance(self.axis, (list, tuple)) else (self.axis,)
            rank = len(input_shape)
            # Normalize axes to be positive
            axis = [ax if ax >= 0 else rank + ax for ax in axis]

            output_shape = []
            for i, dim in enumerate(input_shape):
                if i in axis:
                    if dim != 1:
                        # Keras ops would raise an error, so we should too.
                        raise ValueError(
                            f"Cannot squeeze axis {i} because its size is {dim}, not 1."
                        )
                    # Don't include this dimension in the output
                    continue
                output_shape.append(dim)
            return tuple(output_shape)


@keras.saving.register_keras_serializable()
class Stack(keras.layers.Layer):
    """
    A Keras layer to stack a list of tensors along a new axis.

    This layer is a wrapper for `keras.ops.stack`. All tensors in the
    input list must have the same shape.

    Args:
        axis (int, optional): The axis in the result tensor along which the
            input tensors are stacked. Defaults to -1.
    """

    def __init__(self, axis=-1, **kwargs):
        """
        Initializes the Stack layer.
        """
        super().__init__(**kwargs)
        assert axis != 0
        self.axis = axis

    def call(self, inputs):
        """
        Applies the stack operation.

        Args:
            inputs: A list of tensors to be stacked.

        Returns:
            A single, stacked tensor.
        """
        if not isinstance(inputs, (list, tuple)):
            raise ValueError("Input to Stack layer must be a list of tensors.")
        return ops.stack(inputs, axis=self.axis)

    def get_ops(self):
        return lambda x: ops.stack(x, axis=self.axis)

    def compute_output_shape(self, input_shape):
        """
        Computes the output shape of the layer.
        """
        if not isinstance(input_shape, (list, tuple)) or not input_shape:
            raise ValueError("Input shape must be a list of shapes.")

        # All input shapes must be identical.
        ref_shape = input_shape[0]
        for shape in input_shape[1:]:
            if shape != ref_shape:
                raise ValueError(
                    "All tensors in a stack must have the same shape. "
                    f"Got {ref_shape} and {shape}."
                )

        # The output shape is the reference shape with a new dimension inserted.
        output_shape = list(ref_shape)
        output_shape.insert(self.axis, len(input_shape))

        return tuple(output_shape)


@keras.saving.register_keras_serializable()
class Std(keras.layers.Layer):
    """
    A Keras layer to compute the standard deviation of tensor elements.

    This layer is a wrapper for `keras.ops.std`.

    Args:
        axis (int, tuple of ints, optional): The axis or axes along which
            to compute the standard deviation. If None, the standard deviation
            of all elements is computed. Defaults to None.
        keepdims (bool, optional): If True, the reduced axes are left in the
            result as dimensions with size 1. Defaults to False.
    """

    def __init__(self, axis=None, keepdims=False, **kwargs):
        """
        Initializes the Std layer.
        """
        super().__init__(**kwargs)
        self.axis = axis
        self.keepdims = keepdims

    def call(self, inputs):
        """
        Applies the standard deviation operation.

        Args:
            inputs: The input tensor.

        Returns:
            A tensor with the standard deviations.
        """
        return ops.std(
            inputs,
            axis=self.axis,
            keepdims=self.keepdims,
        )

    def get_ops(self):
        return lambda x: ops.std(
            x,
            axis=self.axis,
            keepdims=self.keepdims,
        )

    def compute_output_shape(self, input_shape):
        """
        Computes the output shape of the layer.
        """
        if self.axis is None:
            if self.keepdims:
                return (1,) * len(input_shape)
            else:
                return ()

        # Normalize axis to be a tuple of positive integers
        rank = len(input_shape)
        axis = self.axis if isinstance(self.axis, (list, tuple)) else (self.axis,)
        axis = [ax if ax >= 0 else rank + ax for ax in axis]

        if self.keepdims:
            output_shape = list(input_shape)
            for ax in axis:
                output_shape[ax] = 1
            return tuple(output_shape)
        else:
            output_shape = [dim for i, dim in enumerate(input_shape) if i not in axis]
            return tuple(output_shape)


@keras.saving.register_keras_serializable()
class SwapAxes(keras.layers.Layer):
    """
    A Keras layer to interchange two axes of a tensor.

    This layer is a wrapper for `keras.ops.swapaxes`.

    Args:
        axis1 (int): The first axis to be swapped.
        axis2 (int): The second axis to be swapped.
    """

    def __init__(self, axis1, axis2, **kwargs):
        """
        Initializes the SwapAxes layer.
        """
        super().__init__(**kwargs)
        assert axis1 != 0
        assert axis2 != 0
        self.axis1 = axis1
        self.axis2 = axis2

    def call(self, inputs):
        """
        Applies the swapaxes operation.

        Args:
            inputs: The input tensor.

        Returns:
            A new tensor with the specified axes swapped.
        """
        return ops.swapaxes(inputs, axis1=self.axis1, axis2=self.axis2)

    def get_ops(self):
        return lambda x: ops.swapaxes(x, axis1=self.axis1, axis2=self.axis2)

    def compute_output_shape(self, input_shape):
        """
        Computes the output shape by swapping the specified dimensions.
        """
        shape = list(input_shape)

        # Swap the dimensions at the specified axes
        shape[self.axis1], shape[self.axis2] = shape[self.axis2], shape[self.axis1]

        return tuple(shape)


@keras.saving.register_keras_serializable()
class Tan(keras.layers.Layer):
    """
    A Keras layer to compute the element-wise tangent of a tensor.

    This layer is a wrapper for `keras.ops.tan`. The input tensor is
    assumed to be in radians.
    """

    def __init__(self, **kwargs):
        """
        Initializes the Tan layer.
        """
        super().__init__(**kwargs)

    def call(self, inputs):
        """
        Applies the tangent operation.

        Args:
            inputs: The input tensor (in radians).

        Returns:
            A new tensor containing the tangents of the input elements.
        """
        return ops.tan(inputs)

    def get_ops(self):
        return ops.tan


@keras.saving.register_keras_serializable()
class Trace(keras.layers.Layer):
    """
    A Keras layer to compute the sum along the diagonals of a tensor.

    This layer is a wrapper for `keras.ops.trace`. It reduces the rank of
    the input tensor by 2.

    Args:
        offset (int, optional): The offset of the diagonal to trace. `k=0` is
            the main diagonal. Defaults to 0.
        axis1 (int, optional): The first axis of the 2D planes from which to
            compute the trace. Defaults to 0.
        axis2 (int, optional): The second axis of the 2D planes from which to
            compute the trace. Defaults to 1.
    """

    def __init__(self, offset=0, axis1=1, axis2=2, **kwargs):
        """
        Initializes the Trace layer.
        """
        super().__init__(**kwargs)
        self.offset = offset
        assert axis1 != 0
        assert axis2 != 0

        self.axis1 = axis1
        self.axis2 = axis2

    def call(self, inputs):
        """
        Applies the trace operation.

        Args:
            inputs: The input tensor. Must be at least 2D.

        Returns:
            A tensor containing the trace.
        """
        return ops.trace(
            inputs,
            offset=self.offset,
            axis1=self.axis1,
            axis2=self.axis2,
        )

    def compute_output_shape(self, input_shape):
        """
        Computes the output shape of the layer.
        """
        rank = len(input_shape)
        if rank < 2:
            raise ValueError(f"Input must be at least 2D, but got rank {rank}.")

        # Normalize axes
        axis1 = self.axis1 if self.axis1 >= 0 else rank + self.axis1
        axis2 = self.axis2 if self.axis2 >= 0 else rank + self.axis2

        # The output shape is the input shape with the two traced axes removed
        output_shape = [dim for i, dim in enumerate(input_shape) if i not in (axis1, axis2)]
        return tuple(output_shape)

    def get_ops(self):
        return lambda x: ops.trace(
            x,
            offset=self.offset,
            axis1=self.axis1,
            axis2=self.axis2,
        )


@keras.saving.register_keras_serializable()
class Transpose(keras.layers.Layer):
    """
    A Keras layer to permute the dimensions of a tensor.

    This layer is a wrapper for `keras.ops.transpose`.

    Args:
        axes (list or tuple of ints, optional): A permutation of the dimensions
            of the input tensor. If None, the order of the dimensions is
            reversed. Defaults to None.
    """

    def __init__(self, axes=None, **kwargs):
        """
        Initializes the Transpose layer.
        """
        super().__init__(**kwargs)
        self.axes = axes

    def call(self, inputs):
        """
        Applies the transpose operation.

        Args:
            inputs: The input tensor.

        Returns:
            A new tensor with its axes permuted.
        """
        return ops.transpose(inputs, axes=self.axes)

    def get_ops(self):
        return lambda x: ops.transpose(x, axes=self.axes)

    def compute_output_shape(self, input_shape):
        """
        Computes the output shape by reordering the input shape's dimensions.
        """
        if self.axes is None:
            # If no axes are specified, reverse the shape
            return input_shape[::-1]

        # Build the new shape according to the axes permutation
        return tuple(input_shape[i] for i in self.axes)


@keras.saving.register_keras_serializable()
class Tril(keras.layers.Layer):
    """
    A Keras layer to extract the lower triangular part of a tensor.

    This layer is a wrapper for `keras.ops.tril`. Elements above the k-th
    diagonal are zeroed out.

    Args:
        k (int, optional): The diagonal to consider. `k=0` is the main
            diagonal, `k<0` is below, and `k>0` is above. Defaults to 0.
    """

    def __init__(self, k=0, **kwargs):
        """
        Initializes the Tril layer.
        """
        super().__init__(**kwargs)
        self.k = k

    def call(self, inputs):
        """
        Applies the tril operation.

        Args:
            inputs: The input tensor. Must be at least 2D.

        Returns:
            A new tensor with the upper triangular part zeroed out.
        """
        return ops.tril(inputs, k=self.k)

    def get_ops(self):
        return lambda x: ops.tril(x, k=self.k)

    def compute_output_shape(self, input_shape):
        """
        Computes the output shape of the layer.

        Since this operation does not change the tensor's shape, this method
        returns the input shape unchanged.

        Args:
            input_shape: Shape of the input tensor.

        Returns:
            The same shape as the input tensor.
        """
        if len(input_shape) < 2:
            raise ValueError("Input to Tril layer must be at least 2D.")
        return input_shape


@keras.saving.register_keras_serializable()
class Triu(keras.layers.Layer):
    """
    A Keras layer to extract the upper triangular part of a tensor.

    This layer is a wrapper for `keras.ops.triu`. Elements above the k-th
    diagonal are zeroed out.

    Args:
        k (int, optional): The diagonal to consider. `k=0` is the main
            diagonal, `k<0` is below, and `k>0` is above. Defaults to 0.
    """

    def __init__(self, k=0, **kwargs):
        """
        Initializes the Tril layer.
        """
        super().__init__(**kwargs)
        self.k = k

    def call(self, inputs):
        """
        Applies the triu operation.

        Args:
            inputs: The input tensor. Must be at least 2D.

        Returns:
            A new tensor with the lower triangular part zeroed out.
        """
        return ops.triu(inputs, k=self.k)

    def get_ops(self):
        return lambda x: ops.triu(x, k=self.k)

    def compute_output_shape(self, input_shape):
        """
        Computes the output shape of the layer.

        Since this operation does not change the tensor's shape, this method
        returns the input shape unchanged.

        Args:
            input_shape: Shape of the input tensor.

        Returns:
            The same shape as the input tensor.
        """
        if len(input_shape) < 2:
            raise ValueError("Input to Tril layer must be at least 2D.")
        return input_shape


@keras.saving.register_keras_serializable()
class TrueDivide(keras.layers.Layer):
    """
    A Keras layer to compute element-wise true division of two tensors.

    This layer is a wrapper for `keras.ops.true_divide` (the `/` operator).
    It takes a list of two tensors as input, `[x1, x2]`, which must be
    broadcastable to the same shape, and computes `x1 / x2`.
    """

    def __init__(self, **kwargs):
        """
        Initializes the TrueDivide layer.
        """
        super().__init__(**kwargs)

    def call(self, inputs):
        """
        Applies the true division operation.

        Args:
            inputs: A list or tuple of two tensors, `[x1, x2]`.

        Returns:
            The tensor resulting from the element-wise division.
        """
        if not isinstance(inputs, (list, tuple)) or len(inputs) != 2:
            raise ValueError("Input to TrueDivide layer must be a list of two tensors.")
        x1, x2 = inputs
        return ops.true_divide(x1, x2)

    def get_ops(self):
        return lambda x: ops.true_divide(x[0], x[1])

    def compute_output_shape(self, input_shape):
        """
        Computes the output shape of the layer via broadcasting rules.
        """
        if not isinstance(input_shape, (list, tuple)) or len(input_shape) != 2:
            raise ValueError("Input shape must be a list of two shapes.")

        shape1, shape2 = input_shape

        # To compute the broadcasted shape, we align shapes from the right.
        s1_rev = list(shape1)[::-1]
        s2_rev = list(shape2)[::-1]
        max_len = max(len(s1_rev), len(s2_rev))

        output_shape_rev = []
        for i in range(max_len):
            d1 = s1_rev[i] if i < len(s1_rev) else 1
            d2 = s2_rev[i] if i < len(s2_rev) else 1

            if d1 is None or d2 is None:
                output_shape_rev.append(None)
            elif d1 == d2 or d1 == 1 or d2 == 1:
                output_shape_rev.append(max(d1, d2))
            else:
                raise ValueError("Input shapes are not broadcastable: " f"{shape1} and {shape2}")

        return tuple(output_shape_rev[::-1])


@keras.saving.register_keras_serializable()
class Trunc(keras.layers.Layer):
    """
    A Keras layer to compute the element-wise truncated value of a tensor.

    This layer is a wrapper for `keras.ops.trunc`. It rounds the input
    elements towards zero.
    """

    def __init__(self, **kwargs):
        """
        Initializes the Trunc layer.
        """
        super().__init__(**kwargs)

    def call(self, inputs):
        """
        Applies the truncation operation.

        Args:
            inputs: The input tensor.

        Returns:
            A new tensor with the truncated values.
        """
        return ops.trunc(inputs)

    def get_ops(self):
        return ops.trunc


@keras.saving.register_keras_serializable()
class Var(keras.layers.Layer):
    """
    A Keras layer to compute the variance of tensor elements.

    This layer is a wrapper for `keras.ops.var`.

    Args:
        axis (int, tuple of ints, optional): The axis or axes along which
            to compute the variance. If None, the variance of all elements
            is computed. Defaults to None.
        keepdims (bool, optional): If True, the reduced axes are left in the
            result as dimensions with size 1. Defaults to False.
    """

    def __init__(self, axis=None, keepdims=False, **kwargs):
        """
        Initializes the Var layer.
        """
        super().__init__(**kwargs)
        self.axis = axis
        self.keepdims = keepdims

    def call(self, inputs):
        """
        Applies the variance operation.

        Args:
            inputs: The input tensor.

        Returns:
            A tensor with the variances.
        """
        return ops.var(
            inputs,
            axis=self.axis,
            keepdims=self.keepdims,
        )

    def compute_output_shape(self, input_shape):
        """
        Computes the output shape of the layer.
        """
        if self.axis is None:
            if self.keepdims:
                return (1,) * len(input_shape)
            else:
                return ()

        # Normalize axis to be a tuple of positive integers
        rank = len(input_shape)
        axis = self.axis if isinstance(self.axis, (list, tuple)) else (self.axis,)
        axis = [ax if ax >= 0 else rank + ax for ax in axis]

        if self.keepdims:
            output_shape = list(input_shape)
            for ax in axis:
                output_shape[ax] = 1
            return tuple(output_shape)
        else:
            output_shape = [dim for i, dim in enumerate(input_shape) if i not in axis]
            return tuple(output_shape)

    def get_ops(self):
        return lambda x: ops.var(
            x,
            axis=self.axis,
            keepdims=self.keepdims,
        )


@keras.saving.register_keras_serializable()
class ZerosLike(keras.layers.Layer):
    """
    A Keras layer that creates a tensor of zeros with the same shape as
    another tensor.

    This layer is a wrapper for the `keras.ops.zeros_like` function. The
    values of the input tensor are ignored; only its shape is used.

    Args:
        dtype (string, optional): The data type of the output tensor. If None,
            the dtype is inferred from the input tensor.
    """

    def call(self, inputs):
        """
        Applies the ones_like operation.

        Args:
            inputs: The input tensor (used for its shape).

        Returns:
            A new tensor of the same shape as the input, filled with ones.
        """
        return ops.zeros_like(inputs, dtype=inputs.dtype)

    def get_ops(self):
        return ops.zeros_like
