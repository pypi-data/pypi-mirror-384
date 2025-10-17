from typing import List, Union

import keras  # type:ignore
import numpy as np
from keras import KerasTensor as Tensor  # type:ignore
from keras.layers import Layer  # type:ignore
from keras.layers import (  # type:ignore
    Dense,
    EinsumDense,
    Flatten,
    Permute,
    RepeatVector,
    Reshape,
)
from keras.models import Model, Sequential  # type:ignore
from keras.src.layers.pooling.base_global_pooling import BaseGlobalPooling
from keras.src.ops.node import Node


def switch_model_input_channel(
    model: Model,
    original_order: str,
) -> Model:
    """
    Switches the input channel format of a Keras model by updating the input tensor's
    channel order from 'channels_first' to 'channels_last' or vice versa. This function
    handles the modification of the input layer and the propagation of the new format
    through the model's layers.

    Args:
        model: A Keras model instance, which must not be a Sequential model.
        original_order: The original channel order of the input tensor,
                               either 'channels_first' or 'channels_last'.

    Returns:
        Model: A new Keras model with the input tensor's channel format switched.
        str: The updated channel order after switching.

    Raises:
        NotImplementedError: If the model has multiple inputs or is an instance of Sequential.
    """

    forward_order = switch_order(original_order)
    if len(model.inputs) > 1:
        raise NotImplementedError(
            "we do not support multiple inputs. Raise a dedicated PR if needed"
        )
    if isinstance(model, Sequential):
        raise NotImplementedError("Please convert your sequential model in a keras.models.Model")
    input_shape_wo_batch = list(model.input.shape[1:])
    # create an input tensor with opposite channel (first-> last, last_first)
    switch_shape = np.copy(input_shape_wo_batch)
    switch_shape[0] = input_shape_wo_batch[-1]
    switch_shape[-1] = input_shape_wo_batch[0]

    switch_input = keras.layers.Input(switch_shape)

    model_outputs = list(model.outputs)
    forward_order_outputs = []
    outputs = []
    dico_node = dict()
    for model_output in model_outputs:
        # layer_out
        # do a loop
        node_out_list = [
            n
            for subnodes in model._nodes_by_depth.values()
            for n in subnodes
            if n.operation.output.name == model_output.name
        ]

        node_out = node_out_list[0]
        output, forward_order_output = forward_switch_propagate(
            node_out, switch_input, original_order, forward_order, dico_node
        )
        forward_order_outputs.append(forward_order_output)
        outputs.append(output)

    if len(model_outputs) == 1:
        forward_order = forward_order[0]
        outputs = outputs[0]
    return Model(switch_input, outputs), forward_order


def forward_switch_propagate(
    node: Node, nested_input: Tensor, original_order: str, forward_order: str, dico_node
) -> Tensor:
    """
    Recursively propagates the switching of input channels through the layers of a Keras model.
    This function handles the transformation of the input tensor format for each layer while
    keeping track of the original and updated channel orders. It ensures that each layer receives
    the appropriate input tensor with the correct format.

    Args:
        node: The current node in the computation graph, representing a layer in the model.
        nested_input: The input tensor to the current node, potentially with modified channel order.
        original_order: The original channel order of the input tensor, either 'channels_first' or 'channels_last'.
        forward_order: The current channel order used in the propagation through the model.
        dico_node : A dictionary used to memorize the computed outputs for nodes to avoid redundant calculations.

    Returns:
        Tensor: The output tensor after the channel order transformation and layer processing.
        str: The updated channel order after the transformation.
    """

    if id(node) in dico_node:
        return dico_node[id(node)]
    if isinstance(node.operation, keras.layers.InputLayer):
        dico_node[id(node)] = (nested_input, forward_order)
        return nested_input, forward_order

    # get parent of nodes
    parent_nodes: List[None] = node.parent_nodes
    if len(parent_nodes):
        parents_inputs = []
        forward_order_from_parents = []
        for p_node in parent_nodes:
            p_input, p_forward_order = forward_switch_propagate(
                p_node, nested_input, original_order, forward_order, dico_node
            )

            if isinstance(p_input, list):
                parents_inputs += p_input
            else:
                parents_inputs.append(p_input)
            if isinstance(p_forward_order, list):
                forward_order_from_parents += p_forward_order
            else:
                forward_order_from_parents.append(p_forward_order)

        layer_node = node.operation
        if isinstance(layer_node.input, list):
            output, forward_layer_order = switch_channel_layer(
                parents_inputs, layer_node, original_order, forward_order_from_parents
            )
        else:
            output, forward_layer_order = switch_channel_layer(
                parents_inputs[0], layer_node, original_order, forward_order_from_parents[0]
            )

        dico_node[id(node)] = (output, forward_layer_order)
        return output, forward_layer_order

    else:
        dico_node[id(node)] = (nested_input, forward_order)
        return nested_input, forward_order


def get_permute(input_tensor: Tensor):
    """
    Generates a permutation of the input tensor's dimensions, swapping the first and last dimensions
    (i.e., the channel and spatial dimensions) while preserving the batch size dimension.

    Args:
        input_tensor: The input tensor to be permuted, typically a tensor with shape
                                (batch_size, channels, height, width) or (batch_size, height, width, channels).

    Returns:
        Tensor: A new tensor with the first and last dimensions permuted. The output shape is
                (batch_size, width, height, channels) or (batch_size, channels, height, width),
                depending on the original input shape.
    """

    input_shape_wo_batch = input_tensor.shape[1:]
    n_dim = len(input_shape_wo_batch)
    dims = np.arange(n_dim) + 1
    dims[0] = n_dim
    dims[-1] = 1
    input_tensor_perm = Permute(dims)(input_tensor)
    return input_tensor_perm


def switch_order(data_format: str) -> str:
    """
    Switches the channel order format between 'channels_first' and 'channels_last'.
    If the input data format is 'channels_first', the function returns 'channels_last',
    and vice versa.

    Args:
        data_format: The original data format, either 'channels_first' or 'channels_last'.

    Returns:
        The switched data format, either 'channels_first' or 'channels_last'.
    """
    if data_format == "channels_first":  # better with an Enum
        return "channels_last"
    return "channels_first"


def switch_channel_layer(
    input_tensor: Union[Tensor, List[Tensor]],
    layer: Layer,
    original_order: str,
    forward_order: Union[List[str], str],
):
    """
    Switches the channel order for a given layer while handling the input tensor(s) format.
    This function supports layers with multiple inputs and adjusts the input tensor(s) to match
    the required channel order. It also handles layers with attributes like `data_format` and `axis`,
    ensuring proper tensor transformation.

    Args:
        input_tensor: The input tensor(s) for the layer, either a single tensor
                                                   or a list of tensors (for layers with multiple inputs).
        layer: The Keras layer whose input tensor(s) is being processed.
        original_order: The original channel order of the input tensor(s), either 'channels_first' or 'channels_last'.
        forward_order: The target channel order for the forward pass, which may be a single string
                                                or a list of strings if multiple inputs are provided.

    Returns:
        The transformed tensor(s) with the switched channel order, and the updated channel order.
    """
    # consider multiple inputs
    if isinstance(input_tensor, list):
        # assess that every input is in the same order
        perm_indices = np.where([f == original_order for f in forward_order])[0]
        if len(perm_indices) == len(forward_order):
            return layer(input_tensor), original_order
        if len(perm_indices) != 0:
            # permute every input indices to be in the forward channel order
            for i in perm_indices:
                input_tensor[i] = get_permute(input_tensor[i])
            forward_order = switch_order(original_order)
            # no merging layer has data_format, we can apply it directly
            return layer(input_tensor), forward_order
        return layer(input_tensor), switch_order(original_order)

    if original_order == forward_order:
        return layer(input_tensor), forward_order
    if isinstance(layer, Model) or isinstance(layer, Sequential):
        if len(layer.inputs) > 1:
            raise NotImplementedError(
                "raise a dedicated PR for a nested model with multiple inputs"
            )
        return switch_model_input_channel(layer, original_order)
    if isinstance(layer, Flatten) or isinstance(layer, BaseGlobalPooling):
        # special case, Flatten has a data_format attribute but after Flatten we loose the channel dimension
        # we need to permute first
        input_tensor_perm = get_permute(input_tensor)
        return layer(input_tensor_perm), original_order
    if hasattr(layer, "data_format"):
        config = layer.get_config()
        config["data_format"] = forward_order
        layer_switch = layer.__class__.from_config(config)
        # built
        _ = layer_switch(input_tensor)
        if hasattr(layer_switch, "set_weights"):
            layer_switch.set_weights(layer.get_weights())
        return layer_switch(input_tensor), forward_order
    if hasattr(layer, "axis"):
        N = len(layer.input.shape[1:])
        if layer.axis in [-1, N, 1]:
            # set axis to 1
            config = layer.get_config()
            if layer.axis == 1:
                config["axis"] = -1
            else:
                config["axis"] = 1
            layer_switch = layer.__class__.from_config(config)
            # built
            _ = layer_switch(input_tensor)
            if hasattr(layer_switch, "set_weights"):
                layer_switch.set_weights(layer.get_weights())
            return layer_switch(input_tensor), forward_order
        else:
            return layer(input_tensor), forward_order
    # if layer is reshaping, do a dedicated copy
    if max(
        [
            isinstance(layer, class_i)
            for class_i in [Permute, Reshape, RepeatVector, Dense, EinsumDense]
        ]
    ):
        # permute input
        input_tensor_perm = get_permute(input_tensor)
        return layer(input_tensor_perm), original_order
    else:
        return layer(input_tensor), forward_order
