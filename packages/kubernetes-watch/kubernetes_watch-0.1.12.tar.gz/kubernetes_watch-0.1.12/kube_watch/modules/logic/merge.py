from typing import Any, List, Dict
from kube_watch.enums.logic import Operations
from copy import deepcopy

def merge_logical_outputs(inp_dict: Dict):
    if 'operation' not in inp_dict.keys():
        raise TypeError("Missing required parameters: 'operation'")
    operation = inp_dict.get('operation')
    del inp_dict['operation']

    inputs = [v for k,v in inp_dict.items()]
    return merge_logical_list(inputs, operation)


def merge_logical_list(inp_list: List, operation: Operations):
    if operation == Operations.OR:
        return any(inp_list)
    if operation == Operations.AND:
        return all(inp_list)
    raise ValueError("Invalid logical operation")


def partial_dict_update(orig_data, new_data):
    """
    This function is used when some key value pairs in orig_data should
    be updated from new_data.
    """
    orig_data_copy = deepcopy(orig_data)
    for k, v in new_data.items():
        orig_data_copy[k] = v

    return orig_data_copy
