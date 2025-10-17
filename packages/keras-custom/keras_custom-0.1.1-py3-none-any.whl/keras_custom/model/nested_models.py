from typing import List, Union

import keras  # type:ignore
from keras import KerasTensor as Tensor  # type:ignore
from keras.layers import Layer  # type:ignore
from keras.models import Model, Sequential  # type:ignore
from keras.src.ops.node import Node


def forward_propagate(node: Node, nested_input: Tensor, layer_in: Tensor) -> Tensor:
    """
    Perform forward propagation through a computational graph, starting from the given node.

    The function recursively traverses the parent nodes of the input node and propagates the input
    through the operations associated with each node, ultimately returning the output of the forward pass.

    Args:
        node: The node from which forward propagation starts. It represents an operation
                      in the computational graph.
        nested_input: The input tensor to be propagated through the network.
        layer_in: A tensor that specifies a layer's input for comparison to determine
                           if propagation should continue.

    Returns:
        Tensor: The output of the forward propagation, which is the result of applying the
                operations of the node's parent nodes and operations in sequence.

    """

    if not (layer_in is None) and node.operation.name == layer_in.name:
        return nested_input

    else:
        # get parent of nodes
        parent_nodes: List[None] = node.parent_nodes
        if len(parent_nodes):
            parents_inputs = []
            for p_node in parent_nodes:
                p_input = forward_propagate(p_node, nested_input, layer_in)
                if isinstance(p_input, list):
                    parents_inputs += p_input
                else:
                    parents_inputs.append(p_input)

            layer_node = node.operation
            if isinstance(layer_node.input, list):
                output = layer_node(parents_inputs)
            else:
                try:
                    output = layer_node(parents_inputs[0])
                except ValueError:
                    import pdb

                    pdb.set_trace()
            return output
        else:
            return nested_input


def get_nested_model(
    model: Union[Model, Sequential],
    layer_out: Layer,
    layer_in: Layer,
    input_shape_wo_batch: List[int],
) -> Model:
    """
    Create a nested model that extracts a sub-model from a given model, starting from the specified input and output layers.

    This function allows you to define a sub-model that performs forward propagation starting from the `layer_in`
    to the `layer_out`. The model is constructed by traversing the layers in the original model and selecting the
    appropriate layers based on their names.

    Args:
        model: The original Keras model or sequential model to extract the sub-model from.
        layer_out: The output layer of the sub-model. The function will extract the layer operation associated
                           with this layer.
        layer_in: The input layer to the sub-model. This layer defines where the forward pass will begin.
                          If `None`, the `input_shape_wo_batch` is used directly.
        input_shape_wo_batch: The shape of the input tensor excluding the batch size.

    Returns:
        Model: A Keras Model representing the nested sub-model that starts from `layer_in` and ends at `layer_out`.
    """

    if not layer_in is None:
        input_shape_wo_batch = layer_in.output.shape[1:]

    nested_input = keras.layers.Input(input_shape_wo_batch)

    node_out_list = [
        n
        for subnodes in model._nodes_by_depth.values()
        for n in subnodes
        if n.operation.name == layer_out.name
    ]
    node_out = node_out_list[0]

    output = forward_propagate(node_out, nested_input, layer_in)

    return Model(nested_input, output)
