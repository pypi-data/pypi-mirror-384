import keras
from keras.models import Model
from typing import List


def forward_propagate(node, nested_input, layer_in):


    if not(layer_in is None) and node.operation.name == layer_in.name:
        return nested_input

    else:
        # get parent of nodes
        parent_nodes: List[None] = node.parent_nodes
        if len(parent_nodes):
            parents_inputs=[]
            for p_node in parent_nodes:
                p_input = forward_propagate(p_node, nested_input, layer_in)
                if isinstance(p_input, list):
                    parents_inputs+= p_input
                else:
                    parents_inputs.append(p_input)

    
            layer_node = node.operation
            if isinstance(layer_node.input, list):
                output = layer_node(parents_inputs)
            else:
                try:
                    output = layer_node(parents_inputs[0])
                except ValueError:
                    import pdb; pdb.set_trace()
            return output
        else:
            return nested_input
        

def get_nested_model(model, layer_out, layer_in, input_shape_wo_batch):

    if not layer_in is None:
        input_shape_wo_batch = layer_in.output.shape[1:]
        
    nested_input = keras.layers.Input(input_shape_wo_batch)
    print(nested_input)
    
    node_out_list = [n for subnodes in model._nodes_by_depth.values() for n in subnodes if n.operation.name==layer_out.name]
    node_out = node_out_list[0]

    output = forward_propagate(node_out, nested_input, layer_in)

    return Model(nested_input, output)
    